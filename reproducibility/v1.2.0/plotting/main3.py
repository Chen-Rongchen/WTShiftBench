"""Render frozen display data; no model fitting or statistical inference."""
import hashlib
import json
from pathlib import Path
import platform
import xml.etree.ElementTree as ET
import matplotlib
import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.transforms import Bbox
import numpy as np
import pandas as pd
from scipy import stats
(WIDTH, HEIGHT) = (1320, 1880)
(INK, MUTED, LINE) = ('#24313a', '#61707b', '#dde4ea')
(POINT, INTERVAL, REFERENCE) = ('#384650', '#74818b', '#c3cbd1')
HCC = ['HCC1143', 'HCC38']
MARKERS = {'HCC1143': 'o', 'HCC38': 's'}
CONTEXT_COLORS = {'HCC1143': '#73729f', 'HCC38': '#3b827a'}
CONTEXT_CI = {'HCC1143': '#a4a3be', 'HCC38': '#84aaa5'}
CORRELATION_COLORS = ['#879aaf', '#f7f7f7', '#b98c86']
SMALL = 13.2
MODELS = ['Geneformer kernel', 'Geneformer ridge', 'Linear low-rank', 'scGPT kernel', 'scGPT ridge', 'CPA', 'CellOT', 'GEARS', 'scGen']
SEED_MODELS = [m for m in MODELS if m in {'CPA', 'CellOT', 'GEARS', 'scGen'}]
KEYS = ['endpoint_alignment_spearman', 'anchor_separation_auc', 'directional_recovery_median_signed_cosine', 'target_identity_spearman', 'excess_homogenization_uncentered']
CI_PREFIX = ['endpoint_alignment', 'anchor_separation', 'directional_recovery', None, 'excess_homogenization_uncentered']
SHORT = ['Align.', 'Anchor sep.', 'Direction', 'Identity', 'Similarity Δ']
REFERENCES = ['observed_shift_oracle', 'negated_oracle', 'observed_magnitude_random_direction', 'shared_mean_baseline']
REF_LABELS = ['Observed-shift\noracle', 'Negated oracle', 'Magnitude-only\n(randomized direction)', 'Shared-mean\nreference']
RECTS = {'A': (20, 20, 1280, 690), 'B': (20, 735, 560, 510), 'C': (600, 735, 700, 510), 'D': (20, 1270, 640, 590), 'E': (690, 1270, 610, 590)}
A_BASES = np.array([0, 2.5, 5, 7.5, 10, 14, 16.5, 19, 21.5])
B_ROWS = np.array([[17, 45], [85, 113], [181, 245], [300, 328]])
D_CONTEXT_ROWS = {'HCC1143': 10, 'HCC38': 31}
D_STATE_OFFSETS = {'uncentered': -4, 'centered': 4}

def display_name(value):
    return 'Chargram low-rank' if value == 'Linear low-rank' else value

def select(frame, **keys):
    rows = frame
    for (key, value) in keys.items():
        rows = rows.loc[rows[key].eq(value)]
    assert len(rows) == 1, keys
    return rows.iloc[0]

class Panel:

    def __init__(self, fig, letter):
        (self.fig, self.letter) = (fig, letter)
        (self.x, self.y, self.w, self.h) = RECTS[letter]
        self.sy = self.h / {'A': 690, 'B': 540, 'C': 540, 'D': 620, 'E': 620}[letter]
        (self.texts, self.axes) = ([], [])

    def text(self, x, y, label, size=13, bold=False, color=INK, ha='left', **kwargs):
        text = self.fig.text((self.x + x) / WIDTH, 1 - (self.y + (y * self.sy if y >= 60 else y)) / HEIGHT, label, fontsize=size, fontweight='bold' if bold else 'normal', color=color, ha=ha, va='center', linespacing=1.12, **kwargs)
        self.texts.append(text)
        return text

    def heading(self, title):
        self.text(0, 21, self.letter, 19, bold=True)
        self.text(36, 23, title, 15.5, bold=True)

    def axis(self, x, y, w, h):
        ax = self.fig.add_axes([(self.x + x) / WIDTH, 1 - (self.y + (y + h) * self.sy) / HEIGHT, w / WIDTH, h * self.sy / HEIGHT])
        self.axes.append(ax)
        for spine in ax.spines.values():
            spine.set_color(MUTED)
            spine.set_linewidth(0.7)
        ax.spines[['top', 'right', 'left']].set_visible(False)
        ax.tick_params(length=3, width=0.7, labelsize=SMALL, pad=3, colors=MUTED)
        return ax

    def rule(self, x, y, w):
        ax = self.axis(x, y, w, 1)
        ax.set_axis_off()
        ax.plot([0, 1], [0.5, 0.5], color='#d1dae2', linewidth=0.8, transform=ax.transAxes)

    def crop(self):
        return Bbox.from_bounds(self.x / 100, (HEIGHT - self.y - self.h) / 100, self.w / 100, self.h / 100)

def number(value, digits=2):
    if abs(value) < 0.5 * 10 ** (-digits):
        value = 0
    return f'{value:.{digits}f}'.replace('-', '−')

def forest_axis(ax, xlim, ylim, ticks, ref=0):
    ax.set(xlim=xlim, ylim=ylim, xticks=ticks, yticks=[])
    ax.axvline(ref, color=REFERENCE, linewidth=0.8, linestyle=(0, (3, 3)), zorder=0)

def point(ax, value, y, marker='o', filled=True, color=POINT, size=5.5, gid=None):
    (artist,) = ax.plot([value], [y], marker=marker, markersize=size, markerfacecolor=color if filled else 'white', markeredgecolor=color, markeredgewidth=0.9, linestyle='none', zorder=3)
    artist.set_gid(gid)
    return artist

def whisker(ax, value, low, high, y, marker='o', filled=True, color=POINT, interval_color=INTERVAL, gid=None):
    assert low <= value <= high
    limits = ax.get_xlim()
    assert limits[0] <= low and high <= limits[1], (gid, low, high, limits)
    interval = ax.errorbar(value, y, xerr=[[value - low], [high - value]], fmt='none', ecolor=interval_color, elinewidth=0.95, capsize=2.3, zorder=2)
    interval.lines[2][0].set_gid(f'{gid}-ci')
    return point(ax, value, y, marker, filled, color, gid=gid)

def context_label(p, x, y, context, label=None, size=14):
    ax = p.axis(x, y - 9, 16, 18)
    ax.set_axis_off()
    ax.plot(0.5, 0.5, marker=MARKERS[context], color=CONTEXT_COLORS[context], markersize=5.5, linestyle='none', transform=ax.transAxes)
    p.text(x + 23, y, label or context, size, bold=True, color=CONTEXT_COLORS[context])

def context_key(p, y, roles=False):
    context_label(p, 0, y, 'HCC1143', 'HCC1143 — primary' if roles else None)
    context_label(p, 330 if roles else 195, y, 'HCC38', 'HCC38 — sensitivity' if roles else None)

def panel_a(p, data):
    p.heading('Model-output profiles in HCC1143 and HCC38')
    context_key(p, 60, roles=True)
    starts = [205, 410, 610, 810, 1055]
    widths = [178, 178, 178, 82, 205]
    heads = ['Shift-magnitude\nalignment', 'Endpoint-anchor\nseparation', 'Directional recovery', 'Target-identity\npreservation', 'Target-similarity\ndifference']
    notes = ['Spearman ρ', 'AUC', 'Median signed cosine', 'Similarity-matrix\nSpearman ρ', 'Predicted − observed']
    limits = [(-0.5, 1), (-0.04, 1.04), (-0.12, 0.8), (-0.1, 0.5), (-0.15, 1.05)]
    ticks = [[-0.5, 0, 0.5, 1], [0, 0.5, 1], [0, 0.4, 0.8], [0, 0.5], [0, 0.5, 1]]
    p.text(0, 166, 'Response-LOO', SMALL, color=MUTED)
    p.rule(0, 435, 1260)
    p.text(0, 457, 'Same-context fit', SMALL, color=MUTED)
    for (base, model) in zip(A_BASES, MODELS):
        p.text(0, 190 + 20 * (base + 1), display_name(model), 13.5)
    for (j, (key, prefix, x, w)) in enumerate(zip(KEYS, CI_PREFIX, starts, widths)):
        center = x + (106 if j == 3 else w / 2)
        p.text(center, 100, heads[j], 13.5, ha='center', bold=True)
        p.text(center, 142, notes[j], SMALL, ha='center', color=MUTED)
        if j == 3:
            p.text(1046, 174, 'Mantel q', SMALL, ha='right', color=MUTED)
        ax = p.axis(x, 190, w, 470)
        forest_axis(ax, limits[j], (23, -0.5), ticks[j], ref=0.5 if j == 1 else 0)
        for (base, model) in zip(A_BASES, MODELS):
            for (offset, context) in enumerate(HCC):
                row = select(data['formal'], cell_line=context, display_name=model)
                y = base + offset
                gid = f'A-{context}-{row.entrant_id}-{key}'
                if prefix:
                    whisker(ax, row[key], row[prefix + '_ci_low'], row[prefix + '_ci_high'], y, marker=MARKERS[context], color=CONTEXT_COLORS[context], interval_color=CONTEXT_CI[context], gid=gid)
                else:
                    point(ax, row[key], y, marker=MARKERS[context], color=CONTEXT_COLORS[context], gid=gid)
                if j == 3:
                    q = row.target_identity_permutation_qvalue_bh
                    q_text = p.text(1046, 190 + 20 * (y + 0.5), 'q<0.001' if q < 0.001 else f'q={q:.3f}', SMALL, ha='right')
                    q_text.set_gid(f'A-number-{context}-{row.entrant_id}-{key}-mantel-q')

def panel_b(p, data):
    p.heading('Diagnostic reference predictions')
    context_key(p, 75)
    starts = [185, 280, 375, 470]
    limits = [(-0.1, 1.1), (-0.1, 1.1), (-1.15, 1.15), (-0.2, 1.15)]
    ticks = [[0, 1], [0, 1], [-1, 0, 1], [0, 1]]
    for (x, label) in zip(starts, ['Alignment', 'AUC', 'Direction', 'Identity']):
        p.text(x + 37.5, 112, label, SMALL, ha='center', bold=True)
    for (ys, label) in zip(B_ROWS, REF_LABELS):
        p.text(0, 140 + ys.mean(), label, 13.5)
    for (j, (key, x)) in enumerate(zip(KEYS[:4], starts)):
        ax = p.axis(x, 140, 75, 345)
        forest_axis(ax, limits[j], (345, 0), ticks[j], ref=0.5 if j == 1 else 0)
        for (i, reference) in enumerate(REFERENCES):
            for (context_i, context) in enumerate(HCC):
                y = B_ROWS[i, context_i]
                rows = data['references'].loc[data['references'].cell_line.eq(context) & data['references'].reference_type.eq(reference)].sort_values('reference_seed')
                offsets = np.linspace(-25, 25, 10) if len(rows) == 10 else [0]
                for ((_, row), offset) in zip(rows.iterrows(), offsets):
                    if pd.isna(row[key]):
                        p.text(x + 37.5, 140 + y, 'NA', SMALL, ha='center', color='#89939b')
                    else:
                        point(ax, row[key], y + offset, marker=MARKERS[context], color=CONTEXT_COLORS[context], size=2.5 if len(rows) == 10 else 5.5, gid=f'B-{context}-{row.entrant_id}-{key}')

def panel_c(p, data):
    p.heading('Metric correlations across model outputs')
    cmap = LinearSegmentedColormap.from_list('muted_relationships', CORRELATION_COLORS)
    for (context, x) in zip(HCC, [110, 420]):
        context_label(p, x + 67, 65, context)
        p.text(x + 135, 92, 'n = 9 evaluated model outputs', SMALL, ha='center', color=MUTED)
        source = data['correlations'].loc[data['correlations'].cell_line.eq(context)]
        array = source.pivot(index='i', columns='j', values='spearman_rho').to_numpy()
        ax = p.axis(x, 113, 270, 270)
        displayed = np.ma.array(array, mask=np.triu(np.ones((5, 5), dtype=bool), k=1))
        im = ax.pcolormesh(np.arange(6) - 0.5, np.arange(6) - 0.5, displayed, vmin=-1, vmax=1, cmap=cmap, shading='flat', rasterized=False, edgecolors='white', linewidth=0.4)
        im.set_gid(f'C-{context}-correlations')
        ax.set(xlim=(-0.5, 4.5), ylim=(4.5, -0.5), xticks=np.arange(5), yticks=np.arange(5))
        ax.set_aspect('equal')
        ax.set_xticklabels(SHORT, rotation=90, ha='center', fontsize=SMALL)
        ax.set_yticklabels(SHORT if context == HCC[0] else [''] * 5, fontsize=SMALL)
        ax.tick_params(length=0)
        ax.spines[:].set_visible(False)
        for i in range(5):
            for j in range(i + 1):
                value = array[i, j]
                label = number(value)
                text = ax.text(j, i, label, ha='center', va='center', fontsize=SMALL, color=INK)
                text.set_gid(f'C-number-{context}-{i}-{j}')
    bar_ax = p.axis(170, 500, 470, 11)
    cb = p.fig.colorbar(im, cax=bar_ax, orientation='horizontal', ticks=[-1, 0, 1])
    cb.solids.set_rasterized(False)
    cb.solids.set_edgecolor('face')
    cb.outline.set_visible(False)
    bar_ax.tick_params(labelsize=SMALL, length=2)
    p.text(0, 506, 'Spearman ρ', SMALL)

def panel_d(p, data):
    p.heading('Target-similarity differences')
    key = p.axis(194, 42, 422, 24)
    key.set_axis_off()
    for (left, filled, label) in [(0, False, 'Uncentered'), (0.49, True, 'Target-centered')]:
        for (offset, context) in zip([0.015, 0.06], HCC):
            key.plot(left + offset, 0.5, marker=MARKERS[context], markersize=5.5, markerfacecolor=CONTEXT_COLORS[context] if filled else 'white', markeredgecolor=CONTEXT_COLORS[context], linestyle='none', transform=key.transAxes)
        key.text(left + 0.105, 0.5, label, fontsize=SMALL, color=INK, va='center', transform=key.transAxes)
    for (context, y) in zip(HCC, [86, 109]):
        context_label(p, 0, y, context)
    p.text(250.3, 110, 'No difference', SMALL, ha='center', color='#89939b')
    ax = p.axis(194, 125, 422, 438)
    forest_axis(ax, (-0.16, 1.04), (438, 0), [0, 0.5, 1])
    for (i, model) in enumerate(MODELS):
        p.text(0, 145.5 + 48 * i, display_name(model), 13.5)
        for context in HCC:
            row = select(data['formal'], cell_line=context, display_name=model)
            center = 48 * i + D_CONTEXT_ROWS[context]
            values = [row[f'excess_homogenization_{c}'] for c in ['uncentered', 'centered']]
            ax.plot(values, [center - 4, center + 4], color=REFERENCE, linewidth=0.8, zorder=1)
            for (c, offset) in D_STATE_OFFSETS.items():
                k = f'excess_homogenization_{c}'
                whisker(ax, row[k], row[k + '_ci_low'], row[k + '_ci_high'], center + offset, marker=MARKERS[context], filled=c == 'centered', color=CONTEXT_COLORS[context], interval_color=CONTEXT_CI[context], gid=f'D-{context}-{row.entrant_id}-{c}')
    p.text(406, 600, 'Target-similarity difference (predicted − observed)', SMALL, ha='center')

def panel_e(p, data):
    p.heading('Model-output variation across training seeds')
    context_key(p, 55)
    starts = [175, 410]
    for (x, label) in zip(starts, ['Shift-magnitude\nalignment', 'Directional recovery\n(median signed cosine)']):
        p.text(x + 93.5, 88, label, 13.5, ha='center', bold=True)
    for (i, model) in enumerate(SEED_MODELS):
        label = p.text(0, 176 + i * 105, model, SMALL)
        label.set_gid(f'E-model-{model}')
    for (j, (key, x)) in enumerate(zip([KEYS[0], KEYS[2]], starts)):
        ax = p.axis(x, 125, 187, 420)
        forest_axis(ax, (-0.5, 0.85) if j == 0 else (-0.04, 0.7), (480, 0), [-0.5, 0, 0.5] if j == 0 else [0, 0.3, 0.6])
        for (i, model) in enumerate(SEED_MODELS):
            for (context_i, context) in enumerate(HCC):
                rows = data['seeds'].loc[data['seeds'].cell_line.eq(context) & data['seeds'].display_name.eq(model)].sort_values('training_seed')
                for ((_, row), offset) in zip(rows.iterrows(), np.linspace(-17, 17, len(rows))):
                    y = 30 + 120 * i + 55 * context_i + offset
                    point(ax, row[key], y, marker=MARKERS[context], size=5, color=CONTEXT_COLORS[context], gid=f'E-{context}-{model}-seed{int(row.training_seed)}-{key}')
    p.text(starts[0] + 93.5, 584, 'Spearman ρ', SMALL, ha='center')
    p.text(starts[1] + 93.5, 584, 'Signed cosine', SMALL, ha='center')
