# SOUL STONE — Shattered Soul QR Series

Seven progressive MISC challenges for ByteMe CTF.

## Player distribution

For each level, distribute ONLY:
- `README.txt`
- `pieces/`

Do NOT distribute:
- `organizer_manifest.json`
- `organizer_reference_qr.png`
- `SOLVED_QR.png`
- `FLAG.txt`

## Levels

0 — First Fragment: 3x3, shuffled  
1 — Shattered Memories: 4x4, shuffled + rotations  
2 — False Souls: 5x5 + rotations + decoys  
3 — Lost Edge: 6x6 + rotations + decoys  
4 — Judgment of Vormir: 7x7 + rotations + decoys  
5 — Soul World: 8x8 + rotations + flips + decoys  
6 — The Soul Stone: 10x10 + rotations + flips + decoys

The standalone `FINAL_FLAG_QR.png` contains:

`OWASP{Th3_f149_i5_h3r3}`

## Important

The included solver uses the organizer manifest so it can validate the generated set deterministically. For a genuine player solver, reconstruct pieces by image-edge matching and use QR decoding as the success criterion.
