#!/usr/bin/env python3
"""Build A4 figure PDFs with concise legends.

The layout follows the reference article's figure pages: one figure per page,
large artwork on top, compact legend below, small page footer.
"""
from __future__ import annotations

import re
from functools import lru_cache
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.font_manager import FontProperties
from matplotlib.textpath import TextPath

ROOT = Path(__file__).resolve().parents[2]
MANUSCRIPT = ROOT / "manuscript"
FIGURES = MANUSCRIPT / "figures"
ED_DIR = MANUSCRIPT / "extended_data"
LEGENDS_FILE = MANUSCRIPT / "text" / "figure_legends_v1.md"
OUT_DIR = MANUSCRIPT / "submission_pdfs"

# A4 portrait in inches.
A4_W, A4_H = 8.27, 11.69
MARGIN_LR = 0.55
MARGIN_TOP = 0.52
MARGIN_BOT = 0.45
USABLE_W = A4_W - 2 * MARGIN_LR

TITLE_SIZE = 8.2
BODY_SIZE = 6.5
PAGE_NUM_SIZE = 6.2
MAX_WORDS_PER_PANEL = 38
MAX_SINGLE_PANEL_WORDS = 72
CAPTION_LEADING = 1.34
CAPTION_WRAP_FRACTION = 0.94
TITLE_BODY_GAP_PT = 13.0

SHORT_TITLES = {
    "Fig. 1": "Truth object definition",
    "Fig. 2": "Anchor tiering",
    "Fig. 3": "Model adjudication",
    "Fig. 4": "Finite-budget rebuttal tests",
    "Fig. 5": "Boundary governance",
    "Extended Data Fig. 1": "Dataset familiarization",
    "Extended Data Fig. 2": "Metric robustness",
    "Extended Data Fig. 3": "K562 and Replogle bridge support",
    "Extended Data Fig. 4": "Axis-level signal space",
    "Extended Data Fig. 5": "Pathway-response polarity",
}

MANUAL_LEGENDS = {
    "Fig. 1": (
        "Fig. 1 | Truth object definition. "
        "a, Workflow defining the frozen phenotype-aligned recovery object before model scoring by linking absolute mean perturbation shift to CRISPR DepMap dependency. "
        "b, Pre-specified 25/75 joint-percentile rule separating Q1 anchors, Q2 transcriptomic excess, Q3 dependency excess, Q4 low-information targets and the retained middle band. "
        "c,d, HCC38 and HCC1143 target-level rank-percentile grids; panels report n, aligned Spearman rho and Q1 anchor count. "
        "e, Category composition across the two primary contexts, including zero-count Q2 and Q3 categories. "
        "f, Bridge strength summary showing observed aligned Spearman rho with Fisher z 95% confidence intervals and a 1,000-permutation null envelope."
    ),
    "Fig. 2": (
        "Fig. 2 | Anchor tiering. "
        "a, Shared-canonical anchor ranking by paired shift and dependency quantile means across HCC38 and HCC1143. "
        "b, Recurrence matrix for the four final stable anchors, with Q1 status and mean joint quantiles shown per context. "
        "c, Stability fraction separates stable anchors from cutoff-sensitive supporting objects without using covariate information. "
        "d, Stable anchors retain high shift and dependency ranks across both HCC contexts. "
        "e, Per-anchor covariate Total Variation Distance (TVD) audit across five covariate axes and two HCC contexts; TVD > 0.25 marks imbalance. "
        "f, Claim-tier matrix: PFDN5 is primary but qualified, whereas PMF1, PRPF6 and ZNF131 remain supporting because of covariate exposure."
    ),
    "Fig. 3": (
        "Fig. 3 | Model adjudication. "
        "a, Three pre-specified metrics evaluate backbone recovery, shift-excess identification and structure-versus-context separation across the shared-mean baseline, GEARS, foundation-model entrants, linear controls and a null reference. "
        "b, Paired summary showing that the shared-mean baseline leads backbone recovery, whereas GEARS leads structure-versus-context separation. "
        "c, Backbone recovery versus structure-versus-context separation places entrants in an asymmetric recovery space; no entrant occupies the illustrative upper-right region, so GEARS is retained as an architecture-level diagnosis rather than an overall primary winner. "
        "d, Per-context backbone recovery ratios relative to the shared-mean baseline are shown for GEARS, Geneformer and scGPT in HCC38 and HCC1143, confirming that the residual backbone gap is present in both primary contexts."
    ),
    "Fig. 4": (
        "Fig. 4 | Finite-budget rebuttal tests. "
        "a, Six pre-specified GEARS recipes define the finite local rebuttal neighborhood under the unchanged truth object and scoring system. "
        "b, Rebuttal recovery space compares the shared-mean baseline, formal GEARS, five GEARS sweep candidates and three embedding-based linear controls on backbone recovery and structure/context separation. "
        "c, Per-context residual backbone gaps show that all tested candidates remain below the shared-mean baseline in HCC38 and HCC1143; the stop rule therefore does not promote GEARS to the primary winner."
    ),
    "Fig. 5": (
        "Fig. 5 | Boundary governance. "
        "a, Covariate boundary in HCC38 and HCC1143, showing mean target-control TVD across five covariate stratifications and marking targets exceeding TVD > 0.25. "
        "b, Endpoint hierarchy across HCC38, HCC1143, K562 7d and K562 13d compares CRISPR DepMap dependency with RNAi DEMETER2; CRISPR is higher in all four contexts. "
        "c, K562 temporal stratification shows larger perturbation magnitude at 13d but stronger dependency-aligned rank structure at 7d. "
        "d, A0/A1/B tiering retains K562 as architecture-form and bounded bridge-form support, not content-level replication."
    ),
    "Extended Data Fig. 1": (
        "Extended Data Fig. 1 | Dataset familiarization. "
        "a, Dataset overview for five perturbation-expression contexts and two endpoint resources, summarizing cell-line identity, size and benchmark use. "
        "b, UMAPs of perturbation-level mean profiles for HCC38, HCC1143, Dixit K562 7d, Dixit K562 13d and Replogle K562 essential day 7; the matched control aggregate is marked. "
        "c, Target-gene expression changes for the same five contexts, with arrows from control expression to post-perturbation expression."
    ),
    "Extended Data Fig. 2": (
        "Extended Data Fig. 2 | Metric robustness. "
        "a, Top-n gene-subset sensitivity recomputes aligned Spearman correlation after ranking genes by control expression or perturbation-response magnitude. "
        "b, Metric and CRISPR endpoint heat map marks the retained primary bridge metric and endpoint. "
        "c, Endpoint sensitivity compares CRISPR dependency with RNAi DEMETER2 across primary HCC and supplementary K562 contexts. "
        "d, Control-subsampling robustness shows mean and 2.5th-97.5th percentile ranges across repeated control-cell subsamples. "
        "e, Whole-transcriptome shift, rather than target-gene self-expression, carries the fitness bridge."
    ),
    "Extended Data Fig. 3": (
        "Extended Data Fig. 3 | K562 and Replogle bridge support. "
        "a, K562 temporal bridge-magnitude dissociation shows aligned Spearman correlation with CRISPR DepMap dependency and mean perturbation-shift magnitude at 7d and 13d; 13d has larger magnitude but weaker rank alignment. "
        "b, Replogle K562 essential day 7 bridge test plots 1,882 matched CRISPRi targets as rank percentiles for perturbation shift and dependency, with 25/75 percentile cutoffs, Q1-Q4 category counts and aligned Spearman rho = 0.402."
    ),
    "Extended Data Fig. 4": (
        "Extended Data Fig. 4 | Axis-level signal space. "
        "a, Axis-level signal space compares dependency signal with transcriptomic shift signal across annotated axes; color denotes descriptive signal profile rather than claim tier. "
        "b, Paired axis R-squared ranking displays axes with the largest signal in either dimension on a common scale, supporting an audit-style view of partial axis-level structure."
    ),
    "Extended Data Fig. 5": (
        "Extended Data Fig. 5 | Pathway-response polarity. "
        "a, Pathway normalized enrichment score heat map across pre-specified display targets in HCC38, HCC1143, K562 7d and K562 13d. "
        "Rows show selected anchors and high-variance response examples; columns show the Hallmark response panel; asterisks mark FDR < 0.10. "
        "Right-hand summaries report same-target partner-context pathway Spearman correlation and sign agreement, treating pathway polarity as exploratory context rather than a benchmark-defining endpoint."
    ),
}


def parse_legends() -> dict[str, str]:
    text = LEGENDS_FILE.read_text()
    legends = {}
    current_id = None
    current_lines = []
    for line in text.split("\n"):
        if line.startswith("## Fig. ") or line.startswith("## Extended Data Fig. "):
            if current_id and current_lines:
                legends[current_id] = "\n".join(current_lines).strip()
            heading = line.replace("## ", "")
            m = re.match(r'(Fig\.\s+\d+|Extended Data Fig\.\s+\d+)\.\s+', heading)
            if m:
                current_id = m.group(1)
            current_lines = [heading]
        elif current_id and line.strip():
            current_lines.append(line)
        elif current_id and not line.strip() and current_lines:
            current_lines.append("")
    if current_id and current_lines:
        legends[current_id] = "\n".join(current_lines).strip()
    return legends


def clean_markdown(text: str) -> str:
    text = text.replace("**", "")
    text = text.replace("`", "")
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def split_sentences(text: str) -> list[str]:
    text = clean_markdown(text)
    if not text:
        return []
    protected = {
        "Extended Data Fig.": "Extended Data Fig<dot>",
        "Fig.": "Fig<dot>",
        "e.g.": "e<dot>g<dot>",
        "i.e.": "i<dot>e<dot>",
    }
    for source, target in protected.items():
        text = text.replace(source, target)
    sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", text) if s.strip()]
    restored = []
    for sentence in sentences:
        for source, target in protected.items():
            sentence = sentence.replace(target, source)
        restored.append(sentence)
    return restored


def limit_words(text: str, limit: int) -> str:
    words = text.split()
    if len(words) <= limit:
        return text
    trimmed_words = words[:limit]
    while trimmed_words and trimmed_words[-1].strip(" ,;:.").lower() in {"and", "or", "the", "with", "for", "across", "of"}:
        trimmed_words.pop()
    trimmed = " ".join(trimmed_words).rstrip(" ,;:")
    if trimmed.count("(") > trimmed.count(")"):
        trimmed = trimmed.rsplit("(", 1)[0].rstrip(" ,;:")
    return trimmed + "."


def concise_panel_text(panel_letter: str, panel_body: str, single_panel: bool) -> str:
    sentences = split_sentences(panel_body)
    if not sentences:
        return f"{panel_letter},"
    limit = MAX_SINGLE_PANEL_WORDS if single_panel else MAX_WORDS_PER_PANEL
    if len(sentences) > 1 and len(sentences[0].split()) <= 8:
        summary = limit_words(f"{sentences[0]} {sentences[1]}", limit)
        return f"{panel_letter}, {summary}"
    selected: list[str] = []
    for sentence in sentences:
        candidate = " ".join(selected + [sentence])
        if selected and len(candidate.split()) > limit:
            break
        selected.append(sentence)
        if len(candidate.split()) >= limit * 0.75:
            break
    summary = limit_words(" ".join(selected), limit)
    return f"{panel_letter}, {summary}"


def make_concise_legend(raw_legend: str) -> str:
    """Convert verbose manuscript legends to compact figure-page legends."""
    raw_legend = raw_legend.strip()
    lines = [line.strip() for line in raw_legend.splitlines() if line.strip()]
    if not lines:
        return raw_legend

    heading = clean_markdown(lines[0])
    manual_match = re.match(r"^(Fig\. \d+|Extended Data Fig\. \d+)\.\s+", heading)
    if manual_match and manual_match.group(1) in MANUAL_LEGENDS:
        return MANUAL_LEGENDS[manual_match.group(1)]

    body = clean_markdown(" ".join(lines[1:]))
    title = heading
    title_match = re.match(r"^(Fig\. \d+|Extended Data Fig\. \d+)\.\s+(.+)$", heading)
    if title_match:
        fig_id, fig_title = title_match.groups()
        title = f"{fig_id} | {SHORT_TITLES.get(fig_id, fig_title.rstrip('.'))}"

    panel_pattern = re.compile(r"\*\*([a-z]),\*\*")
    matches = list(panel_pattern.finditer(" ".join(lines[1:])))
    if not matches:
        first = split_sentences(body)[:2]
        return f"{title}. {' '.join(first)}".strip()

    source = " ".join(lines[1:])
    panels: list[tuple[str, str]] = []
    for idx, match in enumerate(matches):
        start = match.end()
        end = matches[idx + 1].start() if idx + 1 < len(matches) else len(source)
        panels.append((match.group(1), source[start:end].strip()))

    single_panel = len(panels) == 1
    panel_text = [concise_panel_text(letter, text, single_panel) for letter, text in panels]
    legend = title.rstrip(".") + ". " + " ".join(panel_text)
    if not legend.endswith("."):
        legend += "."
    return legend


def split_caption_prefix(legend: str) -> tuple[str, str]:
    match = re.match(r"^(Fig\. \d+|Extended Data Fig\. \d+) \| ([^.]+)\.\s*(.*)$", legend)
    if not match:
        return "", legend
    fig_id, title, body = match.groups()
    return f"{fig_id} | {title}.", body


@lru_cache(maxsize=None)
def text_width_pt(text: str, *, size: float, weight: str = "normal") -> float:
    if not text:
        return 0.0
    props = FontProperties(family="DejaVu Sans", size=size, weight=weight)
    return TextPath((0, 0), text, prop=props).get_extents().width


def words_width_pt(words: list[str], *, size: float, weight: str = "normal") -> float:
    if not words:
        return 0.0
    space_width = size * 0.32
    return sum(text_width_pt(word, size=size, weight=weight) for word in words) + space_width * (len(words) - 1)


def wrap_words_to_width(words: list[str], max_width_pt: float, size: float) -> tuple[str, list[str]]:
    current: list[str] = []
    remaining = words[:]
    while remaining:
        candidate_words = current + [remaining[0]]
        if current and words_width_pt(candidate_words, size=size) > max_width_pt:
            break
        current.append(remaining.pop(0))
    return " ".join(current), remaining


def build_caption_lines(legend: str, max_width_pt: float) -> list[list[tuple[str, bool, float]]]:
    """Return caption line segments as (text, bold, x_offset_points)."""
    prefix, body = split_caption_prefix(make_concise_legend(legend))
    lines: list[list[tuple[str, bool, float]]] = []
    body_words = body.split()

    if prefix:
        prefix_words = prefix.split()
        prefix_line, prefix_words = wrap_words_to_width(prefix_words, max_width_pt, TITLE_SIZE)
        while prefix_words:
            lines.append([(prefix_line, True, 0.0)])
            prefix_line, prefix_words = wrap_words_to_width(prefix_words, max_width_pt, TITLE_SIZE)

        if prefix.startswith("Extended Data Fig."):
            lines.append([(prefix_line, True, 0.0)])
            prefix_line = ""

        prefix_width = words_width_pt(prefix_line.split(), size=TITLE_SIZE, weight="bold") + TITLE_BODY_GAP_PT
        available = max_width_pt - prefix_width
        if prefix_line and body_words and available > max_width_pt * 0.18 and prefix_width < max_width_pt * 0.58:
            first_body, body_words = wrap_words_to_width(body_words, available, BODY_SIZE)
            lines.append([(prefix_line, True, 0.0), (first_body, False, prefix_width)])
        elif prefix_line:
            lines.append([(prefix_line, True, 0.0)])
    while body_words:
        body_line, body_words = wrap_words_to_width(body_words, max_width_pt, BODY_SIZE)
        lines.append([(body_line, False, 0.0)])
    return lines or [[(legend, False, 0.0)]]


def render_page(fig: plt.Figure, img_path: Path, legend: str, page_num: int) -> None:
    """A4 page: image on image-axes, legend/text on separate text-axes (vector)."""
    fig.clf()

    # Prepare legend
    caption_w = USABLE_W * CAPTION_WRAP_FRACTION
    caption_lines = build_caption_lines(legend, caption_w * 72)

    # Estimate heights (inches)
    line_h = BODY_SIZE / 72 * CAPTION_LEADING
    legend_text_h = len(caption_lines) * line_h + 0.18

    # Image height: whatever is left
    img_h_avail = max(2.5, A4_H - MARGIN_TOP - legend_text_h - MARGIN_BOT - 0.12)
    img = mpimg.imread(img_path)
    aspect = img.shape[1] / img.shape[0]
    img_h = min(USABLE_W / aspect, img_h_avail)
    img_w = img_h * aspect
    img_x0 = (A4_W - img_w) / 2
    img_y0 = A4_H - MARGIN_TOP - img_h

    # Image axes (normalized figure coords)
    ax_img = fig.add_axes([
        img_x0 / A4_W, img_y0 / A4_H,
        img_w / A4_W, img_h / A4_H,
    ])
    ax_img.imshow(img)
    ax_img.set_axis_off()

    # Text axes — separate from image, keeps text as vector
    text_top = img_y0 - 0.10
    ax_text = fig.add_axes([
        ((A4_W - caption_w) / 2) / A4_W, MARGIN_BOT / A4_H,
        caption_w / A4_W, (text_top - MARGIN_BOT) / A4_H,
    ])
    ax_text.set_xlim(0, 1)
    ax_text.set_ylim(0, 1)
    ax_text.set_axis_off()

    y = 1.0
    y_step = line_h / max((text_top - MARGIN_BOT), 0.01)
    for line in caption_lines:
        for text, bold, x_pt in line:
            ax_text.text(
                x_pt / (caption_w * 72),
                y,
                text,
                fontsize=TITLE_SIZE if bold else BODY_SIZE,
                fontweight="bold" if bold else "normal",
                va="top",
                ha="left",
                color="#1F1F1F" if bold else "#333333",
                transform=ax_text.transAxes,
            )
        y -= y_step

    # Page number
    ax_pn = fig.add_axes([0, 0, 1, MARGIN_BOT / A4_H])
    ax_pn.set_axis_off()
    ax_pn.text(0.5, 0.35, str(page_num), fontsize=PAGE_NUM_SIZE,
               ha="center", va="center", color="#888888", transform=ax_pn.transAxes)


def build_pdf(image_map: dict[str, Path], legends: dict[str, str], output_path: Path) -> None:
    fig = plt.figure(figsize=(A4_W, A4_H), dpi=200)
    page = 1
    with PdfPages(output_path) as pdf:
        for fig_id, img_path in image_map.items():
            legend = legends.get(fig_id, fig_id)
            render_page(fig, img_path, legend, page)
            pdf.savefig(fig, dpi=200, facecolor="white")
            page += 1
    plt.close(fig)
    print(f"[OK] {output_path.name} - {page - 1} pages")


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    legends = parse_legends()
    print(f"Parsed {len(legends)} figure legends")

    main_map = {f"Fig. {n}": FIGURES / f"Figure_{n}" / f"Figure_{n}.png"
                for n in range(1, 6) if (FIGURES / f"Figure_{n}" / f"Figure_{n}.png").exists()}
    build_pdf(main_map, legends, OUT_DIR / "01_main_figures_concise_legends.pdf")

    ed_map = {f"Extended Data Fig. {n}": ED_DIR / f"Extended_Data_Figure_{n}" / f"Extended_Data_Figure_{n}.png"
              for n in range(1, 6) if (ED_DIR / f"Extended_Data_Figure_{n}" / f"Extended_Data_Figure_{n}.png").exists()}
    build_pdf(ed_map, legends, OUT_DIR / "02_extended_data_figures_concise_legends.pdf")

    build_pdf({**main_map, **ed_map}, legends, OUT_DIR / "03_all_figures_concise_legends.pdf")


if __name__ == "__main__":
    main()
