"""Plot only public frozen source tables using extracted delivered functions, without private Word files."""
from pathlib import Path
import argparse, csv, hashlib, json, shutil, textwrap
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.patches import FancyBboxPatch
ROOT = Path(__file__).resolve().parent
OUT = ROOT / "outputs/figures"
COLORS = {"HCC38": "#B65E31", "HCC1143": "#008A70"}
SOURCES = {}
CAPTIONS = {}
INDEX = json.loads((ROOT / "presentation/workbook_manifest.json").read_text())["sources"]

def data(n):
    record = INDEX[f"D{n:02d}"]
    path = ROOT / "presentation" / record["csv"]
    SOURCES[f"D{n:02d}"] = record
    return pd.read_csv(path)

METRICS=["endpoint_alignment_spearman","directional_recovery_median_signed_cosine","anchor_separation_auc","target_identity_spearman","excess_homogenization_uncentered"]
MLABEL=["Endpoint ρ ↑","Signed cosine ↑","Anchor AUC ↑","Identity ρ ↑","Excess H: warning"]
def setup():
    for sub in ["Figures", "Results", "Source", "Preview"]:
        (OUT/sub).mkdir(parents=True, exist_ok=True)
    plt.rcParams.update({"font.family": "Liberation Sans", "font.size": 9,
                         "axes.titlesize": 10, "axes.labelsize": 9, "xtick.labelsize": 8,
                         "ytick.labelsize": 8, "pdf.fonttype": 42, "svg.fonttype": "none",
                         "axes.spines.top": False, "axes.spines.right": False,
                         "savefig.facecolor": "white"})

def save(fig, name, caption, alt, sources, pdf=None):
    fig.suptitle(name.replace("_", " "), fontsize=13, fontweight="bold")
    for extension in ["pdf", "svg", "png"]:
        fig.savefig(OUT/"Figures"/f"{name}.{extension}", dpi=360, bbox_inches="tight", pad_inches=.15)
        if extension=="svg":
            svg=OUT/"Figures"/f"{name}.svg"
            svg.write_text("\n".join(line.rstrip() for line in svg.read_text().splitlines())+"\n")
    if pdf is not None:
        pdf.savefig(fig, bbox_inches="tight", pad_inches=.15)
    CAPTIONS[name] = {"caption": caption, "alt_text": alt, "sources": sources}
    plt.close(fig)

def heading(ax, letter, title):
    ax.set_title(f"{letter}  {title}", loc="left", fontweight="bold", pad=12)

def forest(ax, df, value, low, high, labels, color="#2876A6", reference=0):
    y = np.arange(len(df))
    v = df[value].to_numpy(float)
    if low is not None:
        # Plot frozen interval endpoints directly; do not label existing intervals as new inference.
        for i, (_, r) in enumerate(df.iterrows()):
            ax.plot([r[low], r[high]], [i, i], color=color, lw=1.4)
    ax.scatter(v, y, s=24, color=color, zorder=3)
    ax.axvline(reference, color=".65", lw=.7, ls="--")
    ax.set_yticks(y, labels)
    ax.invert_yaxis()
    ax.grid(axis="x", alpha=.12)

def heat(ax, values, rows, columns, lo=-1, hi=1, cmap="RdBu_r", precision=2):
    values = np.asarray(values, float)
    palette = plt.get_cmap(cmap).copy()
    palette.set_bad("#E8E8E8")
    im = ax.imshow(np.ma.masked_invalid(values), cmap=palette, vmin=lo, vmax=hi, aspect="auto")
    ax.set_xticks(range(len(columns)), columns, rotation=35, ha="right")
    ax.set_yticks(range(len(rows)), rows)
    for (i,j), val in np.ndenumerate(values):
        label = f"{val:.{precision}f}" if np.isfinite(val) else "NA"
        rgba=palette((val-lo)/(hi-lo)) if np.isfinite(val) else (1,1,1,1)
        dark = .2126*rgba[0]+.7152*rgba[1]+.0722*rgba[2] < .48
        ax.text(j, i, label, ha="center", va="center", fontsize=8, color="white" if dark else "#222222")
    return im

def box(ax, x, y, w, h, text, color):
    ax.add_patch(FancyBboxPatch((x,y), w,h, boxstyle="round,pad=.015", facecolor=color,
                               edgecolor="#B8C5CC", lw=1))
    ax.text(x+w/2,y+h/2,text,ha="center",va="center",fontsize=10,linespacing=1.55)

def figure1():
    fig, ax = plt.subplots(figsize=(10,7.5), layout="constrained")
    ax.set(xlim=(0,1),ylim=(0,1)); ax.axis("off")
    steps = [
        ("A   QUALIFY THE OBSERVED OBJECT\nCounts + guide calls + same-context controls\nExact DepMap probability match; ≥20 cells/target\nRaw shift → matched-size control-null correction", "#EAF3F8"),
        ("B   FREEZE THE EVALUATION OBJECT\nDeclare the amplitude estimator and endpoint\nFix eligible targets, category rules and metrics\nVersion-lock the definition before model scoring", "#E8F4F0"),
        ("C   ALIGN OUTPUTS ON DECLARED AXES\nHCC: 47 targets × 47 response genes\n5 response-LOO + 4 in-sample implementations\nReplogle: 1,882 targets × 1,024 genes; 3 response-LOO", "#F4F0E8"),
        ("D   AUDIT DISTINCT PROPERTIES\nDependency ordering • signed direction • anchor AUC\nTarget identity • observed-relative homogenization\nReport uncertainty and NA; no composite ranking", "#F0ECF7")]
    for i,(txt,col) in enumerate(steps):
        y=.77-i*.245
        box(ax,.07,y,.86,.19,txt,col)
        if i<3:
            ax.annotate("",xy=(.5,y-.05),xytext=(.5,y-.01),arrowprops={"arrowstyle":"->","lw":1.5})
    save(fig,"Fig_1","A–D, Four operations from qualification to output auditing. The HCC construction matrix contains 36,601 expression-feature rows, whereas its common model response panel contains 47 genes. For the worked example, A003 was frozen on 4 September 2026 after benchmark development and before uniform revised scoring, not before all data or historical-output inspection. It retains negative corrected amplitudes, applies 25/75 categories to the complete 47/48-target cohorts, and treats HCC1143 as qualified primary and HCC38 as a boundary context. Arrows denote workflow, not causal effects.",
         "Four steps connect sampling-aware qualification, frozen categories, declared output axes and separate measures of model capability.",["D18","D20","D27","D32","D36"])

def figure2():
    t, inf, pair = data(28), data(8), data(9)
    fig = plt.figure(figsize=(11,12),layout="constrained")
    grid=fig.add_gridspec(4,3,height_ratios=[1,1,1.35,1])
    for i,c in enumerate(["HCC38","HCC1143"]):
        q=t[t.cell_line==c]
        for j,(x,y,xlab,ylab) in enumerate([
            ("n_cells_target","observed_shift_mean_abs","Recovered cells (log scale)","Raw mean-absolute shift"),
            ("n_cells_target","depmap_gene_dependency","Recovered cells (log scale)","Dependency probability"),
            ("depmap_gene_dependency","observed_shift_mean_abs","Dependency probability","Raw mean-absolute shift")]):
            ax=fig.add_subplot(grid[i,j]); ax.scatter(q[x],q[y],s=17,c=COLORS[c],alpha=.8)
            if x=="n_cells_target": ax.set_xscale("log")
            rho=(pair[(pair.cell_line==c)&(pair.covariate=="n_cells_target")&(pair.outcome==y)].spearman_rho.iloc[0]
                 if j<2 else inf[(inf.cell_line==c)&(inf.analysis_id=="raw_observed_shift")].spearman_rho.iloc[0])
            heading(ax,chr(65+i*3+j),f"{c}  |  n={len(q)},  ρ={rho:.3f}")
            ax.set(xlabel=xlab,ylabel=ylab)
    analyses=["raw_observed_shift","noise_corrected_shift","equal_n_expected_shift_depth_20","partial_model_a_log_n","partial_model_d_log_n_deg_breadth"]
    # Analysis names come from frozen tables; aliases affect display only, not statistic definitions.
    labels=["Raw","Corrected","Mean equal-n=20","Raw | count","Raw | count + breadth"]
    ax=fig.add_subplot(grid[2,:2]); heading(ax,"G","Different questions, not a sequence of adjustments")
    for c,offset in [("HCC38",-.12),("HCC1143",.12)]:
        q=inf[inf.cell_line==c].set_index("analysis_id").loc[analyses]
        for k,(_,r) in enumerate(q.iterrows()):
            ax.plot([r.bootstrap_ci_low,r.bootstrap_ci_high],[k+offset]*2,color=COLORS[c],lw=1.5)
            ax.scatter(r.spearman_rho,k+offset,color=COLORS[c],s=25,label=c if k==0 else None)
    ax.set_yticks(range(5),labels); ax.invert_yaxis(); ax.axvline(0,c=".6",lw=.7,ls="--")
    ax.set(xlim=(-.45,1),xlabel="Spearman / partial Spearman ρ (target-bootstrap 95% CI)"); ax.legend(frameon=False,loc="lower right")
    ax=fig.add_subplot(grid[2,2]); heading(ax,"H","Fixed ≥100-cell cohorts")
    for c in COLORS:
        q=data(11).query("cell_line == @c")
        ax.plot(q.depth,q.rho_median,"o-",color=COLORS[c],label=f"{c} (n={int(q.n_targets.iloc[0])})")
        ax.fill_between(q.depth,q.rho_q025,q.rho_q975,color=COLORS[c],alpha=.13)
    ax.set(xlabel="Cells sampled per target",ylabel="Replicate bridge ρ",xticks=[20,50,100]); ax.legend(frameon=False,fontsize=8)
    groups=data(25)
    for j,(m,lab) in enumerate([("raw_shift","Mean raw shift"),("depmap_gene_dependency","Mean dependency")]):
        ax=fig.add_subplot(grid[3,j]); heading(ax,chr(73+j),"Depth 100: excluded vs retained")
        q=groups[(groups.depth==100)&(groups.metric==m)&groups.context.isin(COLORS)]
        for k,c in enumerate(COLORS):
            r=q[q.context==c].iloc[0]
            ax.plot([0,1],[r.excluded_mean,r.retained_mean],"o-",color=COLORS[c],label=f"{c}: {int(r.n_excluded)}/{int(r.n_retained)}")
        ax.set(xticks=[0,1],xticklabels=["Excluded","Retained"],xlim=(-.25,1.25),ylabel=lab); ax.legend(frameon=False,fontsize=7)
    ax=fig.add_subplot(grid[3,2]); heading(ax,"K","Complete corrected categories")
    q=data(23).pivot(index="cell_line",columns="endpoint_category",values="n_targets").loc[list(COLORS)]
    fields=["endpoint_anchor","shift_excess","dependency_excess","low_information","middle"]
    heat(ax,q[fields],q.index,["Anchor","Shift excess","Dependency excess","Low","Middle"],0,48,"Blues",0)
    save(fig,"Fig_2","A–F, Target-level count, raw amplitude and dependency with frozen pairwise correlations. G, Point estimates and target-bootstrap 95% CIs; joint conditional results use raw amplitude and a threshold-defined breadth proxy. H, Same ≥100-cell targets sampled at varying depth; shaded bands are 2.5th–97.5th replicate percentiles, not target-bootstrap CIs. I,J, Depth-100 group means (legend: excluded/retained counts). K, Full A003 category counts before model intersection. Negative corrected values are retained.",
         "Sampling correction retains positive association, joint raw count-and-breadth adjustment is inconclusive, and higher coverage thresholds remove a nonrandom target group.",["D08","D09","D11","D23","D25","D28"])

def figure3():
    m=data(1); formal=m[m.entrant_role=="formal"]
    fig=plt.figure(figsize=(11,14.5),layout="constrained"); gs=fig.add_gridspec(4,2,height_ratios=[1.6,1,1,.8])
    for j,c in enumerate(["HCC1143","HCC38"]):
        q=formal[formal.cell_line==c].copy()
        q["fit"]=q.model_family.isin(["scGen","CPA","GEARS","CellOT"])
        q=q.sort_values(["fit","display_name"])
        ax=fig.add_subplot(gs[0,j]); heading(ax,chr(65+j),f"{c}: common 47 × 47 panel")
        vals=q[METRICS].to_numpy(float)
        # First four columns share a [-1,1] scale; mark the AUC baseline at 0.5 and use warning colors for H.
        heat(ax,vals[:,:4],q.display_name+q.fit.map({True:" [Fit]",False:" [LOO]"}),MLABEL[:4],-1,1)
        ax.axhline(4.5,c="black",lw=1.3)
        ax.text(.5,1.01,"Raw values; AUC reference = 0.5; others = 0",transform=ax.transAxes,ha="center",fontsize=8)
    for j,c in enumerate(["HCC1143","HCC38"]):
        q=m[(m.cell_line==c)&((m.entrant_role=="formal")|(m.entrant_id=="shared_mean_baseline"))]
        ax=fig.add_subplot(gs[1,j]); heading(ax,chr(67+j),f"{c}: direction and shared-mean reference")
        forest(ax,q,"directional_recovery_median_signed_cosine","directional_recovery_ci_low","directional_recovery_ci_high",q.display_name,color=COLORS[c])
        ax.set(xlim=(-.25,1),xlabel="Median signed cosine (95% target-bootstrap CI)")
        ax=fig.add_subplot(gs[2,j]); heading(ax,chr(69+j),f"{c}: observed-relative homogenization")
        y=np.arange(len(q))
        ax.scatter(q.excess_homogenization_uncentered,y,c="#B45728",s=24,label="Uncentered excess")
        ax.scatter(q.excess_homogenization_centered,y,facecolors="none",edgecolors="#315C89",s=28,label="Centered excess")
        for form,color in [("uncentered","#B45728"),("centered","#315C89")]:
            ax.hlines(y,q[f"excess_homogenization_{form}_ci_low"],q[f"excess_homogenization_{form}_ci_high"],color=color,lw=1)
        ax.set_yticks(y,q.display_name);ax.invert_yaxis();ax.axvline(0,c=".6",lw=.7,ls="--")
        ax.set(xlabel="Predicted H − observed H (warning, not reward)",xlim=(-.3,1.05))
        ax.legend(frameon=False,fontsize=7,loc="upper center",bbox_to_anchor=(.5,-.23),ncol=2)
        ax.text(.99,1.01,f"Observed H = {q.observed_homogenization_uncentered.iloc[0]:.3f}; centered shared mean = NA",transform=ax.transAxes,ha="right",fontsize=7)
    seeds=data(38)
    for j,c in enumerate(["HCC1143","HCC38"]):
        q=seeds[seeds.cell_line.eq(c)].sort_values("training_seed")
        ax=fig.add_subplot(gs[3,j]);heading(ax,chr(71+j),f"{c}: CellOT training-seed sensitivity")
        labels=q.training_seed.map(lambda s:f"Seed {int(s)}"+(" (formal)" if s==123 else ""))
        forest(ax,q,"endpoint_alignment_spearman","endpoint_alignment_ci_low","endpoint_alignment_ci_high",labels,color=COLORS[c])
        ax.set(xlim=(-.75,.9),xlabel="Endpoint ρ (target-bootstrap 95% CI per seed)")
    save(fig,"Fig_3","A,B, Nine formal HCC implementations per context, grouped by response-LOO and in-sample fitting, not ranked. CellOT uses seed 123. Cells print raw values; the common correlation/cosine range is −1 to 1, with AUC reference 0.5. C,D, Direction with target-bootstrap 95% CIs and shared mean. E,F, Uncentered and separately centered predicted-minus-observed H with paired target-delete-one jackknife 95% intervals. Positive excess is a warning. G,H, All five CellOT training seeds, including the sequentially registered extension to 126/127 after the first three results were known. Endpoint ordering changes across seeds, so the positive seed-123 result is not a seed-stable model capability. All CIs condition on each saved output, not across seeds. Identity uses Mantel P/q without CI; centered shared-mean zero vectors remain NA. Full values are in Tables 3a,b/S1 and D01/D38/D43/D44.",
         "Mixed-setting HCC outputs have different properties. Across five CellOT seeds, dependency ordering is positive for 123 and HCC38 seed126 but otherwise negative, alongside weak direction and unsupported positive identity correspondence.",["D01","D32","D38","D43","D44"])

def figure4():
    m=data(2)
    m["display_name"]=m.display_name.replace({"shared_mean_baseline":"Shared-mean reference","observed_shift_oracle":"Observed oracle","negated_oracle":"Negated oracle","observed_magnitude_random_direction":"L2 magnitude / random direction"}).str.replace(" LOO","",regex=False)
    q=m[(m.entrant_role=="formal")|(m.entrant_id=="shared_mean_baseline")]
    fig,axes=plt.subplots(2,3,figsize=(12,8.5),layout="constrained")
    for ax,field,low,high,title,ref in [
        (axes[0,0],"conventional_normalized_rmse_median","conventional_normalized_rmse_ci_low","conventional_normalized_rmse_ci_high","Reconstruction nRMSE ↓",1),
        (axes[0,1],"endpoint_alignment_spearman","endpoint_alignment_ci_low","endpoint_alignment_ci_high","Dependency ordering ρ ↑",0),
        (axes[0,2],"target_identity_spearman",None,None,"Identity ρ (no CI)",0)]:
        forest(ax,q,field,low,high,q.display_name,reference=ref)
        heading(ax,chr(65+list(axes[0]).index(ax)),title)
        if field=="endpoint_alignment_spearman": ax.set_xlim(-.1,.4)
    ax=axes[1,0]; heading(ax,"D","Controls reveal score meaning")
    refs=m[m.entrant_role!="formal"]
    heat(ax,refs[METRICS[:4]],refs.display_name,["Endpoint ρ","Direction","AUC","Identity"],-1,1,precision=3)
    ax=axes[1,1]; heading(ax,"E","Homogenization: same-space reference")
    heat(ax,q[["predicted_homogenization_uncentered","observed_homogenization_uncentered","excess_homogenization_centered"]],q.display_name,["Predicted H","Observed H","Centered excess"],-1,1,precision=3)
    ax=axes[1,2]; heading(ax,"F","Post-hoc cutoff selection")
    d=data(4); q=d[d.cell_line.str.contains("Replogle",case=False)]
    for k,(_,r) in enumerate(q.iterrows()):
        ax.plot([0,1],[r.frozen_anchor_auc,r.tuned_anchor_auc],"o-",label=r.display_name)
        ax.annotate(f"+{r.apparent_auc_inflation:.3f}",(1,r.tuned_anchor_auc),xytext=(5,0),textcoords="offset points",fontsize=8)
    ax.set(xticks=[0,1],xticklabels=["Frozen 25/75","Selected cutoff"],xlim=(-.15,1.4),ylabel="Anchor AUC (changing category membership)")
    ax.legend(frameon=False,fontsize=7,loc="upper left",bbox_to_anchor=(-.05,-.16))
    save(fig,"Fig_4","A–C, Three Replogle response-LOO implementations and the observed-data shared-mean diagnostic on the same 1,882 targets × 1,024 genes. A,B show existing target-bootstrap 95% CIs; C has no CI and Table 3c supplies target-label Mantel q. These describe individual-output uncertainty, not between-model tests. Shared-mean endpoint and identity are undefined, not zero. D, Oracle, negated, random-direction magnitude-only and shared-mean controls. E, Observed and predicted homogenization, with separately centered excess. F, Apparent AUC changes after selecting among five cutoff pairs; categories change, so this is not performance improvement on the same fixed task. The 1,024-gene oracle amplitude correlation is distinct from corrected context qualification.",
         "Similar ridge reconstruction summaries coexist with different dependency ordering; negated and random-direction controls show that endpoint scores alone do not demonstrate response recovery.",["D02","D04"])

def supplementary(pdf):
    fig,ax=plt.subplots(1,2,figsize=(11,9),layout="constrained")
    d=data(18)
    for j,c in enumerate(COLORS):
        q=d[d.cell_line==c].set_index("stage")
        ax[j].set(xlim=(0,1),ylim=(0,1));ax[j].axis("off");heading(ax[j],chr(65+j),f"{c}: recorded attrition")
        stages=[("matrix_barcodes","Input matrix cells"),("barcodes_with_protospacer_call","Cells with guide calls"),("single_feature_cells","Single-feature cells"),
                ("assayed_noncontrol_targets","Recovered noncontrol targets"),("targets_passing_minimum_cells","Targets with ≥20 cells"),("targets_with_depmap_gene_column","Resolvable DepMap columns"),("targets_with_exact_model_endpoint","Nonmissing exact-model endpoint")]
        for k,(stage,label) in enumerate(stages):
            r=q.loc[stage];y=.87-k*.123
            excluded="" if pd.isna(r.n_excluded_from_parent) or k==0 else f"\nExcluded: {int(r.n_excluded_from_parent):,}"
            box(ax[j],.05,y,.90,.084,f"{label}: {int(r.n_retained):,}"+excluded,"#EEF5F8")
            if k<len(stages)-1:
                ax[j].annotate("",xy=(.5,y-.025),xytext=(.5,y-.005),arrowprops={"arrowstyle":"->","lw":1})
        ctrl=q.loc["single_feature_controls","n_retained"];pert=q.loc["single_feature_perturbed","n_retained"]
        final=q.loc["final_truth_object_perturbed_cells","n_retained"]
        ax[j].text(.5,.02,f"Single-feature split: {int(ctrl):,} controls + {int(pert):,} perturbation cells\nFinal retained perturbation cells: {int(final):,}\nSame construction space: 36,601 GEX rows; 10 duplicate symbols retained",ha="center",va="bottom",fontsize=8)
    save(fig,"Fig_S1","A,B, All recorded cell and target attrition stages. Counts are not a single linear chain: pooled control and perturbation subsets branch from single-feature calls. Exact parent-stage links and rules are retained in workbook D18; identifier handling and preprocessing are in D19–D20. Corrected categories are in Table S3/D23, and all target eligibility records in D22.","Complete HCC cell and target counts document construction of the 47- and 48-target endpoint objects.",["D18","D19","D20","D22","D23"],pdf)
    fig,axs=plt.subplots(2,2,figsize=(12,9.5),layout="constrained"); r=data(14); inf=data(8)
    for j,c in enumerate(COLORS):
        ax=axs[0,j];q=r[(r.cell_line==c)&(r.evidence_type=="shift_metric_definition")]
        altlabels=q.analysis.map({"alternative_real_DEG_burden":"Threshold-defined breadth proxy","alternative_real_shift_L2":"L2 amplitude","alternative_real_shift_top100_mean":"Top-100 mean amplitude","alternative_real_shift_top20_mean":"Top-20 mean amplitude","alternative_real_shift_top50_mean":"Top-50 mean amplitude","raw_observed_shift":"Raw mean-absolute amplitude"})
        forest(ax,q,"estimate",None,None,altlabels,color=COLORS[c])
        heading(ax,chr(65+j),f"{c}: alternative raw summaries");ax.set(xlabel="Spearman ρ",xlim=(0,1))
        ax=axs[1,j];q=inf[(inf.cell_line==c)&inf.analysis_id.str.startswith("partial_")]
        labels=q.analysis_id.map({"partial_model_a_log_n":"Count","partial_model_b_log_n_library":"Count + library complexity","partial_model_c_log_n_expression_efficiency":"Count + baseline + RNA proxy","partial_model_d_log_n_deg_breadth":"Count + breadth proxy"})
        forest(ax,q,"spearman_rho","bootstrap_ci_low","bootstrap_ci_high",labels,color=COLORS[c])
        heading(ax,chr(67+j),f"{c}: conditional analyses");ax.set(xlabel="Partial ρ (95% target-bootstrap CI)",xlim=(-.6,1))
    save(fig,"Fig_S2","A,B, Alternative response-amplitude summaries from frozen robustness results (points, without invented intervals). C,D, Available partial-rank sensitivities, with target-bootstrap intervals and Freedman–Lane inference in D08. Breadth is a threshold-defined response proxy, not FDR-defined DEG burden. Full control-cell subsampling and historical raw-anchor influence estimates and interval types are supplied in D14; equal-depth and fixed-cohort distributions are in D10–D12/Fig. 2. These are distinct tests, not successive corrections of the same quantity.","Alternative amplitude summaries and small covariate models reveal robustness and attenuation without conflating sampling correction and conditional information.",["D08","D10","D11","D12","D14"],pdf)
    fig,axs=plt.subplots(4,1,figsize=(10,14),layout="constrained",gridspec_kw={"height_ratios":[1.5,1.2,1,1.5]})
    q=data(29); labels=q.context+q.raw_n_targets.map(lambda n:f" (n={n})")
    forest(axs[0],q,"raw_spearman_rho","raw_bootstrap_ci_low","raw_bootstrap_ci_high",labels)
    heading(axs[0],"A","Legacy raw contexts (original target-bootstrap intervals)")
    axs[0].set(xlabel="Raw Spearman ρ",xlim=(-1,1))
    q=data(16);q=q[(q.adjusted==True)&(~q.context.isin(COLORS))&(q.outcome=="raw_shift")]
    forest(axs[1],q,"spearman_rho","bootstrap_ci_low","bootstrap_ci_high",q.context+q.n_targets.map(lambda n:f" (n={n})"))
    heading(axs[1],"B","External raw shift conditional on cell count only")
    axs[1].set(xlabel="Partial Spearman ρ",xlim=(-1,1))
    axs[2].axis("off");heading(axs[2],"C","A006: corrected qualification in frozen candidate order")
    q=data(30);lines=[]
    for _,r in q.iterrows():
        label=(f"QUALIFIED: ρ={r.corrected_spearman_rho:.3f}, 95% CI [{r.bootstrap_ci_low:.3f}, {r.bootstrap_ci_high:.3f}], n={int(r.n_eligible_targets)}" if r.status=="evaluated" else "NOT ASSESSED: selection stopped after first qualified context")
        lines.append(f"{int(r.candidate_rank)}. {r.context}\n    {label}")
    axs[2].text(0,.9,"\n\n".join(lines),va="top",fontsize=10,transform=axs[2].transAxes)
    q=data(41)
    registry=json.loads((ROOT/"configs/revision/revision_m5_candidate_qualification_v1.json").read_text())
    context_names={Path(r["bridge_table"]).parent.name:r["context"] for r in registry["candidate_order"]}
    labels=q.cell_line.map(lambda name:context_names.get(name,name))+q.n_targets.map(lambda n:f" (n={n})")
    forest(axs[3],q,"spearman_rho","bootstrap_ci_low","bootstrap_ci_high",labels)
    heading(axs[3],"D","Sensitivity: unified Public 25Q3 gene effect")
    axs[3].set(xlabel="Raw amplitude versus negative gene effect: ρ (95% CI)",xlim=(-.3,1))
    save(fig,"Fig_S3","A, Eight historical raw associations with original intervals; retrospective pass/fail accounting and permutation P are in Table S2/D29. B, Available external raw count-only partial associations; these are not count-plus-breadth tests and retain existing cohort filters. C, A006 corrected qualification assesses the first candidate and stops, so HepG2/Jurkat are unassessed rather than rejected. D, All gene-effect sensitivities use Public 25Q3 CRISPRGeneEffect.csv on the existing probability-eligible cohorts (5,000 target bootstraps, 10,000 permutations; eight-context BH family). Historical HepG2/Jurkat columns instead match 23Q4; the release comparison is retained in D42. Full statistics are in D16/D30/D41.","Legacy raw, count-adjusted, corrected qualification and unified gene-effect sensitivities are distinguished; unassessed candidates are not mislabeled failures.",["D16","D29","D30","D41","D42"],pdf)
    CAPTIONS["Fig_S3"]["context_display_mapping"]=context_names
    CAPTIONS["Fig_S3"]["caption"] += " The legacy source ID K562_essential_day7 denotes Replogle K562 essential day 6 in the candidate registry; only its display label is standardized."
    fig,axs=plt.subplots(1,2,figsize=(12,10),layout="constrained")
    q=data(35);labels=q.cell_line+": "+q.entrant_id.str.replace("_hcc_sens_"," ",regex=False).str.replace("_"," ")
    forest(axs[0],q,"endpoint_alignment_spearman",None,None,labels)
    heading(axs[0],"A","24 finite-budget outputs: point estimates only")
    axs[0].set(xlabel="Endpoint ρ",xlim=(-.25,1))
    q=data(5)
    # Retain original cutoff fields and all prespecified candidates; do not filter to favorable results.
    key=q.cell_line+": "+q.entrant_id
    col=q.low_quantile.map(lambda x:f"{int(round(x*100))}/{100-int(round(x*100))}")
    wide=q.assign(row=key,cutoff=col).pivot(index="row",columns="cutoff",values="anchor_auc")
    wide=wide[["10/90","15/85","20/80","25/75","30/70"]]
    heat(axs[1],wide,wide.index.str.replace("_"," "),wide.columns,0,1,"Blues")
    heading(axs[1],"B","Full cutoff grid: AUC (NA retained)")
    save(fig,"Fig_S4","A, All 24 finite-budget HCC sensitivities, without using single-bootstrap placeholder columns as confidence intervals. B, All 21 formal model-context outputs across the predefined five-cutoff grid. Raw AUC values are displayed; class counts and non-estimable cells remain in D05. Formal configurations are not replaced by the largest value. This grid changes category membership and is not a common fixed-task improvement experiment.","All limited-budget outputs and cutoff choices are shown, not only selected maxima, with undefined values kept as NA.",["D05","D35"],pdf)
    fig,axs=plt.subplots(1,2,figsize=(13,6),layout="constrained")
    q=data(34)
    names={**dict(zip(METRICS,MLABEL)),"conventional_pearson_median":"Pearson","conventional_normalized_rmse_median":"nRMSE",
           "negative_excess_homogenization_uncentered":"− excess H","negative_conventional_normalized_rmse_median":"− nRMSE"}
    for j,c in enumerate(COLORS):
        z=q[q.scope==c];keys=list(dict.fromkeys(z.metric_x.tolist()+z.metric_y.tolist()));a=np.full((len(keys),len(keys)),np.nan)
        for _,r in z.iterrows():
            x,y=keys.index(r.metric_x),keys.index(r.metric_y);a[x,y]=a[y,x]=r.spearman_rho
        im=heat(axs[j],a,[names.get(k,k) for k in keys],[names.get(k,k) for k in keys])
        heading(axs[j],chr(65+j),f"{c}: nine formal outputs (mixed settings)")
    fig.colorbar(im,ax=axs,shrink=.65,label="Descriptive Spearman ρ across outputs")
    save(fig,"Fig_S5","A,B, Complete seven-measure correlation matrices across nine formal outputs per context, recomputed after A010 replaced historical CellOT with seed-123 outputs. Negative excess H and negative nRMSE retain their minus signs on both axes. Values describe mixed-setting implementations, not independent model trials or evidence of independent dimensions. Figures 3E,F and 4E provide observed-relative and centered homogenization references, including shared-mean NA. Pooled correlations are retained in D34; the figure introduces no further selection or hypothesis tests.","Full metric-correlation matrices show overlap and differences across the current nine outputs in each HCC context.",["D34","D01","D02"],pdf)
    annotation=ROOT/"presentation/Results/D40_historical_annotation.tsv"
    ann=pd.read_csv(annotation,sep="\t")
    shutil.copy2(annotation,OUT/"Results/D40_historical_annotation.tsv")
    SOURCES["D40"]={"source":str(annotation.relative_to(ROOT)),"sha256":hashlib.sha256(annotation.read_bytes()).hexdigest(),"rows":len(ann)}
    # Historical figure sources contain only Hallmark aggregation and leave-anchor panels; do not invent Reactome/GO panels.
    fig,axs=plt.subplots(1,3,figsize=(13,7),layout="constrained")
    z=ann[ann.panel=="c"]
    for j,field in enumerate(["mean_NES","median_NES"]):
        wide=z.pivot(index="pathway",columns="context",values=field)
        labels=[textwrap.fill(str(x),24) for x in wide.index]
        im=heat(axs[j],wide,labels,wide.columns,-3,3,"RdBu_r",2)
        heading(axs[j],chr(65+j),"Hallmark: "+("mean aggregation" if j==0 else "median aggregation"))
    z=ann[ann.panel=="d"]
    forest(axs[2],z,"full_NES","loo_NES_min","loo_NES_max",z.context+": "+z.pathway.map(lambda x:textwrap.fill(x,25)))
    heading(axs[2],"C","Historical leave-anchor sensitivity")
    axs[2].set_xlabel("NES: full estimate and leave-anchor range (not CI)")
    save(fig,"Fig_S6","A,B, All eight Hallmark terms present in the retained historical figure source, using mean and median aggregation of the historical response object. C, Full NES and recorded leave-anchor min–max ranges; these are not confidence intervals. All 32 source records, q values and sensitivity fields are supplied in D40. The legacy source contains these Hallmark panels, not populated Reactome/GO panels; empty panels have not been reconstructed from a different contrast. This is descriptive historical annotation, not new enrichment on corrected A003 categories or evidence of pathway causality.","Eight historical Hallmark programs are shown with aggregation and leave-anchor sensitivities, separately from the corrected endpoint object.",["D40"],pdf)
    # Distinguish training randomness from feature-approximation randomness in the supplementary figure.
    training,features=data(46),data(45)
    fig,axs=plt.subplots(2,2,figsize=(11,9),layout="constrained")
    model_colors={"scgen":"#008A70","cpa":"#B65E31","gears":"#7354A2"}
    for j,context in enumerate(["HCC38","HCC1143"]):
        ax=axs[0,j];heading(ax,chr(65+j),f"{context}: training-seed sensitivity")
        for offset,(model,color) in zip([-.12,0,.12],model_colors.items()):
            q=training[training.cell_line.eq(context)&training.model_family.eq(model)].sort_values("training_seed")
            x=q.training_seed.to_numpy(float)+offset
            ax.plot(x,q.endpoint_alignment_spearman,"o-",color=color,label={"scgen":"scGen","cpa":"CPA","gears":"GEARS"}[model],lw=1)
            ax.vlines(x,q.endpoint_alignment_ci_low,q.endpoint_alignment_ci_high,color=color,lw=1)
        ax.axhline(0,color=".6",ls="--",lw=.7)
        ax.set(xticks=[123,124,125],xlabel="Training seed (same split and budget)",ylabel="Endpoint ρ (target-bootstrap 95% CI)",ylim=(-1,1))
        ax.legend(frameon=False,fontsize=8)
    for j,field in enumerate(["endpoint_alignment_spearman","target_identity_spearman"]):
        ax=axs[1,j];heading(ax,chr(67+j),"Replogle: feature-seed sensitivity")
        for model,label,color in [("geneformer_embedding_ridge_loo","Geneformer ridge","#2876A6"),("chargram_lowrank_ridge_loo","Chargram ridge","#B65E31")]:
            q=features[features.base_model_id.eq(model)].sort_values("feature_seed")
            ax.plot(q.feature_seed,q[field],"o-",color=color,label=label,lw=1)
            if j==0:ax.vlines(q.feature_seed,q.endpoint_alignment_ci_low,q.endpoint_alignment_ci_high,color=color,lw=1)
        ax.axhline(0,color=".6",ls="--",lw=.7)
        ax.set(xticks=[123,124,125],xlabel="Feature PCA/SVD seed (fixed base features)",ylabel="Endpoint ρ (95% target-bootstrap CI)" if j==0 else "Identity ρ (Mantel inference; no CI)")
        ax.legend(frameon=False,fontsize=8)
    save(fig,"Fig_S7","A,B, All 18 additional scGen/CPA/GEARS same-context fits: three training seeds, two contexts, fixed data, splits and training budgets. These are supplementary executions, not replacements for the original formal outputs or an architecture ranking. C,D, Six Replogle ridge outputs after changing only randomized feature PCA/SVD seeds; Geneformer's checkpoint, chargram base features and both response-LOO methods remain fixed. Point estimates and, where shown, target-bootstrap intervals condition on each prediction, not a training-seed population. D45/D46 contain all metrics and separate six-output/eighteen-output inference families. No best seed or prediction average is selected.",
         "A single supplementary figure separates variation from three training seeds in scGen, CPA and GEARS from randomized feature preparation in two Replogle ridge models.",["D45","D46"],pdf)

def graphical():
    fig,ax=plt.subplots(figsize=(10,4.5),layout="constrained");ax.axis("off");ax.set(xlim=(0,1),ylim=(0,1))
    for x,txt,col in [(.02,"Observed responses\n+ external dependency\n\nExamine sampling\nand target eligibility","#EAF3F8"),(.36,"Freeze the object\n\nCorrected amplitudes\nFixed categories\nDeclared target/gene axes","#E8F4F0"),(.70,"Model-output audit\n\nOrdering • direction\nAnchor separation • identity\nHomogenization warning","#F0ECF7")]:
        box(ax,x,.22,.28,.62,txt,col)
    for x in [.315,.655]:ax.annotate("",xy=(x+.035,.53),xytext=(x-.01,.53),arrowprops={"arrowstyle":"->","lw":2})
    ax.text(.5,.06,"Assess preserved properties, not an overall ranking",ha="center",fontsize=13,fontweight="bold")
    save(fig,"Graphical_Abstract","Model-output audit: assess preserved properties, not an overall ranking. Qualification and a versioned object precede uniform scoring; arrows show the workflow, not a causal mechanism.","Sampling-aware observed responses and dependency define a fixed object for separate model capability measures.",["D27","D01","D02"])

def plots():
    figure1();figure2();figure3();figure4()
    with PdfPages(OUT/"Figures/Supplementary_Figures.pdf") as pdf:supplementary(pdf)
    graphical()
    (OUT/"Source/figure_manifest.json").write_text(json.dumps(CAPTIONS,ensure_ascii=False,indent=2)+"\n")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=OUT)
    args = parser.parse_args()
    OUT = args.output.resolve()
    setup(); plots()
