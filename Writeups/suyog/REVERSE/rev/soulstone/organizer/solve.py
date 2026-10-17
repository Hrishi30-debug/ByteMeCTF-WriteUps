#!/usr/bin/env python3
"""
SoulStone - CTF Challenge Solver
Brute-forces the 24-bit Astral Resonance Token and recovers the flag.
"""

import sys
import os
import time
import subprocess
from multiprocessing import Pool, cpu_count

TARGET_RESONANCE_TAG = 0xE7F841B8

# Obfuscated sacrifice mask and keys extracted from binary
MASK = [0x47 ^ 0x5A, 0x41 ^ 0x6B, 0x4D ^ 0x7C, 0x4F ^ 0x8D, 0x52 ^ 0x9E, 0x41 ^ 0xAF]
KEYS = [0x5A, 0x6B, 0x7C, 0x8D, 0x9E, 0xAF]

def recover_sacrifice_name() -> str:
    return "".join(chr(m ^ k) for m, k in zip(MASK, KEYS))

def precompute_prefix_hash(sacrifice: str) -> int:
    h = 0x5A17F00D
    for ch in sacrifice.encode("ascii"):
        h = ((h * 31 + ch) ^ 0x9E3779B9) & 0xFFFFFFFF
    return h

def search_chunk(args):
    start, end, h = args
    for token in range(start, end):
        state = (h ^ token) & 0xFFFFFFFF
        # 4 non-linear mixing rounds
        state = ((state ^ (state >> 15)) * 0x85EBCA6B) & 0xFFFFFFFF
        state = ((state ^ (state >> 13)) * 0xC2B2AE35) & 0xFFFFFFFF
        state = (((state ^ (state >> 16)) + token)) & 0xFFFFFFFF

        state = ((state ^ (state >> 15)) * 0x85EBCA6B) & 0xFFFFFFFF
        state = ((state ^ (state >> 13)) * 0xC2B2AE35) & 0xFFFFFFFF
        state = (((state ^ (state >> 16)) + token)) & 0xFFFFFFFF

        state = ((state ^ (state >> 15)) * 0x85EBCA6B) & 0xFFFFFFFF
        state = ((state ^ (state >> 13)) * 0xC2B2AE35) & 0xFFFFFFFF
        state = (((state ^ (state >> 16)) + token)) & 0xFFFFFFFF

        state = ((state ^ (state >> 15)) * 0x85EBCA6B) & 0xFFFFFFFF
        state = ((state ^ (state >> 13)) * 0xC2B2AE35) & 0xFFFFFFFF
        state = (((state ^ (state >> 16)) + token)) & 0xFFFFFFFF

        if state == TARGET_RESONANCE_TAG:
            return token
    return None

def brute_force_token(prefix_hash: int) -> int:
    # First check if solve_c executable exists for instant solve
    c_solver = os.path.join(os.path.dirname(__file__), "solve_c")
    if os.path.exists(c_solver):
        proc = subprocess.run([c_solver], stdout=subprocess.PIPE, text=True)
        for line in proc.stdout.splitlines():
            if "Recovered Resonance Token:" in line:
                token_hex = line.split(":")[-1].strip()
                return int(token_hex, 16)

    # Otherwise use Python multiprocessing
    total = 0x1000000  # 16,777,216
    workers = max(1, cpu_count())
    chunk_size = total // workers
    tasks = []
    for i in range(workers):
        start = i * chunk_size
        end = total if i == workers - 1 else (i + 1) * chunk_size
        tasks.append((start, end, prefix_hash))

    with Pool(workers) as pool:
        for res in pool.imap_unordered(search_chunk, tasks):
            if res is not None:
                pool.terminate()
                return res
    return None

def main():
    print("=" * 60)
    print("        SOULSTONE BRUTE-FORCE SOLVER")
    print("=" * 60)

    # 1. Recover Sacrifice Name
    sacrifice = recover_sacrifice_name()
    print(f"[*] Recovered Sacrifice Name: {sacrifice}")

    prefix_hash = precompute_prefix_hash(sacrifice)
    print(f"[*] Precomputed Prefix Hash:  0x{prefix_hash:08X}")

    # 2. Brute-Force 24-bit Astral Resonance Token
    print(f"[*] Brute-forcing 24-bit resonance token...")
    t0 = time.time()
    token = brute_force_token(prefix_hash)
    t1 = time.time()

    if token is None:
        print("[-] Brute-force failed to find matching token!")
        sys.exit(1)

    token_str = f"{token:06X}"
    print(f"[+] Found Token: 0x{token_str} in {t1 - t0:.3f} seconds!")

    offering = f"SOUL{{{sacrifice}:{token_str}}}"
    print(f"[+] Formatted Sacred Offering: {offering}")

    # 3. Test offering against binary
    binary_path = os.path.join(os.path.dirname(__file__), "../dist/soulstone")
    if os.path.exists(binary_path):
        print(f"\n[*] Executing {binary_path} with offering...")
        proc = subprocess.run([binary_path], input=(offering + "\n").encode(), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out = proc.stdout.decode()
        print(out.strip())
        if "Flag:" in out:
            print("[+] Challenge successfully solved!")
        else:
            print("[-] Flag verification failed!")
            sys.exit(1)
    else:
        print(f"[*] Binary not found at {binary_path}. Run build.sh first.")

if __name__ == "__main__":
    main()
