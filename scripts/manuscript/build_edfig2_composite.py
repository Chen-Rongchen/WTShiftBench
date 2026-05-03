#!/usr/bin/env python3
"""Build ED Fig 2 composite: row0 (a+b), row1 (c+d), row2 (e). PIL vertical stack."""
from __future__ import annotations
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[2]
PDIR = ROOT / "manuscript/extended_data/Extended_Data_Figure_2/panels"
OUT = ROOT / "manuscript/extended_data/Extended_Data_Figure_2"

FONT_PATH = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FONT_SIZE = 34
LETTER_X = 32
LETTER_Y = 18


def load(letter: str) -> Image.Image:
    return Image.open(PDIR / f"Extended_Data_Figure_2_panel_{letter}.png")


def hpair(left: Image.Image, right: Image.Image) -> Image.Image:
    """Match heights, place side by side."""
    h = max(left.height, right.height)
    l = left.resize((int(left.width * h / left.height), h), Image.LANCZOS)
    r = right.resize((int(right.width * h / right.height), h), Image.LANCZOS)
    row = Image.new("RGB", (l.width + r.width, h), "white")
    row.paste(l, (0, 0))
    row.paste(r, (l.width, 0))
    return row


def add_panel_letter(img: Image.Image, letter: str) -> Image.Image:
    """Bold panel letter top-left, matching ED Fig 3a style."""
    draw = ImageDraw.Draw(img)
    font = ImageFont.truetype(FONT_PATH, FONT_SIZE)
    draw.text((LETTER_X, LETTER_Y), letter, fill="#1F1F1F", font=font)
    return img


def main():
    # Row 0: a + b (each with own panel letter)
    # add_panel_letter calls removed
    row0 = hpair(load("a"), load("b"))
    # Row 1: c + d
    row1 = hpair(load("c"), load("d"))
    # Row 2: e
    img_e = load("e")  # add_panel_letter removed

    # Rows 0-1 determine width; panel e keeps native size (centered)
    W = max(row0.width, row1.width)
    row0_s = row0 if row0.width == W else row0.resize((W, int(row0.height * W / row0.width)), Image.LANCZOS)
    row1_s = row1 if row1.width == W else row1.resize((W, int(row1.height * W / row1.width)), Image.LANCZOS)
    # Panel e: center at native width, pad with white
    if img_e.width < W:
        pad = Image.new("RGB", (W, img_e.height), "white")
        pad.paste(img_e, (0, 0))
        row2 = pad
    else:
        row2 = img_e.resize((W, int(img_e.height * W / img_e.width)), Image.LANCZOS)

    total_h = row0_s.height + row1_s.height + row2.height
    final = Image.new("RGB", (W, total_h), "white")
    final.paste(row0_s, (0, 0))
    final.paste(row1_s, (0, row0_s.height))
    final.paste(row2, (0, row0_s.height + row1_s.height))

    # Downscale to target width for consistent resolution
    target_w = 4500
    final = final.resize((target_w, int(total_h * target_w / W)), Image.LANCZOS)

    final.save(OUT / "Extended_Data_Figure_2.png")
    test_dir = ROOT / "reports/manuscript_extended_data_v1/edfig2_test_composite"
    test_dir.mkdir(parents=True, exist_ok=True)
    final.save(test_dir / "edfig2_composite.png")
    print(f"[OK] ED Fig 2 composite: {final.size}")


if __name__ == "__main__":
    main()
