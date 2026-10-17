# SOUL'S WEAKNESS — Organizer Documentation

## Challenge Information
- **Name:** SOUL'S WEAKNESS
- **Category:** Pwn / Binary Exploitation
- **Difficulty:** Easy (Beginner)
- **Flag:** `OWASP{S0ul_St0ne_Buff3r_0v3rfl0w}`

---

## Challenge Description (For Players)
> Thanos created an impenetrable vault to guard the legendary Soul Stone... or so he thought.
> Can you find the weakness in the vault's authentication program and claim the Soul Stone?
>
> **Connection:** `nc <SERVER_IP> 1337`  
> **Provided File:** `soul`

---

## Vulnerability Analysis
The binary contains an unbounded stack buffer overflow:
- In `vault()`, a 32-byte character array `char name[32]` is allocated on the stack.
- Input is accepted via `gets(name)`. `gets()` performs no bounds checking on input length.
- The binary is compiled without stack canaries (`-fno-stack-protector`) and without position-independent executable protections (`-no-pie`).
- An unused win function named `soul_stone()` resides at a static address in the `.text` segment.

---

## Compilation Details
The build command used in [build.sh](file:///home/suyog/Downloads/ByteMe_CTF/chall/pwn/soul-stone-pwn/build.sh):
```bash
gcc src/soul.c -o challenge/soul -fno-stack-protector -no-pie -Wno-implicit-function-declaration
chmod 755 challenge/soul
```

### Expected `checksec` Output
```text
Arch:       amd64-64-little
RELRO:      Partial RELRO
Stack:      No canary found
NX:         NX enabled
PIE:        No PIE (0x400000)
Stripped:   No
```

---

## Intended Solve Methodology

1. **Reconnaissance & Mitigation Audit:**
   - Players examine binary security flags with `checksec --file=soul`.
   - Observation: No canary, No PIE, NX enabled.
2. **Reverse Engineering & Symbol Identification:**
   - Identify functions using `nm soul`, `objdump -t soul`, or decompilers (Ghidra/IDA/cutter):
     ```bash
     nm soul | grep soul_stone
     # or
     objdump -d soul | grep soul_stone
     ```
   - Notice the unused function `soul_stone` which prints the flag.
3. **Offset Calculation:**
   - Using GDB with cyclic patterns:
     ```text
     gdb ./soul
     pwndbg> cyclic 100
     pwndbg> run
     (paste cyclic string)
     pwndbg> cyclic -l <faulting_address_or_pattern>
     ```
   - On standard x86-64 Linux ABI, 32 bytes of buffer + 8 bytes of saved RBP yields an offset of 40 bytes to the return address (RIP).
4. **Execution Redirection (ret2win):**
   - Target the fixed address of `soul_stone`.
   - *Note on Stack Alignment:* On x86-64 Linux, GLIBC functions (like `printf`/`puts` inside `soul_stone`) may execute `movaps` instructions that expect a 16-byte aligned stack pointer (`RSP % 16 == 0`). If a player encounters a crash inside `printf` when jumping directly to `soul_stone`, jumping to `soul_stone + 1` (or inserting a `ret` gadget before `soul_stone`) will resolve the alignment issue.

---

## Deployment & Hosting

### Option A: Docker Compose (Recommended)
```bash
docker compose up -d --build
```
Verify the container is listening on port 1337:
```bash
nc localhost 1337
```

To stop:
```bash
docker compose down
```

### Option B: Standalone Docker
```bash
docker build -t soul_stone_pwn .
docker run -d -p 1337:1337 --name soul_stone_pwn soul_stone_pwn
```

### Option C: Direct Socat (Without Docker)
```bash
socat TCP-LISTEN:1337,reuseaddr,fork EXEC:./challenge/soul,pty,stderr
```

---

## What to Distribute to Players
Distribute **only**:
- `challenge/soul`
- Connection details (`nc <SERVER_IP> 1337`)

Do **not** distribute:
- `src/soul.c`
- `build.sh`
- `Dockerfile` / `docker-compose.yml`
- Flag or internal writeups

---

## Troubleshooting & FAQ
- **Connection closes immediately without prompt:** Check whether stdin/stdout buffering is disabled. `soul.c` calls `setvbuf()` with `_IONBF` on `stdin`, `stdout`, and `stderr` to prevent buffered I/O deadlocks over network streams.
- **SIGSEGV at `movaps` instruction in libc:** Explain the x86-64 stack alignment requirement (16-byte boundary). Jumping past the function prologue (e.g. `soul_stone + 1` or `+ 4`) or chaining an extra `ret` gadget restores 16-byte alignment.
