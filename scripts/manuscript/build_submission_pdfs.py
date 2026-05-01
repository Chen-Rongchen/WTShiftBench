#!/usr/bin/env python3
"""Build A4 figure PDFs with concise legends.

The layout follows the reference article's figure pages: one figure per page,
large artwork on top, compact legend below, small page footer.
"""
from __future__ import annotations

import re
import textwrap
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
from matplotlib.backends.backend_pdf import PdfPages

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
BODY_SIZE = 6.9
PAGE_NUM_SIZE = 6.2
WRAP_WIDTH = 108
MAX_WORDS_PER_PANEL = 42
MAX_SINGLE_PANEL_WORDS = 72


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
    trimmed = " ".join(words[:limit]).rstrip(" ,;:")
    return trimmed + "."


def concise_panel_text(panel_letter: str, panel_body: str, single_panel: bool) -> str:
    sentences = split_sentences(panel_body)
    if not sentences:
        return f"{panel_letter},"
    limit = MAX_SINGLE_PANEL_WORDS if single_panel else MAX_WORDS_PER_PANEL
    selected: list[str] = []
    for sentence in sentences:
        candidate = " ".join(selected + [sentence])
        if selected and len(candidate.split()) > limit:
            break
        selected.append(sentence)
        if len(" ".join(selected).split()) >= limit * 0.75:
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
    body = clean_markdown(" ".join(lines[1:]))
    title = heading
    title_match = re.match(r"^(Fig\. \d+|Extended Data Fig\. \d+)\.\s+(.+)$", heading)
    if title_match:
        fig_id, fig_title = title_match.groups()
        title = f"{fig_id} | {fig_title.rstrip('.')}"

    panel_pattern = re.compile(r"\*\*([a-z]),\*\*")
    matches = list(panel_pattern.finditer(" ".join(lines[1:])))
    if not matches:
        first = split_sentences(body)[:2]
        return "\n".join([title, " ".join(first)])

    source = " ".join(lines[1:])
    panels: list[tuple[str, str]] = []
    for idx, match in enumerate(matches):
        start = match.end()
        end = matches[idx + 1].start() if idx + 1 < len(matches) else len(source)
        panels.append((match.group(1), source[start:end].strip()))

    single_panel = len(panels) == 1
    panel_text = [concise_panel_text(letter, text, single_panel) for letter, text in panels]
    legend = title + "\n" + " ".join(panel_text)
    if not legend.endswith("."):
        legend += "."
    return legend


def wrap_text_block(text: str) -> str:
    paragraphs = text.split("\n")
    result = []
    for para in paragraphs:
        if para.strip():
            result.append("\n".join(textwrap.wrap(para, width=WRAP_WIDTH)))
        else:
            result.append("")
    return "\n".join(result)


def render_page(fig: plt.Figure, img_path: Path, legend: str, page_num: int) -> None:
    """A4 page: image on image-axes, legend/text on separate text-axes (vector)."""
    fig.clf()

    # Prepare legend
    legend = make_concise_legend(legend)
    legend_lines = legend.split("\n")
    title_line = "\n".join(textwrap.wrap(legend_lines[0], width=105))
    body = "\n".join(legend_lines[1:])
    body = wrap_text_block(body)
    n_title = title_line.count("\n") + 1
    n_body = body.count("\n") + 1 if body else 0

    # Estimate heights (inches)
    line_h = BODY_SIZE / 72 * 1.22
    title_h = n_title * (TITLE_SIZE / 72) * 1.30
    legend_text_h = title_h + 0.06 + n_body * line_h + 0.18

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
    ax_text.text(0, y, title_line, fontsize=TITLE_SIZE, fontweight="bold",
                 va="top", ha="left", color="#1F1F1F", linespacing=1.25,
                 transform=ax_text.transAxes)
    y -= 0.075 + (n_title - 1) * 0.055
    ax_text.text(0, y, body, fontsize=BODY_SIZE, fontweight="normal",
                 va="top", ha="left", color="#333333",
                 linespacing=1.25, transform=ax_text.transAxes)

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
