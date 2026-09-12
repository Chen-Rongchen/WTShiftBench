"""在已独立解压的CellOT包中回放全部470个权重，不新增训练。"""
import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
from pathlib import Path
import subprocess
import sys


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--workers", type=int, default=4)
    args = parser.parse_args()
    root, out = args.archive.resolve(), args.output.resolve()
    # 实际已有旧三seed验收；新验收单独落盘，禁止覆盖旧记录。
    out.mkdir(parents=True, exist_ok=False)
    manifest_path = root / "training_archive_manifest.json"
    manifest = json.loads(manifest_path.read_text())
    assert manifest["seeds"] == [123, 124, 125, 126, 127]
    jobs = [(seed, context) for seed in manifest["seeds"] for context in manifest["targets"]]

    def replay(job):
        seed, context = job
        log = out / f"seed{seed}_{context}.log"
        with log.open("w") as handle:
            subprocess.run(
                [sys.executable, str(root / "run_cellot.py"), "--mode", "replay",
                 "--seed", str(seed), "--context", context, "--output", str(out / "replayed")],
                cwd=root, stdout=handle, stderr=subprocess.STDOUT, check=True,
            )
        print(f"回放完成 seed={seed} context={context}", flush=True)

    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        list(pool.map(replay, jobs))
    records = [json.loads(p.read_text()) for p in sorted((out / "replayed").glob("*/*/*/verification.json"))]
    expected = {(s, c, t) for s, c in jobs for t in manifest["targets"][c]}
    assert {(r["seed"], r["context"], r["target"]) for r in records} == expected
    assert len(records) == 470 and all(r["passed"] for r in records)
    summary = dict(
        passed=True, checkpoint_replays=len(records), seeds=manifest["seeds"],
        maximum_absolute_difference=max(r["maximum_absolute_difference"] for r in records),
        tolerance=1e-10, training_manifest_sha256=hashlib.sha256(manifest_path.read_bytes()).hexdigest(),
        archive=str(root), execution_prefix=sys.prefix, public_download_verified=False,
        scope="本地独立目录全部470个checkpoint到预测回放；不是470项从头重训或公开下载验收",
        records=records,
    )
    (out / "cellot_replay_verification.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({k: v for k, v in summary.items() if k != "records"}, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
