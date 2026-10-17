# SoulVault — Insane Reverse Engineering CTF Challenge

## Challenge Information

- **Title:** SoulVault
- **Category:** Reverse Engineering
- **Difficulty:** Insane
- **Player Artifact:** `dist/soulvault` (Only one Linux x86-64 stripped binary)
- **Flag Format:** `OWASP{...}`
- **Flag:** `OWASP{s0ul_v4ult_byt3c0d3_vm_r3v3rs3d_7a8f9c2e}`
- **Valid Sequence (Key):** `SV-8F4C-3B91-7E02-A6D5-C918-B472`

---

## CTF Description

> An abandoned security vault was found running an authentication program written in Go.
>
> The original source code is gone. The vault still accepts one particular key, but nobody knows what it is.
>
> Recover the key and uncover what the vault is hiding.
>
> **Flag format:** `OWASP{...}`

### Hints
- **Hint 1:** "Not everything interesting in the binary is meant to be executed."
- **Hint 2:** "The vault remembers what you do to it."

---

## Directory Structure

```text
soulvault/
│
├── README.md                 # Challenge documentation
├── build.sh                  # Release build script
├── Makefile                  # Build and test orchestration
├── Dockerfile                # Reproducible Docker build
│
├── dist/
│   └── soulvault             # Release binary given to players (stripped, static x86_64)
│
├── src/
│   ├── go.mod                # Go module specification
│   ├── main.go               # Entrypoint & CLI interactive UX
│   ├── state.go              # Persistent RuntimeState engine
│   ├── decoder.go            # State-dependent opcode decoding routines
│   ├── vm.go                 # Virtual machine core & memory management
│   ├── vm_dispatch.go        # Computed handler table & indirect dispatch
│   ├── validators.go         # Stage 1 (checksum) & Stage 2 (permutation)
│   ├── decoys.go             # Decoy engines (Alpha, Beta, Delta) & 100+ functions
│   ├── vault.go              # Master security pipeline coordinator
│   └── fragments.go          # Flag ciphertext fragments & KDF flag reconstruction
│
├── generator/
│   └── generate.go           # Challenge constant & bytecode assembler/verifier
│
└── organizer/
    ├── solve.py              # Full automated Python solver & disassembler
    ├── WRITEUP.md            # Comprehensive official writeup
    └── ANSWER.txt            # Solution key and flag reference
```

---

## Building the Challenge

### Local Build (Linux amd64)
Requirements: Go 1.21+
```bash
./build.sh
```
Or via Makefile:
```bash
make build
```

The output binary will be generated at `dist/soulvault`.

### Verification & Testing
```bash
make test
```

### Running the Organizer Solver
```bash
make solve
```
Or directly:
```bash
python3 organizer/solve.py
```

---

## Architecture & Security Highlights

1. **No Plaintext Flag:**
   The binary contains zero plaintext flag strings. The flag is constructed in volatile memory only after full verification of state and inputs, then wiped immediately.
2. **Custom Bytecode VM:**
   The VM runs an encoded bytecode program. Every instruction's opcode is decoded dynamically using a formula involving its instruction position, runtime seed, and execution phase.
3. **Indirect Computed Dispatcher:**
   Rather than using switch-case statements, opcodes map through a routing permutation table to an array of discrete Go handler functions, decompiling into indirect function pointer calls.
4. **Multiple Decoy VMs & Algorithms:**
   The binary includes three distinct decoy execution engines (`EngineAlpha`, `EngineBeta`, `EngineDelta`) and over 100 realistic cryptographic, hashing, and encoding algorithms to resist naive automation and static symbol scanners.
5. **Completely Solvable:**
   The mathematical core (ARX Feistel rounds and byte permutation) is completely invertible. An experienced human analyst using Ghidra, IDA Pro, Binary Ninja, or GDB can reverse the bytecode, decode the instructions, emulate or invert the arithmetic operations, and reconstruct the exact flag deterministically.
