"""Replay A013 CPA with the recorded recipe, supplying missing constructor load parameters without changing weights."""
import argparse
from pathlib import Path

import anndata as ad
import cpa
import numpy as np
import pandas as pd
import torch

from scripts.revision.run_cellot_seeded_retrain import read, sha, write
from scripts.revision.run_other_model_training_seeds import reset_seed, state_hash

ROOT=Path(__file__).resolve().parents[2]


def replay(context,seed):
    cfg=read(ROOT/"configs/revision/amendment_013_other_model_seeds.json")
    run=ROOT/cfg["output_root"]/"cpa"/f"seed{seed}"/context
    completed=read(run/"completed.json")
    checkpoint=run/f"checkpoint_{context}"
    original_hash=sha(checkpoint/"model.pt")
    assert original_hash==completed["checkpoint_hashes"][str((checkpoint/"model.pt").relative_to(ROOT))]
    payload=torch.load(checkpoint/"model.pt",map_location="cpu")
    recorded=payload["attr_dict"]["init_params_"]
    # Actual CPA parameters were fixed in A013 and the original run_training code.
    parameters=dict(n_latent=cfg["cpa"]["n_latent"],recon_loss="gauss",doser_type="logsigm",
                    n_hidden_encoder=128,n_layers_encoder=2,n_hidden_decoder=128,n_layers_decoder=2,seed=seed)
    assert recorded=={"kwargs":{},"non_kwargs":{}},recorded
    adata=ad.read_h5ad(ROOT/f"data/processed/cpa_hcc_formal/{context}.h5ad")
    adata.var_names_make_unique()
    torch.set_num_threads(1)
    # Native CPA load appends batch again to the saved covariate list, creating nonexistent triple-context labels.
    # Rebuild encoders/model with the original setup and strictly load saved tensors; do not modify training/checkpoint files.
    encoders=read(checkpoint/"CPA_info.json")
    cpa.CPA.pert_encoder=encoders["pert_encoder"]
    cpa.CPA.covars_encoder=encoders["covars_encoder"]
    cpa.CPA.pert_smiles_map=encoders.get("pert_smiles_map")
    cpa.CPA.setup_anndata(adata,perturbation_key="cpa_perturbation",control_group="control",
        dosage_key="cpa_dosage",batch_key="cpa_batch",categorical_covariate_keys=["cpa_context"],is_count_data=False)
    assert np.array_equal(payload["var_names"],adata.var_names.to_numpy())
    model=cpa.CPA(adata,**parameters)
    model.module.load_state_dict(payload["model_state_dict"],strict=True)
    model.is_trained_=True
    model.to_device("cuda:0" if torch.cuda.is_available() else "cpu")
    model.module.eval()
    assert state_hash(model.module)==completed["trained_state_sha256"]
    controls=adata[adata.obs.cpa_perturbation.eq("control")].copy()
    control_mean=np.asarray(controls.X.mean(axis=0)).ravel()
    targets=sorted(t for t in adata.obs.cpa_perturbation.unique() if t!="control")
    reset_seed(completed["inference_seed"])
    rows=[]
    for target in targets:
        counterfactual=controls.copy()
        counterfactual.obs["cpa_perturbation"]=target
        counterfactual.obs["cpa_dosage"]="1.0"
        cpa.CPA.setup_anndata(counterfactual,perturbation_key="cpa_perturbation",control_group="control",
            dosage_key="cpa_dosage",batch_key="cpa_batch",categorical_covariate_keys=["cpa_context"],is_count_data=False)
        model.predict(counterfactual,n_samples=1,return_mean=True)
        shift=counterfactual.obsm["CPA_pred"].mean(axis=0)-control_mean
        rows.append(shift)
    replayed=pd.DataFrame(rows,index=targets,columns=adata.var_names)
    expected=pd.read_csv(ROOT/completed["prediction_path"],sep="\t",index_col=0)
    assert replayed.index.equals(expected.index) and replayed.columns.equals(expected.columns)
    discrepancy=np.abs(replayed.to_numpy()-expected.to_numpy())
    tolerance=1e-5
    passed=bool(np.allclose(replayed.to_numpy(),expected.to_numpy(),atol=tolerance,rtol=0))
    assert sha(checkpoint/"model.pt")==original_hash
    out=ROOT/"reports/revision/other_model_training_seeds_v1/cpa_replay"
    out.mkdir(parents=True,exist_ok=True)
    write(out/f"{context}_seed{seed}.json",dict(context=context,seed=seed,passed=passed,
        checkpoint_sha256=original_hash,checkpoint_unchanged=True,trained_state_sha256=completed["trained_state_sha256"],
        stored_init_params=recorded,explicit_load_parameters=parameters,inference_seed=completed["inference_seed"],
        saved_encoder_sha256=sha(checkpoint/"CPA_info.json"),
        native_load_limitation="CPA's saved covariates already contain batch; native load appends it again, causing category mismatch. Reconstruct encoders once with the original setup and strictly load tensors",
        maximum_absolute_difference=float(discrepancy.max()),absolute_tolerance=tolerance,
        loader_sha256=sha(Path(__file__).resolve()),
        scope="Replay saved weights and JSON encoders to predictions; explicitly supply missing constructor metadata from the recorded recipe without changing checkpoints or claiming historical training reproduction"))
    assert passed,float(discrepancy.max())
    print(f"CPA {context} seed={seed} checkpoint replay passed, maximum difference={discrepancy.max():.3g}",flush=True)


if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--context",choices=["HCC38","HCC1143"],required=True)
    parser.add_argument("--seed",type=int,choices=[123,124,125],required=True)
    args=parser.parse_args();replay(args.context,args.seed)
