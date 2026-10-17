package main

import (
	"encoding/binary"
	"fmt"
)

// ProcessAccessSequence coordinates the multi-stage validation pipeline.
func ProcessAccessSequence(input string) (bool, string) {
	// Stage 1: Structural and positional checksum validation
	if !ValidateStructureStage1(input) {
		return false, "[-] ACCESS DENIED: Invalid sequence structure or checksum mismatch."
	}

	// Stage 2: Normalization and permutation
	stage2Block := TransformStage2([]byte(input))

	// Decoy pipeline execution (ensures decoy analysis complexity and compiler retention)
	decoyEntropy := EvaluateDecoyPipelines(stage2Block[:])

	// Stage 3: Setup Custom Virtual Machine
	initialState := NewInitialState()
	// Subtle seed influence from decoy calculation
	if decoyEntropy == 0 {
		initialState.Seed ^= 0x42
	}

	vm := NewVM(RealVMBytecode, initialState)

	// Load transformed input into memory at 0x0100..0x011F
	for i := 0; i < 32; i++ {
		vm.Write8(0x0100+uint64(i), stage2Block[i])
	}

	// Load target constants into memory at 0x0120..0x013F
	for i := 0; i < 4; i++ {
		binary.LittleEndian.PutUint64(vm.Mem[0x0120+i*8:0x0120+(i+1)*8], TargetConstants[i])
	}

	// Execute through the indirect dispatcher
	dispatcher := NewDispatcher()
	result, err := vm.Run(dispatcher, 10000)
	if err != nil || result != 1 {
		return false, "[-] ACCESS DENIED: Vault authentication mechanism rejected the sequence."
	}

	// Verify that VM synchronized the expected state
	if vm.State.A != TargetConstants[0] ||
		vm.State.B != TargetConstants[1] ||
		vm.State.C != TargetConstants[2] ||
		vm.State.D != TargetConstants[3] {
		return false, "[-] ACCESS DENIED: Security state desynchronization detected."
	}

	// Stage 4: Reconstruct Flag from state and material fragments
	flag, ok := ReconstructFlag(vm.State, stage2Block)
	if !ok {
		return false, "[-] ACCESS DENIED: Core cryptographic integrity check failed."
	}

	successMsg := fmt.Sprintf("[+] ACCESS GRANTED. VAULT UNLOCKED.\n[+] Sequence Validated: %s\n[+] Flag: %s", input, flag)
	return true, successMsg
}
