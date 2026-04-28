# WT Benchmark 环境策略

## 目标

WT Benchmark 使用一个 `pixi` workspace 管理四个相互隔离的环境：

- `core`：评估主链路
- `gears`：GEARS 模型
- `scgpt`：scGPT 模型
- `geneformer`：Geneformer 模型

目标只有三条：

- 模型环境全部使用 GPU 版 PyTorch
- 环境之间不混装
- 依赖与修复全部落在仓库和 `pixi.toml`

## 当前落地

`pixi.toml` 采用 `feature + environment + solve-group`：

- 每个环境只挂自己的 feature
- 每个环境各自独立求解
- `core` 不混入模型依赖

这保证了 GEARS、scGPT、Geneformer 互不污染，也让单个模型的兼容修复不会反向影响主链路。

## GPU 约定

最终通过验证的 GPU 组合如下：

- `gears`：`torch 2.5.1` + `pytorch-cuda 12.1`
- `scgpt`：`torch 2.3.0` + `pytorch-cuda 12.1`
- `geneformer`：`torch 2.5.1` + `pytorch-cuda 12.1`

其中 `scgpt` 没有继续跟 `gears / geneformer` 统一到 `torch 2.5.x`，原因很直接：`scgpt 0.2.4` 会拉入 `torchtext 0.18.*`，而这套 ABI 只和 `torch 2.3.x` 兼容。

## 上游兼容修复

### scGPT

`scgpt 0.2.4` 的真实可运行约束是：

- `datasets < 3.0`
- 需要 `IPython`
- 需要与 `torchtext 0.18.*` 匹配的 `torch 2.3.x`

因此这些约束都已经固化进 `pixi.toml`。

### Geneformer

上游 `jkobject/geneformer` 直接从远程源码安装时存在两个问题：

- git 安装会触发 Git LFS 权重拉取
- 源码本身包含语法错误和顶层循环导入

因此当前方案不再直接引用远程 git，而是把可安装源码 vendor 到仓库内：

- 本地路径：`vendor/geneformer`
- 安装方式：`[feature.geneformer.pypi-dependencies] geneformer = { path = "vendor/geneformer" }`

这样仓库内的修复也能被 `pixi` 锁定并复现。

## 验证标准

模型环境统一按照下面的条件通过：

- `import torch` 成功
- `torch.cuda.is_available() == True`
- 对应模型包可 import

命令：

```bash
pixi run check-envs
```

## 结果

当前机器上的最终验收结果已经通过：

- `core`：PASS
- `gears`：PASS
- `scgpt`：PASS
- `geneformer`：PASS
