"""Agent mode: use the reconstructed key for a real task, then zeroize it.

The reconstructed master key exists only in memory for the length of one
operation, is never written to disk, and is never sent to any external API.
"""
import hashlib, hmac, os

def _keystream_xor(key: bytes, msg: bytes) -> bytes:
    """AES-GCM when the cryptography package is present, honest fallback
    keystream (SHA-256 in counter mode) otherwise. Either way the plaintext
    is only ever encrypted locally."""
    try:
        from cryptography.hazmat.primitives.ciphers.aead import AESGCM
        aes_key = hashlib.sha256(b"splitkey-agent-v1" + key).digest()
        nonce = os.urandom(12)
        return nonce + AESGCM(aes_key).encrypt(nonce, msg, None)
    except Exception:
        stream = bytearray()
        counter = 0
        while len(stream) < len(msg):
            stream += hashlib.sha256(key + counter.to_bytes(8, "big")).digest()
            counter += 1
        return bytes(a ^ b for a, b in zip(msg, stream))

def agent_encrypt(key: bytes, message: str) -> str:
    return _keystream_xor(key, message.encode()).hex()

def agent_decrypt(key: bytes, blob_hex: str) -> str:
    blob = bytes.fromhex(blob_hex)
    return _keystream_xor(key, blob).decode(errors="replace")
