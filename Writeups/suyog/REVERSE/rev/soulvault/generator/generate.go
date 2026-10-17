package main

import (
	"bytes"
	"crypto/sha256"
	"encoding/binary"
	"fmt"
	"math/bits"
	"os"
)

// Target Key and Flag
const TargetKey = "SV-8F4C-3B91-7E02-A6D5-C918-B472"
const TargetFlag = "OWASP{s0ul_v4ult_byt3c0d3_vm_r3v3rs3d_7a8f9c2e}"

// Seed and initial state
const InitialSeed uint64 = 0x5A17F00DC0FFEE11
const InitialPhase uint32 = 0x1

// Stage 2 permutation and key/constant arrays (32 bytes)
var Permutation = [32]byte{
	17, 4, 29, 12, 1, 23, 8, 31,
	15, 6, 20, 2, 28, 11, 24, 7,
	19, 0, 27, 14, 5, 22, 9, 30,
	16, 3, 21, 10, 26, 13, 25, 18,
}

var PermutationInv [32]byte

var MaskK = [32]byte{
	0x4A, 0x9F, 0x13, 0xD7, 0x82, 0x5E, 0x3C, 0xB1,
	0x68, 0xF4, 0x29, 0xAC, 0x75, 0x0E, 0xE3, 0x96,
	0x51, 0x3F, 0x8A, 0x2D, 0xC4, 0x7B, 0x19, 0xE0,
	0x6F, 0xB8, 0x42, 0x9D, 0x05, 0xCE, 0x27, 0xA3,
}

var AddC = [32]byte{
	0x23, 0x5D, 0x81, 0x19, 0xFE, 0x4A, 0xB7, 0x62,
	0x90, 0x0C, 0xE4, 0x38, 0x7F, 0xD1, 0x55, 0xAA,
	0x1B, 0x6E, 0x32, 0x8C, 0xF0, 0x07, 0x49, 0xBD,
	0x73, 0xCE, 0x28, 0x94, 0x56, 0x3A, 0xE1, 0x8F,
}

// 8 Round Constants (64-bit)
var RoundConstants = [8]uint64{
	0x243F6A8885A308D3, 0x13198A2E03707344,
	0xA4093822299F31D0, 0x082EFA98EC4E6C89,
	0x452821E638D01377, 0xBE5466CF34E90C6C,
	0xC0AC29B7C97C50DD, 0x3F84D5B5B5470917,
}

// ARX Round functions
func rotl64(x uint64, n uint) uint64 {
	return bits.RotateLeft64(x, int(n))
}

func rotr64(x uint64, n uint) uint64 {
	return bits.RotateLeft64(x, -int(n))
}

func arxRound(r0, r1, r2, r3, rc uint64) (uint64, uint64, uint64, uint64) {
	r0 = r0 + r1 + rc
	r3 = rotl64(r3^r0, 17)
	r2 = r2 + r3
	r1 = rotr64(r1^r2, 19)
	r0 = r0 + r1
	r3 = rotl64(r3^r0, 23)
	r2 = r2 + r3 + rc
	r1 = rotr64(r1^r2, 29)
	return r0, r1, r2, r3
}

func arxRoundInv(r0, r1, r2, r3, rc uint64) (uint64, uint64, uint64, uint64) {
	r1 = rotl64(r1, 29) ^ r2
	r2 = r2 - r3 - rc
	r3 = rotr64(r3, 23) ^ r0
	r0 = r0 - r1
	r1 = rotl64(r1, 19) ^ r2
	r2 = r2 - r3
	r3 = rotr64(r3, 17) ^ r0
	r0 = r0 - r1 - rc
	return r0, r1, r2, r3
}

func init() {
	for i := 0; i < 32; i++ {
		PermutationInv[Permutation[i]] = byte(i)
	}
}

// Stage 1 Checksum
func ComputeStage1Checksum(input string) uint32 {
	if len(input) != 32 {
		return 0
	}
	// Extract the 24 hex characters
	var hexChars []byte
	indices := []int{
		3, 4, 5, 6,
		8, 9, 10, 11,
		13, 14, 15, 16,
		18, 19, 20, 21,
		23, 24, 25, 26,
		28, 29, 30, 31,
	}
	for _, idx := range indices {
		hexChars = append(hexChars, input[idx])
	}

	csum := uint32(0x5A17F00D)
	for i, ch := range hexChars {
		csum = (csum*31 + uint32(ch)*17 + uint32(i*13)) & 0xFFFFFFFF
	}
	return csum
}

// Stage 2 Transform
func TransformStage2(input []byte) [32]byte {
	var out [32]byte
	for i := 0; i < 32; i++ {
		orig := input[Permutation[i]]
		x := orig ^ MaskK[i]
		shift := byte((i % 7) + 1)
		rot := (x << shift) | (x >> (8 - shift))
		out[i] = rot + AddC[i]
	}
	return out
}

func TransformStage2Inv(out [32]byte) []byte {
	var intermediate [32]byte
	for i := 0; i < 32; i++ {
		sub := out[i] - AddC[i]
		shift := byte((i % 7) + 1)
		rotInv := (sub >> shift) | (sub << (8 - shift))
		orig := rotInv ^ MaskK[i]
		intermediate[i] = orig
	}
	res := make([]byte, 32)
	for i := 0; i < 32; i++ {
		res[Permutation[i]] = intermediate[i]
	}
	return res
}

func main() {
	fmt.Println("=== SoulVault Generator & Consistency Verifier ===")

	// 1. Stage 1 check
	csum := ComputeStage1Checksum(TargetKey)
	fmt.Printf("[+] Stage 1 Checksum for Target Key: 0x%08X\n", csum)

	// 2. Stage 2 transform
	stage2Out := TransformStage2([]byte(TargetKey))
	fmt.Printf("[+] Stage 2 Output: %x\n", stage2Out)

	// Verify Stage 2 inversion
	recoveredKey := string(TransformStage2Inv(stage2Out))
	if recoveredKey != TargetKey {
		fmt.Printf("[-] Stage 2 inversion failed! Got: %s\n", recoveredKey)
		os.Exit(1)
	}
	fmt.Println("[+] Stage 2 inversion verified successfully!")

	// 3. Compute Forward ARX on the 4 64-bit blocks
	var r [4]uint64
	for i := 0; i < 4; i++ {
		r[i] = binary.LittleEndian.Uint64(stage2Out[i*8 : (i+1)*8])
	}
	fmt.Printf("[+] Initial R8-R11: 0x%016X 0x%016X 0x%016X 0x%016X\n", r[0], r[1], r[2], r[3])

	// 8 rounds
	for round := 0; round < 8; round++ {
		r[0], r[1], r[2], r[3] = arxRound(r[0], r[1], r[2], r[3], RoundConstants[round])
	}
	targetT := r
	fmt.Printf("[+] Final Target Constants T0-T3:\n")
	for i := 0; i < 4; i++ {
		fmt.Printf("    T%d = 0x%016X\n", i, targetT[i])
	}

	// Verify ARX Inversion
	testR := targetT
	for round := 7; round >= 0; round-- {
		testR[0], testR[1], testR[2], testR[3] = arxRoundInv(testR[0], testR[1], testR[2], testR[3], RoundConstants[round])
	}
	for i := 0; i < 4; i++ {
		expected := binary.LittleEndian.Uint64(stage2Out[i*8 : (i+1)*8])
		if testR[i] != expected {
			fmt.Printf("[-] ARX inversion failed for block %d! Got 0x%016X, expected 0x%016X\n", i, testR[i], expected)
			os.Exit(1)
		}
	}
	fmt.Println("[+] ARX round inversion verified successfully!")

	// 4. Derive KDF keystream from target state (T0, T1, T2, T3) and encrypt flag fragments
	// Let's create flag encryption
	keyMaterial := make([]byte, 32)
	for i := 0; i < 4; i++ {
		binary.LittleEndian.PutUint64(keyMaterial[i*8:(i+1)*8], targetT[i])
	}

	h := sha256.New()
	h.Write(keyMaterial)
	h.Write([]byte("SoulVault::MasterFlagKeystream::v1"))
	h.Write(stage2Out[:])
	keyHash1 := h.Sum(nil) // 32 bytes

	h.Reset()
	h.Write(keyHash1)
	h.Write([]byte("SoulVault::SubStreamKey::v1"))
	keyHash2 := h.Sum(nil) // 32 bytes

	fullKeystream := append(keyHash1, keyHash2...) // 64 bytes
	flagBytes := []byte(TargetFlag)
	encryptedFlag := make([]byte, len(flagBytes))
	for i := 0; i < len(flagBytes); i++ {
		encryptedFlag[i] = flagBytes[i] ^ fullKeystream[i]
	}

	// Split into 4 fragments
	fragLen := (len(encryptedFlag) + 3) / 4
	var fragments [4][]byte
	for i := 0; i < 4; i++ {
		start := i * fragLen
		end := start + fragLen
		if end > len(encryptedFlag) {
			end = len(encryptedFlag)
		}
		if start < len(encryptedFlag) {
			fragments[i] = encryptedFlag[start:end]
		}
	}

	fmt.Printf("[+] Encrypted Flag (%d bytes): %x\n", len(encryptedFlag), encryptedFlag)
	for i := 0; i < 4; i++ {
		fmt.Printf("    Fragment %d: %x\n", i, fragments[i])
	}

	// Verify Decryption
	var combined []byte
	for i := 0; i < 4; i++ {
		combined = append(combined, fragments[i]...)
	}
	decryptedFlag := make([]byte, len(combined))
	for i := 0; i < len(combined); i++ {
		decryptedFlag[i] = combined[i] ^ fullKeystream[i]
	}
	if !bytes.Equal(decryptedFlag, flagBytes) {
		fmt.Printf("[-] Flag decryption test failed! Got: %s\n", decryptedFlag)
		os.Exit(1)
	}
	fmt.Printf("[+] Decrypted Flag successfully: %s\n", decryptedFlag)

	// 5. Build VM Bytecode Program
	fmt.Println("\n=== Assembling VM Bytecode ===")
	prog := assembleRealVM()
	fmt.Printf("[+] Raw unencoded instructions: %d (%d bytes)\n", len(prog)/4, len(prog))

	// Encode instructions
	encodedProg := make([]byte, len(prog))
	for i := 0; i < len(prog); i += 4 {
		pos := uint64(i / 4)
		runtimeOp := prog[i]
		encOp := encodeOpcode(runtimeOp, pos, InitialSeed, InitialPhase)
		encodedProg[i] = encOp
		encodedProg[i+1] = prog[i+1]
		encodedProg[i+2] = prog[i+2]
		encodedProg[i+3] = prog[i+3]

		// Verify decode immediately
		decOp := decodeOpcode(encOp, pos, InitialSeed, InitialPhase)
		if decOp != runtimeOp {
			fmt.Printf("[-] Opcode decode failed at pos %d: raw 0x%02x, enc 0x%02x, dec 0x%02x\n", pos, runtimeOp, encOp, decOp)
			os.Exit(1)
		}
	}
	fmt.Println("[+] All opcodes encoded and verified successfully!")

	// 6. Test VM execution
	vmRes, vmFinalState := runRealVM(encodedProg, stage2Out, targetT)
	if vmRes != 1 {
		fmt.Printf("[-] Real VM test run returned %d, expected 1\n", vmRes)
		os.Exit(1)
	}
	fmt.Printf("[+] Real VM executed successfully! R0=%d\n", vmRes)
	fmt.Printf("[+] VM Final State: A=0x%016X B=0x%016X C=0x%016X D=0x%016X Counter=%d\n",
		vmFinalState.A, vmFinalState.B, vmFinalState.C, vmFinalState.D, vmFinalState.Counter)

	// Verify state matches targetT
	if vmFinalState.A != targetT[0] || vmFinalState.B != targetT[1] || vmFinalState.C != targetT[2] || vmFinalState.D != targetT[3] {
		fmt.Println("[-] VM Final state did not match targetT!")
		os.Exit(1)
	}
	fmt.Println("[+] Final state matches targetT perfectly!")

	// Print Go code snippets to paste into src/
	fmt.Println("\n=== Go Data Definitions for src/ ===")
	fmt.Printf("// Bytecode\nvar RealVMBytecode = []byte{\n\t")
	for i, b := range encodedProg {
		fmt.Printf("0x%02x, ", b)
		if (i+1)%12 == 0 {
			fmt.Printf("\n\t")
		}
	}
	fmt.Printf("\n}\n\n")

	fmt.Printf("// Target Constants\nvar TargetConstants = [4]uint64{\n")
	for i := 0; i < 4; i++ {
		fmt.Printf("\t0x%016X,\n", targetT[i])
	}
	fmt.Printf("}\n\n")

	fmt.Printf("// Stage 1 Checksum\nconst Stage1ExpectedChecksum uint32 = 0x%08X\n\n", csum)

	fmt.Printf("// Encrypted Flag Fragments\n")
	for i := 0; i < 4; i++ {
		fmt.Printf("var Fragment%d = []byte{", i)
		for _, b := range fragments[i] {
			fmt.Printf("0x%02x, ", b)
		}
		fmt.Printf("}\n")
	}
}

// Opcode Definitions
const (
	OP_NOP        byte = 0x01
	OP_MOV_REG    byte = 0x02
	OP_MOV_IMM    byte = 0x03
	OP_LOAD8      byte = 0x04
	OP_STORE8     byte = 0x05
	OP_LOAD64     byte = 0x06
	OP_STORE64    byte = 0x07
	OP_ADD        byte = 0x08
	OP_SUB        byte = 0x09
	OP_XOR        byte = 0x0A
	OP_AND        byte = 0x0B
	OP_OR         byte = 0x0C
	OP_ROL_IMM    byte = 0x0D
	OP_ROR_IMM    byte = 0x0E
	OP_MUL        byte = 0x0F
	OP_CMP        byte = 0x10
	OP_JMP        byte = 0x11
	OP_JZ         byte = 0x12
	OP_JNZ        byte = 0x13
	OP_PUSH       byte = 0x14
	OP_POP        byte = 0x15
	OP_SYNC_STATE byte = 0x16
	OP_HALT       byte = 0x17
)

// Opcode Encode / Decode
func rotl8(b byte, n byte) byte {
	return (b << (n & 7)) | (b >> (8 - (n & 7)))
}

func rotr8(b byte, n byte) byte {
	return (b >> (n & 7)) | (b << (8 - (n & 7)))
}

func encodeOpcode(op byte, pos uint64, seed uint64, phase uint32) byte {
	k := byte((seed >> ((pos % 7) * 8)) & 0xFF)
	shift := byte((pos % 5) + 1)
	r := rotl8(op, shift)
	enc := r ^ k ^ byte(phase*17) ^ byte(pos&0x3F)
	return enc
}

func decodeOpcode(enc byte, pos uint64, seed uint64, phase uint32) byte {
	k := byte((seed >> ((pos % 7) * 8)) & 0xFF)
	shift := byte((pos % 5) + 1)
	r := enc ^ k ^ byte(phase*17) ^ byte(pos&0x3F)
	op := rotr8(r, shift)
	return op
}

// Assemble Real VM Program
func assembleRealVM() []byte {
	var code []byte

	emit := func(op, dst, src, imm byte) {
		code = append(code, op, dst, src, imm)
	}

	emitImm16 := func(op, dst byte, imm uint16) {
		code = append(code, op, dst, byte(imm>>8), byte(imm&0xFF))
	}

	// 1. Load 4 input blocks into R8, R9, R10, R11 from 0x0100
	emitImm16(OP_MOV_IMM, 12, 0x0100) // R12 = 0x0100
	emit(OP_LOAD64, 8, 12, 0)         // R8 = Mem64[R12 + 0]
	emit(OP_LOAD64, 9, 12, 8)         // R9 = Mem64[R12 + 8]
	emit(OP_LOAD64, 10, 12, 16)       // R10 = Mem64[R12 + 16]
	emit(OP_LOAD64, 11, 12, 24)       // R11 = Mem64[R12 + 24]

	// 2. Base pointer for round constants at 0x0000 -> R7
	emitImm16(OP_MOV_IMM, 7, 0x0000)

	// 3. 8 Rounds of ARX
	for round := 0; round < 8; round++ {
		// R1 = Mem64[R7 + round*8]
		emit(OP_LOAD64, 1, 7, byte(round*8))

		// R8 = R8 + R9 + R1
		emit(OP_ADD, 8, 9, 0)
		emit(OP_ADD, 8, 1, 0)

		// R11 = (R11 ^ R8) ROL 17
		emit(OP_XOR, 11, 8, 0)
		emit(OP_ROL_IMM, 11, 0, 17)

		// R10 = R10 + R11
		emit(OP_ADD, 10, 11, 0)

		// R9 = (R9 ^ R10) ROR 19
		emit(OP_XOR, 9, 10, 0)
		emit(OP_ROR_IMM, 9, 0, 19)

		// R8 = R8 + R9
		emit(OP_ADD, 8, 9, 0)

		// R11 = (R11 ^ R8) ROL 23
		emit(OP_XOR, 11, 8, 0)
		emit(OP_ROL_IMM, 11, 0, 23)

		// R10 = R10 + R11 + R1
		emit(OP_ADD, 10, 11, 0)
		emit(OP_ADD, 10, 1, 0)

		// R9 = (R9 ^ R10) ROR 29
		emit(OP_XOR, 9, 10, 0)
		emit(OP_ROR_IMM, 9, 0, 29)
	}

	// 4. Compare with Targets at 0x0120
	emitImm16(OP_MOV_IMM, 12, 0x0120) // R12 = 0x0120

	// Check R8 == Target[0]
	emit(OP_LOAD64, 1, 12, 0)
	emit(OP_CMP, 8, 1, 0)
	failLabelRel1 := len(code)
	emitImm16(OP_JNZ, 0, 0) // placeholder

	// Check R9 == Target[1]
	emit(OP_LOAD64, 1, 12, 8)
	emit(OP_CMP, 9, 1, 0)
	failLabelRel2 := len(code)
	emitImm16(OP_JNZ, 0, 0) // placeholder

	// Check R10 == Target[2]
	emit(OP_LOAD64, 1, 12, 16)
	emit(OP_CMP, 10, 1, 0)
	failLabelRel3 := len(code)
	emitImm16(OP_JNZ, 0, 0) // placeholder

	// Check R11 == Target[3]
	emit(OP_LOAD64, 1, 12, 24)
	emit(OP_CMP, 11, 1, 0)
	failLabelRel4 := len(code)
	emitImm16(OP_JNZ, 0, 0) // placeholder

	// SUCCESS:
	emitImm16(OP_MOV_IMM, 0, 1) // R0 = 1
	emit(OP_SYNC_STATE, 0, 0, 0)
	emit(OP_HALT, 0, 0, 0)

	// FAIL:
	failTarget := len(code)
	emitImm16(OP_MOV_IMM, 0, 0) // R0 = 0
	emit(OP_HALT, 0, 0, 0)

	// Patch JNZ offsets (relative in bytes)
	patchJump := func(offset int, target int) {
		rel := target - (offset + 4)
		code[offset+2] = byte(rel >> 8)
		code[offset+3] = byte(rel & 0xFF)
	}

	patchJump(failLabelRel1, failTarget)
	patchJump(failLabelRel2, failTarget)
	patchJump(failLabelRel3, failTarget)
	patchJump(failLabelRel4, failTarget)

	return code
}

// Runtime State struct
type RuntimeState struct {
	A       uint64
	B       uint64
	C       uint64
	D       uint64
	Counter uint64
	Seed    uint64
	Phase   uint32
}

// Simple emulator for Real VM
func runRealVM(bytecode []byte, inputBlock [32]byte, targets [4]uint64) (uint64, RuntimeState) {
	state := RuntimeState{
		A:       0x736F756C7661756C,
		B:       0x745F6B65795F3234,
		C:       0xDEADBEEFCAFEBABE,
		D:       0x1337C0DE8BADF00D,
		Counter: 0,
		Seed:    InitialSeed,
		Phase:   InitialPhase,
	}

	var regs [16]uint64
	mem := make([]byte, 2048)

	// Initialize memory
	// 0x0000: Round constants
	for i := 0; i < 8; i++ {
		binary.LittleEndian.PutUint64(mem[i*8:(i+1)*8], RoundConstants[i])
	}
	// 0x0100: Transformed input block
	copy(mem[0x0100:0x0120], inputBlock[:])
	// 0x0120: Target constants
	for i := 0; i < 4; i++ {
		binary.LittleEndian.PutUint64(mem[0x0120+i*8:0x0120+(i+1)*8], targets[i])
	}

	ip := 0
	flags := 0 // 0: equal, 1: less, 2: greater

	for ip >= 0 && ip+4 <= len(bytecode) {
		pos := uint64(ip / 4)
		encOp := bytecode[ip]
		dst := bytecode[ip+1]
		src := bytecode[ip+2]
		imm8 := bytecode[ip+3]
		imm16 := (uint16(src) << 8) | uint16(imm8)

		op := decodeOpcode(encOp, pos, state.Seed, state.Phase)
		state.Counter++
		ip += 4

		switch op {
		case OP_NOP:
		case OP_MOV_REG:
			regs[dst] = regs[src]
		case OP_MOV_IMM:
			regs[dst] = uint64(imm16)
		case OP_LOAD8:
			addr := regs[src] + uint64(imm8)
			regs[dst] = uint64(mem[addr])
		case OP_STORE8:
			addr := regs[dst] + uint64(imm8)
			mem[addr] = byte(regs[src] & 0xFF)
		case OP_LOAD64:
			addr := regs[src] + uint64(imm8)
			regs[dst] = binary.LittleEndian.Uint64(mem[addr : addr+8])
		case OP_STORE64:
			addr := regs[dst] + uint64(imm8)
			binary.LittleEndian.PutUint64(mem[addr:addr+8], regs[src])
		case OP_ADD:
			regs[dst] = regs[dst] + regs[src]
		case OP_SUB:
			regs[dst] = regs[dst] - regs[src]
		case OP_XOR:
			regs[dst] = regs[dst] ^ regs[src]
		case OP_AND:
			regs[dst] = regs[dst] & regs[src]
		case OP_OR:
			regs[dst] = regs[dst] | regs[src]
		case OP_ROL_IMM:
			regs[dst] = rotl64(regs[dst], uint(imm8))
		case OP_ROR_IMM:
			regs[dst] = rotr64(regs[dst], uint(imm8))
		case OP_MUL:
			regs[dst] = regs[dst] * regs[src]
		case OP_CMP:
			if regs[dst] == regs[src] {
				flags = 0
			} else if regs[dst] < regs[src] {
				flags = 1
			} else {
				flags = 2
			}
		case OP_JMP:
			rel := int16(imm16)
			ip += int(rel)
		case OP_JZ:
			if flags == 0 {
				rel := int16(imm16)
				ip += int(rel)
			}
		case OP_JNZ:
			if flags != 0 {
				rel := int16(imm16)
				ip += int(rel)
			}
		case OP_SYNC_STATE:
			state.A = regs[8]
			state.B = regs[9]
			state.C = regs[10]
			state.D = regs[11]
		case OP_HALT:
			return regs[0], state
		default:
			panic(fmt.Sprintf("unknown opcode 0x%02x at ip %d", op, ip-4))
		}
	}

	return regs[0], state
}

