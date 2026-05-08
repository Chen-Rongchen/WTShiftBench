from __future__ import annotations

import argparse
import itertools
import json
from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG_PATH = PROJECT_ROOT / "configs/gears_hcc_backbone_sweep_v1.json"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="物化 GEARS backbone 有限预算 sweep 候选 recipe。")
    parser.add_argument("--config", default=str(DEFAULT_CONFIG_PATH), help="sweep 配置 JSON 路径。")
    return parser


def resolve_path(path_value: str | Path) -> Path:
    path = Path(path_value)
    if path.is_absolute():
        return path
    return PROJECT_ROOT / path


def load_json(path: Path) -> dict[str, object]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{path} 必须是 JSON 对象。")
    return payload


def sanitize_number(value: float) -> str:
    return format(value, ".0e").replace("+", "").replace(".", "p")


def build_variant_id(epochs: int, lr: float, weight_decay: float) -> str:
    return f"e{epochs}_lr{sanitize_number(lr)}_wd{sanitize_number(weight_decay)}"


def summarize_diagnostic(path: Path) -> tuple[str, list[str]]:
    frame = pd.read_csv(path, sep="\t")
    calls = [str(value) for value in frame["failure_mode_call"].tolist()]
    summary = ", ".join(f"{row.cell_line}={row.failure_mode_call}" for row in frame.itertuples(index=False))
    return summary, calls


def compute_change_count(base_runtime: dict[str, object], epochs: int, lr: float, weight_decay: float) -> int:
    count = 0
    if int(base_runtime["epochs"]) != epochs:
        count += 1
    if float(base_runtime["lr"]) != lr:
        count += 1
    if float(base_runtime["weight_decay"]) != weight_decay:
        count += 1
    return count


def materialize_candidates(sweep: dict[str, object], base_recipe: dict[str, object]) -> pd.DataFrame:
    allowed = dict(sweep["allowed_recipe_axes"])
    base_runtime = dict(base_recipe["runtime"])
    rows: list[dict[str, object]] = []
    for epochs, lr, weight_decay, export_sanity in itertools.product(
        allowed["epochs"],
        allowed["lr"],
        allowed["weight_decay"],
        allowed["materialization_export_sanity"],
    ):
        epochs = int(epochs)
        lr = float(lr)
        weight_decay = float(weight_decay)
        variant_id = build_variant_id(epochs, lr, weight_decay)
        rows.append(
            {
                "variant_id": variant_id,
                "epochs": epochs,
                "lr": lr,
                "weight_decay": weight_decay,
                "materialization_export_sanity": str(export_sanity),
                "change_count": compute_change_count(base_runtime, epochs, lr, weight_decay),
                "distance_tuple": (
                    compute_change_count(base_runtime, epochs, lr, weight_decay),
                    abs(epochs - int(base_runtime["epochs"])),
                    abs(lr - float(base_runtime["lr"])),
                    abs(weight_decay - float(base_runtime["weight_decay"])),
                ),
            }
        )
    frame = pd.DataFrame(rows).sort_values(["change_count", "epochs", "lr", "weight_decay"]).reset_index(drop=True)
    if str(sweep["selection"]["strategy"]) != "nearest_to_base":
        raise ValueError("当前只支持 nearest_to_base 选择策略。")
    max_candidates = int(sweep["selection"]["max_candidates"])
    frame = frame.sort_values("distance_tuple").head(max_candidates).reset_index(drop=True)
    frame["candidate_rank"] = range(1, len(frame) + 1)
    return frame.drop(columns=["distance_tuple"])


def build_recipe(
    *,
    base_recipe: dict[str, object],
    candidate: dict[str, object],
    sweep_config_path: Path,
    diagnostic_path: Path,
    diagnostic_summary: str,
) -> dict[str, object]:
    recipe = json.loads(json.dumps(base_recipe))
    runtime = dict(recipe["runtime"])
    runtime["epochs"] = int(candidate["epochs"])
    runtime["lr"] = float(candidate["lr"])
    runtime["weight_decay"] = float(candidate["weight_decay"])
    recipe["runtime"] = runtime

    base_model_id = str(base_recipe["model_id"])
    variant_suffix = str(candidate["variant_id"])
    recipe["model_id"] = f"{base_model_id}_{variant_suffix}"
    recipe["entrant_version"] = recipe["model_id"]
    recipe["claim_scope"] = (
        str(base_recipe["claim_scope"])
        + " 当前对象属于 GEARS backbone 有限 sweep 候选，只用于基于诊断摘要的定向比较。"
    )
    recipe["sweep_context"] = {
        "stage": "stage2_gears_backbone_recovery_sweep_candidate",
        "parent_recipe_config_path": str(sweep_config_path.relative_to(PROJECT_ROOT)),
        "diagnostic_artifact_path": str(diagnostic_path.relative_to(PROJECT_ROOT)),
        "diagnostic_summary": diagnostic_summary,
        "candidate_rank": int(candidate["candidate_rank"]),
        "allowed_materialization_export_sanity": str(candidate["materialization_export_sanity"]),
    }
    return recipe


def write_markdown_report(
    *,
    sweep: dict[str, object],
    diagnostic_summary: str,
    candidates: pd.DataFrame,
    output_path: Path,
) -> None:
    lines = [
        "# GEARS Backbone Sweep 候选",
        "",
        "## 定位",
        "",
        "- 这是 GEARS HCC primary mainline 的有限预算 backbone sweep 候选物化清单。",
        "- 这里只物化 recipe，不扩模型、不扩 truth object、不引入新评分体系。",
        f"- 当前诊断摘要：`{diagnostic_summary}`。",
        "",
        "## 候选选择策略",
        "",
        f"- strategy = `{sweep['selection']['strategy']}`",
        f"- max_candidates = `{int(sweep['selection']['max_candidates'])}`",
        "- 选择原则：优先保留与 base recipe 距离最近的候选，先比较单轴变化，再比较多轴联动。",
        "",
        "## 候选列表",
        "",
    ]
    for row in candidates.itertuples(index=False):
        lines.append(
            f"- rank `{row.candidate_rank}`：`{row.variant_id}`，epochs = `{row.epochs}`，lr = `{row.lr}`，weight_decay = `{row.weight_decay}`，change_count = `{row.change_count}`。"
        )
    lines.extend(
        [
            "",
            "## Stop Rule",
            "",
            f"- {sweep['stop_rule']}",
            "",
        ]
    )
    output_path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    args = build_parser().parse_args()
    sweep_config_path = resolve_path(args.config)
    sweep = load_json(sweep_config_path)
    base_recipe_path = resolve_path(str(sweep["base_recipe_config_path"]))
    diagnostic_path = resolve_path(str(sweep["prerequisite_artifact_path"]))
    if not diagnostic_path.exists():
        raise FileNotFoundError(f"缺少前置诊断产物：{diagnostic_path}")
    base_recipe = load_json(base_recipe_path)
    generated_config_root = resolve_path(str(sweep["generated_config_root"]))
    report_root = resolve_path(str(sweep["report_root"]))
    generated_config_root.mkdir(parents=True, exist_ok=True)
    report_root.mkdir(parents=True, exist_ok=True)

    diagnostic_summary, _ = summarize_diagnostic(diagnostic_path)
    candidates = materialize_candidates(sweep, base_recipe)

    config_rows: list[dict[str, object]] = []
    for candidate in candidates.to_dict(orient="records"):
        recipe = build_recipe(
            base_recipe=base_recipe,
            candidate=candidate,
            sweep_config_path=sweep_config_path,
            diagnostic_path=diagnostic_path,
            diagnostic_summary=diagnostic_summary,
        )
        config_path = generated_config_root / f"{candidate['variant_id']}.json"
        config_path.write_text(json.dumps(recipe, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        config_rows.append(
            {
                **candidate,
                "model_id": recipe["model_id"],
                "config_path": str(config_path.relative_to(PROJECT_ROOT)),
                "run_command": f"PYTHONPATH=src pixi run --environment gears python scripts/pipeline/gears_hcc_predictions.py --config {config_path.relative_to(PROJECT_ROOT)}",
            }
        )

    manifest = pd.DataFrame(config_rows)
    manifest.to_csv(report_root / "candidate_manifest.tsv", sep="\t", index=False)
    write_markdown_report(
        sweep=sweep,
        diagnostic_summary=diagnostic_summary,
        candidates=manifest,
        output_path=report_root / "candidate_manifest.md",
    )
    print(f"已写出: {report_root / 'candidate_manifest.tsv'}")
    print(f"已写出: {report_root / 'candidate_manifest.md'}")
    print(f"已写出: {generated_config_root}")


if __name__ == "__main__":
    main()
