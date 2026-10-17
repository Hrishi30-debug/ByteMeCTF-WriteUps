# Soul Echoes — Introductory Reverse Engineering CTF Challenge

## Challenge Information

- **Title:** Soul Echoes (The Stonekeeper's Chronicles)
- **Category:** Reverse Engineering
- **Difficulty:** Very Easy / Sanity Check
- **Player Artifact:** `dist/soul_echo` (Linux x86-64 ELF executable)
- **Flag Format:** `OWASP{...}`
- **Flag:** `OWASP{th3_st0n3k33p3r_wh1sp3rs_1nt0_th3_v01d}`

---

## CTF Description

> The chilling winds across the barren peaks of Vormir carry ancient echoes.
>
> The Stonekeeper has inscribed his memories of exile, sacrifice, and sorrow into the obsidian stone.
>
> Can you hear the whisper hidden inside the chronicle?
>
> **Flag format:** `OWASP{...}`

---

## Quick Solve

```bash
strings soul_echo | grep OWASP
```

Output:
```text
OWASP{th3_st0n3k33p3r_wh1sp3rs_1nt0_th3_v01d}
```

---

## Building

```bash
make build
```
Or:
```bash
./build.sh
```

## Testing & Verifying

```bash
make test
make solve
```
