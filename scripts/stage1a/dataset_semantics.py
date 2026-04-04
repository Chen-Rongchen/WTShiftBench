from __future__ import annotations

import pandas as pd


GENE_SYMBOL_ALIASES = {
    "ATP5C1": "ATP5F1C",
    "ATP5H": "ATP5PD",
    "TMEM55A": "PIP4P2",
    "C19orf26": "CBARP",
    "C3orf72": "FOXL2NB",
    "KIAA1804": "MAP3K21",
}

ADAMSON_CONTROL_TARGETS = frozenset({"63(mod)", "62(mod)", "Gal4-4(mod)"})
ADAMSON_DROP_PERTURBATION_LABELS = frozenset({"", "*"})


def stringify(series: pd.Series) -> pd.Series:
    return series.astype("string").fillna("")


def canonicalize_gene_symbol(symbol: str) -> str:
    token = str(symbol).strip()
    if not token:
        return ""
    return GENE_SYMBOL_ALIASES.get(token, token)


def canonicalize_gene_series(series: pd.Series) -> pd.Series:
    values = stringify(series)
    return values.map(canonicalize_gene_symbol).astype("string")


def parse_adamson_target_series(perturbation: pd.Series) -> pd.Series:
    labels = stringify(perturbation)
    target = pd.Series("", index=labels.index, dtype="string")
    parseable_mask = labels.str.contains("_", regex=False)
    if parseable_mask.any():
        parsed = labels.loc[parseable_mask].str.rsplit("_", n=1, expand=True)
        target.loc[parseable_mask] = parsed[0].astype("string")
    target = target.where(~labels.isin(ADAMSON_DROP_PERTURBATION_LABELS), other="")
    return target.astype("string")


def is_adamson_control_target(series: pd.Series) -> pd.Series:
    target = stringify(series)
    return target.isin(ADAMSON_CONTROL_TARGETS)
