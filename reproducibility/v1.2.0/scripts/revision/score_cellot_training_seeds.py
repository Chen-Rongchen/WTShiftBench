"""Verify newly trained runs against registrations and summarize seed sensitivity without best-seed selection."""
import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

from scripts.revision.run_cellot_training_seeds import CONFIG, configuration
from scripts.revision.score_cellot_seeded_retrain import verify_training
from wtbench.hcc_prediction_export import load_axis_membership
from wtbench.revision_hcc_audit import _derived_seed, bh_qvalues, endpoint_label_permutation_pvalue
from wtbench.revision_metric_validity import contract_axes, score_context, sha256_file, validate_contract_matrix
from wtbench.revision_finalization import h_leave_one, jackknife_interval

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "reports/revision/finalization_v2/cellot_seeds"


def verify_recipe(config_path=CONFIG):
    """After observed sign changes across seeds, verify shared data, configurations, and libraries for every fit."""
    root123=ROOT/"reports/revision/cellot_seed123_retrain_v1"
    baseline=json.loads((root123/"input_manifest.json").read_text())
    jobs={}
    for p in baseline["jobs"]:
        j=json.loads((ROOT/p).read_text())
        jobs[j["context"],j["target"]]=(j,json.loads((ROOT/p).with_name("completed.json").read_text()))
    comparisons=[]
    amendment=json.loads(config_path.read_text())
    for seed in amendment["additional_seeds"]:
        root=ROOT/configuration(seed,config_path)[1]["output_root"]
        manifest=json.loads((root/"input_manifest.json").read_text())
        assert manifest["source_revision"]==baseline["source_revision"]
        for p in manifest["jobs"]:
            job=json.loads((ROOT/p).read_text())
            old,previous=jobs[job["context"],job["target"]]
            now=json.loads((ROOT/p).with_name("completed.json").read_text())
            assert job["inputs_sha256"]==old["inputs_sha256"]
            assert job["source_config"]==old["source_config"]
            for field in ["package_versions","device","torch_threads","deterministic_algorithms","last_step"]:
                assert now[field]==previous[field],(seed,job["context"],job["target"],field)
            configpath=job["output"]+"/config.yaml"
            oldconfig=old["output"]+"/config.yaml"
            assert sha256_file(ROOT/configpath)==sha256_file(ROOT/oldconfig)
            comparisons.append(dict(seed=seed,context=job["context"],target=job["target"],same_inputs_config_runtime=True))
    assert len(comparisons)==94*len(amendment["additional_seeds"])
    (OUT/"fixed_recipe_verification.json").write_text(json.dumps(dict(source_revision=baseline["source_revision"],
        compared_target_fits=len(comparisons),formal_seed=123,comparisons=comparisons,
        scope="Itemwise checks of staged cells, features, complete configurations, libraries, determinism, and iteration counts; seeds differ and concurrency limits are4/8, with each task single-threaded"),ensure_ascii=False,indent=2)+"\n")


def main(config_path=CONFIG):
    global OUT
    amendment = json.loads(config_path.read_text())
    OUT=ROOT/amendment.get("scoring_output_root","reports/revision/finalization_v2/cellot_seeds")
    OUT.mkdir(parents=True, exist_ok=True)
    verify_recipe(config_path)
    cfg = configuration(amendment["additional_seeds"][0],config_path)[1]
    hcc_path = ROOT / cfg["scoring"]["hcc_config"]
    spec_path = ROOT / cfg["scoring"]["metric_spec"]
    hcc = json.loads(hcc_path.read_text())
    spec = json.loads(spec_path.read_text())
    endpoint_path = ROOT / hcc["inputs"]["endpoint_object"]
    axis_path = ROOT / spec["inputs"]["axis_membership"]
    endpoints = pd.read_csv(endpoint_path, sep="\t")
    targets, genes = contract_axes(load_axis_membership(axis_path))
    old_manifest = json.loads((ROOT / "reports/revision/m4_hcc_full_audit/run_manifest.json").read_text())
    frozen = {r["path"]: r["sha256"] for r in old_manifest["inputs"]}
    inputs = [config_path, Path(__file__).resolve(), hcc_path, spec_path, endpoint_path, axis_path,
              ROOT / "src/wtbench/revision_metric_validity.py", ROOT / "src/wtbench/revision_hcc_audit.py",
              ROOT / "src/wtbench/revision_finalization.py", ROOT / "pixi.lock"]
    for p in [spec_path, endpoint_path, axis_path]:
        assert sha256_file(p) == frozen[str(p.relative_to(ROOT))], p
    summaries, target_tables, intervals = [], [], []
    for seed in amendment["additional_seeds"]:
        _, cfg = configuration(seed,config_path)
        root = ROOT / cfg["output_root"]
        complete = json.loads((root / "training_complete.json").read_text())
        assert complete["n_fits"] == 94 and complete["seed"] == seed
        verification = verify_training(cfg, root)
        (OUT / f"seed{seed}_training_verification.json").write_text(json.dumps(verification, ensure_ascii=False, indent=2) + "\n")
        inputs.extend([root / "training_complete.json", root / "input_manifest.json"])
        for context in cfg["contexts"]:
            predpath = root / "predictions" / context / "predicted_shift.tsv.gz"
            obspath = ROOT / f"reports/revision/m3_metric_validity/observed_shift_{context}.tsv.gz"
            assert sha256_file(obspath) == frozen[str(obspath.relative_to(ROOT))]
            observed = validate_contract_matrix(pd.read_csv(obspath, sep="\t"), target_order=targets,
                                                gene_order=genes, matrix_name=f"observed:{context}")
            predicted = validate_contract_matrix(pd.read_csv(predpath, sep="\t"), target_order=targets,
                                                 gene_order=genes, matrix_name=f"seed{seed}:{context}")
            target, row = score_context(prediction=predicted, observed=observed,
                endpoint=endpoints.loc[endpoints.cell_line.eq(context)].copy(), cell_line=context,
                entrant_id=cfg["run_id"], reference_type="", reference_seed=None, config=spec)
            row.update(training_seed=seed, entrant_role="training_seed_sensitivity", entrant_kind="training_seed_sensitivity",
                       scored_target_held_out=False, display_name="CellOT", model_family="CellOT",
                       endpoint_alignment_label_permutation_pvalue=endpoint_label_permutation_pvalue(
                           target.predicted_shift_mean_abs.to_numpy(float), target.depmap_gene_dependency.to_numpy(float),
                           permutations=hcc["inference"]["endpoint_label_permutations"],
                           seed=_derived_seed(hcc["inference"]["endpoint_label_seed"], cfg["run_id"], context)))
            target["training_seed"] = seed
            target["entrant_kind"] = "training_seed_sensitivity"
            for centered in [False, True]:
                form = "centered" if centered else "uncentered"
                hp, lp = h_leave_one(predicted.to_numpy(float), centered)
                ho, lo = h_leave_one(observed.to_numpy(float), centered)
                for name, point, loo, bound in [("predicted", hp, lp, 1), ("observed", ho, lo, 1), ("excess", hp-ho, lp-lo, 2)]:
                    metric = f"{name}_homogenization_{form}"
                    assert np.isclose(point, row[metric], atol=1e-10, equal_nan=True)
                    low, high, se, status = jackknife_interval(point, loo, bound)
                    row[metric + "_ci_low"], row[metric + "_ci_high"] = low, high
                    intervals.append(dict(cell_line=context, entrant_id=cfg["run_id"], training_seed=seed,
                                          metric=metric, estimate=point, ci_low=low, ci_high=high, jackknife_se=se, status=status))
            summaries.append(row)
            target_tables.append(target)
            inputs.extend([predpath, obspath])
            print(f"seed={seed} {context}:94 run records verified and current-context scoring completed.", flush=True)
    extra = pd.DataFrame(summaries)
    if "previous_scoring_root" in amendment:
        previous=ROOT/amendment["previous_scoring_root"]
        prior_manifest=previous/"scoring_manifest.json"
        for p,h in json.loads(prior_manifest.read_text())["outputs_sha256"].items():
            assert sha256_file(ROOT/p)==h,p
        extra=pd.concat([pd.read_csv(previous/"additional_context_metrics.tsv",sep="\t"),extra],ignore_index=True)
        target_tables.insert(0,pd.read_csv(previous/"additional_target_metrics.tsv.gz",sep="\t"))
        intervals=pd.read_csv(previous/"additional_homogenization_intervals.tsv",sep="\t").to_dict("records")+intervals
        inputs.extend([prior_manifest,previous/"additional_context_metrics.tsv",previous/"additional_target_metrics.tsv.gz",previous/"additional_homogenization_intervals.tsv"])
    for p, q in [("endpoint_alignment_label_permutation_pvalue", "endpoint_alignment_permutation_qvalue_bh"),
                 ("target_identity_label_permutation_pvalue", "target_identity_permutation_qvalue_bh")]:
        extra[q] = bh_qvalues(extra[p])
    extra["inference_family"] = amendment.get("inference_family","A011_four_additional_seed_context_outputs")
    formalpath = ROOT / "reports/revision/finalization_v2/m4/formal_and_diagnostic_context_metrics_with_uncertainty.tsv"
    formal = pd.read_csv(formalpath, sep="\t")
    formal = formal.loc[formal.entrant_id.eq("cellot_hcc_seed123_retrain_v1")].copy()
    formal["training_seed"] = 123
    formal["inference_family"] = "A010_eighteen_formal_HCC_outputs"
    inputs.append(formalpath)
    all_seeds = pd.concat([formal, extra], ignore_index=True).sort_values(["cell_line", "training_seed"])
    paths = []
    for filename, table in [("additional_context_metrics.tsv", extra), ("all_seed_context_metrics.tsv", all_seeds),
                            ("additional_target_metrics.tsv.gz", pd.concat(target_tables)),
                            ("additional_homogenization_intervals.tsv", pd.DataFrame(intervals))]:
        p = OUT / filename
        table.to_csv(p, sep="\t", index=False, na_rep="NA")
        paths.append(p)
    record = dict(amendment=amendment["amendment_id"], formal_seed=123, additional_seeds=sorted(extra.training_seed.unique().astype(int).tolist()),
                  scope="Training-seed sensitivity under the same recipe; no prediction averaging, best-score selection, or changes to the formal18-test BH family",
                  inputs_sha256={str(p.relative_to(ROOT)): sha256_file(p) for p in inputs},
                  outputs_sha256={str(p.relative_to(ROOT)): sha256_file(p) for p in paths})
    (OUT / "scoring_manifest.json").write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n")


if __name__ == "__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config",type=Path,default=CONFIG)
    main(parser.parse_args().config.resolve())
