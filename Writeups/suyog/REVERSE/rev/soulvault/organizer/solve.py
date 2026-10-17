#!/usr/bin/env python3
"""
SoulVault - Insane Reverse Engineering CTF Challenge Solver
Author: Organizer / Author Solution
"""

import sys
import os
import struct
import subprocess
import hashlib

# ==============================================================================
# 1. RECOVERED ARCHITECTURAL CONSTANTS (FROM REVERSING SOULVAULT)
# ==============================================================================

INITIAL_SEED = 0x5A17F00DC0FFEE11
INITIAL_PHASE = 0x1

# 8 Round Constants extracted from memory at 0x0000 (main.RoundConstants)
ROUND_CONSTANTS = [
    0x243F6A8885A308D3, 0x13198A2E03707344,
    0xA4093822299F31D0, 0x082EFA98EC4E6C89,
    0x452821E638D01377, 0xBE5466CF34E90C6C,
    0xC0AC29B7C97C50DD, 0x3F84D5B5B5470917,
]

# Target Constants compared in the VM at 0x0120 (main.TargetConstants)
TARGET_CONSTANTS = [
    0x914C537D5FF807C4,
    0x4CB53E7A4E23D414,
    0x9CA92D19C1339829,
    0x46EA1254AC1C539E,
]

# Stage 2 Permutation and Additive Masks (main.Permutation, MaskK, AddC)
PERMUTATION = [
    17, 4, 29, 12, 1, 23, 8, 31,
    15, 6, 20, 2, 28, 11, 24, 7,
    19, 0, 27, 14, 5, 22, 9, 30,
    16, 3, 21, 10, 26, 13, 25, 18,
]

MASK_K = [
    0x4A, 0x9F, 0x13, 0xD7, 0x82, 0x5E, 0x3C, 0xB1,
    0x68, 0xF4, 0x29, 0xAC, 0x75, 0x0E, 0xE3, 0x96,
    0x51, 0x3F, 0x8A, 0x2D, 0xC4, 0x7B, 0x19, 0xE0,
    0x6F, 0xB8, 0x42, 0x9D, 0x05, 0xCE, 0x27, 0xA3,
]

ADD_C = [
    0x23, 0x5D, 0x81, 0x19, 0xFE, 0x4A, 0xB7, 0x62,
    0x90, 0x0C, 0xE4, 0x38, 0x7F, 0xD1, 0x55, 0xAA,
    0x1B, 0x6E, 0x32, 0x8C, 0xF0, 0x07, 0x49, 0xBD,
    0x73, 0xCE, 0x28, 0x94, 0x56, 0x3A, 0xE1, 0x8F,
]

# Encrypted Flag Fragments (main.Fragment0..3)
FRAGMENTS = [
    bytes([0xc0, 0x0e, 0x12, 0x3f, 0x7a, 0x91, 0xb4, 0x09, 0xad, 0xfe, 0x32, 0x6a]),
    bytes([0x54, 0x25, 0x27, 0x24, 0xa3, 0x99, 0xd9, 0x00, 0x85, 0x8c, 0xe4, 0xe7]),
    bytes([0x2a, 0x2e, 0xe6, 0x25, 0x71, 0x1b, 0xf6, 0x7c, 0xad, 0x75, 0xa6, 0xd3]),
    bytes([0xb8, 0x4e, 0xad, 0x35, 0xe6, 0x76, 0x45, 0xaf, 0x05, 0xe7, 0x9f])
]

# ==============================================================================
# 2. VM DISASSEMBLER & OPCODE DECODER
# ==============================================================================

OPCODE_NAMES = {
    0x01: "NOP",
    0x02: "MOV_REG",
    0x03: "MOV_IMM",
    0x04: "LOAD8",
    0x05: "STORE8",
    0x06: "LOAD64",
    0x07: "STORE64",
    0x08: "ADD",
    0x09: "SUB",
    0x0A: "XOR",
    0x0B: "AND",
    0x0C: "OR",
    0x0D: "ROL_IMM",
    0x0E: "ROR_IMM",
    0x0F: "MUL",
    0x10: "CMP",
    0x11: "JMP",
    0x12: "JZ",
    0x13: "JNZ",
    0x14: "PUSH",
    0x15: "POP",
    0x16: "SYNC_STATE",
    0x17: "HALT",
}

def rotr8(b, n):
    n &= 7
    return ((b >> n) | (b << (8 - n))) & 0xFF

def rotl8(b, n):
    n &= 7
    return ((b << n) | (b >> (8 - n))) & 0xFF

def decode_opcode(enc, pos, seed, phase):
    k = (seed >> ((pos % 7) * 8)) & 0xFF
    shift = (pos % 5) + 1
    r = enc ^ k ^ ((phase * 17) & 0xFF) ^ (pos & 0x3F)
    return rotr8(r, shift)

def disassemble_bytecode(bytecode):
    lines = []
    for ip in range(0, len(bytecode), 4):
        pos = ip // 4
        enc_op = bytecode[ip]
        dst = bytecode[ip+1]
        src = bytecode[ip+2]
        imm8 = bytecode[ip+3]
        imm16 = (src << 8) | imm8
        op = decode_opcode(enc_op, pos, INITIAL_SEED, INITIAL_PHASE)
        name = OPCODE_NAMES.get(op, f"UNK_0x{op:02X}")
        lines.append(f"0x{ip:04X} [pos={pos:03d}]: {name:<10} Dst=R{dst&0xF:<2} Src=R{src&0xF:<2} Imm8=0x{imm8:02X} Imm16=0x{imm16:04X}")
    return lines

# ==============================================================================
# 3. MATHEMATICAL REVERSAL OF VM VALIDATION (INVERT ARX & STAGE 2)
# ==============================================================================

def rotl64(x, n):
    n &= 63
    return ((x << n) | (x >> (64 - n))) & 0xFFFFFFFFFFFFFFFF

def rotr64(x, n):
    n &= 63
    return ((x >> n) | (x << (64 - n))) & 0xFFFFFFFFFFFFFFFF

def arx_round_inv(r0, r1, r2, r3, rc):
    # Invert:
    # R9 = (R9 ^ R10) ROR 29
    r1 = (rotl64(r1, 29) ^ r2) & 0xFFFFFFFFFFFFFFFF
    # R10 = R10 + R11 + R1
    r2 = (r2 - r3 - rc) & 0xFFFFFFFFFFFFFFFF
    # R11 = (R11 ^ R8) ROL 23
    r3 = (rotr64(r3, 23) ^ r0) & 0xFFFFFFFFFFFFFFFF
    # R8 = R8 + R9
    r0 = (r0 - r1) & 0xFFFFFFFFFFFFFFFF
    # R9 = (R9 ^ R10) ROR 19
    r1 = (rotl64(r1, 19) ^ r2) & 0xFFFFFFFFFFFFFFFF
    # R10 = R10 + R11
    r2 = (r2 - r3) & 0xFFFFFFFFFFFFFFFF
    # R11 = (R11 ^ R8) ROL 17
    r3 = (rotr64(r3, 17) ^ r0) & 0xFFFFFFFFFFFFFFFF
    # R8 = R8 + R9 + R1
    r0 = (r0 - r1 - rc) & 0xFFFFFFFFFFFFFFFF
    return r0, r1, r2, r3

def solve_stage2_block():
    r0, r1, r2, r3 = TARGET_CONSTANTS
    # Invert 8 ARX rounds in reverse order (round 7 down to 0)
    for round_idx in range(7, -1, -1):
        r0, r1, r2, r3 = arx_round_inv(r0, r1, r2, r3, ROUND_CONSTANTS[round_idx])
    return struct.pack("<QQQQ", r0, r1, r2, r3)

def solve_key(stage2_block):
    # Invert Stage 2 Transformation
    intermediate = [0] * 32
    for i in range(32):
        sub = (stage2_block[i] - ADD_C[i]) & 0xFF
        shift = (i % 7) + 1
        rot_inv = ((sub >> shift) | (sub << (8 - shift))) & 0xFF
        intermediate[i] = rot_inv ^ MASK_K[i]

    key = [0] * 32
    for i in range(32):
        key[PERMUTATION[i]] = intermediate[i]

    return bytes(key).decode("latin-1")

def reconstruct_flag(stage2_block):
    key_material = struct.pack("<QQQQ", *TARGET_CONSTANTS)
    h1 = hashlib.sha256(key_material + b"SoulVault::MasterFlagKeystream::v1" + stage2_block).digest()
    h2 = hashlib.sha256(h1 + b"SoulVault::SubStreamKey::v1").digest()
    keystream = h1 + h2

    enc_flag = b"".join(FRAGMENTS)
    flag_bytes = bytes([enc_flag[i] ^ keystream[i] for i in range(len(enc_flag))])
    return flag_bytes.decode("utf-8")

# ==============================================================================
# 4. SOLVER EXECUTION ENTRYPOINT
# ==============================================================================

def main():
    print("=" * 60)
    print("        SOULVAULT REVERSE ENGINEERING SOLVER")
    print("=" * 60)

    # 1. Reverse the VM Stage 3 ARX Rounds
    print("[*] Reversing 8 rounds of ARX in Real VM...")
    stage2_block = solve_stage2_block()
    print(f"[+] Recovered Stage 2 Transformed Block: {stage2_block.hex()}")

    # 2. Reverse Stage 2 Permutation and Mixing
    print("[*] Inverting Stage 2 byte permutation and rotation...")
    key = solve_key(stage2_block)
    print(f"[+] Recovered Authentication Key: {key}")

    # 3. Derive Flag
    print("[*] Deriving KDF keystream from VM State and fragments...")
    flag = reconstruct_flag(stage2_block)
    print(f"[+] Recovered Flag: {flag}")

    # 4. Validate with binary if present
    binary_path = os.path.join(os.path.dirname(__file__), "../dist/soulvault")
    if os.path.exists(binary_path):
        print(f"\n[*] Validating against binary: {binary_path}")
        proc = subprocess.run([binary_path], input=(key + "\n").encode(), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out = proc.stdout.decode()
        if "ACCESS GRANTED" in out and flag in out:
            print("[+] Binary verification SUCCESS!")
            print(out.strip())
        else:
            print("[-] Binary verification FAILED!")
            print(out)
            sys.exit(1)
    else:
        print(f"[*] Note: Binary not found at {binary_path}, run build.sh first.")

    print("\n" + "=" * 60)
    print("SOLVE SUMMARY:")
    print(f"Key:  {key}")
    print(f"Flag: {flag}")
    print("=" * 60)

if __name__ == "__main__":
    main()
