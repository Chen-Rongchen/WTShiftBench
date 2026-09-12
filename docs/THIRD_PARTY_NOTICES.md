# 第三方来源与使用条件

项目根LICENSE只覆盖该许可明确授权的项目代码，不自动覆盖第三方数据、模型权重、代码及派生资产。

- CellOT附带源码保留原BSD-3-Clause许可证和作者署名，见当前源码的`training/cellot/vendor/cellot/LICENSE`；实际执行使用训练ZIP里的完整vendor目录。
- GEO数据保留accession与原论文引用。获取入口：[GEO](https://www.ncbi.nlm.nih.gov/geo/)。记录的accession见DATA_AVAILABILITY；具体dataset的使用要求应按其原站说明核对。
- Replogle数据入口：[figshare 20029387](https://figshare.com/articles/dataset/20029387)。不把本项目MIT许可当作该数据的许可。
- DepMap官方文件从[DepMap下载页](https://depmap.org/portal/download/all/)取得；版本、ModelID、官方文件hash和提取表分开记录。完整官方CSV不随源码重新发布。
- Geneformer／scGPT及其他上游权重未默认重分发；获取方式和定位信息以冻结checkpoint登记、实际适配脚本及上游许可证为准。

本清单说明来源与责任边界，不是对每个上游资产均已取得再分发授权的声明。上传完整矩阵和staged输入前，应按实际归档成员核对数据使用及派生分发条件。无法确认的项目保留明确限制，不以“可公开下载”代替许可判断。
