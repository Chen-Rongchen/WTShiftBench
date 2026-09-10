"""BIB major revision M6: frozen-versus-endpoint-tuned counterfactual."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from wtbench.revision_metric_validity import rank_auc, sha256_file


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def category_from_percentiles(
    shift_percentile: np.ndarray,
    dependency_percentile: np.ndarray,
    *,
    low: float,
    high: float,
) -> np.ndarray:
    shift = np.asarray(shift_percentile, dtype=float)
    dependency = np.asarray(dependency_percentile, dtype=float)
    category = np.full(len(shift), "middle", dtype=object)
    category[(shift >= high) & (dependency >= high)] = "endpoint_anchor"
    category[(shift <= low) & (dependency <= low)] = "low_information"
    category[(shift >= high) & (dependency <= low)] = "shift_excess"
    category[(shift <= low) & (dependency >= high)] = "dependency_excess"
    category[~np.isfinite(shift) | ~np.isfinite(dependency)] = "insufficient"
    return category.astype(str)


def score_cutoff_grid(
    *,
    scope: str,
    endpoint: pd.DataFrame,
    target_metrics: pd.DataFrame,
    cutoffs: list[dict[str, float]],
    minimum_anchor: int,
    minimum_low: int,
) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    endpoint = endpoint.copy()
    endpoint["target_gene"] = endpoint["target_gene"].astype(str)
    target_metrics = target_metrics.copy()
    target_metrics["target_gene"] = target_metrics["target_gene"].astype(str)
    for context, context_endpoint in endpoint.groupby("cell_line", sort=True):
        context_scores = target_metrics.loc[target_metrics["cell_line"].eq(context)]
        if context_scores.empty:
            raise ValueError(f"No formal target metrics for context {context}")
        for cutoff in cutoffs:
            low = float(cutoff["low"])
            high = float(cutoff["high"])
            categories = category_from_percentiles(
                context_endpoint["corrected_shift_percentile"].to_numpy(float),
                context_endpoint["corrected_dependency_percentile"].to_numpy(float),
                low=low,
                high=high,
            )
            category_frame = pd.DataFrame(
                {
                    "target_gene": context_endpoint["target_gene"].to_numpy(str),
                    "counterfactual_category": categories,
                }
            )
            full_anchor = int((categories == "endpoint_anchor").sum())
            full_low = int((categories == "low_information").sum())
            for (entrant_id, display_name), group in context_scores.groupby(
                ["entrant_id", "display_name"], sort=True
            ):
                scored = group[["target_gene", "predicted_shift_mean_abs"]].merge(
                    category_frame,
                    on="target_gene",
                    how="left",
                    validate="one_to_one",
                )
                subset = scored.loc[
                    scored["counterfactual_category"].isin(
                        ["endpoint_anchor", "low_information"]
                    )
                ]
                labels = subset["counterfactual_category"].eq("endpoint_anchor").to_numpy()
                anchor_n = int(labels.sum())
                low_n = int((~labels).sum())
                estimable = anchor_n >= minimum_anchor and low_n >= minimum_low
                auc = (
                    rank_auc(subset["predicted_shift_mean_abs"].to_numpy(float), labels)
                    if estimable
                    else np.nan
                )
                rows.append(
                    {
                        "scope": scope,
                        "cell_line": context,
                        "entrant_id": entrant_id,
                        "display_name": display_name,
                        "low_quantile": low,
                        "high_quantile": high,
                        "full_endpoint_anchor_n": full_anchor,
                        "full_low_information_n": full_low,
                        "scored_anchor_n": anchor_n,
                        "scored_low_information_n": low_n,
                        "anchor_auc": auc,
                        "estimable": bool(estimable),
                    }
                )
    return pd.DataFrame(rows)


def select_tuned_scores(
    grid: pd.DataFrame,
    *,
    frozen_low: float,
) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    grouping = ["scope", "cell_line", "entrant_id", "display_name"]
    for keys, group in grid.groupby(grouping, sort=True):
        group = group.loc[group["estimable"] & group["anchor_auc"].notna()].copy()
        frozen = group.loc[np.isclose(group["low_quantile"], frozen_low)]
        if len(frozen) != 1:
            raise ValueError(f"Frozen cutoff is not uniquely estimable for {keys}")
        group["distance_from_frozen"] = np.abs(group["low_quantile"] - frozen_low)
        best = group.sort_values(
            ["anchor_auc", "distance_from_frozen", "low_quantile"],
            ascending=[False, True, True],
            kind="mergesort",
        ).iloc[0]
        frozen_auc = float(frozen.iloc[0]["anchor_auc"])
        tuned_auc = float(best["anchor_auc"])
        rows.append(
            {
                **dict(zip(grouping, keys)),
                "frozen_low_quantile": frozen_low,
                "frozen_high_quantile": 1.0 - frozen_low,
                "frozen_anchor_auc": frozen_auc,
                "tuned_low_quantile": float(best["low_quantile"]),
                "tuned_high_quantile": float(best["high_quantile"]),
                "tuned_anchor_auc": tuned_auc,
                "apparent_auc_inflation": tuned_auc - frozen_auc,
                "tuned_cutoff_differs": not np.isclose(float(best["low_quantile"]), frozen_low),
            }
        )
    return pd.DataFrame(rows)


def aggregate_inflation(
    selected: pd.DataFrame,
    thresholds: list[float],
) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    grouping = [("all_contexts", selected), *selected.groupby("scope", sort=True)]
    for scope, group in grouping:
        values = group["apparent_auc_inflation"].to_numpy(float)
        row: dict[str, Any] = {
            "scope": scope,
            "n_model_contexts": len(group),
            "mean_inflation": float(values.mean()),
            "median_inflation": float(np.median(values)),
            "q25_inflation": float(np.quantile(values, 0.25)),
            "q75_inflation": float(np.quantile(values, 0.75)),
            "maximum_inflation": float(values.max()),
            "fraction_tuned_cutoff_differs": float(group["tuned_cutoff_differs"].mean()),
        }
        for threshold in thresholds:
            label = str(threshold).replace(".", "p")
            row[f"fraction_inflation_gt_{label}"] = float((values > threshold).mean())
        rows.append(row)
    return pd.DataFrame(rows)


def build_figure(selected: pd.DataFrame, output_path: Path) -> None:
    scopes = selected["scope"].drop_duplicates().tolist()
    fig, axes = plt.subplots(1, len(scopes), figsize=(6 * len(scopes), 4.5), squeeze=False)
    for index, scope in enumerate(scopes):
        axis = axes[0, index]
        group = selected.loc[selected["scope"].eq(scope)].sort_values(
            "apparent_auc_inflation"
        )
        positions = np.arange(len(group))
        axis.plot(group["frozen_anchor_auc"], positions, "o", color="#4477AA", label="Frozen 25/75")
        axis.plot(group["tuned_anchor_auc"], positions, "s", color="#CC6677", label="Post-hoc best")
        for y, (_, row) in zip(positions, group.iterrows()):
            axis.plot([row["frozen_anchor_auc"], row["tuned_anchor_auc"]], [y, y], color="#999999", linewidth=0.8)
        axis.set_yticks(positions)
        axis.set_yticklabels(
            [f"{row.display_name} | {row.cell_line}" for row in group.itertuples()],
            fontsize=7,
        )
        axis.set_xlabel("Anchor-vs-low-information AUC")
        axis.set_title(scope.replace("_", " "))
        axis.set_xlim(0.0, 1.02)
        axis.spines[["top", "right"]].set_visible(False)
        axis.legend(frameon=False, fontsize=8)
    fig.tight_layout()
    fig.savefig(output_path, dpi=220, bbox_inches="tight")
    svg_path = output_path.with_suffix(".svg")
    fig.savefig(svg_path, bbox_inches="tight")
    plt.close(fig)
    svg_text = svg_path.read_text(encoding="utf-8")
    svg_path.write_text(
        "\n".join(line.rstrip() for line in svg_text.splitlines()) + "\n",
        encoding="utf-8",
    )


def file_record(path: Path) -> dict[str, Any]:
    return {
        "path": str(path.relative_to(PROJECT_ROOT)),
        "size_bytes": path.stat().st_size,
        "sha256": sha256_file(path),
    }


def run_endpoint_tuning(config_path: Path, output_root: Path | None = None) -> dict[str, Any]:
    config = json.loads(config_path.read_text(encoding="utf-8"))
    output_root = output_root or PROJECT_ROOT / config["outputs"]["root"]
    output_root.mkdir(parents=True, exist_ok=True)
    grid_frames: list[pd.DataFrame] = []
    stored_context_frames: list[pd.DataFrame] = []
    input_paths = [config_path, PROJECT_ROOT / config["amendment"]]
    for item in config["inputs"]:
        endpoint_path = PROJECT_ROOT / item["endpoint_object"]
        target_path = PROJECT_ROOT / item["target_metrics"]
        context_path = PROJECT_ROOT / item["context_metrics"]
        endpoint = pd.read_csv(endpoint_path, sep="\t")
        target = pd.read_csv(target_path, sep="\t")
        target = target.loc[
            target[item["formal_role_column"]].eq(item["formal_role_value"])
        ].copy()
        stored = pd.read_csv(context_path, sep="\t")
        role_column = "entrant_role" if "entrant_role" in stored.columns else "entrant_kind"
        stored = stored.loc[stored[role_column].eq("formal")].copy()
        stored["scope"] = item["scope"]
        stored_context_frames.append(stored)
        grid_frames.append(
            score_cutoff_grid(
                scope=item["scope"],
                endpoint=endpoint,
                target_metrics=target,
                cutoffs=config["candidate_cutoffs"],
                minimum_anchor=int(config["validation"]["minimum_anchor_targets"]),
                minimum_low=int(config["validation"]["minimum_low_information_targets"]),
            )
        )
        input_paths.extend([endpoint_path, target_path, context_path])
    grid = pd.concat(grid_frames, ignore_index=True)
    frozen_low = float(config["frozen_cutoff"]["low"])
    selected = select_tuned_scores(grid, frozen_low=frozen_low)

    stored_context = pd.concat(stored_context_frames, ignore_index=True)
    validation = selected.merge(
        stored_context[["scope", "cell_line", "entrant_id", "anchor_separation_auc"]],
        on=["scope", "cell_line", "entrant_id"],
        how="left",
        validate="one_to_one",
    )
    validation["absolute_reproduction_error"] = np.abs(
        validation["frozen_anchor_auc"] - validation["anchor_separation_auc"]
    )
    validation["pass"] = validation["absolute_reproduction_error"].le(
        float(config["validation"]["frozen_auc_absolute_error_max"])
    )
    if not validation["pass"].all():
        raise RuntimeError("Frozen 25/75 AUC reproduction failed.")

    aggregate = aggregate_inflation(
        selected, [float(value) for value in config["summary"]["inflation_thresholds"]]
    )
    outputs = config["outputs"]
    grid_path = output_root / outputs["cutoff_grid_scores"]
    selected_path = output_root / outputs["model_context_inflation"]
    aggregate_path = output_root / outputs["aggregate_summary"]
    validation_path = output_root / outputs["validation"]
    figure_path = output_root / outputs["figure"]
    grid.to_csv(grid_path, sep="\t", index=False, na_rep="NA")
    selected.to_csv(selected_path, sep="\t", index=False, na_rep="NA")
    aggregate.to_csv(aggregate_path, sep="\t", index=False, na_rep="NA")
    validation.to_csv(validation_path, sep="\t", index=False, na_rep="NA")
    build_figure(selected, figure_path)

    primary = aggregate.set_index("scope").loc[config["summary"]["primary_scope"]]
    independent = aggregate.set_index("scope").loc[config["summary"]["independent_scope"]]
    largest = selected.sort_values("apparent_auc_inflation", ascending=False).head(5)
    report_lines = [
        "# M6 frozen-versus-endpoint-tuned counterfactual",
        "",
        "This is an intentionally invalid post-hoc analysis used only to quantify optimism from model-informed endpoint cutoff selection.",
        "",
        f"- Primary HCC model-contexts: n={int(primary['n_model_contexts'])}, median inflation={primary['median_inflation']:.3f}, mean={primary['mean_inflation']:.3f}, maximum={primary['maximum_inflation']:.3f}.",
        f"- Independent sensitivity entrants: n={int(independent['n_model_contexts'])}, median inflation={independent['median_inflation']:.3f}, mean={independent['mean_inflation']:.3f}, maximum={independent['maximum_inflation']:.3f}.",
        "- Frozen 25/75 AUC values were reproduced before tuning for every formal model-context.",
        "",
        "## Largest apparent inflations",
        "",
        "| Scope | Context | Entrant | Frozen AUC | Tuned cutoff | Tuned AUC | Inflation |",
        "| --- | --- | --- | ---: | ---: | ---: | ---: |",
    ]
    for row in largest.itertuples():
        report_lines.append(
            f"| {row.scope} | {row.cell_line} | {row.display_name} | {row.frozen_anchor_auc:.3f} | "
            f"{row.tuned_low_quantile:.2f}/{row.tuned_high_quantile:.2f} | {row.tuned_anchor_auc:.3f} | "
            f"{row.apparent_auc_inflation:.3f} |"
        )
    report_lines.extend(
        [
            "",
            "The tuned variant is not promoted, is not used to redefine endpoint categories, and is excluded from all formal model claims.",
        ]
    )
    report_path = output_root / outputs["report"]
    report_path.write_text("\n".join(report_lines) + "\n", encoding="utf-8")

    output_paths = [
        grid_path,
        selected_path,
        aggregate_path,
        validation_path,
        figure_path,
        figure_path.with_suffix(".svg"),
        report_path,
    ]
    manifest = {
        "analysis_id": config["analysis_id"],
        "n_model_contexts": len(selected),
        "frozen_reproduction_all_pass": bool(validation["pass"].all()),
        "counterfactual_only": True,
        "inputs": [file_record(path) for path in input_paths],
        "outputs": [file_record(path) for path in output_paths],
    }
    manifest_path = output_root / outputs["manifest"]
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n")
    return manifest
