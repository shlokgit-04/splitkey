import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from shamir_core import split, reconstruct, zeroize

def test_roundtrip():
    for length in (1, 16, 32, 77):
        key = os.urandom(length)
        shares = split(key, k=3, n=5)
        assert reconstruct(shares[:3]) == key, f"3-of-5 failed at len {length}"
        assert reconstruct(shares) == key, "all-5 failed"

def test_below_threshold_fails():
    key = os.urandom(32)
    shares = split(key, k=3, n=5)
    wrong = reconstruct(shares[:2] + [(99, shares[0][1])])
    assert wrong != key, "2 shares must not reconstruct the key"

def test_threshold_configs():
    for k, n in ((2, 3), (3, 5), (4, 6)):
        key = os.urandom(24)
        shares = split(key, k=k, n=n)
        assert reconstruct(shares[:k]) == key

def test_zeroize():
    buf = bytearray(b"super-secret-key")
    zeroize(buf)
    assert buf == bytearray(len(buf))

test_roundtrip(); test_below_threshold_fails(); test_threshold_configs(); test_zeroize()
print("ALL TESTS PASSED")
