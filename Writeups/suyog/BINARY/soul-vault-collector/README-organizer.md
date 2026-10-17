# SOUL VAULT: The Collector — Organizer Documentation

## Challenge Metadata
- **Name:** SOUL VAULT — The Collector
- **Category:** Pwn / Binary Exploitation
- **Difficulty:** Hard
- **Mitigations:** Full RELRO, Canary, NX enabled, PIE enabled, FORTIFY_SOURCE=2
- **Flag:** `OWASP{S0ul_St0ne_C0ll3ct0r_UAF_Aw4k3n3d}`

---

## Challenge Story & Overview (For Players)
> The Collector has gathered fragments of six cosmic entities.
> Unfortunately, the Soul Stone has begun remembering things that were supposed to be forgotten.
> Can you make it remember you?
> Connect to the vault and recover what lies beyond the final Soul.
>
> **Connection:** `nc <SERVER_IP> 1338`  
> **Provided Files:** `soul_vault`, `libc.so.6`, `ld-linux-x86-64.so.2`

---

## Architecture & Data Structures

Each Soul chunk is represented by:
```c
struct soul {
    char name[32];
    char *memory;
    void (*consume)(struct soul *);
    unsigned int id;
    unsigned int memory_size;
};
```
Total size: `32 + 8 + 8 + 4 + 4 = 56 bytes` (fits into the 0x40 chunk / tcache bin).

### Vulnerability Mechanism
In `release_soul()`:
```c
struct soul *s = souls[idx];
if (s->memory) free(s->memory);
free(s);
/* Missing: souls[idx] = NULL; */
```
The pointer in the global `souls` table remains intact after freeing both `s->memory` and `s`.
Subsequent actions on `idx` trigger **Use-After-Free (UAF)**:
1. `inspect_soul(idx)` calls `s->consume(s)` on the freed struct pointer, and prints `s->name`/`s->memory`.
2. `rename_soul(idx)` writes directly into `s->name` on a freed chunk.

---

## State Machine Conditions for `soul_stone_awakens()`
```c
void soul_stone_awakens(void) {
    if (stone_state == STATE_FINAL &&
        sacrifice_count == 3 &&
        collector_awakened == 1) {
        ...
        system("/bin/sh");
    }
}
```

1. **`stone_state == 6` (STATE_FINAL)**
2. **`sacrifice_count == 3`** (Releasing 3 souls increments this counter)
3. **`collector_awakened == 1`**

---

## Exploit Flow (Concepts)
1. **Leak PIE / Heap Addresses:**
   - Free chunks and read back memory via `inspect_soul()`.
   - Forward/backward tcache pointers or libc pointers reveal addresses.
2. **Tcache Poisoning / Chunk Overlapping:**
   - Use `rename_soul()` or controlled memory reallocations to manipulate tcache `fd` pointers (accounting for `safe-linking` pointer mangling if glibc >= 2.32).
3. **State Corruption & Callback Trigger:**
   - Overwrite global control variables (`stone_state`, `collector_awakened`) or hijack the `consume` function pointer to redirect execution flow.
4. **Win Condition:**
   - Trigger `enter_soul_stone()` to spawn the shell and retrieve `/home/ctf/flag.txt`.

---

## Deployment & Hosting

### Option A: Docker Compose
```bash
cd soul-vault-collector
docker compose up -d --build
```

### Option B: Standalone Docker
```bash
docker build -t soul_vault_collector_pwn .
docker run -d -p 1338:1338 --name soul_vault_collector_pwn soul_vault_collector_pwn
```

### Extracting Libc for Players
To provide players with the exact `libc.so.6` and loader matching the challenge environment:
```bash
id=$(docker create soul_vault_collector_pwn)
docker cp $id:/lib/x86_64-linux-gnu/libc.so.6 ./challenge/
docker cp $id:/lib64/ld-linux-x86-64.so.2 ./challenge/
docker rm -v $id
```
