from __future__ import annotations

import argparse
import json
from pathlib import Path

import anndata as ad
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG_PATH = PROJECT_ROOT / "configs/stage1a/candidate_audits/raw_candidate_sources.json"
DEFAULT_OUTPUT_PATH = PROJECT_ROOT / "reports/stage1a/candidate_raw_integrity.tsv"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="校验 candidate raw 文件是否与预期来源语义一致。")
    parser.add_argument(
        "--config",
        type=Path,
        default=DEFAULT_CONFIG_PATH,
        help="候选 raw 源配置 JSON。",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT_PATH,
        help="输出 TSV 路径。",
    )
    return parser.parse_args()


def load_config(path: Path) -> list[dict[str, object]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    datasets = payload.get("datasets", [])
    if not datasets:
        raise ValueError(f"{path} 未定义 datasets。")
    return [dict(item) for item in datasets]


def build_row(item: dict[str, object]) -> dict[str, object]:
    dataset_id = str(item["dataset_id"])
    local_path = PROJECT_ROOT / str(item["local_path"])
    row: dict[str, object] = {
        "dataset_id": dataset_id,
        "tier": str(item.get("tier", "")),
        "local_path": str(local_path),
        "download_url": str(item.get("download_url", "")),
        "file_exists": local_path.exists(),
        "shape": "",
        "required_obs_columns_ok": False,
        "required_obs_column_any_of_ok": True,
        "forbidden_obs_columns_absent": True,
        "status": "missing",
        "note": "",
    }
    if not local_path.exists():
        row["note"] = "文件不存在。"
        return row

    adata = ad.read_h5ad(local_path, backed="r")
    try:
        obs_columns = {str(col) for col in adata.obs.columns}
        row["shape"] = f"{adata.n_obs}x{adata.n_vars}"

        required = [str(col) for col in item.get("required_obs_columns", [])]
        required_any = [
            [str(col) for col in group]
            for group in item.get("required_obs_column_any_of", [])
        ]
        forbidden = [str(col) for col in item.get("forbidden_obs_columns", [])]

        required_ok = all(col in obs_columns for col in required)
        any_ok = all(any(col in obs_columns for col in group) for group in required_any)
        forbidden_absent = all(col not in obs_columns for col in forbidden)

        row["required_obs_columns_ok"] = required_ok
        row["required_obs_column_any_of_ok"] = any_ok
        row["forbidden_obs_columns_absent"] = forbidden_absent
        row["status"] = (
            "ok" if required_ok and any_ok and forbidden_absent else "mismatch"
        )

        missing_required = [col for col in required if col not in obs_columns]
        failed_any = [
            "|".join(group)
            for group in required_any
            if not any(col in obs_columns for col in group)
        ]
        present_forbidden = [col for col in forbidden if col in obs_columns]

        notes: list[str] = []
        if missing_required:
            notes.append(f"缺少必需列: {','.join(missing_required)}")
        if failed_any:
            notes.append(f"未命中任一候选列组: {';'.join(failed_any)}")
        if present_forbidden:
            notes.append(f"出现禁用列: {','.join(present_forbidden)}")
        if not notes:
            notes.append("obs 语义列与配置一致。")
        row["note"] = " ".join(notes)
        return row
    finally:
        adata.file.close()


def main() -> None:
    args = parse_args()
    rows = [build_row(item) for item in load_config(args.config)]
    frame = pd.DataFrame(rows).sort_values("dataset_id").reset_index(drop=True)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(args.output, sep="\t", index=False)
    print(f"已写出: {args.output}")
    print(frame.to_string(index=False))


if __name__ == "__main__":
    main()
