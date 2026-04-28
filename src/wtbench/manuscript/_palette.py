"""Canonical colour palette for manuscript figures.

Rules (see Figure 1/2 freeze specs):

- Figure 1 and Figure 2 share a single Okabe-Ito compatible anchor palette.
- Green encodes primary / anchor / stable / clean / HCC1143.
- Orange encodes HCC38 / contrast / exposed / warning.
- Blue encodes shift / threshold / reference / cutoff.
- Gray encodes supporting / neutral / non-anchor / background.
- Colour must never be the only encoding: text labels, bold emphasis, chips,
  row washes, and numeric annotations duplicate the same information so the
  figures remain legible in grayscale.

Import these constants instead of hard-coding hex values inside figure scripts,
and extend this module rather than introducing new colours ad hoc.
"""

from __future__ import annotations

PRIMARY_GREEN: str = "#009E73"
PRIMARY_GREEN_EDGE: str = "#00795A"
PRIMARY_GREEN_FILL: str = "#E8F5E9"

VERMILLION: str = "#D55E00"
VERMILLION_FILL: str = "#FFF3E0"
SKY_BLUE: str = "#56B4E9"

NEUTRAL_GRAY: str = "#8E8E8E"
MID_GRAY: str = "#BDBDBD"
LIGHT_GRAY: str = "#F5F5F5"
DIVIDER_GRAY: str = "#E0E0E0"
DARK_TEXT: str = "#000000"

# Legacy aliases kept to avoid churn in older figure scripts.
SUPPORTING_AMBER: str = VERMILLION
SENSITIVE_AMBER: str = MID_GRAY


TIER_COLORS: dict[str, str] = {
    "primary_but_qualified": PRIMARY_GREEN,
    "supporting_only": NEUTRAL_GRAY,
    "supporting_but_sensitive": MID_GRAY,
}

# —— Figure 5 (boundary: covariate / endpoint / temporal) ——
# TVD: cool blue-gray sequential ("technical audit" vs discovery-layer warmth); TVD>0.25 = VERMILLION.
FIG5_TVD_CMAP_STOPS: tuple[str, ...] = ("#F8FAFC", "#D9E2EC", "#B0C4DE", "#7A9EAF")
# Endpoint dumbbell: same primary green as Fig. 1/2; RNAi = supporting gray.
FIG5_ENDPOINT_CRISPR: str = PRIMARY_GREEN
FIG5_ENDPOINT_RNAI: str = "#AAAAAA"
FIG5_DUMBBELL_CONNECTOR: str = "#D5D5D5"
# UMI row grouping: flat divider, same grammar as other manuscript dividers.
FIG5_UMI_GROUP_LINE: str = MID_GRAY
# Paired 7d / 13d (shift magnitude): gray-only, distinction by lightness + x position.
FIG5_K562_BOX_7D_FILL: str = LIGHT_GRAY
FIG5_K562_BOX_7D_EDGE: str = MID_GRAY
FIG5_K562_BOX_13D_FILL: str = "#D5D5D5"
FIG5_K562_BOX_13D_EDGE: str = "#8E8E8E"
FIG5_K562_PAIR_LINE: str = DIVIDER_GRAY
FIG5_K562_JITTER: str = "#AAAAAA"
# Box whiskers / caps: neutral; K562 temporal *medians*: green family (supporting extension, not black).
FIG5_MEDIAN: str = "#333333"
FIG5_K562_BOXPLOT_MEDIAN: str = "#2E8B57"
FIG5_TVD_GLYPH_ZERO_EDGE: str = MID_GRAY
FIG5_TVD_GLYPH_ZERO_FACE: str = "#E8E8E8"
# 1 pt stroke between vermillion and neutral heatmap (does not add a new hue).
FIG5_TVD_EXPOSED_STROKE: str = "#FFFFFF"


__all__ = [
    "PRIMARY_GREEN",
    "PRIMARY_GREEN_EDGE",
    "PRIMARY_GREEN_FILL",
    "VERMILLION",
    "VERMILLION_FILL",
    "SKY_BLUE",
    "NEUTRAL_GRAY",
    "DIVIDER_GRAY",
    "SUPPORTING_AMBER",
    "SENSITIVE_AMBER",
    "LIGHT_GRAY",
    "MID_GRAY",
    "DARK_TEXT",
    "TIER_COLORS",
    "FIG5_TVD_CMAP_STOPS",
    "FIG5_ENDPOINT_CRISPR",
    "FIG5_ENDPOINT_RNAI",
    "FIG5_DUMBBELL_CONNECTOR",
    "FIG5_UMI_GROUP_LINE",
    "FIG5_K562_BOX_7D_FILL",
    "FIG5_K562_BOX_7D_EDGE",
    "FIG5_K562_BOX_13D_FILL",
    "FIG5_K562_BOX_13D_EDGE",
    "FIG5_K562_PAIR_LINE",
    "FIG5_K562_JITTER",
    "FIG5_MEDIAN",
    "FIG5_K562_BOXPLOT_MEDIAN",
    "FIG5_TVD_GLYPH_ZERO_EDGE",
    "FIG5_TVD_GLYPH_ZERO_FACE",
    "FIG5_TVD_EXPOSED_STROKE",
]
