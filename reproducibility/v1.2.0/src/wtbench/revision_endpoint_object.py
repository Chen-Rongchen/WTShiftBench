"""M2: Materialize the sampling-aware endpoint object."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats


PROJECT_ROOT = Path(__file__).resolve().parents[2]
CATEGORY_ORDER = [
    "endpoint_anchor",
    "shift_excess",
    "dependency_excess",
    "low_information",
    "middle",
]


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def percentile_rank(values: pd.Series) -> pd.Series:
    return values.astype(float).rank(method="average", pct=True)


def assign_band(rank: float, *, low: float, high: float) -> str:
    if not np.isfinite(rank):
        return "insufficient"
    if rank >= high:
        return "high"
    if rank <= low:
        return "low"
    return "middle"


def assign_category(shift_band: str, dependency_band: str) -> str:
    if "insufficient" in {shift_band, dependency_band}:
        return "insufficient"
    if shift_band == "high" and dependency_band == "high":
        return "endpoint_anchor"
    if shift_band == "high" and dependency_band == "low":
        return "shift_excess"
    if shift_band == "low" and dependency_band == "high":
        return "dependency_excess"
    if shift_band == "low" and dependency_band == "low":
        return "low_information"
    return "middle"


def categorize_statistic(
    frame: pd.DataFrame,
    *,
    shift_column: str,
    prefix: str,
    low: float,
    high: float,
) -> pd.DataFrame:
    pieces: list[pd.DataFrame] = []
    for _, context in frame.groupby("cell_line", sort=True):
        context = context.copy()
        context[f"{prefix}_shift_percentile"] = percentile_rank(context[shift_column])
        context[f"{prefix}_dependency_percentile"] = percentile_rank(
            context["depmap_gene_dependency"]
        )
        context[f"{prefix}_shift_band"] = context[f"{prefix}_shift_percentile"].map(
            lambda value: assign_band(float(value), low=low, high=high)
        )
        context[f"{prefix}_dependency_band"] = context[
            f"{prefix}_dependency_percentile"
        ].map(lambda value: assign_band(float(value), low=low, high=high))
        context[f"{prefix}_category"] = [
            assign_category(shift_band, dependency_band)
            for shift_band, dependency_band in zip(
                context[f"{prefix}_shift_band"],
                context[f"{prefix}_dependency_band"],
            )
        ]
        pieces.append(context)
    return pd.concat(pieces, ignore_index=True)


def candidate_summary(
    frame: pd.DataFrame,
    inference: pd.DataFrame,
    candidate_columns: dict[str, str],
) -> pd.DataFrame:
    inference_ids = {
        "raw_descriptive_reference": "raw_observed_shift",
        "noise_corrected_primary": "noise_corrected_shift",
        "expected_equal_n_depth_20_sensitivity": "equal_n_expected_shift_depth_20",
    }
    rows: list[dict[str, Any]] = []
    for cell_line, context in frame.groupby("cell_line", sort=True):
        for label, column in candidate_columns.items():
            values = context[column].astype(float)
            dependency = context["depmap_gene_dependency"].astype(float)
            source = inference.loc[
                inference["cell_line"].eq(cell_line)
                & inference["analysis_id"].eq(inference_ids[label])
            ]
            if len(source) != 1:
                raise ValueError(f"{cell_line}/{label} does not have exactly one M1 inference row.")
            source_row = source.iloc[0]
            rows.append(
                {
                    "cell_line": cell_line,
                    "candidate": label,
                    "column": column,
                    "n_targets": len(context),
                    "rho_with_dependency": stats.spearmanr(values, dependency).statistic,
                    "bootstrap_ci_low": source_row["bootstrap_ci_low"],
                    "bootstrap_ci_high": source_row["bootstrap_ci_high"],
                    "permutation_qvalue": source_row[
                        "permutation_qvalue_bh_within_analysis"
                    ],
                    "rho_with_raw_shift": stats.spearmanr(
                        values, context["observed_shift_mean_abs"]
                    ).statistic,
                    "negative_value_count": int(values.lt(0).sum()),
                    "median_value": values.median(),
                    "q25_value": values.quantile(0.25),
                    "q75_value": values.quantile(0.75),
                }
            )
    return pd.DataFrame(rows)


def category_summary(frame: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for cell_line, context in frame.groupby("cell_line", sort=True):
        for category in CATEGORY_ORDER:
            subset = context.loc[context["endpoint_category"].eq(category)]
            rows.append(
                {
                    "cell_line": cell_line,
                    "context_role": context["context_role"].iloc[0],
                    "endpoint_category": category,
                    "n_targets": len(subset),
                    "fraction_targets": len(subset) / len(context),
                    "targets": ",".join(sorted(subset["target_gene"])),
                }
            )
    return pd.DataFrame(rows)


def build_figure(frame: pd.DataFrame, output_path: Path) -> None:
    preferred = ["HCC38", "HCC1143"]
    contexts = [name for name in preferred if name in set(frame["cell_line"])]
    contexts.extend(
        name for name in frame["cell_line"].drop_duplicates() if name not in contexts
    )
    colors = {
        "endpoint_anchor": "#AA3377",
        "shift_excess": "#EE7733",
        "dependency_excess": "#009988",
        "low_information": "#4477AA",
        "middle": "#BBBBBB",
    }
    fig, axes = plt.subplots(len(contexts), 2, figsize=(10.5, 4.2 * len(contexts)), squeeze=False)
    for row_index, cell_line in enumerate(contexts):
        context = frame.loc[frame["cell_line"].eq(cell_line)]
        for column_index, (column, title) in enumerate(
            [
                ("observed_shift_mean_abs", "Raw descriptive reference"),
                ("primary_shift_value", "Sampling-aware primary"),
            ]
        ):
            axis = axes[row_index, column_index]
            for category in CATEGORY_ORDER:
                subset = context.loc[context["endpoint_category"].eq(category)]
                axis.scatter(
                    subset[column],
                    subset["depmap_gene_dependency"],
                    label=category,
                    color=colors[category],
                    s=30,
                    alpha=0.85,
                )
            rho = stats.spearmanr(context[column], context["depmap_gene_dependency"]).statistic
            axis.set_title(f"{cell_line}: {title}; ρ={rho:.3f}")
            axis.set_xlabel(column)
            axis.set_ylabel("Dependency probability")
            axis.spines[["top", "right"]].set_visible(False)
            if row_index == 0 and column_index == 1:
                axis.legend(frameon=False, fontsize=8, bbox_to_anchor=(1.02, 1.0), loc="upper left")
    fig.tight_layout()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=220, bbox_inches="tight")
    fig.savefig(output_path.with_suffix(".svg"), bbox_inches="tight")
    plt.close(fig)


def run(config_path: Path, output_root: Path) -> dict[str, Any]:
    config = json.loads(config_path.read_text(encoding="utf-8"))
    inputs = config["inputs"]
    target_path = PROJECT_ROOT / inputs["m1_target_table"]
    inference_path = PROJECT_ROOT / inputs["m1_inference"]
    targets = pd.read_csv(target_path, sep="\t")
    inference = pd.read_csv(inference_path, sep="\t")
    categories = config["categories"]
    candidate_columns = {
        "raw_descriptive_reference": "observed_shift_mean_abs",
        "noise_corrected_primary": config["primary_shift"]["column"],
        "expected_equal_n_depth_20_sensitivity": "equal_n_primary_shift",
    }
    summary = candidate_summary(targets, inference, candidate_columns)

    working = categorize_statistic(
        targets,
        shift_column="observed_shift_mean_abs",
        prefix="raw",
        low=float(categories["low_quantile"]),
        high=float(categories["high_quantile"]),
    )
    working = categorize_statistic(
        working,
        shift_column=config["primary_shift"]["column"],
        prefix="corrected",
        low=float(categories["low_quantile"]),
        high=float(categories["high_quantile"]),
    )
    working["context_role"] = working["cell_line"].map(config["context_roles"])
    working["primary_shift_value"] = working[config["primary_shift"]["column"]]
    working["endpoint_category"] = working["corrected_category"]
    working["category_changed_from_raw"] = working["raw_category"].ne(
        working["corrected_category"]
    )

    old_grid_path = PROJECT_ROOT / "reports/truth_bridge_decomposition/target_level_joint_grid.tsv"
    old_grid = pd.read_csv(old_grid_path, sep="\t")
    old_grid = old_grid[["cell_line", "target_gene", "joint_grid"]].copy()
    old_grid["expected_raw_category"] = old_grid["joint_grid"].replace(
        {
            "Q1_anchor": "endpoint_anchor",
            "Q2_transcriptomic_excess": "shift_excess",
            "Q3_dependency_excess": "dependency_excess",
            "Q4_low_information": "low_information",
        }
    )
    validation = working[["cell_line", "target_gene", "raw_category"]].merge(
        old_grid[["cell_line", "target_gene", "expected_raw_category"]],
        on=["cell_line", "target_gene"],
        how="left",
        validate="one_to_one",
    )
    validation["matches_existing_raw_grid"] = validation["raw_category"].eq(
        validation["expected_raw_category"]
    )
    if not validation["matches_existing_raw_grid"].all():
        raise ValueError("Recomputed raw 25/75 categories differ from the existing bridge decomposition.")

    category_counts = category_summary(working)
    transition_detail = working[[
        "cell_line",
        "context_role",
        "target_gene",
        "raw_category",
        "corrected_category",
        "category_changed_from_raw",
        "observed_shift_mean_abs",
        "noise_corrected_shift",
        "equal_n_primary_shift",
        "depmap_gene_dependency",
    ]].sort_values(["cell_line", "target_gene"])
    transition_summary = (
        transition_detail.groupby(
            ["cell_line", "context_role", "raw_category", "corrected_category"],
            as_index=False,
        )
        .size()
        .rename(columns={"size": "n_targets"})
    )
    shared = (
        working.loc[working["endpoint_category"].eq("endpoint_anchor")]
        .groupby("target_gene", as_index=False)
        .agg(n_contexts=("cell_line", "nunique"), contexts=("cell_line", lambda x: ",".join(sorted(x))))
    )

    output_root.mkdir(parents=True, exist_ok=True)
    object_columns = [
        "cell_line",
        "context_role",
        "target_gene",
        "n_cells_target",
        "observed_shift_mean_abs",
        "matched_null_shift_mean",
        "noise_corrected_shift",
        "equal_n_primary_shift",
        "depmap_gene_dependency",
        "corrected_shift_percentile",
        "corrected_dependency_percentile",
        "corrected_shift_band",
        "corrected_dependency_band",
        "endpoint_category",
        "raw_category",
        "category_changed_from_raw",
    ]
    working[object_columns].sort_values(["cell_line", "target_gene"]).to_csv(
        output_root / "sampling_aware_endpoint_object.tsv",
        sep="\t",
        index=False,
    )
    summary.to_csv(output_root / "endpoint_statistic_candidate_summary.tsv", sep="\t", index=False)
    category_counts.to_csv(output_root / "endpoint_category_summary.tsv", sep="\t", index=False)
    transition_detail.to_csv(output_root / "endpoint_category_transition_detail.tsv", sep="\t", index=False)
    transition_summary.to_csv(output_root / "endpoint_category_transition_summary.tsv", sep="\t", index=False)
    shared.to_csv(output_root / "shared_corrected_anchors.tsv", sep="\t", index=False)
    validation.to_csv(output_root / "raw_category_recalculation_validation.tsv", sep="\t", index=False)
    build_figure(working, output_root / "sampling_aware_endpoint_object.png")

    lines = [
        "# M2: Sampling-aware endpoint object",
        "",
        "- Primary shift statistic: matched-size noise-corrected shift, without truncating negative values.",
        "- Raw mean-absolute shift：descriptive reference。",
        "- Expected equal-n shift at 20 cells：sampling-depth sensitivity。",
        "- HCC1143：qualified primary context；HCC38：sensitivity/boundary context。",
        "- This object was frozen before any revised model scoring.",
        "",
        "## Statistic summary",
        "",
        "| context | candidate | n | rho dependency | 95% CI | rho raw | negatives |",
        "| --- | --- | ---: | ---: | --- | ---: | ---: |",
    ]
    for _, row in summary.sort_values(["cell_line", "candidate"]).iterrows():
        lines.append(
            f"| {row['cell_line']} | {row['candidate']} | {int(row['n_targets'])} | "
            f"{row['rho_with_dependency']:.3f} | [{row['bootstrap_ci_low']:.3f}, {row['bootstrap_ci_high']:.3f}] | "
            f"{row['rho_with_raw_shift']:.3f} | {int(row['negative_value_count'])} |"
        )
    lines.extend(
        [
            "",
            "## Corrected category composition",
            "",
            "| context | role | category | n | targets |",
            "| --- | --- | --- | ---: | --- |",
        ]
    )
    for _, row in category_counts.iterrows():
        lines.append(
            f"| {row['cell_line']} | {row['context_role']} | {row['endpoint_category']} | "
            f"{int(row['n_targets'])} | {row['targets']} |"
        )
    changed = transition_detail.groupby("cell_line")["category_changed_from_raw"].agg(["sum", "count"])
    lines.extend(["", "## Category stability", ""])
    for cell_line, row in changed.iterrows():
        lines.append(
            f"- {cell_line}：{int(row['sum'])}/{int(row['count'])} targets changed category from the raw object。"
        )
    lines.extend(
        [
            "",
            "## Interpretation boundary",
            "",
            "The object corrects the expected finite-sampling shift floor under the matched-control null; it does not claim to remove all technical or biological confounding. HCC38 is sensitivity-only and must not be used to retune categories, cutoffs, or metrics.",
            "",
        ]
    )
    report_path = output_root / "m2_endpoint_object_report.md"
    report_path.write_text("\n".join(lines), encoding="utf-8")

    input_paths = [
        config_path,
        PROJECT_ROOT / config["amendment"],
        target_path,
        inference_path,
        PROJECT_ROOT / inputs["m1_final_manifest"],
        old_grid_path,
    ]
    output_paths = sorted(
        path for path in output_root.iterdir() if path.is_file() and path.name != "run_manifest.json"
    )
    manifest = {
        "object_id": config["object_id"],
        "status": config["status"],
        "model_scores_inspected": False,
        "inputs": [
            {"path": str(path.relative_to(PROJECT_ROOT)), "sha256": sha256_file(path)}
            for path in input_paths
        ],
        "outputs": [
            {"path": str(path.relative_to(PROJECT_ROOT)), "sha256": sha256_file(path)}
            for path in output_paths
        ],
    }
    (output_root / "run_manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return manifest
