# 当前对象与统计含义

- 外部端点是dependency；sampling-corrected shift是转录响应幅度统计，不是“构造出的真实fitness”。matched-size control-null扣除后保留负值；负值不是响应方向反转。
- A003 corrected对象采用冻结25/75 categories；equal-n=20是敏感性，raw是描述性参照。raw偏相关、corrected和equal-n回答不同问题，不写成一串逐级调整。
- `real_DEG_burden`展示为threshold-defined response-breadth proxy，按冻结表达下限与绝对log1p-normalized均值差≥0.25计数，不是FDR显著DEG数。
- HCC实测端点资格队列与共同评分子集分开；共同评分空间为47 genes。Replogle完整模型评分为1882×1024。target／gene轴在`manifests/axes/`逐值保存，不能在读者取交集时重新划categories。
- signed cosine度量方向；endpoint排序和AUC不能替代它。oracle不以dependency排序为优化目标，所以其endpoint相关不必等于1。
- identity使用target-label Mantel推断；pairwise entries不是独立样本。H及predicted–observed excess使用target-delete-one jackknife区间，中心化版本每次删一后重新中心化；不覆盖训练seed、细胞层抽样或所有系统误差。
- 常量／零向量的不可定义项按冻结实现保留NA，不以0补齐后声称超过基线。各模型单独的CI/P/q不是模型间差值检验。
- formal、seed sensitivity与diagnostic的BH族保持原声明。seed123正式结果不代表CellOT跨seed稳定；其他模型in-sample检查不变成held-out泛化证据。
