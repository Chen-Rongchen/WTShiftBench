from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

from wtbench.hcc_prediction_export import (
    DEFAULT_AXIS_MEMBERSHIP_PATH,
    DEFAULT_CONTRACT_PATH,
    load_axis_membership,
    load_json,
    validate_prediction_contract,
)

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def load_prediction(path: Path) -> pd.DataFrame:
    frame = pd.read_csv(path, sep="\t")
    if frame.empty:
        raise ValueError(f"{path} 为空。")
    return frame


def main() -> None:
    parser = argparse.ArgumentParser(description="验证 Stage 2 HCC scorer-ready prediction contract。")
    parser.add_argument("--prediction-path", required=True)
    parser.add_argument("--summary-path", required=True)
    parser.add_argument("--contract-path", default=str(DEFAULT_CONTRACT_PATH))
    parser.add_argument("--axis-membership-path", default=str(DEFAULT_AXIS_MEMBERSHIP_PATH))
    parser.add_argument("--manifest-path")
    args = parser.parse_args()

    contract = load_json(Path(args.contract_path))
    prediction = load_prediction(Path(args.prediction_path))
    manifest = None
    if args.manifest_path:
        manifest = json.loads(Path(args.manifest_path).read_text(encoding="utf-8"))
    axis_membership = load_axis_membership(Path(args.axis_membership_path))
    summary = validate_prediction_contract(prediction, contract, manifest or {}, axis_membership)
    summary["manifest_checks"]["manifest_provided"] = manifest is not None
    summary["required_first_column"] = str(contract["required_first_column"])
    summary["has_duplicate_targets"] = bool(prediction.iloc[:, 0].astype(str).duplicated().any())
    summary_path = Path(args.summary_path)
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
