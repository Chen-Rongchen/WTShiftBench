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
MAX_WORDS_PER_PANEL = 14
MAX_SINGLE_PANEL_WORDS = 28
CAPTION_LEADING = 1.45
CAPTION_WRAP_FRACTION = 0.78
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
    return [s.strip() for s in re.split(r"(?<=[.!?])\s+", text) if s.strip()]


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
    summary = limit_words(sentences[0], limit)
    return f"{panel_letter}, {summary}"


def make_concise_legend(raw_legend: str) -> str:
    """Convert verbose manuscript legends to compact figure-page legends."""
    raw_legend = raw_legend.strip()
    lines = [line.strip() for line in raw_legend.splitlines() if line.strip()]
    if not lines:
        return raw_legend

    heading = clean_markdown(lines[0])
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

        prefix_width = words_width_pt(prefix_line.split(), size=TITLE_SIZE, weight="bold") + TITLE_BODY_GAP_PT
        available = max_width_pt - prefix_width
        if body_words and available > max_width_pt * 0.18 and prefix_width < max_width_pt * 0.62:
            first_body, body_words = wrap_words_to_width(body_words, available, BODY_SIZE)
            lines.append([(prefix_line, True, 0.0), (first_body, False, prefix_width)])
        else:
            lines.append([(prefix_line, True, 0.0)])
    while body_words:
        body_line, body_words = wrap_words_to_width(body_words, max_width_pt, BODY_SIZE)
        lines.append([(body_line, False, 0.0)])
    return lines or [[(legend, False, 0.0)]]


def render_page(fig: plt.Figure, img_path: Path, legend: str, page_num: int) -> None:
    """A4 page: image on image-axes, legend/text on separate text-axes (vector)."""
    fig.clf()

    # Prepare legend
    caption_lines = build_caption_lines(legend, USABLE_W * 72 * CAPTION_WRAP_FRACTION)

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
        MARGIN_LR / A4_W, MARGIN_BOT / A4_H,
        USABLE_W / A4_W, (text_top - MARGIN_BOT) / A4_H,
    ])
    ax_text.set_xlim(0, 1)
    ax_text.set_ylim(0, 1)
    ax_text.set_axis_off()

    y = 1.0
    y_step = line_h / max((text_top - MARGIN_BOT), 0.01)
    for line in caption_lines:
        for text, bold, x_pt in line:
            ax_text.text(
                x_pt / (USABLE_W * 72),
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
