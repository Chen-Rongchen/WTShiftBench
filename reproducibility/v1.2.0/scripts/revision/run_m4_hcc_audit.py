#!/usr/bin/env python
"""Run M4 revised HCC full audit."""

from __future__ import annotations

import argparse

from wtbench.revision_hcc_audit import PROJECT_ROOT, run_hcc_audit


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--config",
        default="configs/revision/revision_hcc_full_audit_v1.json",
    )
    parser.add_argument("--output-root", default=None)
    args = parser.parse_args()
    output_root = PROJECT_ROOT / args.output_root if args.output_root else None
    manifest = run_hcc_audit(PROJECT_ROOT / args.config, output_root)
    print(
        "M4 HCC audit completed: "
        f"formal={manifest['formal_model_contexts_scored']}, "
        f"diagnostic={manifest['diagnostic_model_contexts_scored']}"
    )


if __name__ == "__main__":
    main()
