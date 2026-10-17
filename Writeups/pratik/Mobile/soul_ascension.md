# Soul Ascension (Rev / Mobile, Expert)

**Author:** Pratik Jadhav  
**Category:** Mobile / Android Reverse Engineering  
**Difficulty:** Expert  

## Challenge Description

> Reverse engineer the Android application and its native guardian library to awaken the Fifth Guardian.  
> Four guardians guard the gate within the application's Dalvik bytecode; their awakened spirits forge a transcript chain that unlocks the final seal hidden deep within native ARM machine code.

**Given:** Android APK artifact (`SoulAscension.apk`).  
**Network Requirements:** None (100% offline, standalone reverse engineering).  
**Flag Format:** `OWASP{...}` (or `FLAG{...}`)

## Summary

Soul Ascension is an advanced two-tier Android reverse engineering challenge combining Kotlin bytecode logic with native C++ JNI cryptography. The challenge requires solvers to defeat four distinct algorithmic input verifiers inside `MainActivity.kt` to awaken Guardians I through IV. Each correct answer generates an encoded state segment that forms an ordered cryptographic transcript: `A9yromem:B4moon:C2tpvm:D82620`. This transcript is passed into `libguardian.so` via JNI, where a custom key-derivation routine mutates four 32-bit seeds to produce an XTEA key. The native engine then executes an XTEA-CBC block decryption with PKCS#7 unpadding and FNV-1a integrity validation to release the final flag.

## Flag

```
OWASP{s0ul_4sc3nd3d_th3_f1fth_guardian}
```

---

## Step 1 — APK Decompilation & Activity Structure

We load `SoulAscension.apk` into **JADX-GUI**:

```bash
jadx-gui SoulAscension.apk
```

Inspecting the package structure under `com.byteme.soulascension`:
- `MainActivity.kt` — Manages the user interface, progression state, guardian input validation, and native bridge invocation.
- `lib/` directory — Contains `libguardian.so` precompiled for `arm64-v8a`, `armeabi-v7a`, `x86`, and `x86_64`.

The companion object in `MainActivity` loads the native library on startup:
```kotlin
companion object {
    init { 
        System.loadLibrary("guardian") 
    }
}
private external fun nativeFinal(chain: String): String
```

## Step 2 — Reversing the Kotlin Input Verifiers (`MainActivity.kt`)

Progression through the challenge requires satisfying four input verifiers in `verify(level, raw)`:

```kotlin
private fun verify(level: Int, raw: String): Boolean {
    val s = raw.trim()
    return when (level) {
        0 -> s.length == 6 && mix(s) == 0xAE91
        1 -> s.lowercase().reversed() == "noom"
        2 -> {
            val x = s.lowercase()
            x.map { (it.code xor 7).toChar() }.joinToString("") == "thrk"
        }
        3 -> {
            s.length == 4 && s.all { it in '0'..'9' } &&
                s.mapIndexed { i, c -> (c.code - 48) xor (i + 3) }.sum() == 12
        }
        else -> false
    }
}
```

Let us reverse each guardian step by step:

### Guardian I — MEMORY (`level == 0`)
- **Constraint:** String length must be 6, and `mix(s) == 0xAE91`.
- Looking at `mix(s)`:
  ```kotlin
  private fun mix(s: String): Int {
      var x = 0x1357
      for (c in s) {
          x = ((x shl 5) xor c.code xor (x ushr 3)) and 0xFFFF
      }
      return x
  }
  ```
- Clue from UI prompt: *"Guardian I — MEMORY: Recover the forgotten word."*
- Testing the word `"memory"`:
  - Iteration 1 ('m' = 109): `x = ((0x1357 << 5) ^ 109 ^ (0x1357 >> 3)) & 0xFFFF`
  - Continuing through `'e'`, `'m'`, `'o'`, `'r'`, `'y'` yields `0xAE91` exactly!
- **Answer I:** `memory`

### Guardian II — SHADOW (`level == 1`)
- **Constraint:** `s.lowercase().reversed() == "noom"`.
- Reversing `"noom"` gives `"moon"`.
- **Answer II:** `moon`

### Guardian III — CIPHER (`level == 2`)
- **Constraint:** Each lowercase character XORed with 7 equals `"thrk"`.
- Because XOR is an involution ($c = enc \oplus 7$):
  - `'t' ^ 7 = 116 ^ 7 = 115 = 's'`
  - `'h' ^ 7 = 104 ^ 7 = 111 = 'o'`
  - `'r' ^ 7 = 114 ^ 7 = 117 = 'u'`
  - `'k' ^ 7 = 107 ^ 7 = 108 = 'l'`
- **Answer III:** `soul`

### Guardian IV — TIME (`level == 3`)
- **Constraint:** 4 ASCII digits such that $\sum_{i=0}^3 ((d_i - 48) \oplus (i + 3)) = 12$.
- The year of the competition is 2026. Testing `"2026"`:
  - $i=0: 2 \oplus (0 + 3) = 2 \oplus 3 = 1$
  - $i=1: 0 \oplus (1 + 3) = 0 \oplus 4 = 4$
  - $i=2: 2 \oplus (2 + 3) = 2 \oplus 5 = 7$
  - $i=3: 6 \oplus (3 + 3) = 6 \oplus 6 = 0$
  - Sum: $1 + 4 + 7 + 0 = 12$!
- **Answer IV:** `2026`

## Step 3 — Transcript Construction

When each guardian is awakened, `stateFor(level, answer)` encodes the answer into a state marker:

```kotlin
private fun stateFor(level: Int, answer: String): String {
    val v = answer.trim().lowercase()
    return when (level) {
        0 -> "A9" + v.reversed()                               // "A9" + "yromem"
        1 -> "B4" + v                                          // "B4" + "moon"
        2 -> "C2" + v.map { (it.code + 1).toChar() }.joinToString("") // "C2" + "tpvm"
        3 -> "D8" + v.chunked(2).reversed().joinToString("")   // "D8" + "2620"
        else -> "X"
    }
}
```

Evaluating each segment:
1. `level 0` (`memory`): `"A9" + "yromem"` $\rightarrow$ `A9yromem`
2. `level 1` (`moon`): `"B4" + "moon"` $\rightarrow$ `B4moon`
3. `level 2` (`soul`): Shift each ASCII character by +1:
   - `'s' + 1 = 't'`, `'o' + 1 = 'p'`, `'u' + 1 = 'v'`, `'l' + 1 = 'm'`
   - `"C2" + "tpvm"` $\rightarrow$ `C2tpvm`
4. `level 3` (`2026`): Split into 2-digit chunks `["20", "26"]` and reverse `["26", "20"]`:
   - `"D8" + "2620"` $\rightarrow$ `D82620`

Joining with colons (`states.joinToString(":")`):
```text
A9yromem:B4moon:C2tpvm:D82620
```

This composite transcript is passed to `nativeFinal(chain)`.

## Step 4 — Native Reverse Engineering (`libguardian.so`)

Opening `libguardian.so` in **Ghidra**, we inspect `Java_com_byteme_soulascension_MainActivity_nativeFinal`.

### 1. Marker Order Verification
The library scans the transcript to ensure `"A9"`, `"B4"`, `"C2"`, and `"D8"` appear in sequential order:
```c
bool hasOrderedGuardians(const std::string& chain) {
    const char* guardians[] = {"A9", "B4", "C2", "D8"};
    size_t offset = 0;
    for (const char* guardian : guardians) {
        offset = chain.find(guardian, offset);
        if (offset == std::string::npos) return false;
        offset += 2;
    }
    return true;
}
```

### 2. XTEA Key Derivation (`deriveKey`)
The function initializes four 32-bit unsigned key words:
```c
key[0] = 0xC3A5C85Cu;
key[1] = 0xB492B66Fu;
key[2] = 0x9AE16A3Bu;
key[3] = 0x7F4A7C15u;
```

For each character in the transcript string (index `i`):
```c
for (size_t i = 0; i < chain.size(); ++i) {
    const size_t slot = i & 3u;
    const uint32_t next = key[(slot + 1u) & 3u];
    const uint32_t byte = static_cast<unsigned char>(chain[i]);
    key[slot] ^= byte + 0x9E3779B9u + (next << 6) + (next >> 2);
    key[slot] = rotateLeft(key[slot], static_cast<unsigned int>((i % 23u) + 5u));
    key[slot] += static_cast<uint32_t>(i) * 0x045D9F3Bu;
}
```

### 3. Ciphertext Decryption & CBC Mode
The binary embeds a 40-byte ciphertext array and an 8-byte initialization vector (IV):
```c
const uint8_t ciphertext[] = {
    31, 158, 20, 122, 141, 137, 168, 45, 240, 106, 95, 245, 69, 77,
    84, 118, 196, 207, 161, 254, 153, 120, 188, 149, 5, 239, 219, 28,
    41, 153, 245, 94, 96, 9, 107, 183, 189, 3, 93, 45
};
const uint8_t iv[] = {83, 65, 124, 25, 45, 136, 196, 6};
```

The decryption routine is standard **XTEA** in Cipher Block Chaining (CBC) mode with 32 rounds ($sum = 32 \times \delta$ descending).

### 4. Integrity Verification & Unpadding
After CBC decryption:
1. Validates standard PKCS#7 padding: `padding = plaintext.back()`.
2. Resizes plaintext by stripping the padding bytes.
3. Computes the 32-bit FNV-1a checksum over the unpadded plaintext:
   ```c
   uint32_t checksum(const std::vector<uint8_t>& bytes) {
       uint32_t value = 0x811C9DC5u;
       for (uint8_t byte : bytes) {
           value = (value ^ byte) * 0x01000193u;
       }
       return value;
   }
   ```
4. Asserts `checksum == 0x757052CAu`.
5. Returns the null-terminated decrypted string.

## Step 5 — Standalone Reimplementation in Python

We implement the complete key derivation and XTEA-CBC decryption in a standalone Python script (`solve_ascension.py`):

```python
kDelta = 0x9E3779B9

def rotl32(v, c):
    return ((v << c) | (v >> (32 - c))) & 0xFFFFFFFF

def derive_key(transcript):
    key = [0xC3A5C85C, 0xB492B66F, 0x9AE16A3B, 0x7F4A7C15]
    for i, byte in enumerate(transcript.encode('utf-8')):
        slot = i & 3
        next_val = key[(slot + 1) & 3]
        key[slot] ^= (byte + kDelta + (next_val << 6) + (next_val >> 2)) & 0xFFFFFFFF
        key[slot] = rotl32(key[slot], (i % 23) + 5)
        key[slot] = (key[slot] + i * 0x045D9F3B) & 0xFFFFFFFF
    return key

def decrypt_xtea_block(block, key):
    left = block[0] | (block[1] << 8) | (block[2] << 16) | (block[3] << 24)
    right = block[4] | (block[5] << 8) | (block[6] << 16) | (block[7] << 24)
    sum_val = (kDelta * 32) & 0xFFFFFFFF
    
    for _ in range(32):
        t_r = ((((left << 4) ^ (left >> 5)) + left) ^ (sum_val + key[(sum_val >> 11) & 3])) & 0xFFFFFFFF
        right = (right - t_r) & 0xFFFFFFFF
        sum_val = (sum_val - kDelta) & 0xFFFFFFFF
        t_l = ((((right << 4) ^ (right >> 5)) + right) ^ (sum_val + key[sum_val & 3])) & 0xFFFFFFFF
        left = (left - t_l) & 0xFFFFFFFF
        
    res = bytearray(8)
    for i in range(4):
        res[i] = (left >> (i * 8)) & 0xFF
        res[i + 4] = (right >> (i * 8)) & 0xFF
    return res

def solve():
    transcript = "A9yromem:B4moon:C2tpvm:D82620"
    print(f"[*] Transcript: {transcript}")
    
    key = derive_key(transcript)
    print(f"[*] Derived XTEA Key: {[hex(k) for k in key]}")
    
    ciphertext = bytes([
        31, 158, 20, 122, 141, 137, 168, 45, 240, 106, 95, 245, 69, 77,
        84, 118, 196, 207, 161, 254, 153, 120, 188, 149, 5, 239, 219, 28,
        41, 153, 245, 94, 96, 9, 107, 183, 189, 3, 93, 45
    ])
    iv = bytes([83, 65, 124, 25, 45, 136, 196, 6])
    
    prev = bytearray(iv)
    plaintext = bytearray()
    for offset in range(0, len(ciphertext), 8):
        chunk = ciphertext[offset:offset+8]
        dec = decrypt_xtea_block(chunk, key)
        plain_chunk = bytearray(dec[i] ^ prev[i] for i in range(8))
        plaintext.extend(plain_chunk)
        prev = bytearray(chunk)
        
    padding = plaintext[-1]
    unpadded = plaintext[:-padding]
    flag = unpadded.decode('utf-8')
    print(f"\n[🏆] Plaintext Flag: {flag}\n")

if __name__ == "__main__":
    solve()
```

## Step 6 — Execution & Flag Extraction

Running the Python script:

```text
$ python solve_ascension.py
[*] Transcript: A9yromem:B4moon:C2tpvm:D82620
[*] Derived XTEA Key: ['0x296e838e', '0x18151fd4', '0x2bf7b750', '0x81e28509']

[🏆] Plaintext Flag: OWASP{s0ul_4sc3nd3d_th3_f1fth_guardian}
```

The ciphertext decrypts to:
```
OWASP{s0ul_4sc3nd3d_th3_f1fth_guardian}
```

Entering the answers (`memory`, `moon`, `soul`, `2026`) directly into the Android application interface on a device or emulator also awakens the Fifth Guardian and renders the flag on screen:

![Soul Ascension Solved Interface](resources/soul_ascension_solved.png)

## Solution Summary

| Parameter | Value |
|---|---|
| Target APK | `SoulAscension.apk` (`com.byteme.soulascension`) |
| Guardian I Answer | `memory` (`mix() == 0xAE91`) |
| Guardian II Answer | `moon` (reversed `"noom"`) |
| Guardian III Answer | `soul` (`c ^ 7 == "thrk"`) |
| Guardian IV Answer | `2026` ($\sum (d_i \oplus (i+3)) == 12$) |
| Cryptographic Transcript | `A9yromem:B4moon:C2tpvm:D82620` |
| Native Cipher | XTEA in CBC Mode (32 rounds, IV `53 41 7C 19 2D 88 C4 06`) |
| Checksum Verification | FNV-1a Checksum `0x757052CAu` |
| Flag | `OWASP{s0ul_4sc3nd3d_th3_f1fth_guardian}` |

## Root Cause & Reverse Engineering Takeaways

1. **Multi-Stage Defense-in-Depth:** The challenge demonstrates how complex software systems split logic across higher-level interpreted environments (Kotlin on ART) and unmanaged native code (C++ in `.so` shared objects) to obscure critical business logic.
2. **Deterministic State Derivation:** Because the cryptographic keys were deterministically derived from user input transcript characters, breaking the higher-level verifiers provided the exact key material needed to unlock the native stage without requiring complex mathematical attacks on XTEA itself.
3. **Static vs. Dynamic Analysis:** While a solver could solve the challenge entirely statically through Ghidra and JADX, dynamic instrumentation (e.g. using **Frida**) to hook `nativeFinal` or dump the transcript at runtime is an equally viable shortcut.

## Tools Used

- **JADX-GUI** — Decompiling Kotlin bytecode and reversing guardian logic.
- **Ghidra** — Disassembling ARM64 ELF shared object (`libguardian.so`) and analyzing JNI functions.
- **Python 3** — Pure Python reimplementation of the key derivation and XTEA-CBC cipher.
- **Android Studio / Emulator** — Runtime application verification.

## Timeline

| Step | Action | Result |
|---|---|---|
| 1 | Decompiled `MainActivity.kt` with JADX | Identified 4 guardian input verifiers and JNI `nativeFinal` |
| 2 | Reversed Guardian I (`memory`) | Solved `mix()` hash against `0xAE91` |
| 3 | Reversed Guardians II, III, IV | Recovered `moon`, `soul`, and `2026` via string and XOR reversing |
| 4 | Assembled state transcript | Formed `A9yromem:B4moon:C2tpvm:D82620` |
| 5 | Analyzed `libguardian.so` in Ghidra | Extracted XTEA-CBC decryption, derived keys, and IV |
| 6 | Decrypted ciphertext | Recovered `OWASP{s0ul_4sc3nd3d_th3_f1fth_guardian}` |
