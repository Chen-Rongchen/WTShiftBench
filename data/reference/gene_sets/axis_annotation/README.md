# Stage 2 Axis Annotation 基因集资源

这个目录用于放置 `Stage 2 axis enrichment` 使用的本地 `GMT` 资源。

当前约定：

- 只接受本地 `GMT` 文件
- `scripts/pipeline/axis_enrichment.py` 不在脚本内部自动联网下载
- 缺失 `gmt_path` 时直接 `fail-fast`

当前文件：

- `msigdb_hallmark.gmt`
  来源：`Enrichr / MSigDB_Hallmark_2020`
- `reactome.gmt`
  来源：`Enrichr / Reactome_2022`
  说明：本次运行时 `Reactome` 官方 `ReactomePathways.gmt.zip` 返回 `504`，先使用可访问镜像以保证分析链条可执行
- `go_bp.gmt`
  来源：`Enrichr / GO_Biological_Process_2025`
- `corum.gmt`
  来源：`Enrichr / CORUM`

推荐搭配：

- `configs/axis_enrichment_template_v1.json`
- `scripts/pipeline/axis_enrichment.py`

已生成产物：

- `reports/axis_analysis/axis_enrichment.tsv`

后续如果需要更严格的数据库冻结，可以把这些来源进一步固化到版本化 manifest 中，但当前最小注释流程已经可复现执行。
