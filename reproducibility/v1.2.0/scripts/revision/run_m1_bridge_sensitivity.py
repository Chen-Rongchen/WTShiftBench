#!/usr/bin/env python3
"""Run M1 bridge sampling-confounding audit."""

from __future__ import annotations

import argparse
from pathlib import Path

from wtbench.revision_bridge_sensitivity import PROJECT_ROOT, run


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--registry",
        type=Path,
        default=Path("configs/revision/revision_analysis_registry_v1.json"),
    )
    parser.add_argument(
        "--output-root",
        type=Path,
        default=Path("reports/revision/m1_bridge_confounding"),
    )
    args = parser.parse_args()
    registry = args.registry if args.registry.is_absolute() else PROJECT_ROOT / args.registry
    output_root = args.output_root if args.output_root.is_absolute() else PROJECT_ROOT / args.output_root
    manifest = run(registry, output_root)
    print(f"M1 completed: dual_context_endpoint_object_pass={manifest['dual_context_endpoint_object_pass']}")
    print(f"Results directory: {output_root}")


if __name__ == "__main__":
    main()
