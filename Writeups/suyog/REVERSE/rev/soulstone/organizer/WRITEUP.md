# SoulStone — Official Challenge Writeup

**Category:** Reverse Engineering  
**Difficulty:** Medium / Hard  
**Theme:** The Altar of Vormir (The Soul Stone)  
**Flag:** `OWASP{a_s0ul_f0r_a_s0ul_v0rm1r_cl1ff_7c8d9e2a}`  
**Sacred Offering:** `SOUL{GAMORA:A73D91}`  

---

## 1. Challenge Overview

Players are provided with a single stripped Linux x86-64 ELF executable: `soulstone`.

```text
╔═══════════════════════════════════════════════════════════════╗
║                      THE ALTAR OF VORMIR                      ║
║                    Trial of the Soul Stone                    ║
╚═══════════════════════════════════════════════════════════════╝

"Welcome, traveler. Many have sought the Stone, but none
 comprehend its price. An everlasting exchange is demanded:
 A soul for a soul.
 Name your true sacrifice and present the Astral Soul Resonance."

Enter Sacred Offering (format: SOUL{<SACRIFICE>:<RESONANCE>}):
> 
```

The goal is to determine the correct `<SACRIFICE>` name and brute-force the 24-bit `<RESONANCE>` token to derive the decryption key for the flag.

---

## 2. Reconnaissance

```bash
$ file soulstone
soulstone: ELF 64-bit LSB executable, x86-64, version 1 (SYSV), statically linked, stripped

$ strings soulstone | grep -iE "OWASP|GAMORA|A73D91"
(No matches found)
```

No plaintext flag or secrets exist in the binary. The flag is stored exclusively as an authenticated ciphertext (`ENCRYPTED_FLAG`).

---

## 3. Static Analysis

Decompiling `main` in Ghidra / IDA Pro / Binary Ninja reveals the verification sequence:

### Phase 1: Input Format Validation
The input string must match `SOUL{<SACRIFICE>:<RESONANCE>}`:
- Starts with `SOUL{` and ends with `}`.
- Contains a colon `:` separating the sacrifice name from a 6-character hexadecimal resonance token.

### Phase 2: Sacrifice Name Verification
Looking at `verify_sacrifice_name`:
```c
int verify_sacrifice_name(const char *name) {
    if (!name || strlen(name) != 6) return 0;
    static const uint8_t xor_keys[6] = {0x5A, 0x6B, 0x7C, 0x8D, 0x9E, 0xAF};
    static const uint8_t mask[6]     = {0x1D, 0x2A, 0x31, 0xC2, 0xCC, 0xEE};
    for (int i = 0; i < 6; i++) {
        if (((uint8_t)name[i] ^ xor_keys[i]) != mask[i]) {
            return 0;
        }
    }
    return 1;
}
```
Unmasking each byte:
- `0x1D ^ 0x5A = 0x47 = 'G'`
- `0x2A ^ 0x6B = 0x41 = 'A'`
- `0x31 ^ 0x7C = 0x4D = 'M'`
- `0xC2 ^ 0x8D = 0x4F = 'O'`
- `0xCC ^ 0x9E = 0x52 = 'R'`
- `0xEE ^ 0xAF = 0x41 = 'A'`

The sacrifice name is **`GAMORA`**.

### Phase 3: The Astral Resonance Function
The 6 hex characters are parsed into a 24-bit unsigned integer `token` ($0 \le token \le \text{0xFFFFFF}$).
The function `soul_resonance` is then invoked:

```c
uint32_t soul_resonance(const char *sacrifice, uint32_t token) {
    uint32_t h = 0x5A17F00D;
    for (const char *p = sacrifice; *p; p++) {
        h = ((h * 31 + (uint8_t)*p) ^ 0x9E3779B9);
    }
    uint32_t state = (h ^ token);
    for (int i = 0; i < 4; i++) {
        state = (state ^ (state >> 15)) * 0x85EBCA6B;
        state = (state ^ (state >> 13)) * 0xC2B2AE35;
        state = (state ^ (state >> 16));
        state = (state + token);
    }
    return state;
}
```
The result is compared against a constant:
```c
if (soul_resonance("GAMORA", token) != 0xE7F841B8) {
    puts("[-] The Altar rumbles: \"The soul resonance is dissonant. The Stone remains sealed.\"");
    return 1;
}
```

---

## 4. Why Brute Force is Required

The `soul_resonance` function employs non-linear bitwise shifts, right shifts, and modular additions across 4 cascading rounds. This makes algebraic inversion analytically unfeasible.

However, the search space is bounded to **24 bits** ($16^6 = 16,777,216$ possibilities).
A multi-threaded Python script or optimized C program can evaluate all 16.7 million states in **under 0.05 seconds** in C, or **~1–2 seconds** in Python.

---

## 5. Brute-Force Implementation

### Fast C Solver:
```c
#include <stdio.h>
#include <stdint.h>

#define TARGET_RESONANCE_TAG 0xE7F841B8U

int main(void) {
    uint32_t h = 0x58F35C68; // precomputed hash for "GAMORA"
    for (uint32_t token = 0; token <= 0xFFFFFF; token++) {
        uint32_t state = (h ^ token);
        for (int i = 0; i < 4; i++) {
            state = (state ^ (state >> 15)) * 0x85EBCA6B;
            state = (state ^ (state >> 13)) * 0xC2B2AE35;
            state = (state ^ (state >> 16)) + token;
        }
        if (state == TARGET_RESONANCE_TAG) {
            printf("[+] Found Token: 0x%06X\n", token);
            break;
        }
    }
    return 0;
}
```

Running the solver immediately reveals:
```text
[+] Found Token: 0xA73D91
```

---

## 6. Cryptographic Gate & Flag Decryption

Once `GAMORA` and `A73D91` are recovered, the program derives:
1. `MasterKey = SHA256("GAMORA:A73D91:VORMIR_SOUL_TITHE_2026")`
2. `ChaChaKey = SHA256(MasterKey + "::CIPHER_KEY")`
3. `ChaChaNonce = SHA256(MasterKey + "::NONCE")[:12]`
4. `HmacKey = SHA256(MasterKey + "::HMAC_KEY")`

The binary checks the HMAC-SHA256 authentication tag over the ciphertext:
If someone patches the `soul_resonance` comparison in GDB or Ghidra without the true key, the HMAC verification fails and ChaCha20 decrypts into random byte garbage.
Only with the exact key `SOUL{GAMORA:A73D91}` does the ChaCha20 cipher yield the plaintext flag:
```text
OWASP{a_s0ul_f0r_a_s0ul_v0rm1r_cl1ff_7c8d9e2a}
```

---

## 7. Flag Recovery

```bash
$ printf "SOUL{GAMORA:A73D91}\n" | ./dist/soulstone
╔═══════════════════════════════════════════════════════════════╗
║                      THE ALTAR OF VORMIR                      ║
║                    Trial of the Soul Stone                    ║
╚═══════════════════════════════════════════════════════════════╝

"Welcome, traveler. Many have sought the Stone, but none
 comprehend its price. An everlasting exchange is demanded:
 A soul for a soul.
 Name your true sacrifice and present the Astral Soul Resonance."

Enter Sacred Offering (format: SOUL{<SACRIFICE>:<RESONANCE>}):
> 
[+] The clouds part above the precipice as an amber radiance engulfs the sky.
[+] A tear falls into the abyss. The everlasting exchange is complete.
[+] You awaken in the shallow waters, holding that which you paid dearly for.
[+] Flag: OWASP{a_s0ul_f0r_a_s0ul_v0rm1r_cl1ff_7c8d9e2a}
```
