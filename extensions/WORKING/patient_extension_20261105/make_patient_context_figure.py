"""Figure S3 and Table S9 from verified descriptive source files; no models.

Portable use:
  python make_patient_context_figure.py --input-dir analysis --output-dir figures --source-dir figure_source
"""
from pathlib import Path
import argparse
import csv
import hashlib
import json
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.ticker import FuncFormatter, MaxNLocator

HERE = Path(__file__).resolve().parent
parser = argparse.ArgumentParser()
parser.add_argument('--input-dir', type=Path, default=HERE/'analysis')
parser.add_argument('--output-dir', type=Path, default=HERE.parents[1]/'FIGURES')
parser.add_argument('--source-dir', type=Path, default=HERE/'figure_source')
parser.add_argument('--basename', default='Figure_S3')
args = parser.parse_args()
args.output_dir.mkdir(parents=True, exist_ok=True)
args.source_dir.mkdir(parents=True, exist_ok=True)

inputs = {name:args.input_dir/name for name in ['patient_context_38_windows.csv', 'patient_context_13_quarters.csv', 'descriptive_comparisons.csv', 'patient_context_summary.json']}
w = pd.read_csv(inputs['patient_context_38_windows.csv'])
q = pd.read_csv(inputs['patient_context_13_quarters.csv'])
c = pd.read_csv(inputs['descriptive_comparisons.csv']).set_index('measure')
summary = json.loads(inputs['patient_context_summary.json'].read_text(encoding='utf-8'))
assert summary['status']=='PASS' and len(w)==38 and len(q)==13
assert w.period_end_month.is_unique and q.period_end_month.is_unique
assert w.period_start_month.min()=='2022-01' and w.period_end_month.max()=='2025-04'
assert q.period_end_month.iloc[0]=='2022-03' and q.period_end_month.iloc[-1]=='2025-03'
assert set(q.period_end_month).issubset(set(w.period_end_month))
for field in ['numerator','oral_daily_items','oral_daily_ddd']:
    assert np.allclose(q.set_index('period_end_month')[field],w.set_index('period_end_month').loc[q.period_end_month,field])
latest = w.loc[w.period_end_month.eq('2025-04')].iloc[0]
x = pd.to_datetime(w.period_end_month+'-01')
xq = pd.to_datetime(q.period_end_month+'-01')
xl = pd.Timestamp('2025-04-01')

INK = '#26343D'
TEAL = '#315F6F'
LIGHT = '#BEC5C8'
GRID = '#E6E9E8'
GREY = '#616E74'
plt.rcParams.update({
    'font.family':'Arial', 'font.size':9, 'axes.labelsize':9,
    'xtick.labelsize':8.4, 'ytick.labelsize':8.4, 'axes.linewidth':0.65,
    'axes.edgecolor':'#899398', 'text.color':INK, 'axes.labelcolor':INK,
    'xtick.color':INK, 'ytick.color':INK, 'pdf.fonttype':42,
    'ps.fonttype':42, 'svg.fonttype':'none', 'savefig.facecolor':'white',
    'figure.facecolor':'white', 'axes.facecolor':'white',
})

fig = plt.figure(figsize=(180/25.4,160/25.4))
axes=[]
panels=[
    ('A','oral_daily_items','Oral prescription items','All ages and sexes; oral products','Items per day'),
    ('B','oral_daily_ddd','Oral defined daily doses','All ages and sexes; oral products','DDDs per day'),
    ('C','numerator','Female recipients','Age 13–54 years; counts aggregated across practices','Recipients'),
]
legend_items=[
    Line2D([0],[0],color=LIGHT,lw=1.4,label='Rolling three-month windows (38)'),
    Line2D([0],[0],marker='o',color='none',markerfacecolor=TEAL,markeredgecolor='white',markersize=4.7,label='Calendar quarters (13)'),
    Line2D([0],[0],marker='D',color='none',markerfacecolor='white',markeredgecolor=GREY,markersize=4.4,label='Feb–Apr 2025'),
]
leg=fig.legend(handles=legend_items,loc='upper center',bbox_to_anchor=(0.525,0.995),ncol=3,frameon=False,fontsize=8.0,handlelength=1.5,columnspacing=1.3,handletextpad=0.6,borderaxespad=0)

for (letter,field,title,subtitle,ylabel),bottom in zip(panels,[0.685,0.415,0.145]):
    ax=fig.add_axes([0.145,bottom,0.615,0.175])
    axes.append(ax)
    ax.plot(x,w[field],color=LIGHT,lw=1.35,zorder=1)
    ax.scatter(xq,q[field],color=TEAL,s=19,edgecolor='white',linewidth=0.45,zorder=3)
    ax.scatter([xq.iloc[0],xq.iloc[-1]],[q[field].iloc[0],q[field].iloc[-1]],color=TEAL,s=27,edgecolor=INK,linewidth=0.55,zorder=4)
    ax.scatter([xl],[latest[field]],marker='D',s=24,facecolor='white',edgecolor=GREY,linewidth=0.9,zorder=5)
    ymin,ymax=float(w[field].min()),float(w[field].max())
    span=ymax-ymin
    ax.set_ylim(ymin-span*0.12,ymax+span*0.12)
    ax.set_xlim(pd.Timestamp('2022-01-20'),pd.Timestamp('2025-05-20'))
    ax.yaxis.set_major_locator(MaxNLocator(nbins=3,min_n_ticks=3))
    ax.yaxis.set_major_formatter(FuncFormatter(lambda v,pos:f'{v:,.0f}'))
    ax.grid(axis='y',color=GRID,lw=0.55,zorder=0)
    ax.spines[['top','right']].set_visible(False)
    ax.tick_params(axis='both',length=3,width=0.65,pad=3)
    ax.set_ylabel(ylabel,labelpad=7)
    ax.set_xticks([pd.Timestamp(f'{year}-03-01') for year in range(2022,2026)])
    if letter=='C':
        ax.set_xticklabels(['Mar 2022','Mar 2023','Mar 2024','Mar 2025'])
        ax.set_xlabel('Three-month window ending',labelpad=6)
    else:
        ax.tick_params(axis='x',labelbottom=False)
    fig.text(0.052,bottom+0.205,letter,fontsize=10.5,fontweight='bold',va='center')
    fig.text(0.145,bottom+0.205,title,fontsize=9.5,fontweight='bold',va='center')
    fig.text(0.145,bottom+0.180,subtitle,fontsize=8.2,color=GREY,va='bottom')
    ref=c.loc[field]
    change=f"{ref.percent_change_Q1_2022_to_Q1_2025:+.1f}%".replace('-','−')
    fig.text(0.792,bottom+0.133,f"Q1 2022: {ref.Q1_2022:,.0f}",fontsize=8.4,va='center')
    fig.text(0.792,bottom+0.098,f"Q1 2025: {ref.Q1_2025:,.0f}",fontsize=8.4,va='center')
    fig.text(0.792,bottom+0.051,change,fontsize=11,fontweight='bold',color=TEAL,va='center')
    fig.text(0.792,bottom+0.018,'Descriptive change',fontsize=7.7,color=GREY,va='center')

base=args.output_dir/args.basename
for ext in ['pdf','svg','png']:
    fig.savefig(base.with_suffix('.'+ext),dpi=600,metadata={'Creator':'Matplotlib'} if ext=='pdf' else None)
fig.canvas.draw()
renderer=fig.canvas.get_renderer()
canvas=fig.get_window_extent(renderer)
text_checks=[]
for t in fig.findobj(matplotlib.text.Text):
    if t.get_visible() and t.get_text():
        bbox=t.get_window_extent(renderer)
        if bbox.width and bbox.height:
            clipped=any([bbox.x0<canvas.x0-0.5,bbox.y0<canvas.y0-0.5,bbox.x1>canvas.x1+0.5,bbox.y1>canvas.y1+0.5])
            text_checks.append({'text':t.get_text(),'inside_canvas':not clipped})
assert all(z['inside_canvas'] for z in text_checks), [z for z in text_checks if not z['inside_canvas']]
plt.close(fig)

measures=[
    ('numerator','Female recipients aged 13–54, practice-aggregated count',0),
    ('calculated_rate_per_1000','Female recipient indicator per 1,000 registered females aged 13–54',3),
    ('oral_daily_items','Oral prescription items per day, all ages and sexes',1),
    ('oral_daily_ddd','Oral DDDs per day, all ages and sexes',1),
]
def fmt(v,dp):return f'{v:,.{dp}f}'.replace('-','−')
table_rows=[]
numeric_rows=[]
for field,label,dp in measures:
    r=c.loc[field]
    table_rows.append({'Measure':label,'Q1 2022':fmt(r.Q1_2022,dp),'Q1 2025':fmt(r.Q1_2025,dp),'Change, Q1 2022 to Q1 2025':fmt(r.absolute_change_Q1_2022_to_Q1_2025,dp)+' ('+fmt(r.percent_change_Q1_2022_to_Q1_2025,1)+'%)','Feb–Apr 2025':fmt(r.Feb_Apr_2025,dp)})
    numeric_rows.append({'measure':field,'label':label,'Q1_2022':float(r.Q1_2022),'Q1_2025':float(r.Q1_2025),'absolute_change':float(r.absolute_change_Q1_2022_to_Q1_2025),'percent_change':float(r.percent_change_Q1_2022_to_Q1_2025),'Feb_Apr_2025':float(r.Feb_Apr_2025)})
with (args.source_dir/'Table_S9_patient_context.csv').open('w',encoding='utf-8-sig',newline='') as f:
    writer=csv.DictWriter(f,fieldnames=list(table_rows[0]));writer.writeheader();writer.writerows(table_rows)
with (args.source_dir/'Table_S9_patient_context_numeric.csv').open('w',encoding='utf-8-sig',newline='') as f:
    writer=csv.DictWriter(f,fieldnames=list(numeric_rows[0]));writer.writeheader();writer.writerows(numeric_rows)

caption={
 'figure_number':'Figure S3',
 'figure_title':'Calendar-aligned national valproate dispensing and female recipient indicators',
 'figure_legend':'Panels show oral prescription items per day (A), oral defined daily doses (DDDs) per day (B), and the NHSBSA VPA1 female recipient count for ages 13–54 years (C). Grey lines show 38 overlapping three-month windows fully within January 2022–April 2025; teal circles mark 13 non-overlapping calendar quarters from Q1 2022 to Q1 2025. Outlined circles identify those two endpoint quarters. The open diamond marks February–April 2025, which overlaps Q1 2025 and is not an additional independent quarter. Dispensing totals were summed within each window and divided by its actual calendar days. Q1-to-Q1 percentage changes are descriptive comparisons, not policy effects or counterfactual estimates. Each panel retains its own units and axis range. Panels A and B include all ages and sexes and only oral products; panel C covers females aged 13–54 and the dashboard drug scope. Dashboard counts aggregate patients deduplicated within prescribing practices and are not guaranteed nationally unique persons. Non-overlapping windows may include the same patients. The series provide complementary measurements from NHSBSA sources, not independent external validation or a basis for dose-per-person calculations. Patient data are a current historical snapshot retrieved from the public dashboard on 5 November 2026.',
 'figure_alt_text':'Three stacked panels show calendar-aligned valproate indicators with separate units. Q1 2022 to Q1 2025 descriptive changes are −10.2% in all-age, all-sex oral prescription items per day, −2.0% in oral DDDs per day, and −25.2% in female recipients aged13–54 counted within practices and aggregated nationally. Population and formulation coverage differ across panels.',
 'table_number':'Table S9',
 'table_title':'Descriptive comparison of calendar-aligned dispensing and female recipient indicators',
 'table_columns':list(table_rows[0]),'table_rows':table_rows,'table_numeric_rows':numeric_rows,
 'table_notes':[
   'Change is the absolute difference (percentage change) from Q1 2022 to Q1 2025, calculated from unrounded values. These are descriptive comparisons, not policy-effect estimates.',
   'Q1 denotes January–March. The February–April 2025 column is the latest fully within-period window; it overlaps Q1 2025 and is shown separately.',
   'Female recipient counts are aggregated from prescribing practices after within-practice deduplication; nationally unique people are not guaranteed. The denominator-derived rate is recalculated from the published count and GP-registered female population denominator and rounded to three decimal places here.',
   'Oral items and DDDs include all ages and sexes; counts cover females aged13–54 and the dashboard drug scope. Oral totals are divided by the actual number of calendar days in each window. Differences in population and formulation coverage preclude dose-per-person calculations or direct effect-size equivalence.',
   'DDDs: defined daily doses. The public patient dashboard was accessed on 5 November 2026; data were preserved by UI text extraction, not an original provider CSV export.'
 ],
 'data_sources':{'dispensing':'Frozen NHSBSA English Prescribing Dataset oral series, aggregated in verified analysis inputs','patients':'NHSBSA Valproate Prescribing in Female Patients Under55 dashboard, National, female13–54, VPA1; UI_TEXT_EXTRACTION'},
 'sources_urls':['https://www.nhsbsa.nhs.uk/access-our-data-products/epact2/dashboards-and-specifications/valproate-safety-dashboard','https://datahub.nhsbsa.nhs.uk/data-hub/data-products/public-data/prescription-dashboards-and-reports/dcb9ec3c-8aba-40e6-a808-6e1c848f4462'],
}
(args.source_dir/'Figure_S3_Table_S9_caption.json').write_text(json.dumps(caption,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
legend_enzh={
 'figure_number':'Figure S3',
 'en':{'title':caption['figure_title'],'legend':caption['figure_legend'],'alt_text':caption['figure_alt_text']},
 'zh':{
  'title':'按相同日历窗口呈现的全国丙戊酸处方量与女性用药者指标',
  'legend':'A、B、C分别显示口服处方项目数/日、口服限定日剂量（DDD）/日，以及NHSBSA VPA1中13–54岁女性用药者计数。浅灰线为完全位于2022年1月至2025年4月内的38个相互重叠的三个月窗口；墨青圆点为2022年第一季度至2025年第一季度的13个不重叠自然季度。带轮廓的圆点标识上述两个端点季度。空心菱形表示2025年2–4月；该窗口与2025年第一季度重叠，不作为另一个独立季度。处方量先在各窗口内求和，再除以该窗口实际日历天数。两个第一季度之间的百分比变化仅作描述，不是政策效应或反事实估计。三个面板保留各自单位和纵轴范围。A、B包括所有年龄、男女合计且仅限口服剂型；C仅覆盖13–54岁女性及仪表板药品范围。仪表板患者数先在各处方机构内部去重，再跨机构汇总，不保证全国范围每人只计一次；不重叠窗口中也可能出现同一患者。这些序列属于NHSBSA资料的互补测量，不构成独立外部验证，也不能用于计算人均用药剂量。患者资料为2026年11月5日从公开仪表板获取的回溯历史快照。',
  'alt_text':'三个纵向面板使用独立单位呈现日历窗口一致的丙戊酸指标。2022年第一季度至2025年第一季度，所有年龄、男女合计的口服处方项目数/日描述性下降10.2%，口服DDD/日下降2.0%，机构内去重后全国汇总的13–54岁女性用药者计数下降25.2%。各面板的人群和剂型范围不同。'
 },
 'source_urls':caption['sources_urls'],
}
(args.source_dir/'Figure_S3_legend_ENZH.json').write_text(json.dumps(legend_enzh,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
zh_headers=['指标','2022年第一季度','2025年第一季度','2022至2025年第一季度变化','2025年2–4月']
zh_labels=['13–54岁女性用药者，机构内去重后汇总人数','每1,000名GP注册13–54岁女性中的用药者指标','所有年龄、男女合计的口服处方项目数/日','所有年龄、男女合计的口服DDD/日']
zh_rows=[dict(zip(zh_headers,[label]+list(row.values())[1:])) for label,row in zip(zh_labels,table_rows)]
table_enzh={
 'table_number':'Table S9',
 'en':{'title':caption['table_title'],'columns':caption['table_columns'],'rows':table_rows,'notes':caption['table_notes']},
 'zh':{
  'title':'相同日历窗口内处方量与女性用药者指标的描述性比较',
  'columns':zh_headers,'rows':zh_rows,
  'notes':[
   '变化列为2022年第一季度至2025年第一季度的绝对差值（百分比变化），按未四舍五入的数据计算，仅作描述，不是政策效应估计。',
   '第一季度为1–3月。2025年2–4月是完全落在研究期内的最新窗口，与2025年第一季度重叠，因此单列展示。',
   '女性用药者先在各处方机构内去重后汇总，不保证全国每人只计一次。每千人率根据发布的分子及GP注册女性人口分母重新计算，本表保留三位小数。',
   '口服项目数和DDD包括所有年龄、男女合计；女性计数覆盖13–54岁及仪表板药品范围。口服量按每个窗口实际日历天数计算日均值。人群和剂型范围不同，不能据此计算人均剂量或将变化幅度视为同一种效应。',
   'DDD：限定日剂量；GP：全科医生。公开患者仪表板访问日期为2026年11月5日，资料通过界面文本提取保存，并非平台原始CSV导出。'
  ]
 },
 'numeric_source_rows':numeric_rows,
}
(args.source_dir/'Table_S9_ENZH.json').write_text(json.dumps(table_enzh,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
qa={
 'status':'PASS_NUMERIC_AND_CANVAS_QA_VISUAL_REVIEW_REQUIRED','figure_mm':[180,160],
 'png_dpi':600,'font':'Arial','n_rolling_windows':38,'n_calendar_quarters':13,
 'latest_window':'Feb 25-Apr 25','all_text_bounding_boxes_inside_canvas':True,
 'figure_series':['oral_daily_items','oral_daily_ddd','numerator'],
 'table_rows':4,'table_columns':5,
 'input_sha256':{k:hashlib.sha256(v.read_bytes()).hexdigest() for k,v in inputs.items()},
 'output_sha256':{f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in list(args.output_dir.glob(args.basename+'.*'))+list(args.source_dir.glob('*.csv'))+list(args.source_dir.glob('*caption.json'))+list(args.source_dir.glob('*ENZH.json'))},
 'analysis_not_run':'The script only renders independently verified descriptive sources; no fits, tests, policy contrasts or patient-dose ratios.',
}
(args.source_dir/'Figure_S3_Table_S9_QA.json').write_text(json.dumps(qa,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'figure_base':str(base),'table_source_dir':str(args.source_dir),'status':qa['status']},ensure_ascii=False))
