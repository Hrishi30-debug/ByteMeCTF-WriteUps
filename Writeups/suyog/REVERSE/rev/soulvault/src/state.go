package main

import (
	"encoding/binary"
	"math/bits"
)

// RuntimeState represents the persistent execution state across the validation lifecycle.
type RuntimeState struct {
	A       uint64
	B       uint64
	C       uint64
	D       uint64
	Counter uint64
	Seed    uint64
	Phase   uint32
}

const (
	SeedConst1 uint64 = 0x5A17F00DC0FFEE11
	SeedConst2 uint64 = 0xDEADBEEFCAFEBABE
	SeedConst3 uint64 = 0x1337C0DE8BADF00D
	PhaseInit  uint32 = 0x1
)

// NewInitialState instantiates a deterministic state structure.
func NewInitialState() RuntimeState {
	return RuntimeState{
		A:       0x736F756C7661756C, // "soulvaul"
		B:       0x745F6B65795F3234, // "t_key_24"
		C:       SeedConst2,
		D:       SeedConst3,
		Counter: 0,
		Seed:    SeedConst1,
		Phase:   PhaseInit,
	}
}

// MutateStep advances the runtime seed and phase deterministically.
func (s *RuntimeState) MutateStep(tag uint32) {
	s.Counter++
	s.Seed = bits.RotateLeft64(s.Seed^uint64(tag), 13) + 0x9E3779B97F4A7C15
	s.Phase = (s.Phase*31 + tag) & 0x0FFFFFFF
}

// EntropyFeed incorporates an external block of bytes into the running state.
func (s *RuntimeState) EntropyFeed(buf []byte) {
	for i := 0; i+8 <= len(buf); i += 8 {
		chunk := binary.LittleEndian.Uint64(buf[i : i+8])
		s.A ^= bits.RotateLeft64(chunk, 17)
		s.B += chunk + s.Seed
		s.C = bits.RotateLeft64(s.C+chunk, 29)
		s.D ^= bits.RotateLeft64(s.D+s.Seed, 37)
		s.Counter++
	}
}

// ExportStateDigest returns a 32-byte digest of the runtime state.
func (s *RuntimeState) ExportStateDigest() [32]byte {
	var out [32]byte
	binary.LittleEndian.PutUint64(out[0:8], s.A)
	binary.LittleEndian.PutUint64(out[8:16], s.B)
	binary.LittleEndian.PutUint64(out[16:24], s.C)
	binary.LittleEndian.PutUint64(out[24:32], s.D)
	return out
}
