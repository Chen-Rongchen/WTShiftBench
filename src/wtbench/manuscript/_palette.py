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
]
