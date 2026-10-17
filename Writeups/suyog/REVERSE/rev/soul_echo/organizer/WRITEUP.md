# Soul Echoes — Official Challenge Writeup

**Category:** Reverse Engineering  
**Difficulty:** Very Easy / Introductory  
**Theme:** The Stonekeeper's Chronicle (Vormir)  
**Flag:** `OWASP{th3_st0n3k33p3r_wh1sp3rs_1nt0_th3_v01d}`  

---

## 1. Challenge Overview

Players receive an atmospheric story-driven Linux ELF executable: `soul_echo`.

```text
╔═══════════════════════════════════════════════════════════════╗
║                 SOUL ECHOES: THE CHRONICLES                   ║
║               Memories from the Edge of Space                 ║
╚═══════════════════════════════════════════════════════════════╝
```

The challenge is designed as an entry-level "sanity check" / introductory challenge for reverse engineering competitions.

---

## 2. Solution

### Method 1: Static Strings Inspection (Intended Fast Path)

Since the flag is stored directly in the program's read-only data section (`.rodata`), it can be obtained instantly using the standard UNIX `strings` utility:

```bash
$ strings soul_echo | grep OWASP
OWASP{th3_st0n3k33p3r_wh1sp3rs_1nt0_th3_v01d}
```

### Method 2: Interactive Story Reading

Running the program interactively and selecting Chapter III ("The Inscription upon the Obsidian Cliff") or Chapter IV ("Listen to the entire chronicle") prints the carved secret directly:

```bash
$ ./soul_echo
Choose your path (1-5): 3

[+] CHAPTER III: THE INSCRIPTION UPON THE OBSIDIAN CLIFF
-----------------------------------------------------------------
Before the silence reclaimed this mountain, I carved a final secret
into the black stones above the clouds.
A whisper etched into eternity for those who have eyes to see:

    >>> OWASP{th3_st0n3k33p3r_wh1sp3rs_1nt0_th3_v01d} <<<
```

---

## 3. Flag

`OWASP{th3_st0n3k33p3r_wh1sp3rs_1nt0_th3_v01d}`
