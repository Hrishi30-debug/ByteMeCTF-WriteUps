#!/usr/bin/env python3

"""
SOUL STONE - QR Reconstruction Validator

Organizer-only validator for the Soul Stone QR challenge.

IMPORTANT:
Do NOT distribute organizer_manifest.json to players.

Dependencies:
    pip install pillow opencv-python
"""

from pathlib import Path
import argparse
import json

import cv2
from PIL import Image, ImageOps


# ============================================================
# QR DECODER
# ============================================================

def decode_qr(path):

    img = cv2.imread(
        str(path),
        cv2.IMREAD_GRAYSCALE
    )

    if img is None:
        return None

    detector = cv2.QRCodeDetector()

    data, points, _ = detector.detectAndDecode(img)

    return data if data else None


# ============================================================
# REVERSE PIECE TRANSFORMATION
# ============================================================

def inverse_transform(
    image,
    angle,
    hflip,
    vflip
):

    # Generator:
    # 1. horizontal flip
    # 2. vertical flip
    # 3. rotation

    p = image

    # Reverse rotation first
    p = p.rotate(
        (-angle) % 360,
        expand=False
    )

    # Reverse vertical flip
    if vflip:
        p = ImageOps.flip(p)

    # Reverse horizontal flip
    if hflip:
        p = ImageOps.mirror(p)

    return p


# ============================================================
# SOLVE ONE LEVEL
# ============================================================

def solve_level(level_dir):

    level_dir = Path(level_dir)

    manifest_path = (
        level_dir /
        "organizer_manifest.json"
    )

    if not manifest_path.exists():

        print(
            f"[!] Manifest missing: "
            f"{level_dir}"
        )

        return False


    manifest = json.loads(
        manifest_path.read_text()
    )


    n = manifest["grid"]

    tile_size = manifest["tile_size"]

    pieces_dir = level_dir / "pieces"
    if not pieces_dir.exists():
        candidates = [c for c in level_dir.glob("pieces*") if c.is_dir()]
        if candidates:
            pieces_dir = candidates[0]


    # Create blank canvas
    canvas = Image.new(
        "L",
        (
            n * tile_size,
            n * tile_size
        ),
        255
    )


    # ========================================================
    # RESTORE PIECES
    # ========================================================

    for item in manifest["pieces"]:

        # Ignore decoys
        if item["decoy"]:
            continue


        piece_path = (
            pieces_dir /
            item["file"]
        )


        piece = Image.open(
            piece_path
        ).convert("L")


        # Undo transformations
        piece = inverse_transform(
            piece,
            item["angle_applied"],
            item["hflip_applied"],
            item["vflip_applied"]
        )


        # Original position
        x = (
            item["source_col"]
            * tile_size
        )

        y = (
            item["source_row"]
            * tile_size
        )


        canvas.paste(
            piece,
            (x, y)
        )


    # ========================================================
    # SAVE RECONSTRUCTED QR
    # ========================================================

    solved_path = (
        level_dir /
        "SOLVED_QR.png"
    )

    canvas.save(
        solved_path
    )


    # ========================================================
    # DECODE QR
    # ========================================================

    decoded = decode_qr(
        solved_path
    )

    expected = manifest["message"]


    print()
    print("=" * 60)
    print(
        f"LEVEL: {level_dir.name}"
    )
    print("=" * 60)

    print(
        f"Decoded : {decoded!r}"
    )

    print(
        f"Expected: {expected!r}"
    )


    if decoded == expected:

        print(
            "STATUS  : PASS ✓"
        )

        return True

    else:

        print(
            "STATUS  : FAIL ✗"
        )

        return False


# ============================================================
# VALIDATE FINAL FLAG QR
# ============================================================

def validate_final_qr(root):

    final_qr = (
        root /
        "FINAL_FLAG_QR.png"
    )

    if not final_qr.exists():

        return True


    decoded = decode_qr(
        final_qr
    )


    print()
    print("=" * 60)
    print("FINAL FLAG QR")
    print("=" * 60)

    print(
        f"Decoded: {decoded!r}"
    )


    if decoded:

        print(
            "STATUS : PASS ✓"
        )

        return True

    print(
        "STATUS : FAIL ✗"
    )

    return False


# ============================================================
# MAIN
# ============================================================

def main():

    parser = argparse.ArgumentParser(
        description=(
            "Validate Soul Stone QR challenges"
        )
    )


    parser.add_argument(
        "root",
        nargs="?",
        default="soul_stone_levels"
    )


    args = parser.parse_args()

    root = Path(args.root)


    if not root.exists():

        print(
            f"[!] Directory not found: {root}"
        )

        raise SystemExit(1)


    success = True


    # Find levels
    level_dirs = sorted(
        root.glob("level_*")
    )


    if not level_dirs:

        print(
            "[!] No level directories found."
        )

        raise SystemExit(1)


    # Validate every level
    for level_dir in level_dirs:

        result = solve_level(
            level_dir
        )

        if not result:
            success = False


    # Validate final QR
    if not validate_final_qr(root):

        success = False


    print()
    print("=" * 60)


    if success:

        print(
            "ALL SOUL STONE LEVELS PASSED ✓"
        )

    else:

        print(
            "VALIDATION FAILED ✗"
        )


    print("=" * 60)


    raise SystemExit(
        0 if success else 1
    )


if __name__ == "__main__":

    main()