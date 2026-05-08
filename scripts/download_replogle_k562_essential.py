#!/usr/bin/env python3
"""Fetch the Replogle 2022 K562 essential Perturb-seq dataset.

Outputs:
    data/raw/stage1a/replogle_2022_k562_essential.h5ad

Two retrieval strategies are attempted, in order:
    1. The pertpy data loader (preferred; mirrors the same processed h5ad
       used during manuscript preparation).
    2. A direct figshare download as a fallback.

Source publication:
    Replogle JM, et al. (2022). Mapping information-rich genotype-phenotype
    landscapes with genome-scale Perturb-seq. Cell, 185(14), 2559-2575.
    https://doi.org/10.1016/j.cell.2022.05.013

Public dataset record:
    https://plus.figshare.com/articles/dataset/_Mapping_information-rich_genotype-phenotype_landscapes_with_genome-scale_Perturb-seq_Replogle_et_al_2022_processed_Perturb-seq_datasets/20029387
"""
from __future__ import annotations

import shutil
import sys
import urllib.request
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
OUT_PATH = PROJECT_ROOT / "data/raw/stage1a/replogle_2022_k562_essential.h5ad"

# Figshare direct-download URL for the K562 essential h5ad file.
# Verify the version against the figshare record before relying on it for
# audit-grade reproducibility.
FIGSHARE_FILE_URL = (
    "https://plus.figshare.com/ndownloader/files/35775606"
)


def _fetch_via_pertpy(out_path: Path) -> bool:
    try:
        import pertpy as pt
    except ImportError:
        print("[info] pertpy is not installed; falling back to figshare", file=sys.stderr)
        return False

    print("[info] downloading via pertpy.dt.replogle_2022_k562_essential() ...")
    adata = pt.dt.replogle_2022_k562_essential()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    adata.write_h5ad(out_path)
    return True


def _fetch_via_figshare(out_path: Path) -> bool:
    print(f"[info] downloading from figshare: {FIGSHARE_FILE_URL}")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = out_path.with_suffix(out_path.suffix + ".part")
    with urllib.request.urlopen(FIGSHARE_FILE_URL) as response, open(tmp_path, "wb") as f:
        shutil.copyfileobj(response, f)
    tmp_path.rename(out_path)
    return True


def main() -> int:
    if OUT_PATH.exists():
        print(f"[skip] {OUT_PATH} already exists ({OUT_PATH.stat().st_size:,} bytes)")
        return 0
    if _fetch_via_pertpy(OUT_PATH):
        print(f"[done] wrote {OUT_PATH}")
        return 0
    if _fetch_via_figshare(OUT_PATH):
        print(f"[done] wrote {OUT_PATH}")
        return 0
    print("[error] could not retrieve dataset", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
