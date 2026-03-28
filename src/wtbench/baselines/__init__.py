"""WT Benchmark baselines package."""

from wtbench.baselines.linear_utils import (
    build_gene_embedding_from_shift_pca,
    build_target_embedding_from_lookup,
    solve_bilinear_ridge_closed_form,
    predict_shift_from_gwp,
    validate_target_lookup_coverage,
    TargetLookupSpace,
)

from wtbench.baselines.linear_pca_shift_baseline import (
    build_linear_pca_shift_baseline,
    LinearPCAShiftConfig,
    LinearPCAShiftResult,
    DEFAULT_N_COMPONENTS,
    DEFAULT_RIDGE_LAMBDA,
)

from wtbench.baselines.linear_external_p_shift_baseline import (
    build_linear_external_p_baseline,
    LinearExternalPConfig,
    LinearExternalPResult,
    load_external_embeddings_from_file,
)

__all__ = [
    "build_gene_embedding_from_shift_pca",
    "build_target_embedding_from_lookup",
    "solve_bilinear_ridge_closed_form",
    "predict_shift_from_gwp",
    "validate_target_lookup_coverage",
    "TargetLookupSpace",
    "build_linear_pca_shift_baseline",
    "LinearPCAShiftConfig",
    "LinearPCAShiftResult",
    "DEFAULT_N_COMPONENTS",
    "DEFAULT_RIDGE_LAMBDA",
    "build_linear_external_p_baseline",
    "LinearExternalPConfig",
    "LinearExternalPResult",
    "load_external_embeddings_from_file",
]
