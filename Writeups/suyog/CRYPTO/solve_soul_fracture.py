#!/usr/bin/env python3
"""
ByteMe CTF - Soul Fracture Solver
Category: Cryptography
Difficulty: Hard
"""

import re
import hashlib
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
FRAGMENT_DIR = SCRIPT_DIR / "resources" / "fragments"
if not FRAGMENT_DIR.exists():
    FRAGMENT_DIR = Path("soul_fracture/fragments")
if not FRAGMENT_DIR.exists():
    FRAGMENT_DIR = Path("fragments")

def ror8(x, n):
    n %= 8
    return ((x >> n) | (x << (8 - n))) & 0xff

def nibble_swap(x):
    return ((x & 0x0f) << 4) | ((x & 0xf0) >> 4)

def derive_master_key(chain, fragments):
    material = "|".join(fragments[i]["memory"] for i in chain).encode()
    h = hashlib.sha256(material).digest()
    for _ in range(1337):
        h = hashlib.sha256(h + material).digest()
    return h

def decrypt(data, key, chain):
    out = bytearray()
    for i, byte in enumerate(data):
        k = key[i % len(key)]
        chain_val = chain[i % len(chain)]
        
        x = byte ^ (((i * 31) + chain_val) & 0xff)
        x = nibble_swap(x)
        x = ror8(x, (k + chain_val + i) % 8)
        x ^= (chain_val * 17) & 0xff
        x ^= k
        out.append(x)
    return bytes(out)

def parse_fragment(path):
    text = path.read_text(encoding="utf-8")
    def get(name):
        return re.search(rf"^{name}\s*:\s*(.+)$", text, re.MULTILINE).group(1).strip()
    return {
        "id": int(get("fragment_id")),
        "memory": get("memory"),
        "resonance": int(get("resonance")),
        "echo": int(get("echo")),
        "payload": bytes.fromhex(get("soul_data")),
    }

def find_hamiltonian_cycles(fragments):
    adj = {a["id"]: [] for a in fragments.values()}
    for a in fragments.values():
        for b in fragments.values():
            if a["id"] != b["id"] and a["echo"] == b["resonance"]:
                adj[a["id"]].append(b["id"])

    cycles = []
    def dfs(path, visited):
        if len(path) == 24:
            if path[0] in adj[path[-1]]:
                cycles.append(path[:])
            return
        cur = path[-1]
        for nxt in adj[cur]:
            if nxt not in visited:
                dfs(path + [nxt], visited | {nxt})

    # Fix node 0 as representative member of any full 24-node cycle
    dfs([0], {0})
    return cycles

def main():
    if not FRAGMENT_DIR.exists():
        print(f"[-] Directory {FRAGMENT_DIR} not found. Please extract fragments.")
        return

    fragments = {f["id"]: f for f in (parse_fragment(p) for p in sorted(FRAGMENT_DIR.glob("fragment_*.sf")))}
    print(f"[+] Loaded {len(fragments)} fragments.")

    cycles = find_hamiltonian_cycles(fragments)
    print(f"[+] Discovered {len(cycles)} candidate Hamiltonian cycle topologies.")

    print("[*] Testing cycle rotations against flag header...")
    for cyc in cycles:
        for rot in range(len(cyc)):
            chain = cyc[rot:] + cyc[:rot]
            memories = [fragments[i]["memory"] for i in chain]
            key = derive_master_key(chain, fragments)
            ciphertext = b"".join(fragments[i]["payload"] for i in chain)
            plaintext = decrypt(ciphertext, key, chain)
            
            if b"OWASP{" in plaintext:
                print(f"[+] Recovered Soul chain: {' -> '.join(f'{x:02d}' for x in chain)}")
                print(f"[+] Memory sequence: {' -> '.join(memories)}")
                print(f"[+] Derived key: {key.hex()}")
                print(f"[+] Reassembled ciphertext: {ciphertext.hex()}")
                print(f"[+] Decrypted plaintext: {plaintext}")
                print("\n" + "=" * 41)
                flag = re.search(rb"OWASP\{[^}]+\}", plaintext).group().decode()
                print(f"FLAG: {flag}")
                print("=" * 41)
                return

    print("[-] No valid decryption recovered.")

if __name__ == "__main__":
    main()
