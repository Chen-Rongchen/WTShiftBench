# 主文稿 Results 草案 v1

## 1. Result 1：GEARS 在 HCC primary adjudication 中表现为 architecture trade-off diagnosis，而非 primary winner

我们首先评估了当前 strongest formal entrant `GEARS` 在 `HCC38 / HCC1143` 真实 HCC mainline 中对 frozen architecture 的恢复能力。当前结果不支持将 `GEARS` 写成 HCC primary 路线上的整体胜者。相反，更稳的解释是：`GEARS` 展现出选择性结构优势，但其主要价值在于揭示 architecture-level trade-off，而不是整体压过 `shared_mean_baseline`。

具体来说，`GEARS` 在 `structure vs context separation` 上稳定优于 `shared_mean_baseline`，并在 `HCC1143` 上表现出更强的 `shift-excess identification`；然而，在两个 cell line 上，`canonical_backbone recovery` 均仍落后于 `shared_mean_baseline`。跨细胞系均值上，`shared_mean_baseline` 的 backbone recovery 为 `0.807`，而正式 `GEARS` recipe 为 `0.660`；相对地，`GEARS` 的 structure-vs-context separation 为 `0.428`，高于 `shared_mean_baseline` 的 `0.353`。因此，`GEARS` 当前更像一个 `structure/context separation` 偏置的 entrant，而不是 backbone recovery 更强的主胜者。

在完成有限预算 backbone sweep 后，这一判断进一步稳定。虽然若干 sweep 候选继续提升了 `shift-excess identification` 或 `structure vs context separation`，但没有任何候选接近或追平 `shared_mean_baseline` 的 backbone recovery，也没有候选超过当前正式 `GEARS` recipe 的 backbone 表现。预先冻结的 stop rule 因而被触发，使 `GEARS` 在本阶段的最合理定位收敛为 `architecture trade-off diagnosis`。

更重要的是，这一 backbone gap 当前不能再简单归因于 entrant 尚未正式接入。到目前为止，`GEARS / scGPT / Geneformer / lm_train_lowrank / lm_G_scgpt_ridge / lm_G_geneformer_ridge` 均已进入同一份 HCC formal comparison，两条 embedding ablation control 也已经实现 `1.000` target coverage。当前更稳的解释是：HCC task 中的 `canonical backbone` 本身具有很强的 shared component，因此 `shared_mean_baseline` 已经是一个很强的 backbone estimator；相比之下，复杂 entrant 所学习到的额外能力更倾向于 `structure/context separation`、`shift-excess identification` 或 context-sensitive deviation，而这些优势并未稳定转化为更强的 backbone recovery。与此一致，`lm_G_scgpt_ridge` 与 `lm_G_geneformer_ridge` 的 backbone failure 都更接近 `direction`，说明当前 gap 更像是 backbone 主方向恢复偏弱，而不是单纯的幅度不足。

因此，若后续仍要继续推进这条解释线，更稳的默认拆法也不再是重复问“模型为什么打不过 baseline”，而是先把两个更小的问题钉死：`baseline winner` 是否主要由 shared backbone objective 决定，以及 entrant 的额外能力是否稳定落在 `separation / deviation` 而不是 backbone 上。在这两点没有进一步收紧前，biology-facing explanation 仍不应升级成主结论。

更短的 Results-style 写法可以直接固定为：后续对 baseline-vs-model gap 的推进应优先聚焦于两个方法学问题，即 `baseline winner` 是否主要由 shared backbone objective 决定，以及 entrant gain 是否主要落在 `separation / deviation` 而非 backbone；在此之前，biology-facing explanation 仍只应保留为 plausible interpretation。

## 2. Result 2：truth–DepMap bridge 可分解为 stable target-level anchors 与 limited formal axis evidence

在 truth-side，我们将原先较粗的整体 bridge 现象进一步分解为两个递进层次。第一层是 `target-level joint bridge`，即 transcriptomic impact 与 aligned dependency 同时处于高位的少数结构上稳定 anchors。当前最稳的 shared anchors 包括 `PFDN5`、`PMF1`、`PRPF6` 与 `ZNF131`。这些对象的重要性不在于单基因幅度本身，而在于它们在多组 cutoff 设定下持续保持 anchor 身份，并支持 transcriptomic impact 与 cellular dependency 之间存在结构化耦合。需要同时强调的是，当前 covariate audit 已显示：`structural stability` 与 `covariate cleanliness` 不能简单等同，因此这些对象当前更适合作为分层化 bridge evidence，而不是统一意义上的 fully deconfounded strongest anchors；其中，`PFDN5` 最多只能写成 `primary_but_qualified`，而 `PMF1 / PRPF6 / ZNF131` 当前只能写成 `supporting_only`。与此同时，混杂线当前更准确的状态应写成：已完成第一轮多轴 covariate audit，并已据此完成对象级降级治理，但 full closure 仍受实验设计元数据上限约束。

第二层是 `axis-level explanatory structure`。与 target-level anchors 相比，这一层当前证据明显更保守。按照 `n_targets >= 2` 的 formal call 约束以及 bootstrap stability 审计，当前 formal axis evidence 总体仍然有限。其中，`transcription / chromatin` 是目前唯一同时满足 formal criteria 且在 bootstrap 下保持稳定的正向 axis，但当前最多只能写成 `primary_axis_but_qualified`；其余 axis 多数仍应保留为 supporting、unstable 或 preliminary lines of evidence。因而，当前结果支持的是“存在可治理、可分层的 truth–DepMap bridge structure”，而不是“多数 axis 已完成正式闭环”或“shared explanatory architecture 已全面建立”。

## 3. Result 3：frozen axis 已完成第一轮 annotation 与 validation，但整体仍应保持 partially supported axes

在 axis 层，我们完成了第一轮 `annotation + validation + tiering`，使当前 frozen structure 不再只是未命名的几何对象，而具备了可进入主文写作的解释边界。当前更稳的 axis 包括 `transcription / chromatin`、`chromatin remodeling`、`TGF-beta / BMP signaling`、`ER stress / UPR`、`RNA processing / spliceosome`、`ribosome biogenesis / nucleolar` 与 `ribosomal / translation`。其中，`transcription / chromatin` 是当前最稳的一条 formal positive axis，但最多只能写成 `primary_axis_but_qualified`；其他 axis 虽获得了方向一致的 enrichment 或 per-target consistency 支持，但多数仍未达到 fully established functional axis 的主张上限。

因此，当前 axis 结果最合适的总体表述是：多数 frozen axes 已获得部分支持，但支持强度不均匀；现阶段更适合将其写成 `partially supported axes`，而不是 fully closed architecture。换句话说，当前工作的主要贡献，不在于证明一个已经完全闭合的模块架构，而在于完成了第一轮 annotation、validation 与 evidence tiering，使哪些 axis 可以进入更强层级、哪些 axis 必须保守表述，已经具备清晰边界。

## 4. Result 4：Dixit/K562 在 supplementary 层面支持 architecture existence，但 dominant macro-class remains context-specific

为检验 architecture 是否具有跨 context 的可复制性，我们进一步考察了 `Dixit/K562` 这一 supplementary external structure replication 对象。当前结果表明，`K562` 中同样可以观察到 `canonical backbone` 与 `shift-excess` 两类结构成分，因此支持 architecture existence 在外部 context 中具有一定可复制性。然而，这种复现主要停留在结构层，而非主导功能类别层。相较于 HCC 中以 `gene expression machinery` 为主的 backbone，`K562` 的 dominant backbone 更偏 `biosynthetic support / mitochondrial metabolism`，且其 shift-excess macro class 仍未得到稳定命名。

按当前 supplementary evidence-tier 口径，`architecture existence` 与 `canonical backbone present` 可保留为 `supplementary_confirmed`；`shift-excess present` 与 context-specific backbone macro class 更适合保留为 `supplementary_supporting`；而 `shift-excess macro class` 及多数单条 K562 axis 仍应保持 `preliminary`。因此，`Dixit/K562` 当前支持的是 supplementary-level architecture replication，而不是与 HCC 对称的 primary shared architecture evidence。

## 5. Result 5：Stage 1A / 1B 在 truth-first 主线下应被重写为 failure decomposition track

在 truth-first 主线下，`Stage 1A / 1B` 的作用也需要被重新解释。`Stage 1A` 不再只是 short-horizon leaderboard，而应被理解为 `short-horizon failure decomposition`：它更适合回答模型丢掉的是 backbone、shift-excess，还是 context-specific deviation，并判断这些 failure mode 是否在 formal held-out / multi-split 下稳定存在。相应地，`Stage 1B` 不再只是 long-horizon stress test，而应被理解为 `long-horizon / temporal failure decomposition`：它更适合判断 short-horizon 中已出现的 failure mode 是否在 external time-aligned truth 中进一步放大为 `temporal structure degradation`。

因此，`Stage 1A / 1B` 当前最重要的价值，不是提供一组脱离结构语义的排名，而是为 `Stage 2` 的 architecture adjudication 提供结构化失败解释层。它们解释的是 model failure，而不是新 truth object，也不应与 truth-side discovery 或 HCC primary biological conclusion 竞争同一层级。

## 6. Result Summary

综合以上结果，我们认为本项目已经完成从“现象级相关”到“分层化结构证据”的第一轮收口。当前最稳的主张包括：`GEARS` 在 HCC primary adjudication 中应被定位为 `architecture trade-off diagnosis`；`truth–DepMap bridge` 由少数结构上稳定、但需按 `PFDN5 = primary_but_qualified`、`PMF1 / PRPF6 / ZNF131 = supporting_only` 继续分层书写的 anchors 与有限 formal axis evidence 共同支撑；frozen axis 已完成第一轮 `annotation + validation + tiering`，但整体仍应保持 `partially supported axes`，其中 `transcription / chromatin` 最多只能写成 `primary_axis_but_qualified`；`Dixit/K562` 在 supplementary 层面支持 architecture existence，但其 dominant macro-class remains context-specific；`Stage 1A / 1B` 则应被重写为 frozen truth architecture 下的 `failure decomposition track`。同时，当前 entrant family comparison 还表明，复杂模型之所以不能稳定胜过 baseline，最主要不是接入错误或 coverage 缺口，而是 shared canonical backbone 本身较强，而 entrant 学到的额外结构优势更偏 separation / deviation 方向，尚未稳定转化为 backbone superiority。这些结果共同说明，当前阶段最重要的进展不是得到了更多信号，而是 evidence tier、claim strength 与 model-failure explanation 已被系统对齐，从而使整体叙事更加清晰、可信且可防守。

若继续向后推进，当前默认也不应再把 baseline-vs-model explanation 保留为开放式泛问题，而应先回答 `baseline winner 是否主要由 backbone objective 决定` 与 `entrant extra capability 是否主要落在 separation / deviation` 这两个更小的问题。
