#!/usr/bin/env python3
"""Add build_single_panel() and build_combined() to all remaining figure source modules."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src/wtbench/manuscript"


API_FIG3 = '''

# --- Public API for build scripts ---

def _ensure_style() -> None:
    apply_manuscript_style()


def build_single_panel(panel_id: str, output_root: Path) -> None:
    _ensure_style()
    root = repo_root()
    sources = _build_sources(root)
    if panel_id not in sources:
        raise ValueError(f"Unknown panel_id: {panel_id}")
    panel_sizes = {"a": (3.6, 2.4), "b": (3.3, 2.4), "c": (3.6, 2.8), "d": (3.3, 2.4)}
    w, h = panel_sizes[panel_id]
    fig, ax = plt.subplots(figsize=(w, h))
    fig.patch.set_facecolor("white")
    ax.set_facecolor("white")
    _render_panel_by_id(panel_id)(ax, sources[panel_id])
    ensure_dir(output_root)
    s = f"Figure_3_panel_{panel_id}"
    write_tsv(sources[panel_id], output_root / f"{s}_source_data.tsv")
    finalize_manuscript_figure(fig)
    fig.savefig(output_root / f"{s}.png", dpi=300, bbox_inches="tight")
    fig.savefig(output_root / f"{s}.pdf", bbox_inches="tight")
    plt.close(fig)
    print(f"  Figure 3 panel {panel_id} -> {output_root}")


def build_combined(output_root: Path) -> None:
    _ensure_style()
    root = repo_root()
    sources = _build_sources(root)
    fig = plt.figure(figsize=(10.0, 6.5))
    outer = fig.add_gridspec(2, 1, height_ratios=[1.0, 1.12], hspace=0.28, left=0.09, right=0.97, top=0.95, bottom=0.08)
    top = outer[0].subgridspec(1, 2, wspace=0.38)
    bot = outer[1].subgridspec(1, 2, width_ratios=[3, 7], wspace=0.28)
    _render_panel_by_id("a")(fig.add_subplot(top[0, 0]), sources["a"])
    _render_panel_by_id("b")(fig.add_subplot(top[0, 1]), sources["b"])
    _render_panel_by_id("c")(fig.add_subplot(bot[0]), sources["c"])
    _render_panel_by_id("d")(fig.add_subplot(bot[1]), sources["d"])
    ensure_dir(output_root)
    finalize_manuscript_figure(fig)
    fig.savefig(output_root / "Figure_3.png", dpi=300, bbox_inches="tight")
    fig.savefig(output_root / "Figure_3.pdf", bbox_inches="tight")
    plt.close(fig)
    print(f"  Figure 3 combined -> {output_root}")
'''

API_FIG4 = '''

# --- Public API for build scripts ---

def _ensure_style() -> None:
    apply_manuscript_style()


def build_single_panel(panel_id: str, output_root: Path) -> None:
    _ensure_style()
    root = repo_root()
    sources = _build_panel_sources(root)
    if panel_id not in sources:
        raise ValueError(f"Unknown panel_id: {panel_id}")
    panel_sizes = {"a": (5.1, 2.9), "b": (5.0, 2.9), "c": (5.4, 4.15)}
    w, h = panel_sizes[panel_id]
    fig, ax = plt.subplots(figsize=(w, h))
    fig.patch.set_facecolor("white")
    ax.set_facecolor("white")
    render_panel_by_id(panel_id)(ax, sources[panel_id])
    ensure_dir(output_root)
    s = f"Figure_4_panel_{panel_id}"
    write_tsv(sources[panel_id], output_root / f"{s}_source_data.tsv")
    finalize_manuscript_figure(fig)
    fig.savefig(output_root / f"{s}.png", dpi=300, bbox_inches="tight")
    fig.savefig(output_root / f"{s}.pdf", bbox_inches="tight")
    plt.close(fig)
    print(f"  Figure 4 panel {panel_id} -> {output_root}")


def build_combined(output_root: Path) -> None:
    _ensure_style()
    root = repo_root()
    sources = _build_panel_sources(root)
    fig = plt.figure(figsize=(9.6, 6.9))
    outer = fig.add_gridspec(2, 1, height_ratios=[0.92, 1.02], hspace=0.28, left=0.060, right=0.975, top=0.950, bottom=0.088)
    top = outer[0].subgridspec(1, 2, width_ratios=[0.90, 1.0], wspace=0.18)
    render_panel_by_id("a")(fig.add_subplot(top[0, 0]), sources["a"])
    render_panel_by_id("b")(fig.add_subplot(top[0, 1]), sources["b"])
    render_panel_by_id("c")(fig.add_subplot(outer[1]), sources["c"])
    ensure_dir(output_root)
    finalize_manuscript_figure(fig)
    fig.savefig(output_root / "Figure_4.png", dpi=300, bbox_inches="tight")
    fig.savefig(output_root / "Figure_4.pdf", bbox_inches="tight")
    plt.close(fig)
    print(f"  Figure 4 combined -> {output_root}")
'''

API_FIG5 = '''

# --- Public API for build scripts ---

def _ensure_style() -> None:
    apply_manuscript_style()


def build_single_panel(panel_id: str, output_root: Path) -> None:
    _ensure_style()
    root = repo_root()
    sources = _build_panel_sources(root)
    if panel_id not in sources:
        raise ValueError(f"Unknown panel_id: {panel_id}")
    panel_sizes = {"a": (5.5, 2.2), "b": (5.5, 2.6), "c": (5.5, 3.6), "d": (5.5, 3.6)}
    w, h = panel_sizes[panel_id]
    fig, ax = plt.subplots(figsize=(w, h))
    fig.patch.set_facecolor("white")
    ax.set_facecolor("white")
    render_panel_by_id(panel_id)(ax, sources[panel_id])
    ensure_dir(output_root)
    s = f"Figure_5_panel_{panel_id}"
    write_tsv(sources[panel_id], output_root / f"{s}_source_data.tsv")
    finalize_manuscript_figure(fig)
    fig.savefig(output_root / f"{s}.png", dpi=300, bbox_inches="tight")
    fig.savefig(output_root / f"{s}.pdf", bbox_inches="tight")
    plt.close(fig)
    print(f"  Figure 5 panel {panel_id} -> {output_root}")


def build_combined(output_root: Path) -> None:
    _ensure_style()
    root = repo_root()
    sources = _build_panel_sources(root)
    fig = plt.figure(figsize=(11.5, 8.6))
    outer = fig.add_gridspec(2, 1, height_ratios=[0.86, 0.78], hspace=0.32, left=0.06, right=0.97, top=0.95, bottom=0.08)
    top = outer[0].subgridspec(1, 2, wspace=0.34)
    bot = outer[1].subgridspec(1, 2, wspace=0.30)
    render_panel_by_id("a")(fig.add_subplot(top[0, 0]), sources["a"])
    render_panel_by_id("b")(fig.add_subplot(top[0, 1]), sources["b"])
    render_panel_by_id("c")(fig.add_subplot(bot[0, 0]), sources["c"])
    render_panel_by_id("d")(fig.add_subplot(bot[0, 1]), sources["d"])
    ensure_dir(output_root)
    finalize_manuscript_figure(fig)
    fig.savefig(output_root / "Figure_5.png", dpi=300, bbox_inches="tight")
    fig.savefig(output_root / "Figure_5.pdf", bbox_inches="tight")
    plt.close(fig)
    print(f"  Figure 5 combined -> {output_root}")
'''


def append_if_missing(filepath: Path, text: str, marker: str = "Public API for build scripts") -> None:
    content = filepath.read_text()
    if marker in content:
        print(f"  SKIP {filepath.name} (already present)")
        return
    filepath.write_text(content + text)
    print(f"  DONE {filepath.name}")


# Main figures
append_if_missing(SRC / "figure3_model_tradeoff.py", API_FIG3)
append_if_missing(SRC / "figure4_sweep_controls.py", API_FIG4)
append_if_missing(SRC / "figure6_boundary.py", API_FIG5)

# For ED figures, add a generic build_single_panel using the existing function names
print("\nChecking ED figures...")
for fname, man_stem, pan_size_src in [
    ("extended_data_figure1.py", "Extended_Data_Figure_1", "{(3.2, 2.35)}"),
    ("extended_data_figure3_v2.py", "Extended_Data_Figure_3", '{"a": (7.0, 4.2), "b": (6.0, 6.2), "c": (5.0, 6.2)}'),
    ("extended_data_figure10_axis_explanatory.py", "Extended_Data_Figure_4", '{"a": (4.1, 3.4), "b": (5.1, 3.4)}'),
    ("extended_data_figure9_biological_landing.py", "Extended_Data_Figure_5", '{"a": (6.0, 3.8)}'),
    ("extended_data_figure_robustness.py", "Extended_Data_Figure_6", "{(3.2, 2.35)}"),
]:
    fp = SRC / fname
    if not fp.exists():
        print(f"  MISSING {fname}")
        continue
    content = fp.read_text()
    if "Public API for build scripts" in content:
        print(f"  SKIP {fname}")
        continue

    # Check function names used
    if "_build_panel_sources" in content:
        src_func = "_build_panel_sources"
    elif "def build_sources" in content:
        src_func = "build_sources"
    else:
        print(f"  WARN {fname}: cannot find source builder")
        continue

    if "_render_panel_by_id" in content:
        rend_func = "_render_panel_by_id"
    elif "def render_panel_by_id" in content:
        rend_func = "render_panel_by_id"
    else:
        print(f"  WARN {fname}: cannot find render function")
        continue

    # Check for active_panels
    if "ACTIVE_PANELS" in content:
        panels_var = "ACTIVE_PANELS"
    elif "PANEL_IDS" in content:
        panels_var = "PANEL_IDS"
    else:
        print(f"  WARN {fname}: cannot find panel IDs")
        continue

    # Check for manuscript-specific figure dir function
    man_dir_func = "output_dir"

    api = f'''

# --- Public API for build scripts ---

def _ensure_style() -> None:
    apply_manuscript_style()


def build_single_panel(panel_id: str, output_root: Path) -> None:
    _ensure_style()
    root = repo_root()
    sources = {src_func}(root)
    if panel_id not in sources:
        raise ValueError(f"Unknown panel_id: {{panel_id}}")
    panel_sizes = {pan_size_src}
    w, h = panel_sizes.get(panel_id, (3.2, 2.35))
    fig, ax = plt.subplots(figsize=(w, h))
    fig.patch.set_facecolor("white")
    ax.set_facecolor("white")
    {rend_func}(panel_id)(ax, sources[panel_id])
    ensure_dir(output_root)
    s = f"{{man_stem}}_panel_{{panel_id}}"
    write_tsv(sources[panel_id], output_root / f"{{s}}_source_data.tsv")
    finalize_manuscript_figure(fig)
    fig.savefig(output_root / f"{{s}}.png", dpi=300, bbox_inches="tight")
    fig.savefig(output_root / f"{{s}}.pdf", bbox_inches="tight")
    plt.close(fig)
    print(f"  {{man_stem}} panel {{panel_id}} -> {{output_root}}")
'''
    fp.write_text(content + api)
    print(f"  DONE {fname}")

print("\nAll done.")
