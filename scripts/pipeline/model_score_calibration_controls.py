"""Build model score-calibration null controls.

This script does not train models. It reads scorer-ready prediction matrices,
computes observed architecture-aware recovery scores, and estimates null
behavior under three controls:

- target-label permutation,
- model-output shuffle,
- truth-contract role permutation.

The controls calibrate the score range and help separate recovery-object signal
from label, output-distribution, and contract-assignment artifacts.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from wtbench.model_structure_scorer import (
    load_prediction_matrix,
    load_tsv,
    project_prediction_to_axes,
    summarize_structure_scores,
)


DEFAULT_CONFIG = Path("configs/model_score_calibration_controls_v1.json")
VALID_CONTROLS = {
    "target_label_permutation",
    "model_output_shuffle",
    "truth_contract_role_permutation",
}


def repo_root() -> Path:
    return PROJECT_ROOT


def resolve_path(root: Path, value: str | Path) -> Path:
    path = Path(value)
    return path if path.is_absolute() else root / path


def read_config(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def score_frame(
    *,
    prediction: pd.DataFrame,
    truth_contract: pd.DataFrame,
    axis_membership: pd.DataFrame,
) -> pd.DataFrame:
    projected = project_prediction_to_axes(
        prediction=prediction,
        axis_membership=axis_membership,
        truth_contract=truth_contract,
    )
    return summarize_structure_scores(projected)


def with_metadata(
    scores: pd.DataFrame,
    *,
    model_id: str,
    cell_line: str,
    role: str,
    control_type: str,
    iteration: int | str,
) -> pd.DataFrame:
    frame = scores.copy()
    frame.insert(0, "iteration", iteration)
    frame.insert(0, "control_type", control_type)
    frame.insert(0, "role", role)
    frame.insert(0, "cell_line", cell_line)
    frame.insert(0, "model_id", model_id)
    return frame


def permute_target_labels(prediction: pd.DataFrame, rng: np.random.Generator) -> pd.DataFrame:
    frame = prediction.copy()
    labels = frame["target_gene"].to_numpy(copy=True)
    rng.shuffle(labels)
    frame["target_gene"] = labels
    return frame


def shuffle_model_output(prediction: pd.DataFrame, rng: np.random.Generator) -> pd.DataFrame:
    frame = prediction.copy()
    value_columns = [c for c in frame.columns if c != "target_gene"]
    values = frame[value_columns].to_numpy(dtype=float, copy=True)
    shuffled = rng.permutation(values.ravel()).reshape(values.shape)
    frame.loc[:, value_columns] = shuffled
    return frame


def permute_truth_contract_roles(truth_contract: pd.DataFrame, rng: np.random.Generator) -> pd.DataFrame:
    frame = truth_contract.copy()
    role_columns = [c for c in ("architecture_role", "confidence") if c in frame.columns]
    if not role_columns:
        raise ValueError("truth contract has no architecture_role or confidence columns to permute")
    order = np.arange(len(frame))
    rng.shuffle(order)
    for column in role_columns:
        frame[column] = frame[column].to_numpy(copy=True)[order]
    return frame


def score_controls_for_prediction(
    *,
    entry: dict,
    prediction: pd.DataFrame,
    truth_contract: pd.DataFrame,
    axis_membership: pd.DataFrame,
    controls: list[str],
    iterations: int,
    rng: np.random.Generator,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    model_id = str(entry["model_id"])
    cell_line = str(entry["cell_line"])
    role = str(entry.get("role", ""))

    observed = with_metadata(
        score_frame(
            prediction=prediction,
            truth_contract=truth_contract,
            axis_membership=axis_membership,
        ),
        model_id=model_id,
        cell_line=cell_line,
        role=role,
        control_type="observed",
        iteration="observed",
    )

    null_frames: list[pd.DataFrame] = []
    for iteration in range(iterations):
        for control in controls:
            if control == "target_label_permutation":
                control_prediction = permute_target_labels(prediction, rng)
                control_contract = truth_contract
            elif control == "model_output_shuffle":
                control_prediction = shuffle_model_output(prediction, rng)
                control_contract = truth_contract
            elif control == "truth_contract_role_permutation":
                control_prediction = prediction
                control_contract = permute_truth_contract_roles(truth_contract, rng)
            else:
                raise ValueError(f"unknown control: {control}")
            null_frames.append(
                with_metadata(
                    score_frame(
                        prediction=control_prediction,
                        truth_contract=control_contract,
                        axis_membership=axis_membership,
                    ),
                    model_id=model_id,
                    cell_line=cell_line,
                    role=role,
                    control_type=control,
                    iteration=iteration,
                )
            )
    return observed, pd.concat(null_frames, ignore_index=True)


def summarize_null_distribution(null_scores: pd.DataFrame) -> pd.DataFrame:
    group_cols = ["model_id", "cell_line", "role", "control_type", "score_name"]
    rows: list[dict[str, object]] = []
    for keys, group in null_scores.groupby(group_cols, sort=True, dropna=False):
        values = group["score_value"].astype(float).dropna().to_numpy()
        row = dict(zip(group_cols, keys))
        row["n"] = int(values.size)
        if values.size:
            row.update(
                {
                    "mean": float(values.mean()),
                    "sd": float(values.std(ddof=1)) if values.size > 1 else 0.0,
                    "q025": float(np.quantile(values, 0.025)),
                    "q500": float(np.quantile(values, 0.5)),
                    "q975": float(np.quantile(values, 0.975)),
                }
            )
        else:
            row.update({"mean": np.nan, "sd": np.nan, "q025": np.nan, "q500": np.nan, "q975": np.nan})
        rows.append(row)
    return pd.DataFrame(rows)


def run(
    config_path: Path,
    *,
    root: Path,
    iterations_override: int | None = None,
    outdir_override: Path | None = None,
) -> dict[str, object]:
    config = read_config(config_path)
    outdir = resolve_path(root, outdir_override or config.get("outdir", "reports/model_score_calibration_v1"))
    outdir.mkdir(parents=True, exist_ok=True)

    truth_contract = load_tsv(resolve_path(root, config["truth_contract_path"]))
    axis_membership = load_tsv(resolve_path(root, config["axis_membership_path"]))
    controls = list(config.get("controls", []))
    unknown_controls = sorted(set(controls) - VALID_CONTROLS)
    if unknown_controls:
        raise ValueError(f"unknown controls in config: {unknown_controls}")
    iterations = int(iterations_override if iterations_override is not None else config.get("iterations", 25))
    rng = np.random.default_rng(int(config.get("seed", 20260518)))
    skip_missing = bool(config.get("skip_missing", False))

    observed_frames: list[pd.DataFrame] = []
    null_frames: list[pd.DataFrame] = []
    skipped: list[dict[str, str]] = []
    for entry in config.get("predictions", []):
        print(
            "scoring "
            f"{entry.get('model_id', '')} "
            f"{entry.get('cell_line', '')} "
            f"with {iterations} calibration iterations",
            flush=True,
        )
        prediction_path = resolve_path(root, entry["prediction_path"])
        if not prediction_path.exists():
            if skip_missing:
                skipped.append(
                    {
                        "model_id": str(entry.get("model_id", "")),
                        "cell_line": str(entry.get("cell_line", "")),
                        "prediction_path": str(prediction_path),
                    }
                )
                continue
            raise FileNotFoundError(prediction_path)
        prediction = load_prediction_matrix(prediction_path)
        observed, null_scores = score_controls_for_prediction(
            entry=entry,
            prediction=prediction,
            truth_contract=truth_contract,
            axis_membership=axis_membership,
            controls=controls,
            iterations=iterations,
            rng=rng,
        )
        observed_frames.append(observed)
        null_frames.append(null_scores)

    observed_scores = pd.concat(observed_frames, ignore_index=True) if observed_frames else pd.DataFrame()
    null_scores = pd.concat(null_frames, ignore_index=True) if null_frames else pd.DataFrame()
    null_summary = summarize_null_distribution(null_scores) if not null_scores.empty else pd.DataFrame()

    observed_path = outdir / "observed_model_scores.tsv"
    null_distribution_path = outdir / "null_score_distribution.tsv.gz"
    null_summary_path = outdir / "null_score_summary.tsv"
    observed_scores.to_csv(observed_path, sep="\t", index=False)
    null_scores.to_csv(null_distribution_path, sep="\t", index=False, compression="gzip")
    null_summary.to_csv(null_summary_path, sep="\t", index=False)

    manifest = {
        "config": str(config_path.relative_to(root) if config_path.is_relative_to(root) else config_path),
        "outdir": str(outdir.relative_to(root) if outdir.is_relative_to(root) else outdir),
        "iterations": iterations,
        "controls": controls,
        "n_predictions_scored": len(observed_frames),
        "n_skipped": len(skipped),
        "skipped": skipped,
        "outputs": {
            "observed_scores": str(observed_path.relative_to(root) if observed_path.is_relative_to(root) else observed_path),
            "null_score_distribution": str(
                null_distribution_path.relative_to(root)
                if null_distribution_path.is_relative_to(root)
                else null_distribution_path
            ),
            "null_score_summary": str(
                null_summary_path.relative_to(root) if null_summary_path.is_relative_to(root) else null_summary_path
            ),
        },
    }
    (outdir / "model_score_calibration_manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return manifest


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Build model score-calibration null controls.")
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--iterations", type=int, default=None, help="Override the configured calibration iterations.")
    parser.add_argument("--outdir", type=Path, default=None, help="Override the configured output directory.")
    args = parser.parse_args(argv)

    root = repo_root()
    config_path = args.config if args.config.is_absolute() else root / args.config
    manifest = run(
        config_path,
        root=root,
        iterations_override=args.iterations,
        outdir_override=args.outdir,
    )
    print(json.dumps(manifest["outputs"], indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
