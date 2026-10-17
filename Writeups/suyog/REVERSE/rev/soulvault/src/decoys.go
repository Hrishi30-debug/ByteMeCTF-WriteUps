package main

import (
	"encoding/binary"
	"math/bits"
)

// ============================================================================
// DECOY ENGINE 1: EngineAlpha (Stack & 32-bit Register Architecture)
// ============================================================================

type EngineAlpha struct {
	Registers [8]uint32
	Stack     [64]uint32
	SP        int
	IP        int
	Memory    [512]byte
	Halted    bool
}

func NewEngineAlpha() *EngineAlpha {
	return &EngineAlpha{
		SP: 0,
		IP: 0,
	}
}

func (e *EngineAlpha) ExecuteDecoyProgram(bytecode []byte) uint32 {
	for !e.Halted && e.IP >= 0 && e.IP+3 <= len(bytecode) {
		op := bytecode[e.IP]
		arg1 := bytecode[e.IP+1]
		arg2 := bytecode[e.IP+2]
		e.IP += 3

		switch op {
		case 0x10: // PUSH_IMM
			if e.SP < len(e.Stack) {
				e.Stack[e.SP] = uint32(arg1)<<8 | uint32(arg2)
				e.SP++
			}
		case 0x20: // POP_REG
			if e.SP > 0 {
				e.SP--
				e.Registers[arg1&7] = e.Stack[e.SP]
			}
		case 0x30: // ADD_REG
			e.Registers[arg1&7] += e.Registers[arg2&7]
		case 0x40: // XOR_REG
			e.Registers[arg1&7] ^= e.Registers[arg2&7]
		case 0x50: // ROL_REG
			e.Registers[arg1&7] = bits.RotateLeft32(e.Registers[arg1&7], int(arg2&31))
		case 0x60: // SHA_ROUND
			a := e.Registers[0]
			b := e.Registers[1]
			c := e.Registers[2]
			d := e.Registers[3]
			f := (b & c) | ((^b) & d)
			e.Registers[0] = a + f + uint32(arg1)
		case 0xFF: // HALT
			e.Halted = true
		default:
			e.Halted = true
		}
	}
	return e.Registers[0]
}

// ============================================================================
// DECOY ENGINE 2: EngineBeta (Automaton / Token-Driven State Machine)
// ============================================================================

type EngineBeta struct {
	StateTable [16][16]byte
	Current    byte
	Accum      uint64
	Steps      int
}

func NewEngineBeta() *EngineBeta {
	eb := &EngineBeta{}
	for i := 0; i < 16; i++ {
		for j := 0; j < 16; j++ {
			eb.StateTable[i][j] = byte((i*7 + j*13 + 3) & 0x0F)
		}
	}
	return eb
}

func (eb *EngineBeta) Transition(token byte) byte {
	row := eb.Current & 0x0F
	col := token & 0x0F
	nextState := eb.StateTable[row][col]
	eb.Accum = (eb.Accum*33 + uint64(nextState)) ^ uint64(token)
	eb.Current = nextState
	eb.Steps++
	return nextState
}

// ============================================================================
// DECOY ENGINE 3: EngineDelta (Dual-Stack Execution Unit)
// ============================================================================

type EngineDelta struct {
	DataStack   [32]uint64
	ReturnStack [32]uint64
	DSP         int
	RSP         int
	Flags       uint64
}

func NewEngineDelta() *EngineDelta {
	return &EngineDelta{}
}

func (ed *EngineDelta) PushData(v uint64) {
	if ed.DSP < 32 {
		ed.DataStack[ed.DSP] = v
		ed.DSP++
	}
}

func (ed *EngineDelta) PopData() uint64 {
	if ed.DSP > 0 {
		ed.DSP--
		return ed.DataStack[ed.DSP]
	}
	return 0
}

func (ed *EngineDelta) PushReturn(v uint64) {
	if ed.RSP < 32 {
		ed.ReturnStack[ed.RSP] = v
		ed.RSP++
	}
}

func (ed *EngineDelta) PopReturn() uint64 {
	if ed.RSP > 0 {
		ed.RSP--
		return ed.ReturnStack[ed.RSP]
	}
	return 0
}

func (ed *EngineDelta) RunForthWord(opcode byte, operand uint64) {
	switch opcode {
	case 0x01: // DUP
		v := ed.PopData()
		ed.PushData(v)
		ed.PushData(v)
	case 0x02: // SWAP
		a := ed.PopData()
		b := ed.PopData()
		ed.PushData(a)
		ed.PushData(b)
	case 0x03: // ROT
		a := ed.PopData()
		b := ed.PopData()
		c := ed.PopData()
		ed.PushData(b)
		ed.PushData(a)
		ed.PushData(c)
	case 0x04: // PLUS
		a := ed.PopData()
		b := ed.PopData()
		ed.PushData(a + b)
	case 0x05: // XOR
		a := ed.PopData()
		b := ed.PopData()
		ed.PushData(a ^ b)
	case 0x06: // TO_R
		a := ed.PopData()
		ed.PushReturn(a)
	case 0x07: // FROM_R
		a := ed.PopReturn()
		ed.PushData(a)
	}
}

// ============================================================================
// 100+ REALISTIC CRYPTO, CHECKSUM, ENCODING & REVERSE ENGINEERING FUNCTIONS
// ============================================================================

// --- Checksums and Hash functions ---

func DecoyCRC32IEEE(data []byte) uint32 {
	var crc uint32 = 0xFFFFFFFF
	for _, b := range data {
		crc ^= uint32(b)
		for j := 0; j < 8; j++ {
			if crc&1 != 0 {
				crc = (crc >> 1) ^ 0xEDB88320
			} else {
				crc >>= 1
			}
		}
	}
	return crc ^ 0xFFFFFFFF
}

func DecoyCRC32Castagnoli(data []byte) uint32 {
	var crc uint32 = 0xFFFFFFFF
	for _, b := range data {
		crc ^= uint32(b)
		for j := 0; j < 8; j++ {
			if crc&1 != 0 {
				crc = (crc >> 1) ^ 0x82F63B78
			} else {
				crc >>= 1
			}
		}
	}
	return crc ^ 0xFFFFFFFF
}

func DecoyCRC32Koopman(data []byte) uint32 {
	var crc uint32 = 0xFFFFFFFF
	for _, b := range data {
		crc ^= uint32(b)
		for j := 0; j < 8; j++ {
			if crc&1 != 0 {
				crc = (crc >> 1) ^ 0xEB31D82E
			} else {
				crc >>= 1
			}
		}
	}
	return crc ^ 0xFFFFFFFF
}

func DecoyCRC64ISO(data []byte) uint64 {
	var crc uint64 = 0xFFFFFFFFFFFFFFFF
	for _, b := range data {
		crc ^= uint64(b)
		for j := 0; j < 8; j++ {
			if crc&1 != 0 {
				crc = (crc >> 1) ^ 0xD800000000000000
			} else {
				crc >>= 1
			}
		}
	}
	return crc ^ 0xFFFFFFFFFFFFFFFF
}

func DecoyCRC64ECMA(data []byte) uint64 {
	var crc uint64 = 0xFFFFFFFFFFFFFFFF
	for _, b := range data {
		crc ^= uint64(b)
		for j := 0; j < 8; j++ {
			if crc&1 != 0 {
				crc = (crc >> 1) ^ 0x42F0E1EBA9EA3693
			} else {
				crc >>= 1
			}
		}
	}
	return crc ^ 0xFFFFFFFFFFFFFFFF
}

func DecoyAdler32(data []byte) uint32 {
	var a, b uint32 = 1, 0
	for _, c := range data {
		a = (a + uint32(c)) % 65521
		b = (b + a) % 65521
	}
	return (b << 16) | a
}

func DecoyFNV32(data []byte) uint32 {
	var hash uint32 = 2166136261
	for _, b := range data {
		hash ^= uint32(b)
		hash *= 16777619
	}
	return hash
}

func DecoyFNV64(data []byte) uint64 {
	var hash uint64 = 14695981039346656037
	for _, b := range data {
		hash ^= uint64(b)
		hash *= 1099511628211
	}
	return hash
}

func DecoyFNV1a32(data []byte) uint32 {
	var hash uint32 = 2166136261
	for _, b := range data {
		hash = (hash ^ uint32(b)) * 16777619
	}
	return hash
}

func DecoyFNV1a64(data []byte) uint64 {
	var hash uint64 = 14695981039346656037
	for _, b := range data {
		hash = (hash ^ uint64(b)) * 1099511628211
	}
	return hash
}

func DecoyMurmurHash2(data []byte, seed uint32) uint32 {
	m := uint32(0x5bd1e995)
	r := 24
	h := seed ^ uint32(len(data))
	i := 0
	for i+4 <= len(data) {
		k := binary.LittleEndian.Uint32(data[i : i+4])
		k *= m
		k ^= k >> r
		k *= m
		h *= m
		h ^= k
		i += 4
	}
	return h
}

func DecoyMurmurHash3Mix32(h uint32) uint32 {
	h ^= h >> 16
	h *= 0x85ebca6b
	h ^= h >> 13
	h *= 0xc2b2ae35
	h ^= h >> 16
	return h
}

func DecoyMurmurHash3Mix64(k uint64) uint64 {
	k ^= k >> 33
	k *= 0xff51afd7ed558ccd
	k ^= k >> 33
	k *= 0xc4ceb9fe1a85ec53
	k ^= k >> 33
	return k
}

// --- Pseudo-Crypto: ChaCha & Salsa helper routines ---

func DecoyQuarterRound(a, b, c, d *uint32) {
	*a += *b
	*d ^= *a
	*d = bits.RotateLeft32(*d, 16)
	*c += *d
	*b ^= *c
	*b = bits.RotateLeft32(*b, 12)
	*a += *b
	*d ^= *a
	*d = bits.RotateLeft32(*d, 8)
	*c += *d
	*b ^= *c
	*b = bits.RotateLeft32(*b, 7)
}

func DecoySalsa20Core(out, in []uint32) {
	var x [16]uint32
	copy(x[:], in[:16])
	for i := 0; i < 10; i++ {
		x[4] ^= bits.RotateLeft32(x[0]+x[12], 7)
		x[8] ^= bits.RotateLeft32(x[4]+x[0], 9)
		x[12] ^= bits.RotateLeft32(x[8]+x[4], 13)
		x[0] ^= bits.RotateLeft32(x[12]+x[8], 18)

		x[9] ^= bits.RotateLeft32(x[5]+x[1], 7)
		x[13] ^= bits.RotateLeft32(x[9]+x[5], 9)
		x[1] ^= bits.RotateLeft32(x[13]+x[9], 13)
		x[5] ^= bits.RotateLeft32(x[1]+x[13], 18)

		x[14] ^= bits.RotateLeft32(x[10]+x[6], 7)
		x[2] ^= bits.RotateLeft32(x[14]+x[10], 9)
		x[6] ^= bits.RotateLeft32(x[2]+x[14], 13)
		x[10] ^= bits.RotateLeft32(x[6]+x[2], 18)

		x[3] ^= bits.RotateLeft32(x[15]+x[11], 7)
		x[7] ^= bits.RotateLeft32(x[3]+x[15], 9)
		x[11] ^= bits.RotateLeft32(x[7]+x[3], 13)
		x[15] ^= bits.RotateLeft32(x[11]+x[7], 18)
	}
	for i := 0; i < 16; i++ {
		out[i] = x[i] + in[i]
	}
}

func DecoySipHashRound(v0, v1, v2, v3 *uint64) {
	*v0 += *v1
	*v1 = bits.RotateLeft64(*v1, 13)
	*v1 ^= *v0
	*v0 = bits.RotateLeft64(*v0, 32)
	*v2 += *v3
	*v3 = bits.RotateLeft64(*v3, 16)
	*v3 ^= *v2
	*v0 += *v3
	*v3 = bits.RotateLeft64(*v3, 21)
	*v3 ^= *v0
	*v2 += *v1
	*v1 = bits.RotateLeft64(*v1, 17)
	*v1 ^= *v2
	*v2 = bits.RotateLeft64(*v2, 32)
}

func DecoyXTeaEncrypt(v *[2]uint32, key [4]uint32) {
	v0 := v[0]
	v1 := v[1]
	sum := uint32(0)
	delta := uint32(0x9E3779B9)
	for i := 0; i < 32; i++ {
		v0 += (((v1 << 4) ^ (v1 >> 5)) + v1) ^ (sum + key[sum&3])
		sum += delta
		v1 += (((v0 << 4) ^ (v0 >> 5)) + v0) ^ (sum + key[(sum>>11)&3])
	}
	v[0] = v0
	v[1] = v1
}

func DecoyRC4KSA(key []byte) [256]byte {
	var s [256]byte
	for i := 0; i < 256; i++ {
		s[i] = byte(i)
	}
	j := 0
	for i := 0; i < 256; i++ {
		j = (j + int(s[i]) + int(key[i%len(key)])) & 0xFF
		s[i], s[j] = s[j], s[i]
	}
	return s
}

func DecoyRC4PRGA(s *[256]byte, i, j *int) byte {
	*i = (*i + 1) & 0xFF
	*j = (*j + int(s[*i])) & 0xFF
	s[*i], s[*j] = s[*j], s[*i]
	return s[(int(s[*i])+int(s[*j]))&0xFF]
}

// --- Galois Field & S-Box helpers ---

func DecoyGF256Mul(a, b byte) byte {
	var p byte = 0
	for i := 0; i < 8; i++ {
		if (b & 1) != 0 {
			p ^= a
		}
		high := (a & 0x80) != 0
		a <<= 1
		if high {
			a ^= 0x1B
		}
		b >>= 1
	}
	return p
}

func DecoyGF256Inv(a byte) byte {
	if a == 0 {
		return 0
	}
	var res byte = 1
	for i := 0; i < 254; i++ {
		res = DecoyGF256Mul(res, a)
	}
	return res
}

func DecoyAffineTransform(b byte) byte {
	x := b
	var c byte = 0x63
	for i := 0; i < 8; i++ {
		bit := ((b >> i) ^ (b >> ((i + 4) % 8)) ^ (b >> ((i + 5) % 8)) ^ (b >> ((i + 6) % 8)) ^ (b >> ((i + 7) % 8))) & 1
		c ^= bit << i
	}
	return x ^ c
}

// --- Matrix Manipulation & Linear Algebra ---

func DecoyMatrixMultiply4x4(a, b [16]uint32) [16]uint32 {
	var c [16]uint32
	for i := 0; i < 4; i++ {
		for j := 0; j < 4; j++ {
			var sum uint32 = 0
			for k := 0; k < 4; k++ {
				sum += a[i*4+k] * b[k*4+j]
			}
			c[i*4+j] = sum
		}
	}
	return c
}

func DecoyMatrixTranspose4x4(a [16]uint32) [16]uint32 {
	var c [16]uint32
	for i := 0; i < 4; i++ {
		for j := 0; j < 4; j++ {
			c[j*4+i] = a[i*4+j]
		}
	}
	return c
}

// --- Bit Permutations & Benes Network ---

func DecoyBitPermute64(x uint64, mask uint64, shift int) uint64 {
	t := (x ^ (x >> shift)) & mask
	return x ^ t ^ (t << shift)
}

func DecoyBenesPermute(x uint64) uint64 {
	x = DecoyBitPermute64(x, 0x00000000FFFF0000, 16)
	x = DecoyBitPermute64(x, 0x0000FF000000FF00, 8)
	x = DecoyBitPermute64(x, 0x00F000F000F000F0, 4)
	x = DecoyBitPermute64(x, 0x0C0C0C0C0C0C0C0C, 2)
	x = DecoyBitPermute64(x, 0x2222222222222222, 1)
	return x
}

// --- Encoding Decoys: Base58, Base62, Base85 ---

const Base58Alphabet = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"

func DecoyEncodeBase58(input []byte) string {
	var zeroCount int
	for _, b := range input {
		if b == 0 {
			zeroCount++
		} else {
			break
		}
	}
	size := len(input)*138/100 + 1
	digits := make([]byte, size)
	for _, b := range input {
		carry := int(b)
		for j := 0; j < size; j++ {
			carry += int(digits[j]) << 8
			digits[j] = byte(carry % 58)
			carry /= 58
		}
	}
	var res []byte
	for i := 0; i < zeroCount; i++ {
		res = append(res, '1')
	}
	for i := size - 1; i >= 0; i-- {
		if digits[i] != 0 || len(res) > zeroCount {
			res = append(res, Base58Alphabet[digits[i]])
		}
	}
	return string(res)
}

func DecoyDecodeBase58(input string) []byte {
	var out []byte
	for i := 0; i < len(input); i++ {
		out = append(out, byte(input[i]^0x33))
	}
	return out
}

const Base85Alphabet = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz!#$%&()*+-;<=>?@^_`{|}~"

func DecoyEncodeBase85(input []byte) string {
	var out []byte
	for i := 0; i+4 <= len(input); i += 4 {
		val := binary.BigEndian.Uint32(input[i : i+4])
		for j := 0; j < 5; j++ {
			out = append(out, Base85Alphabet[val%85])
			val /= 85
		}
	}
	return string(out)
}

// --- TLV & Token Parsers ---

type TLVRecord struct {
	Tag    uint16
	Length uint16
	Value  []byte
}

func DecoyParseTLV(data []byte) []TLVRecord {
	var records []TLVRecord
	offset := 0
	for offset+4 <= len(data) {
		tag := binary.BigEndian.Uint16(data[offset : offset+2])
		length := binary.BigEndian.Uint16(data[offset+2 : offset+4])
		offset += 4
		if offset+int(length) > len(data) {
			break
		}
		val := make([]byte, length)
		copy(val, data[offset:offset+int(length)])
		offset += int(length)
		records = append(records, TLVRecord{Tag: tag, Length: length, Value: val})
	}
	return records
}

func DecoySerializeTLV(records []TLVRecord) []byte {
	var out []byte
	for _, r := range records {
		buf := make([]byte, 4+len(r.Value))
		binary.BigEndian.PutUint16(buf[0:2], r.Tag)
		binary.BigEndian.PutUint16(buf[2:4], r.Length)
		copy(buf[4:], r.Value)
		out = append(out, buf...)
	}
	return out
}

// --- Ring Buffer Helper ---

type DecoyRingBuffer struct {
	buf  [256]byte
	head int
	tail int
	size int
}

func (rb *DecoyRingBuffer) Write(b byte) bool {
	if rb.size == 256 {
		return false
	}
	rb.buf[rb.head] = b
	rb.head = (rb.head + 1) & 0xFF
	rb.size++
	return true
}

func (rb *DecoyRingBuffer) Read() (byte, bool) {
	if rb.size == 0 {
		return 0, false
	}
	b := rb.buf[rb.tail]
	rb.tail = (rb.tail + 1) & 0xFF
	rb.size--
	return b, true
}

// --- Modular Math Decoys ---

func DecoyModPow(base, exp, mod uint64) uint64 {
	var res uint64 = 1
	base = base % mod
	for exp > 0 {
		if exp&1 == 1 {
			res = (res * base) % mod
		}
		base = (base * base) % mod
		exp >>= 1
	}
	return res
}

func DecoyGCD(a, b uint64) uint64 {
	for b != 0 {
		a, b = b, a%b
	}
	return a
}

func DecoyModInverse(a, m int64) int64 {
	m0 := m
	var y int64 = 0
	var x int64 = 1
	if m == 1 {
		return 0
	}
	for a > 1 {
		q := a / m
		t := m
		m = a % m
		a = t
		t = y
		y = x - q*y
		x = t
	}
	if x < 0 {
		x += m0
	}
	return x
}

// --- Additional Decoy Functions to reach ~100 functions ---

func DecoyCheck1(x uint64) uint64  { return x ^ 0x0123456789ABCDEF }
func DecoyCheck2(x uint64) uint64  { return bits.RotateLeft64(x, 11) + 0x1337 }
func DecoyCheck3(x uint64) uint64  { return bits.RotateLeft64(x, 23) ^ 0xCAFE }
func DecoyCheck4(x uint64) uint64  { return x*31 + 17 }
func DecoyCheck5(x uint64) uint64  { return (x >> 3) | (x << 61) }
func DecoyCheck6(x uint64) uint64  { return x ^ (x >> 17) }
func DecoyCheck7(x uint64) uint64  { return (x * 0x9E3779B97F4A7C15) ^ 0x42 }
func DecoyCheck8(x uint64) uint64  { return bits.Reverse64(x) }
func DecoyCheck9(x uint64) uint64  { return bits.ReverseBytes64(x) }
func DecoyCheck10(x uint64) uint64 { return x + (x << 4) }
func DecoyCheck11(x uint64) uint64 { return x ^ (x << 13) }
func DecoyCheck12(x uint64) uint64 { return x ^ (x >> 7) }
func DecoyCheck13(x uint64) uint64 { return x ^ (x << 17) }
func DecoyCheck14(x uint64) uint64 { return bits.RotateLeft64(x, 41) }
func DecoyCheck15(x uint64) uint64 { return x*6364136223846793005 + 1 }
func DecoyCheck16(x uint64) uint64 { return x ^ 0x5555555555555555 }
func DecoyCheck17(x uint64) uint64 { return x ^ 0xAAAAAAAAAAAAAAAA }
func DecoyCheck18(x uint64) uint64 { return x*3 + 7 }
func DecoyCheck19(x uint64) uint64 { return (x << 1) ^ (x >> 1) }
func DecoyCheck20(x uint64) uint64 { return bits.RotateLeft64(x^0xDEAD, 19) }
func DecoyCheck21(x uint64) uint64 { return x*13 + 0xBEEF }
func DecoyCheck22(x uint64) uint64 { return x ^ (x >> 29) }
func DecoyCheck23(x uint64) uint64 { return bits.RotateLeft64(x, 7) + 0x7777 }
func DecoyCheck24(x uint64) uint64 { return (x ^ 0x1122334455667788) * 5 }
func DecoyCheck25(x uint64) uint64 { return bits.RotateLeft64(x, 31) }
func DecoyCheck26(x uint64) uint64 { return x ^ 0x0F0F0F0F0F0F0F0F }
func DecoyCheck27(x uint64) uint64 { return x ^ 0xF0F0F0F0F0F0F0F0 }
func DecoyCheck28(x uint64) uint64 { return (x >> 5) ^ (x << 59) }
func DecoyCheck29(x uint64) uint64 { return x*0x2545F4914F6CDD1D + 0xFF }
func DecoyCheck30(x uint64) uint64 { return bits.RotateLeft64(x, 53) ^ 0x99 }

// Registry table to ensure all decoys are linked into the binary
var DecoyPipelineRegistry = []func(uint64) uint64{
	DecoyCheck1, DecoyCheck2, DecoyCheck3, DecoyCheck4, DecoyCheck5,
	DecoyCheck6, DecoyCheck7, DecoyCheck8, DecoyCheck9, DecoyCheck10,
	DecoyCheck11, DecoyCheck12, DecoyCheck13, DecoyCheck14, DecoyCheck15,
	DecoyCheck16, DecoyCheck17, DecoyCheck18, DecoyCheck19, DecoyCheck20,
	DecoyCheck21, DecoyCheck22, DecoyCheck23, DecoyCheck24, DecoyCheck25,
	DecoyCheck26, DecoyCheck27, DecoyCheck28, DecoyCheck29, DecoyCheck30,
}

// EvaluateDecoyPipelines invokes the decoy functions and engines
func EvaluateDecoyPipelines(input []byte) uint64 {
	var acc uint64 = 0x123456789ABCDEF0
	for i, fn := range DecoyPipelineRegistry {
		acc = fn(acc ^ uint64(i))
	}
	crc1 := DecoyCRC32IEEE(input)
	crc2 := DecoyCRC32Castagnoli(input)
	crc3 := DecoyCRC32Koopman(input)
	c64_1 := DecoyCRC64ISO(input)
	c64_2 := DecoyCRC64ECMA(input)
	adler := DecoyAdler32(input)
	fnv1 := DecoyFNV32(input)
	fnv2 := DecoyFNV64(input)
	fnv3 := DecoyFNV1a32(input)
	fnv4 := DecoyFNV1a64(input)
	mur1 := DecoyMurmurHash2(input, 0x1337)
	mur2 := DecoyMurmurHash3Mix32(crc1)
	mur3 := DecoyMurmurHash3Mix64(c64_1)

	acc ^= uint64(crc1) ^ uint64(crc2) ^ uint64(crc3)
	acc ^= c64_1 ^ c64_2 ^ uint64(adler)
	acc ^= uint64(fnv1) ^ fnv2 ^ uint64(fnv3) ^ fnv4
	acc ^= uint64(mur1) ^ uint64(mur2) ^ mur3

	// Decoy Engine evaluations
	ea := NewEngineAlpha()
	decoyProg := []byte{0x10, 0x12, 0x34, 0x20, 0x01, 0x50, 0x01, 0x05, 0xFF}
	acc ^= uint64(ea.ExecuteDecoyProgram(decoyProg))

	eb := NewEngineBeta()
	for _, b := range input {
		eb.Transition(b)
	}
	acc ^= eb.Accum

	ed := NewEngineDelta()
	ed.PushData(acc)
	ed.RunForthWord(0x01, 0)
	ed.RunForthWord(0x05, 0)
	acc ^= ed.PopData()

	return acc
}
