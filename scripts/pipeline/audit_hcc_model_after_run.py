from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from wtbench.model_endpoint_recovery import CELL_LINES, DEFAULT_PREDICTION_ROOT, run_endpoint_recovery_audit


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUTPUT_BASE = PROJECT_ROOT / "reports/model_endpoint_recovery/by_model"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Audit one HCC model immediately after both cell-line predictions are exported.",
    )
    parser.add_argument("--model-id", required=True)
    parser.add_argument("--prediction-root", default=str(DEFAULT_PREDICTION_ROOT))
    parser.add_argument("--output-base", default=str(DEFAULT_OUTPUT_BASE))
    parser.add_argument("--n-permutations", type=int, default=1000)
    parser.add_argument("--seed", type=int, default=1)
    return parser


def check_inputs(model_id: str, prediction_root: Path) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for cell_line in CELL_LINES:
        path = prediction_root / model_id / cell_line / "predicted_shift.tsv.gz"
        rows.append(
            {
                "model_id": model_id,
                "cell_line": cell_line,
                "prediction_path": str(path),
                "prediction_exists": path.exists(),
            }
        )
    return rows


def classify_row(row: pd.Series) -> str:
    total = row.get("total_shift_depmap_spearman")
    axis = row.get("axis_aligned_depmap_spearman")
    homogenization = row.get("predicted_target_similarity_mean")
    axis_auc = row.get("anchor_vs_low_information_axis_auc")

    total_ok = pd.notna(total) and float(total) > 0.2
    axis_ok = pd.notna(axis) and float(axis) > 0.2
    auc_ok = pd.notna(axis_auc) and float(axis_auc) > 0.6
    homogenization_high = pd.notna(homogenization) and float(homogenization) > 0.75

    if total_ok and axis_ok and auc_ok and not homogenization_high:
        return "endpoint_relevant_structure_supported"
    if total_ok and not axis_ok and homogenization_high:
        return "output_homogenization_warning"
    if not total_ok and not axis_ok:
        return "weak_or_shrunken_endpoint_recovery"
    if axis_ok and not total_ok:
        return "axis_signal_without_depmap_endpoint_alignment"
    return "mixed_requires_manual_review"


def write_interpretation(model_summary_path: Path, output_path: Path) -> None:
    summary = pd.read_csv(model_summary_path, sep="\t")
    if summary.empty:
        pd.DataFrame().to_csv(output_path, sep="\t", index=False)
        return
    rows = []
    for row in summary.itertuples(index=False):
        payload = row._asdict()
        payload["interpretation_call"] = classify_row(pd.Series(payload))
        payload["interpretation_caveat"] = (
            "Heuristic call for execution triage only; manuscript claims should cite the underlying "
            "total-shift, response-aligned, category-separation, target-identity, and "
            "output-homogenization metrics."
        )
        rows.append(payload)
    pd.DataFrame(rows).to_csv(output_path, sep="\t", index=False)


def main() -> None:
    args = build_parser().parse_args()
    prediction_root = Path(args.prediction_root)
    output_root = Path(args.output_base) / args.model_id
    output_root.mkdir(parents=True, exist_ok=True)

    readiness = check_inputs(args.model_id, prediction_root)
    readiness_path = output_root / "input_readiness.tsv"
    pd.DataFrame(readiness).to_csv(readiness_path, sep="\t", index=False)
    missing = [row for row in readiness if not row["prediction_exists"]]
    if missing:
        raise FileNotFoundError(
            "Missing scorer-ready predictions: "
            + ", ".join(f"{row['cell_line']}={row['prediction_path']}" for row in missing)
        )

    paths = run_endpoint_recovery_audit(
        model_ids=[args.model_id],
        prediction_root=prediction_root,
        output_root=output_root,
        n_permutations=args.n_permutations,
        seed=args.seed,
    )
    interpretation_path = output_root / "interpretation_summary.tsv"
    write_interpretation(paths["model_summary"], interpretation_path)
    result = {key: str(value) for key, value in paths.items()}
    result["input_readiness"] = str(readiness_path)
    result["interpretation_summary"] = str(interpretation_path)
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
