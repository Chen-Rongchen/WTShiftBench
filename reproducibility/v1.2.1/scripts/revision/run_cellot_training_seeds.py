"""按独立amendment改变训练seed，复用已验证worker，不触碰原模型。"""
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import subprocess
import sys

from scripts.revision import run_cellot_seeded_retrain as base

ROOT=Path(__file__).resolve().parents[2]
CONFIG=ROOT/"configs/revision/amendment_011_cellot_training_seeds.json"


def configuration(seed,config_path=CONFIG):
    a=json.loads(config_path.read_text())
    cfg=json.loads((ROOT/a["base_registration"]).read_text())
    assert seed in a["additional_seeds"]
    cfg.update(training_seed=seed,run_id=f"cellot_hcc_seed{seed}_sensitivity_v1",
               output_root=f"{a['output_root']}/seed{seed}")
    cfg["pilot"]["replicates"]=0
    return a,cfg


def run_job(seed,path,config_path=CONFIG):
    a,cfg=configuration(seed,config_path)
    path=ROOT/path
    done=path.parent/"completed.json"
    if done.exists():
        record=json.loads(done.read_text())
        assert record["job_sha256"]==base.sha(path)
        assert record["training_seed"]==record["torch_initial_seed"]==seed
        for p,h in record["outputs_sha256"].items():assert base.sha(ROOT/p)==h,p
        return record
    env=dict(os.environ,PYTHONHASHSEED=str(seed),OMP_NUM_THREADS="1",MKL_NUM_THREADS="1",
             OPENBLAS_NUM_THREADS="1",CUDA_VISIBLE_DEVICES="")
    command=[sys.executable,str(Path(__file__).resolve()),"worker","--seed",str(seed),"--job",str(path),"--config",str(config_path)]
    with (path.parent/"training.log").open("w") as log:
        subprocess.run(command,cwd=ROOT,env=env,stdout=log,stderr=subprocess.STDOUT,check=True)
    return json.loads(done.read_text())


def full(config_path=CONFIG):
    a=json.loads(config_path.read_text());jobs=[]
    for p in [config_path,Path(__file__).resolve()]:
        assert subprocess.check_output(["git","show",f"HEAD:{p.relative_to(ROOT)}"],cwd=ROOT)==p.read_bytes(),p
    for seed in a["additional_seeds"]:
        _,cfg=configuration(seed,config_path);root=ROOT/cfg["output_root"]
        if not root.exists():
            base.CONFIG=config_path
            base.prepare(cfg)
            base.write(root/"execution_configuration.json",cfg)
            for job in root.glob("full/*/*/job.json"):
                job.with_name("run_cellot_train.sh").write_text(
                    "#!/usr/bin/env bash\nset -euo pipefail\n# 单项执行显式使用本seed注册，不调用seed123默认入口。\n"
                    f"pixi run --environment cellot python scripts/revision/run_cellot_training_seeds.py job --seed {seed} --config {config_path} --job {job}\n")
        registered=base.read(root/"input_manifest.json")
        for p,h in registered["inputs_sha256"].items():assert base.sha(ROOT/p)==h,p
        jobs.extend((seed,p) for p in registered["jobs"])
    records=[];out=ROOT/a["output_root"]
    with ThreadPoolExecutor(max_workers=a["max_parallel_jobs"]) as pool:
        futures=[pool.submit(run_job,seed,path,config_path) for seed,path in jobs]
        for future in as_completed(futures):
            row=future.result();records.append(row)
            base.write(out/"training_progress.json",dict(completed=len(records),total=len(jobs),runs=records))
            print(f"{len(records)}/{len(jobs)} seed={row['training_seed']} {row['context']} {row['target']} 完成",flush=True)
    for seed in a["additional_seeds"]:
        _,cfg=configuration(seed,config_path);root=ROOT/cfg["output_root"]
        for context in cfg["contexts"]:
            command=[sys.executable,str(ROOT/"scripts/models/cellot/export_cellot_hcc_predicted_shift.py"),
                     "--cell-line",context,"--staging-root",str(root/"full"),"--outdir",str(root/"predictions"),
                     "--cellot-source",cfg["source_root"]]
            with (root/f"export_{context}.log").open("w") as log:
                subprocess.run(command,cwd=ROOT,stdout=log,stderr=subprocess.STDOUT,check=True)
        base.write(root/"training_complete.json",dict(seed=seed,n_fits=94,contexts=cfg["contexts"],
                   completed_utc=datetime.now(timezone.utc).isoformat()))
    base.write(out/"training_complete.json",dict(seeds=a["additional_seeds"],n_fits=len(records),
               completed_utc=datetime.now(timezone.utc).isoformat(),formal_seed=123))


if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode",choices=["full","job","worker"])
    parser.add_argument("--seed",type=int)
    parser.add_argument("--job",type=Path)
    parser.add_argument("--config",type=Path,default=CONFIG)
    args=parser.parse_args()
    config_path=args.config.resolve()
    if args.mode=="worker":base.worker(configuration(args.seed,config_path)[1],args.job)
    elif args.mode=="job":run_job(args.seed,args.job,config_path)
    else:full(config_path)
