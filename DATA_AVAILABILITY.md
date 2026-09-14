# 数据与复现资产

当前版本为 v1.2.1。代码入口见[复现说明](reproducibility/v1.2.1/README.md)，ZIP下载URL、大小和SHA256见[资产清单](reproducibility/v1.2.1/manifests/archive_assets.json)。[GitHub Release](https://github.com/Chen-Rongchen/WTShiftBench/releases/tag/v1.2.1) 已提供四个计算复现ZIP。代码版本DOI为[10.5281/zenodo.22735108](https://doi.org/10.5281/zenodo.22735108)；实际核验该Zenodo记录只有源码ZIP，内容与固定Release代码一致，不包含矩阵／训练附件。完整数据归档和对应版本DOI仍待完成，不能以源码DOI冒充数据已归档。

2026-09-14从GitHub实际重新下载四个ZIP，并在新解压目录的锁定Pixi环境完成87输出/373项完整评分对账，以及M6四表、八context的gene-effect辅助复算；全部在冻结容差内通过。详见[公开下载验收记录](docs/verification/v1.2.1/github_release_verification.json)。本次没有重新训练模型、重放470个checkpoint或重新处理全部原始细胞；这些范围与既有本地验证分别记录。

## 上游来源与当前用途

| 对象 | 来源 | 本版本处理 |
|---|---|---|
| HCC38／HCC1143 | GEO GSE241115 | 保留既有预处理与冻结端点；模型共同47-gene评分空间 |
| Replogle K562 essential | figshare 20029387 | day6；1,882 targets × 1,024 genes；legacy ID中的day7仅保留作映射 |
| K562 TF | GEO GSE90063 | 既有7／13天外部context检验 |
| HepG2／Jurkat | GEO GSE264667 | 外部context sensitivity；适用范围以冻结纳入集合为准 |
| dependency probability | DepMap Public 25Q3 CRISPRGeneDependency.csv | 当前primary端点；越高表示依赖越强 |
| gene effect | DepMap Public 25Q3 CRISPRGeneEffect.csv | 当前所有context的GE sensitivity；越负表示依赖越强 |

逐文件官方 hash 与 ModelID 见[DepMap登记](reproducibility/v1.2.1/provenance/depmap_provenance.tsv)。历史HepG2／Jurkat GE与23Q4的数值及missing状态匹配，不等于恢复了当年下载日志。精确内部Chronos build未公开的部分不推测。官方大表与本项目提取表的hash分开保存。

## 归档内容

公开数值源表、绘图代码和图源对应关系；本轮人工排版的论文成品图、最终投稿Excel及稿件／回复不作为默认公开附件。原有公开SVG保留为[历史图件](figures/README.md)，不指代当前结果。

矩阵ZIP包含87个已登记输出及相应实测矩阵／轴、冻结endpoint/categories、当前统计配置、评分代码、expected比较基准和科学来源记录。完整评分与辅助复算的范围见当前README；expected不是预测值或评分答案的计算输入。

训练ZIP保留CellOT123–127两context的470个checkpoint、staged输入和执行代码。其他模型的已报告seed预测也进入矩阵评分范围，但不能因此宣称其全部原始数据处理、上游预训练和训练checkpoint均已归档。

不默认重新分发全部raw h5ad、完整DepMap大表或上游预训练权重。原站获取和各自使用条件见[第三方来源说明](docs/THIRD_PARTY_NOTICES.md)。公开发布前仍需作者按实际文件核对再分发权限。
