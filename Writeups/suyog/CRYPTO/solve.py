#!/usr/bin/env python3
"""
ByteMe CTF - Soul's Locked Message Solve Script
Category: Cryptography
Difficulty: Easy
"""

import sys
from sympy import factorint

# Challenge parameters
n = 6449532267779447351663897013188090145564263455587622461927118526627616204482433356040522957273837936749400700891863976105743563635576474167612348778693883
e = 65537
c = 2158566680867780440751710410606396264856347294813562081688332544610378951560972509642880335284414600125431031093545016412459984599106647039686416700181597

def solve():
    print(f"[*] Modulus bit length: {n.bit_length()} bits")
    print("[*] Factoring n...")
    
    # Factor n into prime factors
    factors = factorint(n)
    primes = list(factors.keys())
    
    if len(primes) < 2:
        print("[-] Could not factor n.")
        return

    p, q = primes[0], primes[1]
    print(f"[+] Found p = {p}")
    print(f"[+] Found q = {q}")

    # Compute Euler's Totient phi(n)
    phi = (p - 1) * (q - 1)
    
    # Compute private decryption exponent d = e^(-1) mod phi(n)
    d = pow(e, -1, phi)
    print(f"[+] Computed private exponent d")

    # Decrypt ciphertext: m = c^d mod n
    m = pow(c, d, n)

    # Convert decrypted integer to bytes
    flag_bytes = m.to_bytes((m.bit_length() + 7) // 8, byteorder="big")
    print(f"\n[+] Flag: {flag_bytes.decode('utf-8', errors='ignore')}")

if __name__ == "__main__":
    solve()
