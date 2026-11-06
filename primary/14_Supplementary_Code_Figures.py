from pathlib import Path
import sys,json
ROOT=Path(__file__).resolve().parent
sys.path.append(str(ROOT/'WORKING/python_deps'))
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from PIL import Image
plt.rcParams.update({'font.family':'Arial','font.size':9,'axes.labelsize':9,'xtick.labelsize':8,'ytick.labelsize':8,'legend.fontsize':8,'axes.spines.top':False,'axes.spines.right':False,'axes.linewidth':.65,'lines.linewidth':1.2,'pdf.fonttype':42,'svg.fonttype':'none','savefig.facecolor':'white','text.color':'#26343D','axes.labelcolor':'#26343D','xtick.color':'#26343D','ytick.color':'#26343D'})
TEAL='#315F6F';RUST='#AD725D';GRAY='#8B8780';INK='#26343D';SAGE='#5B7E78'
out=ROOT/'FIGURES';out.mkdir(exist_ok=True)
d=pd.read_csv(ROOT/'ANALYSIS/data/monthly_analysis.csv');d['date']=pd.to_datetime(d.YEAR_MONTH.astype(str),format='%Y%m')
cur=pd.read_csv(ROOT/'ANALYSIS/results/model_curves.csv');cur['date']=pd.to_datetime(cur.year_month.astype(str),format='%Y%m')
models=json.loads((ROOT/'ANALYSIS/results/models.json').read_text())['fits']
manifest=[]
def finish(fig,name,wmm,hmm):
    fig.set_size_inches(wmm/25.4,hmm/25.4)
    fig.savefig(out/(name+'.pdf'))
    fig.savefig(out/(name+'.svg'))
    fig.savefig(out/(name+'.png'),dpi=180)
    # Vector PDF is the intended journal upload; PNG is only for DOCX review.
    im=Image.open(out/(name+'.png'))
    im.convert('L').save(out/(name+'_grayscale.png'))
    manifest.append({'name':name,'width_mm':wmm,'height_mm':hmm,'upload_format':'PDF vector with embedded TrueType fonts','review_png_pixels':list(im.size),'pixels':im.width*im.height})
    plt.close(fig)
def timeaxis(ax,bottom=True):
    ax.set_xlim(d.date.iloc[0]-pd.Timedelta(days=7),d.date.iloc[-1]+pd.Timedelta(days=7));ax.xaxis.set_major_locator(mdates.MonthLocator(bymonth=[1,7]));ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %Y'))
    if not bottom:ax.tick_params(labelbottom=False)
    ax.tick_params(length=3)
def panel(ax,letter):ax.text(-.105,1.04,letter,transform=ax.transAxes,fontweight='bold',fontsize=11)

fig,axs=plt.subplots(2,1,sharex=True,gridspec_kw={'hspace':.38})
for name,label,col,mark,ls in [('daily_ddd','Dispensed volume',TEAL,'o','-'),('daily_items','Prescription items',RUST,'s','--'),('daily_rows','Aggregate rows',GRAY,'^',':')]:
    axs[0].plot(d.date,d[name]/d[name].iloc[0]*100,label=label,color=col,marker=mark,markersize=2.7,linestyle=ls)
axs[0].set_ylabel('Index (January 2022 = 100)');axs[0].legend(loc='upper left',frameon=False,ncols=3,bbox_to_anchor=(0,1.23))
for name,label,col,mark,ls in [('ddd_per_item','DDDs per prescription item',TEAL,'o','-'),('items_per_row','Items per aggregate row',RUST,'s','--')]:
    axs[1].plot(d.date,d[name]/d[name].iloc[0]*100,label=label,color=col,marker=mark,markersize=2.7,linestyle=ls)
axs[1].set_ylabel('Index (January 2022 = 100)');axs[1].legend(loc='upper left',frameon=False)
for i,ax in enumerate(axs):
    ax.axvspan(pd.Timestamp('2023-10-01'),pd.Timestamp('2024-02-01'),color='#F0EEEA',zorder=0)
    ax.axhline(100,color='#D9DEDF',lw=.6,zorder=0);timeaxis(ax,i==1);panel(ax,chr(65+i))
fig.subplots_adjust(left=.14,right=.98,top=.90,bottom=.09)
finish(fig,'Figure_1',180,150)

fig,axs=plt.subplots(3,1,sharex=True,gridspec_kw={'hspace':.28})
for i,(measure,label,col) in enumerate([('daily_ddd','Dispensed volume\n(thousand DDDs/day)',TEAL),('items','Prescription items\n(thousands/month)',RUST),('rows','Aggregate rows\n(thousands/month)',GRAY)]):
    ax=axs[i];g=cur[cur.id.eq(measure+'_202311_month')]
    ax.plot(g.date,g.observed/1000,'o',ms=3.1,mfc='white',mec=col,mew=.8,label='Observed',zorder=3)
    ax.plot(g.date,g.fitted/1000,color=col,label='Fitted',zorder=2)
    post=g.year_month>=202311
    ax.plot(g.loc[post,'date'],g.loc[post,'counterfactual']/1000,color=INK,ls='--',lw=1.05,label='Prior-trend projection')
    ax.axvline(pd.Timestamp('2023-11-01'),color='#B8B7B3',ls=':',lw=.8)
    ax.set_ylabel(label);timeaxis(ax,i==2);panel(ax,chr(65+i))
axs[0].legend(loc='upper left',ncols=3,frameon=False,bbox_to_anchor=(-.04,1.31))
fig.subplots_adjust(left=.17,right=.98,top=.91,bottom=.08)
finish(fig,'Figure_2',180,187)

specs=[('November 2023 (primary)','daily_ddd_202311_month'),('October 2023','daily_ddd_202310_month'),('December 2023','daily_ddd_202312_month'),('February 2024','daily_ddd_202402_month'),('Fixed 30.4-day divisor','ddd_30_4_202311_month'),('Sodium valproate code only','sodium_only_202311_month'),('Solid oral formulations only','solid_only_202311_month'),('Annual sine/cosine seasonality','daily_ddd_202311_harmonic'),('No seasonal terms','daily_ddd_202311_none')]
fig=plt.figure();ax=fig.add_axes([.37,.15,.41,.79]);tax=fig.add_axes([.80,.15,.20,.79],sharey=ax)
for k,(label,key) in enumerate(specs):
    r=models[key]['terminal_percent'];yy=len(specs)-k-1
    ax.hlines(yy,r['lower'],r['upper'],color=TEAL,lw=1.15,zorder=2);ax.scatter(r['estimate'],yy,color=TEAL,marker='D' if k==0 else 'o',s=27 if k==0 else 18,zorder=3)
    tax.text(0,yy,f"{r['estimate']:.2f} ({r['lower']:.2f}, {r['upper']:.2f})",va='center',fontsize=8)
ax.axvline(0,color='#B6B7B5',lw=.65,zorder=0);ax.set_yticks(range(len(specs)),[s[0] for s in reversed(specs)],fontsize=8.2);ax.tick_params(axis='y',length=0,pad=8)
ax.set_xlim(-14,8);ax.set_xticks([-12,-8,-4,0,4,8]);ax.set_xlabel('April 2025 difference from projection (%)')
ax.set_ylim(-.7,len(specs)-.1);ax.spines['left'].set_visible(False);tax.axis('off');tax.text(0,len(specs)-.15,'Estimate (95% CI)',va='bottom',fontsize=8,fontweight='bold')
finish(fig,'Figure_3',180,117)

fig,axs=plt.subplots(3,2,gridspec_kw={'wspace':.34,'hspace':.45})
for i,(measure,label,col) in enumerate([('daily_ddd','Volume',TEAL),('items','Items',RUST),('rows','Rows',GRAY)]):
    g=cur[cur.id.eq(measure+'_202311_month')]
    ax=axs[i,0];ax.plot(g.date,g.normalized_residual,'o-',color=col,ms=2.7,lw=.7);ax.axhline(0,color='#B6B7B5',lw=.65);ax.set_ylabel(label+' residual');timeaxis(ax,i==2);ax.xaxis.set_major_locator(mdates.YearLocator());ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y'));panel(ax,chr(65+2*i))
    ax=axs[i,1];ac=models[measure+'_202311_month']['normalized_acf'][1:];ax.vlines(np.arange(1,13),0,ac,color=col,lw=1.15);ax.scatter(np.arange(1,13),ac,s=10,color=col);ax.axhline(0,color='#B6B7B5',lw=.6);ax.set_ylim(-.65,.65);ax.set_xlim(.5,12.5);ax.set_xticks([1,3,6,9,12]);ax.set_ylabel('Residual ACF');ax.set_xlabel('Lag (months)' if i==2 else '');panel(ax,chr(66+2*i))
fig.subplots_adjust(left=.13,right=.98,top=.95,bottom=.08)
finish(fig,'Figure_S1',180,170)
(out/'figure_manifest.json').write_text(json.dumps(manifest,indent=2))
d.to_csv(out/'Figure_1_source.csv',index=False)
cur[cur.id.isin([x+'_202311_month' for x in ['daily_ddd','items','rows']])].to_csv(out/'Figure_2_and_S1_source.csv',index=False)
pd.DataFrame([{'label':s[0],'model':s[1],**models[s[1]]['terminal_percent']} for s in specs]).to_csv(out/'Figure_3_source.csv',index=False)
print(json.dumps(manifest,indent=2))
