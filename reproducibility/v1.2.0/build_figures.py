"""Render the current four main and seven supplementary figures from frozen tables."""
import argparse
import hashlib
import json
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager
import pandas as pd

from plotting import main1, main2, main3, main4, supplement, supplement_pages

ROOT = Path(__file__).resolve().parent
DATA = ROOT / 'presentation/final'
INDEX = json.loads((ROOT / 'presentation/workbook_manifest.json').read_text())['sources']

def table(group, name):
    return pd.read_csv(DATA / group / (name + '.tsv'), sep='\t')

def result(name):
    key = 'D' + name[:2]
    return pd.read_csv(ROOT / 'presentation' / INDEX[key]['csv'])

def datasets():
    return {
        2: dict(target=table('main2','endpoint_targets'), counts=table('main2','category_counts'),
                inference=result('08_association_inference.csv'),
                count_summary=table('main2','count_associations'), external=result('16_association_inference.csv')),
        3: dict(formal=table('main3','formal_profiles'), references=table('main3','diagnostic_references'),
                correlations=table('main3','metric_relationships'), seeds=table('main3','training_seeds')),
        4: dict(formal=table('main4','formal_profiles'), cutoff=table('main4','cutoff_comparison'),
                grid=table('main4','cutoff_grid'), seeds=table('main4','feature_seeds'),
                seed_ids=table('main4','feature_seeds').base_model_id.drop_duplicates().tolist()),
    }

def verify_inputs():
    records = json.loads((DATA / 'sources.json').read_text())['files']
    for r in records:
        path = ROOT / r['path']
        assert path.stat().st_size == r['bytes'], r['path']
        assert hashlib.sha256(path.read_bytes()).hexdigest() == r['sha256'], r['path']
    return records

def build(output, font='DejaVu Sans'):
    records = verify_inputs()
    output = Path(output).resolve()
    output.mkdir(parents=True, exist_ok=True)
    font_manager.findfont(font_manager.FontProperties(family=font), fallback_to_default=False)
    plt.rcParams.update({'font.family':font, 'pdf.fonttype':42, 'svg.fonttype':'none',
                         'svg.hashsalt':'wtshiftbench-v1.2.0-final', 'font.size':8,
                         'axes.spines.top':False,'axes.spines.right':False,'savefig.facecolor':'white'})
    outputs=[]
    def save(fig,name):
        name={'M01_construction':'S1','M04_additional_contexts':'S4'}.get(name,name)
        fig.canvas.draw()
        fig.set_layout_engine('none')
        for ext in ('pdf','svg','png'):
            path=output/(name+'.'+ext)
            fig.savefig(path,dpi=180)
            outputs.append({'file':path.name,'bytes':path.stat().st_size,
                            'sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
        plt.close(fig)
        print('Rendered '+name,flush=True)
    fig=plt.figure(figsize=(12,12*main1.HEIGHT/main1.WIDTH))
    for x,y,w,h,draw in [(30,20,1680,690,main1.panel_a),(30,714,760,820,main1.panel_b),(790,714,920,710,main1.panel_c)]:
        draw(main1.axes(fig,x,y,w,h))
    save(fig,'Figure-1')
    for n,data in datasets().items():
        module={2:main2,3:main3,4:main4}[n]
        fig=plt.figure(figsize=(module.WIDTH/100,module.HEIGHT/100))
        for letter in module.RECTS:
            getattr(module,'panel_'+letter.lower())(module.Panel(fig,letter),data)
        save(fig,'Figure-'+str(n))
    supplement.OUT=output
    supplement.DATA=DATA
    supplement.CHECKS=[]
    supplement.read=lambda name:table('supplement',name)
    supplement.result=result
    supplement.save=save
    supplement.construction()
    supplement.additional()
    supplement_pages.build(supplement)
    verify_inputs()
    manifest={'figures':11,'font':font,'matplotlib':matplotlib.__version__,
              'scope':'Current scientific panels from frozen tables; manual typography is not reproduced pixel-for-pixel.',
              'statistical_inference_rerun':False,'inputs':records,'outputs':outputs}
    (output/'plot-verification.json').write_text(json.dumps(manifest,indent=2)+'\n')
    return manifest

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,default=ROOT/'outputs/figures')
    parser.add_argument('--font',default='DejaVu Sans',help='Use Arial if installed locally; font must support Unicode mathematical symbols.')
    args=parser.parse_args()
    build(args.output,args.font)
