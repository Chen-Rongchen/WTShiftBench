# Stage 1A Baseline Runtime Spec

## 1. 文档定位

本文件是 `Stage 1A` baseline family 的实现层 / runtime spec。

它记录：

- canonical baseline/null family 在实现层的落地口径
- canonical `linear_delta_baseline` 的实现状态
- 允许的线性实例化方案
- fit discipline 与 anti-leakage 纪律

它不改写：

- `docs/protocol_blueprint.md` 的长期制度定义
- blueprint 中对 canonical baseline class 的上位约束
- 当前某个 estimator 选择在长期协议中的地位

## 2. Formal Canonical Family

`Stage 1A` 的 formal canonical family 固定为：

- `zero_shift_null`
- `mean_shift_baseline`
- `linear_delta_baseline`
- `label_shuffle`
- `random_pairing`

说明：

- 这里的 `linear_delta_baseline` 是一个制度类别（baseline class），而不是单一永恒 estimator 名称
- formal adjudication 仍相对上述 canonical family 解释
- implementation 层可以记录补充的 audit-only / sensitivity-only reference，但不得替代上述 canonical family

## 3. 当前仓库状态

当前仓库**尚未**落地 canonical `linear_delta_baseline`。

当前仅保留一个历史兼容实现：

- `linear_delta_baseline_legacy`

说明：

- 该实现本质上是 `deterministic random-feature ridge` 的 legacy 版本
- 它用于历史产物兼容、baseline ladder smoke 与代码路径回归
- 它**不是**当前仓库中可直接上升为 formal canonical `linear_delta_baseline` 的实现
- formal adjudication 若需要引用 canonical linear baseline，应等待独立、明确、可审计的新实现与 runtime registry

## 4. Allowed Linear Variants

允许的线性实例化方案包括：

- `elasticnet_delta_baseline`
- `lowrank_linear_delta_baseline`

其中，`lowrank_linear_delta_baseline` 可以包括但不限于以下形式：

- `PCA + Ridge`
- `TruncatedSVD + Ridge`
- `PLSRegression`

正式说明：

- 上述方案都属于 `linear_delta_baseline` 的 allowed linear instantiations
- 除非未来协议层另行修订，formal canonical baseline class 仍然叫做 `linear_delta_baseline`，而不是把某个实例化方案直接上升为新的协议类别
- 若当前仓库实现采用其中某一种，应在 runtime spec / audit report 中记录版本、特征、超参数与 manifest，而不是回写到 blueprint 里

## 5. Fit Discipline / Anti-Leakage Rules

实现纪律如下：

- 每个 `dataset × split × lane` 独立拟合
- 仅使用 training targets 的合法 `target-side features` 与 `lane-local real_shift`
- 不得查看 held-out truth 后再调整主超参数
- 不得引入外部 phenotype 信息
- 不得跨 dataset pooled fit
- 必须输出 lane-local `predicted_shift`，并与 formal scoring space 对齐后再评分
- 需要在实现文档中保留 estimator choice、feature manifest、regularization registry、random seed policy 与 version identity

## 6. Runtime Registration Expectations

若某次实现实例化 `linear_delta_baseline`，至少应记录：

- `estimator_class`
- `feature_manifest_id`
- `regularization_registry_version`
- `hyperparameter_manifest`
- `random_seed_policy`
- `version_identity`
- `dataset_id`
- `split_seed`
- `lane_id`

说明：

- 这些字段属于 runtime governance，不属于 blueprint 主文
- runtime 层的变更应通过 implementation report、audit report 或 registry manifest 记录
- runtime 记录可以升级，但不得反向改写 `linear_delta_baseline` 在 blueprint 中的制度定义
