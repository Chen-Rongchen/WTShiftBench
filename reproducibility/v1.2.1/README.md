# WTShiftBench v1.2.1 复现入口

本目录对应已发布的[GitHub Release v1.2.1](https://github.com/Chen-Rongchen/WTShiftBench/releases/tag/v1.2.1)，固定源码为`63a00cedcf4960ede5f1b21066cc94a8469cec6c`。发布后的文档提交不移动tag或替换归档ZIP。Zenodo公开下载及版本DOI仍单独验收。不要在根目录旧实现执行当前命令；工作目录、输入ZIP和所加载模块必须来自同一版本。

## 1. 下载与校验

[manifests/archive_assets.json](manifests/archive_assets.json)列出三个计算／验收ZIP的GitHub下载位置、实际字节数、SHA256及`extracted_root`；精确源码ZIP另在Release的Assets中提供，四包完整清单为Release附件`release_manifest.json`。不得用旧版本DOI补空。将矩阵ZIP、训练ZIP分别解压到不同的新目录，保留原内部路径。

矩阵ZIP展开后须进入`WTShiftBench_v1.2.1_matrices/`，训练ZIP须进入`WTShiftBench_v1.2.1_cellot_training/`。不要停留在其父目录运行，否则Pixi可能向上找到另一项目的环境。

源码树为可阅读的小型科学文件视图，不含大型矩阵。此处的`archive_manifest.json`是完整矩阵ZIP的原成员清单，不是“源码目录应包含全部矩阵”的声明。计算从完整矩阵ZIP根目录执行；不要手工拼接源码视图、旧根目录与矩阵成员。

## 2. 冻结矩阵到统计

以下命令的工作目录是**矩阵ZIP解压根目录**（该目录同时含`recompute.py`、`pixi.toml`、`archive_manifest.json`）：

```sh
pixi run --frozen --environment core python recompute.py --verify-only
pixi run --frozen --environment core python recompute.py --output recomputed
pixi run --frozen --environment core python recompute_auxiliary.py
```

完整评分计算87个输出的点估计及已有CI/P/q，然后与冻结expected对账。`--points-only`是快速点估计检查，不代替完整推断。分组可用`--group m3`、`--group m4`、`--group m5`、`--group cellot_training_seeds`、`--group other_training_seeds`、`--group replogle_feature_seeds`。

辅助入口从已归档target级评分重建M6四张表、从提取的25Q3数据重算八context GE sensitivity；不是重新处理整个官方DepMap大表。HCC连续统计容差1e-10、Replogle float32连续统计1e-6，P/q与样本数使用更严格容差。实际实现为最终依据。

## 3. CellOT checkpoint回放与staged训练

以下命令的工作目录是**训练ZIP解压根目录**（含`run_cellot.py`及完整vendor与staged输入）：

```sh
pixi run --frozen --environment cellot python run_cellot.py --mode replay --seed 124 --context HCC1143 --output replay_check
pixi run --frozen --environment cellot python run_cellot.py --seed 123 --context HCC38 --target ARID1A --output retrained_check
```

当前源码`training/cellot/`提供入口、环境和许可的浏览副本，hash与原训练ZIP对应；它不是独立训练包。训练从初始化开始，不需要外部预训练CellOT权重。历史投稿checkpoint的seed未知，不冒称本次123恢复了历史seed。

既有本地记录覆盖470个checkpoint回放及HCC38/HCC1143各一个ARID1A的seed123 staged重训；不是全部470次独立重训，更不是raw-single-cell到全部模型训练的完整复现。

## 4. 公开源表绘图与轻量测试

以下命令工作目录是**本源码目录**`reproducibility/v1.2.1/`：

```sh
pixi run --frozen --environment core python build_figures.py --output outputs/figures
pixi run --frozen --environment core python -m pytest tests -q
```

绘图直接读取`presentation/Results/`的46张冻结CSV/TSV及科学配置，不需要Word、稿件或回复。绘图函数来自同一交付实现；函数hash与唯一D40路径映射见`presentation/plot_source_provenance.json`。

现有`build_figures.py`生成程序排版的组合图及其图源清单，不是逐panel独立文件导出器。各panel的绘制代码与数值来源可以核对；作者后续的人工拼接、字体和留白调整留在私有工作区。论文成品图和最终投稿Excel不作为默认公开附件，其对应源表仍公开。不承诺自动生成与人工最终版逐像素相同的版式；PDF/SVG也可能包含时间等元数据。

## 5. 对象、运行与历史

- [输出及轴索引](manifests/outputs.tsv)：87个输出，formal／seed sensitivity／diagnostic分别登记；生成型参照标明代码/seed，不能伪装成保存矩阵。
- [运行索引](provenance/run_registry.tsv)：训练seed与feature seed分开；已登记的原始细节继续引用模型registry和配置。
- [DepMap来源](provenance/depmap_provenance.tsv)：当前25Q3与历史23Q4数值匹配分开。
- [46张展示源表](presentation/INDEX.tsv)：导出hash与原计算路径对应，不手录数字。
- [解释与边界](docs/data_dictionary.md)、[来源时间线](provenance/README.md)。

保留的旧来源记录可能描述当时“尚未恢复”的状态；它们是历史记录，不能覆盖当前正式定义。`docs/README.md`是矩阵ZIP的原说明副本，本README明确源码浏览与实际ZIP执行之间的区别。

## 6. 验证与发布状态

`verification/local/`保留发布前本地验收记录的真实范围，不重命名成公开验证。GitHub发布状态、匿名下载文件核验、矩阵到完整统计复算与Zenodo验收分别记录；不能只因出现下载URL就填写`public_download_verified=true`。取得相应版本DOI后再回填引用。
