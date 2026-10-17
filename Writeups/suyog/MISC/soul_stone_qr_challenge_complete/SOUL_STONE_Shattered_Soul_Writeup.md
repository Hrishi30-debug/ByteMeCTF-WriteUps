# ByteMe CTF 2026 — SOUL STONE: Shattered Soul (Misc)

**Author:** OWASP PCCOE Student Chapter  
**Category:** Misc  
**Difficulty:** Easy → Hard  
**Levels:** 7  
**Flag Format:** `OWASP{...}`

## Challenge Description

> The Soul Stone was shattered across Vormir.
>
> Seven fragments of its power remain, but each fragment has been broken into pieces and scattered.
>
> Reconstruct the Stone at every stage and recover the message hidden inside it.
>
> Each level introduces a new complication, progressively increasing the difficulty of the QR reconstruction.

The challenge is presented as a seven-level progression:

| Level | Name | Grid | Additional Difficulty |
|---|---|---:|---|
| 0 | First Fragment | 3 × 3 | Basic reconstruction |
| 1 | Shattered Memories | 4 × 4 | Rotated pieces |
| 2 | False Souls | 5 × 5 | Decoy pieces + rotation |
| 3 | Lost Edge | 6 × 6 | More decoys + rotation |
| 4 | Judgment of Vormir | 7 × 7 | Increased decoys + rotation |
| 5 | Soul World | 8 × 8 | Flips + rotation + decoys |
| 6 | The Soul Stone | 10 × 10 | Maximum complexity |

---

# Summary

Each level contains a QR code that has been divided into multiple image fragments.

The fragments are shuffled and, depending on the level, may also be rotated, flipped, or mixed with decoy fragments.

The objective is to reconstruct the original QR image and decode the message contained within it.

The general solving workflow is:

```text
Collect QR fragments
        ↓
Identify valid fragments
        ↓
Determine orientation
        ↓
Arrange fragments
        ↓
Reconstruct QR image
        ↓
Decode QR
        ↓
Recover flag
```

The challenge starts as a manual image puzzle and gradually becomes more suitable for scripting and image-processing techniques.

---

# Level 0 — First Fragment

## Challenge Description

> A single fragment has been recovered from the ruins of Vormir.
>
> The fragment is damaged, but its pattern remains intact.
>
> Reassemble the fragments and recover the first message of the Soul Stone.

## Configuration

```text
Grid:       3 × 3
Pieces:     9
Rotations:  No
Flips:      No
Decoys:     0
```

## Step 1 — Inspect the Pieces

The challenge provides nine PNG files:

```text
pieces/
├── piece_001.png
├── piece_002.png
├── ...
└── piece_009.png
```

Each image represents one section of the original QR code.

Since there are no rotations or decoys, the main task is determining the correct position of each fragment.

## Step 2 — Reconstruct the QR

The pieces can be arranged by comparing their adjacent black/white patterns.

The final image forms a `3 × 3` QR grid.

Once the pieces are correctly positioned, save the result as:

```text
SOLVED_QR.png
```

## Step 3 — Decode

The QR can be decoded using a standard QR scanner or:

```bash
zbarimg SOLVED_QR.png
```

The decoded message contains the flag.

## Flag

```text
OWASP{Th3_f1rst_fr4gm3nt}
```

---

# Level 1 — Shattered Memories

## Challenge Description

> The first fragment was only the beginning.
>
> The Soul Stone no longer remembers which way its fragments were facing.
>
> Restore the memories of the Stone.

## Configuration

```text
Grid:       4 × 4
Pieces:     16
Rotations:  Yes
Flips:      No
Decoys:     0
```

## Step 1 — Identify the New Mechanic

Unlike Level 0, fragments can now be rotated by:

```text
0°
90°
180°
270°
```

Therefore, a fragment's location and orientation both have to be determined.

## Step 2 — Test Orientations

For each fragment, rotate it through the four possible orientations and compare its edges with neighboring pieces.

The QR's finder patterns are particularly useful for identifying corner regions.

## Step 3 — Reconstruct

After determining the correct positions and orientations, assemble the `4 × 4` image.

The reconstructed QR can then be scanned normally.

## Flag

```text
OWASP{Sh4tt3r3d_m3m0r13s}
```

---

# Level 2 — False Souls

## Challenge Description

> Not every fragment belongs to the Soul Stone.
>
> Among the recovered pieces are false fragments.
>
> Separate the true pieces from the false souls.

## Configuration

```text
Grid:       5 × 5
Real Pieces: 25
Decoys:      4
Total:       29
Rotations:   Yes
Flips:       No
```

## Step 1 — Identify Candidate Pieces

There are 29 pieces, but only 25 belong to the original QR.

The four remaining pieces are decoys.

A useful way to identify them is to compare the edges of each piece against the edges of other pieces.

For example:

```text
A.right  ↔  B.left
A.bottom ↔ B.top
```

Pieces that consistently have poor matches are likely to be decoys.

## Step 2 — Resolve Rotations

Each valid piece can have one of four rotations:

```text
0°
90°
180°
270°
```

The correct orientation should produce continuous QR patterns across neighboring boundaries.

## Step 3 — Reconstruct the QR

Once the 25 valid pieces are identified, arrange them into:

```text
5 × 5
```

and decode the resulting QR.

## Flag

```text
OWASP{Tru3_s0ul_0r_f4ls3}
```

---

# Level 3 — Lost Edge

## Challenge Description

> The Stone is almost recognizable.
>
> But the boundary between the fragments has been lost.
>
> Reconstruct the remaining pieces and recover the hidden message.

## Configuration

```text
Grid:       6 × 6
Real Pieces: 36
Decoys:      5
Total:       41
Rotations:   Yes
Flips:       No
```

## Step 1 — Remove the Decoys

The input contains 41 pieces.

Only 36 are required for the QR.

Compare the edge patterns of the fragments and identify the five pieces that do not participate in a consistent QR arrangement.

## Step 2 — Identify QR Finder Patterns

A QR code contains three large finder patterns.

These patterns can be used to identify likely corner fragments.

A finder pattern has a characteristic structure:

```text
███████
█     █
█ ███ █
█ ███ █
█ ███ █
█     █
███████
```

Finding fragments containing these structures significantly reduces the search space.

## Step 3 — Reconstruct

Arrange the 36 valid pieces into the `6 × 6` grid, correcting rotations as necessary.

The resulting QR can then be decoded.

> **Implementation note:** The current generator retains the QR quiet zone. The challenge name refers to the fragmented boundary rather than actually deleting the QR quiet zone.

## Flag

```text
OWASP{Th3_l0st_3dg3}
```

---

# Level 4 — Judgment of Vormir

## Challenge Description

> What you seek is not given. It must be earned.
>
> The guardian of Vormir has scattered the fragments across the void.
>
> Restore every fragment and prove that you are worthy.

## Configuration

```text
Grid:       7 × 7
Real Pieces: 49
Decoys:      8
Total:       57
Rotations:   Yes
Flips:       No
```

## Step 1 — Reduce the Search Space

There are 57 pieces, but only 49 belong to the QR.

Start by identifying the pieces that have strong edge relationships with other pieces.

For automated solving, represent each image edge as a pixel vector.

For example:

```python
left_edge = image[:, 0]
right_edge = image[:, -1]
top_edge = image[0, :]
bottom_edge = image[-1, :]
```

## Step 2 — Calculate Edge Similarity

For two horizontally adjacent pieces:

```text
A → B
```

compare:

```text
A.right
B.left
```

A simple similarity metric is Mean Squared Error:

```python
MSE = mean((A_right - B_left) ** 2)
```

Repeat the process for vertical neighbors.

## Step 3 — Account for Rotation

Each candidate piece must be evaluated at:

```text
0°
90°
180°
270°
```

The orientation producing the strongest edge matches is selected.

## Step 4 — Reconstruct

Once the 49 valid pieces have been determined, reconstruct the `7 × 7` QR.

Decode the completed image.

## Flag

```text
OWASP{J3dg3m3nt_0f_V0rm1r}
```

---

# Level 5 — Soul World

## Challenge Description

> You have entered the Soul World.
>
> Nothing here is what it appears to be.
>
> Some fragments have been rotated.
> Some have been reflected.
> Others are false memories.
>
> Trust nothing. Reconstruct everything.

## Configuration

```text
Grid:             8 × 8
Real Pieces:      64
Decoys:           10
Total:            74
Rotations:        Yes
Horizontal Flip:  Yes
Vertical Flip:    Yes
```

## Step 1 — Identify Valid Pieces

There are 74 pieces in total.

Only 64 belong to the QR.

The ten decoys must be eliminated based on edge compatibility.

## Step 2 — Test Transformations

A piece may have been transformed using:

```text
Rotation:
    0°
    90°
    180°
    270°

Horizontal flip
Vertical flip
```

Therefore, each piece needs to be evaluated under multiple orientations.

## Step 3 — Use QR Structure

The three finder patterns provide strong constraints.

They normally occur near three corners of the reconstructed QR.

Once a candidate finder pattern is located, its position and orientation can be used to constrain nearby fragments.

## Step 4 — Reconstruct

After selecting the 64 valid pieces and resolving their transformations, construct the `8 × 8` image.

Save the result:

```text
SOLVED_QR.png
```

Then decode:

```bash
zbarimg SOLVED_QR.png
```

## Flag

```text
OWASP{W3lc0m3_t0_th3_s0ul_w0rld}
```

---

# Level 6 — The Soul Stone

## Challenge Description

> You have crossed Vormir.
>
> You have survived the Soul World.
>
> One final reconstruction remains.
>
> One hundred fragments.
>
> Countless false memories.
>
> Complete the Soul Stone.

## Configuration

```text
Grid:             10 × 10
Real Pieces:      100
Decoys:           12
Total:            112
Rotations:        Yes
Horizontal Flip:  Yes
Vertical Flip:    Yes
```

## Step 1 — Analyze the Dataset

The final level contains 112 fragments.

Only 100 are part of the QR.

The remaining 12 are decoys.

At this point, manually testing every possible arrangement is impractical.

## Step 2 — Identify Finder Patterns

Search the pieces for sections of the QR finder patterns.

These patterns provide reliable information about:

- QR corners
- orientation
- relative piece placement

This greatly reduces the search space.

## Step 3 — Generate Transformations

For every candidate piece, generate the possible transformations:

```text
Original
90°
180°
270°
Horizontal flip
Vertical flip
```

and the applicable combinations.

## Step 4 — Build an Edge Compatibility Matrix

For each candidate pair, calculate how well their edges match.

Horizontal comparison:

```text
A.right ↔ B.left
```

Vertical comparison:

```text
A.bottom ↔ B.top
```

A low pixel difference indicates a strong match.

## Step 5 — Remove Decoys

Pieces that do not form strong relationships with the rest of the image can be classified as decoys.

After removing the 12 decoys, exactly 100 pieces remain.

## Step 6 — Reconstruct the QR

Arrange the pieces into:

```text
10 × 10
```

while applying the correct transformation to each piece.

Save the final image as:

```text
SOLVED_QR.png
```

## Step 7 — Decode

Using `zbarimg`:

```bash
zbarimg SOLVED_QR.png
```

or OpenCV:

```python
import cv2

img = cv2.imread("SOLVED_QR.png")

detector = cv2.QRCodeDetector()

data, points, _ = detector.detectAndDecode(img)

print(data)
```

The QR reveals the final flag.

## Flag

```text
OWASP{Th3_S0ul_St0n3_1s_wh0l3}
```

---

# Organizer Validation

The challenge generator produces an organizer manifest containing the original position and transformation of every piece.

The manifest contains:

```json
{
    "file": "piece_001.png",
    "source_row": 2,
    "source_col": 4,
    "angle_applied": 90,
    "hflip_applied": false,
    "vflip_applied": true,
    "decoy": false
}
```

This allows the organizer solver to reconstruct the QR deterministically and verify that the generated challenge is valid.

Run:

```bash
python3 solve_soul_stone.py soul_stone_levels
```

A successful validation should report:

```text
LEVEL 0 → PASS
LEVEL 1 → PASS
LEVEL 2 → PASS
LEVEL 3 → PASS
LEVEL 4 → PASS
LEVEL 5 → PASS
LEVEL 6 → PASS
FINAL FLAG QR → PASS
```

The organizer manifest and reference QR images must not be distributed with the player challenge.

---

# Flags

| Level | Name | Flag |
|---:|---|---|
| 0 | First Fragment | `OWASP{Th3_f1rst_fr4gm3nt}` |
| 1 | Shattered Memories | `OWASP{Sh4tt3r3d_m3m0r13s}` |
| 2 | False Souls | `OWASP{Tru3_s0ul_0r_f4ls3}` |
| 3 | Lost Edge | `OWASP{Th3_l0st_3dg3}` |
| 4 | Judgment of Vormir | `OWASP{J3dg3m3nt_0f_V0rm1r}` |
| 5 | Soul World | `OWASP{W3lc0m3_t0_th3_s0ul_w0rld}` |
| 6 | The Soul Stone | `OWASP{Th3_S0ul_St0n3_1s_wh0l3}` |

---

# Root Cause / Challenge Design

The challenge is based on image reconstruction rather than a software vulnerability.

The increasing difficulty is introduced through:

1. **Increasing grid size** — more fragments have to be placed correctly.
2. **Rotation** — pieces are no longer guaranteed to have the correct orientation.
3. **Decoys** — additional fragments do not belong to the QR.
4. **Flips** — later levels introduce horizontal and vertical reflections.
5. **QR structure analysis** — finder patterns provide constraints for reconstruction.
6. **Edge matching** — image boundaries can be compared programmatically to identify neighboring pieces.

The main intended skill progression is:

```text
Visual reconstruction
        ↓
Orientation handling
        ↓
Decoy identification
        ↓
Image analysis
        ↓
Constraint solving
        ↓
Computer-assisted reconstruction
```

---

# Tools Used

- Image viewer
- QR code scanner
- `zbarimg`
- Python 3
- Pillow
- NumPy
- OpenCV
- `qrcode`

Install the required Python dependencies with:

```bash
pip install pillow qrcode numpy opencv-python
```

---

# Timeline of Commands

| Step | Action | Result |
|---|---|---|
| 1 | Inspect `pieces/` | Determine number of fragments |
| 2 | Identify QR finder patterns | Locate likely QR corners |
| 3 | Compare piece edges | Determine neighboring fragments |
| 4 | Test rotations/flips | Determine correct orientation |
| 5 | Remove decoy pieces | Keep only valid QR fragments |
| 6 | Reconstruct QR | Generate `SOLVED_QR.png` |
| 7 | Run `zbarimg SOLVED_QR.png` | Decode hidden message |
| 8 | Extract `OWASP{...}` | Capture level flag |

---

# Final Notes

The challenge is designed as a progressive seven-level QR reconstruction series.

The first levels can be solved visually, while the later levels encourage automation using image processing and constraint-solving techniques.

The final objective is to reconstruct the complete Soul Stone and recover:

```text
OWASP{Th3_S0ul_St0n3_1s_wh0l3}
```
