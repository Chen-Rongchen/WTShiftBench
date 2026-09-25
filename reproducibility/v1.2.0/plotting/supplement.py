"""Render frozen display data; no model fitting or statistical inference."""
import json
from pathlib import Path
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.lines import Line2D
from matplotlib.patches import Rectangle
import numpy as np
import pandas as pd
HCC = ['HCC1143', 'HCC38']
COLORS = {'HCC1143': '#73729f', 'HCC38': '#3b827a'}
MARKERS = {'HCC1143': 'o', 'HCC38': 's'}
(INK, GRAY, LINE) = ('#24313a', '#74818b', '#dde4ea')
MODELS = ['Geneformer kernel', 'Geneformer ridge', 'Linear low-rank', 'scGPT kernel', 'scGPT ridge', 'CPA', 'CellOT', 'GEARS', 'scGen']
EXTERNAL = ['Replogle K562 essential day 6', 'Replogle K562 genome-wide day 8', 'HepG2 day 7', 'Jurkat day 7', 'K562 TF day 7', 'K562 TF day 13']
METRIC_NAMES = {'real_shift_mean_abs': 'Mean absolute', 'real_shift_L2': 'L2', 'real_shift_top20_mean': 'Top 20', 'real_shift_top50_mean': 'Top 50', 'real_shift_top100_mean': 'Top 100', 'real_shift_top50_concentration': 'Top-50 concentration', 'real_Edistance': 'E-distance', 'real_DEG_burden': 'Threshold-based breadth'}

def pick(d, **keys):
    for (k, v) in keys.items():
        d = d.loc[d[k].eq(v)]
    assert len(d) == 1, keys
    return d.iloc[0]

def page(title, height):
    fig = plt.figure(figsize=(180 / 25.4, height), layout='constrained')
    fig.suptitle(title, fontsize=11)
    return fig

def heading(ax, letter, title):
    ax.set_title(title, loc='left', fontsize=9, pad=13)
    ax.text(-0.025, 1.025, letter, transform=ax.transAxes, ha='right', va='bottom', fontsize=11, weight='bold', gid='panel_letter')

def points(ax, x, y, c, **kw):
    ax.scatter(x, y, color=COLORS[c], marker=MARKERS[c], s=14, alpha=0.75, **kw)

def reference(ax, value=0, axis='x'):
    (ax.axvline if axis == 'x' else ax.axhline)(value, color='#bdc6cd', lw=0.6, ls='--', zorder=0)

def legend(fig):
    fig.legend(handles=[Line2D([], [], marker=MARKERS[c], color=COLORS[c], ls='', label=c) for c in HCC], loc='outside lower center', ncol=2, frameon=False, fontsize=8)

def forest(ax, d, labels, key, ci=False):
    for (i, label) in enumerate(labels):
        for (j, c) in enumerate(HCC):
            r = pick(d, cell_line=c, label=label)
            y = i + (j - 0.5) * 0.25
            if ci:
                ax.plot([r.interval_low, r.interval_high], [y, y], color=COLORS[c], alpha=0.6, lw=1)
            points(ax, r[key], y, c)
    ax.set_yticks(range(len(labels)), labels)
    ax.invert_yaxis()
    reference(ax)

def construction():
    overview = read('M01_dataset_overview')
    attr = read('M01_attrition')
    eligible = read('M01_eligibility')
    labels = read('M01_frozen_categories')
    targets = read('M05_formal_target_metrics')
    completion = read('M06_completion')
    rep = read('M06_replogle_registry')
    fig = page('Data and evaluation-set construction', 180 / 25.4)
    fig._suptitle.set_visible(False)
    gs = fig.add_gridspec(2, 1, height_ratios=[1, 2.65], hspace=0.045)
    ax = fig.add_subplot(gs[0])
    ax.axis('off')
    heading(ax, 'A', 'Dataset overview')
    rows = overview.astype(str).replace({'Association': 'Additional association'}).values.tolist()
    tab = ax.table(cellText=rows, colLabels=['Context', 'Day', 'Modality', 'Cells at\nindicated stage', 'Endpoint-association\ngenes', 'Analysis role'], colWidths=[0.23, 0.05, 0.1, 0.18, 0.19, 0.25], bbox=[0, 0, 1, 0.96], cellLoc='left')
    tab.auto_set_font_size(False)
    tab.set_fontsize(7.5)
    for ((r, c), cell) in tab.get_celld().items():
        cell.set_edgecolor(LINE)
        cell.set_linewidth(0.4)
        cell.set_height(cell.get_height() * (1.4 if r == 0 else 0.95))
        if r == 0:
            cell.set_facecolor('#f1f3f5')
    ax = fig.add_subplot(gs[1])
    ax.axis('off')
    ax.set(xlim=(0, 1), ylim=(0, 1))
    heading(ax, 'B', 'Eligibility and model-scoring set construction')

    def txt(x, y, s, size=8, color=INK, weight='normal', ha='center'):
        return ax.text(x, y, s, fontsize=size, color=color, weight=weight, ha=ha, va='center', linespacing=1.15)

    def arrow(x, y, xx, yy, color=GRAY):
        ax.annotate('', xy=(xx, yy), xytext=(x, y), arrowprops=dict(arrowstyle='->', lw=0.7, color=color, shrinkA=0, shrinkB=0))

    def branch(x, y, s):
        ax.plot([x, x + 0.045], [y, y], color=GRAY, lw=0.6)
        txt(x + 0.055, y, s, 7.5, '#596670', ha='left')
    checks = []
    txt(0.29, 1.012, 'Target axis', 9, weight='bold')
    for (j, c) in enumerate(HCC):
        x = 0.12 + j * 0.34
        n = [int(pick(attr, cell_line=c, stage=s).n_retained) for s in ['assayed_noncontrol_targets', 'targets_passing_minimum_cells', 'targets_with_exact_model_endpoint']]
        excluded = eligible.loc[eligible.cell_line.eq(c) & ~eligible.final_eligible]
        low = ', '.join(excluded.loc[excluded.exclusion_reason.eq('below_minimum_cells'), 'target_gene'])
        missing = ', '.join(excluded.loc[excluded.exclusion_reason.eq('exact_model_endpoint_missing'), 'target_gene'])
        full = labels.loc[labels.cell_line.eq(c)]
        scored = targets.loc[targets.cell_line.eq(c), ['target_gene', 'endpoint_category']].drop_duplicates()
        assert scored.target_gene.is_unique and len(full) == n[-1]
        assert scored.set_index('target_gene').endpoint_category.equals(full.set_index('target_gene').loc[scored.target_gene, 'endpoint_category'])
        left = sorted(set(full.target_gene) - set(scored.target_gene))
        ng = completion.loc[completion.cell_line.eq(c), 'n_genes'].unique()
        assert list(ng) == [47]
        nf = int(full.endpoint_category.eq('endpoint_anchor').sum())
        ns = int(scored.endpoint_category.eq('endpoint_anchor').sum())
        txt(x, 0.978, c, 9, COLORS[c], weight='bold')
        ax.scatter(x - 0.095, 0.978, color=COLORS[c], marker=MARKERS[c], s=18)
        for (y, value, label) in zip([0.91, 0.77, 0.625], n, ['assayed targets', '≥20 recovered cells', 'endpoint-eligible']):
            txt(x, y, str(value), 12, weight='bold')
            txt(x, y - 0.031, label, 7.5)
        arrow(x, 0.852, x, 0.8, COLORS[c])
        branch(x, 0.825, low + '\n<20 cells')
        arrow(x, 0.716, x, 0.656, COLORS[c])
        branch(x, 0.685, missing + '\ndependency missing')
        arrow(x, 0.568, x, 0.535, COLORS[c])
        txt(x, 0.51, 'Frozen labels', 8, weight='bold')
        txt(x, 0.482, f'{nf} anchors', 7.5)
        arrow(x, 0.456, x, 0.39, COLORS[c])
        if left:
            branch(x, 0.424, ', '.join(left) + '\noutside intersection')
        txt(x, 0.36, str(len(scored)), 12, weight='bold')
        txt(x, 0.328, 'common scoring targets', 7.5)
        txt(x, 0.301, f'{ns} anchors retained', 7.5)
        ax.plot([x, x, 0.49], [0.28, 0.251, 0.251], color=COLORS[c], lw=0.7)
        checks.append(dict(context=c, attrition=n, scoring_targets=len(scored), full_anchors=nf, scoring_anchors=ns, intersection_excluded=left, scoring_genes=int(ng[0])))
    assert overview.loc[overview.Context.isin(HCC), 'Association genes'].unique().tolist() == ['36,601']
    txt(0.84, 1.012, 'Gene axis', 9, weight='bold')
    txt(0.84, 0.91, '36,601', 12, weight='bold')
    txt(0.84, 0.865, 'Endpoint-association\ngenes', 7.5)
    arrow(0.84, 0.812, 0.84, 0.748)
    txt(0.84, 0.707, 'Normalized/aligned\nexpression space', 8)
    arrow(0.84, 0.658, 0.84, 0.571)
    txt(0.84, 0.526, 'Model-specific alignment\nand gene intersection', 8)
    arrow(0.84, 0.475, 0.84, 0.391)
    txt(0.84, 0.36, '47', 12, weight='bold')
    txt(0.84, 0.328, 'shared scoring genes', 7.5)
    ax.plot([0.84, 0.84, 0.49], [0.28, 0.251, 0.251], color=GRAY, lw=0.7)
    arrow(0.49, 0.251, 0.49, 0.225)
    txt(0.49, 0.204, '47 targets × 47 genes', 11, weight='bold')
    txt(0.49, 0.176, 'Separate matrix per HCC context; frozen labels retained.', 7.5)
    ax.axhline(0.148, color=LINE, lw=0.6)
    nt = rep.n_targets.unique()
    ng = rep.n_genes.unique()
    assert len(nt) == len(ng) == 1
    txt(0.01, 0.121, 'Replogle K562 essential CRISPRi — day 6', 8, weight='bold', ha='left')
    txt(0.14, 0.058, f'{nt[0]:,} targets', 10, weight='bold')
    txt(0.14, 0.021, 'Independent audit', 7.5)
    arrow(0.28, 0.056, 0.36, 0.056)
    txt(0.51, 0.056, 'Shared observed/predicted\ngene space', 7.5)
    arrow(0.66, 0.056, 0.72, 0.056)
    txt(0.86, 0.058, f'{nt[0]:,} × {ng[0]:,}', 10, weight='bold')
    txt(0.86, 0.021, 'targets × genes', 7.5)
    (OUT / 'S1-construction-checks.json').write_text(json.dumps(checks, indent=2) + '\n')
    save(fig, 'M01_construction')

def additional():
    d = read('M04_current_target_distributions')
    inference = result('16_association_inference.csv')
    fig = page('Raw shift–dependency distributions across contexts', 180 / 25.4)
    axes = fig.subplots(3, 2)
    fig._suptitle.set_visible(False)
    for (i, (ax, c)) in enumerate(zip(axes.flat, EXTERNAL)):
        q = d.loc[d.display_context.eq(c)]
        r = pick(inference, context=c, analysis_id='raw_shift_unadjusted')
        assert len(q) == r.n_targets
        large = len(q) >= 1000
        alpha = 0.13 if len(q) >= 5000 else 0.22 if large else 0.75
        ax.scatter(q.real_shift_mean_abs, q.depmap_gene_dependency, s=1.2 if large else 9, color=INK, alpha=alpha, edgecolors='none', rasterized=large)
        ax.set_ylim(-.03, 1.22)
        ax.set_yticks(np.arange(0, 1.01, .2))
        ax.set_gid('S4-' + chr(65+i))
        heading(ax, chr(65 + i), c.replace('Replogle K562', 'Replogle K562\n'))
        ax.text(0.03, 0.97, f'n = {len(q):,}; ρ = {r.spearman_rho:.3f}\n95% CI [{r.bootstrap_ci_low:.3f}, {r.bootstrap_ci_high:.3f}]', transform=ax.transAxes, va='top', fontsize=7.5)
        ax.set_xlabel('Raw mean-absolute shift')
        ax.set_ylabel('CRISPR dependency probability')
        CHECKS.append(dict(panel='S4', context=c, n=len(q), point_area=1.2 if large else 9, alpha=alpha, rasterized=large))
    save(fig, 'M04_additional_contexts')
