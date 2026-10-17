#!/usr/bin/env python3
"""
SOUL STONE - Shattered Soul QR Challenge Generator
Generates 7 progressively harder QR reconstruction levels.

Dependencies:
    pip install pillow qrcode numpy opencv-python
"""

from pathlib import Path
import argparse
import random
import shutil
import json

import qrcode
from PIL import Image, ImageOps


# ============================================================
# FLAGS
# ============================================================

FLAGS = {
    0: "OWASP{Th3_f1rst_fr4gm3nt}",
    1: "OWASP{Sh4tt3r3d_m3m0r13s}",
    2: "OWASP{Tru3_s0ul_0r_f4ls3}",
    3: "OWASP{Th3_l0st_3dg3}",
    4: "OWASP{J3dg3m3nt_0f_V0rm1r}",
    5: "OWASP{W3lc0m3_t0_th3_s0ul_w0rld}",
    6: "OWASP{Th3_S0ul_St0n3_1s_wh0l3}",
}


# ============================================================
# LEVEL CONFIGURATION
# ============================================================

LEVELS = {
    0: dict(
        name="first_fragment",
        grid=3,
        rotations=False,
        flips=False,
        decoys=0,
    ),

    1: dict(
        name="shattered_memories",
        grid=4,
        rotations=True,
        flips=False,
        decoys=0,
    ),

    2: dict(
        name="false_souls",
        grid=5,
        rotations=True,
        flips=False,
        decoys=4,
    ),

    3: dict(
        name="lost_edge",
        grid=6,
        rotations=True,
        flips=False,
        decoys=5,
    ),

    4: dict(
        name="judgment_of_vormir",
        grid=7,
        rotations=True,
        flips=False,
        decoys=8,
    ),

    5: dict(
        name="soul_world",
        grid=8,
        rotations=True,
        flips=True,
        decoys=10,
    ),

    6: dict(
        name="the_soul_stone",
        grid=10,
        rotations=True,
        flips=True,
        decoys=12,
    ),
}


# ============================================================
# QR MESSAGES
# ============================================================

MESSAGES = {
    0: "SOUL STONE // FIRST FRAGMENT // " + FLAGS[0],

    1: "SOUL STONE // SHATTERED MEMORIES // " + FLAGS[1],

    2: "SOUL STONE // FALSE SOULS // " + FLAGS[2],

    3: "SOUL STONE // LOST EDGE // " + FLAGS[3],

    4: "SOUL STONE // JUDGMENT OF VORMIR // " + FLAGS[4],

    5: "SOUL STONE // SOUL WORLD // " + FLAGS[5],

    6: "SOUL STONE // THE SOUL STONE // " + FLAGS[6],
}


# ============================================================
# CREATE QR
# ============================================================

def make_qr(payload: str, size: int) -> Image.Image:

    qr = qrcode.QRCode(
        version=None,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=10,
        border=4,
    )

    qr.add_data(payload)
    qr.make(fit=True)

    img = qr.make_image(
        fill_color="black",
        back_color="white"
    ).convert("L")

    # Preserve sharp QR modules
    img = img.resize(
        (size, size),
        Image.Resampling.NEAREST
    )

    return img


# ============================================================
# SAVE PIECE
# ============================================================

def save_piece(im, path):

    im.convert("L").save(
        path,
        "PNG",
        optimize=True
    )


# ============================================================
# CREATE LEVEL
# ============================================================

def create_level(root: Path, level: int, seed: int):

    cfg = LEVELS[level]

    rng = random.Random(
        seed + level * 10007
    )

    n = cfg["grid"]

    # Larger QR for higher levels
    side = 1200 if n <= 8 else 1600

    qr = make_qr(
        MESSAGES[level],
        side
    )

    # Make sure image divides exactly into grid
    tile = side // n

    side = tile * n

    qr = qr.crop(
        (0, 0, side, side)
    )

    out = root / (
        f"level_{level}_{cfg['name']}"
    )

    if out.exists():
        shutil.rmtree(out)

    pieces_dir = out / "pieces"

    pieces_dir.mkdir(
        parents=True
    )

    # Organizer reference
    qr.save(
        out / "organizer_reference_qr.png"
    )

    # ========================================================
    # SPLIT QR
    # ========================================================

    pieces = []

    for r in range(n):

        for c in range(n):

            piece = qr.crop(
                (
                    c * tile,
                    r * tile,
                    (c + 1) * tile,
                    (r + 1) * tile
                )
            )

            pieces.append(
                (r, c, piece)
            )


    # ========================================================
    # CREATE DECOYS
    # ========================================================

    for _ in range(cfg["decoys"]):

        src_r, src_c, src = rng.choice(
            pieces
        )

        dec = src.copy()

        px = dec.load()

        w, h = dec.size

        for _ in range(
            max(3, tile // 30)
        ):

            x = rng.randrange(w)

            y = rng.randrange(h)

            radius = rng.randrange(
                max(2, tile // 20),
                max(3, tile // 8)
            )

            for yy in range(
                max(0, y - radius),
                min(h, y + radius)
            ):

                for xx in range(
                    max(0, x - radius),
                    min(w, x + radius)
                ):

                    px[xx, yy] = (
                        255 - px[xx, yy]
                    )

        pieces.append(
            (-1, -1, dec)
        )


    # Shuffle everything
    rng.shuffle(pieces)


    # ========================================================
    # ORGANIZER MANIFEST
    # ========================================================

    manifest = {

        "level": level,

        "name": cfg["name"],

        "grid": n,

        "tile_size": tile,

        "decoys": cfg["decoys"],

        "rotations": cfg["rotations"],

        "flips": cfg["flips"],

        "seed": seed,

        "flag": FLAGS[level],

        "message": MESSAGES[level],

        "pieces": []
    }


    # ========================================================
    # TRANSFORM + SAVE PIECES
    # ========================================================

    for idx, (r, c, piece) in enumerate(
        pieces,
        1
    ):

        transform = {

            "angle": 0,

            "hflip": False,

            "vflip": False
        }


        # Rotation
        if cfg["rotations"]:

            transform["angle"] = rng.choice(
                [0, 90, 180, 270]
            )


        # Flips
        if cfg["flips"]:

            transform["hflip"] = bool(
                rng.getrandbits(1)
            )

            transform["vflip"] = bool(
                rng.getrandbits(1)
            )


        p = piece


        if transform["hflip"]:

            p = ImageOps.mirror(p)


        if transform["vflip"]:

            p = ImageOps.flip(p)


        p = p.rotate(
            transform["angle"],
            expand=False
        )


        filename = (
            f"piece_{idx:03d}.png"
        )


        save_piece(
            p,
            pieces_dir / filename
        )


        manifest["pieces"].append({

            "file": filename,

            "source_row": r,

            "source_col": c,

            "angle_applied":
                transform["angle"],

            "hflip_applied":
                transform["hflip"],

            "vflip_applied":
                transform["vflip"],

            "decoy":
                r == -1
        })


    # ========================================================
    # PLAYER README
    # ========================================================

    desc = f"""
╔══════════════════════════════════════╗
║          SOUL STONE                  ║
║       SHATTERED SOUL                 ║
╚══════════════════════════════════════╝

LEVEL {level}
{cfg['name'].replace('_', ' ').upper()}

The Soul Stone was shattered across Vormir.

These fragments are all that remain.

Restore the Stone.
Recover the message.

The final secret follows the format:

OWASP{{...}}

Pieces : {len(pieces)}
Grid   : {n} x {n}

Good luck, mortal.
"""

    (out / "README.txt").write_text(
        desc.strip() + "\n"
    )


    # Organizer manifest
    (
        out / "organizer_manifest.json"
    ).write_text(
        json.dumps(
            manifest,
            indent=2
        )
    )

    return out


# ============================================================
# MAIN
# ============================================================

def main():

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--out",
        default="soul_stone_levels"
    )

    parser.add_argument(
        "--seed",
        type=int,
        default=20261004
    )

    args = parser.parse_args()

    root = Path(args.out)


    if root.exists():

        shutil.rmtree(root)


    root.mkdir(
        parents=True
    )


    # Generate all 7 levels
    for level in LEVELS:

        create_level(
            root,
            level,
            args.seed
        )


    # ========================================================
    # FINAL STANDALONE FLAG QR
    # ========================================================

    final_qr = make_qr(
        FLAGS[6],
        1200
    )

    final_path = (
        root / "FINAL_FLAG_QR.png"
    )

    final_qr.save(
        final_path
    )


    # Store all flags for organizer
    flags_file = (
        root / "FLAGS.txt"
    )

    with flags_file.open("w") as f:

        for level in sorted(FLAGS):

            f.write(
                f"Level {level}: "
                f"{FLAGS[level]}\n"
            )


    print()
    print(
        "======================================"
    )

    print(
        " SOUL STONE CHALLENGE GENERATED"
    )

    print(
        "======================================"
    )

    print(
        f"[+] Levels generated : {len(LEVELS)}"
    )

    print(
        f"[+] Output directory  : {root}"
    )

    print(
        f"[+] Final flag QR     : {final_path}"
    )

    print()

    for level in sorted(FLAGS):

        print(
            f"[Level {level}] "
            f"{FLAGS[level]}"
        )

    print()


if __name__ == "__main__":

    main()