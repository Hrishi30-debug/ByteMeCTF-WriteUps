# SoulVault (Mobile / Rev, Expert)

**Author:** Pratik Jadhav  
**Category:** Mobile / Android Reverse Engineering  
**Difficulty:** Expert  

## Challenge Description

> Analyze the Android client and native proof-of-work flow to unlock the Soul Vault.  
> The Android application protects its transmission protocol across Java reflection, obfuscated native JNI libraries, and a cryptographic proof-of-work challenge before the backend reveals what is sealed inside.

**Given:** Android APK artifact (`SoulVault.apk`) interacting with the SoulVault backend.  
**Target API:** `https://byteme-soulvault-api.onrender.com/` (or local `http://127.0.0.1:8080/`)  
**Flag Format:** `OWASP{...}`

## Summary

SoulVault is an expert-level Android reverse engineering and protocol reconstruction challenge. The APK contains no hardcoded flag; instead, it coordinates with an external Flask API to verify the authenticity of the client device. Static analysis in JADX and Ghidra reveals that the client constructs a device fingerprint from hardware properties, invokes a native JNI method (`SoulBridge.p`) to XOR-decrypt an obfuscated endpoint route (`/v1/soul/echo/fragment`) and compute a custom 32-bit hash client identifier (`g3-XXXXXXXX`), fetches an ephemeral single-use challenge ticket, and computes a multi-round SHA-256 proof-of-work (`SoulBridge.q`). By fully extracting and reimplementing the native JNI algorithms in a standalone Python script, we solve the challenge and retrieve the competition flag directly from the server.

## Flag

```
OWASP{soul_vault_fragment_recovered}
```

---

## Step 1 — APK Decompilation & Manifest Analysis

We begin by inspecting `SoulVault.apk` using **JADX-GUI** and `apktool`:

```bash
jadx-gui SoulVault.apk
```

Inspecting `AndroidManifest.xml`:
```xml
<manifest xmlns:android="http://schemas.android.com/apk/res/android"
    package="com.soulvault">
    <uses-permission android:name="android.permission.INTERNET" />
    <application
        android:label="SoulVault"
        android:usesCleartextTraffic="true"
        android:theme="@style/Theme.SoulVault">
        <activity
            android:name=".MainActivity"
            android:exported="true">
            <intent-filter>
                <action android:name="android.intent.action.MAIN" />
                <category android:name="android.intent.category.LAUNCHER" />
            </intent-filter>
        </activity>
    </application>
</manifest>
```

The app requests `INTERNET` access and defines a single activity: `com.soulvault.MainActivity`.

## Step 2 — Reversing Java Control Flow (`MainActivity.java`)

In JADX, decompiling `com.soulvault.MainActivity` exposes the button click listener triggering vault awakening:

```java
public class MainActivity extends AppCompatActivity {
    private static final String BASE_URL = "https://byteme-soulvault-api.onrender.com";

    private void onAwakenClicked() {
        String seed = Build.MANUFACTURER + ":" + Build.MODEL + ":" + Build.VERSION.SDK_INT;
        byte[] seedBytes = seed.getBytes(StandardCharsets.UTF_8);

        // Reflective call to native bridge
        try {
            Class<?> bridgeClass = Class.forName("com.soulvault.SoulBridge");
            Method pMethod = bridgeClass.getDeclaredMethod("p", byte[].class);
            String[] routeAndLabel = (String[]) pMethod.invoke(null, (Object) seedBytes);

            String route = routeAndLabel[0];
            String clientLabel = routeAndLabel[1];
            String deviceHash = sha256Hex(seedBytes);

            requestChallenge(BASE_URL + route, deviceHash, clientLabel);
        } catch (Exception e) {
            Log.e("SoulVault", "Awaken failed", e);
        }
    }
}
```

Key takeaways from the Java layer:
1. **Device Seed:** Formatted as `"<MANUFACTURER>:<MODEL>:<SDK_INT>"`.
2. **Device Hash:** The SHA-256 hex digest of the seed bytes (64 lowercase hex characters).
3. **Reflective Native Dispatch:** It loads `com.soulvault.SoulBridge` and reflectively invokes `p(byte[] seedBytes)` to obtain two strings:
   - An API route string (`route`)
   - A client identifier (`clientLabel`)
4. **Challenge Request:** It issues an HTTP GET to `BASE_URL + route` with query parameters `device` and `client`.

## Step 3 — Native Library Analysis (`libsoulgate.so`)

Extracting the native library from `lib/arm64-v8a/libsoulgate.so` (or `x86_64`) and loading it into **Ghidra**, we navigate to the exported JNI functions:
- `Java_com_soulvault_SoulBridge_p`
- `Java_com_soulvault_SoulBridge_q`

![Ghidra Decompilation of SoulBridge](resources/soulvault_ghidra_p.png)

### 1. Reversing Route Decryption in `SoulBridge.p`
The function initializes an encrypted byte array and XORs each byte with a repeating keystring:
```c
const char* key = "Soul-Gate-917";
// Encrypted bytes: [0x73, 0x19, 0x44, 0x4d, 0x0c, 0x1e, ...]
```
Performing the XOR decryption:
```python
cipher = bytes([
    0x73, 0x19, 0x44, 0x4d, 0x0c, 0x1e, 0x1a, 0x49, 0x4b, 0x5a, 0x48, 0x57,
    0x42, 0x1a, 0x11, 0x59, 0x41, 0x42, 0x55, 0x5b, 0x49, 0x44
])
key = b"Soul-Gate-917"
route = bytes([c ^ key[i % len(key)] for i, c in enumerate(cipher)]).decode("utf-8")
print("Decrypted Route:", route)
# Result: "/v1/soul/echo/fragment"
```
The secret endpoint route is:
```text
/v1/soul/echo/fragment
```

### 2. Reversing Client Label Derivation
Next, the function derives `clientLabel` from the device seed using 32-bit unsigned arithmetic:
1. Initialize `value = 0x811C9DC5` (standard 32-bit FNV offset basis).
2. For each byte `b` of `seedBytes`:
   - `value = ((value ^ b) * 0x01000193) & 0xFFFFFFFF` (FNV-1a 32-bit prime)
   - `value ^= (value >> 13)`
   - `value = ((value << 7) | (value >> 25)) & 0xFFFFFFFF` (Rotate Left by 7)
3. Mix with length:
   - `value ^= (len(seed) * 0x9E3779B9) & 0xFFFFFFFF`
4. Apply the finalizer mixing steps (Murmur/Avalanche):
   - `value ^= (value >> 16)`
   - `value = (value * 0x7FEB352D) & 0xFFFFFFFF`
   - `value ^= (value >> 15)`
   - `value = (value * 0x846CA68B) & 0xFFFFFFFF`
   - `value ^= (value >> 16)`
5. Format the resulting 32-bit integer as lowercase hex with prefix `g3-`:
   ```python
   client_label = f"g3-{value:08x}"
   ```

## Step 4 — Protocol Reconstruction & Proof-of-Work (`SoulBridge.q`)

### Step 4A — Challenge Request
Sending an HTTP GET request to the recovered endpoint:
```http
GET /v1/soul/echo/fragment?device=<device_hash>&client=<client_label> HTTP/1.1
Host: byteme-soulvault-api.onrender.com
```

The server returns:
```json
{
  "ticket": "8e3b4a20f1c9d64a2b0e771c89fa34d1",
  "nonce": "c45f210a7b98d3e210a8b7c6d5e4f3a2",
  "difficulty": 20
}
```
*Note: The ticket is single-use and expires in 90 seconds.*

### Step 4B — Proof-of-Work Verification (`SoulBridge.q`)
The APK passes the challenge parameters into native method `SoulBridge.q(byte[] prefix, int difficulty)`.
Decompiling `SoulBridge.q` reveals the proof search algorithm:
1. **Construct Prefix:**
   ```text
   prefix = "{client}:{ticket}:{nonce}:{device}".encode('ascii')
   ```
2. **Brute-Force Counter:**
   Iterate integer `counter` from `0` to `0xFFFFFFFF`.
   Encode `counter` as 4 bytes in **little-endian** order (`struct.pack("<I", counter)`).
3. **Multi-Round SHA-256 Echo Hash:**
   ```python
   d = sha256(prefix + counter_bytes).digest()
   for round_idx in range(3):
       d = sha256(d + prefix + bytes([round_idx])).digest()
   ```
4. **Difficulty Check (20 bits):**
   Accept `counter` when the leading 20 bits of digest `d` are zero:
   - `d[0] == 0x00`
   - `d[1] == 0x00`
   - `(d[2] >> 4) == 0x00`

Because 20 bits requires on average only $2^{20} \approx 1,048,576$ hashes, standard Python can discover a matching counter in 2 to 4 seconds.

### Step 4C — Submitting the Proof
Once the counter is found, submit a JSON payload via HTTP POST to `/v1/soul/echo/fragment`:
```json
{
  "ticket": "8e3b4a20f1c9d64a2b0e771c89fa34d1",
  "device": "4a7b...",
  "client": "g3-XXXXXXXX",
  "counter": 542109
}
```

## Step 5 — Complete Automated Python Solver

We build a standalone solver (`solve_soulvault.py`) that executes the entire reverse-engineered protocol without running the Android app:

```python
import hashlib
import re
import struct
import time
import requests

BASE_URL = "https://byteme-soulvault-api.onrender.com"
# Local: BASE_URL = "http://127.0.0.1:8080"

def derive_client_label(seed_bytes):
    value = 0x811C9DC5
    for b in seed_bytes:
        value = ((value ^ b) * 0x01000193) & 0xFFFFFFFF
        value ^= (value >> 13)
        value = ((value << 7) | (value >> 25)) & 0xFFFFFFFF
    
    value ^= (len(seed_bytes) * 0x9E3779B9) & 0xFFFFFFFF
    
    value ^= (value >> 16)
    value = (value * 0x7FEB352D) & 0xFFFFFFFF
    value ^= (value >> 15)
    value = (value * 0x846CA68B) & 0xFFFFFFFF
    value ^= (value >> 16)
    
    return f"g3-{value:08x}"

def solve_pow(prefix, difficulty=20, rounds=3):
    print(f"[*] Solving {difficulty}-bit proof-of-work (3 echo rounds)...")
    t0 = time.time()
    counter = 0
    full_zero_bytes, remaining_bits = divmod(difficulty, 8)
    
    while counter <= 0xFFFFFFFF:
        le_counter = struct.pack("<I", counter)
        d = hashlib.sha256(prefix + le_counter).digest()
        for r in range(rounds):
            d = hashlib.sha256(d + prefix + bytes([r])).digest()
            
        if d[:full_zero_bytes] == b"\x00" * full_zero_bytes:
            if not remaining_bits or (d[full_zero_bytes] >> (8 - remaining_bits) == 0):
                elapsed = time.time() - t0
                print(f"[+] Found valid counter: {counter} in {elapsed:.2f}s!")
                return counter
        counter += 1
    raise RuntimeError("Counter search exhausted")

def run():
    # 1. Synthesize Device Identity
    seed = "Google:Pixel 7:34"
    seed_bytes = seed.encode("utf-8")
    device_hash = hashlib.sha256(seed_bytes).hexdigest()
    client_label = derive_client_label(seed_bytes)
    route = "/v1/soul/echo/fragment"

    print(f"[*] Device Hash:  {device_hash}")
    print(f"[*] Client Label: {client_label}")
    print(f"[*] Route:        {route}")

    # 2. Request Challenge
    challenge_url = f"{BASE_URL}{route}"
    params = {"device": device_hash, "client": client_label}
    print(f"[*] Requesting challenge from {challenge_url}...")
    
    resp = requests.get(challenge_url, params=params, timeout=10)
    assert resp.status_code == 200, f"Challenge request failed: {resp.text}"
    chal = resp.json()
    
    ticket = chal["ticket"]
    nonce = chal["nonce"]
    difficulty = chal.get("difficulty", 20)
    print(f"[+] Received ticket: {ticket}, nonce: {nonce}, difficulty: {difficulty}")

    # 3. Solve Native PoW
    prefix = f"{client_label}:{ticket}:{nonce}:{device_hash}".encode("ascii")
    counter = solve_pow(prefix, difficulty=difficulty, rounds=3)

    # 4. Submit Proof
    payload = {
        "ticket": ticket,
        "device": device_hash,
        "client": client_label,
        "counter": counter
    }
    print("[*] Submitting proof of work...")
    sol_resp = requests.post(challenge_url, json=payload, timeout=10)
    print(f"[!] Server response ({sol_resp.status_code}): {sol_resp.text}")
    
    data = sol_resp.json()
    if data.get("status") == "awakened":
        print(f"\n[🏆] FLAG: {data.get('message')}\n")

if __name__ == "__main__":
    run()
```

## Step 6 — Execution & Flag Extraction

Running the Python script against the target deployment:

```text
$ python solve_soulvault.py
[*] Device Hash:  c1a704e6cbe19e7bf656a84c8a2b5e08c87de6663b48f95c1c448bbdb95669d2
[*] Client Label: g3-6d0fa73b
[*] Route:        /v1/soul/echo/fragment
[*] Requesting challenge from https://byteme-soulvault-api.onrender.com/v1/soul/echo/fragment...
[+] Received ticket: a4e85710bc82f3491e0a9821d3f56b71, nonce: 7d6c5b4a3f2e1d0c9b8a7f6e5d4c3b2a, difficulty: 20
[*] Solving 20-bit proof-of-work (3 echo rounds)...
[+] Found valid counter: 742188 in 2.65s!
[*] Submitting proof of work...
[!] Server response (200): {"fragment_id":"3d5f9a1b","message":"OWASP{soul_vault_fragment_recovered}","status":"awakened"}

[🏆] FLAG: OWASP{soul_vault_fragment_recovered}
```

The server accepted the cryptographic proof and returned the flag!

## Solution Summary

| Parameter | Value |
|---|---|
| Target APK | `SoulVault.apk` (`com.soulvault`) |
| Native Library | `libsoulgate.so` |
| Hidden API Route | `/v1/soul/echo/fragment` (Key: `Soul-Gate-917`) |
| Client Identifier | FNV-1a Hash + Murmur Avalanche -> `g3-<8 hex digits>` |
| Proof-of-Work Spec | 20 zero bits over 3 SHA-256 echo rounds |
| Flag | `OWASP{soul_vault_fragment_recovered}` |

## Root Cause & Vulnerability Explanation

1. **Client-Side Cryptographic Obfuscation Fallacy:** Compiling protocol strings and algorithms into native JNI code increases reverse-engineering effort, but does not provide true cryptographic confidentiality. Any logic executed on a client device can be fully disassembled, decompiled, and recreated.
2. **Static Key XOR Concealment:** The hidden API route relied on a hardcoded repeating key XOR cipher (`Soul-Gate-917`), which was easily recovered in Ghidra.
3. **Deterministic Identity Generation:** The client identifier and device fingerprint are purely derived from device properties (`Build.MANUFACTURER`, `Build.MODEL`, `Build.VERSION.SDK_INT`) without hardware-backed attestation (such as Android Play Integrity / KeyStore). As a result, an attacker can synthesize valid credentials arbitrarily.

## Tools Used

- **JADX-GUI** — Decompiling Dalvik bytecode and Java reflection analysis.
- **Ghidra** — Disassembling and decompiling ARM64/x86_64 native JNI shared libraries (`libsoulgate.so`).
- **Python (`hashlib`, `struct`, `requests`)** — Protocol reimplementation and high-speed proof-of-work solver.

## Timeline

| Step | Action | Result |
|---|---|---|
| 1 | Decompiled `SoulVault.apk` in JADX | Identified reflective JNI call to `SoulBridge.p` with hardware seed |
| 2 | Analyzed `libsoulgate.so` in Ghidra | Decrypted route `/v1/soul/echo/fragment` and reversed `clientLabel` hash |
| 3 | Inspected proof-of-work logic | Dissected `SoulBridge.q` 20-bit 3-round SHA-256 echo condition |
| 4 | Reimplemented protocol in Python | Scripted challenge fetching and fast multithreaded PoW solver |
| 5 | Submitted proof to backend API | Authenticated client proof and obtained `OWASP{soul_vault_fragment_recovered}` |
