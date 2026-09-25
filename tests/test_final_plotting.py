"""Check scientific objects and rendered coordinates, not only file hashes."""
import importlib.util
from pathlib import Path
import sys
import re
import xml.etree.ElementTree as ET

import numpy as np
import pytest
import matplotlib.pyplot as plt

ROOT=Path(__file__).resolve().parents[1]/'reproducibility/v1.2.0'
sys.path.insert(0,str(ROOT))
SPEC=importlib.util.spec_from_file_location('final_plot_entry',ROOT/'build_figures.py')
ENTRY=importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(ENTRY)

def test_frozen_plot_inputs():
    assert len(ENTRY.verify_inputs())==33
    for n,d in ENTRY.datasets().items():
        if n in (3,4):
            assert d['formal'].display_name.str.strip().ne('').all()
    assert len(ENTRY.datasets()[3]['formal'])==18
    assert len(ENTRY.datasets()[4]['formal'])==3

def test_figure4_all_54_points_use_raw_precision():
    m=ENTRY.main4;data=ENTRY.datasets()[4]
    f=plt.figure(figsize=(m.WIDTH/100,m.HEIGHT/100))
    for letter in 'ABCD':getattr(m,'panel_'+letter.lower())(m.Panel(f,letter),data)
    lines={line.get_gid():line for ax in f.axes for line in ax.lines if line.get_gid()}
    expected={}
    for r in data['formal'].itertuples():
        for key in m.KEYS:expected[f'A-{r.entrant_id}-{key}']=(getattr(r,key),None)
        for key in [m.KEYS[0],m.KEYS[3]]:
            expected[f'B-{r.entrant_id}-{key}']=(getattr(r,m.NRMSE),getattr(r,key))
    for r in data['seeds'].itertuples():
        for key in [m.KEYS[0],m.KEYS[3]]:
            expected[f'C-{r.base_model_id}-seed{int(r.feature_seed)}-{key}']=(getattr(r,key),None)
    for r in data['cutoff'].itertuples():
        expected[f'D-{r.cell_line}-{r.entrant_id}']=(r.apparent_auc_inflation,None)
    assert len(expected)==54 and set(lines)==set(expected)
    for gid,(x,y) in expected.items():
        np.testing.assert_allclose(lines[gid].get_xdata(),[x],rtol=0,atol=1e-14)
        if y is not None:np.testing.assert_allclose(lines[gid].get_ydata(),[y],rtol=0,atol=1e-14)
    assert sum(r.apparent_auc_inflation==0 for r in data['cutoff'].itertuples())==7
    plt.close(f)

@pytest.fixture(scope='module')
def supplements(tmp_path_factory):
    p=ENTRY.supplement
    p.OUT=tmp_path_factory.mktemp('plot-check');p.DATA=ENTRY.DATA;p.CHECKS=[]
    p.read=lambda n:ENTRY.table('supplement',n)
    p.result=ENTRY.result
    figures={}
    p.save=lambda f,n:figures.__setitem__(n,f)
    p.additional()
    from plotting import geometry
    geometry.build(p)
    yield figures
    for f in figures.values():plt.close(f)

def test_s4_same_probability_mapping(supplements):
    f=supplements['M04_additional_contexts'];f.canvas.draw()
    distances=[]
    assert len(f.axes)==6
    for ax in f.axes:
        np.testing.assert_allclose(ax.get_ylim(),[-.03,1.22])
        np.testing.assert_allclose(ax.get_yticks(),np.arange(0,1.01,.2))
        distances.append(ax.transData.transform((0,.2))[1]-ax.transData.transform((0,0))[1])
    np.testing.assert_allclose(distances,distances[0],atol=1e-8)

def test_s6_context_split_and_ecdf(supplements):
    f=supplements['S6'];g=ENTRY.table('supplement','M07_geometry')
    pairs=ENTRY.table('supplement','M07_pairwise_cosines')
    p=ENTRY.supplement;count=0;labels=[];curves=0
    for ax in f.axes:
        for points in ax.collections:
            gid=points.get_gid()
            if gid and gid.startswith('A-'):
                _,ctx,key=gid.removesuffix('-data').split('-',2)
                rows=g.loc[g.context.eq(ctx)&g.model.isin(p.MODELS)]
                np.testing.assert_allclose(points.get_offsets(),rows[['excess_target_similarity',key]],atol=1e-14)
                count+=len(rows)
        labels.extend(t for t in ax.texts if (t.get_gid() or '').startswith('A-label-'))
        for line in ax.lines:
            gid=line.get_gid()
            if gid and gid.startswith('B-'):
                _,ctx,source=re.split('-(HCC1143|HCC38)-',gid)
                x=np.sort(pairs.loc[pairs.context.eq(ctx)&pairs.model.eq(source),'cosine'])
                np.testing.assert_array_equal(line.get_xdata(),x)
                np.testing.assert_array_equal(line.get_ydata(),np.arange(1,1082)/1081)
                curves+=1
    assert count==54 and len(labels)==54 and curves==40
    assert sum(t.get_text().startswith('Target-similarity difference') for t in f.texts)==1

def test_cutoff_completeness_and_rules():
    d=ENTRY.table('supplement','M08_cutoff_grid')
    assert len(d)==105 and d.estimable.sum()==78 and d.anchor_auc.isna().sum()==27
    assert d[['cell_line','entrant_id']].drop_duplicates().shape[0]==21
    assert ((d.scored_anchor_n>=2)&(d.scored_low_information_n>=2)).equals(d.estimable)
    assert len(d.loc[d.low_quantile.eq(.25)&d.high_quantile.eq(.75)])==21

def test_figure3_seeds_and_triangle():
    d=ENTRY.datasets()[3]
    assert len(d['correlations'])==50
    assert d['seeds'].groupby(['display_name','cell_line']).training_seed.nunique().tolist()==[3,3,5,5,3,3,3,3]
    m=ENTRY.main3;f=plt.figure(figsize=(m.WIDTH/100,m.HEIGHT/100))
    m.panel_c(m.Panel(f,'C'),d)
    numbers=[t for ax in f.axes for t in ax.texts if (t.get_gid() or '').startswith('C-number')]
    assert len(numbers)==30
    plt.close(f)
