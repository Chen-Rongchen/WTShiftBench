#!/usr/bin/env python3
"""Build ED Fig 1 composite from individual panel PNGs.

Panel layout (top to bottom):
  Row 0 — panel a (dataset table)
  Row 1 — UMAP panels b–f (HCC38, HCC1143, K562 7d, K562 13d, Replogle K562 essential)
  Row 2 — target-gene expression arrow panels g–k
"""
from __future__ import annotations
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[2]
PDIR = ROOT / "manuscript/extended_data/Extended_Data_Figure_1/panels"
OUT = ROOT / "manuscript/extended_data/Extended_Data_Figure_1"
TARGET_W = 4000
UMAP_H = 800
ARROW_H = 700

FONT_PATH = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FONT_SIZE = 34
LETTER_X = 32
LETTER_Y = 18


def load(letter: str) -> Image.Image:
    return Image.open(PDIR / f"Extended_Data_Figure_1_panel_{letter}.png")


def add_panel_letter(img: Image.Image, letter: str) -> Image.Image:
    """Add bold panel letter top-left, matching ED Fig 3a style."""
    draw = ImageDraw.Draw(img)
    font = ImageFont.truetype(FONT_PATH, FONT_SIZE)
    draw.text((LETTER_X, LETTER_Y), letter, fill="#1F1F1F", font=font)
    return img


def main():
    # Row 0: Panel a (table)
    row0 = load("a")
    row0 = row0.resize((TARGET_W, int(row0.height * TARGET_W / row0.width)), Image.LANCZOS)

    # Row 1: UMAP panels b–f
    umap_letters = list("bcdef")
    umap_imgs = []
    for c in umap_letters:
        im = load(c)
        im = im.resize((int(im.width * UMAP_H / im.height), UMAP_H), Image.LANCZOS)
        umap_imgs.append(im)
    row1_w = sum(im.width for im in umap_imgs)
    row1 = Image.new("RGB", (row1_w, UMAP_H), "white")
    x = 0
    for im in umap_imgs:
        row1.paste(im, (x, 0))
        x += im.width
    row1 = row1.resize((TARGET_W, int(UMAP_H * TARGET_W / row1_w)), Image.LANCZOS)

    # Row 2: Arrow panels g–k
    arrow_letters = list("ghijk")
    arrow_imgs = []
    for c in arrow_letters:
        im = load(c)
        arrow_imgs.append(im.resize((int(im.width * ARROW_H / im.height), ARROW_H), Image.LANCZOS))
    row2_w = sum(im.width for im in arrow_imgs)
    row2 = Image.new("RGB", (row2_w, ARROW_H), "white")
    x = 0
    for im in arrow_imgs:
        row2.paste(im, (x, 0))
        x += im.width
    row2 = row2.resize((TARGET_W, int(ARROW_H * TARGET_W / row2_w)), Image.LANCZOS)

    # Vertical stack
    total_h = row0.height + row1.height + row2.height
    final = Image.new("RGB", (TARGET_W, total_h), "white")
    final.paste(row0, (0, 0))
    final.paste(row1, (0, row0.height))
    final.paste(row2, (0, row0.height + row1.height))

    final.save(OUT / "Extended_Data_Figure_1.png")
    test_dir = ROOT / "reports/manuscript_extended_data_v1/edfig1_test_composite"
    test_dir.mkdir(parents=True, exist_ok=True)
    final.save(test_dir / "edfig1_composite.png")
    n_umap = len(umap_letters)
    n_arr = len(arrow_letters)
    print(f"[OK] ED Fig 1 composite: {final.size}  (a + {n_umap} UMAPs + {n_arr} arrows)")


if __name__ == "__main__":
    main()
