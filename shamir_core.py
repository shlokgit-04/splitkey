"""Shamir's Secret Sharing over GF(2^8) - pure Python, no third-party crypto.

SplitKey's custody engine: a master key is split into n shares with a k-of-n
threshold. Fewer than k shares mathematically reveal nothing about the key.
"""
import secrets as _secrets
from typing import List, Tuple

GF_POLY = 0x11D  # AES irreducible polynomial for GF(2^8)

def _gmul(a: int, b: int) -> int:
    p = 0
    for _ in range(8):
        if b & 1:
            p ^= a
        hi = a & 0x80
        a = (a << 1) & 0xFF
        if hi:
            a ^= GF_POLY & 0xFF
        b >>= 1
    return p

def _gpow(a: int, n: int) -> int:
    r = 1
    while n:
        if n & 1:
            r = _gmul(r, a)
        a = _gmul(a, a)
        n >>= 1
    return r

def _ginv(a: int) -> int:
    if a == 0:
        raise ZeroDivisionError("0 has no inverse in GF(256)")
    return _gpow(a, 254)

def split(key: bytes, k: int = 3, n: int = 5) -> List[Tuple[int, bytes]]:
    """Split key bytes into n shares needing k to reconstruct."""
    if not 1 <= k <= n:
        raise ValueError("threshold must satisfy 1 <= k <= n")
    rng = _secrets.SystemRandom()
    # coefficients are drawn ONCE per byte, then every share evaluates the
    # same polynomial, so the points stay consistent across shares.
    shares = [(x, bytearray()) for x in range(1, n + 1)]
    for b in key:
        # polynomial p(t) = b + c1*t + ... + c(k-1)*t^(k-1)
        coeffs = [b] + [rng.randint(0, 255) for _ in range(k - 1)]
        for x, data in shares:
            y = 0
            for m, c in enumerate(coeffs):
                y ^= _gmul(c, _gpow(x, m))
            data.append(y)
    return [(x, bytes(d)) for x, d in shares]

def reconstruct(shares: List[Tuple[int, bytes]], length: int | None = None) -> bytes:
    """Rebuild the secret from >= k shares via Lagrange interpolation at t=0."""
    xs = [x for x, _ in shares]
    if len(set(xs)) != len(xs):
        raise ValueError("duplicate share index")
    ys = [y for _, y in shares]
    k = len(shares)
    out = bytearray()
    for t in range(len(ys[0])):
        secret = 0
        for i in range(k):
            term = ys[i][t]
            for j in range(k):
                if i == j:
                    continue
                # Lagrange basis at 0: x_j / (x_j - x_i)  (subtraction = XOR in GF(2^8))
                term = _gmul(term, _gmul(xs[j], _ginv(xs[j] ^ xs[i])))
            secret ^= term
        out.append(secret)
    return bytes(out)

def zeroize(buf: bytearray) -> None:
    """Overwrite a buffer with zeros so the key does not linger in memory."""
    for i in range(len(buf)):
        buf[i] = 0
