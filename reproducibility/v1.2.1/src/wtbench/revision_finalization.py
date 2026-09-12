"""A010最终版本：复用已验收输出、统一辅助端点、补充target级同质化区间。"""

from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

from wtbench.revision_hcc_audit import (
    _derived_seed, bh_qvalues, build_metric_correlations, build_metric_long,
    build_discordance_tables, endpoint_label_permutation_pvalue,
)
from wtbench.revision_metric_validity import (
    sha256_file, bootstrap_spearman_ci, mean_off_diagonal_cosine,
)
from wtbench.revision_m6_endpoint_tuning import run_endpoint_tuning
from wtbench.truth_bridge import load_depmap_endpoint

ROOT = Path(__file__).resolve().parents[2]
CONFIG = ROOT / "configs/revision/amendment_010_formal_release_v2.json"
OUT = ROOT / "reports/revision/finalization_v2"
INPUTS = {}


def read(path):
    path = ROOT / path
    INPUTS[str(path.relative_to(ROOT))] = sha256_file(path)
    return pd.read_csv(path, sep="\t")


def write(frame, path):
    path.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(path, sep="\t", index=False, na_rep="NA")


def manifest(name, outputs):
    record = dict(amendment="A010", inputs_sha256=INPUTS,
                  outputs_sha256={str(p.relative_to(ROOT)): sha256_file(p) for p in outputs})
    path = OUT / name / "run_manifest.json"
    path.write_text(json.dumps(record, ensure_ascii=False, indent=2)+"\n")


def migrate():
    """既有区间/P保留；正式BH检验族和依赖模型集合的摘要重算。"""
    oldroot = "reports/revision/m4_hcc_full_audit/"
    old = read(oldroot+"formal_and_diagnostic_context_metrics.tsv")
    new = read("docs/revision_cellot_seed123/new_context_metrics.tsv")
    old_id, new_id = "cellot_hcc_formal_v1", "cellot_hcc_seed123_retrain_v1"
    for column in ["entrant_role", "entrant_kind"]:
        new[column] = "formal"
    new["display_name"] = "CellOT"
    new["model_family"] = "CellOT"
    new = new.drop(columns=["endpoint_q_bh_new_two_context_family", "identity_q_bh_new_two_context_family"])
    context = pd.concat([old.loc[~old.entrant_id.eq(old_id)], new], ignore_index=True)
    context = context.sort_values(["cell_line", "entrant_id"]).reset_index(drop=True)
    formal = context.entrant_role.eq("formal")
    assert formal.sum() == 18
    for p, q in [("endpoint_alignment_label_permutation_pvalue", "endpoint_alignment_permutation_qvalue_bh"),
                 ("target_identity_label_permutation_pvalue", "target_identity_permutation_qvalue_bh")]:
        context.loc[formal, q] = bh_qvalues(context.loc[formal, p])
    target = read(oldroot+"formal_and_diagnostic_target_metrics.tsv.gz")
    new_target = read("docs/revision_cellot_seed123/new_target_metrics.tsv.gz")
    new_target["entrant_kind"] = "formal"
    new_target["entrant_role"] = "formal"
    new_target["display_name"] = "CellOT"
    new_target["model_family"] = "CellOT"
    target = pd.concat([target.loc[~target.entrant_id.eq(old_id)], new_target], ignore_index=True)
    target = target.sort_values(["cell_line", "entrant_id", "target_gene"])
    reg = read(oldroot+"model_training_evaluation_registry.tsv")
    mask = reg.model_id.eq(old_id)
    reg.loc[mask, "model_id"] = new_id
    reg.loc[mask, "model_version"] = new_id
    reg.loc[mask, "evaluation_design"] = "same-context fit includes scored-target cells; A010 formal seed-123 retraining"
    reg.loc[mask, "documentation_gap"] = "none for current training seed; historical seed remains unavailable"
    reg.loc[mask, "source_kind"] = "revision_time_retrained_from_random_initialization"
    cfg = json.loads((ROOT/"configs/revision/cellot_seed123_retrain_v1.json").read_text())
    reg.loc[mask, "runtime_and_hyperparameters_json"] = json.dumps(dict(cfg["training"], seed=123, runtime=cfg["runtime"]), ensure_ascii=False)
    for i in reg.index[mask]:
        c = reg.at[i, "cell_line"]
        reg.at[i, "checkpoint_or_reference"] = f"reports/revision/cellot_seed123_retrain_v1/full/{c}/<target>/model-cellot/cache/model.pt"
        reg.at[i, "source_files"] = "configs/revision/cellot_seed123_retrain_v1.json;docs/revision_cellot_seed123/training_verification_manifest.json;configs/revision/amendment_010_formal_release_v2.json"
    completion = read(oldroot+"revised_model_context_completion.tsv")
    completion = completion.replace(old_id, new_id)
    recorded = json.loads((ROOT/"docs/revision_cellot_seed123/scoring_manifest.json").read_text())["outputs_sha256"]
    for i in completion.index[completion.model_id.eq(new_id)]:
        context_name = completion.at[i,"cell_line"]
        path = f"docs/revision_cellot_seed123/predicted_shift_{context_name}.tsv.gz"
        digest = sha256_file(ROOT/path)
        assert digest == recorded[path], path
        frame = pd.read_csv(ROOT/path,sep="\t",index_col=0)
        assert frame.shape == (47,47)
        completion.loc[i,["prediction_path","current_sha256","registered_sha256","hash_matches_registry"]] = [path,digest,recorded[path],True]
        INPUTS[path] = digest
    out = OUT/"m4"
    outputs = []
    tables = {
        "formal_and_diagnostic_context_metrics.tsv": context,
        "formal_and_diagnostic_target_metrics.tsv.gz": target,
        "model_training_evaluation_registry.tsv": reg,
        "revised_model_context_completion.tsv": completion,
        "metric_correlation_summary.tsv": build_metric_correlations(context),
        "formal_metric_long.tsv": build_metric_long(context),
    }
    hcc = json.loads((ROOT/"configs/revision/revision_hcc_full_audit_v1.json").read_text())
    for name, df in zip(["all_discordance_pairs.tsv", "selected_discordance_pairs.tsv", "reconstruction_homogenization_examples.tsv"], build_discordance_tables(context,hcc)):
        tables[name] = df
    for name, df in tables.items():
        path=out/name
        write(df,path); outputs.append(path)
    manifest("m4",outputs)
    tuning = json.loads((ROOT/"configs/revision/revision_m6_endpoint_tuning_v1.json").read_text())
    tuning["analysis_id"] = "bib_revision_m6_endpoint_tuning_A010"
    tuning["amendment"] = str(CONFIG.relative_to(ROOT))
    tuning["inputs"][0]["context_metrics"] = str((out/"formal_and_diagnostic_context_metrics.tsv").relative_to(ROOT))
    tuning["inputs"][0]["target_metrics"] = str((out/"formal_and_diagnostic_target_metrics.tsv.gz").relative_to(ROOT))
    tuning["outputs"]["root"] = str((OUT/"m6").relative_to(ROOT))
    path=out/"m6_config.json"
    path.write_text(json.dumps(tuning,ensure_ascii=False,indent=2)+"\n")
    run_endpoint_tuning(path)
    print("A010 CellOT正式迁移、18-test BH、M4相关性和M6已完成。",flush=True)


def depmap():
    """直接复用旧核验规则，保留每季度逐值结果；另算明确25Q3的辅助统计。"""
    spec=importlib.util.spec_from_file_location("verify_depmap",ROOT/"scripts/revision/verify_depmap_restore.py")
    verify=importlib.util.module_from_spec(spec);spec.loader.exec_module(verify)
    cfg=json.loads(CONFIG.read_text())["gene_effect_sensitivity"]
    groups=[]
    for source in verify.SOURCES:
        frame=read(source);frame["source_path"]=source;frame["source_line"]=np.arange(len(frame))+2
        groups.extend(group for _,group in frame.groupby("cell_line",sort=False))
    summaries=[];details=[];files=[];official=None
    for path in [ROOT/"depmap/CRISPRGeneEffect.csv",*sorted((ROOT/"depmap").glob("*/CRISPRGeneEffect.csv"))]:
        sha=sha256_file(path);relative=str(path.relative_to(ROOT));INPUTS[relative]=sha
        release="25Q3" if path.parent.name=="depmap" else path.parent.name
        matrix=load_depmap_endpoint(path).set_index("depmap_model_id",verify_integrity=True)
        files.append(dict(release=release,path=relative,sha256=sha,bytes=path.stat().st_size,n_models=len(matrix),n_genes=len(matrix.columns)))
        if release=="25Q3":
            assert sha==cfg["sha256"]
            official=matrix
        for group in groups:
            detail,summary=verify.compare_endpoint(group,matrix,"depmap_gene_effect")
            detail["candidate_release"]=release;summary["candidate_release"]=release
            details.append(detail);summaries.append(summary)
        print(f"DepMap {release}逐值核验完成。",flush=True)
    tests=[];target_rows=[]
    for group in groups:
        context=group.cell_line.iloc[0]
        frame=group.copy()
        frame["gene_effect_25q3"]=[official.loc[r.depmap_model_id].get(r.target_gene,np.nan) for r in frame.itertuples()]
        frame=frame.dropna(subset=["real_shift_mean_abs","depmap_gene_dependency","gene_effect_25q3"])
        frame["historical_gene_effect"]=frame["depmap_gene_effect"]
        x=frame.real_shift_mean_abs.to_numpy(float);y=-frame.gene_effect_25q3.to_numpy(float)
        seed=_derived_seed(cfg["base_seed"],context)
        lo,hi=bootstrap_spearman_ci(x,y,replicates=cfg["bootstrap_replicates"],seed=seed,confidence=cfg["confidence"])
        p=endpoint_label_permutation_pvalue(x,y,permutations=cfg["permutations"],seed=seed+1)
        tests.append(dict(cell_line=context,n_targets=len(frame),gene_effect_release="25Q3",orientation="negative_gene_effect_stronger_dependency",
                          spearman_rho=float(stats.spearmanr(x,y).statistic),bootstrap_ci_low=lo,bootstrap_ci_high=hi,
                          permutation_pvalue_two_sided=p,bootstrap_seed=seed,permutation_seed=seed+1,
                          probability_rho_same_targets=float(stats.spearmanr(x,frame.depmap_gene_dependency).statistic),
                          historical_gene_effect_rho_same_targets=float(stats.spearmanr(x,-frame.depmap_gene_effect).statistic)))
        target_rows.append(frame[["cell_line","depmap_model_id","target_gene","real_shift_mean_abs","depmap_gene_dependency","historical_gene_effect","gene_effect_25q3","source_path","source_line"]])
        print(f"{context}: 25Q3 gene-effect sensitivity n={len(frame)}, rho={tests[-1]['spearman_rho']:.3f}",flush=True)
    summary=pd.DataFrame(tests);summary["permutation_qvalue_bh_eight_contexts"]=bh_qvalues(summary.permutation_pvalue_two_sided)
    tables={"candidate_file_registry.tsv":pd.DataFrame(files),"candidate_comparison.tsv":pd.DataFrame(summaries),
            "candidate_detail.tsv.gz":pd.concat(details),"gene_effect_sensitivity.tsv":summary,
            "gene_effect_target_values.tsv.gz":pd.concat(target_rows)}
    outputs=[]
    for name,frame in tables.items():
        path=OUT/"depmap"/name;write(frame,path);outputs.append(path)
    manifest("depmap",outputs)


def h_leave_one(values, centered=False, tolerance=1e-12):
    """重新中心化每个真实删一队列，不将pair视为独立或固定全量中心。"""
    values=np.asarray(values,dtype=float)
    n=len(values)
    full=values-values.mean(axis=0) if centered else values
    point=mean_off_diagonal_cosine(full,tolerance=tolerance)[0]
    # 真实shared-mean中心化后全为零、null参照全为零；数学不可评，不补0。
    if not np.isfinite(point):
        return point,np.full(n,np.nan)
    loo=np.empty(n)
    for i in range(n):
        sample=np.concatenate([values[:i],values[i+1:]],axis=0)
        if centered:sample=sample-sample.mean(axis=0)
        loo[i]=mean_off_diagonal_cosine(sample,tolerance=tolerance)[0]
    return point,loo


def jackknife_interval(point,loo,bound):
    loo=np.asarray(loo,dtype=float);n=len(loo)
    if not np.isfinite(point) or not np.isfinite(loo).all():
        return np.nan,np.nan,np.nan,"not_estimable_zero_vectors"
    se=float(np.sqrt((n-1)/n*np.sum((loo-loo.mean())**2)))
    width=float(stats.t.ppf(.975,n-1))*se
    return max(-bound,point-width),min(bound,point+width),se,"target_delete_one_jackknife"


def uncertainty():
    from wtbench.revision_metric_validity import build_random_direction_prediction
    matrices={}; axes={}; cache={};results=[]
    def matrix(path):
        p=ROOT/path
        INPUTS[path]=sha256_file(p)
        if path not in matrices:
            if p.suffix==".npz":
                with np.load(p,allow_pickle=False) as z:
                    matrices[path]=np.asarray(z["values"],float)
                    axes[id(matrices[path])]=(tuple(z["targets"].astype(str)),tuple(z["genes"].astype(str)))
            else:
                frame=pd.read_csv(p,sep="\t",index_col=0)
                matrices[path]=frame.to_numpy(float)
                axes[id(matrices[path])]=(tuple(frame.index.astype(str)),tuple(frame.columns.astype(str)))
        return matrices[path]
    def h(values,centered):
        import hashlib
        key=(hashlib.sha256(values.tobytes()).hexdigest(),centered)
        if key not in cache:cache[key]=h_leave_one(values,centered)
        return cache[key]
    paths=[("m4",OUT/"m4/formal_and_diagnostic_context_metrics.tsv"),
           ("m5",ROOT/"reports/revision/m5_independent_full_audit/formal_and_reference_context_metrics.tsv"),
           ("m3",ROOT/"reports/revision/m3_metric_validity/reference_context_metrics.tsv")]
    for scope,path in paths:
        table=read(path)
        for row in table.to_dict("records"):
            context,entrant=row["cell_line"],row["entrant_id"]
            if scope=="m5":
                observed=matrix("data/predictions/revision_m5_replogle/observed_shift_contract.npz")
                if row["entrant_role"]=="formal":predicted=matrix(f"data/predictions/revision_m5_replogle/{entrant}_predicted_shift.npz")
                elif entrant=="observed_shift_oracle":predicted=observed.copy()
                elif entrant=="negated_oracle":predicted=-observed
                elif entrant=="shared_mean_baseline":predicted=np.repeat(observed.mean(axis=0,keepdims=True),len(observed),axis=0)
                else:predicted=build_random_direction_prediction(pd.DataFrame(observed),seed=20260920).to_numpy()
            else:
                observed=matrix(f"reports/revision/m3_metric_validity/observed_shift_{context}.tsv.gz")
                if entrant=="cellot_hcc_seed123_retrain_v1":predicted=matrix(f"docs/revision_cellot_seed123/predicted_shift_{context}.tsv.gz")
                elif scope=="m4" or entrant=="shared_mean_baseline":predicted=matrix(f"data/predictions/hcc_scorer_ready/{entrant}/{context}/predicted_shift.tsv.gz")
                elif row["reference_type"]=="observed_shift_oracle":predicted=observed.copy()
                elif row["reference_type"]=="negated_oracle":predicted=-observed
                else:predicted=build_random_direction_prediction(pd.DataFrame(observed),seed=int(row["reference_seed"])).to_numpy()
            if id(predicted) in axes:
                assert axes[id(predicted)]==axes[id(observed)],(context,entrant,"配对target/gene轴不一致")
            for centered in [False,True]:
                form="centered" if centered else "uncentered"
                hp,lp=h(predicted,centered);ho,lo=h(observed,centered)
                for name,point,leave,bound in [("predicted",hp,lp,1),("observed",ho,lo,1),("excess",hp-ho,lp-lo,2)]:
                    metric=f"{name}_homogenization_{form}"
                    expected=row[metric]
                    assert np.isclose(point,expected,atol=1e-6 if scope=="m5" else 1e-10,equal_nan=True), (context,entrant,metric,point,expected)
                    low,high,se,status=jackknife_interval(point,leave,bound)
                    results.append(dict(scope=scope,cell_line=context,entrant_id=entrant,metric=metric,estimate=point,
                                        ci_low=low,ci_high=high,jackknife_se=se,n_targets=len(predicted),status=status))
            print(f"同质化区间完成: {scope} {context} {entrant}",flush=True)
    path=OUT/"uncertainty/homogenization_intervals.tsv";write(pd.DataFrame(results),path)
    # 生成新版本带区间主表，既有点估计保持原值（含M5的历史精度）。
    extra=pd.DataFrame(results)
    outputs=[path]
    for scope,original in paths[:2]:
        table=read(original)
        for r in extra.loc[extra.scope.eq(scope)].itertuples():
            mask=table.cell_line.eq(r.cell_line)&table.entrant_id.eq(r.entrant_id)
            for suffix,val in [("ci_low",r.ci_low),("ci_high",r.ci_high),("jackknife_status",r.status)]:
                table.loc[mask,r.metric+"_"+suffix]=val
        new=OUT/("m4" if scope=="m4" else "m5")/original.name.replace(".tsv","_with_uncertainty.tsv")
        write(table,new);outputs.append(new)
    manifest("uncertainty",outputs)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("step",choices=["depmap","migrate","uncertainty"])
    args=parser.parse_args()
    INPUTS[str(CONFIG.relative_to(ROOT))]=sha256_file(CONFIG)
    INPUTS[str(Path(__file__).relative_to(ROOT))]=sha256_file(Path(__file__))
    globals()[args.step]()


if __name__=="__main__":main()
