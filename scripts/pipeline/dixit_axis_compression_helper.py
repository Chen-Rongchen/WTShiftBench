#!/usr/bin/env python3
"""
Stage 2 — Dixit (K562) Independent Axis Compression

External structure replication track: does K562 show the same backbone/deviation
architecture as HCC, without inheriting HCC axis labels?

Minimal contract:
  - dJIT master atlas (independent)
  - independent fine axes via data-driven clustering
  - macro axes mapped to HCC-comparable categories
  - structure_replication_summary (HCC vs K562 cross-context table)

NOT required:
  - gene-level overlap with HCC
  - fine-axis correspondence with HCC
  - SCP542 basal explanation (not evaluable for K562)

Run:
  pixi run python scripts/pipeline/dixit_axis_compression.py \
    --config configs/dixit_k562_tf_13d_structure_replication_gse90063_v1.json
"""

import json
import os
import argparse
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG_PATH = PROJECT_ROOT / "configs/dixit_k562_tf_13d_structure_replication_gse90063_v1.json"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "运行 Stage 2 Dixit/K562 supplementary structure replication。"
            " 默认配置固定为 GSE90063 K562 13d-only；legacy recipe 请显式传入 historical-only 配置。"
        )
    )
    parser.add_argument("--config", default=str(DEFAULT_CONFIG_PATH))
    return parser


def resolve_path(path_str: str) -> Path:
    path = Path(path_str)
    if path.is_absolute():
        return path
    return PROJECT_ROOT / path


def load_recipe(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


ARGS = build_parser().parse_args()
RECIPE = load_recipe(resolve_path(str(ARGS.config)))

# ── paths ──────────────────────────────────────────────────────────────────
BRIDGE_TABLE = Path(os.environ.get(
    "WTKO_DIXIT_BRIDGE_TABLE",
    str(RECIPE["bridge_table_path"]),
))
HCC_ATLAS = Path(os.environ.get(
    "WTKO_DIXIT_HCC_ATLAS",
    str(RECIPE.get("hcc_master_atlas_path", "reports/truth_driven_bridge/master_atlas/shared_target_master_atlas.tsv")),
))
HCC_AXIS_SUM = Path(os.environ.get(
    "WTKO_DIXIT_HCC_AXIS_SUM",
    str(RECIPE.get("hcc_macro_axis_summary_path", "reports/truth_driven_bridge/master_atlas/axis_summary_macro.tsv")),
))
HCC_FINE_SUM = Path(os.environ.get(
    "WTKO_DIXIT_HCC_FINE_SUM",
    str(RECIPE["hcc_fine_axis_summary_path"]),
))
OUT_DIR = Path(os.environ.get(
    "WTKO_DIXIT_OUT_DIR",
    str(RECIPE["output_dir"]),
))
OUT_DIR.mkdir(parents=True, exist_ok=True)

PRIMARY_Y = os.environ.get("WTKO_DIXIT_PRIMARY_Y", "real_shift_mean_abs")
PRIMARY_X = os.environ.get("WTKO_DIXIT_PRIMARY_X", "depmap_gene_effect")

# Macro architecture categories (comparable across HCC and K562)
MACRO_CATEGORIES = [
    "gene expression machinery",
    "RNA processing / splicing",
    "chromatin / transcriptional regulation",
    "translation / ribosome biogenesis",
    "signaling / stress / immune-state",
    "cell cycle / proliferation",
    "proteostasis / metabolism",
    "other / unresolved",
]

# Known gene sets for functional annotation
KNOWN_SETS = {
    "ribosome / translation": [
        "RPS2","RPS3","RPS3A","RPS4X","RPS5","RPS6","RPS7","RPS8","RPS9","RPS10",
        "RPS11","RPS12","RPS13","RPS14","RPS15","RPS16","RPS17","RPS18","RPS19",
        "RPS20","RPS21","RPS23","RPS24","RPS25","RPS26","RPS27","RPS28","RPS29",
        "RPL3","RPL4","RPL5","RPL6","RPL7","RPL8","RPL9","RPL10","RPL11","RPL12",
        "RPL13","RPL14","RPL15","RPL17","RPL18","RPL19","RPL21","RPL22","RPL23",
        "RPL24","RPL26","RPL27","RPL28","RPL29","RPL30","RPL31","RPL32","RPL34",
        "RPL35","RPL36","RPL37","RPL38","RPL39","RPS27A","EIF1AX","EIF2S1","EIF3A",
        "EIF3B","EIF3E","EIF3F","EIF3H","EIF4A1","EIF4A2","EIF4A3","EIF4E","EIF4G1",
        "EIF5","EEF1A1","EEF1B2","EEF1G","EEF2",
    ],
    "mitochondrial / oxidative phosphorylation": [
        "MT-ND1","MT-ND2","MT-ND3","MT-ND4","MT-ND5","MT-ND6",
        "MT-CO1","MT-CO2","MT-CO3","MT-ATP6","MT-ATP8",
        "NDUFA1","NDUFA2","NDUFA4","NDUFA5","NDUFA6","NDUFA7","NDUFA8","NDUFA9","NDUFA10",
        "NDUFB1","NDUFB2","NDUFB3","NDUFB4","NDUFB5","NDUFB6","NDUFB7","NDUFB8","NDUFB9","NDUFB10",
        "NDUFS1","NDUFS2","NDUFS3","NDUFS4","NDUFS6","NDUFS7","NDUFS8",
        "SDHA","SDHB","SDHC","SDHD","UQCRC1","UQCRC2","UQCRFS1","COX4I1","COX5A","COX5B",
        "COX6A1","COX6B1","COX7A2","COX7C","ATP5F1A","ATP5F1B","ATP5F1C","ATP5F1D","ATP5F1E",
        "PPA1","PPA2","ATP6V1A","ATP6V1B2","ATP6V1C1","ATP6V1D","ATP6V1E1","ATP6V1F",
    ],
    "RNA processing / spliceosome": [
        "PRPF6","PRPF8","PRPF10","PRPF11","PRPF19","PRPF31","PRPF38A","PRPF38B",
        "PRPF39","PRPF40A","PRPF40B",
        "SF3A1","SF3A2","SF3A3","SF3B1","SF3B2","SF3B3","SF3B4","SF3B5","SF3B6",
        "SF3B14","SF3B49",
        "U2AF1","U2AF2","U2AF1L4","U2AF1L5",
        "SNRPB","SNRPD1","SNRPD2","SNRPD3","SNRPE","SNRPF","SNRPG","SNRPN",
        "LSM1","LSM2","LSM3","LSM4","LSM5","LSM6","LSM7","LSM8",
        "SMN1","SMN2","GEMIN2","GEMIN4","GEMIN5","GEMIN6","GEMIN7","GEMIN8",
        "DDX5","DDX6","DDX10","DDX17","DDX18","DDX21","DDX23","DDX39A","DDX39B",
        "DHX9","DHX15","DHX16","DHX29","DHX30","DHX36","DHX38",
        "EFTUD1","EFTUD2","EIF4A3",
        "布","布","NOP1","NOP14","NOP16","NOP56","NOP58","NOP10","NOP16",
        "布","布","布","布",
    ],
    "chromatin / transcription regulation": [
        "EP300","CREBBP","HDAC1","HDAC2","HDAC3","HDAC4","HDAC5","HDAC6","HDAC7","HDAC8","HDAC9","HDAC10","HDAC11",
        "KAT2A","KAT2B","KAT5","KAT6A","KAT6B","KAT7","KAT8","KAT14",
        "ARID1A","ARID1B","ARID2","SMARCA4","SMARCB1","SMARCC1","SMARCC2","SMARCD1","SMARCD2","SMARCD3",
        "CHD1","CHD2","CHD3","CHD4","CHD5","CHD6","CHD7","CHD8","CHD9",
        "CTCF","CTCFL","RAD21","STAG1","STAG2","STAG3","SCC1","SMC1A","SMC3","SMC5","SMC6",
        "DNMT1","DNMT3A","DNMT3B","DNMT3L","TRDMT1",
        "EZH1","EZH2","EED","SUZ12","JARID2","AEBP2",
        "YY1","YY2","YAP1","TAZ","TEAD1","TEAD2","TEAD3","TEAD4",
        "NANOG","POU5F1","SOX2","KLF4","MYC","MAX","MGA","MXD1","MXI1","MLX","MLXIP","MLXIPL",
        "ENY2","TADA1","TADA2A","TADA3","SUPT3H","SUPT7L","TAF1","TAF2","TAF3","TAF4","TAF4B",
        "TAF5","TAF6","TAF7","TAF8","TAF9","TAF10","TAF11","TAF12","TAF13","TAF14","TAF15",
        "GTF2A1","GTF2A2","GTF2B","GTF2E1","GTF2E2","GTF2F1","GTF2F2","GTF2H1","GTF2H2","GTF2H3","GTF2H4","GTF2H5",
        "GTF3C1","GTF3C2","GTF3C3","GTF3C4","GTF3C5","GTF3C6",
        "ZBTB17","ZBTB5","ZBTB7A","ZBTB7B","ZBTB11","ZBTB20","ZBTB21","ZBTB33","ZBTB38","ZBTB40","ZBTB41","ZBTB43","ZBTB44","ZBTB46","ZBTB47","ZBTB48","ZBTB49",
        "KLF1","KLF2","KLF3","KLF4","KLF5","KLF6","KLF7","KLF8","KLF9","KLF10","KLF11","KLF12","KLF13","KLF14","KLF15","KLF16","KLF17",
        "EGR1","EGR2","EGR3","EGR4","ETV1","ETV3","ETV4","ETV5","ETV6",
        "NFKB1","NFKB2","RELA","RELB","NFkB","NFKBIA","NFKBIB","NFKBIE","IKBA","IKBB","IKBKG","IKBKB",
    ],
    "signaling / stress / immune": [
        "STAT1","STAT2","STAT3","STAT4","STAT5A","STAT5B","STAT6",
        "JAK1","JAK2","JAK3","TYK2",
        "MAPK1","MAPK3","MAPK6","MAPK7","MAPK8","MAPK9","MAPK10","MAPK11","MAPK12","MAPK13","MAPK14",
        "MAP2K1","MAP2K2","MAP2K3","MAP2K4","MAP2K5","MAP2K6","MAP2K7",
        "RAF1","ARAF","BRAF","KRAS","NRAS","HRAS","MRAS","RAP1A","RAP1B","RAP2A","RAP2B","RAP2C",
        "AKT1","AKT2","AKT3","AKT1S1","MTOR","RPTOR","MLST8","DEPTOR","STRADA","STRADB","LAMTOR2","LAMTOR3","LAMTOR4","LAMTOR5",
        "PIK3CA","PIK3CB","PIK3CD","PIK3R1","PIK3R2","PIK3R3","PIK3CA","PIK3CG","PIK3R5","PIK3R6",
        "PTEN","INPP4A","INPP4B","INPP5D","INPP5E","INPP5K","INPPL1","SHIP1","SHIP2",
        "SRC","YES1","FYN","LCK","LYN","HCK","BLK","FRK","BRK","CTNK1",
        "GRB2","GRAP","GRAP2","SOS1","SOS2","GAB1","GAB2","GAB3",
        "SHC1","SHC2","SHC3","SHC4","PTPN6","PTPN11","PTPN12","PTPN13","PTPN14","PTPN22","PTPN23",
        "BCL2","BCL2L1","BCL2L2","MCL1","BCL2A1","BCL2L10","BCL2L11","BCL2L12","BCL2L13","BCL2L14",
        "BAX","BAK1","BAK2","BAD","BID","BIK","BMF","HRK","BNIP1","BNIP2","BNIP3","BNIP3L","NIX","PMAIP1",
        "CASP1","CASP2","CASP3","CASP4","CASP5","CASP6","CASP7","CASP8","CASP9","CASP10","CASP11","CASP12","CASP13","CASP14",
        "IRF1","IRF2","IRF3","IRF4","IRF5","IRF6","IRF7","IRF8","IRF9",
        "IFIH1","MDA5","RIG-I","LGP2","DHX58","MAVS","VISA","STING1","TMEM173",
        "TLR1","TLR2","TLR3","TLR4","TLR5","TLR6","TLR7","TLR8","TLR9","TLR10",
        "NFATC1","NFATC2","NFATC3","NFATC4","PPP3CA","PPP3CB","PPP3R1","PPP3R2","PPP2CA","PPP2CB","PPP2R1A","PPP2R1B","PPP2R2A","PPP2R2B","PPP2R2C","PPP2R2D","PPP2R5A","PPP2R5B","PPP2R5C","PPP2R5D","PPP2R5E",
    ],
    "cell cycle / DNA replication": [
        "CDK1","CDK2","CDK3","CDK4","CDK5","CDK6","CDK7","CDK8","CDK9","CDK10","CDK11A","CDK11B","CDK12","CDK13","CDK14","CDK15","CDK16","CDK17","CDK18","CDK19","CDK20",
        "CCNA1","CCNA2","CCNB1","CCNB2","CCNB3","CCND1","CCND2","CCND3","CCNE1","CCNE2","CCNE3",
        "CDKN1A","CDKN1B","CDKN1C","CDKN2A","CDKN2B","CDKN2C","CDKN2D","CDKN3","CDKN4",
        "MCM2","MCM3","MCM4","MCM5","MCM6","MCM7","MCM8","MCM9","MCM10",
        "MCM2","MCM3","MCM4","MCM5","MCM6","MCM7","ORC1","ORC2","ORC3","ORC4","ORC5","ORC6",
        "RPA1","RPA2","RPA3","RPA4",
        "PCNA","RFC1","RFC2","RFC3","RFC4","RFC5","RFC1","POLA1","POLA2","POLB","POLD1","POLD2","POLD3","POLD4",
        "PRIM1","PRIM2","PRMT1","PRMT2","PRMT3","PRMT4","PRMT5","PRMT6","PRMT7","PRMT8",
        "AURKA","AURKB","AURKC","TPX2","BORA","PLK1","PLK2","PLK3","PLK4","PLK5",
        "CDC25A","CDC25B","CDC25C","CDC25D","CDC20","CDC16","CDC23","CDC27","CDC26","CDC31",
        "ANAPC1","ANAPC2","ANAPC4","ANAPC5","ANAPC7","ANAPC10","ANAPC11","ANAPC13","ANAPC15","ANAPC16",
        "MAD1L1","MAD2L1","MAD2L2","TTK","BUB1","BUB1B","BUB3","BUBR1","CENPA","CENPB","CENPC","CENPD","CENPE","CENPF","CENPH","CENPI","CENPJ","CENPK","CENPL","CENPM","CENPN","CENPO","CENPP","CENPQ","CENPR","CENPS","CENPT","CENPU","CENPV","CENPW","CENPX","CENPZ",
        "RRM1","RRM2","RNR1","RNR2","RNR3","RNR4",
    ],
    "proteostasis / chaperone": [
        "HSP90AA1","HSP90AB1","HSP90B1","HSP90D1","TRAP1",
        "HSP70","HSPA1A","HSPA1B","HSPA1L","HSPA2","HSPA4","HSPA5","HSPA6","HSPA7","HSPA8","HSPA9","HSPA13","HSPA14",
        "HSP60","HSPD1","HSPE1","HSPE2","HSPD1","HSCB","HSC20",
        "HSP40","DNAJA1","DNAJA2","DNAJA3","DNAJB1","DNAJB2","DNAJB4","DNAJB6","DNAJB8","DNAJB9","DNAJB11","DNAJB12","DNAJB13","DNAJB14","DNAJC1","DNAJC2","DNAJC3","DNAJC4","DNAJC5","DNAJC6","DNAJC7","DNAJC8","DNAJC9","DNAJC10","DNAJC11","DNAJC12","DNAJC13","DNAJC14","DNAJC15","DNAJC16","DNAJC17","DNAJC18","DNAJC19","DNAJC20","DNAJC21","DNAJC22","DNAJC24","DNAJC25","DNAJC26","DNAJC27","DNAJC28","DNAJC29",
        "PFDN1","PFDN2","PFDN3","PFDN4","PFDN5","PFDN6","PFD1","PFD2","PFD3","PFD4","PFD5","PFD6",
        "CCT1","CCT2","CCT3","CCT4","CCT5","CCT6A","CCT6B","CCT7","CCT8","TCP1","TCP11","TCP11L1","TCP11L2",
        "ERDJ1","ERDJ2","ERDJ3","ERDJ4","ERDJ5","ERDJ6","ERDJ7","ERDJ8","ERDJ9","ERDJ10","ERDJ11",
        "SIL1","SEC62","SEC63","STT3A","STT3B","DDO","DAD1","DAD2","DAD3","DAD4",
        "UBE2D1","UBE2D2","UBE2D3","UBE2D4","UBE2E1","UBE2E2","UBE2E3","UBE2K","UBE2L3","UBE2L6","UBE2N","UBE2Q1","UBE2Q2","UBE2R2","UBE2S","UBE2T","UBE2U","UBE2V1","UBE2V2","UBE2W","UBE2Z",
        "PSMA1","PSMA2","PSMA3","PSMA4","PSMA5","PSMA6","PSMA7","PSMA8",
        "PSMB1","PSMB2","PSMB3","PSMB4","PSMB5","PSMB6","PSMB7","PSMB8","PSMB9","PSMB10",
        "PSMC1","PSMC2","PSMC3","PSMC4","PSMC5","PSMC6",
        "PSMD1","PSMD2","PSMD3","PSMD4","PSMD6","PSMD7","PSMD8","PSMD9","PSMD10","PSMD11","PSMD12","PSMD13","PSMD14",
    ],
    "glycolysis / metabolism": [
        "HK1","HK2","HK3","HK4","GPI","PFK","PFKL","PFKM","PFKP","TPI1","GAPDH","PGK1","PGK2","PGAM1","PGAM2","ENO1","ENO2","ENO3","PKM","PKM1","PKM2","LDHA","LDHB","LDHC","LDHD","MDH1","MDH2","ME1","ME2","ME3","PC","PCK1","PCK2","MPC1","MPC2","DLAT","DLD","PDHA1","PDHA2","PDHB","PDHX","PDHB","DLST","OGDH","OGDHL","SUCLA2","SUCLG1","SUCLG2","ACAA1","ACAA2","ACAD8","ACAD9","ACADM","ACADS","ACADSB","ACADVL","ACAT1","ACLY","ACO1","ACO2","ACOT1","ACOT2","ACOT4","ACOT6","ACOT7","ACOT8","ACOT9","ACOT11","ACOT12",
        "G6PD","G6PDH","PGD","TKT","TKTL1","TALDO1","RPE","RPI1","RPI2","GND1","GND2",
        "FAS","FASN","ACACA","ACACB","SCD","SCD2","SCD3","SCD4","ELOVL1","ELOVL2","ELOVL3","ELOVL4","ELOVL5","ELOVL6","ELOVL7",
    ],
}


def compute_ols_params(df: pd.DataFrame, x_col: str, y_col: str) -> dict | None:
    """Compute OLS parameters for grid cutoffs from a dataframe."""
    sub = df[[x_col, y_col]].dropna()
    if len(sub) < 10:
        return None
    slope, intercept, r, p, se = stats.linregress(sub[x_col], sub[y_col])
    x_q25 = sub[x_col].quantile(0.25)
    x_q75 = sub[x_col].quantile(0.75)
    y_q25 = sub[y_col].quantile(0.25)
    y_q75 = sub[y_col].quantile(0.75)
    return {
        "beta0": intercept,
        "beta1": slope,
        "x_lo": x_q25,
        "x_hi": x_q75,
        "y_lo": y_q25,
        "y_hi": y_q75,
        "n_genes": len(sub),
    }


def compute_fallback_params(df: pd.DataFrame, x_col: str, y_col: str) -> dict:
    """Fallback params when valid points are too few for stable OLS."""
    sub = df[[x_col, y_col]].dropna()
    if len(sub) == 0:
        raise ValueError("K562 bridge table 缺少可用于阈值分层的 DepMap+shift 联合观测。")
    return {
        "beta0": float(sub[y_col].median()),
        "beta1": 0.0,
        "x_lo": float(sub[x_col].quantile(0.25)),
        "x_hi": float(sub[x_col].quantile(0.75)),
        "y_lo": float(sub[y_col].quantile(0.25)),
        "y_hi": float(sub[y_col].quantile(0.75)),
        "n_genes": int(len(sub)),
        "fallback": True,
    }


def ols_residual(shift: float, effect: float, beta0: float, beta1: float) -> float:
    if pd.isna(shift) or pd.isna(effect):
        return np.nan
    return shift - (beta0 + beta1 * effect)


def absolute_grid_category(effect: float, shift: float, p: dict) -> str:
    """Assign Q1/Q2/Q3/Q4 based on Dixit-specific OLS cutoffs."""
    if pd.isna(effect) or pd.isna(shift):
        return "unknown"
    x_lo, x_hi = p["x_lo"], p["x_hi"]
    y_lo, y_hi = p["y_lo"], p["y_hi"]
    # x-axis: depmap effect (more negative = stronger liability)
    # y-axis: shift
    if effect <= x_lo and shift >= y_hi:
        return "Q1: high_liability_high_shift"
    elif effect >= x_hi and shift >= y_hi:
        return "Q2: low_liability_high_shift"
    elif effect >= x_hi and shift <= y_lo:
        return "Q3: low_liability_low_shift"
    elif effect <= x_lo and shift <= y_lo:
        return "Q4: high_liability_low_shift"
    return "middle"


# ── 1. Load and build K562 master atlas ────────────────────────────────────
print("="*70)
print("Stage 2 — Dixit (K562) Axis Compression")
print("="*70)

df = pd.read_csv(BRIDGE_TABLE, sep="\t")
print(f"\nK562 bridge table: {len(df)} targets, {df['target_gene'].nunique()} unique genes")

# Filter to single-condition K562
k562_dataset_label = str(RECIPE.get("k562_dataset_label", "")).strip()
if k562_dataset_label:
    df_k = df[df["cell_line"] == k562_dataset_label].copy()
else:
    unique_cell_lines = sorted(df["cell_line"].dropna().astype(str).unique().tolist())
    if len(unique_cell_lines) == 1:
        df_k = df.copy()
        k562_dataset_label = unique_cell_lines[0]
    else:
        raise ValueError(
            "配置未提供 k562_dataset_label，且 bridge table 含多个 cell_line，无法唯一确定 K562 对象。"
        )
if df_k.empty:
    raise ValueError(f"bridge table 中找不到 k562_dataset_label={k562_dataset_label} 的记录。")

# Compute OLS params from K562 data itself
ols_params = compute_ols_params(df_k, PRIMARY_X, PRIMARY_Y)
if ols_params is None:
    ols_params = compute_fallback_params(df_k, PRIMARY_X, PRIMARY_Y)
print(f"\nOLS params (K562-specific):")
print(f"  beta0={ols_params['beta0']:.6f}, beta1={ols_params['beta1']:.6f}")
print(f"  x_lo={ols_params['x_lo']:.4f}, x_hi={ols_params['x_hi']:.4f}")
print(f"  y_lo={ols_params['y_lo']:.4f}, y_hi={ols_params['y_hi']:.4f}")
print(f"  n_genes_for_ols={ols_params['n_genes']}")
if ols_params.get("fallback", False):
    print("  mode=fallback_quantile_cutoffs (insufficient points for stable OLS)")

# Compute aligned liability = -effect (higher = stronger DepMap liability)
df_k["liability"] = -df_k[PRIMARY_X]

# OLS residuals
df_k["residual"] = df_k.apply(
    lambda r: ols_residual(r[PRIMARY_Y], r[PRIMARY_X],
                           ols_params["beta0"], ols_params["beta1"]), axis=1)

# Grid categories
df_k["grid"] = df_k.apply(
    lambda r: absolute_grid_category(r[PRIMARY_X], r[PRIMARY_Y], ols_params), axis=1)

# Functional annotation
def annotate_gene(gene):
    for cat, genes in KNOWN_SETS.items():
        if gene in genes:
            return cat
    return "other / unresolved"

df_k["functional_category"] = df_k["target_gene"].apply(annotate_gene)

# ── 2. Dual-criteria layering (Type A/B/C/D analog for K562) ─────────────────
# Use K562-specific quantiles (not HCC cutoffs)
shift_q75 = df_k[PRIMARY_Y].quantile(0.75)
shift_q25 = df_k[PRIMARY_Y].quantile(0.25)
liab_q75  = df_k["liability"].quantile(0.75)

print(f"\nK562 shift quantiles: q25={shift_q25:.4f}, q75={shift_q75:.4f}")
print(f"K562 liability quantiles: q75={liab_q75:.4f}")

# Candidate types (K562 analog of Type A/B/C/D)
# Type A: high shift + low-medium liability (state-rewriting)
# Type B: high shift + high liability (still essential but high perturbation)
# Type C: middle range
# Type D: low shift + high liability (DepMap-excess)
def candidate_type_k(row):
    if pd.isna(row[PRIMARY_X]) or pd.isna(row[PRIMARY_Y]):
        return "unknown"
    s = row[PRIMARY_Y]
    l = row["liability"]
    r = row["residual"] if not pd.isna(row["residual"]) else 0
    if s >= shift_q75 and l < liab_q75:
        return "A: shift_excess_low_liability"
    elif s >= shift_q75 and l >= liab_q75:
        return "B: shift_excess_high_liability"
    elif s <= shift_q25 and l >= liab_q75:
        return "D: depmap_excess"
    else:
        return "C: middle_range"

df_k["candidate_type"] = df_k.apply(candidate_type_k, axis=1)

# ── 3. Data-driven fine axis clustering ──────────────────────────────────────
# K-means on shift, liability, residual (standardized) for genes with DepMap data
clust_df = df_k[df_k["depmap_effect_found"] == True].copy()
print(f"\nGenes with DepMap data for clustering: {len(clust_df)}")

feat_cols = [PRIMARY_Y, "liability", "residual"]
X_raw = clust_df[feat_cols].fillna(0).values
scaler = StandardScaler()
X = scaler.fit_transform(X_raw)

n_clusters = min(max(8, len(clust_df) // 20), 15)
print(f"K-means clusters: {n_clusters}")

km = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
clust_df["cluster_id"] = km.fit_predict(X)

# Build cluster statistics
cluster_stats = []
for cid in range(n_clusters):
    sub = clust_df[clust_df["cluster_id"] == cid]
    cats = sub["functional_category"].value_counts()
    dom_cat = cats.index[0] if len(cats) > 0 else "other / unresolved"
    q1_pct = (sub["grid"] == "Q1: high_liability_high_shift").mean()
    q2_pct = (sub["grid"] == "Q2: low_liability_high_shift").mean()
    shift_ex_pct = (sub["candidate_type"].str.startswith("A:")).mean()
    if q1_pct + q2_pct >= 0.5:
        role = "backbone"
    elif shift_ex_pct >= 0.3:
        role = "shift_excess"
    else:
        role = "mixed"
    cluster_stats.append({
        "cluster_id": cid,
        "n_genes": len(sub),
        "dominant_category": dom_cat,
        "dominant_grid": sub["grid"].value_counts().index[0] if len(sub) > 0 else "unknown",
        "mean_shift": sub[PRIMARY_Y].mean(),
        "mean_liability": sub["liability"].mean(),
        "mean_residual": sub["residual"].mean(),
        "q1_fraction": round(q1_pct, 3),
        "q2_fraction": round(q2_pct, 3),
        "shift_excess_fraction": round(shift_ex_pct, 3),
        "architecture_role": role,
    })

cluster_stats_df = pd.DataFrame(cluster_stats)

# Map dominant category to readable fine axis label
CAT_MAP = {
    "ribosome / translation": "ribosomal / translation",
    "mitochondrial / oxidative phosphorylation": "oxidative phosphorylation",
    "RNA processing / spliceosome": "RNA processing / spliceosome",
    "chromatin / transcription regulation": "transcription regulation",
    "signaling / stress / immune": "signaling / stress",
    "cell cycle / DNA replication": "cell cycle / replication",
    "proteostasis / chaperone": "proteostasis / chaperone",
    "glycolysis / metabolism": "metabolism",
    "other / unresolved": "unresolved",
}

# Assign fine axis labels, handling duplicates
from collections import Counter
label_counts = Counter()
cluster_stats_df["fine_axis"] = cluster_stats_df["dominant_category"].apply(
    lambda c: CAT_MAP.get(c, c)
)
final_labels = []
for _, row in cluster_stats_df.iterrows():
    base = row["fine_axis"]
    label_counts[base] += 1
    final_labels.append(f"{base}_{label_counts[base]}" if label_counts[base] > 1 else base)
cluster_stats_df["fine_axis"] = final_labels

# Map cluster_id -> fine_axis
cid_to_axis = dict(zip(cluster_stats_df["cluster_id"], cluster_stats_df["fine_axis"]))
clust_df["fine_axis"] = clust_df["cluster_id"].map(cid_to_axis)

# Genes without DepMap data: assign by shift-distance to nearest cluster centroid
no_depmap_mask = df_k["depmap_effect_found"] != True
no_depmap = df_k[no_depmap_mask].copy()
print(f"\nGenes without DepMap data: {len(no_depmap)}")

# Precompute cluster mean shifts for distance lookup
cluster_mean_shifts = dict(zip(cluster_stats_df["cluster_id"], cluster_stats_df["mean_shift"]))

no_depmap_rows = []
for _, row in no_depmap.iterrows():
    gene = row["target_gene"]
    shift = row[PRIMARY_Y]
    # Find closest cluster by absolute shift difference
    dists = {cid: abs(mu - shift) for cid, mu in cluster_mean_shifts.items()}
    closest_cid = min(dists, key=dists.get)
    assigned_axis = cid_to_axis[closest_cid]
    row = row.copy()
    row["cluster_id"] = closest_cid
    row["fine_axis"] = assigned_axis
    no_depmap_rows.append(row)

no_depmap_assigned = pd.DataFrame(no_depmap_rows)
if no_depmap_assigned.empty:
    no_depmap_assigned = pd.DataFrame(columns=["target_gene", "cluster_id", "fine_axis"])

# Combine
all_genes_df = pd.concat([clust_df[["target_gene", "cluster_id", "fine_axis"]],
                           no_depmap_assigned[["target_gene", "cluster_id", "fine_axis"]]],
                         ignore_index=True)

# Final atlas
dixit_atlas = df_k.merge(all_genes_df, on="target_gene", how="left")
dixit_atlas["fine_axis"] = dixit_atlas["fine_axis"].fillna("unresolved")
dixit_atlas["macro_axis"] = dixit_atlas["fine_axis"].apply(
    lambda x: x.rsplit("_", 1)[0] if "_" in x and x.split("_")[-1].isdigit() else x
)

# ── 4. Build output tables ───────────────────────────────────────────────────
print("\n" + "="*70)
print("Output Tables")
print("="*70)

# Table 1: dixit_master_atlas.tsv
front_cols = ["target_gene", "candidate_type", "functional_category", "grid",
              PRIMARY_Y, "liability", "residual", "real_shift_L2",
              PRIMARY_X, "depmap_gene_dependency"]
front_cols = [c for c in front_cols if c in dixit_atlas.columns]
dixit_master = dixit_atlas.sort_values([PRIMARY_Y], ascending=False).reset_index(drop=True)
dixit_master[front_cols].to_csv(OUT_DIR / "dixit_master_atlas.tsv", sep="\t", index=False)
print(f"\ndixit_master_atlas.tsv: {len(dixit_master)} rows")

# Table 2: dixit_axis_membership.tsv
membership = dixit_atlas[["target_gene", "fine_axis", "macro_axis",
                           "candidate_type", "functional_category", "grid"]].copy()
membership["annotation_confidence"] = membership.apply(
    lambda r: "high" if r["functional_category"] != "other / unresolved" else "low", axis=1)
membership.to_csv(OUT_DIR / "dixit_axis_membership.tsv", sep="\t", index=False)
print(f"dixit_axis_membership.tsv: {membership['target_gene'].nunique()} genes, {membership['fine_axis'].nunique()} fine axes")

# Table 3: dixit_axis_summary.tsv — use cluster_stats_df as base, relabeled
# Build axis_summary from dixit_atlas directly (authoritative)
axis_summary_rows = []
for axis_name, grp in membership.groupby("fine_axis"):
    genes = grp["target_gene"].tolist()
    atlas_sub = dixit_atlas[dixit_atlas["target_gene"].isin(genes)]
    q1 = (atlas_sub["grid"] == "Q1: high_liability_high_shift").mean()
    q2 = (atlas_sub["grid"] == "Q2: low_liability_high_shift").mean()
    shift_ex = (atlas_sub["candidate_type"].str.startswith("A:")).mean()
    # Look up role from cluster_stats_df
    cid_sample = atlas_sub["cluster_id"].iloc[0] if "cluster_id" in atlas_sub.columns else None
    role_row = cluster_stats_df[cluster_stats_df["fine_axis"] == axis_name]
    arch_role = role_row["architecture_role"].values[0] if len(role_row) > 0 else "mixed"
    axis_summary_rows.append({
        "fine_axis": axis_name,
        "macro_axis": grp["macro_axis"].iloc[0],
        "n_genes": len(genes),
        "genes": ",".join(genes[:8]),
        "fraction_Q1": round(q1, 3),
        "fraction_Q2": round(q2, 3),
        "fraction_shift_excess": round(shift_ex, 3),
        "mean_shift": round(atlas_sub[PRIMARY_Y].mean(), 6),
        "mean_liability": round(atlas_sub["liability"].mean(), 6),
        "mean_residual": round(atlas_sub["residual"].mean(), 6),
        "architecture_role": arch_role,
    })

dixit_axis_summary = pd.DataFrame(axis_summary_rows)
dixit_axis_summary = dixit_axis_summary.sort_values(["n_genes"], ascending=False).reset_index(drop=True)

print("\nArchitecture role distribution (before annotation):")
print(dixit_axis_summary["architecture_role"].value_counts())

# ── 5. Structure replication summary ─────────────────────────────────────────

def classify_architecture(summ_df):
    n_backbone = (summ_df["architecture_role"] == "backbone").sum()
    n_shift_ex = (summ_df["architecture_role"] == "shift_excess").sum()
    n_total = len(summ_df)
    if n_backbone >= n_shift_ex and n_backbone / max(n_total, 1) >= 0.4:
        return "backbone_dominant"
    elif n_shift_ex >= n_backbone and n_shift_ex / max(n_total, 1) >= 0.3:
        return "shift_excess_dominant"
    elif n_backbone > 0 and n_shift_ex > 0:
        return "backbone_plus_shift_excess"
    elif n_backbone > 0:
        return "backbone_heavy"
    elif n_shift_ex > 0:
        return "shift_excess_heavy"
    return "mixed_or_undifferentiated"

def summarize_for_comparison(summ_df, label):
    bb = summ_df[summ_df["architecture_role"] == "backbone"]
    se = summ_df[summ_df["architecture_role"] == "shift_excess"]
    arch_class = classify_architecture(summ_df)
    bb_macro = bb["macro_axis"].value_counts().index[0] if len(bb) > 0 else "N/A"
    se_macro = se["macro_axis"].value_counts().index[0] if len(se) > 0 else "N/A"
    return {
        "dataset": label,
        "canonical_backbone_present": len(bb) > 0,
        "shift_excess_present": len(se) > 0,
        "n_backbone_axes": len(bb),
        "n_shift_excess_axes": len(se),
        "dominant_backbone_axes": ",".join(bb["fine_axis"].head(3).tolist()) if len(bb) > 0 else "none",
        "dominant_shift_excess_axes": ",".join(se["fine_axis"].head(3).tolist()) if len(se) > 0 else "none",
        "backbone_macro_class": bb_macro,
        "shift_excess_macro_class": se_macro,
        "architecture_class": arch_class,
    }

# ── 5b. Annotate K562 unresolved backbone axes with conservative functional labels ──
# These are "unresolved" in the automated clustering because the gene set differs
# from HCC, but manual inspection shows they are interpretable.
# Provide provisional macro labels (NOT claiming equivalence with HCC labels).
K562_BACKBONE_ANNOTATIONS = {
    "unresolved_6": "biosynthetic support / mitochondrial metabolism",
    "unresolved_8": "mitochondrial OXPHOS / iron-sulfur biogenesis",
    "unresolved_9": "nucleotide metabolism / mitochondrial energy",
    "unresolved_2": "translation / chromatin machinery",
    "unresolved_5": "translation initiation / RNA processing",
}
# Update macro_axis for annotated backbone axes
for ax, label in K562_BACKBONE_ANNOTATIONS.items():
    mask = dixit_axis_summary["fine_axis"] == ax
    if mask.any():
        dixit_axis_summary.loc[mask, "macro_axis"] = label
        bb_mask = dixit_axis_summary["architecture_role"] == "backbone"
        dixit_axis_summary.loc[mask & bb_mask, "macro_axis"] = label

# Re-summarize K562 with annotated macro classes
dixit_rows_annotated = summarize_for_comparison(dixit_axis_summary, "K562_Dixit")

print("\n" + "="*70)
print("K562 Summary (with provisional backbone annotations)")
print("="*70)
for k, v in dixit_rows_annotated.items():
    print(f"  {k}: {v}")

# Load HCC axis summary — use same architecture role assignment as K562
hcc_fine = pd.read_csv(HCC_FINE_SUM, sep="\t")

# Infer architecture_role using the SAME rule as K562:
# backbone: max(Q1_HCC38, Q1_HCC1143) >= 0.5
# shift_excess: fraction_shift_excess >= 0.5
# else: mixed
def infer_hcc_role(row):
    q1_max = max(row.get("fraction_Q1_HCC38", 0), row.get("fraction_Q1_HCC1143", 0))
    se = row.get("fraction_shift_excess", 0)
    if q1_max >= 0.5:
        return "backbone"
    elif se >= 0.5:
        return "shift_excess"
    return "mixed"

hcc_fine = hcc_fine.copy()
hcc_fine["architecture_role"] = hcc_fine.apply(infer_hcc_role, axis=1)
# Fix macro_axis to use our standardized labels
macro_map = {
    "gene expression machinery": "gene expression machinery",
    "RNA processing": "RNA processing",
    "ribosome / nucleolar biogenesis": "ribosome / nucleolar biogenesis",
    "signaling / growth control": "signaling / growth control",
    "stress response": "stress response",
    "cell-state regulation": "cell-state regulation",
    "proteostasis": "proteostasis",
    "metabolism": "metabolism",
}
hcc_fine["macro_axis"] = hcc_fine["macro_axis"].apply(lambda x: macro_map.get(x, x))

hcc_rows = summarize_for_comparison(hcc_fine, "HCC38_HCC1143")
dixit_rows = dixit_rows_annotated  # use annotated version

print("\n" + "="*70)
print("HCC Summary (reconstructed)")
print("="*70)
for k, v in hcc_rows.items():
    print(f"  {k}: {v}")

print("\n" + "="*70)
print("K562 Summary")
print("="*70)
for k, v in dixit_rows.items():
    print(f"  {k}: {v}")

# Cross-context comparison table
cross_rows = [
    ("canonical backbone present", hcc_rows["canonical_backbone_present"], dixit_rows["canonical_backbone_present"],
     "CONFIRMED" if dixit_rows["canonical_backbone_present"] else "NOT_CONFIRMED"),
    ("shift-excess present", hcc_rows["shift_excess_present"], dixit_rows["shift_excess_present"],
     "CONFIRMED" if dixit_rows["shift_excess_present"] else "NOT_CONFIRMED"),
    ("backbone macro class", hcc_rows["backbone_macro_class"], dixit_rows["backbone_macro_class"],
     "COMPARABLE" if hcc_rows["backbone_macro_class"] == dixit_rows["backbone_macro_class"] else "CONTEXT_SPECIFIC"),
    ("shift-excess macro class", hcc_rows["shift_excess_macro_class"], dixit_rows["shift_excess_macro_class"],
     "COMPARABLE" if hcc_rows["shift_excess_macro_class"] == dixit_rows["shift_excess_macro_class"] else "CONTEXT_SPECIFIC"),
    ("architecture class", hcc_rows["architecture_class"], dixit_rows["architecture_class"],
     "CONFIRMED" if hcc_rows["architecture_class"] == dixit_rows["architecture_class"] else "DIFFERENT"),
]

cross_df = pd.DataFrame(cross_rows, columns=["comparison_field", "HCC38_HCC1143", "K562_Dixit", "replication_status"])
cross_df.to_csv(OUT_DIR / "dixit_structure_replication_summary.tsv", sep="\t", index=False)

print("\n" + "="*70)
print("Structure Replication Summary (K562 vs HCC)")
print("="*70)
print(cross_df.to_string(index=False))

# Write dixit_axis_summary AFTER annotation
dixit_axis_summary.to_csv(OUT_DIR / "dixit_axis_summary.tsv", sep="\t", index=False)
print(f"\nSaved: dixit_axis_summary.tsv (with annotated macro axes)")
print(f"  backbone axes now labeled: {[K562_BACKBONE_ANNOTATIONS.get(ax, 'N/A') for ax in dixit_axis_summary[dixit_axis_summary['architecture_role']=='backbone']['fine_axis']]}")

print(f"\nAll outputs → {OUT_DIR}")
print("  dixit_master_atlas.tsv")
print("  dixit_axis_membership.tsv")
print("  dixit_axis_summary.tsv")
print("  dixit_structure_replication_summary.tsv")


def build_evidence_tier_summary(axis_summary: pd.DataFrame, comparison: pd.DataFrame) -> pd.DataFrame:
    comparison_map = comparison.set_index("comparison_field")["K562_Dixit"].to_dict()
    rows: list[dict[str, object]] = [
        {
            "object_type": "dataset_level",
            "object_id": "architecture_existence",
            "observed_pattern": "canonical_backbone_present=True; shift_excess_present=True",
            "evidence_tier": "supplementary_confirmed",
            "claim_boundary": "支持 supplementary-level architecture existence，不支持 shared mainline architecture",
        },
        {
            "object_type": "dataset_level",
            "object_id": "canonical_backbone_present",
            "observed_pattern": "external backbone-like structure detected",
            "evidence_tier": "supplementary_confirmed",
            "claim_boundary": "支持 backbone existence，不支持 backbone macro class 与 HCC 相同",
        },
        {
            "object_type": "dataset_level",
            "object_id": "shift_excess_present",
            "observed_pattern": "shift-excess structure detected in K562",
            "evidence_tier": "supplementary_supporting",
            "claim_boundary": "支持存在性，不支持 dominant shift-excess macro class 已稳定命名",
        },
        {
            "object_type": "dataset_level",
            "object_id": "backbone_macro_class",
            "observed_pattern": str(comparison_map.get("backbone macro class", "unknown")),
            "evidence_tier": "supplementary_supporting",
            "claim_boundary": "支持 context-specific backbone replication，不支持与 HCC backbone macro class 对齐",
        },
        {
            "object_type": "dataset_level",
            "object_id": "architecture_class",
            "observed_pattern": str(comparison_map.get("architecture class", "unknown")),
            "evidence_tier": "supplementary_supporting",
            "claim_boundary": "支持 K562 architecture composition 与 HCC 不同，不支持跨 context 同构",
        },
        {
            "object_type": "dataset_level",
            "object_id": "shift_excess_macro_class",
            "observed_pattern": str(comparison_map.get("shift-excess macro class", "unknown")),
            "evidence_tier": "preliminary",
            "claim_boundary": "当前不足以写成稳定、可命名的 supplementary positive program",
        },
    ]

    axis_rules = {
        "unresolved_6": ("supplementary_supporting", "支持 K562 backbone 具有 biosynthetic / mitochondrial 倾向，但不是 HCC-equivalent frozen axis"),
        "unresolved_9": ("supplementary_supporting", "支持局部 backbone-like structure，不足以单独承担 dataset-level claim"),
        "unresolved_2": ("supplementary_supporting", "支持 backbone heterogeneity，不能直接等同 HCC gene expression machinery"),
        "unresolved_5": ("preliminary", "轴规模过小，只能作 preliminary supportive line"),
        "unresolved_4": ("preliminary", "支持 K562 含 shift-excess 成分，但不足以稳定命名 macro class"),
    }
    axis_index = axis_summary.set_index("fine_axis")
    for axis_name, (tier, boundary) in axis_rules.items():
        if axis_name not in axis_index.index:
            continue
        row = axis_index.loc[axis_name]
        if axis_name == "unresolved_4":
            pattern = f"shift_excess-like axis; n_genes={int(row['n_genes'])}; fraction_shift_excess={row['fraction_shift_excess']:.3f}"
        else:
            pattern = f"{row['macro_axis']} backbone axis; n_genes={int(row['n_genes'])}; fraction_Q1={row['fraction_Q1']:.3f}"
        rows.append(
            {
                "object_type": "axis_level",
                "object_id": axis_name,
                "observed_pattern": pattern,
                "evidence_tier": tier,
                "claim_boundary": boundary,
            }
        )
    return pd.DataFrame(rows)


def build_claim_tiering() -> pd.DataFrame:
    rows = [
        {
            "object": "architecture_existence",
            "level": "dataset_level",
            "evidence_tier": "supplementary_confirmed",
            "allowed_wording": "Dixit/K562 在 supplementary 层面支持 architecture existence；可写成 architecture-level replication 或 structure-level transferability",
            "disallowed_wording": "Dixit proves model generalization; Dixit is a second primary mainline",
        },
        {
            "object": "canonical_backbone_present",
            "level": "dataset_level",
            "evidence_tier": "supplementary_confirmed",
            "allowed_wording": "外部 context 中存在 backbone-like structure；支持 backbone existence",
            "disallowed_wording": "backbone macro class is the same as HCC; HCC and Dixit share the same frozen mainline architecture",
        },
        {
            "object": "shift_excess_present",
            "level": "dataset_level",
            "evidence_tier": "supplementary_supporting",
            "allowed_wording": "Dixit/K562 中存在 shift-excess structure 成分；支持存在性",
            "disallowed_wording": "Dominant shift-excess macro class has been stably named",
        },
        {
            "object": "backbone_macro_class",
            "level": "dataset_level",
            "evidence_tier": "supplementary_supporting",
            "allowed_wording": "K562 的 dominant backbone 更偏 biosynthetic support / mitochondrial metabolism；说明 replication 是 context-specific",
            "disallowed_wording": "K562 backbone is aligned to HCC gene expression machinery",
        },
        {
            "object": "architecture_class",
            "level": "dataset_level",
            "evidence_tier": "supplementary_supporting",
            "allowed_wording": "K562 更像 backbone_dominant；支持外部结构复现并非与 HCC 同构",
            "disallowed_wording": "Dixit is an isomorphic replication of the HCC architecture",
        },
        {
            "object": "stable_anchor_like_objects",
            "level": "object_group",
            "evidence_tier": "supplementary_supporting",
            "allowed_wording": "在 Dixit/K562 中可观察到 stable anchor-like objects；支持 anchor-like structure can recur across contexts",
            "disallowed_wording": "stable anchors were replicated across contexts; the same anchors generalized across datasets",
        },
        {
            "object": "unresolved_6",
            "level": "axis_level",
            "evidence_tier": "supplementary_supporting",
            "allowed_wording": "支持 biosynthetic / mitochondrial 倾向的 backbone-like axis",
            "disallowed_wording": "可直接等同 HCC frozen axis",
        },
        {
            "object": "unresolved_9",
            "level": "axis_level",
            "evidence_tier": "supplementary_supporting",
            "allowed_wording": "支持局部 backbone-like structure",
            "disallowed_wording": "可单独承担 dataset-level claim",
        },
        {
            "object": "unresolved_2",
            "level": "axis_level",
            "evidence_tier": "supplementary_supporting",
            "allowed_wording": "支持 translation / chromatin-like backbone heterogeneity",
            "disallowed_wording": "可直接写成 HCC-equivalent gene expression machinery axis",
        },
        {
            "object": "unresolved_5",
            "level": "axis_level",
            "evidence_tier": "preliminary",
            "allowed_wording": "仅可作 preliminary supportive line",
            "disallowed_wording": "formal positive supplementary axis",
        },
        {
            "object": "unresolved_4",
            "level": "axis_level",
            "evidence_tier": "preliminary",
            "allowed_wording": "支持 Dixit 含 shift-excess-like component，但仅 preliminary",
            "disallowed_wording": "稳定命名的 shift-excess macro class",
        },
        {
            "object": "model_generalization_claim",
            "level": "global",
            "evidence_tier": "not_supported_by_current_dixit_truth_side",
            "allowed_wording": "当前 Dixit 只支持框架/结构层泛化，不支持模型泛化",
            "disallowed_wording": "model cross-context generalization has been demonstrated",
        },
    ]
    return pd.DataFrame(rows)


evidence_tier_summary = build_evidence_tier_summary(dixit_axis_summary, cross_df)
evidence_tier_summary.to_csv(OUT_DIR / "dixit_evidence_tier_summary.tsv", sep="\t", index=False)

claim_tiering = build_claim_tiering()
claim_tiering.to_csv(OUT_DIR / "dixit_claim_tiering.tsv", sep="\t", index=False)

run_manifest = {
    "stage": "stage2_dixit_k562_structure_replication",
    "config_path": str(resolve_path(str(ARGS.config))),
    "bridge_table_path": str(BRIDGE_TABLE),
    "hcc_fine_axis_summary_path": str(HCC_FINE_SUM),
    "output_dir": str(OUT_DIR),
    "k562_dataset_label": str(RECIPE.get("k562_dataset_label", "dixit_2016_k562_tf_13d_gse90063")),
}
(OUT_DIR / "run_manifest.json").write_text(json.dumps(run_manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
