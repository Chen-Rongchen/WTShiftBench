"""Run independent fixed-seed CellOT training, repeatability checks, and frozen scoring while retaining historical outputs."""

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import random
import runpy
import subprocess
import sys
import time


ROOT = Path(__file__).resolve().parents[2]
CONFIG = ROOT / "configs/revision/cellot_seed123_retrain_v1.json"


def sha(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def read(path):
    return json.loads(Path(path).read_text())


def write(path, data):
    Path(path).write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n")


def original_hash_check(cfg):
    hashes = read(ROOT / cfg["original_replay_manifest"])["inputs_sha256"]
    for path, expected in hashes.items():
        if path == "pixi.lock":
            # Do not rewrite the old recomputation manifest; record environment changes after missing PyTables separately.
            amendment = cfg["runtime_amendment"]
            blob = subprocess.check_output(["git", "show", f"{amendment['original_freeze_commit']}:pixi.lock"], cwd=ROOT)
            assert hashlib.sha256(blob).hexdigest() == expected == amendment["historical_lock_sha256"]
            assert sha(ROOT / path) == amendment["current_lock_sha256"]
            continue
        assert sha(ROOT / path) == expected, path
    return len(hashes)


def prepare(cfg):
    import yaml

    root = ROOT / cfg["output_root"]
    # New training must not reuse an existing cache: the original runner treats existing models as complete.
    root.mkdir(parents=True, exist_ok=False)
    original_hash_check(cfg)
    jobs = []

    def stage(context, item, directory, kind):
        directory.mkdir(parents=True)
        original_dir = (ROOT / item["command_path"]).parent
        source_config = original_dir / "model-cellot/config.yaml"
        model_cfg = yaml.safe_load(source_config.read_text())
        assert model_cfg["training"]["n_iters"] == cfg["training"]["n_iters"]
        assert model_cfg["training"]["n_inner_iters"] == cfg["training"]["n_inner_iters"]
        assert model_cfg["optim"]["lr"] == cfg["training"]["learning_rate"]
        assert model_cfg["dataloader"]["batch_size"] == cfg["training"]["batch_size"]
        assert model_cfg["datasplit"].get("random_state", 0) == 0
        job = dict(context=context, target=item["target_gene"], kind=kind,
                   source_config=str(source_config.relative_to(ROOT)),
                   output=str((directory / "model-cellot").relative_to(ROOT)),
                   training_seed=cfg["training_seed"],
                   inputs_sha256={str(p.relative_to(ROOT)): sha(p) for p in
                                  [source_config, original_dir / "input.h5ad", original_dir / "features.txt"]})
        job_path = directory / "job.json"
        write(job_path, job)
        command = directory / "run_cellot_train.sh"
        command.write_text("#!/usr/bin/env bash\nset -euo pipefail\n"
                           "# Independent new training output; do not resume old caches. Run from the project root.\n"
                           "pixi run --environment cellot python scripts/revision/run_cellot_seeded_retrain.py "
                           f"job --job {job_path.relative_to(ROOT)}\n")
        return str(job_path.relative_to(ROOT)), str(command.relative_to(ROOT))

    for context in cfg["contexts"]:
        old = read(ROOT / cfg["original_staging_root"] / context / "staging_manifest.json")
        assert old["n_genes"] == cfg["genes_per_context"]
        assert len(old["staged_targets"]) == cfg["targets_per_context"]
        staged = []
        for item in old["staged_targets"]:
            target = item["target_gene"]
            path, command = stage(context, item, root / "full" / context / target, "full")
            jobs.append(path)
            staged.append(dict(item, command_path=command))
            if context == cfg["pilot"]["context"] and target == cfg["pilot"]["target"]:
                for replicate in range(1, cfg["pilot"]["replicates"] + 1):
                    stage(context, item, root / "pilot" / f"repeat_{replicate}", "pilot")
        write(root / "full" / context / "staging_manifest.json",
              dict(old, stage=cfg["run_id"], training_seed=cfg["training_seed"], staged_targets=staged))
    inputs = {str(CONFIG.relative_to(ROOT)): sha(CONFIG),
              str(Path(__file__).resolve().relative_to(ROOT)): sha(__file__),
              "pixi.lock": sha(ROOT / "pixi.lock")}
    for path in jobs:
        inputs.update(read(ROOT / path)["inputs_sha256"])
        inputs[path] = sha(ROOT / path)
    for path in sorted((root / "pilot").glob("*/job.json")):
        inputs[str(path.relative_to(ROOT))] = sha(path)
    source = Path(cfg["source_root"])
    revision = subprocess.check_output(["git", "-C", str(source), "rev-parse", "HEAD"], text=True).strip()
    assert revision == cfg["source_revision"]
    dirty = subprocess.check_output(["git", "-C", str(source), "status", "--porcelain"], text=True)
    assert not dirty
    write(root / "input_manifest.json", dict(status="Pretraining inputs frozen", jobs=jobs,
          inputs_sha256=inputs, source_revision=revision, original_input_hashes_checked=671,
          created_utc=datetime.now(timezone.utc).isoformat()))
    print(f"Prepared {len(jobs)} new formal jobs across two contexts plus two repeatability trials; no training run yet.")


def worker(cfg, job_path):
    import numpy as np
    import torch
    # The first pilot failed writing step0 logs; verify this required dependency before creating training directories.
    import tables

    job = read(job_path)
    out = ROOT / job["output"]
    if out.exists():
        raise RuntimeError(f"Refusing to resume RNG-incomplete training in existing output: {out}")
    for path, expected in job["inputs_sha256"].items():
        assert sha(ROOT / path) == expected, path
    assert os.environ["PYTHONHASHSEED"] == str(cfg["training_seed"])
    sys.path.insert(0, cfg["source_root"])
    random.seed(cfg["training_seed"])
    np.random.seed(cfg["training_seed"])
    torch.manual_seed(cfg["training_seed"])
    torch.set_num_threads(cfg["runtime"]["torch_threads"])
    torch.set_num_interop_threads(cfg["runtime"]["torch_interop_threads"])
    torch.use_deterministic_algorithms(True)
    started = time.monotonic()
    sys.argv = [str(Path(cfg["source_root"]) / "scripts/train.py"),
                "--outdir", str(out), "--config", str(ROOT / job["source_config"])]
    runpy.run_path(sys.argv[0], run_name="__main__")
    assert (out / "cache/status").read_text() == "done"
    # Upstream local checkpoints contain NumPy scalars; load only files produced by this process's new training.
    state = torch.load(out / "cache/last.pt", weights_only=False, map_location="cpu")
    assert state["step"] == cfg["training"]["n_iters"] - 1
    outputs = {str(p.relative_to(ROOT)): sha(p) for p in
               [out / "cache/model.pt", out / "cache/last.pt", out / "config.yaml"]}
    write(out.parent / "completed.json", dict(context=job["context"], target=job["target"],
          kind=job["kind"], training_seed=cfg["training_seed"], torch_initial_seed=torch.initial_seed(),
          deterministic_algorithms=torch.are_deterministic_algorithms_enabled(), device="cpu",
          torch_threads=torch.get_num_threads(), job_sha256=sha(job_path),
          package_versions=dict(torch=torch.__version__, numpy=np.__version__, pytables=tables.__version__, python=sys.version),
          last_step=int(state["step"]), elapsed_seconds=time.monotonic() - started,
          outputs_sha256=outputs, completed_utc=datetime.now(timezone.utc).isoformat()))


def run_job(cfg, job_path):
    job_path = Path(job_path)
    completed = job_path.parent / "completed.json"
    # Reuse only verified completed jobs from this new execution; a best checkpoint alone does not prove1000 steps.
    if completed.exists():
        record = read(completed)
        assert record["job_sha256"] == sha(job_path)
        for path, expected in record["outputs_sha256"].items():
            assert sha(ROOT / path) == expected, path
        return record
    env = dict(os.environ, PYTHONHASHSEED=str(cfg["training_seed"]),
               OMP_NUM_THREADS="1", MKL_NUM_THREADS="1", OPENBLAS_NUM_THREADS="1",
               CUDA_VISIBLE_DEVICES="")
    command = [sys.executable, str(Path(__file__).resolve()), "worker", "--job", str(job_path)]
    with (job_path.parent / "training.log").open("w") as log:
        subprocess.run(command, cwd=ROOT, env=env, stdout=log, stderr=subprocess.STDOUT, check=True)
    return read(completed)


def state_equal(left, right):
    import torch

    if isinstance(left, torch.Tensor):
        assert torch.equal(left, right)
    elif isinstance(left, dict):
        assert left.keys() == right.keys()
        for key in left:
            state_equal(left[key], right[key])
    elif isinstance(left, (tuple, list)):
        assert len(left) == len(right)
        for a, b in zip(left, right):
            state_equal(a, b)
    else:
        assert left == right


def pilot(cfg):
    import functools
    import numpy as np
    import torch

    root = ROOT / cfg["output_root"]
    for replicate in [1, 2]:
        record = run_job(cfg, root / "pilot" / f"repeat_{replicate}" / "job.json")
        print(f"Trial{replicate}/2 completed: {record['elapsed_seconds']:.1f} seconds", flush=True)
    dirs = [root / "pilot" / f"repeat_{i}" / "model-cellot" for i in [1, 2]]
    for name in ["model.pt", "last.pt"]:
        states = [torch.load(p / "cache" / name, map_location="cpu", weights_only=False) for p in dirs]
        state_equal(*states)
    sys.path.insert(0, cfg["source_root"])
    torch.load = functools.partial(torch.load, weights_only=False)
    from cellot.utils.evaluate import load_conditions

    vectors = []
    for directory in dirs:
        control, _, prediction = load_conditions(directory, where="data_space", setting="iid")
        vector = prediction.to_df().mean(axis=0) - control.mean(axis=0)
        vector.to_csv(directory.parent / "predicted_shift.tsv", sep="\t", header=["shift"])
        vectors.append(vector.to_numpy())
    assert np.array_equal(*vectors)
    write(root / "pilot_comparison.json", dict(passed=True, context=cfg["pilot"]["context"],
          target=cfg["pilot"]["target"], seed=123, best_and_last_states_exactly_equal=True,
          predicted_shift_exactly_equal=True, max_abs_difference=float(np.abs(vectors[0]-vectors[1]).max()),
          scope="Same-seed repeatability check, not cross-seed robustness"))
    print("Repeatability passed: complete best/last states and exported shifts match exactly.", flush=True)


def full(cfg):
    root = ROOT / cfg["output_root"]
    assert read(root / "pilot_comparison.json")["passed"]
    manifest = read(root / "input_manifest.json")
    for path, expected in manifest["inputs_sha256"].items():
        assert sha(ROOT / path) == expected, path
    rows = []
    with ThreadPoolExecutor(max_workers=cfg["runtime"]["max_workers"]) as pool:
        futures = [pool.submit(run_job, cfg, ROOT / path) for path in manifest["jobs"]]
        try:
            for future in as_completed(futures):
                row = future.result()
                rows.append(row)
                write(root / "training_progress.json", dict(completed=len(rows), total=94, runs=rows))
                print(f"{len(rows)}/94 {row['context']} {row['target']} completed in {row['elapsed_seconds']:.1f} seconds", flush=True)
        except Exception:
            for future in futures:
                future.cancel()
            raise
    for context in cfg["contexts"]:
        command = [sys.executable, str(ROOT / "scripts/models/cellot/export_cellot_hcc_predicted_shift.py"),
                   "--cell-line", context, "--staging-root", str(root / "full"),
                   "--outdir", str(root / "predictions"), "--cellot-source", cfg["source_root"]]
        with (root / f"export_{context}.log").open("w") as log:
            subprocess.run(command, cwd=ROOT, stdout=log, stderr=subprocess.STDOUT, check=True)
    original_hash_check(cfg)
    write(root / "training_complete.json", dict(status="All94 new fits and prediction exports completed across two contexts",
          contexts=cfg["contexts"], n_fits=94, seed=123, original_data_models_predictions_unchanged=True,
          runtime_amendment=cfg["runtime_amendment"],
          completed_utc=datetime.now(timezone.utc).isoformat()))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=["prepare", "pilot", "full", "job", "worker"])
    parser.add_argument("--job", type=Path)
    args = parser.parse_args()
    cfg = read(CONFIG)
    if args.mode == "worker":
        worker(cfg, args.job)
    elif args.mode == "job":
        run_job(cfg, args.job)
    else:
        # Training uses committed registrations/scripts; no unrecorded setting changes after observing new outputs.
        if args.mode != "prepare":
            for path in [CONFIG, Path(__file__).resolve()]:
                committed = subprocess.check_output(["git", "show", f"HEAD:{path.relative_to(ROOT)}"], cwd=ROOT)
                assert committed == path.read_bytes(), path
        {"prepare": prepare, "pilot": pilot, "full": full}[args.mode](cfg)


if __name__ == "__main__":
    main()
