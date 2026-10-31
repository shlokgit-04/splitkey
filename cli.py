#!/usr/bin/env python3
"""SplitKey terminal UI: split, reconstruct, audit - same engine as the web app."""
import argparse, sys
from shamir_core import split as shamir_split, reconstruct, zeroize
from agent import agent_encrypt

def main():
    p = argparse.ArgumentParser(description="SplitKey terminal UI")
    sub = p.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("split"); s.add_argument("--key", required=True); s.add_argument("--threshold", type=int, default=3); s.add_argument("--shares", type=int, default=5)
    r = sub.add_parser("reconstruct"); r.add_argument("--share", action="append", default=[]); r.add_argument("--message", required=True)
    sub.add_parser("audit")
    a = p.parse_args()
    if a.cmd == "split":
        shares = shamir_split(a.key.encode(), k=a.threshold, n=a.shares)
        print(f"split into {a.shares} shares, threshold {a.threshold}")
        for i, (x, data) in enumerate(shares, 1):
            print(f"  vault {i}: share {x} = {data.hex()}")
        print("store each share somewhere else. no single vault holds the key.")
    elif a.cmd == "reconstruct":
        parsed = []
        for raw in a.share:
            x, hexdata = raw.split(":", 1)
            parsed.append((int(x), bytes.fromhex(hexdata)))
        if len(parsed) < 3:
            sys.exit("need at least 3 shares (threshold)")
        key = bytearray(reconstruct(parsed))
        print("key reconstructed in memory only")
        print("ciphertext:", agent_encrypt(bytes(key), a.message))
        zeroize(key)
        print("key zeroized")
    else:
        sys.exit("audit history lives in the web dashboard")

if __name__ == "__main__":
    main()
