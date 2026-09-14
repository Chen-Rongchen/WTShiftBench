"""Extract frozen M4/M5 values with source rows, keys, and version hashes, without rescoring."""

import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "docs/revision_model_findings"
SOURCES = [
    ("M4", "reports/revision/m4_hcc_full_audit", "formal_and_diagnostic_context_metrics.tsv",
     "reports/revision/m2_endpoint_object/sampling_aware_endpoint_object.tsv"),
    ("M5", "reports/revision/m5_independent_full_audit", "formal_and_reference_context_metrics.tsv",
     "reports/revision/m5_candidate_qualification/selected_context_endpoint_object.tsv.gz"),
]
# Preserve source field spelling; translate display labels without inventing missing uncertainty.
METRICS = [
    ("endpoint_alignment_spearman", "Dependency ordering association", "endpoint_alignment_ci_low", "endpoint_alignment_ci_high", "endpoint_alignment_label_permutation_pvalue", "endpoint_alignment_permutation_qvalue_bh"),
    ("directional_recovery_median_signed_cosine", "Target median directional recovery", "directional_recovery_ci_low", "directional_recovery_ci_high", "", ""),
    ("anchor_separation_auc", "Magnitude AUC for frozen anchors versus low-information targets", "anchor_separation_ci_low", "anchor_separation_ci_high", "", ""),
    ("target_identity_spearman", "Preservation of between-target similarity structure", "", "", "target_identity_label_permutation_pvalue", "target_identity_permutation_qvalue_bh"),
    ("predicted_homogenization_uncentered", "Mean uncentered cosine of predicted vectors", "", "", "", ""),
    ("observed_homogenization_uncentered", "Mean uncentered cosine of observed vectors", "", "", "", ""),
    ("excess_homogenization_uncentered", "Uncentered homogenization excess over observed", "", "", "", ""),
    ("excess_homogenization_centered", "Homogenization excess after target centering", "", "", "", ""),
    ("conventional_pearson_median", "Target median Pearson in the common gene space", "conventional_pearson_ci_low", "conventional_pearson_ci_high", "", ""),
    ("conventional_normalized_rmse_median", "Target median nRMSE in the common gene space", "conventional_normalized_rmse_ci_low", "conventional_normalized_rmse_ci_high", "", ""),
    ("secondary_absolute_projection_median", "Target median secondary absolute projection", "secondary_absolute_projection_ci_low", "secondary_absolute_projection_ci_high", "", ""),
]


def digest(path):
    return hashlib.sha256((ROOT / path).read_bytes()).hexdigest()


def read_rows(path):
    with (ROOT / path).open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        return [(reader.line_num, row) for row in reader]


def render_main_table(rows):
    """Format numerical tables from the same citation records without recalculating metrics or intervals."""
    contexts = {}
    for row in rows:
        # Three oracle/random-direction controls appear in the Results control section, not the formal-model table.
        if row["entrant_kind"] == "reference" and row["entrant_id"] != "shared_mean_baseline":
            continue
        contexts.setdefault(row["context"], {}).setdefault(row["entrant_id"], {})[row["metric"]] = row

    def number(value):
        return "NA" if value == "NA" else f"{float(value):.3f}"

    def estimate(row, with_q=False):
        value = number(row["value"])
        if row["ci_low"] != "NA":
            value += f" [{number(row['ci_low'])}, {number(row['ci_high'])}]"
        if with_q and row["bh_q"] != "NA":
            value += f"；q={float(row['bh_q']):.3g}"
        return value

    def design(row):
        if row["entrant_kind"] != "formal":
            return "Diagnostic reference"
        return "target LOO" if row["target_heldout"] == "True" else "not target-held-out"

    lines = ["# Model-audit main table working draft", "",
             "Final table number, page references, and layout remain pending. This table is generated from model_audit_citation_table.tsv without additional statistics. It covers21 formal model-contexts, three shared-mean references, and two zero-output references. Oracle/negated/random-direction controls appear in the associated Results section.", "",
             "Parentheses contain existing95% CIs. Endpoint is dependency ordering; direction is median signed cosine; identity is rho for between-target similarity structure; H is mean off-diagonal cosine. Delta H=H_pred-H_obs; centered Delta H removes the cross-target mean first.", "",
             "Higher endpoint, direction, and AUC values indicate stronger corresponding recovery; positive excess homogenization is elevation relative to observed, not a performance reward, and has no universal warning threshold. Identity and H have no existing CIs in this snapshot; undefined values are NA, not0.", "",
             "Endpoint/identity q values come from separate M4 18-test and M5 3-test families; these test individual outputs, not between-model differences. Shared-mean uses observed responses and is diagnostic, not a predictive baseline with the same information as LOO models.", ""]
    for context, models in contexts.items():
        meta = next(iter(next(iter(models.values())).values()))
        observed = next(iter(models.values()))["observed_homogenization_uncentered"]
        lines += [f"## {context}", "",
                  f"Role: {meta['context_role']}. Full endpoint targets={meta['full_endpoint_n_targets']}; scoring targets by genes={meta['contract_n_targets']} by {meta['contract_n_genes']}; anchors/low-information={meta['anchor_n']}/{meta['low_information_n']}. Common observed H={number(observed['value'])}.", "",
                  "| Output | Setting | Endpoint rho [95% CI]; q | Signed cosine [95% CI] | Anchor AUC [95% CI] | Identity rho; q | H_pred / Delta H / centered Delta H |",
                  "| --- | --- | --- | --- | --- | --- | --- |"]
        for metrics in models.values():
            row = metrics["endpoint_alignment_spearman"]
            h = " / ".join(number(metrics[m]["value"]) for m in ["predicted_homogenization_uncentered", "excess_homogenization_uncentered", "excess_homogenization_centered"])
            cells = [row["display_name"], design(row), estimate(row, True),
                     estimate(metrics["directional_recovery_median_signed_cosine"]), estimate(metrics["anchor_separation_auc"]),
                     estimate(metrics["target_identity_spearman"], True), h]
            lines.append("| " + " | ".join(cells) + " |")
        lines += ["", "### Corresponding common-space reconstruction", "",
                  "Higher Pearson and lower nRMSE indicate better reconstruction summaries, not whole-transcriptome or cross-context rankings.", "",
                  "| Output | Setting | Median Pearson [95% CI] | Median nRMSE [95% CI] |",
                  "| --- | --- | --- | --- |"]
        for metrics in models.values():
            row = metrics["endpoint_alignment_spearman"]
            cells = [row["display_name"], design(row), estimate(metrics["conventional_pearson_median"]), estimate(metrics["conventional_normalized_rmse_median"])]
            lines.append("| " + " | ".join(cells) + " |")
        lines.append("")
    lines += ["## Sources and full precision", "",
              "Raw P/q, CIs, object versions, training settings, source rows/keys/columns, and hashes are retained in the [citation table](model_audit_citation_table.tsv); displayed values use three decimals. HCC1143 SS18L2 is unscored only because common outputs lack coverage; full48-target categories remain unchanged.", "",
              "HCC38 scGen anchors and low-information targets are completely separated in this small sample, giving an empirical stratified-bootstrap AUC interval of[1,1]. This does not imply zero population uncertainty or guaranteed generalization. Small-sample HCC AUCs are not used for point-estimate rankings.", "",
              "HCC shared-mean uses the existing canonical-backbone observed mean; Replogle shared-mean uses the complete scored cohort's observed mean response. Zero-vector direction and identity are undefined; constant magnitude has no endpoint Spearman correlation.", ""]
    path = OUT / "model_audit_main_table.md"
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    inputs, checked, rows = {}, [], []
    for stage, folder, basename, endpoint_path in SOURCES:
        metrics_path = f"{folder}/{basename}"
        training_path = f"{folder}/model_training_evaluation_registry.tsv"
        manifest_path = f"{folder}/run_manifest.json"
        manifest = json.loads((ROOT / manifest_path).read_text())
        training = {
            (r["cell_line"] if stage == "M4" else r["context"], r["model_id"]): (line, r)
            for line, r in read_rows(training_path)
        }
        required = [metrics_path, training_path, endpoint_path, "configs/revision/revision_metric_spec_v1.json"]
        if stage == "M5":
            required.append("src/wtbench/revision_m5_audit.py")
        records = {r["path"]: r for r in manifest["inputs"] + manifest["outputs"]}
        for path in required:
            actual = digest(path)
            assert actual == records[path]["sha256"], path
            inputs[path] = actual
            checked.append(dict(stage=stage, path=path, matched_frozen_manifest=True))
        inputs[manifest_path] = digest(manifest_path)
        for line, source in read_rows(metrics_path):
            key = (source["cell_line"], source["entrant_id"])
            if stage == "M5" and source["entrant_kind"] == "reference":
                training_line = "NA"
                heldout = "Not applicable: diagnostic control constructed from observed responses"
                design = "Not an independent predictive model; shared-mean includes the full cohort's observed mean"
            else:
                training_line, record = training[key]
                heldout = record["scored_target_held_out_from_fit" if stage == "M4" else "target_heldout"]
                design = record["evaluation_design" if stage == "M4" else "training_setting"]
            for metric, label, lo, hi, p, q in METRICS:
                uncertainty = "Original results provide no CI or test; do not replace missing values with zero"
                if lo:
                    uncertainty = "95% CI from5000 target bootstraps; AUC is class-stratified; not a between-model difference CI"
                if metric == "endpoint_alignment_spearman":
                    uncertainty += ";10000 two-sided endpoint-label permutations"
                if metric == "target_identity_spearman":
                    uncertainty = f"Positive one-sided target-label/Mantel permutation; {'10,000' if stage == 'M4' else '999'} iterations; no identity CI"
                if source["entrant_kind"] != "formal":
                    uncertainty += "; diagnostic controls are excluded from formal permutation/BH families; missing P/q remain NA"
                status_field = {
                    "endpoint_alignment_spearman": "endpoint_alignment_status",
                    "target_identity_spearman": "target_identity_status",
                }.get(metric)
                rows.append(dict(
                    stage=stage, context=source["cell_line"], context_role=source["context_role"],
                    entrant_id=source["entrant_id"], display_name=source["display_name"], entrant_kind=source["entrant_kind"],
                    metric=metric, display_metric_zh=label, value=source[metric],
                    ci_low=source[lo] if lo else "NA", ci_high=source[hi] if hi else "NA",
                    permutation_p=source[p] if p else "NA", bh_q=source[q] if q else "NA",
                    value_status=source[status_field] if status_field else ("NA" if source[metric] == "NA" else "Existing estimate"),
                    uncertainty_scope=uncertainty,
                    bh_family="Not applicable" if not q or source["entrant_kind"] != "formal" else ("M4 separate18-test families per dimension" if stage == "M4" else "M5 separate3-test families per dimension"),
                    full_endpoint_n_targets=source["full_endpoint_n_targets"],
                    contract_n_targets=source["contract_n_targets"], contract_n_genes=source["contract_n_genes"],
                    anchor_n=source["anchor_n"], low_information_n=source["low_information_n"],
                    target_heldout=heldout, evaluation_design=design,
                    source_file=metrics_path, source_line=line, source_sha256=inputs[metrics_path],
                    source_key=json.dumps(dict(cell_line=key[0], entrant_id=key[1]), ensure_ascii=False),
                    source_value_column=metric, source_ci_columns=f"{lo};{hi}" if lo else "NA",
                    source_p_column=p or "NA", source_q_column=q or "NA",
                    training_source=training_path if training_line != "NA" else "src/wtbench/revision_m5_audit.py:reference_predictions",
                    training_source_line=training_line, endpoint_object=endpoint_path, endpoint_sha256=inputs[endpoint_path],
                ))
    table_path = OUT / "model_audit_citation_table.tsv"
    with table_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]), delimiter="\t", lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    main_table_path = render_main_table(rows)
    inputs["scripts/revision/export_model_finding_sources.py"] = digest("scripts/revision/export_model_finding_sources.py")
    output = dict(status="Completed: existing results extracted only", completed_utc=datetime.now(timezone.utc).isoformat(),
                  n_metric_rows=len(rows), frozen_source_checks=checked, inputs_sha256=inputs,
                  output_sha256={str(p.relative_to(ROOT)): digest(p.relative_to(ROOT)) for p in [table_path, main_table_path]},
                  new_model_scoring=False, new_statistical_inference=False,
                  selection_scope="All M4 formal/diagnostic and M5 formal/reference outputs; no score-based model selection",
                  pairwise_inference="Source results contain no paired between-model difference CIs or equivalence tests; none are invented")
    (OUT / "extraction_manifest.json").write_text(json.dumps(output, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Extracted {len(rows)} metric records unchanged; {len(checked)} frozen source hashes matched.")


if __name__ == "__main__":
    main()
