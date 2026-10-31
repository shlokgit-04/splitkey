"""SplitKey web dashboard: Shamir key custody for private AI agents."""
import sys
from flask import Flask, render_template, request, jsonify
from shamir_core import split as shamir_split, reconstruct, zeroize
from vaults import VaultStore
from agent import agent_encrypt, agent_decrypt

app = Flask(__name__)
store = VaultStore("vaults.json")
_active_key = bytearray()  # lives in memory only, never persisted

@app.route("/")
def index():
    return render_template("index.html", s=store.state)

@app.get("/api/state")
def state():
    s = store.state
    return jsonify({
        "vaults": [{**v, "has_share": True} for v in s["vaults"]],
        "threshold": s["threshold"], "shares": s["shares"],
        "collected": s["collected"], "audit": store.audit(),
        "key_active": s["key_active"], "enough": store.enough(),
    })

@app.post("/api/split")
def split_route():
    key = (request.json.get("key") or "").strip()
    if not key:
        return jsonify({"ok": False, "error": "empty key"}), 400
    key_bytes = key.encode()
    threshold = int(request.json.get("threshold") or 3)
    shares = shamir_split(key_bytes, k=threshold, n=5)
    store.split_into_vaults(shares, threshold)
    return jsonify({"ok": True})

@app.post("/api/collect/<int:vault_id>")
def collect(vault_id):
    if not store.has_secret:
        return jsonify({"ok": False, "error": "no secret on file"}), 400
    store.collect(vault_id)
    return jsonify({"ok": True, "enough": store.enough()})

@app.post("/api/reconstruct")
def reconstruct_route():
    global _active_key
    if not store.enough():
        return jsonify({"ok": False, "error": f"need {store.state['threshold']} shares, have {len(store.state['collected'])}"}), 400
    key = reconstruct(store.collected_shares())
    _active_key = bytearray(key)
    store.state["key_active"] = True
    store.log("key_reconstructed", f"in memory only, from {len(store.state['collected'])} shares")
    store._save()
    return jsonify({"ok": True})

@app.post("/api/agent/run")
def agent_run():
    global _active_key
    if not _active_key:
        return jsonify({"ok": False, "error": "no key in memory"}), 400
    message = (request.json.get("message") or "").strip()
    if not message:
        return jsonify({"ok": False, "error": "empty message"}), 400
    blob = agent_encrypt(bytes(_active_key), message)
    store.log("agent_task", "message encrypted locally with in-memory key")
    store._save()
    return jsonify({"ok": True, "ciphertext": blob[:64] + ("..." if len(blob) > 64 else ""), "full": blob})

@app.post("/api/zeroize")
def zeroize_route():
    global _active_key
    zeroize(_active_key)
    _active_key = bytearray()
    store.state["key_active"] = False
    store.clear_collected()
    store.log("key_zeroized", "memory wiped, collected shares returned to vaults")
    store._save()
    return jsonify({"ok": True})

@app.post("/api/demo")
def demo():
    """Demo mode: split a sample master key so the whole flow can be shown."""
    key = "sk-demo-4f8a9c2e7b1d6a3f-DO-NOT-USE-IN-PROD"
    shares = shamir_split(key.encode(), k=3, n=5)
    store.split_into_vaults(shares, 3)
    return jsonify({"ok": True})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(sys.argv[1]) if len(sys.argv) > 1 else 8080)
