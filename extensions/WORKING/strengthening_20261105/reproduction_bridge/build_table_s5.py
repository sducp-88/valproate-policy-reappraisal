from pathlib import Path
import json
P=Path(__file__).resolve().parent
original=json.loads((P/'published_values_and_source_notes.json').read_text(encoding='utf8'))
models=json.loads((P/'exploratory_prais_winsten_models.json').read_text(encoding='utf8'))['fits']
def fmt(x,dec=1):
    def num(v):return f'{v:,.{dec}f}'.replace('-','−')
    if isinstance(x,dict):return num(x['estimate'])+'\n('+num(x['lower'])+' to\n'+num(x['upper'])+')'
    return num(x)
labels=[('mean_outcome','Mean outcome\n平均结局'),('pre_slope','Pre-break slope\n断点前斜率'),('immediate_level','Immediate level change\n即时水平变化'),('slope_change','Slope change\n斜率变化'),('post_slope','Post-break slope\n断点后斜率'),('terminal_percent','April 2025 difference, %\n2025年4月差异，%')]
rows=[]
for key,label in labels:
    pub='14,840 (table 1)\n14,922 (text)\n14,840（表1）\n14,922（正文）' if key=='mean_outcome' else '−10.0\nCI not reported\n未报告区间' if key=='terminal_percent' else fmt(original[key])
    rows.append([label,pub]+[fmt(m[key],2 if key=='terminal_percent' else 1) for m in models[:3]])
t={'en':'Table S5. Published-to-reconstructed bridge for the national oral-valproate analysis','zh':'表S5. 全国口服丙戊酸分析的原文报告与重建结果对照','headers':['Measure','Published [3]','Full oral\nPW 2–12','Full oral\nPW 2–11','0408010W0\nPW 2–12'],'headers_zh':['指标','原文报告[3]','全部口服\nPW 2—12月','全部口服\nPW 2—11月','仅0408010W0\nPW 2—12月'],'rows':rows,'widths':[1.6,1.25,1.28,1.28,1.29],'note':'All analyses cover January 2022–April 2025 with a November 2023 breakpoint; the displayed reconstructions use the reported 30.4-day divisor. Full oral includes both chemical descriptors. PW denotes an iterative Prais–Winsten implementation; 2–12 and 2–11 specify calendar-month indicators. Mean and level are DDD/day equivalents; slopes are DDD/day equivalents per month. Parentheses are 95% CIs. The terminal percentage compares fitted April 2025 with projected prior-trend continuation. Published people-labelled estimates are DDD-derived, not observed distinct patients; both published overall means are retained. Exact original input, conversion code and Stata settings were unavailable. These are exploratory source-aligned comparisons, not exact replication or a between-study test. The code-restricted PW 2–11 result was −0.74% (−4.69% to 3.21%); all four new models and the frozen GLS models are retained in the audit.','note_zh':'全部分析覆盖2022年1月至2025年4月，断点为2023年11月；表中重建均采用原文30.4日除数。全部口服范围包括两种化学成分描述符。PW为迭代Prais–Winsten实现，2—12和2—11表示月份指示项。均量和水平的单位为DDD/日当量，斜率为每月DDD/日当量变化；括号内为95%CI。期末百分比比较2025年4月拟合值与断点前趋势外推值。原文标为人数的结局由DDD推导，并非实测不同患者人数；保留原文两个总体均值。未获得原始输入、转换代码及Stata设置。这些是探索性口径对齐比较，不是精确复现或跨研究检验。仅该代码范围的PW 2—11月结果为−0.74%（−4.69%至3.21%）；全部四种新模型及冻结GLS模型均在审计中保留。'}
assert len(t['headers'])==5 and len(t['rows'])==6 and abs(sum(t['widths'])-6.7)<1e-12
(P/'Table_S5.json').write_text(json.dumps(t,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print('Table_S5.json ready: five columns, six rows, width6.7; numeric estimates imported from model JSON.')
