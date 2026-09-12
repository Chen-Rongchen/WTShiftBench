"""A013固定数据/划分的CPA、scGen、GEARS训练敏感性，保留历史模型。"""
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import pickle
import random
import shutil
import subprocess
import sys
import time

from scripts.revision.run_cellot_seeded_retrain import sha, read, write

ROOT=Path(__file__).resolve().parents[2]
CONFIG=ROOT/"configs/revision/amendment_013_other_model_seeds.json"


def reset_seed(seed):
    import numpy as np
    import torch
    random.seed(seed);np.random.seed(seed);torch.manual_seed(seed)
    if torch.cuda.is_available():torch.cuda.manual_seed_all(seed)


def state_hash(module):
    h=hashlib.sha256()
    for name,tensor in sorted(module.state_dict().items()):
        h.update(name.encode());h.update(tensor.detach().cpu().numpy().tobytes())
    return h.hexdigest()


def scvi_run(model,context,seed,out,cfg):
    import numpy as np
    import torch
    import scvi
    if model=="cpa":
        import cpa
        from scripts.models.cpa import run_cpa_full_materialization as runner
        cls=cpa.CPA
    else:
        import scgen
        from scripts.models.scgen import run_scgen_hcc_smoke as runner
        cls=scgen.SCGEN
    # 原scvi默认划分seed为0；先设划分seed，再单独重置初始化/优化RNG。
    scvi.settings.seed=cfg[model]["fixed_scvi_split_seed"]
    reset_seed(seed);torch.set_num_threads(1)
    if model=="cpa":
        # CPA内部构造默认seed=0会覆盖外部seed；在真正初始化之前显式传入。
        original_init=cls.__init__
        def initialize_with_seed(self,*args,**kwargs):
            kwargs["seed"]=seed
            original_init(self,*args,**kwargs)
            scvi.settings.seed=cfg[model]["fixed_scvi_split_seed"]
            reset_seed(seed)
        cls.__init__=initialize_with_seed
    original=cls.train
    info={}
    def train_and_record(self,*args,**kwargs):
        info.update(initial_state_sha256=state_hash(self.module),torch_initial_seed=torch.initial_seed(),
                    scvi_split_seed=scvi.settings.seed,training_arguments=kwargs)
        assert info["torch_initial_seed"]==seed
        value=original(self,*args,**kwargs)
        split={key:np.asarray(getattr(self,key),dtype=int).tolist()
               for key in ["train_indices","validation_indices","test_indices"]}
        write(out/"split.json",split)
        info.update(split_sha256=sha(out/"split.json"),trained_state_sha256=state_hash(self.module),
                    actual_epochs=int(self.trainer.current_epoch))
        if model=="scgen":self.save(str(out/"checkpoint"),overwrite=False)
        reset_seed(123)
        return value
    cls.train=train_and_record
    if model=="cpa":
        runner.run_training(cell_line=context,seed=seed,outdir=out,
            **{k:cfg[model][k] for k in ["max_epochs","early_stopping_patience","batch_size","n_latent"]})
        prediction=out/f"predicted_shift_{context}.tsv.gz"
    else:
        sys.argv=[str(Path(runner.__file__)),"--cell-line",context,"--seed",str(seed),"--outdir",str(out),
                  "--max-targets","0","--max-epochs",str(cfg[model]["max_epochs"]),
                  "--batch-size",str(cfg[model]["batch_size"]),"--early-stopping-patience",str(cfg[model]["early_stopping_patience"])]
        runner.main();prediction=out/context/"predicted_shift.tsv.gz"
    info["scvi_version"]=scvi.__version__
    return prediction,info


def gears_run(context,seed,out,cfg):
    import anndata as ad
    import numpy as np
    import pandas as pd
    import torch
    from gears import GEARS,PertData
    from scripts.stage1a.adapters.gears.build_predictions import build_identity_graph,predict_transcriptomes
    from wtbench.hcc_prediction_export import expected_target_and_gene_order
    recipe=read(ROOT/cfg["gears"]["recipe"]);runtime=recipe["runtime"]
    old=ROOT/"tmp/gears_hcc/gears_hcc_formal_v1"/context
    cache=out/"cache";cache.mkdir()
    for name in ["gene2go_all.pkl","gene_set.pkl"]:shutil.copyfile(old/name,cache/name)
    pdset=PertData(str(cache),gene_set_path=str(cache/"gene_set.pkl"),default_pert_graph=False)
    # 上游load只接受+形式的组合标签；直接恢复本项目已冻结的单基因processed对象。
    dataset=old/f"{context.lower()}_gears_hcc_formal_v1"
    pdset.dataset_name=dataset.name;pdset.dataset_path=str(dataset)
    pdset.adata=ad.read_h5ad(dataset/"perturb_processed.h5ad")
    with (dataset/"data_pyg/cell_graphs.pkl").open("rb") as handle:pdset.dataset_processed=pickle.load(handle)
    pdset.set_pert_genes()
    pdset.ctrl_adata=pdset.adata[pdset.adata.obs.condition.astype(str).eq("ctrl")]
    pdset.gene_names=pdset.adata.var.gene_name
    pdset.prepare_split(split="custom",split_dict_path=str(old/"custom_split.pkl"))
    reset_seed(seed);torch.set_num_threads(1)
    pdset.get_dataloader(batch_size=runtime["batch_size"],test_batch_size=runtime["batch_size"])
    pdset.dataloader.pop("test_loader",None)
    gp,wp=build_identity_graph(len(pdset.pert_names));gg,wg=build_identity_graph(pdset.adata.n_vars)
    device="cuda" if torch.cuda.is_available() else "cpu"
    model=GEARS(pdset,device=device,weight_bias_track=False)
    model.model_initialize(G_go=gp,G_go_weight=wp,G_coexpress=gg,G_coexpress_weight=wg)
    info=dict(initial_state_sha256=state_hash(model.model),torch_initial_seed=torch.initial_seed(),
              split_sha256=sha(old/"custom_split.pkl"),data_and_split_seed=123,
              graph_sha256=sha(old/f"{context.lower()}_gears_hcc_formal_v1/data_pyg/cell_graphs.pkl"))
    assert info["torch_initial_seed"]==seed
    model.train(epochs=runtime["epochs"],lr=runtime["lr"],weight_decay=runtime["weight_decay"])
    model.save_model(str(out/"checkpoint"))
    info["trained_state_sha256"]=state_hash(model.best_model)
    info["actual_epochs"]=runtime["epochs"]
    axis=pd.read_csv(ROOT/recipe["axis_membership_path"],sep="\t")
    targets,genes=expected_target_and_gene_order(axis)
    reset_seed(123)
    predicted=predict_transcriptomes(gears_model=model,target_order=targets,num_samples=runtime["prediction_num_samples"],device=device)
    formal=ad.read_h5ad(ROOT/recipe["formal_h5ad_root"]/f"{context}.h5ad")
    control=np.asarray(formal.X[formal.obs.is_control.to_numpy()].mean(axis=0)).ravel()
    positions=pd.Series(np.arange(pdset.adata.n_vars),index=pdset.adata.var.gene_name.astype(str))
    positions=positions[~positions.index.duplicated(keep="first")].loc[genes].to_numpy()
    rows=[{"target_gene":t,**dict(zip(genes,(predicted[t]-control)[positions]))} for t in targets]
    prediction=out/"predicted_shift.tsv.gz"
    pd.DataFrame(rows).to_csv(prediction,sep="\t",index=False)
    return prediction,info


def worker(model,context,seed):
    import numpy as np
    import torch
    cfg=read(CONFIG);root=ROOT/cfg["output_root"]
    out=root/model/f"seed{seed}"/context
    out.mkdir(parents=True,exist_ok=False)
    started=time.monotonic()
    if model=="gears":prediction,info=gears_run(context,seed,out,cfg)
    else:prediction,info=scvi_run(model,context,seed,out,cfg)
    info.update(model=model,context=context,training_seed=seed,inference_seed=123,
                runner_sha256=sha(Path(__file__).resolve()),
                prediction_path=str(prediction.relative_to(ROOT)),prediction_sha256=sha(prediction),
                elapsed_seconds=time.monotonic()-started,completed_utc=datetime.now(timezone.utc).isoformat(),
                package_versions=dict(torch=torch.__version__,numpy=np.__version__,python=sys.version),
                cuda_available=torch.cuda.is_available(),torch_threads=torch.get_num_threads(),
                deterministic_algorithms=torch.are_deterministic_algorithms_enabled(),
                scope="训练seed敏感性；GPU核可能非逐位确定，不声称历史运行的精确重现")
    info["checkpoint_hashes"]={str(p.relative_to(ROOT)):sha(p) for p in out.rglob("*") if p.is_file() and p.suffix in [".pt",".pkl"]}
    write(out/"completed.json",info)
    print(json.dumps(dict(model=model,context=context,seed=seed,status="completed")),flush=True)


def run_job(job,root):
    model,context,seed=job
    done=root/model/f"seed{seed}"/context/"completed.json"
    if done.exists():
        record=read(done);assert sha(ROOT/record["prediction_path"])==record["prediction_sha256"]
        return record
    logs=root/"logs";logs.mkdir(exist_ok=True)
    env=dict(os.environ,PYTHONHASHSEED=str(seed),OMP_NUM_THREADS="1",MKL_NUM_THREADS="1",OPENBLAS_NUM_THREADS="1")
    command=["pixi","run","--frozen","--environment",model,"python",str(Path(__file__).resolve()),
             "worker","--model",model,"--context",context,"--seed",str(seed)]
    with (logs/f"{model}_{context}_seed{seed}.log").open("w") as log:
        subprocess.run(command,cwd=ROOT,env=env,stdout=log,stderr=subprocess.STDOUT,check=True)
    return read(done)


def full():
    cfg=read(CONFIG);root=ROOT/cfg["output_root"];root.mkdir(parents=True,exist_ok=True)
    for p in [CONFIG,Path(__file__).resolve()]:
        assert subprocess.check_output(["git","show",f"HEAD:{p.relative_to(ROOT)}"],cwd=ROOT)==p.read_bytes(),p
    paths=[CONFIG,ROOT/"configs/revision/amendment_014_seed_execution_fixes.json",Path(__file__).resolve(),ROOT/"pixi.lock",ROOT/cfg["gears"]["recipe"],
           ROOT/"scripts/models/cpa/run_cpa_full_materialization.py",ROOT/"scripts/models/scgen/run_scgen_hcc_smoke.py",
           ROOT/"scripts/stage1a/adapters/gears/build_predictions.py"]
    for context in cfg["contexts"]:
        paths.extend([ROOT/f"data/processed/cpa_hcc_formal/{context}.h5ad",ROOT/f"data/processed/hcc_gears_formal/{context}.h5ad"])
        old=ROOT/f"tmp/gears_hcc/gears_hcc_formal_v1/{context}"
        paths.extend(old/name for name in ["gene2go_all.pkl","gene_set.pkl","custom_split.pkl",
            f"{context.lower()}_gears_hcc_formal_v1/perturb_processed.h5ad",f"{context.lower()}_gears_hcc_formal_v1/data_pyg/cell_graphs.pkl"])
    manifest=root/"input_manifest.json"
    hashes={str(p.relative_to(ROOT)):sha(p) for p in paths}
    if manifest.exists():assert read(manifest)["inputs_sha256"]==hashes
    else:write(manifest,dict(amendment="A013",created_utc=datetime.now(timezone.utc).isoformat(),inputs_sha256=hashes))
    jobs=[(m,c,s) for m in cfg["training_models"] for s in cfg["training_seeds"] for c in cfg["contexts"]]
    records=[]
    with ThreadPoolExecutor(max_workers=cfg["max_parallel_gpu_jobs"]) as pool:
        futures=[pool.submit(run_job,j,root) for j in jobs]
        for future in as_completed(futures):
            record=future.result();records.append(record)
            write(root/"progress.json",dict(completed=len(records),total=len(jobs),runs=records))
            print(f"{len(records)}/{len(jobs)} {record['model']} {record['context']} seed={record['training_seed']}完成",flush=True)
    write(root/"training_complete.json",dict(completed=len(records),total=len(jobs),runs=records))


if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode",choices=["full","worker"])
    parser.add_argument("--model",choices=["cpa","scgen","gears"])
    parser.add_argument("--context",choices=["HCC38","HCC1143"])
    parser.add_argument("--seed",type=int,choices=[123,124,125])
    args=parser.parse_args()
    if args.mode=="full":full()
    else:worker(args.model,args.context,args.seed)
