# Soul Stone — The Soul Stone’s Legacy (OSINT, Easy)

**Author:** Hrishikesh 
**Category:** OSINT  
**Difficulty:** Easy

## Challenge Description

> The Soul Stone’s influence reaches far beyond Vormir. Its journey has left traces across different places, connecting people and events in ways that are not immediately clear. Piece together the story behind the stone and discover where its legacy leads.

## Summary

The challenge begins with metadata embedded in the provided Soul Stone image. The metadata points to the GitHub account `Sacrifice-123`. Its `Nothing_Suspicious` repository contains clues in its files and commit history. A deleted Base64 string decodes to geographic coordinates that identify Pune, while an earlier version of a hex clue reveals the name Anuj. Combining the two values gives the flag `OWASP{Anuj_Pune}`.

## Step 1 — Inspect the image metadata

Use ExifTool to inspect the supplied image:

```bash
exiftool Soul_stone.jpeg
```

The image description gives the clue:

```text
The soul stone demands a price. What must be given in exchange?
```

The author field is `Description-123`. Together, these metadata values direct the investigation to the GitHub account **Sacrifice-123**.

## Step 2 — Inspect the GitHub repository

Open the account's `Nothing_Suspicious` repository:

```text
https://github.com/Sacrifice-123/Nothing_Suspicious
```

The current repository contains `README.md`, `decodeme.md`, and `filesixty4.md`. The README says that dark secrets lie in the past, suggesting that commit history may contain clues that are no longer present in the current files.

## Step 3 — Recover the location clue from repository history

Open the commit history for `filesixty4.md` and inspect the earlier version of the file. It contains this Base64 string:

```text
MTjCsDM54oCyN+KAs04sIDczwrA0NeKAsjQz4oCzRQ==
```

Decode it, for example with:

```bash
echo 'MTjCsDM54oCyN+KAs04sIDczwrA0NeKAsjQz4oCzRQ==' | base64 -d
```

The decoded text is:

```text
18°39′7″N, 73°45′43″E
```

These coordinates point to the Pune area in Maharashtra, India. The clue was deleted in a later commit, so the file history is necessary to recover it.

## Step 4 — Recover the name from the hex clue

Inspect the repository's history for the hex clue file. An earlier version contains:

```text
4d79206e616d6520697320416e756a204920616d2063757272656e746c7920696e205365636f6e642059656172
```

Convert the hexadecimal bytes to text. For example, in Python:

```python
bytes.fromhex(
    "4d79206e616d6520697320416e756a204920616d2063757272656e746c7920696e205365636f6e642059656172"
).decode()
```

This reads:

```text
My name is Anuj I am currently in Second Year
```

The name required for the flag is **Anuj**. The repository has had other versions of this hex clue, so use the earlier version that contains Anuj for this challenge.

## Step 5 — Assemble the flag

The challenge asks for the format `OWASP{Name_City}`. Combining the name and city gives:

```text
OWASP{Anuj_Pune}
```

## Flag

```text
OWASP{Anuj_Pune}
```

## Solution Path at a Glance

| Step | Action | Result |
|---|---|---|
| 1 | Inspect `Soul_stone.jpeg` metadata | Find the `Description-123` clue |
| 2 | Follow the clue to the GitHub account | Locate `Sacrifice-123/Nothing_Suspicious` |
| 3 | Inspect the history of `filesixty4.md` | Recover coordinates for Pune |
| 4 | Decode the earlier hex clue | Recover the name Anuj |
| 5 | Apply the required flag format | `OWASP{Anuj_Pune}` |

## Tools Used

- ExifTool (image metadata inspection)
- GitHub (repository and commit history)
- Base64 decoder
- Hexadecimal-to-text decoder
- Map or coordinate lookup

