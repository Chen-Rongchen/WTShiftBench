"""Template for panel build scripts. Each script monkey-patches the output dirs
of the source module and calls write_panel() directly, preserving all formatting."""

import sys, types
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TEST = ROOT / "manuscript/build_scripts/test_output"
sys.path.insert(0, str(ROOT / "src"))


def redirect_output(module, stem: str):
    """Monkey-patch module's output_dir/panel_dir to point to test_output."""
    odir = TEST / stem
    pdir = odir / "panels"
    module.output_dir = lambda _root: odir
    module.panel_dir = lambda _root: pdir
    # Also remove manuscript dir writes
    if hasattr(module, 'manuscript_figure_dir'):
        module.manuscript_figure_dir = lambda _root: odir
    if hasattr(module, 'manuscript_panel_dir'):
        module.manuscript_panel_dir = lambda _root: pdir
    return pdir


def build_one(module, panel_id: str, stem: str):
    """Build a single panel using the module's existing infrastructure."""
    from wtbench.manuscript.manuscript_style import apply_manuscript_style
    apply_manuscript_style()
    root = module.repo_root()
    pdir = redirect_output(module, stem)
    pdir.mkdir(parents=True, exist_ok=True)
    sources = module._build_sources(root) if hasattr(module, '_build_sources') else module.build_sources(root)
    render = module._render_panel_by_id(panel_id) if hasattr(module, '_render_panel_by_id') else module.render_panel_by_id(panel_id)
    title = module.panel_title(panel_id)
    sizes = getattr(module, 'PANEL_SIZES', None) or {}
    w = sizes.get(panel_id, (3.2, 2.35))[0] if isinstance(sizes.get(panel_id), tuple) else 3.2
    h = sizes.get(panel_id, (3.2, 2.35))[1] if isinstance(sizes.get(panel_id), tuple) else 2.35
    module.write_panel(
        root=root, panel_id=panel_id, panel_title=title,
        source_df=sources[panel_id], render=render, width=w, height=h,
    )
    print(f"  Built {stem} panel {panel_id}")
