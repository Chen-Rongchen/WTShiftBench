# 当前与历史来源

当前formal CellOT是两context的seed123；124–127为训练seed敏感性。训练配方登记、正式升级和后续seed扩展不是同一时点，见冻结A010–A014与selection chronology。不能把结果已知后的正式升级倒写成原投稿前预先指定；不把seed123说成最好seed，也不平均预测。

`run_registry.tsv`是87个评分输出的自动索引，不取代原始训练登记。NA/未记录不填0。CPA/GEARS的CLI seed、数据拆分seed和实际初始化seed可能不同，完整含义以`reports/revision/finalization_v2/m4/model_training_evaluation_registry.tsv`及实际配置为准。Replogle feature seed不是基础模型的重新训练seed。

`depmap_provenance.tsv`区分当前25Q3与历史数值匹配。历史恢复记录里的“尚未确认”属于当时状态；最新GE正式输入见`reports/revision/finalization_v2/depmap/`，历史HepG2／Jurkat逐值和missing匹配23Q4的记录保留但不送入当前评分。

本目录保留科学来源、运行和选择时间线，不保留审稿原信或作者私人讨论。历史日志中的机器路径仅描述当次运行，不是公开执行依赖。原包source commit若来自原分析工作树，仅与所记录文件hash一起描述来源；本次公开代码commit另由外层release manifest记录。
