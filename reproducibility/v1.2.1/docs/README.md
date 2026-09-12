# WTShiftBench v1.2.1 公开复现候选资产

此目录是A010–A014对应的新版本候选，不是已发布证明；Zenodo由作者同步，新DOI取得并核验前不复用v1.2.0 DOI。五seed CellOT及A013全部18项训练/6项特征检查已完成评分。当前矩阵包应含87个评分输出，训练包含470个CellOT checkpoint；具体成员以各包manifest为准。本地验收记录见`verification_five_seed`，不等于公开下载验证。旧三seed候选与验收独立保留，不冒称新版。

## 版本范围

- A003采样修正对象及25Q3 probability主端点不变。
- 正式CellOT为两context seed123；124–127为同配方训练随机性敏感性，不挑选最好seed、不平均预测。
- A013另外提供18个scGen/CPA/GEARS训练seed输出与6个Replogle随机降维输出；以实际完成记录为准，不更换原正式输出，不把随机降维称为基础模型重训。
- HCC正式18项BH/M4相关性/M6已按新正式集合更新。
- 辅助gene-effect统一25Q3，保留历史HepG2/Jurkat匹配23Q4的逐值证据。
- H及配对excess补target-delete-one jackknife区间，每次删一重新中心化。它不覆盖训练seed或细胞层测量不确定性。

## 冻结矩阵到评分

在解压的归档根目录，使用Pixi：

```sh
pixi run --environment core python recompute.py --verify-only
pixi run --environment core python recompute.py --output recomputed
pixi run --environment core python recompute_auxiliary.py
```

需要分组时使用`--group m3`、`--group m4`、`--group m5`、`--group cellot_training_seeds`、`--group other_training_seeds`或`--group replogle_feature_seeds`。完整运行复算点估计、原bootstrap/置换/BH以及新H区间；`--points-only`仅快速核对点估计，不可当作完整推断验收。

HCC矩阵轴严格匹配，连续统计量容差1e-10。Replogle保存为float32，连续量容差1e-6；P/q和样本数不放宽到float32容差。所有冻结输入先核对SHA256。

## 不混淆的复现路径

主候选包提供带轴观察/预测矩阵、端点/类别、配置/锁文件、评分源码和provenance，因此可以复算评分。辅助入口从归档target级评分重建M6四张表，从提取的25Q3值重算八context GE的ρ/CI/P/q；不把它冒称全官方CSV来源核验。

另外提供CellOT staged训练包（五seed版本含固定输入、源码及470个当前seed checkpoint），支持无外部预训练权重的训练与回放。矩阵包不因附带训练脚本就自动成为所有模型的完整训练包；当前CellOT移植测试范围以该包实际verification记录为准，不声称恢复历史未记录seed。

9月12日本地新Pixi前缀验收：470/470 checkpoint回放通过，最大预测误差3.55×10⁻¹⁵；两context各一项ARID1A的seed123从staged数据重训也通过。不是全部470项移植重训，也不是Zenodo下载验证。原三seed验证记录不替代本次实际结果。

旧M4/M6表在历史路径保留；当前权威结果由`expected/`与`reports/revision/finalization_v2/`指定。不要将旧表和新预测混用。上传后还需实际下载复算，并将新版本DOI回填稿件/回复。
