# Red Skull's Trail (OSINT,Easy)

**Author:** Hrishikesh
**Category:** OSINT 
**Difficulty:** Easy

## Challenge Description

> The Soul Stone was supposed to be returned to its resting place on Vormir-616, but the record says otherwise. Investigate who used the stone, follow the trail left behind, and prove that you are worthy of recovering it.

## Summary

The riddle points toward a GitHub account associated with Vormir-616. Its public repository, `Missing-Record`, contains several records about the Soul Stone. `RECORD3` is marked as altered, and its commit history shows what was removed. The account's other records provide context for the recovery. The final clue is in `RECORD6`, whose image contains a hidden Base64 string that reveals the username used in the flag.

## Initial Clue

The challenge begins with a short riddle:

```text
The Soul Stone was supposed to be returned to its resting place on Vormir-616,
but the record says different!!!
Investigate who was the user.
Remember, only Red Skull can lead you to your destination.
Only worthy one will be able to get the stone back.
```

The unusual references to Vormir and Red Skull point toward the GitHub account **Vormir-616**. Its repository is:

```text
https://github.com/Vormir-616/Missing-Record
```

## Step 1 — Inspect the repository

The repository contains `RECORD1` through `RECORD6`. The README describes the Soul Stone as missing and says the final record disappeared. The individual records provide fragments of the story and indicate that the identity of the user must be uncovered.

## Step 2 — Find the altered record

`RECORD3` is marked **UNRECOVERED** and says that it has been tampered with. Its history can be opened from the file's **History** link, or directly at:

```text
https://github.com/Vormir-616/Missing-Record/commits/main/RECORD3
```

Comparing the current file with an earlier revision shows that the record originally said the stone had been returned and that the price had been paid. This confirms that the file history contains evidence missing from the current record.

## Step 3 — Read the surrounding records

The remaining records describe prior recoveries and refer to users such as `soulkeeper`, `echoofvormir`, and `soulbound`. These names establish the record format and reinforce that the challenge is asking for a user identity. The key identity clue is in `RECORD6`.

## Step 4 — Recover the hidden text from RECORD6

`RECORD6` is an image rather than a readable text record. Download or open the image and inspect its contents for text embedded in the image. The intended clue is a Base64-encoded string hidden using an `echo` command. Decode the recovered Base64 text to obtain the username.

For example, if the extracted string is saved as `clue.txt`, decode it with:

```bash
base64 -d clue.txt
```

The decoded username is **PhantomSoul**.

> **Verification note:** The challenge key identifies `PhantomSoul` as the intended decoded username. The local files provided for this writeup do not include the `RECORD6` image, so the hidden payload itself could not be independently re-extracted here.

## Flag

The challenge uses the format `OWASP{username}`. Substituting the recovered username gives:

```text
OWASP{PhantomSoul}
```

## Solution Path at a Glance

| Step | Action | Result |
|---|---|---|
| 1 | Interpret the riddle's Vormir and Red Skull references | Locate the `Vormir-616` GitHub account |
| 2 | Open the `Missing-Record` repository | Find the Soul Stone records |
| 3 | Inspect `RECORD3` and its commit history | Confirm that the record was altered |
| 4 | Examine the image in `RECORD6` | Locate the hidden Base64 text |
| 5 | Decode the Base64 text | Recover `PhantomSoul` |
| 6 | Apply the required flag format | `OWASP{PhantomSoul}` |

## Tools Used

- GitHub repository and commit history
- Image viewer or image-forensics utility
- Base64 decoder (`base64 -d` on Linux/macOS, or an equivalent decoder)

