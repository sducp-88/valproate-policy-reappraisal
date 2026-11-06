"""Descriptive patient-indicator context; no policy-effect model or patient-dose conversion."""
from pathlib import Path
import json,hashlib,calendar,sys
import numpy as np
import pandas as pd

BASE=Path(__file__).resolve().parent
ROOT=BASE.parents[1]
ACQ=BASE/'acquisition'
OUT=BASE/'analysis';OUT.mkdir(exist_ok=True)
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf8')
frozen=json.loads((BASE/'frozen_inputs_manifest.json').read_text('utf8'))
for rel,sha in frozen.items():assert h(ROOT/rel)==sha,rel
plan=json.loads((BASE/'AMENDMENT_BEFORE_PATIENT_ANALYSIS.json').read_text('utf8'))
paths=[ACQ/'vpa1_history.csv',ROOT/'ANALYSIS/data/monthly_analysis.csv',BASE/'AMENDMENT_BEFORE_PATIENT_ANALYSIS.json']
v=pd.read_csv(ACQ/'vpa1_history.csv',dtype={'period_start_month':str,'period_end_month':str})
assert set(v.indicator)=={'VPA1'} and set(v.age_band)=={'13-54'} and set(v.sex)=={'female'}
assert set(v.geography.str.lower())=={'national'}
v['end']=pd.PeriodIndex(v.period_end_month,freq='M')
v['start']=pd.PeriodIndex(v.period_start_month,freq='M')
assert len(v)==94 and not v.end.duplicated().any()
assert all(a==b-2 for a,b in zip(v.start,v.end))
assert list(v.end)==list(pd.period_range(v.end.min(),v.end.max(),freq='M'))
assert v[['numerator','denominator','published_value']].notna().all().all()
assert (v.numerator>0).all() and (v.denominator>v.numerator).all()
v['calculated_rate_per_1000']=1000*v.numerator/v.denominator
round_error=(v.calculated_rate_per_1000-v.published_value).abs()
assert round_error.max()<=0.005+1e-12
within=v[(v.start>=pd.Period('2022-01'))&(v.end<=pd.Period('2025-04'))].copy()
assert len(within)==38
quarter=within[within.end.dt.month.isin([3,6,9,12])].copy()
assert len(quarter)==13
assert list(quarter.end)==list(pd.period_range('2022-03','2025-03',freq='M')[::3])
monthly=pd.read_csv(ROOT/'ANALYSIS/data/monthly_analysis.csv')
monthly['period']=pd.PeriodIndex(monthly.YEAR_MONTH.astype(str),freq='M')
assert len(monthly)==40 and not monthly.period.duplicated().any()
def epd_window(end):
    frame=monthly[(monthly.period>=end-2)&(monthly.period<=end)]
    assert len(frame)==3
    nd=sum(calendar.monthrange(p.year,p.month)[1] for p in frame.period)
    assert nd==int(frame.days.sum())
    return {'window_days':nd,'oral_ddd':float(frame.ddd.sum()),'oral_items':int(frame['items'].sum()),'oral_rows':int(frame.rows.sum()),'oral_daily_ddd':float(frame.ddd.sum()/nd),'oral_daily_items':float(frame['items'].sum()/nd),'oral_daily_rows':float(frame.rows.sum()/nd)}
extra=pd.DataFrame([epd_window(e) for e in within.end],index=within.index)
within=pd.concat([within,extra],axis=1)
within['nonoverlapping_calendar_quarter']=within.end.dt.month.isin([3,6,9,12])
within['window_role']=np.where(within.nonoverlapping_calendar_quarter,'calendar_quarter','overlapping_context')
within.loc[within.end==pd.Period('2025-04'),'window_role']='latest_overlapping_window_not_extra_quarter'
quarter=within[within.nonoverlapping_calendar_quarter].copy()
first=quarter.iloc[0];last=quarter.iloc[-1];latest=within.iloc[-1]
metrics=[('numerator','Female recipients counted within practices, aged13-54'),('calculated_rate_per_1000','Female recipient indicator per1000 registered females, aged13-54'),('denominator','Female GP-registered population denominator, aged13-54'),('oral_daily_ddd','All-age/all-sex oral DDDs per calendar day'),('oral_daily_items','All-age/all-sex oral prescription items per calendar day'),('oral_daily_rows','All-age/all-sex oral source rows per calendar day')]
comparisons=[]
for m,label in metrics:
    a,b,c=map(float,[first[m],last[m],latest[m]])
    comparisons.append({'measure':m,'label':label,'Q1_2022':a,'Q1_2025':b,'absolute_change_Q1_2022_to_Q1_2025':b-a,'percent_change_Q1_2022_to_Q1_2025':100*(b/a-1),'Feb_Apr_2025':c,'latest_window_separate_from_Q1_2025':True})
for frame,name in [(within,'patient_context_38_windows.csv'),(quarter,'patient_context_13_quarters.csv')]:
    frame=frame.drop(columns=['start','end']);frame.to_csv(OUT/name,index=False)
pd.DataFrame(comparisons).to_csv(OUT/'descriptive_comparisons.csv',index=False)
summary={'status':'PASS','design':'Dated exploratory descriptive context; no causal model, p value, dose/person ratio or independent-cohort claim','patient_source':'Same-date current historical dashboard snapshot extracted from visible national UI table, not an original provider CSV export','n_raw_windows':len(v),'n_within_period_windows':len(within),'n_nonoverlapping_calendar_quarters':len(quarter),'first_complete_window':'January–March2022','last_calendar_matched_window':'January–March2025','latest_window':'February–April2025 (overlaps Q1 2025)','max_absolute_published_rounding_difference':float(round_error.max()),'comparisons':comparisons,'interpretation_boundaries':['Different patient population and formulation coverage from EPD oral volume','Patient counts aggregate practice-level deduplication; not guaranteed nationally unique people','Shared NHSBSA origin is complementary measurement, not independent external validation','Nonoverlapping windows can contain the same people and remain serially related','Endpoint percent changes are descriptive, not frozen ITS counterfactual contrasts','No treatment persistence, discontinuation, pregnancy or seizure outcomes identified']}
save(OUT/'patient_context_summary.json',summary)
save(OUT/'input_manifest.json',{'files':{str(p.relative_to(ROOT)).replace('\\','/'):h(p) for p in paths},'frozen_inputs_unchanged':True,'python':sys.version,'numpy':np.__version__,'pandas':pd.__version__})
print(json.dumps(summary,ensure_ascii=False,indent=2))
