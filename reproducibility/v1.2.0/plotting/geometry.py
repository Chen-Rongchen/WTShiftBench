"""Context-separated geometry summaries and frozen pairwise-cosine distributions."""
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.transforms import Bbox

def build(p):
    g=p.read('M07_geometry')
    pairs=p.read('M07_pairwise_cosines')
    display=lambda m: 'Chargram low-rank' if m=='Linear low-rank' else m
    f=plt.figure(figsize=(180/25.4,230/25.4))
    f.text(.015,.980,'A',fontsize=11,weight='bold')
    f.text(.065,.980,'Geometry diagnostics by context',fontsize=9)
    keys=['leading_singular_energy_share','effective_rank','target_identity']
    titles=['Leading singular-value\nenergy share','Effective rank','Target-identity\npreservation']
    formal=g.loc[g.model.isin(p.MODELS)]
    x= formal.excess_target_similarity
    span=x.max()-x.min()
    xlim=(min(0,x.min())-.16*span, x.max()+.20*span)
    axes=[]
    for col,(key,title) in enumerate(zip(keys,titles)):
        y=formal[key]; span=y.max()-y.min()
        ylim=(y.min()-.20*span,y.max()+.24*span)
        for row,ctx in enumerate(p.HCC):
            ax=f.add_axes([.11+col*.30,.775-row*.195,.24,.145])
            d=formal.loc[formal.context.eq(ctx)]
            assert len(d)==9 and d.model.nunique()==9
            points=ax.scatter(d.excess_target_similarity,d[key],color=p.COLORS[ctx],
                             marker=p.MARKERS[ctx],s=14)
            points.set_gid(f'A-{ctx}-{key}-data')
            ax.set(xlim=xlim,ylim=ylim)
            ax.locator_params(nbins=3)
            p.reference(ax)
            if row==0:ax.set_title(title,fontsize=8,pad=8)
            if col==0:
                ax.text(-.36,.5,ctx,transform=ax.transAxes,rotation=90,ha='center',va='center',
                        color=p.COLORS[ctx],fontsize=8,weight='bold')
            axes.append((ax,key,d))
    f.text(.52,.531,'Target-similarity difference (predicted − observed)',ha='center',fontsize=7.5)
    mapping=f.add_axes([.075,.445,.88,.065]);mapping.axis('off')
    labels=[[f'{1+row*3+col}  {display(p.MODELS[row*3+col])}' for col in range(3)] for row in range(3)]
    tab=mapping.table(cellText=labels,cellLoc='left',bbox=[0,0,1,1])
    tab.auto_set_font_size(False);tab.set_fontsize(7.5)
    for cell in tab.get_celld().values():
        cell.set_edgecolor(p.LINE);cell.set_linewidth(.35)
    f.text(.015,.413,'B',fontsize=11,weight='bold')
    f.text(.065,.413,'Descriptive pairwise-cosine distributions',fontsize=9)
    for i,m in enumerate(p.MODELS+['Shared mean']):
        row,col=divmod(i,5)
        ax=f.add_axes([.075+col*.185,.245-row*.15,.15,.105])
        for ctx in p.HCC:
            for name,ls in [(m,'-'),('Observed','--')]:
                v=np.sort(pairs.loc[pairs.context.eq(ctx)&pairs.model.eq(name),'cosine'])
                assert len(v)==1081
                line,=ax.step(v,np.arange(1,len(v)+1)/len(v),where='post',color=p.COLORS[ctx],
                             ls=ls,lw=1.2 if name==m else .8,alpha=.85 if name==m else .65)
                line.set_gid(f'B-{m}-{ctx}-{name}')
        title='Shared-mean\nreference' if m=='Shared mean' else display(m).replace(' ','\n',1)
        ax.set_title(title,fontsize=8,pad=3)
        ax.set(xlim=(-1.03,1.03),ylim=(0,1.02),xticks=[-1,0,1],yticks=[0,.5,1])
        if row==0:ax.tick_params(labelbottom=False)
        if col==0:ax.set_ylabel('ECDF',labelpad=2)
        else:ax.tick_params(labelleft=False)
    f.text(.52,.051,'Pairwise cosine',ha='center',fontsize=7.5)
    f.legend(handles=[Line2D([],[],color=p.COLORS[c],ls='-',label=c) for c in p.HCC]+
             [Line2D([],[],color=p.GRAY,ls=ls,label=lab) for ls,lab in [('-','Predicted'),('--','Observed')]],
             loc='lower center',bbox_to_anchor=(.5,.002),ncol=4,frameon=False,fontsize=7.5)
    f.canvas.draw();renderer=f.canvas.get_renderer();records=[]
    for ax,key,rows in axes:
        placed=[];scale=f.dpi/72
        dots=[Bbox.from_bounds(x-4*scale,y-4*scale,8*scale,8*scale)
              for x,y in ax.transData.transform(rows[['excess_target_similarity',key]].values)]
        for r in rows.itertuples():
            label=str(p.MODELS.index(r.model)+1)
            a=ax.annotate(label,(r.excess_target_similarity,getattr(r,key)),xytext=(5,5),
                          textcoords='offset points',fontsize=7.5,ha='center',va='center',
                          arrowprops=dict(arrowstyle='-',lw=.35,color='#aab3ba'))
            a.set_gid(f'A-label-{r.context}-{key}-{label}')
            best=None
            for radius in [8,12,18,24,32,40,48]:
                for dx,dy in [(radius,radius),(-radius,radius),(radius,-radius),(-radius,-radius),
                              (0,radius),(radius,0),(-radius,0),(0,-radius)]:
                    anchor=ax.transData.transform((r.excess_target_similarity,getattr(r,key)))+np.array([dx,dy])*scale
                    w=renderer.get_text_width_height_descent(label,a.get_fontproperties(),False)[0]+4*scale
                    box=Bbox.from_bounds(anchor[0]-w/2,anchor[1]-5.5*scale,w,11*scale)
                    conflict=sum(box.overlaps(b) for b in placed+dots)+10*(
                        not ax.bbox.contains(box.x0,box.y0) or not ax.bbox.contains(box.x1,box.y1))
                    if best is None or conflict<best[0]:best=(conflict,(dx,dy),box)
                if best[0]==0:break
            a.set_position(best[1]);placed.append(best[2])
            records.append(dict(metric=key,context=r.context,model=r.model,label=label,
                                overlap_count=best[0],offset_x_pt=best[1][0],offset_y_pt=best[1][1]))
    pd.DataFrame(records).to_csv(p.OUT/'S6-label-placement.tsv',sep='\t',index=False)
    p.save(f,'S6')
