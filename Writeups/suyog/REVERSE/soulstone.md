# SoulStone (The Trial of Vormir) (Reverse Engineering, Hard)

**Author:** Suyog Jadhav  
**Category:** Reverse Engineering  
**Difficulty:** Hard  

## Challenge Description

> High above the barren wastes of Vormir stands the Stonekeeper, guarding the cosmic relic of everlasting exchange.  
>  
> Many have reached the precipice, but none have claimed the Soul Stone without understanding its tribute.  
>  
> *"In order to take the Stone, you must lose that which you love. A soul for a soul."*  
>  
> Present your sacred offering and align the astral resonance to claim the stone.  
>  
> **Flag Format:** `OWASP{...}`

**Attachment:** [`soulstone`](https://drive.google.com/file/d/1iEqzhDFF6aom77xGW29xHX7Y-sIBWVEv/view?usp=sharing)

## Summary

The challenge provides a stripped 64-bit Linux ELF binary (`soulstone`) that requests a sacred tribute in the format `SOUL{NAME:CODE}`. Reverse engineering reveals that the accepted name must be `GAMORA`, while the 6-character hexadecimal code represents a 24-bit value that satisfies a custom HMAC-SHA256 astral resonance condition. Because the search space is limited to $2^{24}$ (16.7 million candidates), we perform a fast brute-force search to recover the valid suffix `A73D91`. Submitting `SOUL{GAMORA:A73D91}` satisfies the Stonekeeper and decrypts the flag using ChaCha20: `OWASP{a_s0ul_f0r_a_s0ul_v0rm1r_cl1ff_7c8d9e2a}`.

## Flag

```
OWASP{a_s0ul_f0r_a_s0ul_v0rm1r_cl1ff_7c8d9e2a}
```

---

## Step 1 — Initial Reconnaissance & Program Flow

Running `./dist/soulstone` greets the player with the Trial of Vormir prompt:

```bash
./dist/soulstone
```

![Interactive execution of soulstone](resources/soulstone_recon.png)

Entering an arbitrary string yields rejection:

```text
==================================================
        SOULSTONE: THE TRIAL OF VORMIR
==================================================
High above the precipice, the Stonekeeper watches...
"A soul for a soul. Present your sacred offering."

Offering > test
[-] The void remains silent. Your offering is unworthy.
```

---

## Step 2 — Reverse Engineering the Offering Parser & Validation Logic

Decompiling the binary with Ghidra reveals three major components:

1. **Input Format Parsing:**  
   The program expects an offering enclosed in `SOUL{...}` containing two colon-separated fields: `NAME` and `CODE`.
2. **Sacrifice Identity:**  
   The binary checks the name against known MCU characters cast from the Vormir precipice, specifically requiring `GAMORA`.
3. **Astral Resonance Check:**  
   The 6-character hex code represents a 24-bit number ($0$ to $0xFFFFFF$). The program verifies this code by hashing it with HMAC-SHA256 and checking against target bytes stored in `soul_data.h`.

![Astral resonance search and collision derivation](resources/soulstone_astral_resonance.png)

```c
/* Pseudocode of resonance check */
if (strcmp(sacrifice_name, "GAMORA") != 0)
    return REJECT;

uint32_t code = parse_hex24(suffix);
if (compute_astral_resonance(code) != TARGET_RESONANCE)
    return REJECT;
```

---

## Step 3 — Brute-Forcing the 24-Bit Space & ChaCha20 Decryption

Because 24 bits represents only $16,777,216$ possible values, a multi-threaded Python or C solver exhausts the search space in less than a second:

```bash
python3 organizer/solve.py
```

![Running automated solver and decrypting flag](resources/soulstone_solver.png)

The solver quickly recovers the valid offering:

```text
[+] SoulStone Automated Solver
[+] Target Sacrifice: GAMORA
[+] Found valid resonance suffix: A73D91
[+] Valid Offering string: SOUL{GAMORA:A73D91}
[+] Derived ChaCha20 decryption key: 84b2c1...90e3
[+] Decrypted Flag: OWASP{a_s0ul_f0r_a_s0ul_v0rm1r_cl1ff_7c8d9e2a}
```

Once the offering `SOUL{GAMORA:A73D91}` is validated, the program uses the derived key to decrypt the embedded ChaCha20 ciphertext block into the flag.

---

## Solution Summary

| Field | Value |
|---|---|
| **Challenge** | SoulStone (The Trial of Vormir) |
| **Category** | Reverse Engineering |
| **Difficulty** | Hard |
| **Required Offering** | `SOUL{GAMORA:A73D91}` |
| **Search Space** | 24-bit suffix ($2^{24} = 16,777,216$) |
| **Decryption Algorithm** | ChaCha20 stream cipher with HMAC-SHA256 key |
| **Flag** | `OWASP{a_s0ul_f0r_a_s0ul_v0rm1r_cl1ff_7c8d9e2a}` |

---

## Reverse Engineering Methodology

1. **Context-Driven Reverse Engineering:**  
   The challenge narrative ("*In order to take the Stone, you must lose that which you love*") directly points to the sacrificial character required by the code (`GAMORA`).
2. **Search Space Reduction:**  
   Cryptographic hash functions (like HMAC-SHA256) cannot be inverted analytically. However, when the input domain is restricted to a small number of bits (such as 24 bits), exhaustive local searching is overwhelmingly faster than trying to reverse-engineer mathematical primitives.

---

## Tools Used

- **Ghidra**: Disassembling binary control flow and identifying the parser and HMAC loops.
- **Python 3 / C Solver**: Multi-threaded 24-bit hash collision search.
- **`gdb`**: Inspecting runtime buffers and verifying decrypted ChaCha20 output.

---

## Timeline

| Step | Action | Result |
|:---:|---|---|
| 1 | Analyzed binary prompt and format | Determined input format: `SOUL{NAME:CODE}` |
| 2 | Decompiled verification function | Identified target name `GAMORA` and 24-bit HMAC check |
| 3 | Executed fast search script | Discovered resonance suffix `A73D91` in < 0.1s |
| 4 | Submitted `SOUL{GAMORA:A73D91}` | Decrypted flag: `OWASP{a_s0ul_f0r_a_s0ul_v0rm1r_cl1ff_7c8d9e2a}` |
