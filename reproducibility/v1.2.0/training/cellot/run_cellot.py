"""Public CellOT staged-data training/replay entry; relocate paths only, retaining hyperparameters."""
import argparse
import functools
import hashlib
import json
import os
from pathlib import Path
import random
import runpy
import shutil
import subprocess
import sys

ROOT=Path(__file__).resolve().parent


def worker(args):
    import numpy as np
    import torch
    import yaml
    sys.path.insert(0,str(ROOT/"vendor/cellot"))
    assert os.environ["PYTHONHASHSEED"]==str(args.seed)
    random.seed(args.seed);np.random.seed(args.seed);torch.manual_seed(args.seed)
    torch.set_num_threads(1);torch.set_num_interop_threads(1)
    torch.use_deterministic_algorithms(True)
    staged=ROOT/"staged"/args.context/args.target
    cfg=yaml.safe_load((staged/"config.yaml").read_text())
    cfg["data"]["path"]=str(staged/"input.h5ad")
    cfg["data"]["features"]=str(staged/"features.txt")
    out=args.output.resolve()/f"seed{args.seed}"/args.context/args.target
    # Refuse to overwrite an existing stochastic trajectory; users can specify a new output directory.
    out.mkdir(parents=True,exist_ok=False)
    cfgpath=out/"relocated_config.yaml"
    cfgpath.write_text(yaml.safe_dump(cfg,sort_keys=False))
    model=out/"model-cellot"
    if args.mode=="train":
        sys.argv=[str(ROOT/"vendor/cellot/scripts/train.py"),"--outdir",str(model),"--config",str(cfgpath)]
        runpy.run_path(sys.argv[0],run_name="__main__")
    else:
        (model/"cache").mkdir(parents=True)
        shutil.copyfile(cfgpath,model/"config.yaml")
        shutil.copyfile(ROOT/"saved_models"/f"seed{args.seed}"/args.context/args.target/"model.pt",model/"cache/model.pt")
    torch.load=functools.partial(torch.load,weights_only=False)
    from cellot.utils.evaluate import load_conditions
    import pandas as pd
    controls,_,predicted=load_conditions(model,where="data_space",setting="iid")
    vector=predicted.to_df().mean(axis=0)-controls.mean(axis=0)
    expected=pd.read_csv(ROOT/"expected"/f"seed{args.seed}_{args.context}.tsv.gz",sep="\t",index_col=0)
    expected=expected.loc[args.target,vector.index].to_numpy(float)
    error=float(np.max(np.abs(vector.to_numpy(float)-expected)))
    vector.to_csv(out/"predicted_shift.tsv",sep="\t",header=["shift"])
    report=dict(mode=args.mode,seed=args.seed,context=args.context,target=args.target,
                maximum_absolute_difference=error,tolerance=1e-10,passed=error<=1e-10,
                scope="Verify only this target's staged-data-to-prediction path; not a new seed experiment or complete raw-data processing",
                torch=torch.__version__,numpy=np.__version__)
    (out/"verification.json").write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n")
    print(json.dumps(report,ensure_ascii=False),flush=True)
    assert report["passed"],report


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--mode",choices=["train","replay"],default="train")
    p.add_argument("--seed",type=int,choices=[123,124,125,126,127],required=True)
    p.add_argument("--context",choices=["HCC38","HCC1143"],required=True)
    p.add_argument("--target",help="Run all47 context targets if omitted")
    p.add_argument("--output",type=Path,default=ROOT/"recomputed")
    p.add_argument("--worker",action="store_true",help=argparse.SUPPRESS)
    args=p.parse_args()
    if args.worker:return worker(args)
    manifest=json.loads((ROOT/"training_archive_manifest.json").read_text())
    for r in manifest["files"]:
        assert hashlib.sha256((ROOT/r["path"]).read_bytes()).hexdigest()==r["sha256"],r["path"]
    targets=[args.target] if args.target else manifest["targets"][args.context]
    assert set(targets)<=set(manifest["targets"][args.context])
    env=dict(os.environ,PYTHONHASHSEED=str(args.seed),OMP_NUM_THREADS="1",MKL_NUM_THREADS="1",
             OPENBLAS_NUM_THREADS="1",CUDA_VISIBLE_DEVICES="")
    for target in targets:
        subprocess.run([sys.executable,str(Path(__file__).resolve()),"--worker","--mode",args.mode,
            "--seed",str(args.seed),"--context",args.context,"--target",target,"--output",str(args.output.resolve())],
            env=env,cwd=ROOT,check=True)


if __name__=="__main__":main()
