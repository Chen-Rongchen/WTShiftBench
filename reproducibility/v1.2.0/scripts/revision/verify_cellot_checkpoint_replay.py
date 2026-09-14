"""Recompute formal HCC predictions from saved CellOT models without training, scoring, or overwriting historical results."""

import hashlib
import json
import pickletools
import re
import subprocess
import sys
import zipfile
from datetime import datetime, timezone
from pathlib import Path

import anndata
import numpy as np
import pandas as pd
import torch


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "docs/revision_cellot_replay"
STAGING = ROOT / "reports/model_eligibility/cellot_hcc_smoke"
SOURCE = Path("/tmp/wtko_cellot_install")
REVISION = "522d2b953da8ad244fcf36f64521487fdf763788"
MODEL = "cellot_hcc_formal_v1"
# Fix tolerances before inspecting replay; investigate excess discrepancies without automatic relaxation or retraining.
RTOL, ATOL = 1e-6, 1e-8
SOURCE_PATHS = [
    "scripts/train.py", "cellot/train/experiment.py", "cellot/train/train.py",
    "cellot/data/cell.py", "cellot/data/utils.py", "cellot/utils/evaluate.py",
    "cellot/utils/loaders.py", "cellot/models/cellot.py", "cellot/networks/icnns.py",
]


def digest(path):
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def checkpoint_seed_keys(path):
    # Inspect pickle strings statically without deserialization; model loading uses the existing local exporter.
    with zipfile.ZipFile(path) as archive:
        member = next(n for n in archive.namelist() if n.endswith("/data.pkl"))
        strings = [arg for op, arg, _ in pickletools.genops(archive.read(member))
                   if op.name in {"UNICODE", "BINUNICODE", "SHORT_BINUNICODE", "BINUNICODE8"}]
    return [s for s in strings if any(k in s.lower() for k in ("seed", "rng", "random_state"))]


def compare_frames(rebuilt, historical):
    assert rebuilt.index.equals(historical.index)
    assert rebuilt.columns.equals(historical.columns)
    left, right = rebuilt.to_numpy(dtype=float), historical.to_numpy(dtype=float)
    delta = left - right
    return dict(
        n_targets=len(rebuilt), n_genes=len(rebuilt.columns), n_values=int(left.size),
        max_abs_difference=float(np.abs(delta).max()),
        rmse_difference=float(np.sqrt(np.mean(delta ** 2))),
        exact_numeric_equal=bool(np.array_equal(left, right)),
        within_frozen_tolerance=bool(np.allclose(left, right, rtol=RTOL, atol=ATOL)),
    )


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    exporter = ROOT / "scripts/models/cellot/export_cellot_hcc_predicted_shift.py"
    formal_path = ROOT / "reports/revision/m4_hcc_full_audit/run_manifest.json"
    formal = json.loads(formal_path.read_text())
    frozen = {row["path"]: row["sha256"] for row in formal["inputs"]}
    actual_revision = subprocess.check_output(
        ["git", "-C", str(SOURCE), "rev-parse", "HEAD"], text=True).strip()
    assert actual_revision == REVISION
    upstream = {}
    for path in SOURCE_PATHS:
        blob = subprocess.check_output(["git", "-C", str(SOURCE), "show", f"{REVISION}:{path}"])
        assert (SOURCE / path).read_bytes() == blob
        upstream[path] = hashlib.sha256(blob).hexdigest()
    inputs = [Path(__file__).resolve(), exporter, formal_path, ROOT / "pixi.lock",
              ROOT / "scripts/env/prepare_cellot_source.py"]
    inventory, references = [], {}
    for context in ["HCC38", "HCC1143"]:
        manifest_path = STAGING / context / "staging_manifest.json"
        manifest = json.loads(manifest_path.read_text())
        inputs.append(manifest_path)
        assert len(manifest["staged_targets"]) == 47
        for item in manifest["staged_targets"]:
            command = ROOT / item["command_path"]
            directory = command.parent
            checkpoint = directory / "model-cellot/cache/model.pt"
            config = directory / "model-cellot/config.yaml"
            # Check whether actual formal commands/configs/checkpoints record a seed; do not fill gaps with defaults.
            mentions = [line for p in [command, config] for line in p.read_text().splitlines()
                        if re.search(r"seed|random_state|rng", line, re.I)]
            inventory.append(dict(context=context, target_gene=item["target_gene"],
                                  checkpoint=str(checkpoint.relative_to(ROOT)),
                                  command_or_config_seed_mentions=mentions,
                                  checkpoint_seed_keys=checkpoint_seed_keys(checkpoint)))
            inputs.extend([command, checkpoint, config, directory / "input.h5ad",
                           directory / "features.txt", directory / "task.yaml", directory / "model.yaml"])
        references[context] = {
            "historical_raw": ROOT / f"reports/model_eligibility/cellot_hcc_predictions/{context}/predicted_shift.tsv.gz",
            "frozen_scorer_input": ROOT / f"data/predictions/hcc_scorer_ready/{MODEL}/{context}/predicted_shift.tsv.gz",
        }
        for path in references[context].values():
            inputs.append(path)
        scorer = references[context]["frozen_scorer_input"]
        assert digest(scorer) == frozen[str(scorer.relative_to(ROOT))]
        inputs.append(references[context]["historical_raw"].parent / "export_report.json")
    hashes = {str(p.relative_to(ROOT)): digest(p) for p in inputs}
    record = dict(
        status="Inputs checked; prediction recomputation not yet complete", started_utc=datetime.now(timezone.utc).isoformat(),
        upstream_repository="https://github.com/bunnech/cellot", upstream_revision=REVISION,
        upstream_sources_sha256=upstream, rtol=RTOL, atol=ATOL,
        inputs_sha256=hashes, checkpoint_inventory=inventory,
        package_versions=dict(torch=torch.__version__, numpy=np.__version__, pandas=pd.__version__,
                              anndata=anndata.__version__),
        historical_training_seed=None, seed_123_confirmed=False,
        training_executed=False, model_scoring_executed=False,
        historical_predictions_overwritten=False,
    )
    manifest_out = OUT / "verification_manifest.json"
    manifest_out.write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n")
    comparisons, outputs, commands = [], [], []
    for context in ["HCC38", "HCC1143"]:
        command = [sys.executable, str(exporter), "--cell-line", context,
                   "--outdir", str(OUT / "predictions"), "--cellot-source", str(SOURCE)]
        log = OUT / f"export_{context}.log"
        print(f"Exporting {context} from saved checkpoints; no training.", flush=True)
        with log.open("w") as handle:
            subprocess.run(command, cwd=ROOT, stdout=handle, stderr=subprocess.STDOUT, check=True)
        commands.append(command)
        prediction = OUT / f"predictions/{context}/predicted_shift.tsv.gz"
        exported_path = prediction.parent / "export_report.json"
        rebuilt = pd.read_csv(prediction, sep="\t").set_index("target_gene")
        for name, path in references[context].items():
            historical = pd.read_csv(path, sep="\t").set_index("target_gene")
            row = dict(context=context, model_id=MODEL, reference=name,
                       **compare_frames(rebuilt, historical))
            comparisons.append(row)
            print(json.dumps(row, ensure_ascii=False), flush=True)
        before = json.loads((references[context]["historical_raw"].parent / "export_report.json").read_text())
        after = json.loads(exported_path.read_text())
        assert before["exported_targets"] == after["exported_targets"]
        outputs.extend([prediction, exported_path, log])
    changed_inputs = [p for p, expected in hashes.items() if digest(ROOT / p) != expected]
    assert not changed_inputs, changed_inputs
    comparison_path = OUT / "prediction_comparison.tsv"
    pd.DataFrame(comparisons).to_csv(comparison_path, sep="\t", index=False)
    outputs.append(comparison_path)
    passed = all(row["within_frozen_tolerance"] for row in comparisons)
    record.update(
        status="Checkpoint-to-formal-prediction numerical reproduction passed" if passed else "Differences exceed tolerance; investigation required",
        completed_utc=datetime.now(timezone.utc).isoformat(), commands=commands,
        prediction_comparisons=comparisons, historical_inputs_unchanged=True,
        evaluation_cell_counts_match=True,
        outputs_sha256={str(p.relative_to(ROOT)): digest(p) for p in outputs},
        conclusion="This check validates saved-model-to-prediction replay only; it does not recover the historical training seed or establish from-scratch reproduction or multi-seed stability.",
    )
    manifest_out.write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n")
    if not passed:
        raise SystemExit("Differences exceed tolerance; investigate before any retraining or replacement of historical results.")


if __name__ == "__main__":
    main()
