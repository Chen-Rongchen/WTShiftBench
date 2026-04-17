from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import pandas as pd

from wtbench.manuscript.hash_manifest import sha256_file


DEFAULT_CONFIG = Path("configs/manuscript/supplementary_tables_v1.json")


def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def load_config(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def tsv_shape(path: Path) -> tuple[int | None, int | None]:
    if path.suffix != ".tsv":
        return None, None
    df = pd.read_csv(path, sep="\t")
    return int(df.shape[0]), int(df.shape[1])


def file_record(root: Path, table: dict[str, Any], rel_path: str) -> dict[str, Any]:
    path = root / rel_path
    if not path.exists():
        raise FileNotFoundError(rel_path)
    rows, columns = tsv_shape(path)
    return {
        "table_id": table["table_id"],
        "title": table["title"],
        "claim_layer": table["claim_layer"],
        "path": rel_path,
        "suffix": path.suffix.lstrip("."),
        "bytes": path.stat().st_size,
        "rows": rows,
        "columns": columns,
        "sha256": sha256_file(path),
    }


def write_outputs(root: Path, config: dict[str, Any], records: list[dict[str, Any]]) -> None:
    out = root / config["output_dir"]
    out.mkdir(parents=True, exist_ok=True)
    index = pd.DataFrame(records)
    index.to_csv(out / "supplementary_table_file_index.tsv", sep="\t", index=False)
    summary = (
        index.groupby(["table_id", "title", "claim_layer"], as_index=False)
        .agg(n_files=("path", "count"), total_bytes=("bytes", "sum"), tsv_files=("rows", lambda x: int(x.notna().sum())))
        .sort_values("table_id")
    )
    summary.to_csv(out / "supplementary_table_summary.tsv", sep="\t", index=False)
    manifest = {
        "config": str(DEFAULT_CONFIG),
        "n_tables": len(config["tables"]),
        "n_files": len(records),
        "outputs": {
            "file_index": str((out / "supplementary_table_file_index.tsv").relative_to(root)),
            "summary": str((out / "supplementary_table_summary.tsv").relative_to(root)),
        },
        "files": records,
    }
    with (out / "supplementary_table_manifest.json").open("w", encoding="utf-8") as fh:
        json.dump(manifest, fh, indent=2, ensure_ascii=False, sort_keys=True)
        fh.write("\n")


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Build manuscript supplementary table index with hashes and table shapes.")
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    args = parser.parse_args(argv)
    root = repo_root()
    config = load_config(root / args.config)
    records: list[dict[str, Any]] = []
    for table in config["tables"]:
        for rel_path in table["paths"]:
            records.append(file_record(root, table, rel_path))
    write_outputs(root, config, records)


if __name__ == "__main__":
    main()
