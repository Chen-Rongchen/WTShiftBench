from __future__ import annotations

from pathlib import Path

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


def save_figure(fig: plt.Figure, png_path: Path, pdf_path: Path, *, dpi: int = 300) -> list[Path]:
    ensure_dir(png_path.parent)
    ensure_dir(pdf_path.parent)
    finalize_manuscript_figure(fig)
    fig.savefig(png_path, dpi=dpi, bbox_inches="tight")
    fig.savefig(pdf_path, bbox_inches="tight")
    plt.close(fig)
    return [png_path, pdf_path]

