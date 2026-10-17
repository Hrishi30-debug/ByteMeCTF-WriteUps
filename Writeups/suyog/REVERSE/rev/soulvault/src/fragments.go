package main

import (
	"crypto/sha256"
	"encoding/binary"
)

// Encrypted Flag material partitioned into 4 distinct fragments
var Fragment0 = []byte{0xc0, 0x0e, 0x12, 0x3f, 0x7a, 0x91, 0xb4, 0x09, 0xad, 0xfe, 0x32, 0x6a}
var Fragment1 = []byte{0x54, 0x25, 0x27, 0x24, 0xa3, 0x99, 0xd9, 0x00, 0x85, 0x8c, 0xe4, 0xe7}
var Fragment2 = []byte{0x2a, 0x2e, 0xe6, 0x25, 0x71, 0x1b, 0xf6, 0x7c, 0xad, 0x75, 0xa6, 0xd3}
var Fragment3 = []byte{0xb8, 0x4e, 0xad, 0x35, 0xe6, 0x76, 0x45, 0xaf, 0x05, 0xe7, 0x9f}

// ReconstructFlag dynamically combines the fragments and state to recover the plaintext flag.
func ReconstructFlag(state RuntimeState, stage2Block [32]byte) (string, bool) {
	keyMaterial := make([]byte, 32)
	binary.LittleEndian.PutUint64(keyMaterial[0:8], state.A)
	binary.LittleEndian.PutUint64(keyMaterial[8:16], state.B)
	binary.LittleEndian.PutUint64(keyMaterial[16:24], state.C)
	binary.LittleEndian.PutUint64(keyMaterial[24:32], state.D)

	h := sha256.New()
	h.Write(keyMaterial)
	h.Write([]byte("SoulVault::MasterFlagKeystream::v1"))
	h.Write(stage2Block[:])
	keyHash1 := h.Sum(nil)

	h.Reset()
	h.Write(keyHash1)
	h.Write([]byte("SoulVault::SubStreamKey::v1"))
	keyHash2 := h.Sum(nil)

	keystream := append(keyHash1, keyHash2...)

	var combined []byte
	combined = append(combined, Fragment0...)
	combined = append(combined, Fragment1...)
	combined = append(combined, Fragment2...)
	combined = append(combined, Fragment3...)

	flagBuf := make([]byte, len(combined))
	for i := 0; i < len(combined); i++ {
		flagBuf[i] = combined[i] ^ keystream[i]
	}

	// Verify format
	if len(flagBuf) < 7 || string(flagBuf[:6]) != "OWASP{" || flagBuf[len(flagBuf)-1] != '}' {
		// Zeroize buffer
		for i := range flagBuf {
			flagBuf[i] = 0
		}
		return "", false
	}

	res := string(flagBuf)

	// Zeroize buffer immediately
	for i := range flagBuf {
		flagBuf[i] = 0
	}

	return res, true
}
