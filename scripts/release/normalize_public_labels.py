"""Normalize internal analysis labels in publication-facing TSV files."""

from __future__ import annotations

import argparse
from pathlib import Path


LABEL_REPLACEMENTS = (
    ("Q1_anchor_vs_middle", "endpoint_anchor_vs_middle"),
    ("Q1_anchor", "endpoint_anchor"),
    ("Q2_transcriptomic_excess", "shift_excess"),
    ("Q2_shift_excess", "shift_excess"),
    ("Q3_dependency_excess", "dependency_excess"),
    ("Q4_low_information", "low_information"),
)


def normalize_file(path: Path) -> bool:
    original = path.read_text(encoding="utf-8")
    normalized = original
    for internal_label, public_label in LABEL_REPLACEMENTS:
        normalized = normalized.replace(internal_label, public_label)
    if normalized == original:
        return False
    path.write_text(normalized, encoding="utf-8")
    return True


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "paths",
        nargs="+",
        type=Path,
        help="Publication-facing TSV files or directories to normalize.",
    )
    args = parser.parse_args()

    files: set[Path] = set()
    for path in args.paths:
        if path.is_dir():
            files.update(path.rglob("*.tsv"))
        elif path.suffix == ".tsv" and path.exists():
            files.add(path)

    changed = sum(normalize_file(path) for path in sorted(files))
    print(f"Normalized publication labels in {changed} TSV file(s).")


if __name__ == "__main__":
    main()
