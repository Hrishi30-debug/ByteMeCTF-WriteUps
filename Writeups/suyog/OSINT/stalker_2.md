# Stalker 2 (OSINT, Expert)

**Author:** Suyog Jadhav  
**Category:** OSINT  
**Difficulty:** Expert

## Challenge Description

> Author had a secret YouTube channel, are you brave enough to find its channel ID/handle?  
> Flag format: `OWASP{channel_handle}`

## Summary

This challenge requires identifying the author's hidden, secondary YouTube channel. Since the secret channel is not linked directly to the author's real name or public profiles, the investigation begins by uncovering an intermediate public footprint—the author's anime editing/AMV account (`SUYOG [AMV]` / `@itz_suyog_`). From there, clues hidden in the channel description ("hidden ninja") and a comment left on one of the AMV videos point to the secret channel handle `@hiddenninja5770`.

## Flag

```
OWASP{hiddenninja5770}
```

---

## Step 1 — Finding the Intermediate Channel (The AMV Account)

From earlier OSINT and footprinting on the author (Suyog Jadhav), it is known that the author is a big anime fan and creates Anime Music Videos (AMVs).

Searching YouTube for `suyog amv`:

```
https://www.youtube.com/results?search_query=suyog+amv
```

The top result reveals the author's AMV account: **SUYOG [AMV]** (`@itz_suyog_`).

![YouTube Search for suyog amv](resources/stalker2_sol1.png)

Navigating to the channel page confirms multiple uploaded anime edits featuring characters like Naruto, Luffy, and Obito:

![SUYOG [AMV] Channel Home](resources/stalker2_sol2.png)

However, this is only the **intermediate account**, not the final secret channel.

## Step 2 — Pivoting from the Intermediate Channel

To find the secret channel, we inspect the intermediate account for breadcrumbs. Two independent paths lead to the target:

### Path A — Checking Channel Description & Details

Opening the channel description modal for `SUYOG [AMV]` reveals a hidden phrase:

```
Description:
Anime edits....and AMV

hidden ninja
```

![Channel Description with hidden ninja clue](resources/stalker2_sol3.png)

The keyword **"hidden ninja"** stands out as a clear clue toward the secret channel's identity.

### Path B — Inspecting Video Comments

Browsing through the uploaded videos and checking their comment sections—specifically on the video titled **`Obito sad [ AMV ] 💔`**—uncovers a comment:

- User: **`@hiddenninja5770`**
- Comment: *"Yo"*

![Comment by @hiddenninja5770](resources/stalker2_sol4.png)

This directly reveals the active handle: **`hiddenninja5770`**.

## Step 3 — Locating and Confirming the Secret Channel

Searching YouTube for `hidden ninja`:

```
https://www.youtube.com/results?search_query=hidden+ninja
```

The top search result is a channel named **Hidden Ninja** (`@hiddenninja5770`) with matching anime aesthetics (an Obito avatar), 630 subscribers, and 52 videos.

![YouTube Search Results for Hidden Ninja](resources/stalker2_sol5.png)

Opening the channel's About / Description popup confirms this is the author's secret account:

```
Description
Edited stuff

secret account

More info:
www.youtube.com/@hiddenninja5770
```

![Secret Channel About Modal](resources/stalker2_sol6.png)

The description explicitly states: **"secret account"**, confirming that `@hiddenninja5770` is the intended target.

Extracting the handle gives the final flag:

```
OWASP{hiddenninja5770}
```

## Solution Summary

| Field | Value |
|---|---|
| Intermediate Channel | `SUYOG [AMV]` (`@itz_suyog_`) |
| Lead / Clue Keyword | `hidden ninja` (Channel Description) |
| Clue Comment | Comment on `Obito sad [ AMV ] 💔` by `@hiddenninja5770` |
| Secret Channel Name | `Hidden Ninja` |
| Channel Handle / ID | `hiddenninja5770` |

## OSINT Methodology

1. **Establish Intermediate Pivots:** When targets do not maintain direct links between primary identities and "alt" or burner accounts, search for intermediate hobby/niche channels (e.g., gaming, edits, fan pages) that bridge the persona.
2. **Examine Metadata & "About" Sections:** Descriptions, channel bios, and linked socials often contain subtle text snippets or keywords left by creators.
3. **Analyze Interactions & Comments:** Self-interactions, alternate accounts commenting on old videos, or shared aesthetics (e.g., Obito pfp) frequently expose burner/secret accounts.

## Tools Used

- **YouTube Search Engine:** Querying author-related keywords (`suyog amv`, `hidden ninja`).
- **YouTube Comment Section & Channel Details:** Identifying cross-account activity and verifying the `"secret account"` bio.

## Timeline

| Step | Action | Result |
|---|---|---|
| 1 | Searched `suyog amv` on YouTube | Located intermediate account `SUYOG [AMV]` (`@itz_suyog_`) |
| 2 | Inspected channel description | Found keyword clue `"hidden ninja"` |
| 3 | Checked comments on `Obito sad [ AMV ] 💔` | Found comment by `@hiddenninja5770` |
| 4 | Searched `hidden ninja` on YouTube | Discovered secret channel `Hidden Ninja` (`@hiddenninja5770`) |
| 5 | Verified bio on `@hiddenninja5770` | Confirmed `"secret account"` tag and assembled flag |
