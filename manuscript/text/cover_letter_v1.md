# Genome Biology cover letter v1

Dear Editors,

We are pleased to submit our Research article, "A truth-anchored framework and resource for evaluating transcriptomic perturbation models against cancer dependency endpoints", for consideration in Genome Biology.

Perturbation transcriptome models are increasingly used to reason about gene function, cellular response and disease-relevant biology. However, these models are commonly evaluated by expression reconstruction rather than by recovery of transcriptomic structures linked to downstream phenotypes. This leaves an important gap for functional genomics: a model may predict expression shifts without recovering the components of a perturbation response that align with fitness or dependency. Prior benchmarks have independently shown that simple baselines can match or exceed deep-learning entrants on expression reconstruction, confirming that expression accuracy and phenotype relevance are distinct evaluation dimensions.

In this study, we present a truth-first, architecture-aware framework for perturbation-model evaluation in cancer functional genomics. The framework consists of seven independently defined elements: (1) truth object definition via pre-specified perturbation-to-dependency bridge construction, (2) architecture decomposition into backbone recovery, shift-excess identification and structure-versus-context separation, (3) covariate-aware anchor tiering with explicit evidence governance, (4) architecture-aware model recovery adjudication against a frozen truth object, (5) finite-budget rebuttal tests with pre-specified stop rules, (6) claim-boundary tiering (A0/A1/B) for external evidence, and (7) endpoint hierarchy designation. We demonstrate the framework in the breast-cancer cell-line contexts HCC38 and HCC1143, with supplementary temporal evidence from K562.

The framework yields several findings. Architecture-aware adjudication reveals an asymmetric recovery pattern: the shared-mean baseline achieves the strongest canonical backbone recovery (0.807 versus 0.660 for the formal GEARS recipe), whereas GEARS shows stronger structure-versus-context separation (0.428 versus 0.353). This pattern persists under finite-budget hyperparameter sweeps, embedding-based linear controls and coverage audits. Temporal analysis in K562 reveals that early (7-day) perturbation responses show stronger rank alignment with dependency than later (13-day) responses, despite the latter having larger perturbation magnitude—a temporal stratification with implications for perturbation-experiment design. An exploratory pathway-response analysis further reveals that anchor genes can maintain strong fitness-dependency linkage while their downstream pathway execution programs diverge across cell-line contexts, suggesting that fitness anchoring and transcriptional response wiring are partially dissociable properties. CRISPR DepMap consistently exceeds RNAi DEMETER2 as a bridge endpoint across all four tested contexts, establishing a clear endpoint hierarchy for future benchmarking.

We believe this manuscript fits Genome Biology because it addresses a functional-genomics evaluation problem from a genomic and post-genomic perspective. The work is not framed as a new software tool or a target-discovery claim. Instead, it provides a principled, reproducible framework with explicit claim governance—each figure is accompanied by panel-level source data, SHA256-hashed manifests, and frozen scoring artifacts. The framework is designed for extension to future cell-line contexts, endpoints and model entrants, making it a resource for the perturbation-modeling community rather than a single-use benchmark.

This manuscript is original, is not under consideration elsewhere, and all authors have approved its submission to Genome Biology. [Competing interest statement to be inserted.]

Sincerely,

[Corresponding author name]

[Institution]

[Email]
