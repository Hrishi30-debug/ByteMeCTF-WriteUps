# SOUL // MEMORY OF THANOS — Organizer Documentation

## Challenge Details
- **Name:** SOUL // MEMORY OF THANOS
- **Category:** Pwn
- **Difficulty:** Hard
- **Mitigations:** Full RELRO, Canary, NX, PIE, FORTIFY_SOURCE=2
- **Flag:** `OWASP{Th4n0s_S0ul_M3m0ry_UAF_Typ3_C0nfusi0n}`

---

## Challenge Story & Overview (For Players)
> Six souls. One archive. One memory.
> The Soul Archive holds remnants of the cosmos, but Thanos's memory cache was never meant to hold mortal souls.
> Can you bring harmony to the archive and trigger the ascension?
>
> **Connection:** `nc <SERVER_IP> 1339`  
> **Provided Files:** `soul_archive`, `libc.so.6`, `ld-linux-x86-64.so.2`

---

## Core Vulnerability & Design

### 1. Structure Layout & Alignment
- `struct Soul`: 64 bytes total
  - `name`: 32 bytes (offset 0..31)
  - `essence`: 8 bytes (offset 32..39)
  - `type`: 8 bytes (offset 40..47)
  - `consume`: 8 bytes (offset 48..55)
  - `inspect`: 8 bytes (offset 56..63)

- `struct TransferRecord`: 64 bytes total
  - `realm_origin`: 24 bytes (offset 0..23)
  - `transfer_id`: 4 bytes (offset 24..27)
  - `flags`: 4 bytes (offset 28..31)
  - `timestamp`: 8 bytes (offset 32..39) -> **Aligns with `Soul.essence`**
  - `raw_entropy`: 8 bytes (offset 40..47) -> **Aligns with `Soul.type`**
  - `auth_callback`: 8 bytes (offset 48..55) -> **Aligns with `Soul.consume`**
  - `audit_callback`: 8 bytes (offset 56..63) -> **Aligns with `Soul.inspect`**

### 2. The Lifetime Flaw (UAF)
In `merge_souls()`:
```c
struct Soul *s_b = archive[b];
...
free(s_b);
/* archive[b] is NOT cleared */
```
The pointer in `archive[b]` remains active.

### 3. Allocator Reuse & Type Confusion
Because `struct Soul` and `struct TransferRecord` both allocate exactly 64 bytes (`0x50` heap chunk size):
1. Merging frees a `Soul` into the 0x50 tcache bin.
2. Invoking `5. Transfer soul` allocates a `TransferRecord`, popping the exact same chunk.
3. The player controls:
   - `timestamp` (corresponds to `essence`, which must equal `0x50574e534f554c53ULL`)
   - `audit_callback` (corresponds to `inspect` callback function pointer)
4. Calling `2. Inspect soul` on the dangling index triggers the hijacked `inspect` function with `s` as its first parameter.

### 4. Honeypots & Anti-AI Protections
- `fake_win()`: Prints decoy text and aborts.
- `debug_shell()`: Decoy shell function that prints error and aborts.
- Direct ret2win bypass is blocked by `soul_ascension(s)` enforcing the strict state checks:
  - `total_captured >= 6`
  - `merges_performed == 3`
  - `souls_erased == 1`
  - `s->essence == 0x50574e534f554c53ULL` (`"PWNSOULS"`)

---

## Hosting
```bash
cd soul-archive-thanos
docker compose up -d --build
```
Port: `1339`
