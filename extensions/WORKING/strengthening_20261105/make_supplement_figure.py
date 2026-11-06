from pathlib import Path
import sys,json
ROOT=Path(__file__).resolve().parents[2]
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np,pandas as pd
from PIL import Image
IN=ROOT/'WORKING/strengthening_20261105/measurement_components';OUT=ROOT/'FIGURES'
OUT.mkdir(parents=True,exist_ok=True)
s=json.loads((IN/'decomposition_summary.json').read_text());r=pd.read_csv(IN/'paired_log_ratio_contrasts.csv')
plt.rcParams.update({'font.family':'Arial','font.size':9,'axes.labelsize':9,'xtick.labelsize':8.5,'ytick.labelsize':9,'axes.spines.top':False,'axes.spines.right':False,'axes.linewidth':.6,'pdf.fonttype':42,'svg.fonttype':'none','text.color':'#26343D','axes.labelcolor':'#26343D','xtick.color':'#26343D','ytick.color':'#26343D','savefig.facecolor':'white'})
teal='#315F6F';rust='#AD725D';gray='#8B8780'
fig=plt.figure(figsize=(180/25.4,155/25.4));gs=fig.add_gridspec(2,1,height_ratios=[1,1.45],hspace=.70)
ax=fig.add_subplot(gs[0]);names=['Within presentations','Presentation mix'];values=[s['components'][k]['ddd_per_item'] for k in ['within','mix']]
ax.barh([1,0],values,height=.48,color=[teal,gray]);ax.set_yticks([1,0],names);ax.set_xlim(0,1.62);ax.set_xlabel('Contribution to change in DDDs per prescription item')
for y,k,value in zip([1,0],['within','mix'],values):ax.text(value+.025,y,f"{value:.3f} ({s['components'][k]['percent_of_net_change']:.1f}%)",va='center',fontsize=9)
ax.set_title('A  Pooled period difference: 15.67 to 17.06 DDDs/item',loc='left',fontsize=10,fontweight='bold',pad=10)
ax.text(0,-.55,'One exiting presentation: −0.000003 DDDs/item; no entrants.',transform=ax.transAxes,fontsize=8.5)
lower=gs[1].subgridspec(1,2,width_ratios=[3.5,1.6],wspace=.06)
ax=fig.add_subplot(lower[0]);nums=fig.add_subplot(lower[1]);nums.axis('off');nums.set_ylim(-.6,5.8)
yy=[5.2,4.4,3.0,2.2,.8,0.0];labels=[]
for pos,(name,br) in zip(yy,[(x,b) for x in ['ddd_per_item','items_per_row','ddd_per_row'] for b in [202311,202402]]):
    a=r[(r.measure==name)&(r.breakpoint==br)&(r.HAC_lag==3)].iloc[0]
    v=a.terminal_percent_ratio_difference;ax.errorbar(v,pos,xerr=[[v-a.lower],[a.upper-v]],fmt='o' if br==202311 else 's',color=teal if br==202311 else rust,markersize=4,capsize=2,elinewidth=1)
    labels.append({'ddd_per_item':'DDDs/item','items_per_row':'Items/row','ddd_per_row':'DDDs/row'}[name]+(' · Nov 2023' if br==202311 else ' · Feb 2024'))
    nums.text(1,pos,f'{v:+.2f} ({a.lower:+.2f}, {a.upper:+.2f})',va='center',ha='right',fontsize=8.3)
ax.axvline(0,color=gray,lw=.7,ls='--');ax.set_yticks(yy,labels);ax.set_xlim(-15,21);ax.set_ylim(-.6,5.8);ax.set_xticks([-10,0,10,20]);ax.set_xlabel('Terminal ratio difference relative to prior trend, %',fontsize=8.5)
nums.text(1,5.95,'Estimate (95% CI)',ha='right',fontsize=8.5)
ax.set_title('B  Paired log-ratio models with alternative breakpoints',loc='left',fontsize=10,fontweight='bold',pad=10)
fig.subplots_adjust(left=.25,right=.985,top=.92,bottom=.10)
for suffix in ['pdf','svg','png']:fig.savefig(OUT/f'Figure_S2.{suffix}',dpi=180)
Image.open(OUT/'Figure_S2.png').convert('L').save(OUT/'Figure_S2_grayscale.png')
r[r.HAC_lag==3].to_csv(OUT/'Figure_S2_ratio_source.csv',index=False)
pd.DataFrame([{'component':k,**v} for k,v in s['components'].items()]).to_csv(OUT/'Figure_S2_decomposition_source.csv',index=False)
print('Saved Figure_S2 vector PDF/SVG, review PNG, grayscale and source CSVs.')
