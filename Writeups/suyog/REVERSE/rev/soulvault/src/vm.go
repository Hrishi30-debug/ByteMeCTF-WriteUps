package main

import (
	"encoding/binary"
	"fmt"
)

const (
	VMFlagEqual   uint32 = 0x01
	VMFlagLess    uint32 = 0x02
	VMFlagGreater uint32 = 0x04

	VMMemorySize = 2048
	VMStackInit  = 0x07F8
)

// VM represents the virtual machine instance.
type VM struct {
	Regs     [16]uint64
	Mem      [VMMemorySize]byte
	IP       int
	SP       uint64
	Flags    uint32
	State    RuntimeState
	Halted   bool
	Bytecode []byte
}

// NewVM creates and initializes a VM instance with initial constants.
func NewVM(bytecode []byte, state RuntimeState) *VM {
	vm := &VM{
		IP:       0,
		SP:       VMStackInit,
		Flags:    0,
		State:    state,
		Halted:   false,
		Bytecode: bytecode,
	}

	// Initialize Round Constants into memory area 0x0000..0x003F
	for i := 0; i < 8; i++ {
		binary.LittleEndian.PutUint64(vm.Mem[i*8:(i+1)*8], RoundConstants[i])
	}

	return vm
}

// Read8 reads a byte from VM memory.
func (vm *VM) Read8(addr uint64) byte {
	if addr >= VMMemorySize {
		return 0
	}
	return vm.Mem[addr]
}

// Write8 writes a byte to VM memory.
func (vm *VM) Write8(addr uint64, val byte) {
	if addr < VMMemorySize {
		vm.Mem[addr] = val
	}
}

// Read64 reads a 64-bit integer from VM memory (little-endian).
func (vm *VM) Read64(addr uint64) uint64 {
	if addr+8 > VMMemorySize {
		return 0
	}
	return binary.LittleEndian.Uint64(vm.Mem[addr : addr+8])
}

// Write64 writes a 64-bit integer to VM memory (little-endian).
func (vm *VM) Write64(addr uint64, val uint64) {
	if addr+8 <= VMMemorySize {
		binary.LittleEndian.PutUint64(vm.Mem[addr:addr+8], val)
	}
}

// Push pushes a 64-bit value onto the virtual stack.
func (vm *VM) Push(val uint64) {
	if vm.SP >= 8 {
		vm.SP -= 8
		vm.Write64(vm.SP, val)
	}
}

// Pop pops a 64-bit value from the virtual stack.
func (vm *VM) Pop() uint64 {
	if vm.SP+8 <= VMMemorySize {
		val := vm.Read64(vm.SP)
		vm.SP += 8
		return val
	}
	return 0
}

// Step executes a single instruction through the dispatcher.
func (vm *VM) Step(d *Dispatcher) bool {
	if vm.Halted || vm.IP < 0 || vm.IP+4 > len(vm.Bytecode) {
		vm.Halted = true
		return false
	}

	pos := uint64(vm.IP / 4)
	encOp := vm.Bytecode[vm.IP]
	dst := vm.Bytecode[vm.IP+1]
	src := vm.Bytecode[vm.IP+2]
	imm8 := vm.Bytecode[vm.IP+3]
	imm16 := (uint16(src) << 8) | uint16(imm8)

	op := decodeOpcode(encOp, pos, vm.State.Seed, vm.State.Phase)
	vm.State.Counter++
	vm.IP += 4

	d.Dispatch(vm, op, dst, src, imm8, imm16)
	return !vm.Halted
}

// Run executes the bytecode until HALT or maximum step limit.
func (vm *VM) Run(d *Dispatcher, maxSteps int) (uint64, error) {
	steps := 0
	for !vm.Halted && vm.IP >= 0 && vm.IP+4 <= len(vm.Bytecode) {
		vm.Step(d)
		steps++
		if steps > maxSteps {
			return 0, fmt.Errorf("execution quota exceeded")
		}
	}
	return vm.Regs[0], nil
}
