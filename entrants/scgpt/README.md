# scGPT entrant recipe

## 当前定位

本目录记录 `scgpt_k562_smoke_v1` 的 Stage 1A smoke recipe。当前实现是一个可审计的 task wrapper，而不是声称 scGPT 原生具备 benchmark 所需的 perturbation-level shift 输出头。

## 代码与资产来源

- 代码入口：仓库现有 `scripts/stage1a/adapters/scgpt/build_predictions.py` 的最小逻辑已收口到 `src/wtbench/entrants/scgpt_adapter.py`
- checkpoint：`models/pretrained/scgpt_human/best_model.pt`
- vocab：`models/pretrained/scgpt_human/vocab.json`

## 输入如何转成 scGPT 需要的格式

- 读取 formal filtered Stage 1A single-cell h5ad
- 以 train targets 的 pseudobulk delta 作为监督值
- 用 gene symbol 映射到 scGPT vocab
- 用 pretrained token embedding 做 cosine-kernel 回归，生成 held-out targets 的 `predicted_shift`

## 当前限制

- 当前只冻结单数据集单 split seed smoke recipe
- 当前 wrapper 不覆盖 scGPT 文献中的全部任务模式
- 若 vocab coverage 过低会直接报错，不隐藏成“看似成功”的退化输出
