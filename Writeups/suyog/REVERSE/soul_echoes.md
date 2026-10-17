# Soul Echoes (The Stonekeeper's Chronicles) (Reverse Engineering, Easy)

**Author:** Suyog Jadhav  
**Category:** Reverse Engineering  
**Difficulty:** Easy  

## Challenge Description

> The chilling winds across the barren peaks of Vormir carry ancient echoes.  
>  
> The Stonekeeper has inscribed his memories of exile, sacrifice, and sorrow into the obsidian stone.  
>  
> Can you hear the whisper hidden inside the chronicle?  
>  
> **Flag Format:** `OWASP{...}`

**Attachment:** [`soul_echo`](https://drive.google.com/file/d/1-8GGOFdt0CSfkXf2qKCh8DER53F74mUv/view?usp=sharing)

## Summary

The challenge provides a statically linked Linux x86-64 executable (`soul_echo`). The flag is embedded directly within the read-only data segment (`.rodata`) in plaintext. Extracting strings from the binary or disassembling the output routine reveals the flag immediately without requiring complex dynamic instrumentation.

## Flag

```
OWASP{th3_st0n3k33p3r_wh1sp3rs_1nt0_th3_v01d}
```

---

## Step 1 — Initial Reconnaissance

Inspecting the challenge artifact:

```bash
file soul_echo
ls -lh soul_echo
```

![File reconnaissance on soul_echo](resources/echoes_recon.png)

The executable is a 16 KB static Linux binary.

---

## Step 2 — Static String & Section Extraction

Running `strings` filtered for the known flag prefix `OWASP` quickly extracts the secret:

```bash
strings soul_echo | grep OWASP
objdump -s -j .rodata soul_echo | grep -A 2 "OWASP"
```

![String and rodata section inspection](resources/echoes_strings.png)

The flag is stored continuously in `.rodata`:

```text
402040 4f574153 507b7468 335f7374 306e336b  OWASP{th3_st0n3k
402050 33337033 725f7768 31737033 72735f31  33p3r_wh1sp3rs_1
402060 6e74305f 7468335f 76303164 7d000000  nt0_th3_v01d}...
```

---

## Step 3 — Binary Execution

Running the executable directly outputs the chronicle text and echoes the flag:

```bash
./soul_echo
```

![Direct execution of soul_echo](resources/echoes_execution.png)

Output:
```text
=== THE STONEKEEPER'S CHRONICLES ===

The obsidian stone trembles beneath the cosmic winds...
A voice whispers across the void:

OWASP{th3_st0n3k33p3r_wh1sp3rs_1nt0_th3_v01d}
```

---

## Solution Summary

| Field | Value |
|---|---|
| **Challenge** | Soul Echoes (The Stonekeeper's Chronicles) |
| **Category** | Reverse Engineering |
| **Difficulty** | Easy |
| **Extraction Method** | Direct string / `.rodata` extraction |
| **Flag** | `OWASP{th3_st0n3k33p3r_wh1sp3rs_1nt0_th3_v01d}` |

---

## Reverse Engineering Methodology

1. **Static Triage (The First Step in Any Reverse Challenge):**  
   Always run `strings` before loading a binary into disassemblers. In sanity-check or introductory reverse engineering challenges, flags or key validation strings may be stored in plaintext.
2. **Read-Only Data Segment Inspection:**  
   Constant literals in C programs are compiled into `.rodata`. Using tools like `objdump -s -j .rodata` or `readelf -x .rodata` exposes literal blocks regardless of binary stripping.

---

## Tools Used

- **`strings`**: Extracting printable character sequences from binary files.
- **`objdump`**: Inspecting ELF section contents (`.rodata`).
- **`file`**: Determining file type and architecture.

---

## Timeline

| Step | Action | Result |
|:---:|---|---|
| 1 | Checked file metadata | Identified Linux x86-64 ELF executable |
| 2 | Ran `strings soul_echo \| grep OWASP` | Located plaintext flag in binary |
| 3 | Executed binary | Verified execution and flag output |
