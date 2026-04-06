from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG_PATH = PROJECT_ROOT / "configs/stage1a/dataset_governance.json"
DEFAULT_TSV_PATH = PROJECT_ROOT / "admission_matrix.tsv"
DEFAULT_JSON_PATH = PROJECT_ROOT / "reports/stage1a/dataset_governance/dataset_governance.json"

REQUIRED_COLUMNS = [
    "dataset_id",
    "tier",
    "usage",
    "source_kind",
    "review_status",
    "control_clear",
    "single_target_fit",
    "truth_build_feasible",
    "recommendation",
    "notes",
]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="渲染 Stage 1A 两层数据集治理清单。")
    parser.add_argument("--config", default=str(DEFAULT_CONFIG_PATH), help="治理 JSON 配置路径。")
    parser.add_argument("--tsv-out", default=str(DEFAULT_TSV_PATH), help="输出 TSV 路径。")
    parser.add_argument("--json-out", default=str(DEFAULT_JSON_PATH), help="输出 JSON 路径。")
    return parser


def resolve_path(path_value: str | Path) -> Path:
    path = Path(path_value)
    if path.is_absolute():
        return path
    return PROJECT_ROOT / path


def load_config(path: Path) -> dict[str, object]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{path} 必须是 JSON 对象。")
    datasets = payload.get("datasets", [])
    if not isinstance(datasets, list) or not datasets:
        raise ValueError(f"{path} 必须包含非空 datasets 列表。")
    frame = pd.DataFrame(datasets)
    missing = [column for column in REQUIRED_COLUMNS if column not in frame.columns]
    if missing:
        raise ValueError(f"{path} 缺少字段: {missing}")
    return payload


def main() -> None:
    args = build_parser().parse_args()
    config_path = resolve_path(args.config)
    tsv_out = resolve_path(args.tsv_out)
    json_out = resolve_path(args.json_out)

    payload = load_config(config_path)
    frame = pd.DataFrame(payload["datasets"]).loc[:, REQUIRED_COLUMNS].copy()

    tier_order = pd.CategoricalDtype(["formal", "supplement"], ordered=True)
    usage_order = pd.CategoricalDtype(["mainline", "runnable", "deferred", "backup_only"], ordered=True)
    frame["tier"] = frame["tier"].astype(tier_order)
    frame["usage"] = frame["usage"].astype(usage_order)
    frame = frame.sort_values(["tier", "usage", "dataset_id"]).reset_index(drop=True)
    frame["tier"] = frame["tier"].astype(str)
    frame["usage"] = frame["usage"].astype(str)

    tsv_out.parent.mkdir(parents=True, exist_ok=True)
    json_out.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(tsv_out, sep="\t", index=False)
    json_out.write_text(
        json.dumps(
            {
                "version": payload.get("version", ""),
                "notes": payload.get("notes", []),
                "datasets": frame.to_dict(orient="records"),
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    print(f"已写出: {tsv_out}")
    print(f"已写出: {json_out}")


if __name__ == "__main__":
    main()
