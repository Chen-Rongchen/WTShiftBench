#!/usr/bin/env python
"""运行 BIB 大修 M3 reference-control validation。"""

from __future__ import annotations

import argparse
from pathlib import Path

from wtbench.revision_metric_validity import PROJECT_ROOT, run_reference_validation


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--config",
        default="configs/revision/revision_metric_spec_v1.json",
    )
    parser.add_argument("--output-root", default=None)
    args = parser.parse_args()
    output_root = PROJECT_ROOT / args.output_root if args.output_root else None
    manifest = run_reference_validation(PROJECT_ROOT / args.config, output_root)
    print(
        "M3 reference validation 已完成："
        f"checks_passed={manifest['all_reference_checks_passed']}"
    )


if __name__ == "__main__":
    main()
