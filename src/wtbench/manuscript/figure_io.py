from __future__ import annotations

from pathlib import Path
from typing import Literal

import matplotlib.pyplot as plt
import pandas as pd

from wtbench.manuscript.manuscript_style import finalize_manuscript_figure


def repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def ensure_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def write_tsv(df: pd.DataFrame, path: Path) -> Path:
    ensure_dir(path.parent)
    df.to_csv(path, sep="\t", index=False)
    return path


def save_figure(
    fig: plt.Figure,
    png_path: Path,
    pdf_path: Path,
    *,
    dpi: int = 1200,
    max_width: int = 5000,
    bbox_inches: Literal["tight"] | None = "tight",
) -> list[Path]:
    ensure_dir(png_path.parent)
    ensure_dir(pdf_path.parent)
    finalize_manuscript_figure(fig)
    save_kw: dict = {"dpi": dpi}
    if bbox_inches is None:
        save_kw["bbox_inches"] = None
    else:
        save_kw["bbox_inches"] = bbox_inches
    fig.savefig(png_path, **save_kw)
    fig.savefig(pdf_path, **save_kw)
    plt.close(fig)
    # Downscale PNG if exceeds max width (PDF stays vector)
    if max_width and png_path.exists():
        from PIL import Image as PILImage
        im = PILImage.open(png_path)
        if im.width > max_width:
            im = im.resize((max_width, int(im.height * max_width / im.width)), PILImage.LANCZOS)
            im.save(png_path)
    return [png_path, pdf_path]

