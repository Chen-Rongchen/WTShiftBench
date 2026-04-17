# Community adjudication kit v1

## 状态

完成日期：2026-04-17。

这是 C17 的最小实现，不是独立 pip 包。它提供一个 config-driven CLI，用于把外部 prediction matrix 与 frozen truth architecture 对齐，并输出三项 architecture-aware scores、axis projections 和 manifest。

## CLI

入口：

```bash
PYTHONPATH=src python scripts/manuscript/run_architecture_adjudication.py --config configs/manuscript/architecture_adjudication_example_v1.json
```

## 输入配置

示例配置：

- `configs/manuscript/architecture_adjudication_example_v1.json`

配置字段：

- `truth_contract_path`：truth architecture contract TSV。
- `axis_membership_path`：target-to-axis membership TSV。
- `output_dir`：输出目录。
- `predictions`：待评分 prediction matrices，每个对象包含 `model_id`、`context`、`prediction_path`。

## 输出

示例输出目录：

- `reports/manuscript_architecture_adjudication_example_v1/`

输出文件：

- `architecture_scores.tsv`：三指标评分。
- `axis_projections.tsv.gz`：target x axis projection table。
- `architecture_adjudication_manifest.json`：输入与输出 SHA256 manifest。

## 边界

该 kit 只复用已冻结的 architecture scorer，不新增 scoring system。它不负责训练模型、生成 prediction matrix 或判断 claim tier。claim tier 仍由 manuscript governance 文档约束。
