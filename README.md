# SplitKey — Shamir key custody for private AI agents

Entry for the **Mathematics for Systems Security** Devpost hackathon, *AI pipeline
secret sharing* track. A private AI agent never holds your master key as a whole:
the key is split into 5 Shamir shares over GF(2^8) with a 3-of-5 threshold, held by
5 separate vaults. When the agent needs it, exactly the threshold of shares is
collected, the key is rebuilt **in memory only**, used to encrypt a message locally,
then zeroized. No single vault can ever reveal the key, and no external API ever
sees plaintext or the master key.

## What you get
- **Web dashboard** (Flask, dark UI): split a key, watch 5 vault custody cards, a
  live threshold meter, an audit log of every custody event, and a proof view
  showing each vault alone reveals nothing.
- **Agent mode**: simulated agent task (local encryption of a message) demonstrating
  reconstruct → use → zeroize, with AES-GCM when `cryptography` is installed.
- **Terminal UI** (`cli.py`): split / reconstruct from the command line.
- **Pure-Python Shamir core** (`shamir_core.py`), zero third-party crypto, with tests.

## Run
```bash
pip install -r requirements.txt
python app.py            # http://localhost:8080
python cli.py split --key "my-master-key"
python cli.py reconstruct --share "1:ab12..." --share "2:cd34..." --share "3:ef56..." --message "hello"
```

## Tests
```bash
python tests/test_shamir.py
```

## Why it matches the track
Pre-created cryptography is allowed: we use standard Shamir Secret Sharing. FHE is
optional and not required — the security property shown here is that the agent's
master key never exists as a whole outside memory, and inputs are encrypted
end-to-end before any pipeline use.
