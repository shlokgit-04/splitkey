"""Vault store: five separate custody locations for Shamir shares.

Each vault simulates a distinct store (local disk, USB drive, cloud bucket,
hardware token, paper backup). A vault alone can never reveal the key.
"""
import json, os, time

VAULT_LABELS = [
    "Local Disk", "USB Drive", "Cloud Bucket", "Hardware Token", "Paper Backup",
]

class VaultStore:
    def __init__(self, path="vaults.json"):
        self.path = path
        self.state = {"threshold": 3, "shares": 5, "vaults": [], "audit": [], "collected": [], "key_active": False}
        if os.path.exists(path):
            self.state = json.load(open(path))

    def _save(self):
        json.dump(self.state, open(self.path, "w"), indent=2)

    def log(self, event, detail=""):
        self.state["audit"].append({"ts": time.strftime("%Y-%m-%d %H:%M:%S"), "event": event, "detail": detail})
        self._save()

    @property
    def has_secret(self):
        return bool(self.state["vaults"])

    def split_into_vaults(self, shares, threshold):
        self.state["vaults"] = [
            {"id": i, "label": VAULT_LABELS[i], "x": x, "share_hex": data.hex()}
            for i, (x, data) in enumerate(shares)
        ]
        self.state["threshold"] = threshold
        self.state["shares"] = len(shares)
        self.state["collected"] = []
        self.state["key_active"] = False
        self.log("split", f"key split into {len(shares)} shares, threshold {threshold}")

    def collect(self, vault_id):
        if vault_id not in self.state["collected"]:
            self.state["collected"].append(vault_id)
            self.log("share_collected", f"{self.state['vaults'][vault_id]['label']} (share #{vault_id + 1})")
            self._save()

    def collected_shares(self):
        return [(self.state["vaults"][i]["x"], bytes.fromhex(self.state["vaults"][i]["share_hex"]))
                for i in self.state["collected"]]

    def enough(self):
        return len(self.state["collected"]) >= self.state["threshold"]

    def clear_collected(self):
        self.state["collected"] = []
        self._save()

    def audit(self):
        return list(reversed(self.state["audit"][-40:]))
