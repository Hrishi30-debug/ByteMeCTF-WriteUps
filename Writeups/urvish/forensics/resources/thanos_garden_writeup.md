# Thanos's Garden (Forensics, Medium)

**Author:** Urvish Bharde
**Category:** Forensics  
**Difficulty:** Medium

## Challenge Description

> Recover a hidden flag from an encrypted disk image, using clues hidden in an accompanying archive to find both the decryption passphrase and the one genuine file among hundreds of decoys.

## Summary

The challenge provides a disguised ZIP archive and a compressed, LUKS-encrypted disk image. The archive reveals the decryption passphrase and a riddle, while the mounted image contains hundreds of decoy images. A contact sheet and EXIF metadata identify the one genuine image, whose pixel data contains the flag.

## Flag

```text
OWASP{THE_ONLY_MEMORY_THAT_STAYED}
```

---

## Step 1 — Identify and extract the manifest

The first artifact, `manifest.vault`, has a misleading extension. Check its actual format before attempting to open it:

```bash
file manifest.vault
```

```text
manifest.vault: Zip archive data, made by v3.0 UNIX, extract using at least v1.0, last modified Sep 19 2026 01:59:04, uncompressed size 0, method=store
```

Rename the archive and extract its contents:

```bash
mv manifest.vault manifest.zip
unzip manifest.zip
```

```text
Archive:  manifest.zip
  inflating: manifest_contents/README.txt
```

Read the recovery note:

```bash
cat manifest_contents/README.txt
```

```text
Recovery note: the drive is encrypted.
Passphrase: S0ulWorldMemory
He built a thousand false gardens to bury one true memory.
```

The README provides both the LUKS passphrase and the riddle that will help distinguish the real image from the decoys.

## Step 2 — Decrypt and mount the disk image

Decompress the disk image and verify its format:

```bash
gzip -d thanos_garden.img.gz
file thanos_garden.img
```

```text
thanos_garden.img: LUKS encrypted file, ver 2, header size 16384, ...
```

The image is a LUKS2 volume. Open it and mount it read-only with the recovered passphrase:

```bash
echo -n "S0ulWorldMemory" | sudo cryptsetup luksOpen thanos_garden.img evidence -d -
sudo mkdir -p /mnt/evidence
sudo mount -o ro /dev/mapper/evidence /mnt/evidence
```

## Step 3 — Survey the image collection

Count the files in the `DCIM` directory:

```bash
ls /mnt/evidence/DCIM | wc -l
```

```text
463
```

The directory also contains another clue:

```bash
cat /mnt/evidence/DCIM/README.txt
```

```text
He built a thousand false gardens to bury one true memory.
Only one frame in this archive was never an illusion.
```

There are 463 images, most of which are warm-toned decoys. A smaller group has cooler, purplish colors, matching the visual theme of the challenge and providing a practical way to narrow the candidate set.

## Step 4 — Narrow the candidates with a contact sheet

Create a thumbnail grid of the images to make the visual distinction easier to inspect:

```bash
cd /mnt/evidence/DCIM
montage GARDEN_*.png -tile 20x -geometry 64x64+2+2 /tmp/overview.png
```

The contact sheet makes the warm/cool split obvious, reducing the search from hundreds of images to roughly a dozen cool-toned candidates.

## Step 5 — Identify the genuine image using metadata

Inspect the EXIF `Keywords` field on the remaining candidates:

```bash
for f in GARDEN_20*.png; do echo "$f:"; exiftool -Keywords "$f"; done
```

```text
GARDEN_2004.png:
Keywords                       : unforgotten
GARDEN_2009.png:
Keywords                       : illusion
```

`GARDEN_2004.png` is tagged `unforgotten`, matching the riddle's reference to the one true memory. The `illusion` tag on `GARDEN_2009.png` confirms that it is a decoy.

## Step 6 — Extract the flag from the genuine image

Use `zsteg` to inspect the pixel data of the identified image:

```bash
zsteg GARDEN_2004.png | grep -i owasp
```

```text
imagedata           .. text: "OWASP{THE_ONLY_MEMORY_THAT_STAYED}"
```

After recovering the flag, cleanly unmount and close the encrypted volume:

```bash
sudo umount /mnt/evidence
sudo cryptsetup luksClose evidence
```

## Solution Summary

| Field | Value |
|---|---|
| Initial manifest | `manifest.vault`, a ZIP with a misleading extension |
| Disk image | `thanos_garden.img.gz`, containing a LUKS2 volume |
| LUKS passphrase | `S0ulWorldMemory` |
| Candidate set | 463 images, mostly decoys |
| Genuine image | `GARDEN_2004.png` |
| Metadata clue | EXIF `Keywords: unforgotten` |
| Flag location | Steganographic pixel data |

## Root Cause / Forensics Methodology

1. **File signatures override extensions** — `manifest.vault` is a normal ZIP archive despite its custom extension, and `file` reveals its true format.
2. **Supporting notes provide the next credential** — extracting the manifest exposes the LUKS passphrase and the riddle used later in the investigation.
3. **Strong encryption still depends on secret handling** — LUKS protects the disk image, but the passphrase is supplied in the accompanying README.
4. **Visual triage reduces a large decoy set** — a contact sheet quickly separates the warm-toned decoys from the cooler candidate images.
5. **Redundant clues identify the target** — the riddle, image colors, and EXIF `Keywords` all point toward the single `unforgotten` image.
6. **Steganography hides the final data** — `zsteg` recovers text embedded in the selected image's pixel data.

## Tools Used

- `file` — identify artifacts by their contents rather than their extensions
- `unzip` — extract the disguised manifest archive
- `gzip` — decompress the disk image
- `cryptsetup` — open and close the LUKS2 volume
- `mount` — mount the evidence volume read-only
- `montage` (ImageMagick) — generate a contact sheet
- `exiftool` — inspect EXIF metadata
- `zsteg` — extract steganographic data from the genuine image

## Timeline

| Step | Action | Result |
|---|---|---|
| 1 | Run `file manifest.vault` | Identified the file as a ZIP archive |
| 2 | Rename and unzip the manifest | `README.txt` extracted |
| 3 | Read `manifest_contents/README.txt` | LUKS passphrase and riddle recovered |
| 4 | Decompress and inspect `thanos_garden.img` | Confirmed a LUKS2 volume |
| 5 | Open with `cryptsetup` and mount read-only | Evidence volume became available |
| 6 | Count files in `DCIM` | 463 images found |
| 7 | Read the second `README.txt` | Confirmed that only one image was genuine |
| 8 | Generate a contact sheet with `montage` | Warm decoys separated from cool candidates |
| 9 | Inspect `Keywords` with `exiftool` | `GARDEN_2004.png` identified as `unforgotten` |
| 10 | Run `zsteg` on the genuine image | Flag extracted from pixel data |
| 11 | Unmount and close the LUKS volume | Evidence cleanly closed |
