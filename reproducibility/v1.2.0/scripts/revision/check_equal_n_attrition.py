"""Compare excluded/retained target shifts and dependency at user-specified equal-n thresholds."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import rankdata

from wtbench.revision_bridge_sensitivity import sha256_file


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "docs/revision_equal_n_attrition"
DEPTHS = (20, 25, 50, 100)
M1 = "reports/revision/m1_bridge_confounding/target_level_covariates_and_corrected_shift.tsv"
COHORTS = "docs/revision_external_cell_count/cohort_sources.tsv"
METRICS = {
    "raw_shift": "Raw mean-absolute shift",
    "depmap_gene_dependency": "DepMap dependency probability (higher means stronger dependency)",
    "noise_corrected_shift": "Existing matched-size noise-corrected shift",
    "equal_n_20_expected_shift": "Existing target-level expected shift at equal-n=20",
}


def compare_groups(excluded: np.ndarray, retained: np.ndarray) -> dict:
    result = {"n_excluded": len(excluded), "n_retained": len(retained)}
    for name, values in [("excluded", excluded), ("retained", retained)]:
        # Some thresholds exclude no targets in the actual cohort; empty-group results are not zero.
        for stat, function in [("mean", np.mean), ("median", np.median), ("min", np.min), ("max", np.max)]:
            result[f"{name}_{stat}"] = float(function(values)) if len(values) else np.nan
    if len(excluded) and len(retained):
        ranks = rankdata(np.concatenate([excluded, retained]))
        u = ranks[:len(excluded)].sum() - len(excluded) * (len(excluded) + 1) / 2
        result.update(
            mean_difference=float(excluded.mean() - retained.mean()),
            median_difference=float(np.median(excluded) - np.median(retained)),
            rank_superiority=float(u / (len(excluded) * len(retained))),
            fraction_excluded_above_retained_median=float(np.mean(excluded > np.median(retained))),
            every_excluded_above_every_retained=bool(excluded.min() > retained.max()),
        )
    return result


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    cohorts = pd.read_csv(ROOT / COHORTS, sep="\t")
    hcc = pd.read_csv(ROOT / M1, sep="\t").rename(columns={
        "observed_shift_mean_abs": "raw_shift", "equal_n_primary_shift": "equal_n_20_expected_shift",
    })
    frames = {c: hcc.loc[hcc.cell_line.eq(c)].copy() for c in ["HCC38", "HCC1143"]}
    for row in cohorts.itertuples():
        source = pd.read_csv(ROOT / row.source, sep="\t").rename(columns={"real_shift_mean_abs": "raw_shift"})
        complete = np.isfinite(source[["n_cells_target", "raw_shift", "depmap_gene_dependency"]].to_numpy(float)).all(axis=1)
        frames[row.context] = source.loc[complete].copy()
        assert len(frames[row.context]) == row.analyzed_targets

    records, targets = [], []
    for context, frame in frames.items():
        metrics = [m for m in METRICS if m in frame]
        target = frame[["target_gene", "n_cells_target", *metrics]].copy()
        target.insert(0, "context", context)
        for depth in DEPTHS:
            excluded = frame.n_cells_target.lt(depth)
            target[f"excluded_at_n{depth}"] = excluded.to_numpy()
            for metric in metrics:
                records.append(dict(context=context, depth=depth, metric=metric,
                                    **compare_groups(frame.loc[excluded, metric].to_numpy(float),
                                                     frame.loc[~excluded, metric].to_numpy(float))))
        targets.append(target)
    comparison = pd.DataFrame(records)
    comparison.to_csv(OUT / "group_comparison.tsv", sep="\t", index=False, na_rep="NA")
    pd.concat(targets, ignore_index=True).to_csv(
        OUT / "target_membership.tsv.gz", sep="\t", index=False, na_rep="NA", compression={"method": "gzip", "mtime": 0},
    )

    def pair(row: pd.Series, stat: str) -> str:
        values = [row[f"{group}_{stat}"] for group in ["excluded", "retained"]]
        return " / ".join(f"{v:.6g}" if np.isfinite(v) else "NA" for v in values)

    lines = ["# Shift and dependency of targets excluded by equal-n thresholds", "",
             "## Findings", "",
             "- At thresholds excluding targets in HCC38/HCC1143, excluded-group raw shift and dependency means/medians exceed retained-group values; HCC38 excludes none at n=25. This is a group tendency, not complete targetwise separation.",
             "- Both Replogle datasets at n=25/50/100 and Jurkat at n=100 show the same direction; HepG2 at n=100 has higher excluded-group raw shift but slightly lower dependency. Across13 comparable context-threshold combinations, raw-shift means/medians are higher in13/13 and dependency in12/13; nested thresholds are not independent replicates.",
             "- Group differences do not persist universally after sampling correction. Replogle essential at n=50/100 has lower excluded-group corrected-shift means, slightly higher medians, and rank superiority only0.507/0.504. PRPF6, the sole HCC38 exclusion at n=50, has corrected and existing equal-n=20 shifts below retained-group means/medians.",
             "- Near-zero whole-cohort count-dependency Spearman correlation can coexist with elevated means in a low-count tail: overall monotonic association and threshold-specific group comparisons are different questions.", "",
             "## Questions and definitions", "",
             "This user-requested exploratory cohort-composition check does not alter frozen endpoints, qualification, or model scores. Thresholds are fixed at n=20/25/50/100.", "",
             "Excluded targets have recovered cell count < n, retained targets >= n. Use the previous DepMap-complete eligible cohort before comparing threshold exclusions. Weight targets equally, not by cell count.", "",
             "Raw shift is each target's mean absolute gene-expression change; table means/medians summarize across targets. Dependency is probability, with higher values indicating stronger dependency, not oppositely signed gene effect.", "",
             "This compares target composition after thresholding, without new external equal-n sampling or estimating shifts at n above excluded targets' available cell counts. Existing HCC equal-n=20 and corrected shifts are listed separately.", "",
             "## Raw shift and dependency: means", "",
             "All pairs are excluded/retained; NA indicates no excluded targets and therefore no group comparison.", "",
             "| Context | Threshold n | Targets excluded/retained | Mean raw shift | Mean dependency |",
             "| --- | ---: | ---: | --- | --- |"]
    for (context, depth), group in comparison.groupby(["context", "depth"], sort=False):
        indexed = group.set_index("metric")
        raw, dep = indexed.loc["raw_shift"], indexed.loc["depmap_gene_dependency"]
        lines.append(f"| {context} | {depth} | {int(raw.n_excluded)}/{int(raw.n_retained)} | {pair(raw, 'mean')} | {pair(dep, 'mean')} |")
    lines += ["", "## Medians and targetwise superiority", "",
              "Superiority = P(excluded target value > retained target value) +0.5*P(tie), computed by rank sum and equivalent to comparing all cross-group target pairs.0.5 means no rank advantage;1 means every excluded target strictly exceeds every retained target. This is a descriptive effect size, not a P value or causal evidence.", "",
              "| Context | n | Median raw shift excluded/retained | Median dependency excluded/retained | Raw superiority | Dependency superiority | All raw values strictly higher | All dependency values strictly higher |",
              "| --- | ---: | --- | --- | ---: | ---: | --- | --- |"]
    for (context, depth), group in comparison.groupby(["context", "depth"], sort=False):
        indexed = group.set_index("metric")
        raw, dep = indexed.loc["raw_shift"], indexed.loc["depmap_gene_dependency"]
        if raw.n_excluded == 0:
            continue
        lines.append(f"| {context} | {depth} | {pair(raw, 'median')} | {pair(dep, 'median')} | {raw.rank_superiority:.3f} | {dep.rank_superiority:.3f} | {'Yes' if raw.every_excluded_above_every_retained else 'No'} | {'Yes' if dep.every_excluded_above_every_retained else 'No'} |")
    lines += ["", "## Same-group comparisons using existing sampling-adjusted results", "",
              "Only the shift statistic changes; threshold-defined groups remain fixed. Equal-n=20 is the mean of1000 target-level shift samples from M1, not resampling at n=25/50/100.", "",
              "| Context | Threshold n | Shift statistic | Mean excluded/retained | Median excluded/retained | Superiority |",
              "| --- | ---: | --- | --- | --- | ---: |"]
    for row in comparison.loc[~comparison.metric.isin(["raw_shift", "depmap_gene_dependency"]) & comparison.n_excluded.gt(0)].itertuples():
        series = pd.Series(row._asdict())
        lines.append(f"| {row.context} | {row.depth} | {METRICS[row.metric]} | {pair(series, 'mean')} | {pair(series, 'median')} | {row.rank_superiority:.3f} |")
    lines += ["", "## Scope and interpretation limits", "",
              "- HepG2/Jurkat source tables were already filtered at50 cells; no exclusions at n=25/50 does not imply an absence of low-cell-count targets in the original experiment. n=100 compares existing targets with50-99 versus >=100 cells.",
              "- All eligible K562 TF targets at both time points exceed100 cells, preventing excluded-group comparisons at these thresholds.",
              "- Excluded sets are nested across thresholds, not independent replicates. Gene spaces and target universes differ across contexts, precluding direct cross-context comparisons of absolute shift.",
              "- Higher means/medians do not imply every excluded target exceeds every retained target; targetwise values, threshold membership, ranges, and strict-separation flags are saved in result tables.",
              "- Higher low-cell-count raw shift is also consistent with finite-sampling bias of a mean-absolute estimator and does not alone establish stronger biology. Higher dependency can be described as consistent with fitness-related reduced cell recovery, not proof of cell death or causal depletion.",
              "- This describes all existing eligible targets; no threshold is selected for a favorable result, and no additional significance filter or qualification threshold is introduced.", "",
              "## Reproduction and sources", "", "```bash", "pixi run --environment core python scripts/revision/check_equal_n_attrition.py", "```", "",
              "Reuse the six external sources in cohort_sources.tsv and frozen M1 HCC tables. run_manifest.json records full input/output SHA256 hashes; no model training or Pixi dependency changes.", ""]
    (OUT / "report.md").write_text("\n".join(lines), encoding="utf-8")
    inputs = [M1, COHORTS, *cohorts.source, "scripts/revision/check_equal_n_attrition.py", "pixi.toml", "pixi.lock"]
    manifest = dict(status="Completed", completed_utc=datetime.now(timezone.utc).isoformat(),
                    depth_thresholds=DEPTHS, comparison="count < n versus count >= n; equal target weights; descriptive comparison",
                    new_equal_n_subsampling=False, new_significance_tests=False,
                    input_sha256={p: sha256_file(ROOT / p) for p in inputs},
                    output_sha256={str(p.relative_to(ROOT)): sha256_file(p) for p in sorted(OUT.iterdir()) if p.name != "run_manifest.json"})
    (OUT / "run_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Saved: {OUT.relative_to(ROOT)}")
    print(comparison.loc[comparison.n_excluded.gt(0) & comparison.metric.isin(["raw_shift", "depmap_gene_dependency"]),
                         ["context", "depth", "metric", "n_excluded", "n_retained", "excluded_mean", "retained_mean", "excluded_median", "retained_median", "rank_superiority"]].to_string(index=False))


if __name__ == "__main__":
    main()
