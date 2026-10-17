package main

// HandlerFunc defines the signature for VM opcode handlers.
type HandlerFunc func(vm *VM, dst, src byte, imm8 byte, imm16 uint16)

// Dispatcher manages indirect handler tables and runtime permutation.
type Dispatcher struct {
	handlers   [256]HandlerFunc
	routeTable [256]byte
}

func defaultUnknownHandler(vm *VM, dst, src byte, imm8 byte, imm16 uint16) {
	vm.Halted = true
}

func handleNop(vm *VM, dst, src byte, imm8 byte, imm16 uint16) {}

func handleMovReg(vm *VM, dst, src byte, imm8 byte, imm16 uint16) {
	vm.Regs[dst&0x0F] = vm.Regs[src&0x0F]
}

func handleMovImm(vm *VM, dst, src byte, imm8 byte, imm16 uint16) {
	vm.Regs[dst&0x0F] = uint64(imm16)
}

func handleLoad8(vm *VM, dst, src byte, imm8 byte, imm16 uint16) {
	addr := vm.Regs[src&0x0F] + uint64(imm8)
	vm.Regs[dst&0x0F] = uint64(vm.Read8(addr))
}

func handleStore8(vm *VM, dst, src byte, imm8 byte, imm16 uint16) {
	addr := vm.Regs[dst&0x0F] + uint64(imm8)
	vm.Write8(addr, byte(vm.Regs[src&0x0F]&0xFF))
}

func handleLoad64(vm *VM, dst, src byte, imm8 byte, imm16 uint16) {
	addr := vm.Regs[src&0x0F] + uint64(imm8)
	vm.Regs[dst&0x0F] = vm.Read64(addr)
}

func handleStore64(vm *VM, dst, src byte, imm8 byte, imm16 uint16) {
	addr := vm.Regs[dst&0x0F] + uint64(imm8)
	vm.Write64(addr, vm.Regs[src&0x0F])
}

func handleAdd(vm *VM, dst, src byte, imm8 byte, imm16 uint16) {
	d := dst & 0x0F
	s := src & 0x0F
	vm.Regs[d] = vm.Regs[d] + vm.Regs[s]
}

func handleSub(vm *VM, dst, src byte, imm8 byte, imm16 uint16) {
	d := dst & 0x0F
	s := src & 0x0F
	vm.Regs[d] = vm.Regs[d] - vm.Regs[s]
}

func handleXor(vm *VM, dst, src byte, imm8 byte, imm16 uint16) {
	d := dst & 0x0F
	s := src & 0x0F
	vm.Regs[d] = vm.Regs[d] ^ vm.Regs[s]
}

func handleAnd(vm *VM, dst, src byte, imm8 byte, imm16 uint16) {
	d := dst & 0x0F
	s := src & 0x0F
	vm.Regs[d] = vm.Regs[d] & vm.Regs[s]
}

func handleOr(vm *VM, dst, src byte, imm8 byte, imm16 uint16) {
	d := dst & 0x0F
	s := src & 0x0F
	vm.Regs[d] = vm.Regs[d] | vm.Regs[s]
}

func handleRolImm(vm *VM, dst, src byte, imm8 byte, imm16 uint16) {
	d := dst & 0x0F
	vm.Regs[d] = rotl64(vm.Regs[d], uint(imm8))
}

func handleRorImm(vm *VM, dst, src byte, imm8 byte, imm16 uint16) {
	d := dst & 0x0F
	vm.Regs[d] = rotr64(vm.Regs[d], uint(imm8))
}

func handleMul(vm *VM, dst, src byte, imm8 byte, imm16 uint16) {
	d := dst & 0x0F
	s := src & 0x0F
	vm.Regs[d] = vm.Regs[d] * vm.Regs[s]
}

func handleCmp(vm *VM, dst, src byte, imm8 byte, imm16 uint16) {
	v1 := vm.Regs[dst&0x0F]
	v2 := vm.Regs[src&0x0F]
	if v1 == v2 {
		vm.Flags = VMFlagEqual
	} else if v1 < v2 {
		vm.Flags = VMFlagLess
	} else {
		vm.Flags = VMFlagGreater
	}
}

func handleJmp(vm *VM, dst, src byte, imm8 byte, imm16 uint16) {
	rel := int16(imm16)
	vm.IP += int(rel)
}

func handleJz(vm *VM, dst, src byte, imm8 byte, imm16 uint16) {
	if vm.Flags&VMFlagEqual != 0 {
		rel := int16(imm16)
		vm.IP += int(rel)
	}
}

func handleJnz(vm *VM, dst, src byte, imm8 byte, imm16 uint16) {
	if vm.Flags&VMFlagEqual == 0 {
		rel := int16(imm16)
		vm.IP += int(rel)
	}
}

func handlePush(vm *VM, dst, src byte, imm8 byte, imm16 uint16) {
	vm.Push(vm.Regs[src&0x0F])
}

func handlePop(vm *VM, dst, src byte, imm8 byte, imm16 uint16) {
	vm.Regs[dst&0x0F] = vm.Pop()
}

func handleSyncState(vm *VM, dst, src byte, imm8 byte, imm16 uint16) {
	vm.State.A = vm.Regs[8]
	vm.State.B = vm.Regs[9]
	vm.State.C = vm.Regs[10]
	vm.State.D = vm.Regs[11]
}

func handleHalt(vm *VM, dst, src byte, imm8 byte, imm16 uint16) {
	vm.Halted = true
}

// NewDispatcher constructs the indirect dispatch table.
func NewDispatcher() *Dispatcher {
	d := &Dispatcher{}
	for i := 0; i < 256; i++ {
		d.handlers[i] = defaultUnknownHandler
		d.routeTable[i] = byte(i)
	}

	// Register handlers at specific permutation indices
	register := func(op byte, slot byte, fn HandlerFunc) {
		d.routeTable[op] = slot
		d.handlers[slot] = fn
	}

	register(OpNop, 0x1A, handleNop)
	register(OpMovReg, 0x32, handleMovReg)
	register(OpMovImm, 0x4B, handleMovImm)
	register(OpLoad8, 0x55, handleLoad8)
	register(OpStore8, 0x6E, handleStore8)
	register(OpLoad64, 0x71, handleLoad64)
	register(OpStore64, 0x89, handleStore64)
	register(OpAdd, 0x93, handleAdd)
	register(OpSub, 0xA2, handleSub)
	register(OpXor, 0xBD, handleXor)
	register(OpAnd, 0xC4, handleAnd)
	register(OpOr, 0xD7, handleOr)
	register(OpRolImm, 0xEA, handleRolImm)
	register(OpRorImm, 0xF1, handleRorImm)
	register(OpMul, 0x28, handleMul)
	register(OpCmp, 0x3C, handleCmp)
	register(OpJmp, 0x63, handleJmp)
	register(OpJz, 0x7F, handleJz)
	register(OpJnz, 0x8C, handleJnz)
	register(OpPush, 0x9D, handlePush)
	register(OpPop, 0xAA, handlePop)
	register(OpSyncState, 0xB4, handleSyncState)
	register(OpHalt, 0xFE, handleHalt)

	return d
}

// Dispatch invokes the appropriate handler function via indirect table lookup.
func (d *Dispatcher) Dispatch(vm *VM, op, dst, src, imm8 byte, imm16 uint16) {
	slot := d.routeTable[op]
	d.handlers[slot](vm, dst, src, imm8, imm16)
}
