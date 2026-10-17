# Echoes of Vormir (Forensics, Hard)

**Author:** Sarthak Warale  
**Category:** Forensics  
**Difficulty:** Hard  
**Challenge:** Echoes of Vormir  
**Platform:** CTF7 — OWASP PCCOE, Pune Organizer Console  
**Flag format:** `OWASP{...}`

## Challenge Description

> Vormir remembers.
>
> Something happened on a Windows machine before its memory was captured.
>
> The evidence is scattered, and not everything left behind is what it seems.
>
> Begin by understanding the memory you've been given. Then follow the traces left behind by the expedition.
>
> Five artifacts remain.
>
> The expedition ends when the final record is found.
>
> **File:** Download the supplied memory image from the link in the CTF7 mission description. Use the same memory image for all six stages.
>
> **Flag format:** `OWASP{...}`

## Summary

The CTF7 mission is split into six challenges. The names, difficulty ratings, and points below match the organizer-console screenshots:

| Challenge | Difficulty | Points |
|---|---|---:|
| Mem-1: When It Happened | Easy | 100 |
| Mem-2: Soul Hunt | Medium | 200 |
| Mem-3: The Painted Soul | Hard | 300 |
| Mem-4: A Fragment in Memory | Hard | 250 |
| Mem-5: The Last Trace | Medium | 200 |
| Mem-6: The Forgotten Note | Medium | 250 |

**Total: 1300 points.**

Use the same supplied memory image for all six stages. The investigation moves from system metadata and process enumeration to an image artifact, a memory-resident fragment, browser evidence, and a recovered text note.

Several artifact references are hex-encoded, so searching the dump for the literal string `OWASP{` is not sufficient. Decode recovered hexadecimal strings as ASCII to obtain the corresponding flag.

## Flags

This mission consists of 6 stages:

| Stage | Challenge | Flag | Points |
|---|---|---|---:|
| 1 | Mem-1: When It Happened | `OWASP{2026-10-08 05:07:43}` | 100 |
| 2 | Mem-2: Soul Hunt | `OWASP{SoulHunt_7F31}` | 200 |
| 3 | Mem-3: The Painted Soul | `OWASP{soulstone_paint_52af}` | 300 |
| 4 | Mem-4: A Fragment in Memory | `OWASP{soulstone_memory_84c2}` | 250 |
| 5 | Mem-5: The Last Trace | `OWASP{soulstone_web_8b2d}` | 200 |
| 6 | Mem-6: The Forgotten Note | `OWASP{soulstone_note_3c91}` | 250 |

## Tools Used

- **Volatility 3** — inspect Windows memory, enumerate processes, and locate recoverable file objects.
- **PowerShell** — run Volatility commands and inspect extracted binary data.
- **Hex-to-ASCII conversion** — decode artifact references into flags.

Assume the supplied memory image is named `Vormir.mem` and `vol` is available in the terminal. Replace the filename, process IDs, and addresses below with values from your own output where necessary.

---

## Mem-1 — When It Happened (Easy, 100 points)

**CTF7 description:**

> Before following the trail, determine when the machine gave up its secrets.
>
> Find the time recorded in the memory image.
>
> Flag format: `OWASP{YYYY-MM-DD HH:MM:SS}`

### Establish the capture time

Start by identifying operating-system information and the timestamp stored in the memory image:

```powershell
vol -f .\Vormir.mem windows.info
```

Look for the `SystemTime` field. In the challenge image it is:

```text
2026-10-08 05:07:43+00:00
```

The flag format excludes the timezone suffix. Keep the date and time exactly as shown, without `+00:00`.

**Flag**

```text
OWASP{2026-10-08 05:07:43}
```

## Mem-2 — Soul Hunt (Medium, 200 points)

**CTF7 description:**

> Among everything running on the machine, something doesn't belong.
>
> Find it.

### Find the suspicious process

Enumerate processes present when the memory image was captured:

```powershell
vol -f .\Vormir.mem windows.pslist
```

Inspect the process names and look for an entry that does not fit the surrounding system processes. The challenge process is:

```text
SoulHunt_7F31.exe
```

Use the distinctive process name to form the flag.

**Flag**

```text
OWASP{SoulHunt_7F31}
```

## Mem-3 — The Painted Soul (Hard, 300 points)

### Recover the painted artifact

The next clue points toward an image that was open on the machine. Check whether Microsoft Paint was running:

```powershell
vol -f .\Vormir.mem windows.pslist
```

Look for `mspaint.exe`. The challenge image is named `Vormir.png`. Depending on how the final memory image was captured, recovering the image may require identifying its file object or examining the relevant process memory. Use the output from your dump to determine the appropriate address and recovery method; do not assume a fixed address or PID.

Once the image is recovered, inspect its artifact reference. The reference is a hexadecimal-encoded ASCII string:

```text
4f574153507b736f756c73746f6e655f7061696e745f353261667d
```

Decode it from hex to ASCII. For example, in PowerShell:

```powershell
[System.Text.Encoding]::ASCII.GetString(
    [Convert]::FromHexString("4f574153507b736f756c73746f6e655f7061696e745f353261667d")
)
```

**Flag**

```text
OWASP{soulstone_paint_52af}
```

## Mem-4 — A Fragment in Memory (Hard, 250 points)

**CTF7 description:**

> Not everything that existed on the machine was meant to survive.
>
> One fragment remained where few people think to look.
>
> Dig deeper. Might be image.

### Find the fragment inside process memory

This artifact is not intended to be recovered as an ordinary file from disk. Investigate process memory and its virtual address descriptors (VADs).

Start by enumerating processes and identify likely processes to examine:

```powershell
vol -f .\Vormir.mem windows.pslist
```

Use the relevant PID from your output to inspect memory mappings and VAD information:

```powershell
vol -f .\Vormir.mem windows.memmap --pid <PID>
vol -f .\Vormir.mem windows.vadinfo --pid <PID>
```

Review the mappings and investigate suspicious memory regions. The exact region and extraction steps depend on the final memory image and the output of these plugins. Recover the image fragment, then inspect its hexadecimal artifact reference:

```text
4f574153507b736f756c73746f6e655f6d656d6f72795f383463327d
```

Decode the hex string to ASCII.

**Flag**

```text
OWASP{soulstone_memory_84c2}
```

## Mem-5 — The Last Trace (Medium, 200 points)

**CTF7 description:**

> Someone was looking for something on web shortly before the machine was captured.
>
> The trail did not end on the filesystem, instead in the web.
>
> Follow it.

### Follow the browser trace

The next artifact was left behind by a browser shortly before acquisition. Browser activity may exist in process memory even when the useful evidence is not available as a normal file on disk.

Enumerate processes and identify the relevant Microsoft Edge process. Edge uses multiple processes, so do not assume the first `msedge.exe` PID contains the artifact.

```powershell
vol -f .\Vormir.mem windows.pslist
```

Inspect the appropriate process memory using the PID and memory mappings identified from your output. Search recovered process-memory data for the challenge URL or its hexadecimal artifact reference. The URL used in the challenge is:

```text
https://example.com/vormir?artifact=4f574153507b736f756c73746f6e655f7765625f386232647d
```

The `artifact` parameter contains a hex-encoded flag. Decode its value to ASCII.

**Flag**

```text
OWASP{soulstone_web_8b2d}
```

## Mem-6 — The Forgotten Note (Medium, 250 points)

**CTF7 description:**

> The expedition ends with a record that was left open when everything stopped.
>
> If you've made it this far, you already know how to follow the traces.
>
> Find the final record.

### Recover the forgotten note

The final artifact is a text file that was open when the system was captured. Use the file scanner to locate references to the note:

```powershell
vol -f .\Vormir.mem windows.filescan
```

Find the entry for `expedition.txt`. Use the virtual address reported by your output with `windows.dumpfiles`:

```powershell
vol -f .\Vormir.mem windows.dumpfiles --virtaddr <ADDRESS>
```

Inspect the recovered file. The note contains this artifact reference:

```text
4f574153507b736f756c73746f6e655f6e6f74655f336339317d
```

Decode the hexadecimal value to ASCII to recover the final flag. The note also confirms that the expedition is complete.

**Flag**

```text
OWASP{soulstone_note_3c91}
```

---

## Solution Summary

| Challenge | Difficulty | Artifact | Flag | Points |
|---|---|---|---|---:|
| Mem-1: When It Happened | Easy | System capture time | `OWASP{2026-10-08 05:07:43}` | 100 |
| Mem-2: Soul Hunt | Medium | Suspicious process name | `OWASP{SoulHunt_7F31}` | 200 |
| Mem-3: The Painted Soul | Hard | Paint image artifact | `OWASP{soulstone_paint_52af}` | 300 |
| Mem-4: A Fragment in Memory | Hard | Image fragment in process memory | `OWASP{soulstone_memory_84c2}` | 250 |
| Mem-5: The Last Trace | Medium | Browser artifact | `OWASP{soulstone_web_8b2d}` | 200 |
| Mem-6: The Forgotten Note | Medium | `expedition.txt` | `OWASP{soulstone_note_3c91}` | 250 |

**Total:** 1300 points

## Key Takeaways

1. Start memory analysis with operating-system metadata and process enumeration.
2. Do not rely only on a plaintext search for `OWASP{`; the challenge uses hexadecimal encoding.
3. A process can retain useful artifacts in memory even when they are not readily available on disk.
4. Browser evidence can be distributed across several browser processes.
5. File objects may be recoverable from a memory image with `windows.filescan` and `windows.dumpfiles`.
6. Always validate extraction commands against the exact memory image. PIDs, virtual addresses, and recoverable regions can change between captures.

## Timeline

Use the same downloaded memory image for all stages; do not switch to a different dump midway through the mission.

| Challenge | Action | Result |
|---|---|---|
| Mem-1 | Run `windows.info` | Capture timestamp |
| Mem-2 | Run `windows.pslist` | `SoulHunt_7F31.exe` |
| Mem-3 | Investigate Paint and recover the image | Paint artifact flag |
| Mem-4 | Inspect process mappings and VADs | Memory-resident image artifact |
| Mem-5 | Inspect the relevant Edge process | Browser artifact flag |
| Mem-6 | Run `windows.filescan`, then `windows.dumpfiles` | Final note and flag |
