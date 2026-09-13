# 历史公开图件

本目录保留当前复现入口建立前已经公开的 SVG panel 及其源表，文件不删除、不迁移。它们属于历史公开版本，**不代表 v1.2.1 的正式结果**，也不是本轮人工排版后的论文成品图。

当前分析、数值源表与绘图入口见 [v1.2.1 复现说明](../reproducibility/v1.2.1/README.md)。请勿将下列历史 panel 或根目录旧绘图命令当作当前 Fig.1–4／S1–S7 的来源。

| 历史图件 | 保留的 panel | 历史生成脚本 |
| --- | --- | --- |
| Figure 1 | a-c | 保留当时提供的设计 SVG |
| Figure 2 | a-e | `scripts/figures/build_figure2.py` |
| Figure 3 | a-f | `scripts/figures/build_figure3.py` |
| Figure 4 | a-c | `scripts/figures/build_figure4.py` |
| Extended Data Figure 1 | a-c | `scripts/figures/build_extended_data_figure1.py` |
| Extended Data Figure 2 | a-f | `scripts/figures/build_extended_data_figure2.py` |
| Extended Data Figure 3 | a，含六个小图 | `scripts/figures/build_extended_data_figure3.py` |
| Extended Data Figure 4 | a-b | `scripts/figures/build_extended_data_figure4.py` |
| Extended Data Figure 5 | a-c | `scripts/figures/build_extended_data_figure5.py` |
| Extended Data Figure 6 | a-d | `scripts/figures/build_extended_data_figure6.py` |

仅在需要检查历史图件时，使用根目录的旧环境及以下历史命令；它不是 v1.2.1 的绘图命令：

```bash
pixi run --environment core build-figures
```

历史源表路径与哈希记录于 `source_data/figure_source_data_manifest.tsv`。当前版本的源表与图源映射位于 `reproducibility/v1.2.1/presentation/`，二者不混用。
