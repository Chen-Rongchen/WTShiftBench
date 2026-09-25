"""Render frozen display data; no model fitting or statistical inference."""
import json
import shutil
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap, to_rgba
from matplotlib.lines import Line2D
from matplotlib.patches import Patch, Rectangle
from matplotlib.transforms import Bbox
import numpy as np
import pandas as pd

def cell_text_color(background):
    rgb = np.asarray(to_rgba(background)[:3])
    linear = np.where(rgb <= 0.04045, rgb / 12.92, ((rgb + 0.055) / 1.055) ** 2.4)
    luminance = float(linear @ np.array([0.2126, 0.7152, 0.0722]))
    return '#000000' if (luminance + 0.05) / 0.05 >= 1.05 / (luminance + 0.05) else '#ffffff'

def build(p, only=None):
    plt.rcParams.update({'font.size': 7.5, 'axes.labelsize': 7.5, 'axes.titlesize': 8, 'xtick.labelsize': 7.5, 'ytick.labelsize': 7.5, 'legend.fontsize': 7.5})
    out = p.OUT
    checks = []
    display = lambda name: 'Chargram low-rank' if name == 'Linear low-rank' else name
    model_labels = [display(m) for m in p.MODELS]

    def page(title, height=265):
        f = plt.figure(figsize=(180 / 25.4, height / 25.4), layout='constrained')
        return f

    def head(ax, letter, title):
        ax.set_title(title, loc='left', fontsize=8, pad=9)
        ax.text(-0.025, 1.025, letter, transform=ax.transAxes, ha='right', va='bottom', fontsize=11, weight='bold', gid='panel_letter')

    def save(fig, n):
        if only is None or n in only:
            p.save(fig, n)
        else:
            plt.close(fig)
    f = page('Raw-shift and endpoint-form sensitivity', 210)
    gs = f.add_gridspec(3, 2, height_ratios=[1.3, 0.72, 1.98], hspace=0.05, wspace=0.08)
    a = f.add_subplot(gs[0, 0])
    b = f.add_subplot(gs[0, 1])
    c = f.add_subplot(gs[1, :])
    summary = p.read('M02_raw_summary')
    anchors = p.read('M02_historical_anchor_influence')
    ge = p.read('M02_endpoint_form')
    p.forest(a, summary, ['Mean absolute', 'L2', 'Top 20', 'Top 50', 'Top 100', 'Threshold-based breadth'], 'estimate', True)
    a.set_yticklabels(['Mean absolute', 'L2', 'Top-20 mean', 'Top-50 mean', 'Top-100 mean', 'Threshold-based\nresponse breadth'])
    head(a, 'A', 'Raw-response summaries')
    a.set_xlabel('Spearman ρ (95% CI)')
    a.set_xticks([0, 0.4, 0.8])
    names = {'K562_essential_day7': 'Replogle ess. d6', 'K562_GWPS_day8': 'Replogle GW d8', 'HepG2': 'HepG2 d7', 'Jurkat': 'Jurkat d7', 'dixit_2016_k562_tf_7d_gse90063': 'K562 TF d7', 'dixit_2016_k562_tf_13d_gse90063': 'K562 TF d13'}
    for (i, r) in enumerate(ge.itertuples()):
        for (v, dy, fill) in [(r.probability_rho_same_targets, -0.13, 'white'), (r.spearman_rho, 0.13, p.COLORS.get(r.cell_line, p.INK))]:
            b.scatter(v, i + dy, facecolors=fill, edgecolors=p.COLORS.get(r.cell_line, p.INK), marker=p.MARKERS.get(r.cell_line, 'o'), s=16)
    b.set_yticks(range(len(ge)), [names.get(x, x) for x in ge.cell_line])
    b.set_ylim(len(ge) - 0.5, -1.6)
    b.set_xticks([0.3, 0.5, 0.7])
    b.set_xlabel('Spearman ρ; mean-absolute raw shift')
    head(b, 'B', 'DepMap 25Q3 endpoint representation')
    b.legend(handles=[Line2D([], [], marker='o', ls='', color=p.INK, mfc=fill, label=label) for (fill, label) in [('white', 'Dependency probability'), (p.INK, 'Sign-inverted gene effect')]], loc='upper left', frameon=False, fontsize=7.5, handletextpad=0.3, borderpad=0, labelspacing=0.15)
    p.forest(c, anchors, ['none', 'PFDN5', 'PRPF6', 'PMF1', 'ZNF131', 'all_four_anchors', 'jackknife_min', 'jackknife_max'], 'spearman_rho')
    c.set_yticklabels(['No removal', 'Remove PFDN5', 'Remove PRPF6', 'Remove PMF1', 'Remove ZNF131', 'Remove all four', 'Jackknife minimum', 'Jackknife maximum'])
    head(c, 'C', 'Influence of raw-shift anchors')
    c.set_xlabel('Spearman ρ; point estimates')
    old = p.read('M02_gene_subset_history')
    section = gs[2, :].subgridspec(2, 1, height_ratios=[.08,1], hspace=.015)
    title_ax=f.add_subplot(section[0]); title_ax.axis('off')
    head(title_ax,'D','Gene-subset sensitivity')
    grid = section[1].subgridspec(2, 3, hspace=0.015, wspace=0.05)
    for (j, m) in enumerate(['real_shift_mean_abs', 'real_shift_L2', 'real_DEG_burden']):
        for (i, ranking) in enumerate(['control_expression', 'perturbation_response']):
            ax = f.add_subplot(grid[i, j])
            for ctx in p.HCC:
                d = old.loc[old.cell_line.eq(ctx) & old.truth_metric.eq(m) & old.ranking.eq(ranking)]
                d = d.set_index(d.top_n.astype(str)).loc[['100', '500', '1000', '2000', 'all']]
                ax.plot(range(5), d.aligned_spearman, color=p.COLORS[ctx], marker=p.MARKERS[ctx], ms=2.8, lw=0.8)
            if i == 0:
                ax.set_title(['Mean absolute', 'L2', 'Threshold-based\nresponse breadth'][j],fontsize=8,pad=7)
            ax.set_ylim(0, 1)
            ax.set_yticks([0, 0.5, 1])
            ax.set_xticks(range(5), ['100', '500', '1k', '2k', 'All'])
            if j == 0:
                ax.set_ylabel(('Control-expression ranking' if i == 0 else 'Response ranking') + '\nRaw association, ρ')
            if i == 1:
                ax.set_xlabel('Selected genes')
    p.legend(f)
    save(f, 'S2')
    f = page('Technical coverage and sampling diagnostics', 220)
    gs = f.add_gridspec(4, 2, height_ratios=[1, 1, 1.12, 1.08], hspace=0.095, wspace=0.08)
    axes = [f.add_subplot(gs[i, j]) for i in range(2) for j in range(2)]
    elig = p.read('M01_eligibility')
    cov = p.read('M03_target_covariates')
    tvd = p.read('M03_historical_TVD')
    for ctx in p.HCC:
        d = elig.loc[elig.cell_line.eq(ctx)].sort_values('n_cells_target')
        for keep in [True, False]:
            mask = d.final_eligible.eq(keep)
            axes[0].scatter(d.loc[mask, 'n_cells_target'], np.arange(1, len(d) + 1)[mask], s=12, marker=p.MARKERS[ctx], edgecolors=p.COLORS[ctx], facecolors=p.COLORS[ctx] if keep else 'white', alpha=0.8)
        q = cov.loc[cov.cell_line.eq(ctx) & cov.target_expression_available].dropna(subset=['baseline_target_expression', 'perturbed_target_expression'])
        p.points(axes[1], q.baseline_target_expression, q.perturbed_target_expression, ctx)
        p.points(axes[2], q.baseline_target_expression, q.observed_shift_mean_abs, ctx)
    head(axes[0], 'A', 'Recovered-cell coverage')
    axes[0].set(xlabel='Recovered cells per target', ylabel='Target rank')
    axes[0].set_ylim(-2, 64)
    axes[0].legend(handles=[Line2D([],[],marker='o',ls='',color=p.INK,mfc=fill,label=label) for fill,label in [('white','Excluded'),(p.INK,'Eligible')]],loc='upper left',frameon=False,fontsize=7.5)
    head(axes[1], 'B', 'Target-gene expression')
    axes[1].set(xlabel='Control mean log-expression', ylabel='Perturbed mean log-expression')
    axes[1].text(0.03, 0.97, 'Not a perturbation-efficiency estimate', transform=axes[1].transAxes, va='top', fontsize=7.5)
    lim = max(axes[1].get_xlim()[1], axes[1].get_ylim()[1])
    axes[1].plot([0, lim], [0, lim], ls='--', lw=0.6, color=p.GRAY)
    head(axes[2], 'C', 'Baseline expression vs raw shift')
    axes[2].set(xlabel='Target-gene expression in controls', ylabel='Raw mean-absolute shift')
    for (i, key) in enumerate(tvd.strat_column.unique()):
        for (j, ctx) in enumerate(p.HCC):
            p.points(axes[3], p.pick(tvd, cell_line=ctx, strat_column=key).mean_tvd, i + (j - 0.5) * 0.25, ctx)
    axes[3].set_yticks(range(5), ['GEM group', 'UMI threshold bins', 'UMI quantiles', 'Detected genes', 'Transcriptome signal'])
    axes[3].invert_yaxis()
    head(axes[3], 'D', 'Technical-covariate diagnostic')
    axes[3].set_xlabel('Mean target-to-control TVD')
    e = f.add_subplot(gs[2, :])
    res = p.read('M03_control_resamples')
    for (i, m) in enumerate(p.METRIC_NAMES):
        for (j, ctx) in enumerate(p.HCC):
            d = res.loc[res.cell_line.eq(ctx) & res.truth_metric.eq(m)].sort_values('replicate')
            assert len(d) == 24
            p.points(e, d.spearman_rho_aligned, i + (j - 0.5) * 0.28 + np.linspace(-0.07, 0.07, 24), ctx)
    e.set_yticks(range(8), ['Mean absolute', 'L2', 'Top-20 mean', 'Top-50 mean', 'Top-100 mean', 'Top-50 concentration', 'Energy-distance statistic', 'Threshold-based\nresponse breadth'])
    e.invert_yaxis()
    e.set_xlabel('Raw shift–dependency Spearman ρ')
    head(e, 'E', 'Control-reference subsampling')
    for (j, (name, title)) in enumerate([('M03_D10', 'Depth-specific eligible cohorts'), ('M03_D11', 'Fixed ≥100-cell cohort')]):
        ax = f.add_subplot(gs[3, j])
        d = p.read(name)
        for (k, ctx) in enumerate(p.HCC):
            q = d.loc[d.cell_line.eq(ctx)].sort_values('depth')
            x = np.arange(4) + (k - 0.5) * 0.2
            ax.vlines(x, q.rho_q025, q.rho_q975, color=p.COLORS[ctx], alpha=0.35, lw=5)
            p.points(ax, x, q.rho_median, ctx)
            for (xx, r) in zip(x, q.itertuples()):
                ax.annotate(str(r.n_targets), (xx, r.rho_q975), xytext=(-3 if k == 0 else 3, 5), textcoords='offset points', ha='right' if k == 0 else 'left', fontsize=7.5)
        head(ax, 'FG'[j], title)
        ax.set(ylim=(-0.08, 0.85), xlim=(-0.5, 3.5), xlabel='Cells sampled per target', ylabel='Raw shift–dependency Spearman ρ')
        ax.set_xticks(range(4), ['20', '25', '50', '100'])
    p.legend(f)
    save(f, 'S3')
    t = pd.read_csv(p.DATA / 'layout/S5-display-ranks.tsv', sep='\t')
    raw = p.read('M05_formal_target_metrics')
    formal = p.result('01_formal_and_diagnostic_context_metrics.csv')
    f = plt.figure(figsize=(180 / 25.4, 215 / 25.4))
    categories = [('endpoint_anchor', 'Endpoint anchors', '#3b827a'), ('shift_excess', 'Shift-excess', '#73729f'), ('dependency_excess', 'Dependency-excess', '#9b5a30'), ('low_information', 'Low-information', '#465261'), ('middle', 'Middle band', '#bdbdbd')]
    category_colors = {k: v for (k, _, v) in categories}
    cmap = LinearSegmentedColormap.from_list('rank_single', ['#f3f5f7', '#a2b3c2', '#354b61'])
    cmap.set_bad('#dddddd')
    f.text(0.015, 0.977, 'A', fontsize=11, weight='bold')
    f.text(0.065, 0.977, 'Shift-magnitude alignment: target-level ordering', fontsize=9)
    for (j, ctx) in enumerate(p.HCC):
        left = 0.19 + j * 0.4
        d = t.loc[t.cell_line.eq(ctx)]
        order = d[['target_gene', 'endpoint_category', 'display_target_position']].drop_duplicates().sort_values('display_target_position')
        ax = f.add_axes([left, 0.727, 0.3, 0.18])
        matrix = d.pivot(index='display_name', columns='target_gene', values='display_shift_percentile').loc[p.MODELS, order.target_gene]
        heat = ax.imshow(matrix, aspect='auto', vmin=0, vmax=100, cmap=cmap, interpolation='nearest')
        ax.set_yticks(range(9), model_labels if j == 0 else [''] * 9)
        ax.tick_params(axis='y', length=0)
        ax.set_xticks([0, 11, 23, 35, 46], [1, 12, 24, 36, 47])
        ax.set_xlabel('Targets ordered by dependency', labelpad=3)
        strip = f.add_axes([left, 0.915, 0.3, 0.01])
        strip.imshow([[to_rgba(category_colors[g]) for g in order.endpoint_category]], aspect='auto')
        strip.axis('off')
        f.text(left + 0.15, 0.932, ctx, ha='center', color=p.COLORS[ctx], fontsize=8.5)
        rho = f.add_axes([left + 0.305, 0.727, 0.065, 0.18])
        rho.axis('off')
        rho.set_ylim(8.5, -0.5)
        rho.text(0.5, 1.025, 'ρ', ha='center', transform=rho.transAxes)
        for (i, m) in enumerate(p.MODELS):
            rho.text(0.98, i, f'{p.pick(formal, display_name=m, cell_line=ctx).endpoint_alignment_spearman:.3f}'.replace('-', '−'), ha='right', va='center', fontsize=7.5)
    cb = f.colorbar(heat, cax=f.add_axes([0.27, 0.674, 0.56, 0.008]), orientation='horizontal', ticks=[0, 25, 50, 75, 100])
    cb.set_label('Predicted-shift percentile within output', labelpad=2)
    f.legend(handles=[Patch(facecolor=v, label=label) for (_, label, v) in categories], loc='center', bbox_to_anchor=(0.52, 0.96), ncol=5, frameon=False, fontsize=7.5, columnspacing=0.8, handlelength=1)
    for (letter, y, h, title) in [('B', 0.35, 0.205, 'Endpoint-anchor separation'), ('C', 0.045, 0.205, 'Directional recovery')]:
        f.text(0.015, y + h + 0.039, letter, fontsize=11, weight='bold')
        f.text(0.065, y + h + 0.039, title, fontsize=9)
        for (j, ctx) in enumerate(p.HCC):
            ax = f.add_axes([0.19 + j * 0.4, y, 0.35, h])
            ax.set_title(ctx, color=p.COLORS[ctx], fontsize=8.5, pad=5)
            for (i, m) in enumerate(p.MODELS):
                if letter == 'B':
                    d = t.loc[t.cell_line.eq(ctx) & t.display_name.eq(m)].sort_values('target_gene')
                    for (k, group) in enumerate(['endpoint_anchor', 'low_information']):
                        v = d.loc[d.endpoint_category.eq(group), 'display_shift_percentile'].dropna()
                        ax.scatter(v, i + (k - 0.5) * 0.28 + np.linspace(-0.065, 0.065, len(v)), marker=p.MARKERS[ctx], s=13, edgecolors=p.COLORS[ctx], facecolors=p.COLORS[ctx] if k == 0 else 'white', linewidths=0.7)
                else:
                    d = raw.loc[raw.cell_line.eq(ctx) & raw.display_name.eq(m)].sort_values('target_gene')
                    v = d.signed_cosine.to_numpy()
                    valid = np.isfinite(v)
                    ax.scatter(v[valid], i + np.linspace(-0.18, 0.18, len(v))[valid], s=9, marker=p.MARKERS[ctx], color=p.COLORS[ctx], alpha=0.75)
                    median = p.pick(formal, display_name=m, cell_line=ctx).directional_recovery_median_signed_cosine
                    ax.plot([median] * 2, [i - 0.27, i + 0.27], color=p.INK, lw=1.4)
            ax.set_yticks(range(9), model_labels if j == 0 else [''] * 9)
            ax.set_ylim(8.6, -0.6)
            if letter == 'B':
                ax.set_xlim(-2, 102)
                ax.set_xticks([0, 25, 50, 75, 100])
                ax.set_xlabel('Predicted-shift percentile', labelpad=2)
            else:
                ax.set_xlim(-1.05, 1.05)
                ax.set_xticks([-1, -0.5, 0, 0.5, 1])
                ax.set_xlabel('Signed cosine', labelpad=2)
                p.reference(ax)
    f.legend(handles=[Line2D([], [], marker='o', ls='', color=p.INK, mfc=fill, label=label) for (fill, label) in [(p.INK, 'Endpoint anchors'), ('white', 'Low-information')]], loc='center', bbox_to_anchor=(0.74, 0.597), ncol=2, frameon=False, columnspacing=0.8, handletextpad=0.4)
    save(f, 'S5')
    from . import geometry
    geometry.build(p)
    grid = p.read('M08_cutoff_grid')
    counts = pd.read_csv(p.DATA / 'layout/S7-context-category-counts.tsv', sep='\t')
    rep = 'Replogle K562 essential day 6'
    contexts = p.HCC + [rep]
    cuts = sorted(grid[['low_quantile', 'high_quantile']].drop_duplicates().itertuples(index=False, name=None))
    fixed = cuts.index((0.25, 0.75))
    rows = [(c, m) for m in p.MODELS for c in p.HCC] + [(rep, m) for m in ['Geneformer kernel', 'Geneformer ridge', 'Chargram ridge']]
    values = []
    for (c, m) in rows:
        q = grid.loc[grid.cell_line.eq(c) & grid.display_name.eq(m + ' LOO' if c == rep else m)]
        values.append([p.pick(q, low_quantile=lo, high_quantile=hi).anchor_auc for (lo, hi) in cuts])
    f = page('Cutoff-grid evaluation details', 175)
    gs = f.add_gridspec(2, 1, height_ratios=[5, 1.1], hspace=0.1)
    top = gs[0].subgridspec(1, 3, width_ratios=[1.15, 0.75, 2.7], wspace=0.015)
    model_ax = f.add_subplot(top[0])
    context_ax = f.add_subplot(top[1])
    ax = f.add_subplot(top[2])
    for labels_ax in [model_ax, context_ax]:
        labels_ax.set(xlim=(0, 1), ylim=(20.5, -0.5))
        labels_ax.axis('off')
    for (i, m) in enumerate(model_labels):
        model_ax.text(0, 2 * i + 0.5, m, va='center', fontsize=7.5)
    for (i, m) in enumerate(['Geneformer kernel', 'Geneformer ridge', 'Chargram ridge']):
        model_ax.text(0, 18 + i, m, va='center', fontsize=7.5)
    for (i, (c, m)) in enumerate(rows):
        context_ax.scatter(0.04, i, s=12, color=p.COLORS.get(c, p.INK), marker=p.MARKERS.get(c, 'o'), clip_on=False)
        context_ax.text(0.16, i, 'Replogle' if c == rep else c, va='center', fontsize=7.5)
    for labels_ax in [model_ax, context_ax]:
        labels_ax.axhline(17.5, color=p.GRAY, lw=0.6)
    cmap = LinearSegmentedColormap.from_list('auc_single', ['#f3f5f6', '#667d8d'])
    cmap.set_bad('#eee')
    im = ax.imshow(values, vmin=0, vmax=1, cmap=cmap, aspect='auto')
    ax.set_xticks(range(5), [f'{lo * 100:.0f}/{hi * 100:.0f}' for (lo, hi) in cuts])
    ax.set_yticks([])
    ax.axhline(17.5, color=p.GRAY, lw=0.6)
    for (i, row) in enumerate(values):
        for (j, v) in enumerate(row):
            ax.text(j, i, 'NA' if not np.isfinite(v) else f'{v:.3f}', ha='center', va='center', fontsize=7.5, color=cell_text_color(cmap(v)) if np.isfinite(v) else p.INK)
    ax.add_patch(Rectangle((fixed - 0.5, -0.5), 1, 21, fill=False, ec=p.INK, lw=0.9, clip_on=False))
    ax.text(fixed, 1.012, 'Frozen', transform=ax.get_xaxis_transform(), ha='center', fontsize=7.5)
    head(model_ax, 'A', 'AUC across candidate cutoff pairs')
    ax.set_xlabel('Candidate percentile cutoffs')
    f.colorbar(im, ax=ax, label='AUC', shrink=0.35, pad=0.015)
    bottom = gs[1].subgridspec(1, 2, wspace=0.1)
    for (k, (fields, title)) in enumerate([(['full_endpoint_anchor_n', 'full_low_information_n'], 'Full endpoint cohort'), (['scored_anchor_n', 'scored_low_information_n'], 'Targets used for model scoring')]):
        ax = f.add_subplot(bottom[k])
        ax.set(xlim=(-0.5, 4.5), ylim=(2.5, -0.9))
        ax.set_yticks(range(3), ['HCC1143', 'HCC38', 'Replogle'] if k == 0 else [''] * 3)
        ax.set_xticks(range(5), [f'{lo * 100:.0f}/{hi * 100:.0f}' for (lo, hi) in cuts])
        head(ax, 'B' if k == 0 else '', title)
        for (i, c) in enumerate(contexts):
            for (j, (lo, hi)) in enumerate(cuts):
                r = p.pick(counts, cell_line=c, low_quantile=lo, high_quantile=hi)
                ax.text(j, i, f'{int(r[fields[0]])}/{int(r[fields[1]])}', ha='center', va='center', fontsize=7.5)
        for y in [-0.5, 0.5, 1.5, 2.5]:
            ax.axhline(y, color=p.LINE, lw=0.5)
        for spine in ax.spines.values():
            spine.set_visible(False)
        ax.tick_params(length=0)
        ax.add_patch(Rectangle((fixed - 0.5, -0.5), 1, 3, fill=False, ec=p.INK, lw=0.9))
        ax.text(fixed, -0.7, 'Frozen', ha='center', fontsize=7.5)
        ax.set_xlabel('Candidate percentile cutoffs')
    save(f, 'S7')
    (out / 'single-page-layout.json').write_text(json.dumps({'figures': 7, 'pages_per_figure': 1, 'width_mm': 180, 'height_mm': {'S1': 180, 'S2': 210, 'S3': 220, 'S4': 180, 'S5': 215, 'S6': 230, 'S7': 175}, 'scientific_recomputation': False, 'source_parts_retained': 13, 'font': plt.rcParams['font.family']}, indent=2) + '\n')
