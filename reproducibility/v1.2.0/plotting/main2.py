"""Render frozen display data; no model fitting or statistical inference."""
import hashlib
import json
from pathlib import Path
import platform
import xml.etree.ElementTree as ET
import matplotlib
import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.transforms import Bbox
import numpy as np
import pandas as pd
from scipy import stats
(WIDTH, HEIGHT) = (1320, 1505)
(INK, MUTED, LINE) = ('#24313a', '#61707b', '#dde4ea')
(AXIS, REFERENCE, STRIP) = ('#66737c', '#c3cbd1', '#f4f6f7')
(POINT, INTERVAL) = ('#384650', '#74818b')
(E_RAW, E_ADJUSTED) = ('#858f9a', '#355c7d')
CATEGORIES = [('endpoint_anchor', 'Endpoint anchors', '#e9f4f0', '#3b827a'), ('shift_excess', 'Shift-excess', '#eeeffb', '#73729f'), ('dependency_excess', 'Dependency-excess', '#fbefdd', '#9b5a30'), ('low_information', 'Low-information', '#f0f0f0', '#465261'), ('middle', 'Middle band', '#f9f7ee', '#bdbdbd')]
HCC = ['HCC1143', 'HCC38']
CONTEXT_MARKERS = {'HCC1143': 'o', 'HCC38': 's'}
CONTEXT_COLORS = {'HCC1143': '#73729f', 'HCC38': '#3b827a'}
CONTEXT_CI = {'HCC1143': '#a4a3be', 'HCC38': '#84aaa5'}
ESTIMATORS = ['raw_observed_shift', 'equal_n_expected_shift_depth_20', 'noise_corrected_shift']
CONDITIONAL = ['partial_model_a_log_n', 'partial_model_d_log_n_deg_breadth']
EXTERNAL = [('Replogle K562 essential day 6', 'Replogle K562 essential CRISPRi\nday 6'), ('Replogle K562 genome-wide day 8', 'Replogle K562 genome-wide CRISPRi\nday 8'), ('HepG2 day 7', 'HepG2 day 7'), ('Jurkat day 7', 'Jurkat day 7'), ('K562 TF day 7', 'K562 TF day 7'), ('K562 TF day 13', 'K562 TF day 13')]
RECTS = {'A': (20, 20, 1280, 560), 'B': (20, 600, 595, 430), 'C': (635, 600, 665, 430), 'D': (20, 1050, 520, 435), 'E': (565, 1050, 735, 435)}

def select(frame, **keys):
    mask = pd.Series(True, index=frame.index)
    for (key, value) in keys.items():
        mask &= frame[key].eq(value)
    rows = frame.loc[mask]
    assert len(rows) == 1, keys
    return rows.iloc[0]

class Panel:

    def __init__(self, fig, letter):
        (self.fig, self.letter) = (fig, letter)
        (self.x, self.y, self.w, self.h) = RECTS[letter]
        (self.texts, self.axes) = ([], [])

    def text(self, x, y, label, size=13, ha='left', color=INK, bold=False, rotation=0):
        if self.letter in 'CDE':
            size = max(size, 14)
        artist = self.fig.text((self.x + x) / WIDTH, 1 - (self.y + y) / HEIGHT, label, fontsize=size, color=color, ha=ha, va='center', fontweight='bold' if bold else 'normal', rotation=rotation, linespacing=1.2)
        self.texts.append(artist)
        return artist

    def heading(self, label):
        self.text(0, 21, self.letter, size=19, bold=True)
        self.text(40, 24, label, size=15.5, bold=True)

    def axis(self, x, y, w, h):
        ax = self.fig.add_axes([(self.x + x) / WIDTH, 1 - (self.y + y + h) / HEIGHT, w / WIDTH, h / HEIGHT])
        self.axes.append(ax)
        ax.spines[['top', 'right']].set_visible(False)
        for spine in ax.spines.values():
            spine.set_linewidth(0.8)
            spine.set_color(AXIS)
        ax.tick_params(length=3, width=0.8, colors=AXIS, labelsize=13.8 if self.letter in 'CDE' else 12, pad=3)
        return ax

    def crop(self):
        return Bbox.from_bounds(self.x / 100, (HEIGHT - self.y - self.h) / 100, self.w / 100, self.h / 100)

def forest(ax, row, y, marker='o', filled=True, color=POINT, interval_color=INTERVAL, gid=None):
    (rho, low, high) = (row.spearman_rho, row.bootstrap_ci_low, row.bootstrap_ci_high)
    assert low <= rho <= high
    artist = ax.errorbar(rho, y, xerr=[[rho - low], [high - rho]], fmt=marker, color=color, ecolor=interval_color, markerfacecolor=color if filled else 'white', markeredgewidth=1, markersize=6.5, elinewidth=1.1, capsize=3, linestyle='none', zorder=3)
    if gid is not None:
        artist.lines[0].set_gid(gid)
        artist.lines[2][0].set_gid(gid + '-ci')

def context_label(p, x, y, context, label=None, size=14, color=None):
    color = CONTEXT_COLORS[context] if color is None else color
    key = p.axis(x, y - 9, 16, 18)
    key.set_axis_off()
    key.plot(0.5, 0.5, marker=CONTEXT_MARKERS[context], color=color, markersize=6.5, linestyle='none', transform=key.transAxes)
    p.text(x + 23, y, label or context, size, color=color, bold=True)

def forest_axis(ax, xlim):
    ax.set_xlim(*xlim)
    ax.axvline(0, color=REFERENCE, linewidth=0.8, linestyle=(0, (3, 3)), zorder=0)
    ax.spines['left'].set_visible(False)
    ax.set_yticks([])

def panel_a(p, data):
    p.heading('Sampling-corrected shift–dependency associations')
    for (context, left, role) in zip(HCC, [140, 790], ['primary', 'sensitivity']):
        t = data['target'][data['target'].cell_line.eq(context)]
        row = select(data['inference'], cell_line=context, analysis_id='noise_corrected_shift')
        center = left + 157.5
        context_label(p, center - 173, 57, context, f'{context} day 14 — {role}', 15, color=INK)
        p.text(center, 88, f'n = {len(t)}; Spearman ρ = {row.spearman_rho:.3f}; 95% CI [{row.bootstrap_ci_low:.3f}, {row.bootstrap_ci_high:.3f}]', 12.5, ha='center')
        ax = p.axis(left, 110, 315, 315)
        for q in (25, 75):
            ax.axvline(q, color='#bdbdbd', linewidth=0.9, linestyle=(0, (4, 3)), zorder=0)
            ax.axhline(q, color='#bdbdbd', linewidth=0.9, linestyle=(0, (4, 3)), zorder=0)
        for (key, _, fill, edge) in [CATEGORIES[-1], *CATEGORIES[:-1]]:
            s = t[t.endpoint_category.eq(key)]
            ax.scatter(s.corrected_shift_percentile * 100, s.corrected_dependency_percentile * 100, s=57, marker=CONTEXT_MARKERS[context], facecolor=fill, edgecolor=edge, linewidth=1.2, zorder=3)
        ax.set(xlim=(-2, 102), ylim=(-2, 102), xticks=[0, 25, 50, 75, 100], yticks=[0, 25, 50, 75, 100])
        ax.set_aspect('equal')
        ax.set_xlabel('Sampling-corrected shift percentile', fontsize=13, labelpad=8)
        ax.set_ylabel('CRISPR dependency percentile', fontsize=13, labelpad=8)
    centers = [315, 520, 745, 960, 1155]
    context_label(p, 7, 523, 'HCC1143', size=13.2, color=INK)
    context_label(p, 7, 549, 'HCC38', size=13.2, color=INK)
    table_rule = p.axis(7, 477, 1253, 83)
    table_rule.set_axis_off()
    table_rule.plot([0, 1], [0.94, 0.94], color=LINE, linewidth=0.6, transform=table_rule.transAxes)
    table_rule.plot([0, 1], [0.6, 0.6], color=LINE, linewidth=0.75, transform=table_rule.transAxes)
    for ((key, label, _, edge), x) in zip(CATEGORIES, centers):
        p.text(x, 497, label, 13.2, ha='center', color=MUTED if key == 'middle' else edge)
        for (context, y) in zip(HCC, [523, 549]):
            p.text(x, y, str(int(select(data['counts'], cell_line=context, endpoint_category=key).n_targets)), 13.2, ha='center')

def panel_b(p, data):
    p.heading('Shift–dependency associations\nacross shift estimators')
    context_label(p, 203, 75, 'HCC1143')
    context_label(p, 405, 75, 'HCC38')
    labels = ['Raw shift', 'Equal-n expected shift\n(20 cells/target)', 'Sampling-corrected\nshift']
    for (label, y) in zip(labels, [155, 235, 315]):
        p.text(0, y, label, 13)
    ax = p.axis(245, 115, 285, 240)
    forest_axis(ax, (-0.05, 1.0))
    ax.set(ylim=(2.5, -0.5), xticks=[0, 0.5, 1])
    for (context, offset) in zip(HCC, [-0.18, 0.18]):
        for (i, analysis) in enumerate(ESTIMATORS):
            row = select(data['inference'], cell_line=context, analysis_id=analysis)
            forest(ax, row, i + offset, marker=CONTEXT_MARKERS[context], color=CONTEXT_COLORS[context], interval_color=CONTEXT_CI[context], gid=f'B-{context}-{analysis}')
            ax.text(1.035, i + offset, f'{row.spearman_rho:.3f}', transform=ax.get_yaxis_transform(), ha='left', va='center', fontsize=13.2, color=INK)
    p.text(387.5, 400, 'Spearman ρ (95% CI)', 13, ha='center')

def panel_c(p, data):
    p.heading('Recovered cell count in relation to\nraw shift and dependency')
    p.text(217, 70, 'Raw mean-absolute shift', 14, ha='center', bold=True)
    p.text(525, 70, 'CRISPR dependency probability', 14, ha='center', bold=True)
    for (context, y) in zip(HCC, [108, 270]):
        t = data['target'][data['target'].cell_line.eq(context)]
        row = select(data['count_summary'], context=context)
        strip = p.axis(0, y, 30, 105)
        strip.set_axis_off()
        strip.add_patch(plt.Rectangle((0, 0), 1, 1, transform=strip.transAxes, facecolor=STRIP, edgecolor='none'))
        p.text(15, y + 52.5, context, 14, ha='center', bold=True, rotation=90, color=CONTEXT_COLORS[context])
        for (column, rho_field, x) in [('observed_shift_mean_abs', 'count_shift_rho', 102), ('depmap_gene_dependency', 'count_dependency_rho', 410)]:
            ax = p.axis(x, y, 230, 105)
            points = ax.scatter(np.log(t.n_cells_target), t[column], s=40, color=CONTEXT_COLORS[context], marker=CONTEXT_MARKERS[context], alpha=0.85, linewidths=0, zorder=2)
            points.set_gid(f'C-{context}-{column}')
            ax.set(xlim=(3, 6.3), xticks=[3, 4, 5, 6])
            if column == 'observed_shift_mean_abs':
                ax.set(ylim=(0, 0.026), yticks=[0, 0.01, 0.02], yticklabels=['0', '0.01', '0.02'])
            else:
                ax.set(ylim=(-0.03, 1.04), yticks=[0, 0.5, 1], yticklabels=['0', '0.5', '1'])
            p.text(x + 230, y - 14, f'ρ = {row[rho_field]:.3f}'.replace('-', '−'), 13.2, ha='right')
            if context == 'HCC38':
                ax.set_xlabel('log(cells per target)', fontsize=14, labelpad=7)

def panel_d(p, data):
    p.heading('Raw shift–dependency associations\nafter covariate adjustment')
    for (analysis, heading, start) in [(CONDITIONAL[0], 'Adjusted for log(cells per target)', 116), (CONDITIONAL[1], 'Adjusted for log(cells per target)\n+ response breadth', 288)]:
        p.text(10, start - 35, heading, 13.5, bold=True)
        ax = p.axis(130, start, 310, 84)
        forest_axis(ax, (-0.5, 0.8))
        ax.set(ylim=(1.5, -0.5), xticks=[-0.5, 0, 0.5])
        for (i, context) in enumerate(HCC):
            row = select(data['inference'], cell_line=context, analysis_id=analysis)
            forest(ax, row, i, marker=CONTEXT_MARKERS[context], color=CONTEXT_COLORS[context], interval_color=CONTEXT_CI[context], gid=f'D-{context}-{analysis}')
            p.text(0, start + 21 + i * 42, context, 13, color=CONTEXT_COLORS[context])
            ax.text(1.025, i, f'{row.spearman_rho:.3f}'.replace('-', '−'), transform=ax.get_yaxis_transform(), va='center', ha='left', fontsize=13.2, color=INK)
    p.text(285, 417, 'Partial Spearman ρ (95% CI)', 13, ha='center')

def panel_e(p, data):
    p.heading('Raw and cell-count-adjusted shift–dependency\nassociations across additional contexts')
    key = p.axis(230, 72, 490, 25)
    key.set_axis_off()
    key.plot(0.02, 0.5, 'o', color=E_RAW, markerfacecolor='white', markersize=6.5, transform=key.transAxes)
    key.text(0.06, 0.5, 'Raw', fontsize=12.5, va='center', color=INK, transform=key.transAxes)
    key.plot(0.2, 0.5, 'o', color=E_ADJUSTED, markersize=6.5, transform=key.transAxes)
    key.text(0.24, 0.5, 'Adjusted for log(cells per target)', fontsize=12.5, va='center', color=INK, transform=key.transAxes)
    ax = p.axis(295, 107, 415, 258)
    forest_axis(ax, (-0.5, 1.05))
    ax.set(ylim=(5.5, -0.5), xticks=[-0.5, 0, 0.5, 1])
    for (i, (context, label)) in enumerate(EXTERNAL):
        n = int(select(data['external'], context=context, analysis_id='raw_shift_unadjusted').n_targets)
        p.text(0, 128.5 + 43 * i, f'{label} (n = {n:,})', 12.5)
        raw = select(data['external'], context=context, analysis_id='raw_shift_unadjusted')
        adjusted = select(data['external'], context=context, analysis_id='raw_shift_partial_log_n')
        (connector,) = ax.plot([raw.spearman_rho, adjusted.spearman_rho], [i - 0.13, i + 0.13], color='#cfd6da', linewidth=0.85, zorder=1)
        connector.set_gid(f'paired-estimate-{i}')
        for (analysis, offset, filled) in [('raw_shift_unadjusted', -0.13, False), ('raw_shift_partial_log_n', 0.13, True)]:
            row = select(data['external'], context=context, analysis_id=analysis)
            color = E_ADJUSTED if filled else E_RAW
            forest(ax, row, i + offset, filled=filled, color=color, interval_color=color)
    p.text(502.5, 417, 'Association with CRISPR dependency, ρ (95% CI)', 13, ha='center')
