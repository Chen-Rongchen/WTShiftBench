"""Score new CellOT seed123 outputs using frozen M4 rules; historical formal scores are read-only."""

import json
from pathlib import Path
import shutil

import pandas as pd

from scripts.revision.run_cellot_seeded_retrain import original_hash_check
from wtbench.revision_hcc_audit import _derived_seed, bh_qvalues, endpoint_label_permutation_pvalue
from wtbench.revision_metric_validity import contract_axes, score_context, sha256_file, validate_contract_matrix
from wtbench.hcc_prediction_export import load_axis_membership


ROOT = Path(__file__).resolve().parents[2]


def verify_training(cfg, root):
    """Verify and summarize all94 training records individually, not just completion flags."""
    manifest_path = root / "input_manifest.json"
    manifest = json.loads(manifest_path.read_text())
    hashes = dict(manifest["inputs_sha256"])
    records, seen = [], set()
    for job_path in manifest["jobs"]:
        path = ROOT / job_path
        job = json.loads(path.read_text())
        record_path = path.parent / "completed.json"
        record = json.loads(record_path.read_text())
        key = job["context"], job["target"]
        assert key not in seen
        seen.add(key)
        assert (record["context"], record["target"]) == key
        assert record["kind"] == "full" and record["last_step"] == cfg["training"]["n_iters"] - 1
        assert record["training_seed"] == record["torch_initial_seed"] == cfg["training_seed"]
        assert record["deterministic_algorithms"] and record["torch_threads"] == cfg["runtime"]["torch_threads"]
        assert record["job_sha256"] == sha256_file(path)
        assert (ROOT / job["output"] / "cache/status").read_text() == "done"
        hashes.update(record["outputs_sha256"])
        for source in [record_path, path.parent / "training.log"]:
            hashes[str(source.relative_to(ROOT))] = sha256_file(source)
        records.append(record)
    counts = {context: sum(c == context for c, _ in seen) for context in cfg["contexts"]}
    assert len(records) == cfg["full_run"]["n_target_fits"] == 94
    assert set(c for c, _ in seen) == set(cfg["contexts"])
    assert all(n == cfg["targets_per_context"] for n in counts.values())
    for path, expected in hashes.items():
        assert sha256_file(ROOT / path) == expected, path
    exports = {}
    for context in cfg["contexts"]:
        path = root / "predictions" / context / "export_report.json"
        export = json.loads(path.read_text())
        assert export["n_targets"] == counts[context]
        assert {r["target_gene"] for r in export["exported_targets"]} == {t for c, t in seen if c == context}
        assert all(r["n_genes"] == cfg["genes_per_context"] for r in export["exported_targets"])
        exports[context] = export
        hashes[str(path.relative_to(ROOT))] = sha256_file(path)
    return dict(status="All94 fits and both prediction exports passed verification", contexts=counts,
                training_seed=cfg["training_seed"], historical_training_seed=None,
                original_manifest_entries_checked=original_hash_check(cfg),
                runtime_amendment=cfg["runtime_amendment"],
                prepared_inputs_checked=len(manifest["inputs_sha256"]),
                new_model_config_files_checked=sum(len(r["outputs_sha256"]) for r in records),
                input_and_model_sha256=hashes, runs=records, exports=exports)


def main():
    config_path = ROOT / "configs/revision/cellot_seed123_retrain_v1.json"
    cfg = json.loads(config_path.read_text())
    root = ROOT / cfg["output_root"]
    complete = json.loads((root / "training_complete.json").read_text())
    assert complete["n_fits"] == 94 and complete["contexts"] == cfg["contexts"]
    training = verify_training(cfg, root)
    hcc_path = ROOT / cfg["scoring"]["hcc_config"]
    spec_path = ROOT / cfg["scoring"]["metric_spec"]
    hcc, spec = json.loads(hcc_path.read_text()), json.loads(spec_path.read_text())
    old_manifest = json.loads((ROOT / "reports/revision/m4_hcc_full_audit/run_manifest.json").read_text())
    frozen = {r["path"]: r["sha256"] for r in old_manifest["inputs"]}
    old_results_path = ROOT / cfg["scoring"]["old_results"]
    old_hash = sha256_file(old_results_path)
    old_results = pd.read_csv(old_results_path, sep="\t")
    endpoint_path = ROOT / hcc["inputs"]["endpoint_object"]
    axis_path = ROOT / spec["inputs"]["axis_membership"]
    for path in [spec_path, endpoint_path, axis_path]:
        assert sha256_file(path) == frozen[str(path.relative_to(ROOT))]
    endpoints = pd.read_csv(endpoint_path, sep="\t")
    targets, genes = contract_axes(load_axis_membership(axis_path))
    inputs = [config_path, hcc_path, spec_path, old_results_path, endpoint_path, axis_path,
              Path(__file__).resolve(), ROOT / "src/wtbench/revision_metric_validity.py",
              ROOT / "src/wtbench/revision_hcc_audit.py", root / "training_complete.json",
              root / "input_manifest.json", root / "training_progress.json", root / "pilot_comparison.json",
              ROOT / "pixi.lock", ROOT / "scripts/revision/run_cellot_seeded_retrain.py",
              ROOT / cfg["original_replay_manifest"]]
    results, target_frames, comparisons = [], [], []
    columns = ["endpoint_alignment_spearman", "directional_recovery_median_signed_cosine",
               "anchor_separation_auc", "target_identity_spearman",
               "excess_homogenization_uncentered", "excess_homogenization_centered",
               "conventional_pearson_median", "conventional_normalized_rmse_median"]
    for context in cfg["contexts"]:
        prediction_path = root / "predictions" / context / "predicted_shift.tsv.gz"
        observed_path = ROOT / "reports/revision/m3_metric_validity" / f"observed_shift_{context}.tsv.gz"
        assert sha256_file(observed_path) == frozen[str(observed_path.relative_to(ROOT))]
        observed = validate_contract_matrix(pd.read_csv(observed_path, sep="\t"), target_order=targets,
                                           gene_order=genes, matrix_name=f"observed:{context}")
        predicted = validate_contract_matrix(pd.read_csv(prediction_path, sep="\t"), target_order=targets,
                                            gene_order=genes, matrix_name=f"seed123:{context}")
        target, summary = score_context(prediction=predicted, observed=observed,
            endpoint=endpoints.loc[endpoints["cell_line"].eq(context)].copy(), cell_line=context,
            entrant_id=cfg["run_id"], reference_type="", reference_seed=None, config=spec)
        # score_context defaults to reference; this is supplementary retraining, not a diagnostic oracle or formal entrant.
        summary["entrant_kind"] = "supplementary_retrain"
        target["entrant_kind"] = "supplementary_retrain"
        summary["scored_target_held_out"] = False
        summary["entrant_role"] = "Independent fixed-seed fit; does not replace formal outputs"
        summary["training_seed"] = cfg["training_seed"]
        summary["endpoint_alignment_label_permutation_pvalue"] = endpoint_label_permutation_pvalue(
            target["predicted_shift_mean_abs"].to_numpy(float), target["depmap_gene_dependency"].to_numpy(float),
            permutations=hcc["inference"]["endpoint_label_permutations"],
            seed=_derived_seed(hcc["inference"]["endpoint_label_seed"], cfg["run_id"], context), two_sided=True)
        results.append(summary)
        target_frames.append(target)
        old = old_results.loc[old_results["cell_line"].eq(context)
                              & old_results["entrant_id"].eq(cfg["scoring"]["old_model_id"])].iloc[0]
        for col in columns:
            comparisons.append(dict(context=context, metric=col, historical=float(old[col]),
                                    new_seed123=float(summary[col]), delta=float(summary[col] - old[col])))
        inputs.extend([prediction_path, observed_path])
        print(f"{context} scoring under frozen definitions completed.", flush=True)
    table = pd.DataFrame(results)
    for p, q in [("endpoint_alignment_label_permutation_pvalue", "endpoint_q_bh_new_two_context_family"),
                 ("target_identity_label_permutation_pvalue", "identity_q_bh_new_two_context_family")]:
        table[q] = bh_qvalues(table[p])
    out = ROOT / "docs/revision_cellot_seed123"
    out.mkdir(parents=True, exist_ok=True)
    outputs = [out / "new_context_metrics.tsv", out / "new_target_metrics.tsv.gz", out / "old_new_comparison.tsv",
               out / "training_verification_manifest.json"]
    table.to_csv(outputs[0], sep="\t", index=False)
    pd.concat(target_frames).to_csv(outputs[1], sep="\t", index=False)
    pd.DataFrame(comparisons).to_csv(outputs[2], sep="\t", index=False)
    outputs[3].write_text(json.dumps(training, ensure_ascii=False, indent=2) + "\n")
    # Save both small matrices with local evidence for score-only recomputation, without replacing original M4 matrices.
    for context in cfg["contexts"]:
        path = out / f"predicted_shift_{context}.tsv.gz"
        shutil.copyfile(root / "predictions" / context / "predicted_shift.tsv.gz", path)
        outputs.append(path)
    assert sha256_file(old_results_path) == old_hash
    record = dict(status="New training outputs for both contexts scored under frozen rules", training_seed=123,
                  historical_results_unchanged=True, old_training_seed=None,
                  scope="Single-seed same-context fit supplement; no claim of cross-seed stability or significant model differences",
                  inputs_sha256={str(p.relative_to(ROOT)): sha256_file(p) for p in inputs},
                  outputs_sha256={str(p.relative_to(ROOT)): sha256_file(p) for p in outputs})
    (out / "scoring_manifest.json").write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n")


if __name__ == "__main__":
    main()
