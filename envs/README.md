# WT Benchmark 环境说明

## 环境概览

| 环境 | 职责 | 关键依赖 |
|------|------|----------|
| `core` | 评估主链路 | `numpy` / `pandas` / `scipy` / `anndata` |
| `gears` | GEARS 模型推理 | GPU `torch 2.5.x` / `torch-geometric` / `cell-gears` |
| `scgpt` | scGPT 模型推理 | GPU `torch 2.3.x` / `torchtext 0.18.x` / `scgpt` |
| `geneformer` | Geneformer 模型推理 | GPU `torch 2.5.x` / `transformers 4.x` / vendored `geneformer` |

四个环境彼此独立，不混装，不共享 solve group。

## 安装

按需安装：

```bash
pixi install --environment core
pixi install --environment gears
pixi install --environment scgpt
pixi install --environment geneformer
```

或一次性安装全部：

```bash
pixi install
```

## 验证

最低验收标准：

- `core`：主链路依赖可 import
- `gears`：`import gears` 且 `torch.cuda.is_available() == True`
- `scgpt`：`import scgpt` 且 `torch.cuda.is_available() == True`
- `geneformer`：`import geneformer` 且 `torch.cuda.is_available() == True`

命令如下：

```bash
pixi run --environment core env-check-core
pixi run --environment gears env-check-gears
pixi run --environment scgpt env-check-scgpt
pixi run --environment geneformer env-check-geneformer
```

统一验证：

```bash
pixi run check-envs
```
