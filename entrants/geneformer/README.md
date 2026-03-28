# Geneformer entrant recipe

## 当前定位

本目录记录 `geneformer_k562_smoke_v1` 的 Stage 1A smoke recipe。当前实现是一个可审计的 task wrapper，而不是把“Geneformer”这个名字抽象地当作已完成 entrant。

## acquisition 方式

- 当前仓库采用本地 vendor path：`vendor/geneformer`
- 这不是远程 `pip install geneformer`
- pretrained checkpoint 额外位于 `models/pretrained/geneformer_gf_12l_95m_i4096/`
- vocab / tokenizer 资产位于 `models/pretrained/geneformer_assets/geneformer/`

## 输入如何转成 Geneformer 需要的格式

- 读取 formal filtered Stage 1A single-cell h5ad
- 用 `gene_name_id_dict_gc104M.pkl` 把 gene symbol 映射到 Ensembl
- 再用 `token_dictionary_gc104M.pkl` 映射到 Geneformer token
- 用 pretrained word embedding 做 cosine-kernel 回归，导出 `predicted_shift`

## 当前限制

- 当前只冻结单数据集单 split seed smoke recipe
- 当前 wrapper 不等同于 Geneformer 原生 perturbation predictor
- 若 token coverage 过低会直接报错，不输出伪成功结果
