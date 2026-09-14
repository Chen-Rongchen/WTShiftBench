"""Compare external raw and cell-count-adjusted shift-dependency associations using frozen tables."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from wtbench.revision_bridge_sensitivity import (
    bh_adjust,
    infer_association,
    partial_spearman_statistic,
    sha256_file,
    spearman_statistic,
)


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "docs/revision_external_cell_count"
M1 = "reports/revision/m1_bridge_confounding"
BOOTSTRAPS = 5000
PERMUTATIONS = 10000
BOOTSTRAP_SEED = 2026090511
PERMUTATION_SEED = 2026090512
SOURCES = [
    ("Replogle K562 essential day 6", "reports/revision/m5_candidate_qualification/selected_context_endpoint_object.tsv.gz", "M5 frozen1882-target object; upstream minimum20 cells"),
    ("HepG2 day 7", "reports/gse264667_endpoint_extension/gse264667_hepg2_day7/target_level_bridge_table.tsv.gz", "Upstream minimum50 cells; previously filtered targets are not restored"),
    ("Jurkat day 7", "reports/gse264667_endpoint_extension/gse264667_jurkat_day7/target_level_bridge_table.tsv.gz", "Upstream minimum50 cells; previously filtered targets are not restored"),
    ("Replogle K562 genome-wide day 8", "data/processed/truth_driven_bridge_replogle_k562_gwps_day8/K562_GWPS_day8/target_level_bridge_table.tsv.gz", "Retain target eligibility from the existing genome-wide table"),
    ("K562 TF day 7", "data/processed/truth_driven_bridge_gse90063_7d/dixit_2016_k562_tf_7d_gse90063/target_level_bridge_table.tsv.gz", "Retain the existing10-target temporal panel"),
    ("K562 TF day 13", "data/processed/truth_driven_bridge_gse90063_13d/dixit_2016_k562_tf_13d_gse90063/target_level_bridge_table.tsv.gz", "Retain the existing10-target temporal panel"),
]


def infer(frame: pd.DataFrame, context: str, outcome: str, adjusted: bool) -> dict:
    result = infer_association(
        analysis_id=outcome + ("_partial_log_n" if adjusted else "_unadjusted"),
        cell_line=context,
        x=frame[outcome].to_numpy(float),
        y=frame.depmap_gene_dependency.to_numpy(float),
        covariates=np.log(frame.n_cells_target.to_numpy(float)) if adjusted else None,
        bootstrap_replicates=BOOTSTRAPS,
        permutation_replicates=PERMUTATIONS,
        bootstrap_seed=BOOTSTRAP_SEED,
        permutation_seed=PERMUTATION_SEED,
    )
    result.update(context=context, outcome=outcome, adjusted=adjusted,
                  evidence_role="Exploratory supplement in this execution", reused_m1=False)
    print(f"Completed {context} / {result['analysis_id']}: rho={result['spearman_rho']:.6f}", flush=True)
    return result


def input_record(path: str) -> dict:
    source = ROOT / path
    return dict(path=path, size_bytes=source.stat().st_size, sha256=sha256_file(source))


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    inputs = list(dict.fromkeys([
        *(s[1] for s in SOURCES), f"{M1}/target_level_covariates_and_corrected_shift.tsv",
        f"{M1}/bridge_inference_summary.tsv", "src/wtbench/revision_bridge_sensitivity.py",
        "scripts/revision/test_external_cell_count.py", "pixi.toml", "pixi.lock",
    ]))
    manifest = dict(
        status="Running", started_utc=datetime.now(timezone.utc).isoformat(),
        purpose="User question: do other datasets also show partial correlations near HCC38's0.04?",
        interpretation="Incremental ordering conditional on cell count; no causal identification or changes to qualification/context selection",
        primary="Spearman(raw shift, dependency) and partial Spearman controlling log cell count",
        secondary="Corrected partial correlations only for HCC38, HCC1143, and Replogle essential with existing corrected shifts",
        scope=SOURCES, bootstraps=BOOTSTRAPS, permutations=PERMUTATIONS,
        bootstrap_seed=BOOTSTRAP_SEED, permutation_seed=PERMUTATION_SEED,
        inference="Reuse M1; rerank in target bootstrap; use two-sided rank-scale Freedman-Lane residual permutation for partial correlations",
        multiple_testing="Separate BH families for six external raw tests and six external raw partial tests; three corrected partial tests form another family; HCC references retain M1 inference",
        inputs=[input_record(p) for p in inputs],
    )
    manifest_path = OUT / "run_manifest.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    frames = {}
    cohort_rows = []
    hcc = pd.read_csv(ROOT / M1 / "target_level_covariates_and_corrected_shift.tsv", sep="\t")
    for context in ["HCC38", "HCC1143"]:
        frames[context] = hcc.loc[hcc.cell_line.eq(context)].rename(columns={"observed_shift_mean_abs": "raw_shift"}).copy()
    for context, path, note in SOURCES:
        source = pd.read_csv(ROOT / path, sep="\t")
        columns = ["n_cells_target", "real_shift_mean_abs", "depmap_gene_dependency"]
        eligible = np.isfinite(source[columns].to_numpy(float)).all(axis=1)
        frame = source.loc[eligible].rename(columns={"real_shift_mean_abs": "raw_shift"}).copy()
        # Historical external tables include missing DepMap targets; use identical complete cases for all correlations.
        assert frame.n_cells_target.gt(0).all()
        assert not frame.target_gene.duplicated().any()
        frames[context] = frame
        cohort_rows.append(dict(context=context, input_targets=len(source), analyzed_targets=len(frame),
                                excluded_nonfinite=int((~eligible).sum()),
                                minimum_observed_count=int(frame.n_cells_target.min()),
                                median_count=float(frame.n_cells_target.median()),
                                response_gene_count=int(frame.gene_universe_size.iloc[0]),
                                source=path, eligibility_note=note))

    associations = []
    frozen = pd.read_csv(ROOT / M1 / "bridge_inference_summary.tsv", sep="\t")
    for context in ["HCC38", "HCC1143"]:
        for old_id, outcome, adjusted in [("raw_observed_shift", "raw_shift", False),
                                          ("partial_model_a_log_n", "raw_shift", True),
                                          ("noise_corrected_shift", "noise_corrected_shift", False)]:
            row = frozen.loc[frozen.cell_line.eq(context) & frozen.analysis_id.eq(old_id)].iloc[0].to_dict()
            row.update(context=context, outcome=outcome, adjusted=adjusted,
                       evidence_role="M1 frozen reference", reused_m1=True)
            associations.append(row)

    checks = []
    for context, frame in frames.items():
        x = frame.raw_shift.to_numpy(float)
        y = frame.depmap_gene_dependency.to_numpy(float)
        n = frame.n_cells_target.to_numpy(float)
        rxy = spearman_statistic(x, y)
        rxn = spearman_statistic(x, n)
        ryn = spearman_statistic(y, n)
        partial = partial_spearman_statistic(x, y, np.log(n))
        algebra = (rxy - rxn * ryn) / np.sqrt((1 - rxn**2) * (1 - ryn**2))
        np.testing.assert_allclose(partial, algebra, atol=1e-12)
        if context in ["HCC38", "HCC1143"]:
            old = frozen.loc[frozen.cell_line.eq(context) & frozen.analysis_id.eq("partial_model_a_log_n")].iloc[0]
            np.testing.assert_allclose(partial, old.spearman_rho, atol=1e-12)
        checks.append(dict(context=context, n_targets=len(frame), raw_rho=rxy,
                           count_shift_rho=rxn, count_dependency_rho=ryn,
                           raw_partial_rho=partial, algebra_partial_rho=algebra,
                           algebra_absolute_error=abs(partial - algebra)))
        if context not in ["HCC38", "HCC1143"]:
            associations.append(infer(frame, context, "raw_shift", False))
            associations.append(infer(frame, context, "raw_shift", True))
        if "noise_corrected_shift" in frame:
            if context not in ["HCC38", "HCC1143"]:
                associations.append(infer(frame, context, "noise_corrected_shift", False))
            associations.append(infer(frame, context, "noise_corrected_shift", True))

    results = pd.DataFrame(associations)
    results["q_bh_this_test"] = np.nan
    for outcome, adjusted in [("raw_shift", False), ("raw_shift", True), ("noise_corrected_shift", True)]:
        family = results.outcome.eq(outcome) & results.adjusted.eq(adjusted) & ~results.reused_m1
        results.loc[family, "q_bh_this_test"] = bh_adjust(results.loc[family, "permutation_pvalue_two_sided"])
    results.to_csv(OUT / "association_inference.tsv", sep="\t", index=False, na_rep="NA")
    pd.DataFrame(cohort_rows).to_csv(OUT / "cohort_sources.tsv", sep="\t", index=False)
    summary = pd.DataFrame(checks)
    summary.to_csv(OUT / "count_shift_dependency_summary.tsv", sep="\t", index=False)
    plotted = results.loc[results.outcome.eq("raw_shift")]
    plt.rcParams.update({"font.family": "Noto Sans CJK JP", "axes.unicode_minus": False})
    fig, ax = plt.subplots(figsize=(12, 6.6))
    contexts = list(frames)
    for adjusted, offset, color, label in [(False, -0.12, "#167d9a", "Raw correlation"), (True, 0.12, "#d67732", "Cell-count-adjusted partial correlation")]:
        sub = plotted.loc[plotted.adjusted.eq(adjusted)].set_index("context").loc[contexts]
        value = sub.spearman_rho.to_numpy(float)
        err = np.vstack([value - sub.bootstrap_ci_low, sub.bootstrap_ci_high - value])
        ax.errorbar(value, np.arange(len(contexts)) + offset, xerr=err, fmt="o", color=color, label=label, capsize=3)
    ax.set_yticks(np.arange(len(contexts)), [f"{c}  (targets={len(frames[c]):,})" for c in contexts])
    ax.invert_yaxis()
    ax.axvline(0, color="#777777", linewidth=0.8)
    ax.set_xlim(-1, 1)
    ax.set_xlabel("Spearman correlation and target-bootstrap95% CI")
    ax.set_title("Raw-shift association conditional on target cell count across contexts")
    ax.legend(loc="upper left")
    ax.grid(axis="x", alpha=0.2)
    fig.tight_layout()
    fig.savefig(OUT / "raw_vs_partial.png", dpi=180)
    plt.close(fig)

    lines = ["# Target-cell-count partial correlations in external datasets", "",
             "This user-requested exploratory supplement does not change frozen M1-M6 objects, models, or Gates.", "",
             "## Questions and definitions", "",
             "Compare raw mean-absolute shift with DepMap dependency probability, and partial Spearman conditional on log target cell count. The latter measures conditional ordering, not a causal cell-depletion pathway.", "",
             "HCC38/HCC1143 raw, partial, and noise-corrected correlations/CI/P reuse M1; external datasets use the same implementation. Raw and partial associations use exactly the same targets within each context.", "",
             "Each new test uses5000 target bootstraps and10000 two-sided permutations; partial tests use rank-scale Freedman-Lane. Apply BH separately to six external raw and six external raw partial tests.", "",
             "## Raw associations, cell counts, and partial correlations", "",
             "| Context | Targets | Raw rho | Count-shift rho | Count-dependency rho | Partial rho [95% CI] | Partial P | Current-family BH q |",
             "| --- | ---: | ---: | ---: | ---: | --- | ---: | ---: |"]
    for row in checks:
        s = plotted.loc[plotted.context.eq(row["context"]) & plotted.adjusted].iloc[0]
        q = f"{s.q_bh_this_test:.4g}" if np.isfinite(s.q_bh_this_test) else "M1 reference"
        lines.append(f"| {row['context']} | {row['n_targets']} | {row['raw_rho']:.3f} | {row['count_shift_rho']:.3f} | {row['count_dependency_rho']:.3f} | {s.spearman_rho:.3f} [{s.bootstrap_ci_low:.3f}, {s.bootstrap_ci_high:.3f}] | {s.permutation_pvalue_two_sided:.4g} | {q} |")
    lines += ["", "![Raw and conditional correlation comparison](raw_vs_partial.png)", "", "## Existing sampling-corrected shift supplement", "",
              "This statistic differs from raw partial correlation above. Include only three contexts with existing corrected shifts; do not estimate new noise floors for other datasets here.", "",
              "| Context | Corrected rho | Corrected partial rho [95% CI] | Partial P | BH q (three tests) |",
              "| --- | ---: | --- | ---: | ---: |"]
    for context in ["HCC38", "HCC1143", SOURCES[0][0]]:
        sub = results.loc[results.context.eq(context) & results.outcome.eq("noise_corrected_shift")]
        raw = sub.loc[~sub.adjusted].iloc[0]
        part = sub.loc[sub.adjusted].iloc[0]
        lines.append(f"| {context} | {raw.spearman_rho:.3f} | {part.spearman_rho:.3f} [{part.bootstrap_ci_low:.3f}, {part.bootstrap_ci_high:.3f}] | {part.permutation_pvalue_two_sided:.4g} | {part.q_bh_this_test:.4g} |")
    lines += ["", "## Scope", "",
              "- HepG2/Jurkat were prefiltered at50 cells, so results describe retained cohorts only; see cohort_sources.tsv.",
              "- Each K562 TF time point has only10 targets; time points and multiple K562 datasets are not independent biological replicates.",
              "- Gene spaces, target universes, time points, and preprocessing differ across contexts; this compares analogous phenomena, not directly ranked effect sizes.",
              "- Do not reselect favorable subsets using cell count or shift; explicitly count exclusions for missing dependency.",
              "- Equal-depth sampling and matched-control correction address measurement bias; partial correlations address incremental ordering. They are not interchangeable.",
              "- Partial correlations match the analytical three-correlation formula in all eight contexts, reproducing HCC values near0.040/0.364.", "",
              "## Reproduction", "", "```bash", "pixi run --environment core revision-test-external-count", "```", "",
              "Input tables, statistical implementation, Pixi lockfile, and output SHA256 hashes are recorded in run_manifest.json; no retraining.", ""]
    (OUT / "report.md").write_text("\n".join(lines), encoding="utf-8")
    manifest.update(status="Completed", completed_utc=datetime.now(timezone.utc).isoformat(),
                    outputs=[input_record(str(p.relative_to(ROOT))) for p in sorted(OUT.iterdir()) if p != manifest_path])
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Results saved: {OUT.relative_to(ROOT)}", flush=True)


if __name__ == "__main__":
    main()
