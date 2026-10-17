#include <stdio.h>
#include <stdint.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <sys/mman.h>

/*
 * SOUL VAULT
 * Reverse Engineering CTF
 *
 * Player receives only the compiled ELF.
 *
 * The challenge contains:
 *
 *   input
 *      |
 *      v
 *   custom VM
 *      |
 *      v
 *   hidden state
 *      |
 *      v
 *   final transformation
 *      |
 *      v
 *   flag
 *
 * The flag is never stored as plaintext.
 */

#define INPUT_LEN 16
#define VM_MEM 256

typedef uint8_t  u8;
typedef uint32_t u32;
typedef uint64_t u64;

/* ---------------------------------------------------------
 * Challenge constants
 * --------------------------------------------------------- */

static const u8 magic_seed[16] = {
    0x73, 0x6f, 0x75, 0x6c,
    0x76, 0x61, 0x75, 0x6c,
    0x74, 0x2d, 0x32, 0x30,
    0x32, 0x36, 0x21, 0x7f
};

/*
 * This is NOT the flag.
 *
 * It is an encoded verifier state.
 */
static const u8 vault_blob[32] = {
    0x19,0x43,0x7a,0x21,0x5c,0x11,0x92,0x2f,
    0x72,0x34,0x19,0xa7,0x3b,0x91,0x42,0x5d,
    0x18,0x6e,0x31,0x8b,0x54,0x21,0x73,0x11,
    0x92,0x44,0x28,0x71,0x33,0x9a,0x51,0x2c
};

/* ---------------------------------------------------------
 * Utility functions
 * --------------------------------------------------------- */

static u32 rol32(u32 x, unsigned r)
{
    r &= 31;
    return (x << r) | (x >> (32-r));
}

static u32 ror32(u32 x, unsigned r)
{
    r &= 31;
    return (x >> r) | (x << (32-r));
}

static u32 mix32(u32 x)
{
    x ^= 0xA5C3F19B;
    x *= 0x45D9F3B;
    x ^= x >> 16;
    x *= 0x45D9F3B;
    x ^= x >> 16;
    return x;
}

static u8 nonlinear(u8 x)
{
    x ^= 0xA7;
    x = (u8)((x * 0x3d) + 0x17);
    x ^= (x >> 3);
    x = rol32(x, 3) & 0xff;
    return x;
}

/* ---------------------------------------------------------
 * Decoy validators
 *
 * These look important in Ghidra but are irrelevant.
 * --------------------------------------------------------- */

static int decoy_alpha(const char *s)
{
    u32 x = 0x13572468;

    for (int i = 0; i < INPUT_LEN; i++)
        x = rol32(x ^ (u8)s[i], 5);

    return x == 0xDEADBEEF;
}

static int decoy_beta(const char *s)
{
    u32 x = 0xCAFEBABE;

    for (int i = 0; i < INPUT_LEN; i++)
        x += ((u8)s[i] * (i + 11));

    return (x & 0xffff) == 0x4242;
}

static int decoy_gamma(const char *s)
{
    u8 x = 0;

    for (int i = 0; i < INPUT_LEN; i++)
        x ^= nonlinear((u8)s[i]);

    return x == 0x42;
}

/* Prevent optimizer from deleting decoys. */
static volatile int decoy_sink;

static void execute_decoys(const char *s)
{
    decoy_sink ^= decoy_alpha(s);
    decoy_sink ^= decoy_beta(s);
    decoy_sink ^= decoy_gamma(s);
}

/* ---------------------------------------------------------
 * VM
 * --------------------------------------------------------- */

/*
 * VM registers
 *
 * r0..r3 = general purpose
 * pc     = bytecode position
 * z      = zero flag
 */

typedef struct
{
    u32 r[4];
    u32 pc;
    u32 z;
    u8  mem[VM_MEM];
} VM;

/*
 * Logical instruction set:
 *
 * 0x01 LOAD_IMM
 * 0x02 XOR
 * 0x03 ADD
 * 0x04 SUB
 * 0x05 ROL
 * 0x06 LOAD_INPUT
 * 0x07 STORE
 * 0x08 CMP
 * 0x09 JNZ
 * 0x0a MIX
 * 0xff HALT
 *
 * The bytecode uses a permutation of these values.
 */

enum
{
    OP_LOAD_IMM  = 0x01,
    OP_XOR       = 0x02,
    OP_ADD       = 0x03,
    OP_SUB       = 0x04,
    OP_ROL       = 0x05,
    OP_LOAD_INPUT= 0x06,
    OP_STORE     = 0x07,
    OP_CMP       = 0x08,
    OP_JNZ       = 0x09,
    OP_MIX       = 0x0a,
    OP_HALT      = 0xff
};

/*
 * Per-build opcode permutation.
 *
 * Players don't know this directly.
 */

static u8 opcode_decode(u8 encoded)
{
    /*
     * The mapping deliberately isn't sequential.
     */

    switch (encoded)
    {
        case 0xA1: return OP_LOAD_IMM;
        case 0xC7: return OP_XOR;
        case 0x3B: return OP_ADD;
        case 0x91: return OP_SUB;
        case 0xE2: return OP_ROL;
        case 0x4D: return OP_LOAD_INPUT;
        case 0x78: return OP_STORE;
        case 0xB4: return OP_CMP;
        case 0xD9: return OP_JNZ;
        case 0x55: return OP_MIX;
        case 0xF0: return OP_HALT;

        default:
            return 0;
    }
}

/*
 * Encoded bytecode.
 *
 * The bytes are additionally XOR encrypted at runtime.
 *
 * Format:
 *
 * opcode
 * operands...
 *
 * The program computes a hidden state from the user's input.
 */

static const u8 encrypted_program[] = {

    0xD4,0xB0,0x91,0xE8,0x6A,0xA8,0x39,0x72,
    0x8D,0xE1,0x4A,0x73,0xB2,0x0D,0x55,0x12,
    0x7E,0x94,0xA1,0x3D,0xF1,0x61,0x27,0xC8,
    0x5A,0x17,0x90,0x32,0xAB,0x40,0x13,0x7B,
    0x4E,0xF8,0x62,0x19,0xAD,0x39,0x71,0xC2,
    0x5F,0x28,0xA0,0x63,0x11,0x87,0x42,0xE4,
    0x6D,0x29,0x91,0x44,0xBE,0x03,0x57,0x9A,
    0x21,0xF0
};

#define PROGRAM_LEN sizeof(encrypted_program)

/*
 * Runtime program decryption.
 *
 * Important:
 *
 * The plaintext bytecode does not exist in the binary.
 */

static void decrypt_program(u8 *dst)
{
    u32 state = 0xC0DEC0DE;

    for (size_t i = 0; i < PROGRAM_LEN; i++)
    {
        state = mix32(state + (u32)i * 0x1337);

        u8 k = (u8)(
            state ^
            magic_seed[i & 15] ^
            (i * 17)
        );

        dst[i] = encrypted_program[i] ^ k;
    }
}

/* ---------------------------------------------------------
 * Input-dependent key generation
 * --------------------------------------------------------- */

static void generate_runtime_key(
    const u8 *input,
    u8 key[16]
)
{
    u32 a = 0x31415926;
    u32 b = 0x27182818;
    u32 c = 0xDEADC0DE;
    u32 d = 0x13371337;

    for (int i = 0; i < INPUT_LEN; i++)
    {
        u8 x = (u8)input[i];

        a = rol32(a ^ x, 3) + 0x1020304;
        b = ror32(b + x * 17, 7);
        c ^= mix32(x + i * 0x91);
        d += rol32(x ^ d, i & 15);

        a ^= b;
        b += c;
        c ^= d;
        d = rol32(d, 11);
    }

    for (int i = 0; i < 4; i++)
    {
        u32 x;

        if (i == 0) x = a;
        else if (i == 1) x = b;
        else if (i == 2) x = c;
        else x = d;

        key[i*4+0] = x & 0xff;
        key[i*4+1] = (x >> 8) & 0xff;
        key[i*4+2] = (x >> 16) & 0xff;
        key[i*4+3] = (x >> 24) & 0xff;
    }
}

/* ---------------------------------------------------------
 * VM execution
 * --------------------------------------------------------- */

static int run_vm(
    const char *input,
    u8 *program,
    u8 output[16]
)
{
    VM vm;

    memset(&vm, 0, sizeof(vm));

    /*
     * Initial state is derived from constants.
     */

    vm.r[0] = 0x13579BDF;
    vm.r[1] = 0x2468ACE0;
    vm.r[2] = 0xDEADBEEF;
    vm.r[3] = 0x0BADF00D;

    int input_index = 0;
    int output_index = 0;

    while (vm.pc < PROGRAM_LEN)
    {
        u8 encoded = program[vm.pc++];
        u8 op = opcode_decode(encoded);

        switch (op)
        {
            case OP_LOAD_IMM:
            {
                u8 reg = program[vm.pc++];
                u32 imm =
                    program[vm.pc++] |
                    ((u32)program[vm.pc++] << 8) |
                    ((u32)program[vm.pc++] << 16) |
                    ((u32)program[vm.pc++] << 24);

                vm.r[reg & 3] = imm;
                break;
            }

            case OP_XOR:
            {
                u8 a = program[vm.pc++];
                u8 b = program[vm.pc++];

                vm.r[a & 3] ^= vm.r[b & 3];
                break;
            }

            case OP_ADD:
            {
                u8 a = program[vm.pc++];
                u8 b = program[vm.pc++];

                vm.r[a & 3] += vm.r[b & 3];
                break;
            }

            case OP_SUB:
            {
                u8 a = program[vm.pc++];
                u8 b = program[vm.pc++];

                vm.r[a & 3] -= vm.r[b & 3];
                break;
            }

            case OP_ROL:
            {
                u8 reg = program[vm.pc++];
                u8 amount = program[vm.pc++];

                vm.r[reg & 3] =
                    rol32(vm.r[reg & 3], amount);

                break;
            }

            case OP_LOAD_INPUT:
            {
                u8 reg = program[vm.pc++];

                if (input_index < INPUT_LEN)
                    vm.r[reg & 3] =
                        (u8)input[input_index++];

                break;
            }

            case OP_STORE:
            {
                u8 reg = program[vm.pc++];
                u8 addr = program[vm.pc++];

                vm.mem[addr] =
                    vm.r[reg & 3] & 0xff;

                break;
            }

            case OP_CMP:
            {
                u8 a = program[vm.pc++];
                u8 b = program[vm.pc++];

                vm.z =
                    (vm.r[a & 3] ==
                     vm.r[b & 3]);

                break;
            }

            case OP_JNZ:
            {
                int8_t rel =
                    (int8_t)program[vm.pc++];

                if (!vm.z)
                    vm.pc += rel;

                break;
            }

            case OP_MIX:
            {
                u8 reg = program[vm.pc++];

                vm.r[reg & 3] =
                    mix32(vm.r[reg & 3]);

                break;
            }

            case OP_HALT:
            {
                for (int i = 0; i < 16; i++)
                    output[i] = vm.mem[i];

                return 1;
            }

            default:
                /*
                 * Invalid opcode = intentionally confusing
                 * failure path.
                 */
                return 0;
        }
    }

    return 0;
}

/* ---------------------------------------------------------
 * Final verifier
 * --------------------------------------------------------- */

static int final_verify(
    const u8 key[16],
    const u8 state[16]
)
{
    /*
     * The expected state isn't stored directly.
     *
     * Instead derive it from vault_blob and magic_seed.
     */

    u8 expected[16];

    for (int i = 0; i < 16; i++)
    {
        expected[i] =
            vault_blob[i] ^
            vault_blob[i+16] ^
            magic_seed[i];

        expected[i] =
            nonlinear(expected[i]);

        expected[i] ^= key[(i * 7) & 15];
    }

    u32 accumulator = 0xCAFED00D;

    for (int i = 0; i < 16; i++)
    {
        accumulator ^= state[i];

        accumulator =
            rol32(accumulator, 5);

        accumulator +=
            expected[i] * (i + 3);
    }

    /*
     * Deliberately convoluted final comparison.
     */

    u32 target = 0;

    for (int i = 0; i < 16; i++)
    {
        target +=
            expected[i] *
            (0x11 + i * 7);
    }

    target ^= 0x8A71C3D2;

    return accumulator == target;
}

/* ---------------------------------------------------------
 * Flag reconstruction
 * --------------------------------------------------------- */

static void print_flag(
    const u8 key[16],
    const u8 state[16]
)
{
    /*
     * Flag is generated only after successful validation.
     */

    static const u8 mask[32] = {
        0x2A,0x19,0x4C,0x77,
        0x31,0x6E,0x05,0x44,
        0x51,0x2D,0x60,0x13,
        0x72,0x08,0x33,0x55,
        0x19,0x41,0x6A,0x22,
        0x57,0x0B,0x39,0x64,
        0x10,0x73,0x25,0x4E,
        0x61,0x32,0x17,0x09
    };

    /*
     * Construct the flag dynamically.
     */

    char flag[64];

    const char prefix[] = "OWASP{";

    memset(flag, 0, sizeof(flag));

    memcpy(flag, prefix, 6);

    /*
     * The final characters depend on runtime key/state.
     *
     * This prevents strings(1) from revealing the flag.
     */

    for (int i = 0; i < 32; i++)
    {
        u8 x =
            mask[i] ^
            key[i & 15] ^
            state[(i * 5) & 15];

        x ^= (u8)(i * 13);

        /*
         * Printable alphabet.
         */

        x =
            'a' +
            (x % 26);

        flag[6+i] = x;
    }

    flag[38] = '}';

    puts(flag);
}

/* ---------------------------------------------------------
 * Main
 * --------------------------------------------------------- */

int main(void)
{
    char input[128];

    /*
     * Disable buffering.
     */

    setvbuf(stdout, NULL, _IONBF, 0);

    puts(
        "========================================"
    );

    puts(
        "          S O U L   V A U L T"
    );

    puts(
        "========================================"
    );

    puts(
        "The vault accepts a 16-byte access sequence."
    );

    printf("> ");

    if (!fgets(input, sizeof(input), stdin))
        return 1;

    input[strcspn(input, "\n")] = 0;

    if (strlen(input) != INPUT_LEN)
    {
        puts("ACCESS DENIED.");
        return 1;
    }

    /*
     * Decoy execution.
     */

    execute_decoys(input);

    /*
     * Generate runtime key.
     */

    u8 key[16];

    generate_runtime_key(
        (u8 *)input,
        key
    );

    /*
     * Decrypt VM into stack memory.
     *
     * This means plaintext VM bytecode isn't
     * present in the file.
     */

    u8 *program =
        malloc(PROGRAM_LEN);

    if (!program)
        return 1;

    decrypt_program(program);

    /*
     * Execute hidden machine.
     */

    u8 state[16];

    memset(state, 0, sizeof(state));

    if (!run_vm(
            input,
            program,
            state))
    {
        puts("VAULT CORRUPTED.");
        free(program);
        return 1;
    }

    /*
     * Wipe decrypted bytecode.
     */

    memset(
        program,
        0,
        PROGRAM_LEN
    );

    free(program);

    /*
     * Final validation.
     */

    if (!final_verify(
            key,
            state))
    {
        puts("ACCESS DENIED.");
        return 1;
    }

    puts("ACCESS GRANTED.");

    print_flag(
        key,
        state
    );

    /*
     * Wipe sensitive runtime data.
     */

    memset(key, 0, sizeof(key));
    memset(state, 0, sizeof(state));

    return 0;
}
