"""Descriptive cost extension and exact, ordered fixed-2022-price decomposition."""
from pathlib import Path
import calendar,hashlib,json,os,sys
sys.dont_write_bytecode=True
import numpy as np
import pandas as pd
OUT=Path(__file__).resolve().parent;ROOT=OUT.parents[2]
h=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert json.loads((OUT/'full_validation.json').read_text(encoding='utf8'))['status']=='PASS'
assert (OUT/'ANALYSIS_DEFINITION_BEFORE_COST_RESULTS.json').exists()
cost=pd.read_csv(OUT/'full_all_route_presentation_month.csv')
frozen=pd.read_csv(ROOT/'ANALYSIS/data/valproate_presentation_month.csv')
keys=['YEAR_MONTH','BNF_CODE','BNF_DESCRIPTION'];pkeys=['BNF_CODE','BNF_DESCRIPTION']
data=cost.merge(frozen[keys+['form','g_per_unit','ddd']],on=keys,validate='one_to_one')
oral=data[data.form.isin(['oral_solid','oral_liquid'])].copy()
assert len(oral)==2200
assert not ((oral.ddd==0)&(oral.nic!=0)).any()
oral['days']=[calendar.monthrange(int(str(x)[:4]),int(str(x)[4:]))[1] for x in oral.YEAR_MONTH]
oral.to_csv(OUT/'oral_cost_presentation_month.csv',index=False)
monthly=oral.groupby('YEAR_MONTH').agg(items=('items','sum'),ddd=('ddd','sum'),nic=('nic','sum'),actual_cost=('actual_cost','sum'),days=('days','first')).reset_index()
for col in ['items','ddd','nic','actual_cost']:monthly['daily_'+col]=monthly[col]/monthly.days
monthly['nic_per_ddd']=monthly.nic/monthly.ddd
monthly['nic_per_item']=monthly.nic/monthly['items']
monthly['actual_cost_per_ddd']=monthly.actual_cost/monthly.ddd
monthly['actual_cost_to_nic']=monthly.actual_cost/monthly.nic
monthly['actual_cost_method']='group_specific_discount' 
monthly.loc[monthly.YEAR_MONTH<202404,'actual_cost_method']='previous_average_discount'
baseline=oral[oral.YEAR_MONTH.between(202201,202212)].groupby(pkeys).agg(ddd=('ddd','sum'),nic=('nic','sum')).reset_index()
assert len(monthly[monthly.YEAR_MONTH.between(202201,202212)])==12
baseline=baseline[baseline.ddd>0].copy();baseline['base_nic_per_ddd']=baseline.nic/baseline.ddd
baseline['base_daily_ddd']=baseline.ddd/365;baseline['base_daily_nic']=baseline.nic/365
baseline.to_csv(OUT/'baseline_2022_prices.csv',index=False)
baseC=float(baseline.base_daily_nic.sum());decomp=[];detail=[]
for ym,cur in oral.groupby('YEAR_MONTH'):
    days=int(cur.days.iloc[0]);cur=cur[cur.ddd>0].copy()
    cur['current_daily_ddd']=cur.ddd/days;cur['current_daily_nic']=cur.nic/days
    joined=baseline.merge(cur[pkeys+['current_daily_ddd','current_daily_nic']],on=pkeys,how='outer',indicator=True,validate='one_to_one')
    common=joined[joined._merge=='both'].copy();entry=joined[joined._merge=='right_only'].copy();exit_=joined[joined._merge=='left_only'].copy()
    D0=float(common.base_daily_ddd.sum());Dt=float(common.current_daily_ddd.sum());C0=float(common.base_daily_nic.sum());Ct=float(common.current_daily_nic.sum())
    U0=C0/D0
    fixed=float((common.current_daily_ddd*common.base_nic_per_ddd).sum())
    volume=(Dt-D0)*U0;mix=fixed-Dt*U0;price=Ct-fixed
    entry_cost=float(entry.current_daily_nic.sum());exit_cost=-float(exit_.base_daily_nic.sum())
    observed=float(cur.current_daily_nic.sum())-baseC
    reconstructed=volume+mix+price+entry_cost+exit_cost
    assert abs(observed-reconstructed)<1e-7,(ym,observed,reconstructed)
    record={'YEAR_MONTH':int(ym),'base_daily_nic':baseC,'current_daily_nic':float(cur.current_daily_nic.sum()),'observed_change_daily_nic':observed,'common_volume_component':volume,'common_mix_component':mix,'common_price_component':price,'entry_component':entry_cost,'exit_component':exit_cost,'reconstructed_change':reconstructed,'absolute_identity_error':abs(observed-reconstructed),'common_presentations':len(common),'entrant_presentations':len(entry),'exited_presentations':len(exit_),'common_ddd_coverage':Dt/float(cur.current_daily_ddd.sum()),'common_nic_coverage':Ct/float(cur.current_daily_nic.sum()),'fixed_2022_price_common_daily_nic':fixed,'current_entrant_daily_nic':entry_cost}
    decomp.append(record)
    for _,row in joined.iterrows():
        detail.append({'YEAR_MONTH':int(ym),**{k:row[k] for k in pkeys},'basket_status':str(row['_merge']),'base_daily_ddd':row.get('base_daily_ddd'),'base_daily_nic':row.get('base_daily_nic'),'base_nic_per_ddd':row.get('base_nic_per_ddd'),'current_daily_ddd':row.get('current_daily_ddd'),'current_daily_nic':row.get('current_daily_nic')})
decomp=pd.DataFrame(decomp);decomp.to_csv(OUT/'monthly_fixed_2022_price_decomposition.csv',index=False)
pd.DataFrame(detail).to_csv(OUT/'monthly_basket_detail.csv',index=False)
monthly=monthly.merge(decomp[['YEAR_MONTH','fixed_2022_price_common_daily_nic','common_ddd_coverage','common_nic_coverage']],on='YEAR_MONTH')
monthly.to_csv(OUT/'monthly_cost_summary.csv',index=False)
def pooled(label,x):
    days=float(x.days.sum());D=float(x.ddd.sum());I=float(x['items'].sum());C=float(x.nic.sum());A=float(x.actual_cost.sum())
    return {'period':label,'months':len(x),'calendar_days':days,'items':I,'ddd':D,'nic':C,'actual_cost':A,'daily_ddd':D/days,'daily_items':I/days,'daily_nic':C/days,'nic_per_ddd':C/D,'nic_per_item':C/I,'actual_cost_to_nic':A/C}
periods=[pooled('2022',monthly[monthly.YEAR_MONTH.between(202201,202212)]),pooled('2023',monthly[monthly.YEAR_MONTH.between(202301,202312)]),pooled('2024',monthly[monthly.YEAR_MONTH.between(202401,202412)]),pooled('2025_Jan_Apr',monthly[monthly.YEAR_MONTH.between(202501,202504)]),pooled('before_Nov2023',monthly[monthly.YEAR_MONTH<202311]),pooled('from_Nov2023',monthly[monthly.YEAR_MONTH>=202311])]
pd.DataFrame(periods).to_csv(OUT/'descriptive_periods.csv',index=False)
def native(x):
    if isinstance(x,(np.integer,)):return int(x)
    if isinstance(x,(np.floating,)):return float(x)
    raise TypeError(type(x))
summary={'status':'PASS','date_local':'2026-11-05','exploratory':True,'months':len(monthly),'oral_cells':len(oral),'all_route_cells':len(cost),'arithmetic_max_absolute_error':float(decomp.absolute_identity_error.max()),'min_common_ddd_coverage':float(decomp.common_ddd_coverage.min()),'min_common_nic_coverage':float(decomp.common_nic_coverage.min()),'cost_totals_oral':{k:float(oral[k].sum()) for k in ['nic','actual_cost','ddd','items']},'periods':periods,'april2025_decomposition':decomp[decomp.YEAR_MONTH==202504].iloc[0].to_dict(),'march_april2024':monthly[monthly.YEAR_MONTH.isin([202403,202404])].to_dict('records'),'limitations':['Descriptive unadjusted accounting, not policy effect','NIC is a basic drug-price measure, not total health-system spending','Actual Cost reporting definition changed April 2024','Fixed-price decomposition is ordered, descriptive and base-dependent; common basket plus entry/exit','No person-level clinical outcomes, cost effectiveness, QALY or net savings estimated'],'sources':{'frozen_presentation_month_sha256':h(ROOT/'ANALYSIS/data/valproate_presentation_month.csv'),'full_source_manifest_sha256':h(OUT/'full_source_manifest.json'),'cost_definition':'https://nhsbsa-opendata.s3-eu-west-2.amazonaws.com/English%20Prescribing%20Dataset%20Release%20Guidance%20v001.pdf','actual_cost_change':'https://opendata.nhsbsa.net/news/changes-to-actual-cost-reporting-calculation-pharmacy-only'}}
(OUT/'cost_results_summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2,default=native)+'\n',encoding='utf8')
print(json.dumps(summary,ensure_ascii=False,indent=2,default=native))
