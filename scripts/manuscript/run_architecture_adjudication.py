from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd

from wtbench.stage2_model_structure_scorer import score_prediction_against_frozen_architecture


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def resolve_path(raw: str) -> Path:
    path = Path(raw)
    if path.is_absolute():
        return path
    return PROJECT_ROOT / path


def load_config(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def build_manifest(
    *,
    config_path: Path,
    truth_contract_path: Path,
    axis_membership_path: Path,
    prediction_records: list[dict[str, Any]],
    output_paths: dict[str, Path],
) -> dict[str, Any]:
    return {
        "stage": "manuscript_architecture_adjudication_kit",
        "version": 1,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "config_path": str(config_path.relative_to(PROJECT_ROOT)),
        "config_sha256": sha256_file(config_path),
        "truth_contract_path": str(truth_contract_path.relative_to(PROJECT_ROOT)),
        "truth_contract_sha256": sha256_file(truth_contract_path),
        "axis_membership_path": str(axis_membership_path.relative_to(PROJECT_ROOT)),
        "axis_membership_sha256": sha256_file(axis_membership_path),
        "predictions": prediction_records,
        "outputs": {
            name: {
                "path": str(path.relative_to(PROJECT_ROOT)),
                "sha256": sha256_file(path),
            }
            for name, path in output_paths.items()
        },
    }


def run(config_path: Path) -> None:
    config = load_config(config_path)
    truth_contract_path = resolve_path(config["truth_contract_path"])
    axis_membership_path = resolve_path(config["axis_membership_path"])
    output_dir = resolve_path(config["output_dir"])
    output_dir.mkdir(parents=True, exist_ok=True)

    score_rows: list[pd.DataFrame] = []
    projection_rows: list[pd.DataFrame] = []
    prediction_records: list[dict[str, Any]] = []

    for item in config["predictions"]:
        model_id = str(item["model_id"])
        context = str(item.get("context", "unspecified"))
        prediction_path = resolve_path(item["prediction_path"])
        projected, scores = score_prediction_against_frozen_architecture(
            prediction_path=prediction_path,
            truth_contract_path=truth_contract_path,
            axis_membership_path=axis_membership_path,
        )
        scores.insert(0, "context", context)
        scores.insert(0, "model_id", model_id)
        projected.insert(0, "context", context)
        projected.insert(0, "model_id", model_id)
        score_rows.append(scores)
        projection_rows.append(projected)
        prediction_records.append(
            {
                "model_id": model_id,
                "context": context,
                "prediction_path": str(prediction_path.relative_to(PROJECT_ROOT)),
                "prediction_sha256": sha256_file(prediction_path),
            }
        )

    scores_out = output_dir / "architecture_scores.tsv"
    projections_out = output_dir / "axis_projections.tsv.gz"
    score_table = pd.concat(score_rows, ignore_index=True)
    projection_table = pd.concat(projection_rows, ignore_index=True)
    score_table.to_csv(scores_out, sep="\t", index=False)
    projection_table.to_csv(projections_out, sep="\t", index=False, compression="gzip")

    manifest_out = output_dir / "architecture_adjudication_manifest.json"
    manifest = build_manifest(
        config_path=config_path,
        truth_contract_path=truth_contract_path,
        axis_membership_path=axis_membership_path,
        prediction_records=prediction_records,
        output_paths={
            "architecture_scores": scores_out,
            "axis_projections": projections_out,
        },
    )
    with manifest_out.open("w", encoding="utf-8") as handle:
        json.dump(manifest, handle, indent=2, sort_keys=True)
        handle.write("\n")

    print(f"wrote {scores_out.relative_to(PROJECT_ROOT)}")
    print(f"wrote {projections_out.relative_to(PROJECT_ROOT)}")
    print(f"wrote {manifest_out.relative_to(PROJECT_ROOT)}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run architecture-aware adjudication for one or more prediction matrices."
    )
    parser.add_argument(
        "--config",
        required=True,
        help="Path to JSON config listing truth contract, axis membership and prediction matrices.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    run(resolve_path(args.config))


if __name__ == "__main__":
    main()
