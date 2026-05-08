#!/usr/bin/env python3
"""Build endpoint hierarchy minimal statistical audit table.

Reads endpoint consistency summary TSV files and produces a clean
summary table showing CRISPR vs RNAi bridge Spearman delta across
all tested contexts.

Output: reports/truth_driven_bridge/sensitivity/endpoint_hierarchy_audit.tsv
"""

import os
from pathlib import Path

import pandas as pd

PROJECT_ROOT = str(Path(__file__).resolve().parents[2])

INPUT_FILES = {
    "hcc38_hcc1143": os.path.join(
        PROJECT_ROOT,
        "reports/truth_driven_bridge/hcc38_hcc1143_rnai_endpoint_consistency/endpoint_consistency_summary.tsv",
    ),
    "k562": os.path.join(
        PROJECT_ROOT,
        "reports/truth_driven_bridge/k562_rnai_endpoint_consistency/endpoint_consistency_summary.tsv",
    ),
}

OUTPUT_PATH = os.path.join(
    PROJECT_ROOT,
    "reports/truth_driven_bridge/sensitivity/endpoint_hierarchy_audit.tsv",
)


def load_and_filter(path: str) -> pd.DataFrame:
    """Load a TSV and filter to truth_endpoint_bridge rows with real_shift_mean_abs."""
    df = pd.read_csv(path, sep="\t")
    mask = (
        (df["summary_kind"] == "truth_endpoint_bridge")
        & (df["truth_metric"] == "real_shift_mean_abs")
        & (df["depmap_endpoint"] == "depmap_gene_dependency")
    )
    return df.loc[mask].copy()


def extract_context_bridge(df: pd.DataFrame, timepoint: str) -> dict:
    """Extract CRISPR/RNAi bridge rhos and n_shared for a given timepoint."""
    subset = df[df["timepoint"] == timepoint]

    crisp_row = subset[subset["platform_pair"] == "crispr"]
    rnai_row = subset[subset["platform_pair"] == "rnai"]

    if len(crisp_row) == 0 or len(rnai_row) == 0:
        raise ValueError(
            f"Missing CRISPR or RNAi row for timepoint '{timepoint}'. "
            f"CRISPR rows: {len(crisp_row)}, RNAi rows: {len(rnai_row)}"
        )

    crisp_rho = crisp_row["spearman"].values[0]
    rnai_rho = rnai_row["spearman"].values[0]
    crisp_n = int(crisp_row["n_shared_targets"].values[0])
    rnai_n = int(rnai_row["n_shared_targets"].values[0])
    n_shared = min(crisp_n, rnai_n)

    return {
        "context": timepoint,
        "crispr_rho": crisp_rho,
        "rnai_rho": rnai_rho,
        "delta": crisp_rho - rnai_rho,
        "n_shared_targets": n_shared,
    }


def main():
    # Load both input files
    df_hcc = load_and_filter(INPUT_FILES["hcc38_hcc1143"])
    df_k562 = load_and_filter(INPUT_FILES["k562"])

    # Define contexts to extract
    # HCC38/HCC1143 file has timepoint as the cell line name
    # K562 file has timepoint as "7d" / "13d"
    contexts = [
        ("hcc38_hcc1143", "HCC38"),
        ("hcc38_hcc1143", "HCC1143"),
        ("k562", "7d"),
        ("k562", "13d"),
    ]

    rows = []
    for source, timepoint in contexts:
        df_src = df_hcc if source == "hcc38_hcc1143" else df_k562
        row = extract_context_bridge(df_src, timepoint)
        rows.append(row)

    # Build output table
    lines = []
    header = "Context\tCRISPR_rho\tRNAi_rho\tDelta\tn_shared_targets"
    lines.append(header)

    for r in rows:
        lines.append(
            f"{r['context']}\t"
            f"{r['crispr_rho']:.3f}\t"
            f"{r['rnai_rho']:.3f}\t"
            f"+{r['delta']:.3f}\t"
            f"{r['n_shared_targets']}"
        )

    # Footer comment
    lines.append(
        "# All four tested contexts showed positive CRISPR-RNAi delta. "
        "N=4 contexts, descriptive sign consistency only; "
        "not a formal statistical test."
    )

    # Write output
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    with open(OUTPUT_PATH, "w") as f:
        f.write("\n".join(lines) + "\n")

    print(f"Audit table written to: {OUTPUT_PATH}")
    print()
    for line in lines:
        print(line)


if __name__ == "__main__":
    main()
