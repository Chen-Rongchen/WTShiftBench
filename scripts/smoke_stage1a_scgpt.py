from __future__ import annotations

import argparse

from wtbench.entrants.base import (
    add_smoke_config_argument,
    build_target_level_split_manifest,
    load_smoke_context,
    print_runtime_banner,
    write_json,
)
from wtbench.entrants.export import run_benchmark_postprocess
from wtbench.entrants.scgpt_adapter import ScGPTEntrant


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="运行 scGPT Stage 1A K562 single-seed smoke。")
    return add_smoke_config_argument(parser, "configs/entrants/scgpt_smoke.yaml")


def main() -> None:
    args = build_parser().parse_args()
    context = load_smoke_context(args.config)
    split_manifest = build_target_level_split_manifest(
        context.dataset_id,
        context.split_seed,
        heldout_fraction=float(context.runtime_config.get("heldout_fraction", 0.2)),
    )
    print_runtime_banner(context)
    entrant = ScGPTEntrant(context)
    result = entrant.run_smoke(split_manifest)
    hooks = run_benchmark_postprocess(
        dataset_id=context.dataset_id,
        model_id=context.entrant_name,
        prediction_path=result["prediction_path"],
        output_dir=context.output_dir,
        do_validate_contract=bool(context.raw_config.get("do_validate_contract", True)),
        do_ingest=bool(context.raw_config.get("do_ingest", True)),
        do_align=bool(context.raw_config.get("do_align", True)),
    )
    write_json(context.output_dir / "benchmark_hooks.json", hooks)
    print(f"split_train_targets={len(split_manifest.train_targets)}")
    print(f"split_heldout_targets={len(split_manifest.heldout_targets)}")
    print(f"target_gene_vocabulary_coverage={result['feature_manifest'].get('heldout_vocab_coverage')}")
    print(f"predicted_shift_path={result['prediction_path']}")


if __name__ == "__main__":
    main()
