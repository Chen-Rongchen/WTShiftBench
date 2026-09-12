"""从归档的target级冻结输入复算M6和25Q3辅助统计，不重新下载或重标端点。"""
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/"src"))
import numpy as np
import pandas as pd
from scipy import stats
from wtbench.revision_metric_validity import bootstrap_spearman_ci
from wtbench.revision_hcc_audit import endpoint_label_permutation_pvalue,bh_qvalues
from wtbench.revision_m6_endpoint_tuning import run_endpoint_tuning


def main():
    out=ROOT/"recomputed/auxiliary"
    out.mkdir(parents=True,exist_ok=True)
    final=ROOT/"reports/revision/finalization_v2"
    run_endpoint_tuning(final/"m4/m6_config.json",output_root=out/"m6")
    for filename in ["model_context_inflation.tsv","cutoff_grid_scores.tsv","inflation_summary.tsv","frozen_score_reproduction.tsv"]:
        a=pd.read_csv(final/"m6"/filename,sep="\t")
        b=pd.read_csv(out/"m6"/filename,sep="\t")
        pd.testing.assert_frame_equal(a,b,check_exact=False,atol=1e-12,rtol=0)
    expected=pd.read_csv(final/"depmap/gene_effect_sensitivity.tsv",sep="\t")
    targets=pd.read_csv(final/"depmap/gene_effect_target_values.tsv.gz",sep="\t")
    cfg=json.loads((ROOT/"configs/revision/amendment_010_formal_release_v2.json").read_text())["gene_effect_sensitivity"]
    rows=[]
    for r in expected.itertuples():
        t=targets[targets.cell_line.eq(r.cell_line)]
        x=t.real_shift_mean_abs.to_numpy(float);y=-t.gene_effect_25q3.to_numpy(float)
        lo,hi=bootstrap_spearman_ci(x,y,replicates=cfg["bootstrap_replicates"],seed=int(r.bootstrap_seed),confidence=cfg["confidence"])
        p=endpoint_label_permutation_pvalue(x,y,permutations=cfg["permutations"],seed=int(r.permutation_seed))
        rows.append(dict(cell_line=r.cell_line,n_targets=len(t),spearman_rho=float(stats.spearmanr(x,y).statistic),
                         bootstrap_ci_low=lo,bootstrap_ci_high=hi,permutation_pvalue_two_sided=p))
        print(f"完成25Q3辅助复算：{r.cell_line}",flush=True)
    actual=pd.DataFrame(rows)
    actual["permutation_qvalue_bh_eight_contexts"]=bh_qvalues(actual.permutation_pvalue_two_sided)
    for col in actual.columns[1:]:
        assert np.allclose(actual[col],expected[col],rtol=0,atol=1e-12,equal_nan=True),col
    actual.to_csv(out/"gene_effect_sensitivity.tsv",sep="\t",index=False)
    report=dict(passed=True,m6_tables=4,gene_effect_contexts=8,
                scope="M6从冻结target级评分重建；GE从归档提取值复算，不代替全官方文件来源核验")
    (out/"verification.json").write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n")
    print(json.dumps(report,ensure_ascii=False),flush=True)


if __name__=="__main__":main()
