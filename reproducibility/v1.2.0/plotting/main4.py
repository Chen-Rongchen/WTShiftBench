"""Render frozen display data; no model fitting or statistical inference."""
import importlib.util
import json
from pathlib import Path
import platform
import matplotlib
import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.transforms import Bbox
import numpy as np
import pandas as pd
from . import main3 as style
select = style.select
(point, whisker, forest_axis, number) = (style.point, style.whisker, style.forest_axis, style.number)
(INK, MUTED, POINT, INTERVAL) = (style.INK, style.MUTED, style.POINT, style.INTERVAL)
(KEYS, CI_PREFIX, SMALL) = (style.KEYS, style.CI_PREFIX, style.SMALL)
(WIDTH, HEIGHT) = (1320, 1290)
REPL = 'Replogle K562 essential day 6'
RECTS = {'A': (20, 20, 1280, 365), 'B': (20, 410, 740, 440), 'C': (790, 410, 510, 440), 'D': (20, 875, 1280, 395)}
NRMSE = 'conventional_normalized_rmse_median'

class Panel(style.Panel):

    def __init__(self, fig, letter):
        (self.fig, self.letter) = (fig, letter)
        (self.x, self.y, self.w, self.h) = RECTS[letter]
        (self.texts, self.axes) = ([], [])

    def text(self, x, y, label, size=SMALL, bold=False, color=INK, ha='left', **kwargs):
        text = self.fig.text((self.x + x) / WIDTH, 1 - (self.y + y) / HEIGHT, label, fontsize=size, fontweight='bold' if bold else 'normal', color=color, ha=ha, va='center', linespacing=1.12, **kwargs)
        self.texts.append(text)
        return text

    def axis(self, x, y, w, h):
        ax = self.fig.add_axes([(self.x + x) / WIDTH, 1 - (self.y + y + h) / HEIGHT, w / WIDTH, h / HEIGHT])
        self.axes.append(ax)
        for spine in ax.spines.values():
            spine.set_color(MUTED)
            spine.set_linewidth(0.7)
        ax.spines[['top', 'right', 'left']].set_visible(False)
        ax.tick_params(length=3, width=0.7, labelsize=SMALL, pad=3, colors=MUTED)
        return ax

    def crop(self):
        return Bbox.from_bounds(self.x / 100, (HEIGHT - self.y - self.h) / 100, self.w / 100, self.h / 100)

def panel_a(p, data):
    p.heading('Independent-context model-output evaluation')
    p.text(0, 56, 'Replogle K562 essential CRISPRi, day 6')
    (starts, widths) = ([205, 410, 610, 810, 1055], [138, 138, 138, 82, 154])
    titles = ['Shift-magnitude\nalignment', 'Endpoint-anchor\nseparation', 'Directional recovery', 'Target-identity\npreservation', 'Target-similarity\ndifference']
    subtitles = ['Spearman ρ', 'AUC', 'Median signed cosine', 'Similarity-matrix\nSpearman ρ', 'Predicted − observed']
    limits = [(-0.5, 1), (-0.04, 1.04), (-0.12, 0.8), (-0.1, 0.5), (-0.15, 1.05)]
    ticks = [[-0.5, 0, 0.5, 1], [0, 0.5, 1], [0, 0.4, 0.8], [0, 0.5], [0, 0.5, 1]]
    for (i, (key, prefix, x, w)) in enumerate(zip(KEYS, CI_PREFIX, starts, widths)):
        center = x + (106 if i == 3 else (w + 35) / 2)
        p.text(center, 110, titles[i], 13.5, bold=True, ha='center')
        p.text(center, 147, subtitles[i], color=MUTED, ha='center')
        if i == 3:
            p.text(955, 180, 'Mantel q', SMALL, ha='center', color=MUTED)
        ax = p.axis(x, 177, w, 150)
        forest_axis(ax, limits[i], (2.5, -0.5), ticks[i], ref=0.5 if i == 1 else 0)
        for (model_i, (_, row)) in enumerate(data['formal'].iterrows()):
            gid = f'A-{row.entrant_id}-{key}'
            if prefix:
                whisker(ax, row[key], row[prefix + '_ci_low'], row[prefix + '_ci_high'], model_i, gid=gid)
            else:
                point(ax, row[key], model_i, gid=gid)
            value = number(row[key])
            if key == KEYS[3]:
                value = f'q={row.target_identity_permutation_qvalue_bh:.3f}'
            ax.text(1.06, model_i, value, transform=ax.get_yaxis_transform(), fontsize=SMALL, va='center', color=INK)
    for (i, (_, row)) in enumerate(data['formal'].iterrows()):
        p.text(0, 202 + i * 50, row.plot_label, 13.5)

def panel_b(p, data):
    p.heading('Reconstruction error vs endpoint-aligned metrics')
    placements = [[(0.68, 0.3), (0.46, 0.88), (0.46, 0.53)], [(0.72, 0.59), (0.46, 0.87), (0.46, 0.17)]]
    for (j, (key, left, ylim, ticks, title)) in enumerate([(KEYS[0], 65, (-0.04, 0.36), [0, 0.15, 0.3], 'Shift-magnitude\nalignment, ρ'), (KEYS[3], 435, (-0.06, 0.12), [-0.05, 0, 0.05, 0.1], 'Target-identity\npreservation, ρ')]):
        p.text(left + 140, 80, title, 14, bold=True, ha='center')
        ax = p.axis(left, 117, 280, 245)
        ax.spines['left'].set_visible(True)
        ax.set(xlim=(0.965, 1.15), ylim=ylim, xticks=[1, 1.1], yticks=ticks)
        for (i, (_, row)) in enumerate(data['formal'].iterrows()):
            point(ax, row[NRMSE], row[key], gid=f'B-{row.entrant_id}-{key}')
            label = row.plot_label.replace(' ', '\n', 1)
            if 'ridge' in row.plot_label:
                label += f'\nnRMSE = {row[NRMSE]:.3f}'
            ax.annotate(label, (row[NRMSE], row[key]), xytext=placements[j][i], textcoords='axes fraction', fontsize=14, ha='center', va='center', color=INK, linespacing=1.08, arrowprops=dict(arrowstyle='-', color=MUTED, lw=0.55))
        ax.set_xlabel('Median nRMSE', fontsize=14, color=INK, labelpad=8)

def panel_c(p, data):
    p.heading('Feature-preparation seed sensitivity')
    for (i, base) in enumerate(data['seed_ids']):
        row = select(data['formal'], entrant_id=base)
        p.text(0, 190 + 110 * i, row.plot_label.replace(' ', '\n', 1), 14)
    for (j, (key, x, title)) in enumerate([(KEYS[0], 150, 'Shift-magnitude\nalignment'), (KEYS[3], 345, 'Target-identity\npreservation')]):
        p.text(x + 75, 108, title, 14, ha='center', bold=True)
        ax = p.axis(x, 135, 150, 220)
        ax.set(xlim=(0.18, 0.33) if j == 0 else (-0.04, 0.115), ylim=(1.5, -0.5), xticks=[0.2, 0.25, 0.3] if j == 0 else [0, 0.05, 0.1], yticks=[])
        if j == 1:
            ax.axvline(0, color=MUTED, lw=0.6, ls='--', zorder=0)
        for (i, base) in enumerate(data['seed_ids']):
            rows = data['seeds'].loc[data['seeds'].base_model_id.eq(base)]
            for ((_, row), offset) in zip(rows.iterrows(), [-0.18, 0, 0.18]):
                point(ax, row[key], i + offset, size=4.5, gid=f'C-{base}-seed{int(row.feature_seed)}-{key}')
        p.text(x + 75, 400, 'Spearman ρ', ha='center')

def cutoff_rows(data):
    rows = []
    for context in style.HCC:
        for (i, model) in enumerate(style.MODELS):
            row = select(data['cutoff'], cell_line=context, display_name=model)
            rows.append((row, i, style.CONTEXT_COLORS[context], style.MARKERS[context]))
    for (i, (_, model)) in enumerate(data['formal'].iterrows()):
        row = select(data['cutoff'], cell_line=REPL, entrant_id=model.entrant_id)
        rows.append((row, i, POINT, 'o'))
    return rows

def panel_d(p, data):
    p.heading('AUC increase under post hoc cutoff selection')
    for (column, context) in enumerate([*style.HCC, REPL]):
        left = 0 if column < 2 else 800
        axis_left = [180, 480, 1000][column]
        color = style.CONTEXT_COLORS.get(context, POINT)
        p.text(axis_left + 125 if column < 2 else left, 64, context if context in style.HCC else 'Replogle K562 essential CRISPRi\nday 6', 14, bold=True, color=color, ha='center' if column < 2 else 'left')
        ax = p.axis(axis_left, 100, 250, 240)
        forest_axis(ax, (-0.008, 0.3), (8.5, -0.5), [0, 0.1, 0.2, 0.3])
        if context in style.HCC:
            rows = [select(data['cutoff'], cell_line=context, display_name=m) for m in style.MODELS]
        else:
            rows = [select(data['cutoff'], cell_line=context, entrant_id=r.entrant_id) for r in data['formal'].itertuples()]
        for (i, row) in enumerate(rows):
            if column != 1:
                p.text(left, 100 + (i + 0.5) * 240 / 9, style.display_name(row.display_name.removesuffix(' LOO')), 14)
            point(ax, row.apparent_auc_inflation, i, color=color, marker=style.MARKERS.get(context, 'o'), gid=f'D-{context}-{row.entrant_id}')
    p.text(640, 382, 'ΔAUC = selected − frozen 25/75', 14, ha='center')
