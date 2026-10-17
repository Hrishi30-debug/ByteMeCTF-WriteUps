# SoulVault — Official Challenge Writeup

**Category:** Reverse Engineering  
**Difficulty:** Insane  
**Flag:** `OWASP{s0ul_v4ult_byt3c0d3_vm_r3v3rs3d_7a8f9c2e}`  
**Target Key:** `SV-8F4C-3B91-7E02-A6D5-C918-B472`  

---

## 1. Reconnaissance

We begin by examining the single executable file provided to players: `soulvault`.

```bash
$ file soulvault
soulvault: ELF 64-bit LSB executable, x86-64, version 1 (SYSV), statically linked, stripped
```

Checking sections and headers:

```bash
$ readelf -h soulvault
ELF Header:
  Magic:   7f 45 4c 46 02 01 01 00 00 00 00 00 00 00 00 00 
  Class:                             ELF64
  Data:                              2's complement, little endian
  Version:                           1 (current)
  OS/ABI:                            UNIX - System V
  ABI Version:                       0
  Type:                              EXEC (Executable file)
  Machine:                           Advanced Micro Devices X86-64
  Version:                           0x1
  Entry point address:               0x4653a0
  Start of program headers:          64 (bytes into file)
  Start of section headers:          ...
```

Checking strings:

```bash
$ strings soulvault | grep -i OWASP
(No results)

$ strings soulvault | grep -i "flag"
(No results)

$ strings soulvault | grep -i "SV-"
(No results)
```

Observations:
1. The binary is a standard 64-bit ELF executable compiled with Go (`gc`), statically linked, and stripped of symbol table and debugging info (`-ldflags="-s -w"`).
2. The flag is not stored as plaintext anywhere in the file.
3. The validation key is not present as a literal string.

Running the program interactively:

```text
$ ./soulvault
╔══════════════════════════════════════════╗
║               SOUL VAULT                 ║
║      Secure Key Verification System      ║
║               Version 3.4.1              ║
╚══════════════════════════════════════════╝

Enter access sequence:
> test
[-] ACCESS DENIED: Invalid sequence structure or checksum mismatch.
```

---

## 2. Static Analysis & Pipeline Identification

Opening the binary in Ghidra, IDA Pro, or Binary Ninja:
- Because the binary was built with `-trimpath`, package paths and internal symbol names are stripped.
- However, standard Go runtime functions (e.g. `runtime.main`, `runtime.newobject`, `os.Stdin.Read`) lead us directly to the user entrypoint function `main.main`.

Tracing `main.main`:
1. It prints the banner and reads a line from `os.Stdin`.
2. It passes the trimmed string into the primary coordinator function `main.ProcessAccessSequence`.
3. In `main.ProcessAccessSequence`, we see a distinct 4-stage validation flow:
   - **Stage 1 (`main.ValidateStructureStage1`)**:
     - Checks `len(input) == 32` (0x20).
     - Checks prefix: `input[0] == 'S'`, `input[1] == 'V'`, `input[2] == '-'`.
     - Checks hyphens at fixed positions: indices 7, 12, 17, 22, 27.
     - Checks that all intermediate characters are uppercase ASCII hex digits (`'0'-'9'`, `'A'-'F'`).
     - Calculates a positional polynomial checksum over the 24 hex characters:
       $$\sum_{i=0}^{23} (c_i \times 17 + i \times 13 + csum \times 31) \equiv \text{0x1248D50D} \pmod{2^{32}}$$
       with initial seed `0x5A17F00D`.
   - **Stage 2 (`main.TransformStage2`)**:
     - Takes the 32 input bytes.
     - Shuffles them according to a fixed 32-byte permutation table `main.Permutation`.
     - Applies an XOR mask `main.MaskK[i]`, a variable bitwise rotation `(i % 7) + 1`, and an addition with `main.AddC[i]`.
     - Produces a 32-byte transformed block `stage2Block`.
   - **Decoy Pipelines & Multiple Engines**:
     - The binary contains multiple decoy engines (`EngineAlpha`, `EngineBeta`, `EngineDelta`) and over 100 realistic cryptographic and hashing algorithms (CRC32 variants, CRC64, Adler, FNV-1a, MurmurHash, ChaCha, SipHash).
     - However, tracing the control flow reveals that these decoy results do not alter the main execution path.
   - **Stage 3: Custom Virtual Machine**:
     - An allocation initializes a VM memory buffer of 2048 bytes.
     - Memory `0x0000..0x003F` is populated with eight 64-bit constants (`RoundConstants`).
     - Memory `0x0100..0x011F` is loaded with the 32-byte `stage2Block`.
     - Memory `0x0120..0x013F` is loaded with four 64-bit target constants (`TargetConstants`).
     - The VM executes bytecode through an indirect dispatcher.

---

## 3. Custom VM Dispatcher & Opcode Transformation

In `main.(*VM).Step`, the fetch-decode cycle is revealed:

```go
pos := vm.IP / 4
encOp := vm.Bytecode[vm.IP]
dst   := vm.Bytecode[vm.IP+1]
src   := vm.Bytecode[vm.IP+2]
imm8  := vm.Bytecode[vm.IP+3]
imm16 := (uint16(src) << 8) | uint16(imm8)

op := decodeOpcode(encOp, pos, vm.State.Seed, vm.State.Phase)
```

The function `main.decodeOpcode` implements the runtime opcode decoding:

```python
def decode_opcode(enc, pos, seed, phase):
    k = (seed >> ((pos % 7) * 8)) & 0xFF
    shift = (pos % 5) + 1
    r = enc ^ k ^ ((phase * 17) & 0xFF) ^ (pos & 0x3F)
    # Circular right shift by shift
    return ((r >> shift) | (r << (8 - shift))) & 0xFF
```

### Handler Dispatch

The dispatcher does not use a plain `switch` statement. Instead, it maintains:
1. `routeTable [256]byte`: maps each runtime opcode to a handler slot.
2. `handlers [256]HandlerFunc`: an array of function pointers.

When `d.Dispatch(vm, op, dst, src, imm8, imm16)` is called:
```text
slot := routeTable[op]
handlers[slot](vm, dst, src, imm8, imm16)
```
In the disassembled machine code, this appears as an indirect call:
```assembly
movzx  eax, byte ptr [rdi + rdx]     # lookup routeTable[op]
mov    rax, qword ptr [rsi + rax*8]   # lookup handlers[slot]
call   rax                            # indirect call to handler
```

---

## 4. VM Instruction Set Architecture (ISA)

Each instruction is encoded as a 4-byte word:
`[EncOp (1 byte), Dst (1 byte), Src / Imm16_Hi (1 byte), Imm8 / Imm16_Lo (1 byte)]`

The decoded runtime opcodes map to the following operations:

| Opcode | Mnemonic | Format | Description |
|---|---|---|---|
| `0x01` | `NOP` | `NOP` | No operation |
| `0x02` | `MOV_REG` | `MOV_REG Dst, Src` | `Reg[Dst] = Reg[Src]` |
| `0x03` | `MOV_IMM` | `MOV_IMM Dst, Imm16` | `Reg[Dst] = Imm16` |
| `0x04` | `LOAD8` | `LOAD8 Dst, [Src+Imm8]` | `Reg[Dst] = Mem[Reg[Src]+Imm8]` |
| `0x05` | `STORE8` | `STORE8 [Dst+Imm8], Src` | `Mem[Reg[Dst]+Imm8] = Reg[Src]` |
| `0x06` | `LOAD64` | `LOAD64 Dst, [Src+Imm8]` | `Reg[Dst] = Mem64[Reg[Src]+Imm8]` |
| `0x07` | `STORE64` | `STORE64 [Dst+Imm8], Src` | `Mem64[Reg[Dst]+Imm8] = Reg[Src]` |
| `0x08` | `ADD` | `ADD Dst, Src` | `Reg[Dst] += Reg[Src]` |
| `0x09` | `SUB` | `SUB Dst, Src` | `Reg[Dst] -= Reg[Src]` |
| `0x0A` | `XOR` | `XOR Dst, Src` | `Reg[Dst] ^= Reg[Src]` |
| `0x0B` | `AND` | `AND Dst, Src` | `Reg[Dst] &= Reg[Src]` |
| `0x0C` | `OR` | `OR Dst, Src` | `Reg[Dst] \|= Reg[Src]` |
| `0x0D` | `ROL_IMM`| `ROL_IMM Dst, Imm8` | `Reg[Dst] = rotl64(Reg[Dst], Imm8)` |
| `0x0E` | `ROR_IMM`| `ROR_IMM Dst, Imm8` | `Reg[Dst] = rotr64(Reg[Dst], Imm8)` |
| `0x0F` | `MUL` | `MUL Dst, Src` | `Reg[Dst] *= Reg[Src]` |
| `0x10` | `CMP` | `CMP Dst, Src` | Sets Flags: Equal, Less, Greater |
| `0x11` | `JMP` | `JMP Imm16` | `IP += int16(Imm16)` |
| `0x12` | `JZ` | `JZ Imm16` | If Equal: `IP += int16(Imm16)` |
| `0x13` | `JNZ` | `JNZ Imm16` | If Not Equal: `IP += int16(Imm16)` |
| `0x14` | `PUSH` | `PUSH Src` | `SP -= 8; Mem64[SP] = Reg[Src]` |
| `0x15` | `POP` | `POP Dst` | `Reg[Dst] = Mem64[SP]; SP += 8` |
| `0x16` | `SYNC` | `SYNC_STATE` | `State.A..D = Reg[8..11]` |
| `0x17` | `HALT` | `HALT` | Terminate VM execution |

---

## 5. Bytecode Extraction & Disassembly

Extracting `main.RealVMBytecode` (576 bytes) from `.rodata` and disassembling via the opcode decoder reveals:

1. Loads the four 64-bit input words into registers `R8`, `R9`, `R10`, `R11` from memory `0x0100`:
   ```text
   MOV_IMM  R12, 0x0100
   LOAD64   R8,  [R12 + 0]
   LOAD64   R9,  [R12 + 8]
   LOAD64   R10, [R12 + 16]
   LOAD64   R11, [R12 + 24]
   ```
2. Initializes pointer to round constants at `0x0000`:
   ```text
   MOV_IMM  R7, 0x0000
   ```
3. Executes **8 consecutive ARX rounds**. In each round $r \in [0..7]$:
   ```text
   LOAD64   R1, [R7 + r*8]       ; Load Round Constant RC[r]
   ADD      R8, R9
   ADD      R8, R1
   XOR      R11, R8
   ROL_IMM  R11, 17
   ADD      R10, R11
   XOR      R9, R10
   ROR_IMM  R9, 19
   ADD      R8, R9
   XOR      R11, R8
   ROL_IMM  R11, 23
   ADD      R10, R11
   ADD      R10, R1
   XOR      R9, R10
   ROR_IMM  R9, 29
   ```
4. Compares `R8, R9, R10, R11` with the four 64-bit target constants stored at `0x0120`:
   ```text
   MOV_IMM  R12, 0x0120
   LOAD64   R1, [R12 + 0];  CMP R8, R1;  JNZ fail
   LOAD64   R1, [R12 + 8];  CMP R9, R1;  JNZ fail
   LOAD64   R1, [R12 + 16]; CMP R10, R1; JNZ fail
   LOAD64   R1, [R12 + 24]; CMP R11, R1; JNZ fail

   success:
   MOV_IMM  R0, 1
   SYNC_STATE
   HALT

   fail:
   MOV_IMM  R0, 0
   HALT
   ```

---

## 6. Solving the Challenge

### Step 1: Inverting the ARX Rounds
Because every ARX operation (modular addition mod $2^{64}$, XOR, and bitwise rotation) is bi-directional and invertible:

$$\begin{aligned}
R_1 &\leftarrow (R_1 \text{ ROL } 29) \oplus R_2 \\
R_2 &\leftarrow R_2 - R_3 - RC \\
R_3 &\leftarrow (R_3 \text{ ROR } 23) \oplus R_0 \\
R_0 &\leftarrow R_0 - R_1 \\
R_1 &\leftarrow (R_1 \text{ ROL } 19) \oplus R_2 \\
R_2 &\leftarrow R_2 - R_3 \\
R_3 &\leftarrow (R_3 \text{ ROR } 17) \oplus R_0 \\
R_0 &\leftarrow R_0 - R_1 - RC
\end{aligned}$$

Starting from target constants $T_0, T_1, T_2, T_3$ and inverting rounds 7 down to 0 yields the 32-byte `stage2Block`:
```text
f1c4bac898913e69f1c9ba684c700a98563426a668b3b67b48de05e6d02191bd
```

### Step 2: Inverting Stage 2
For each byte $i \in [0..31]$:
1. Subtract `AddC[i]` mod 256.
2. Circular right shift by `(i % 7) + 1`.
3. XOR with `MaskK[i]`.
4. Apply the inverse permutation `PermutationInv`.

This produces the 32-byte key:
```text
SV-8F4C-3B91-7E02-A6D5-C918-B472
```

### Step 3: Flag Reconstruction
`main.ReconstructFlag` combines the 4 encrypted fragments:
```text
Fragment0: c00e123f7a91b409adfe326a
Fragment1: 54252724a399d900858ce4e7
Fragment2: 2a2ee625711bf67cad75a6d3
Fragment3: b84ead35e67645af05e79f
```
The keystream is generated via SHA-256 KDF:
$$K_1 = \text{SHA256}(T_0 \parallel T_1 \parallel T_2 \parallel T_3 \parallel \text{"SoulVault::MasterFlagKeystream::v1"} \parallel \text{stage2Block})$$
$$K_2 = \text{SHA256}(K_1 \parallel \text{"SoulVault::SubStreamKey::v1"})$$
$$\text{keystream} = K_1 \parallel K_2$$

XORing the ciphertext fragments with the keystream reveals:
```text
OWASP{s0ul_v4ult_byt3c0d3_vm_r3v3rs3d_7a8f9c2e}
```

---

## 7. Execution of the Organizer Solver

```bash
$ python3 organizer/solve.py
============================================================
        SOULVAULT REVERSE ENGINEERING SOLVER
============================================================
[*] Reversing 8 rounds of ARX in Real VM...
[+] Recovered Stage 2 Transformed Block: f1c4bac898913e69f1c9ba684c700a98563426a668b3b67b48de05e6d02191bd
[*] Inverting Stage 2 byte permutation and rotation...
[+] Recovered Authentication Key: SV-8F4C-3B91-7E02-A6D5-C918-B472
[*] Deriving KDF keystream from VM State and fragments...
[+] Recovered Flag: OWASP{s0ul_v4ult_byt3c0d3_vm_r3v3rs3d_7a8f9c2e}

[*] Validating against binary: .../dist/soulvault
[+] Binary verification SUCCESS!
╔══════════════════════════════════════════╗
║               SOUL VAULT                 ║
║      Secure Key Verification System      ║
║               Version 3.4.1              ║
╚══════════════════════════════════════════╝

Enter access sequence:
> 
[+] ACCESS GRANTED. VAULT UNLOCKED.
[+] Sequence Validated: SV-8F4C-3B91-7E02-A6D5-C918-B472
[+] Flag: OWASP{s0ul_v4ult_byt3c0d3_vm_r3v3rs3d_7a8f9c2e}

============================================================
SOLVE SUMMARY:
Key:  SV-8F4C-3B91-7E02-A6D5-C918-B472
Flag: OWASP{s0ul_v4ult_byt3c0d3_vm_r3v3rs3d_7a8f9c2e}
============================================================
```
