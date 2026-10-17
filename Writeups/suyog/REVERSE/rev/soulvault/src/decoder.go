package main

import (
	"math/bits"
)

// Opcode constants
const (
	OpNop        byte = 0x01
	OpMovReg     byte = 0x02
	OpMovImm     byte = 0x03
	OpLoad8      byte = 0x04
	OpStore8     byte = 0x05
	OpLoad64     byte = 0x06
	OpStore64    byte = 0x07
	OpAdd        byte = 0x08
	OpSub        byte = 0x09
	OpXor        byte = 0x0A
	OpAnd        byte = 0x0B
	OpOr         byte = 0x0C
	OpRolImm     byte = 0x0D
	OpRorImm     byte = 0x0E
	OpMul        byte = 0x0F
	OpCmp        byte = 0x10
	OpJmp        byte = 0x11
	OpJz         byte = 0x12
	OpJnz        byte = 0x13
	OpPush       byte = 0x14
	OpPop        byte = 0x15
	OpSyncState  byte = 0x16
	OpHalt       byte = 0x17
)

// decodeOpcode decodes an obfuscated bytecode opcode into a runtime opcode.
// The transformation depends on instruction index, dynamic seed, and runtime phase.
func decodeOpcode(enc byte, pos uint64, seed uint64, phase uint32) byte {
	k := byte((seed >> ((pos % 7) * 8)) & 0xFF)
	shift := byte((pos % 5) + 1)
	r := enc ^ k ^ byte(phase*17) ^ byte(pos&0x3F)
	op := (r >> (shift & 7)) | (r << ((8 - (shift & 7)) & 7))
	return op
}

// rotl64 performs a 64-bit circular left shift.
func rotl64(x uint64, n uint) uint64 {
	return bits.RotateLeft64(x, int(n))
}

// rotr64 performs a 64-bit circular right shift.
func rotr64(x uint64, n uint) uint64 {
	return bits.RotateLeft64(x, -int(n))
}
