"""A013: Score training/feature randomness under fixed definitions without modifying formal results."""
import argparse
import copy
import json
from pathlib import Path

import numpy as np
import pandas as pd

from scripts.revision.run_cellot_seeded_retrain import read,sha,write
from wtbench.hcc_prediction_export import align_prediction_to_contract,load_axis_membership
from wtbench.revision_metric_validity import contract_axes,validate_contract_matrix,score_context
from wtbench.revision_hcc_audit import bh_qvalues,endpoint_label_permutation_pvalue,_derived_seed
from wtbench.revision_finalization import h_leave_one,jackknife_interval

ROOT=Path(__file__).resolve().parents[2]
CONFIG=ROOT/"configs/revision/amendment_013_other_model_seeds.json"


def score(predicted,observed,endpoint,context,entrant,spec,inference):
    targets,row=score_context(prediction=predicted,observed=observed,endpoint=endpoint,
        cell_line=context,entrant_id=entrant,reference_type="",reference_seed=None,config=spec)
    row["endpoint_alignment_label_permutation_pvalue"]=endpoint_label_permutation_pvalue(
        targets.predicted_shift_mean_abs.to_numpy(float),targets.depmap_gene_dependency.to_numpy(float),
        permutations=inference["endpoint_label_permutations"],seed=_derived_seed(inference["endpoint_label_seed"],entrant,context))
    for centered in [False,True]:
        form="centered" if centered else "uncentered"
        hp,lp=h_leave_one(predicted.to_numpy(float),centered)
        ho,lo=h_leave_one(observed.to_numpy(float),centered)
        for name,point,loo,bound in [("predicted",hp,lp,1),("observed",ho,lo,1),("excess",hp-ho,lp-lo,2)]:
            key=f"{name}_homogenization_{form}"
            assert np.isclose(point,row[key],atol=1e-10,equal_nan=True)
            row[key+"_ci_low"],row[key+"_ci_high"],_,_=jackknife_interval(point,loo,bound)
    return targets,row


def save(out,rows,targets,inputs,family):
    table=pd.DataFrame(rows)
    for p,q in [("endpoint_alignment_label_permutation_pvalue","endpoint_alignment_permutation_qvalue_bh"),
                ("target_identity_label_permutation_pvalue","target_identity_permutation_qvalue_bh")]:
        table[q]=bh_qvalues(table[p])
    table["inference_family"]=family
    table.to_csv(out/"context_metrics.tsv",sep="\t",index=False,na_rep="NA")
    pd.concat(targets).to_csv(out/"target_metrics.tsv.gz",sep="\t",index=False,na_rep="NA")
    write(out/"scoring_manifest.json",dict(amendment="A013",scope=family,
        inputs_sha256={str(p.relative_to(ROOT)):sha(p) for p in inputs},
        outputs_sha256={str(p.relative_to(ROOT)):sha(p) for p in [out/"context_metrics.tsv",out/"target_metrics.tsv.gz"]}))


def hcc():
    cfg=read(CONFIG);root=ROOT/cfg["output_root"]
    done=read(root/"training_complete.json")
    assert done["completed"]==18
    out=ROOT/"reports/revision/finalization_v2/other_training_seeds";out.mkdir(parents=True,exist_ok=True)
    axispath=ROOT/"reports/truth_driven_bridge/master_atlas/shared_target_axis_membership.tsv"
    axis=load_axis_membership(axispath);targets,genes=contract_axes(axis)
    specpath=ROOT/"configs/revision/revision_metric_spec_v1.json"
    hccpath=ROOT/"configs/revision/revision_hcc_full_audit_v1.json"
    spec=read(specpath);hcccfg=read(hccpath)
    ep=ROOT/hcccfg["inputs"]["endpoint_object"];endpoint=pd.read_csv(ep,sep="\t")
    rows=[];target_rows=[];inputs=[CONFIG,Path(__file__).resolve(),specpath,hccpath,ep,axispath,root/"input_manifest.json"]
    checks=[]
    for model in cfg["training_models"]:
        for context in cfg["contexts"]:
            records=[read(root/model/f"seed{s}"/context/"completed.json") for s in cfg["training_seeds"]]
            assert len({r["split_sha256"] for r in records})==1,(model,context)
            assert len({r["initial_state_sha256"] for r in records})==3,(model,context)
            checks.append(dict(model=model,context=context,same_split=True,distinct_initializations=True))
            for record in records:
                seed=record["training_seed"]
                predpath=ROOT/record["prediction_path"]
                assert sha(predpath)==record["prediction_sha256"]
                aligned=align_prediction_to_contract(pd.read_csv(predpath,sep="\t"),axis)
                entrant=f"{model}_training_seed{seed}_sensitivity"
                aligned_path=out/f"{entrant}_{context}_predicted_shift.tsv.gz";aligned.to_csv(aligned_path,sep="\t",index=False)
                pred=validate_contract_matrix(aligned,target_order=targets,gene_order=genes,matrix_name=entrant)
                obspath=ROOT/f"reports/revision/m3_metric_validity/observed_shift_{context}.tsv.gz"
                obs=validate_contract_matrix(pd.read_csv(obspath,sep="\t"),target_order=targets,gene_order=genes,matrix_name=context)
                target,row=score(pred,obs,endpoint.loc[endpoint.cell_line.eq(context)],context,entrant,spec,hcccfg["inference"])
                row.update(training_seed=seed,model_family=model,entrant_role="training_seed_sensitivity",scored_target_held_out=False)
                target["training_seed"]=seed;rows.append(row);target_rows.append(target)
                inputs.extend([predpath,obspath,aligned_path,root/model/f"seed{seed}"/context/"completed.json"])
                print(f"Scoring completed {model} {context} seed={seed}",flush=True)
    write(out/"fixed_split_verification.json",dict(checks=checks))
    save(out,rows,target_rows,inputs,"A013_eighteen_HCC_training_sensitivity_outputs")


def features(prepare_only=False):
    from wtbench.revision_m5_audit import load_contract_npz,save_contract_npz,load_geneformer_features,geneformer_ridge_features,chargram_features,ridge_press_loo
    cfgpath=ROOT/"configs/revision/revision_m5_full_audit_v1.json";cfg=read(cfgpath)
    out=ROOT/"reports/revision/finalization_v2/replogle_feature_seeds";out.mkdir(parents=True,exist_ok=True)
    obspath=ROOT/"data/predictions/revision_m5_replogle/observed_shift_contract.npz"
    obs=load_contract_npz(obspath);targets=obs.index.tolist()
    ep=ROOT/cfg["inputs"]["endpoint_object"];endpoint=pd.read_csv(ep,sep="\t")
    endpoint["context_role"]=cfg["contract"]["context_role"]
    specpath=ROOT/cfg["metric_spec"];spec=copy.deepcopy(read(specpath))
    spec["inference"].update({k:cfg["inference"][k] for k in ["bootstrap_replicates","bootstrap_seed","target_identity_permutations","target_identity_seed"]})
    embeddingpath=out/"fixed_geneformer_features.npz"
    if prepare_only:
        embedding=load_geneformer_features(cfg,targets)
        np.savez_compressed(embeddingpath,targets=np.asarray(targets),values=embedding)
        write(out/"feature_preparation.json",dict(sha256=sha(embeddingpath),shape=list(embedding.shape),
            source="Fixed target embeddings from the specified Geneformer checkpoint; extraction only in the geneformer Pixi environment, without training",config_sha256=sha(cfgpath)))
        return
    with np.load(embeddingpath,allow_pickle=False) as arrays:
        assert arrays["targets"].tolist()==targets
        embedding=arrays["values"]
    assert sha(embeddingpath)==read(out/"feature_preparation.json")["sha256"]
    inputs=[CONFIG,Path(__file__).resolve(),cfgpath,obspath,ep,specpath,embeddingpath,ROOT/"src/wtbench/revision_m5_audit.py"]
    rows=[];target_rows=[]
    for entrant in cfg["formal_entrants"]:
        if entrant["method"]!="ridge_press_loo":continue
        for seed in [123,124,125]:
            if entrant["feature_source"]=="geneformer_embedding_pca":
                feature=geneformer_ridge_features(embedding,n_components=entrant["n_components"],seed=seed)
            else:
                feature=chargram_features(targets,ngram_min=entrant["ngram_min"],ngram_max=entrant["ngram_max"],n_components=entrant["n_components"],seed=seed)
            model=f"{entrant['model_id']}_feature_seed{seed}"
            pred=pd.DataFrame(ridge_press_loo(feature,obs.to_numpy(float),ridge_lambda=entrant["ridge_lambda"]),index=obs.index,columns=obs.columns)
            path=out/f"{model}_predicted_shift.npz";save_contract_npz(pred,path);inputs.append(path)
            # As in formal M5, read the saved float32 predictions before scoring.
            target,row=score(load_contract_npz(path),obs,endpoint,cfg["contract"]["context"],model,spec,cfg["inference"])
            row.update(feature_seed=seed,base_model_id=entrant["model_id"],entrant_role="feature_seed_sensitivity",scored_target_held_out=True)
            target["feature_seed"]=seed;rows.append(row);target_rows.append(target)
            print(f"Scoring completed Replogle {model}",flush=True)
    save(out,rows,target_rows,inputs,"A013_six_Replogle_feature_sensitivity_outputs")


if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument("mode",choices=["hcc","features","prepare-features"])
    args=parser.parse_args()
    if args.mode=="hcc":hcc()
    else:features(prepare_only=args.mode=="prepare-features")
