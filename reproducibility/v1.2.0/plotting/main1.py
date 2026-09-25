"""Render frozen display data; no model fitting or statistical inference."""
import csv
import hashlib
import json
from pathlib import Path
import re
import xml.etree.ElementTree as ET
import matplotlib
import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch, Rectangle
(WIDTH, HEIGHT) = (1740, 1542)
PT = 864 / WIDTH
PALETTE = {'ink': '#24313a', 'body': '#40515e', 'muted': '#61707b', 'arrow': '#7a8792', 'line': '#dde4ea', 'purple_bg': '#f6f3fb', 'purple_edge': '#c9c0df', 'purple': '#7469aa', 'purple_inner': '#d8d0e9', 'teal_bg': '#eef8f5', 'teal_edge': '#9ecbc3', 'teal': '#2f8f83', 'teal_inner': '#b7d9d3', 'anchor_bg': '#e9f4f0', 'anchor': '#3b827a', 'shift_bg': '#eeeffb', 'shift': '#73729f', 'dependency_bg': '#fbefdd', 'dependency': '#9b5a30', 'low_bg': '#f0f0f0', 'low': '#465261', 'middle_bg': '#f9f7ee', 'black': '#111111', 'threshold': '#555555'}

def text(ax, x, y, value, size=25, color='ink', bold=False, ha='left', va='center', rotation=0):
    return ax.text(x, y, value, fontsize=(max(size, 25) if ax.get_label() == 'A' else size) * PT, color=PALETTE[color], fontweight='bold' if bold else 'normal', ha=ha, va=va, rotation=rotation, linespacing=1.28)

def box(ax, x, y, w, h, fill='white', edge='line', radius=14, lw=1.6):
    patch = FancyBboxPatch((x, y), w, h, boxstyle=f'round,pad=0,rounding_size={radius}', facecolor=PALETTE.get(fill, fill), edgecolor=PALETTE.get(edge, edge), linewidth=lw * PT)
    ax.add_patch(patch)

def line(ax, points, color='arrow', lw=2):
    ax.plot(*zip(*points), color=PALETTE[color], linewidth=lw * PT)

def arrow(ax, start, end):
    ax.add_patch(FancyArrowPatch(start, end, arrowstyle='-|>', mutation_scale=27 * PT, linewidth=3 * PT, color=PALETTE['arrow'], shrinkA=0, shrinkB=0))

def matrix_icon(ax, x, y):
    colors = ['#8277b8', '#aea6d2', '#d8d2eb', '#958bc4', '#c5bddf', '#7b72b0', '#c9c0df', '#8d83be', '#b8b0da', '#e1dcef', '#7b72b0', '#a59ccd']
    box(ax, x - 8, y - 8, 170, 66, '#f8f6fc', '#e0d9ee', radius=10)
    for (i, color) in enumerate(colors):
        ax.add_patch(Rectangle((x + i % 6 * 27, y + i // 6 * 27), 23, 23, facecolor=color, edgecolor='none'))

def endpoint_icon(ax):
    (x, y, w, h) = (855, 235, 255, 190)
    for q in (0.25, 0.75):
        ax.plot([x + q * w] * 2, [y, y + h], color=PALETTE['teal_edge'], linewidth=1.5 * PT, linestyle=(0, (6 * PT, 5 * PT)))
        ax.plot([x, x + w], [y + (1 - q) * h] * 2, color=PALETTE['teal_edge'], linewidth=1.5 * PT, linestyle=(0, (6 * PT, 5 * PT)))
    line(ax, [(x, y), (x, y + h), (x + w, y + h)], 'body', 2)
    points = [(12, 18), (23, 35), (38, 22), (45, 55), (55, 43), (65, 72), (83, 66), (87, 88), (18, 78), (78, 13)]
    ax.scatter([x + u / 100 * w for (u, _) in points], [y + (1 - v / 100) * h for (_, v) in points], s=(10 * PT) ** 2, color=PALETTE['teal'], linewidths=0, zorder=3)
    text(ax, x + w / 2, y + h + 62, 'Sampling-corrected\nshift percentile', 25, ha='center')
    text(ax, x - 59, y + h / 2, 'Dependency\npercentile', 25, ha='center', rotation=90)

def panel_a(ax):
    ax.set_label('A')
    text(ax, 0, 20, 'A', 37, bold=True)
    box(ax, 45, 64, 590, 600, 'purple_bg', 'purple_edge', radius=26, lw=2.4)
    box(ax, 720, 64, 915, 600, 'teal_bg', 'teal_edge', radius=26, lw=2.4)
    text(ax, 80, 109, 'Expression-based evaluation', 29, 'purple', True)
    text(ax, 755, 109, 'Endpoint-aligned evaluation', 29, 'teal', True)
    box(ax, 80, 190, 235, 245, edge='purple_inner')
    text(ax, 197.5, 238, 'Predicted and\nobserved expression\nprofiles', 23, ha='center')
    matrix_icon(ax, 117.5, 320)
    text(ax, 197.5, 408, 'cells × genes', 23, 'purple', ha='center')
    arrow(ax, (325, 330), (353, 330))
    box(ax, 365, 240, 240, 190, edge='purple_inner')
    text(ax, 485, 267, 'Typical readouts', 25, 'purple', True, ha='center')
    line(ax, [(387, 291), (583, 291)], 'line', 1.4)
    text(ax, 485, 325, 'Reconstruction error', 24, ha='center')
    text(ax, 485, 384, 'Profile similarity /\nDE overlap', 24, ha='center')
    box(ax, 80, 559, 525, 78, edge='purple_inner')
    text(ax, 105, 582, 'Evaluates', 21, 'purple', True)
    text(ax, 105, 614, 'Expression fidelity', 26, bold=True)
    box(ax, 755, 144, 395, 380, edge='teal_inner')
    text(ax, 952.5, 181, 'Observed endpoint object', 25, 'teal', True, ha='center')
    line(ax, [(780, 209), (1125, 209)], 'line', 1.4)
    endpoint_icon(ax)
    arrow(ax, (1162, 320), (1235, 320))
    box(ax, 1245, 190, 355, 245, edge='teal_inner')
    text(ax, 1265, 219, 'Before model scoring', 23, 'teal', True)
    line(ax, [(1265, 243), (1578, 243)], 'line', 1.4)
    text(ax, 1265, 273, 'Assess the shift–dependency\nassociation', 23)
    text(ax, 1265, 363, 'Define eligible targets,\nendpoint categories\nand metrics', 23)
    arrow(ax, (1422.5, 435), (1422.5, 450))
    box(ax, 1245, 457, 355, 77, edge='teal_inner')
    text(ax, 1422.5, 495, 'Model-output\nevaluation', 25, 'teal', True, ha='center')
    arrow(ax, (1422.5, 534), (1422.5, 552))
    box(ax, 755, 559, 845, 78, edge='teal_inner')
    text(ax, 780, 582, 'Evaluates', 21, 'teal', True)
    text(ax, 780, 614, 'Preservation of endpoint-associated structure', 26, bold=True)

def panel_b(ax):
    text(ax, 0, 23, 'B', 37, bold=True)
    text(ax, 55, 42, 'Endpoint categories fixed\nbefore model scoring', 28, bold=True)
    (x, y, side) = (125, 130, 540)
    (low, high) = (0.25, 0.75)
    ax.add_patch(Rectangle((x, y), side, side, facecolor=PALETTE['middle_bg'], edgecolor='none'))
    corners = [(0, 0, 'dependency_bg', 'Dependency-\nexcess', 'dependency'), (high, 0, 'anchor_bg', 'Endpoint\nanchors', 'anchor'), (0, high, 'low_bg', 'Low-\ninformation', 'low'), (high, high, 'shift_bg', 'Shift-\nexcess', 'shift')]
    for (px, py, fill, label, color) in corners:
        ax.add_patch(Rectangle((x + px * side, y + py * side), low * side, low * side, facecolor=PALETTE[fill], edgecolor='none'))
        text(ax, x + (px + low / 2) * side, y + (py + low / 2) * side, label, 21, color, True, ha='center')
    for q in (low, high):
        ax.plot([x + q * side] * 2, [y, y + side], color=PALETTE['threshold'], linewidth=1.5 * PT, linestyle=(0, (6 * PT, 5 * PT)))
        ax.plot([x, x + side], [y + q * side] * 2, color=PALETTE['threshold'], linewidth=1.5 * PT, linestyle=(0, (6 * PT, 5 * PT)))
    ax.add_patch(Rectangle((x, y), side, side, facecolor='none', edgecolor=PALETTE['black'], linewidth=1.6 * PT))
    text(ax, x + side / 2, y + side / 2 - 17, 'Middle band', 27, 'black', True, ha='center')
    text(ax, x + side / 2, y + side / 2 + 22, 'All remaining targets', 23, 'black', ha='center')
    for v in (0, 25, 75, 100):
        (tx, ty) = (x + v / 100 * side, y + (1 - v / 100) * side)
        line(ax, [(tx, y + side), (tx, y + side + 7)], 'black', 1.4)
        line(ax, [(x - 7, ty), (x, ty)], 'black', 1.4)
        text(ax, tx, y + side + 27, str(v), 21, 'black', ha='center')
        text(ax, x - 17, ty, str(v), 21, 'black', ha='right')
    text(ax, x + side / 2, y + side + 68, 'Sampling-corrected shift percentile', 26, 'black', ha='center')
    text(ax, 40, y + side / 2, 'CRISPR dependency percentile', 26, 'black', ha='center', rotation=90)

def panel_c(ax):
    text(ax, 0, 23, 'C', 37, bold=True)
    text(ax, 55, 27, 'Datasets and analysis roles', 28, bold=True)
    text(ax, 55, 130, 'Context', 24, 'body')
    text(ax, 390, 130, 'HCC1143/HCC38\naudit', 22, 'anchor', True, ha='center').set_linespacing(1.1)
    text(ax, 585, 130, 'Independent\nmodel-output audit', 22, 'shift', True, ha='center').set_linespacing(1.1)
    text(ax, 790, 130, 'Additional endpoint-\nassociation analyses', 22, 'dependency', True, ha='center').set_linespacing(1.1)
    line(ax, [(45, 170), (908, 170)], 'black', 1.8)
    rows = [('HCC1143 — day 14', 390, 'Primary', 'ink'), ('HCC38 — day 14', 390, 'Sensitivity', 'ink'), ('Replogle K562 essential\nCRISPRi — day 6', 585, None, 'shift'), ('HepG2 — day 7', 790, None, 'dependency'), ('Jurkat — day 7', 790, None, 'dependency'), ('K562 TF — day 7', 790, None, 'dependency'), ('K562 TF — day 13', 790, None, 'dependency'), ('Replogle K562 genome-wide\nCRISPRi — day 8', 790, None, 'dependency')]
    for (i, (label, col, role, color)) in enumerate(rows):
        y = 209 + 64 * i
        text(ax, 55, y, label, 23)
        if role is not None:
            text(ax, col, y, role, 23, color, ha='center')
        else:
            ax.scatter([col], [y], s=(21 * PT) ** 2, color=PALETTE[color], edgecolor=PALETTE['black'], linewidth=0.8 * PT, zorder=3)
        line(ax, [(45, y + 32), (908, y + 32)], 'line', 1.1)

def axes(fig, x, y, w, h):
    ax = fig.add_axes([x / WIDTH, 1 - (y + h) / HEIGHT, w / WIDTH, h / HEIGHT])
    ax.set(xlim=(0, w), ylim=(h, 0))
    ax.set_axis_off()
    return ax
