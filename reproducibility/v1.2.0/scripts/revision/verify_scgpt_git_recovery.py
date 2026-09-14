"""Verify Git-pinned scGPT assets and recompute saved outputs without rescoring or overwriting historical predictions."""

import argparse
import ast
import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
import torch

from scripts.pipeline import scgpt_hcc_predictions as historical_runner
from scripts.pipeline.lm_g_scgpt_ridge_hcc_predictions import predict_leave_one_out_external_ridge


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "docs/revision_scgpt_git_recovery"
# Fix tolerances before inspecting differences; numerical reproduction is distinct from historical byte identity.
RTOL, ATOL = 1e-6, 1e-8
KERNEL_REVISION = "505ee4533af368fc0cd4dda5e54a35820bc36693"
KERNEL_PATH = "scripts/stage1a/adapters/common/runtime.py"


def digest(path):
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def git_blob(data):
    return hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()


def compare_values(rebuilt, historical):
    assert rebuilt.index.equals(historical.index)
    assert rebuilt.columns.equals(historical.columns)
    left = rebuilt.to_numpy(dtype=np.float64)
    right = historical.to_numpy(dtype=np.float64)
    difference = left - right
    return dict(
        n_values=int(left.size),
        max_abs_difference=float(np.abs(difference).max()),
        rmse_difference=float(np.sqrt(np.mean(difference ** 2))),
        exact_numeric_equal=bool(np.array_equal(left, right)),
        within_frozen_tolerance=bool(np.allclose(left, right, rtol=RTOL, atol=ATOL)),
    )


def historical_kernel_reference():
    # Use the original function as an independent control; the production helper restores its CPU branch without runtime replacement.
    source = subprocess.check_output(["git", "show", f"{KERNEL_REVISION}:{KERNEL_PATH}"], cwd=ROOT)
    parsed = ast.parse(source)
    function = next(node for node in parsed.body
                    if isinstance(node, ast.FunctionDef) and node.name == "cosine_kernel_predict")
    namespace = {"np": np, "torch": torch}
    exec(compile(ast.Module(body=[function], type_ignores=[]),
                 f"git:{KERNEL_REVISION}:{KERNEL_PATH}", "exec"), namespace)
    return namespace["cosine_kernel_predict"], dict(commit=KERNEL_REVISION, path=KERNEL_PATH,
                blob=git_blob(source), source_sha256=hashlib.sha256(source).hexdigest(),
                lines=[function.lineno, function.end_lineno],
                policy="Restore the historical CPU branch in the project helper; M5 uses its separate softmax function and is unchanged")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--checkpoint-dir", type=Path, default=ROOT / "models/pretrained/scgpt_human")
    args = parser.parse_args()
    checkpoint = args.checkpoint_dir.resolve()
    provenance_path = OUT / "git_provenance.json"
    provenance = json.loads(provenance_path.read_text())
    upstream = provenance["upstream_git"]
    weight_path, vocab_path = checkpoint / "best_model.pt", checkpoint / "vocab.json"
    assert weight_path.stat().st_size == upstream["weight_size_bytes"]
    assert digest(weight_path) == upstream["weight_sha256"]
    assert git_blob(vocab_path.read_bytes()) == upstream["vocab_blob"]
    historical_registry = OUT / "historical_checkpoint_registry.yaml"
    assert git_blob(historical_registry.read_bytes()) == provenance["historical_source"]["blob"]
    git_source = subprocess.check_output([
        "git", "show",
        provenance["historical_source"]["commit"] + ":" + provenance["historical_source"]["path"],
    ], cwd=ROOT)
    assert git_source == historical_registry.read_bytes()
    vocab = json.loads(vocab_path.read_text())
    git_kernel, kernel_restoration = historical_kernel_reference()
    state = torch.load(weight_path, map_location="cpu", weights_only=True)
    embedding = state["encoder.embedding.weight"].detach().cpu().numpy()
    assert embedding.shape == (60697, 512)
    inputs = [weight_path, vocab_path, historical_registry, provenance_path, Path(__file__).resolve()]
    inputs += [ROOT / p for p in [
        "scripts/pipeline/scgpt_hcc_predictions.py",
        "scripts/pipeline/lm_g_scgpt_ridge_hcc_predictions.py",
        "src/wtbench/baselines/linear_utils.py",
        "scripts/stage1a/adapters/common/runtime.py",
    ]]
    results, outputs = [], []
    formal_manifest = json.loads((ROOT / "reports/revision/m4_hcc_full_audit/run_manifest.json").read_text())
    expected = {row["path"]: row["sha256"] for row in formal_manifest["inputs"]}
    inputs.append(ROOT / "reports/revision/m4_hcc_full_audit/run_manifest.json")
    for context in ["HCC38", "HCC1143"]:
        truth_path = ROOT / f"reports/revision/m3_metric_validity/observed_shift_{context}.tsv.gz"
        assert digest(truth_path) == expected[str(truth_path.relative_to(ROOT))]
        truth = pd.read_csv(truth_path, sep="\t").set_index("target_gene")
        inputs.append(truth_path)
        for kind, model in [("kernel", "scgpt_hcc_formal_v1"), ("ridge", "lm_g_scgpt_ridge_hcc_formal_v1")]:
            root = "scgpt_raw" if kind == "kernel" else "lm_g_scgpt_ridge_raw"
            historical_path = ROOT / f"data/predictions/{root}/{model}/{context}/predicted_shift.tsv.gz"
            scorer_path = ROOT / f"data/predictions/hcc_scorer_ready/{model}/{context}/predicted_shift.tsv.gz"
            historical = pd.read_csv(historical_path, sep="\t").set_index("target_gene")
            ordered_truth = truth.loc[historical.index, historical.columns].reset_index()
            inputs.extend([historical_path, scorer_path])
            assert digest(scorer_path) == expected[str(scorer_path.relative_to(ROOT))]
            if kind == "kernel":
                rebuilt, metadata = historical_runner.predict_leave_one_out_deltas(
                    ordered_truth, vocab=vocab, emb_weight=embedding.astype(np.float32),
                    top_k=4, fallback_policy="mean_train_real_shift",
                )
                # Compare the original Git function targetwise on actual HCC inputs to verify unchanged weighting rules.
                float_embedding = embedding.astype(np.float32)
                for target in historical.index:
                    refs = historical.index[historical.index != target]
                    expected_row = git_kernel(
                        float_embedding[vocab[target]],
                        float_embedding[[vocab[ref] for ref in refs]],
                        truth.loc[refs, historical.columns].to_numpy(dtype=np.float64),
                        4,
                    )
                    actual_row = rebuilt.set_index("target_gene").loc[target].to_numpy(dtype=np.float64)
                    assert np.array_equal(actual_row, expected_row)
            else:
                features = {target: embedding[vocab[target]].astype(np.float64) for target in historical.index}
                rebuilt, metadata = predict_leave_one_out_external_ridge(
                    ordered_truth, feature_lookup=features, n_components=32,
                    ridge_lambda=0.1, coverage_floor=0.8,
                )
            frame = rebuilt.set_index("target_gene")
            output = OUT / f"reconstructed_{model}_{context}.tsv.gz"
            rebuilt.to_csv(output, sep="\t", index=False)
            outputs.append(output)
            scorer = pd.read_csv(scorer_path, sep="\t").set_index("target_gene")
            for reference, reference_frame in [("raw_prediction", historical), ("frozen_scorer_input", scorer)]:
                row = dict(context=context, model_id=model, reference=reference,
                           **compare_values(frame, reference_frame.loc[frame.index, frame.columns]))
                results.append(row)
                print(json.dumps(row, ensure_ascii=False), flush=True)
            assert not metadata["fallback_targets"]
    summary_path = OUT / "prediction_comparison.tsv"
    pd.DataFrame(results).to_csv(summary_path, sep="\t", index=False)
    outputs.append(summary_path)
    passed = all(row["within_frozen_tolerance"] for row in results)
    manifest = dict(
        status="Numerical reproduction passed" if passed else "Differences found; recovery unconfirmed",
        completed_utc=datetime.now(timezone.utc).isoformat(),
        upstream_revision=upstream["revision"],
        historical_download_revision_was_recorded=False,
        checkpoint_directory=str(checkpoint.relative_to(ROOT)),
        embedding_shape=list(embedding.shape), vocab_entries=len(vocab),
        rtol=RTOL, atol=ATOL, prediction_comparisons=results,
        package_versions=dict(torch=torch.__version__, numpy=np.__version__, pandas=pd.__version__),
        kernel_restoration=kernel_restoration,
        inputs_sha256={str(p.relative_to(ROOT)): digest(p) for p in inputs},
        outputs_sha256={str(p.relative_to(ROOT)): digest(p) for p in outputs},
        model_rescoring=False, historical_predictions_overwritten=False,
        conclusion="Source registration matches the sole upstream weight history, and current files pass LFS/vocabulary hash checks. Numerical reproduction does not imply original download hashes were recorded or that historical predictions uniquely identify every parameter byte.",
    )
    (OUT / "verification_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
    if not passed:
        raise SystemExit("Differences exceed tolerance; retain candidates without overwriting historical outputs or relaxing tolerance.")


if __name__ == "__main__":
    main()
