from __future__ import annotations

import argparse
import hashlib
from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]
CELL_LINES = ("HCC38", "HCC1143")


RAW_ROOTS = (
    "data/predictions/gears_raw",
    "data/predictions/scgpt_raw",
    "data/predictions/geneformer_raw",
    "data/predictions/lm_train_lowrank_raw",
    "data/predictions/lm_g_scgpt_ridge_raw",
    "data/predictions/lm_g_geneformer_ridge_raw",
    "data/predictions/hcc_raw",
)


def sha256_file(path: Path, chunk_size: int = 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while True:
            chunk = handle.read(chunk_size)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()


def candidate_paths(model_id: str) -> list[tuple[str, Path]]:
    paths: list[tuple[str, Path]] = []
    for cell_line in CELL_LINES:
        for root in RAW_ROOTS:
            raw = PROJECT_ROOT / root / model_id / cell_line / "predicted_shift.tsv.gz"
            paths.append((f"raw_prediction:{cell_line}:{root}", raw))
        paths.extend(
            [
                (
                    f"scorer_ready_prediction:{cell_line}",
                    PROJECT_ROOT / "data/predictions/hcc_scorer_ready" / model_id / cell_line / "predicted_shift.tsv.gz",
                ),
                (
                    f"aligned_prediction:{cell_line}",
                    PROJECT_ROOT / "data/predictions/hcc_aligned" / model_id / cell_line / "predicted_shift_aligned.tsv.gz",
                ),
                (
                    f"manifest:{cell_line}",
                    PROJECT_ROOT / "reports/hcc_prediction_contract" / model_id / cell_line / "prediction_manifest.json",
                ),
                (
                    f"validation:{cell_line}",
                    PROJECT_ROOT / "reports/hcc_prediction_validation" / model_id / cell_line / "validation_summary.json",
                ),
                (
                    f"by_model_target_summary:{cell_line}",
                    PROJECT_ROOT / "reports/model_endpoint_recovery/by_model" / model_id / "target_summary.tsv",
                ),
            ]
        )
    paths.extend(
        [
            (
                "audit_model_summary",
                PROJECT_ROOT / "reports/model_endpoint_recovery/by_model" / model_id / "model_summary.tsv",
            ),
            (
                "audit_category_summary",
                PROJECT_ROOT / "reports/model_endpoint_recovery/by_model" / model_id / "category_summary.tsv",
            ),
            (
                "audit_interpretation_summary",
                PROJECT_ROOT / "reports/model_endpoint_recovery/by_model" / model_id / "interpretation_summary.tsv",
            ),
        ]
    )
    return paths


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Write SHA256 hashes for HCC model artifacts.")
    parser.add_argument("--model-id", required=True)
    parser.add_argument(
        "--output-path",
        help="Defaults to reports/model_endpoint_recovery/by_model/<model_id>/artifact_hashes.tsv",
    )
    return parser


def main() -> None:
    args = build_parser().parse_args()
    rows = []
    seen: set[Path] = set()
    for artifact_role, path in candidate_paths(args.model_id):
        if path in seen or not path.exists() or not path.is_file():
            continue
        seen.add(path)
        rows.append(
            {
                "model_id": args.model_id,
                "artifact_role": artifact_role,
                "path": str(path.relative_to(PROJECT_ROOT)),
                "size_bytes": int(path.stat().st_size),
                "sha256": sha256_file(path),
            }
        )
    output_path = (
        Path(args.output_path)
        if args.output_path
        else PROJECT_ROOT / "reports/model_endpoint_recovery/by_model" / args.model_id / "artifact_hashes.tsv"
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_csv(output_path, sep="\t", index=False)
    print(f"artifact hashes: {output_path}")


if __name__ == "__main__":
    main()
