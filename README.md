# WTShiftBench

WTShiftBench（whole-transcriptome shift benchmark）审计模型输出的外部 dependency 排序、响应方向、anchor separation、靶标间结构及同质化。各维度分别解释，不合成通用排行榜，也不把 endpoint 排序当作完整转录响应恢复。

## 当前入口：v1.2.1

[v1.2.1 复现说明](reproducibility/v1.2.1/README.md) 是当前科学版本的唯一执行入口。[GitHub Release v1.2.1](https://github.com/Chen-Rongchen/WTShiftBench/releases/tag/v1.2.1) 已发布四个计算复现ZIP，固定源码提交为 `63a00cedcf4960ede5f1b21066cc94a8469cec6c`。本页后续更新只提供发布／验证说明，不移动该tag。2026-09-14已从实际公开下载的矩阵完成87输出、373项完整统计对账。代码版本DOI为[10.5281/zenodo.22735108](https://doi.org/10.5281/zenodo.22735108)，该Zenodo记录目前仅含源码，不包含矩阵和训练附件；数据持久归档仍需单独完成。

- 代码、配置、小型冻结结果与带轴索引：`reproducibility/v1.2.1/`。
- 矩阵、CellOT 五-seed 训练资产：独立 ZIP，见[资产清单](reproducibility/v1.2.1/manifests/archive_assets.json)。不纳入普通 Git 历史。
- 源数据、数据使用条件与范围：[数据说明](DATA_AVAILABILITY.md)、[第三方来源](docs/THIRD_PARTY_NOTICES.md)。
- 本轮变更：[版本记录](docs/CHANGELOG.md)。
- [公开下载与完整复算记录](docs/verification/v1.2.1/github_release_verification.json)：四个ZIP实际下载及SHA256/ZIP校验通过；371个矩阵成员、87输出/373项统计、M6四表和八context的GE辅助复算通过。训练包1767个成员核验通过，但本次未重新回放checkpoint或训练模型。2026-09-13的初次下载失败记录保留在Git历史中，不再代表当前验收状态。

## 两条不同的执行路径

评分无需重训模型：下载矩阵 ZIP，校验 SHA256，在原结构解压后的根目录使用 Pixi 执行 `recompute.py`。完整运行从实测／预测矩阵计算统计量，再与 `expected/` 对账；不要把源码浏览目录与旧根目录混拼成计算环境。

CellOT 训练／回放另用训练 ZIP。正式 CellOT 为 seed123，其余 seed124–127 全部公开作为敏感性检查；五次结果并不支持将 seed123 单次正向排序概括为稳定能力。470 个 checkpoint 回放与两个 ARID1A target 的 staged 重训，是不同验收范围。

## 评价范围

HCC 模型共同评分空间为 **47 genes**，不是47个 targets 的同义词，也不是全转录组模型恢复。HCC 的 held-out 与 in-sample 输出按冻结登记分别解释。Replogle 完整评分为 **1,882 targets × 1,024 genes**；三个具体 entrants 使用 target-response-held-out LOO。名称中的 WT 不扩大实际评分空间。

当前 primary probability 与 gene-effect sensitivity 均采用 DepMap Public 25Q3。历史 HepG2／Jurkat gene-effect 数值匹配23Q4的事实保留在 provenance，不再作为当前 sensitivity 输入。

## 历史版本

`reproducibility/v1.2.0/` 及旧 tag 原样保留。根目录原有 `src/`、`scripts/`、`configs/`、`pixi.toml` 和旧绘图入口属于历史／开发路径，不是本轮 v1.2.1 执行入口。旧说明中的“CellOT seed123仅为补充”“尚未新增H区间”和未明的 legacy gene-effect 来源，不代表当前版本状态。

[原有 SVG 图件](figures/README.md) 保留原路径，属于历史公开版本，不是 v1.2.1 正式结果入口。当前图源、代码与对应关系从上述 v1.2.1 入口查找；不要将旧 panel 混入当前结果。

## 公开与私有范围

公开分析与绘图代码、配置、环境、seeds、端点／类别表、数值源表及必要的科学 provenance。完整矩阵与训练资产单独归档；精简技术版本说明保留影响科学解释的实际变更。

本轮论文成品图、人工拼图工程、最终投稿 Excel、Word、回复信和内部逐句编辑日志保留私有，不作为默认公开附件。Excel 对应的 CSV／TSV 数值源表、绘图代码和图源映射仍公开。作者可在私有工作区完成最终版式；公开计算不依赖这些投稿文件，也不承诺逐像素重建人工排版。
