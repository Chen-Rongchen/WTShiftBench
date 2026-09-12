"""仅从归档矩阵复算冻结评分；不访问原始细胞或重新训练模型。"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

import numpy as np
import pandas as pd

from wtbench.revision_metric_validity import score_context, build_random_direction_prediction
from wtbench.revision_hcc_audit import (
    _derived_seed as hcc_seed, bh_qvalues, endpoint_label_permutation_pvalue,
)
from wtbench.revision_m5_audit import load_contract_npz, reference_predictions, _derived_seed as m5_seed
from wtbench.revision_finalization import h_leave_one, jackknife_interval


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_matrix(path):
    if path.suffix == ".npz":
        return load_contract_npz(path)
    return pd.read_csv(path, sep="\t", index_col=0).astype(float)


def run(args):
    manifest = json.loads((ROOT / "archive_manifest.json").read_text())
    for record in manifest["files"]:
        path = ROOT / record["path"]
        if digest(path) != record["sha256"]:
            raise ValueError(f"文件hash不符：{record['path']}")
    print(f"完整性检查通过：{len(manifest['files'])} 个文件", flush=True)
    if args.verify_only:
        return
    spec = json.loads((ROOT / "configs/revision/revision_metric_spec_v1.json").read_text())
    out = args.output.resolve()
    out.mkdir(parents=True, exist_ok=True)
    differences = []
    h_cache = {}
    for group in manifest["score_groups"]:
        if args.group and group["name"] not in args.group:
            continue
        expected = pd.read_csv(ROOT / group["expected"], sep="\t")
        rows = []
        target_rows = []
        for item in group["items"]:
            current = copy.deepcopy(spec)
            current["inference"].update(group.get("inference_overrides", {}))
            if item.get("identity_permutations") is not None:
                current["inference"]["target_identity_permutations"] = item["identity_permutations"]
            if args.points_only:
                current["inference"].update(bootstrap_replicates=0, target_identity_permutations=0)
            observed = load_matrix(ROOT / item["observed"])
            endpoint = pd.read_csv(ROOT / item["endpoint"], sep="\t")
            if group["name"] in {"m5","replogle_feature_seeds"}:
                config = json.loads((ROOT / "configs/revision/revision_m5_full_audit_v1.json").read_text())
                endpoint["context_role"] = config["contract"]["context_role"]
            else:
                endpoint = endpoint.loc[endpoint["cell_line"].eq(item["context"])].copy()
            reference = item.get("reference_type", "")
            seed = item.get("reference_seed")
            if "prediction" in item:
                prediction = load_matrix(ROOT / item["prediction"])
            elif group["name"] == "m5":
                prediction = reference_predictions(observed, 20260920)[reference]
            elif reference == "observed_shift_oracle":
                prediction = observed.copy()
            elif reference == "negated_oracle":
                prediction = -observed
            else:
                prediction = build_random_direction_prediction(observed, seed=seed)
            if not prediction.index.equals(observed.index) or not prediction.columns.equals(observed.columns):
                raise ValueError(f"矩阵轴不符：{item['entrant_id']} {item['context']}")
            targets, summary = score_context(
                prediction=prediction, observed=observed, endpoint=endpoint,
                cell_line=item["context"], entrant_id=item["entrant_id"],
                reference_type=reference, reference_seed=seed, config=current,
            )
            if "endpoint_seed" in item and not args.points_only:
                summary["endpoint_alignment_label_permutation_pvalue"] = endpoint_label_permutation_pvalue(
                    targets["predicted_shift_mean_abs"].to_numpy(float),
                    targets["depmap_gene_dependency"].to_numpy(float),
                    permutations=10000, seed=item["endpoint_seed"],
                )
            if not args.points_only and group["name"] != "m3":
                def h(matrix,centered):
                    array=matrix.to_numpy(float)
                    key=(hashlib.sha256(array.tobytes()).hexdigest(),centered)
                    if key not in h_cache:h_cache[key]=h_leave_one(array,centered)
                    return h_cache[key]
                for centered in [False,True]:
                    form="centered" if centered else "uncentered"
                    hp,lp=h(prediction,centered);ho,lo=h(observed,centered)
                    for name,point,loo,bound in [("predicted",hp,lp,1),("observed",ho,lo,1),("excess",hp-ho,lp-lo,2)]:
                        low,high,_,status=jackknife_interval(point,loo,bound)
                        metric=f"{name}_homogenization_{form}"
                        summary[metric+"_ci_low"]=low;summary[metric+"_ci_high"]=high
                        summary[metric+"_jackknife_status"]=status
            rows.append(summary)
            target_rows.append(targets)
            print(f"完成 {group['name']} / {item['context']} / {item['entrant_id']}", flush=True)
        actual = pd.DataFrame(rows)
        keys = ["cell_line", "entrant_id"]
        eligible = actual["entrant_id"].isin(group["bh_entrants"])
        if not args.points_only:
            for p, q in group["bh_columns"]:
                actual[q] = np.nan
                actual.loc[eligible, q] = bh_qvalues(actual.loc[eligible, p])
        actual.to_csv(out / f"{group['name']}_context_metrics.tsv", sep="\t", index=False, na_rep="NA")
        pd.concat(target_rows).to_csv(out / f"{group['name']}_target_metrics.tsv.gz", sep="\t", index=False)
        left = actual.set_index(keys)
        right = expected.set_index(keys).loc[left.index]
        for col in left.columns.intersection(right.columns):
            if args.points_only and ("ci_" in col or "pvalue" in col or "qvalue" in col):
                continue
            if col in ("entrant_kind",):
                continue
            if pd.api.types.is_numeric_dtype(right[col]):
                a = pd.to_numeric(left[col]).to_numpy(float)
                b = right[col].to_numpy(float)
                # 原M5归档为float32；只允许序列化精度误差，不放宽P/q和样本数。
                tol = 1e-6 if group["name"] in {"m5","replogle_feature_seeds"} else 1e-10
                if "pvalue" in col or "qvalue" in col or col.endswith("_n") or "n_targets" in col or "n_genes" in col:
                    tol = 1e-12
                ok = np.isclose(a, b, rtol=0, atol=tol, equal_nan=True)
                error = np.abs(a-b)
                differences.append(dict(group=group["name"], metric=col, passed=bool(ok.all()),
                    max_abs_difference=float(np.nanmax(error)) if np.isfinite(error).any() else 0,
                    absolute_tolerance=tol))
            elif col.endswith("_status") or col == "missing_endpoint_targets":
                ok = left[col].fillna("").astype(str).equals(right[col].fillna("").astype(str))
                differences.append(dict(group=group["name"], metric=col, passed=ok, max_abs_difference=0, absolute_tolerance=0))
    pd.DataFrame(differences).to_csv(out / "comparison.tsv", sep="\t", index=False)
    failed = [row for row in differences if not row["passed"]]
    result = dict(mode="point_estimates_only" if args.points_only else "full_frozen_inference",
        files_verified=len(manifest["files"]), comparisons=len(differences), failed=failed,
        source_module=str(sys.modules["wtbench.revision_metric_validity"].__file__))
    (out / "verification.json").write_text(json.dumps(result, ensure_ascii=False, indent=2)+"\n")
    print(json.dumps(result, ensure_ascii=False), flush=True)
    if failed:
        raise SystemExit(1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verify-only", action="store_true")
    parser.add_argument("--points-only", action="store_true")
    parser.add_argument("--group", action="append", choices=["m3", "m4", "m5", "cellot_training_seeds","other_training_seeds","replogle_feature_seeds"])
    parser.add_argument("--output", type=Path, default=ROOT / "recomputed")
    run(parser.parse_args())
