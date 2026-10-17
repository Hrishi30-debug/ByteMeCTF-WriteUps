# Sacrifice

**Author:** Urvish Bharde 
**Category:** Forensics  
**Difficulty:** Medium

## Challenge Description

> Recover a hidden flag from a PCAP file containing an embedded image and several layers of archived data.

## Resources

![pcap file](resources/soul.pcap)

## Summary

The challenge provides a `.pcap` capture file containing a transferred JPEG and multiple nested archive layers. The solution is to recover the image from the capture, use its metadata to unlock an embedded archive, and follow the hints through the compressed files until the encoded flag is found.

## Flag

```text
OWASP{4_50u1_f0r_4_50u1_v0rm1r}
```

---

## Step 1 — Extract the transferred JPEG

Open the supplied capture in Wireshark and inspect the transferred objects or streams. Export the JPEG named `manifest_final_047.jpg` for offline analysis.

## Step 2 — Recover the archive password from EXIF metadata

```bash
exiftool manifest_final_047.jpg
```

The `Comment` field contains the password needed to open an embedded ZIP archive.

## Step 3 — Extract the embedded ZIP archive

```bash
binwalk -e manifest_final_047.jpg
```

`binwalk` locates data appended to or embedded inside the JPEG and extracts it into a new directory:

```bash
cd _manifest_final_047.jpg.extracted
ls
```

Unpack the extracted ZIP using the password recovered from the EXIF `Comment` field:

```bash
unzip -P '<PASSWORD_FROM_COMMENT>' <archive>.zip
```

## Step 4 — Identify and decompress the nested archive

The archive contains a file named `comms.bin` with no useful extension. Identify its actual format from its magic bytes:

```bash
file comms.bin
```

Rename and decompress the file according to the format reported by `file`. For example, if it is gzip-compressed:

```bash
mv comms.bin comms.gz
gzip -d comms.gz
file comms
```

If it is bzip2-compressed instead:

```bash
mv comms.bin comms.bz2
bzip2 -d comms.bz2
file comms
```

Repeat the identification and decompression process until the result is identified as a tar archive:

```bash
mv comms comms.tar
tar -xf comms.tar
```

The extracted directory contains `README.txt` and the next set of instructions.

## Step 5 — Follow the README hint

```bash
cat README.txt
```

The README identifies which of the extracted communication files should be inspected:

```bash
cat <correct-comms-file>
```

The selected file contains a Base64-encoded value. Decode it to recover the flag:

```bash
echo '<BASE64_VALUE>' | base64 -d
```

## Solution Summary

| Field | Value |
|---|---|
| Initial artifact | PCAP containing a transferred JPEG |
| Metadata clue | EXIF `Comment` field |
| Embedded archive | Password-protected ZIP inside the JPEG |
| Nested data | Compressed file followed by a tar archive |
| Final encoding | Base64 |
| Flag | Not captured in the original notes |

## Root Cause / Forensics Methodology

1. **PCAP object extraction** — Files transferred in captured traffic can be reassembled and exported directly from Wireshark.
2. **Metadata inspection** — EXIF fields such as `Comment` can carry passwords or other clues without changing the visible image.
3. **Embedded archive discovery** — `binwalk` detects data appended to or embedded inside an otherwise valid image.
4. **Magic-byte identification** — File extensions are not authoritative; `file` reveals the actual format of an unknown binary.
5. **Layered decompression** — Each archive or compression layer must be identified and removed before the next layer can be inspected.
6. **Base64 decoding** — The final value is encoded rather than encrypted, so it can be recovered with a standard Base64 decoder.

## Tools Used

- Wireshark — export the JPEG from the PCAP
- `exiftool` — inspect EXIF metadata
- `binwalk` — locate and extract the embedded ZIP
- `unzip` — unpack the password-protected archive
- `file` — identify unknown file formats
- `gzip`, `bzip2`, and `tar` — unpack nested data
- `base64` — decode the final value

## Timeline

| Step | Action | Result |
|---|---|---|
| 1 | Export objects from the PCAP in Wireshark | `manifest_final_047.jpg` recovered |
| 2 | Run `exiftool manifest_final_047.jpg` | ZIP password found in the `Comment` field |
| 3 | Run `binwalk -e manifest_final_047.jpg` | Embedded ZIP extracted |
| 4 | Run `unzip -P '<password>' <archive>.zip` | `comms.bin` recovered |
| 5 | Run `file comms.bin` and decompress the reported format | Next archive layer revealed |
| 6 | Extract the tar archive | `README.txt` and communication files recovered |
| 7 | Read `README.txt` | Correct communication file identified |
| 8 | Decode the selected file with `base64 -d` | Encoded flag value recovered |
