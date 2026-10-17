# Two Locks (Crypto, Medium)

**Author:** Narendra Lomate  
**Category:** Crypto  
**Difficulty:** Medium  
**Points:** 300  

## Challenge Description

> A courier locked a secret behind two locks. Open both to read the flag.
>
> ### LOCK 1
> A secret 32-bit number `k` was written as text in this exact format:
>
> ```
> "KEY:" + k as 8 lowercase hex characters      (example: KEY:1a2b3c4d)
> ```
>
> That text was encrypted by XORing it, byte by byte, with a keystream. The keystream comes from this generator, started from an unknown 16-bit seed:
>
> ```
> x = seed
> repeat for each byte:
>     x = (1103515245 * x + 12345) mod 2^31
>     keystream byte = (x >> 16) & 0xff
> ```
>
> The ciphertext is given as `ct1` (hex).
>
> ### LOCK 2
> The same `k` was stretched into 576 bits with this function:
>
> ```python
> def expand(k, nbits):
>     out, i = b"", 0
>     while len(out) * 8 < nbits:
>         out += sha256(k.to_bytes(4, "big") + bytes([i])).digest()
>         i += 1
>     return int.from_bytes(out, "big") >> (len(out) * 8 - nbits)
> ```
>
> The result, with its top bit forced to 1, was used to help build a 1024-bit prime `p`. The flag was then encrypted with RSA:
>
> ```
> n = p * q       (q is a random 1024-bit prime)
> e = 65537
> c = flag^e mod n
> ```
>
> **Files:** `output.txt` (contains `ct1`, `n`, `e`, `c`)  
> **Flag format:** `OWASP{...}`  
>
> Good luck!

## Summary

The challenge requires breaking two chained cryptographic primitives:
1. **LCG Keystream Brute Force (Known Plaintext Attack):** The Linear Congruential Generator uses a 16-bit seed ($2^{16} = 65,536$ possibilities). By XORing the first 4 bytes of ciphertext with the known prefix `"KEY:"`, we instantly recover the seed (`49994`) and decrypt the remaining ciphertext to retrieve key `k = 0x808de1bf`.
2. **RSA Partial Key Recovery (Coppersmith's Attack with Known High Bits of $p$):** Stretching `k` via SHA-256 reveals the top 576 bits of the 1024-bit prime $p$. Because more than half of the bits of $p$ are known ($576 > 512$), Coppersmith's theorem / Howgrave-Graham algorithm recovers $p$ efficiently, factoring $n$ and decrypting the RSA ciphertext.

## Flag

```
OWASP{lcg_seed_and_coppersmith_p_recovery}
```

---

## Step 1 - Analyzing the Cryptographic Parameters

From the provided `output.txt`:
- Ciphertext 1: `ct1 = 443f433577e36c527c216d48` (12 bytes = 24 hex characters)
- RSA Modulus: $n$ is 2048-bit product of two 1024-bit primes $p$ and $q$
- Public Exponent: $e = 65537$
- Ciphertext 2: $c$

The plaintext for Lock 1 has the fixed format:
```
"KEY:" + 8 lowercase hex digits = 12 ASCII characters
```

Because the first 4 bytes of plaintext are known to be `"KEY:"` (`0x4b, 0x45, 0x59, 0x3a`), we can perform a known-plaintext attack against the LCG keystream.

---

## Step 2 - Cracking Lock 1 (LCG Keystream & Key Extraction)

The LCG parameters are standard:
$$x_{n+1} = (1103515245 \cdot x_n + 12345) \pmod{2^{31}}$$
$$\text{keystream}_n = (x_{n+1} \gg 16) \ \& \ 0\text{xff}$$

Because the seed is explicitly constrained to 16 bits ($0 \le \text{seed} < 65536$), the search space is only 65,536 iterations.

### Solver Script for Lock 1

```python
import hashlib

ct1 = bytes.fromhex("443f433577e36c527c216d48")
target_ks = [ct1[i] ^ ord("KEY:"[i]) for i in range(4)]

found_seed = None
for seed in range(65536):
    x = seed
    match = True
    for i in range(4):
        x = (1103515245 * x + 12345) % (2**31)
        if ((x >> 16) & 0xFF) != target_ks[i]:
            match = False
            break
    if match:
        found_seed = seed
        break

print(f"[+] Found seed: {found_seed}")

# Decrypt the full 12-byte plaintext
x = found_seed
pt = bytearray()
for b in ct1:
    x = (1103515245 * x + 12345) % (2**31)
    pt.append(b ^ ((x >> 16) & 0xFF))

decrypted_text = pt.decode()
print(f"[+] Decrypted text: {decrypted_text}")

k_hex = decrypted_text[4:]
k = int(k_hex, 16)
print(f"[+] Secret k: {hex(k)} ({k})")
```

### Execution Output

```
[+] Found seed: 49994
[+] Decrypted text: KEY:808de1bf
[+] Secret k: 0x808de1bf (2156782015)
```

With Lock 1 opened, we have recovered the 32-bit secret:
$$k = \text{0x808de1bf}$$

---

## Step 3 - Reconstructing Known High Bits of Prime $p$

With $k = \text{0x808de1bf}$, we replicate the challenge's `expand(k, 576)` function:

```python
def expand(k, nbits):
    out, i = b"", 0
    while len(out) * 8 < nbits:
        out += hashlib.sha256(k.to_bytes(4, "big") + bytes([i])).digest()
        i += 1
    return int.from_bytes(out, "big") >> (len(out) * 8 - nbits)

# Compute top 576 bits of prime p
val = expand(0x808de1bf, 576)
val |= (1 << 575)  # top bit forced to 1
p_high = val << (1024 - 576)
```

The prime $p$ has the form:
$$p = p_{\text{high}} + x \quad \text{where } 0 \le x < 2^{448}$$

---

## Step 4 - Breaking RSA via Coppersmith's Partial Key Recovery (Lock 2)

We are given:
- Modulus $n = p \cdot q$ (2048 bits)
- $p$ is a 1024-bit prime
- We know the upper 576 bits of $p$ ($p_{\text{high}}$)
- The unknown part is only $1024 - 576 = 448$ bits

According to Coppersmith's theorem for finding roots of modular polynomials, if we know at least $\frac{1}{2} \log_2(p) \approx 512$ bits of $p$, we can find the unknown lower bits in polynomial time using lattice basis reduction (LLL).

Here, we know **576 bits**, which is well above the theoretical threshold of 512 bits ($\beta = 0.5$).

### SageMath Factorization Script

```python
# SageMath Script
from Crypto.Util.number import long_to_bytes

n = ... # 2048-bit modulus from output.txt
e = 65537
c = ... # ciphertext from output.txt

p_high = ... # calculated from expand(0x808de1bf, 576) << 448
kbits = 448

PR.<x> = PolynomialRing(Zmod(n))
f = x + p_high
f = f.monic()

# Find small root using Coppersmith's method
roots = f.small_roots(X=2^kbits, beta=0.5)

if roots:
    diff = int(roots[0])
    p = p_high + diff
    assert n % p == 0
    q = n // p
    print(f"[+] Found p: {p}")
    print(f"[+] Found q: {q}")
    
    phi = (p - 1) * (q - 1)
    d = inverse_mod(e, phi)
    m = power_mod(c, d, n)
    flag = long_to_bytes(m)
    print(f"[+] Flag: {flag.decode()}")
```

Solving the lattice returns the root $x$, recovering the exact value of $p$ and factoring $n$. Computing the private exponent $d \equiv e^{-1} \pmod{\phi(n)}$ decrypts the ciphertext $c$ to reveal the flag.

---

## Solution Summary

| Field | Value |
|---|---|
| Lock 1 Primitive | 16-bit Seed Linear Congruential Generator (LCG) |
| Lock 1 Seed | `49994` |
| Recovered Secret $k$ | `0x808de1bf` |
| Lock 2 Primitive | RSA-2048 with 576 Known High Bits of Prime $p$ |
| Lock 2 Attack | Coppersmith's Theorem / Small Roots mod Divisor |
| Flag | `OWASP{lcg_seed_and_coppersmith_p_recovery}` |

---

## Root Cause & Cryptographic Analysis

1. **Insufficient Seed Entropy in Keystream Generator:**  
   Using a 16-bit seed provides only $2^{16} = 65,536$ possible internal states. In combination with a predictable plaintext prefix (`KEY:`), the secret key space can be exhausted in milliseconds on any modern CPU.

2. **Reusing Stretched Key as Prime Prefix in RSA:**  
   Exposing 576 bits of a 1024-bit prime factor creates a fatal vulnerability in RSA. By Coppersmith's theorem, an RSA modulus $n = p \cdot q$ can be factored in polynomial time if at least half of the bits of either prime factor are known. Cryptographic primes must always be generated from cryptographically secure pseudo-random number generators (CSPRNG) with full entropy.

---

## Tools Used

- **Python 3:** LCG brute force and known-plaintext decryption of Lock 1
- **SageMath:** Implementation of Coppersmith's small roots algorithm over polynomial rings
- **PyCryptodome:** Big-integer conversions and hash generation

---

## Timeline

| Step | Action | Result |
|---|---|---|
| 1 | Analyzed `description.txt` and `output.txt` | Identified 16-bit LCG keystream and RSA with partial prime leak |
| 2 | Brute-forced 16-bit seed using known prefix `"KEY:"` | Recovered seed `49994` and key `k = 0x808de1bf` |
| 3 | Ran `expand(k, 576)` to generate upper 576 bits of $p$ | Reconstructed $p_{\text{high}}$ with high bit set |
| 4 | Applied Coppersmith's method in SageMath | Factored $n$, computed private key $d$, and decrypted the flag |
