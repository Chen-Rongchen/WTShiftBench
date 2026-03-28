"""Stage 1A 方案 B：eligible → support 排序 → low/mid/high 分层 → 每层独立 held-out。

预注册参数见 configs/stage1a_split_governance.yaml；制度说明见 docs/protocol_blueprint.md 第 5.1A 节。
"""

from __future__ import annotations

import math
import zlib
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import yaml

from stage1a_catalog import PROJECT_ROOT

GOVERNANCE_PATH = PROJECT_ROOT / "configs/stage1a_split_governance.yaml"


def load_split_governance(path: Path | None = None) -> dict[str, Any]:
    p = path or GOVERNANCE_PATH
    data = yaml.safe_load(p.read_text(encoding="utf-8")) or {}
    seeds = data.get("split_seeds", [101, 202, 303, 404, 505])
    data["split_seeds"] = [int(s) for s in seeds]
    data["default_split_seed_for_truth_freeze"] = int(
        data.get("default_split_seed_for_truth_freeze", 101)
    )
    data["min_cells_per_group"] = int(data.get("min_cells_per_group", 5))
    if data["default_split_seed_for_truth_freeze"] not in data["split_seeds"]:
        raise ValueError(
            "default_split_seed_for_truth_freeze 必须在 split_seeds 中: "
            f"{data['default_split_seed_for_truth_freeze']} not in {data['split_seeds']}"
        )
    return data


def n_test_stratum(n_stratum: int) -> int:
    """n_test_stratum = ceil(0.2 * n_stratum)，且 <= n_stratum - 1。"""
    if n_stratum <= 0:
        return 0
    raw = int(math.ceil(0.2 * n_stratum))
    return min(raw, n_stratum - 1)


def tercile_sizes(n: int) -> tuple[int, int, int]:
    """将 n 个 target 尽量三等分为 low/mid/high 层大小。"""
    if n < 3:
        raise ValueError(f"方案 B 需要至少 3 个 eligible targets，当前 n={n}")
    base = n // 3
    r = n % 3
    low_n = base + (1 if r >= 1 else 0)
    mid_n = base + (1 if r >= 2 else 0)
    high_n = n - low_n - mid_n
    return low_n, mid_n, high_n


def stable_dataset_rng(dataset_id: str, split_seed: int) -> np.random.Generator:
    """跨数据集可复现、且与 dataset_id 耦合的 RNG（避免不同数据集共用同一随机序列起点）。"""
    did = zlib.adler32(dataset_id.encode("utf-8")) & 0xFFFFFFFF
    return np.random.default_rng(np.random.SeedSequence([split_seed, did]))


def plan_b_heldout_targets(
    eligible_rows: pd.DataFrame,
    dataset_id: str,
    split_seed: int,
) -> list[str]:
    """
    eligible_rows: 单数据集，含 target_gene、n_cells_perturbed；须已 eligible。
    返回：held-out target_gene 列表，顺序为 low→mid→high 层内按字母序稳定拼接。
    """
    need = {"target_gene", "n_cells_perturbed"}
    missing = need - set(eligible_rows.columns)
    if missing:
        raise ValueError(f"eligible 行缺少列: {sorted(missing)}")

    df = eligible_rows.loc[:, ["target_gene", "n_cells_perturbed"]].copy()
    df["target_gene"] = df["target_gene"].astype("string")
    df["n_cells_perturbed"] = pd.to_numeric(df["n_cells_perturbed"], errors="raise").astype(int)
    df = df.sort_values(["n_cells_perturbed", "target_gene"], ascending=[True, True]).reset_index(drop=True)

    n = len(df)
    low_n, mid_n, high_n = tercile_sizes(n)
    low_df = df.iloc[:low_n]
    mid_df = df.iloc[low_n : low_n + mid_n]
    high_df = df.iloc[low_n + mid_n :]

    rng = stable_dataset_rng(dataset_id, split_seed)
    heldout: list[str] = []

    for stratum_df in (low_df, mid_df, high_df):
        genes = stratum_df["target_gene"].astype(str).tolist()
        k = n_test_stratum(len(genes))
        if k == 0:
            continue
        pick = rng.choice(len(genes), size=k, replace=False)
        chosen = [genes[i] for i in sorted(pick.tolist())]
        heldout.extend(sorted(chosen))

    if not heldout:
        raise ValueError(
            f"{dataset_id}: 方案 B 未产生任何 held-out（eligible n={n}）。"
            "请检查 eligible 规模或制度参数。"
        )
    return heldout


def filter_eligible_to_heldout(
    eligible_targets: pd.DataFrame,
    dataset_id: str,
    split_seed: int,
) -> pd.DataFrame:
    """返回仅含 held-out 行的 eligible 子表；行顺序与 plan_b_heldout_targets 一致。"""
    sub = eligible_targets.loc[eligible_targets["dataset_id"].astype("string").eq(dataset_id)].copy()
    if sub.empty:
        raise ValueError(f"{dataset_id}: 无 eligible 行")
    heldout_order = plan_b_heldout_targets(sub, dataset_id, split_seed)
    heldout = set(heldout_order)
    out = sub.loc[sub["target_gene"].astype("string").isin(heldout)].copy()
    if len(out) != len(heldout):
        raise ValueError(f"{dataset_id}: held-out 与 eligible 行不一致")
    order_index = {g: i for i, g in enumerate(heldout_order)}
    out = out.copy()
    out["_ord"] = out["target_gene"].astype("string").map(order_index)
    out = out.sort_values("_ord").drop(columns=["_ord"]).reset_index(drop=True)
    return out


def expected_heldout_counts_by_dataset(split_seed: int | None = None) -> pd.DataFrame:
    """供 freeze_stage1a_truth 校验：与 truth 构建使用同一规则得到每数据集 held-out 数。"""
    gov = load_split_governance()
    seed = int(split_seed if split_seed is not None else gov["default_split_seed_for_truth_freeze"])
    eligible_path = PROJECT_ROOT / "data/frozen/stage1a_formal/eligible_targets.tsv"
    eligible = pd.read_csv(eligible_path, sep="\t")
    eligible["eligible_for_pseudobulk"] = (
        eligible["eligible_for_pseudobulk"].astype("string").str.lower().eq("true")
    )
    eligible = eligible.loc[eligible["eligible_for_pseudobulk"]].copy()

    rows = []
    for dataset_id in sorted(eligible["dataset_id"].astype("string").unique()):
        sub = eligible.loc[eligible["dataset_id"].astype("string").eq(dataset_id)]
        heldout = plan_b_heldout_targets(sub, str(dataset_id), seed)
        rows.append(
            {
                "dataset_id": str(dataset_id),
                "n_targets_expected_eval": len(heldout),
                "split_seed": seed,
                "split_scheme": gov.get("split_scheme", "B"),
            }
        )
    return pd.DataFrame(rows).sort_values("dataset_id").reset_index(drop=True)
