"""Offline reconstruction from the accompanying public national aggregates.
No network access or patient-level data are needed. Run in this file's directory.
"""
from pathlib import Path
import json,calendar
import numpy as np
import pandas as pd
ROOT=Path(__file__).resolve().parent
out=ROOT/'ANALYSIS/data';out.mkdir(parents=True,exist_ok=True)
(ROOT/'ANALYSIS/results').mkdir(exist_ok=True);(ROOT/'FIGURES').mkdir(exist_ok=True)
m=pd.read_csv(ROOT/'07_Supplementary_Data_2_Mapping.csv')
v=pd.read_csv(ROOT/'08_Supplementary_Data_3_Aggregates.csv')
z=pd.read_csv(ROOT/'09_Supplementary_Data_4_Release_Comparison.csv')
assert len(m)==64 and len(v)==2393 and len(z)==4044
assert z['_merge'].eq('both').all()
assert (z.items_epd==z.items_snomed).all()
assert (z.total_quantity_epd==z.total_quantity_snomed).all()
assert (z.total_quantity_epd==z.quantity_times_items_epd).all()
assert (z.n_rows_epd!=z.n_rows_snomed).sum()==572
val=z.CHEMICAL_SUBSTANCE_BNF_DESCR_epd.isin(['Sodium valproate','Valproic acid'])
assert val.sum()==2393 and (z.loc[val,'n_rows_epd']!=z.loc[val,'n_rows_snomed']).sum()==120
keys=['BNF_CODE','BNF_DESCRIPTION','CHEMICAL_SUBSTANCE_BNF_DESCR']
v=v.drop(columns=['form','g_per_unit','ddd','unweighted_ddd']).merge(m,on=keys,validate='many_to_one')
v['ddd']=v.total_quantity*v.g_per_unit/1.5
v['unweighted_ddd']=v.quantity_unweighted*v.g_per_unit/1.5
oral=v[v.form.str.startswith('oral')].copy()
assert len(oral)==2200 and (oral.adq>0).all()
assert (abs(oral.ddd-.8*oral.adq)/oral.ddd).max()<1e-6
d=oral.groupby('YEAR_MONTH').agg(items=('items','sum'),rows=('n_rows','sum'),ddd=('ddd','sum'),unweighted_ddd=('unweighted_ddd','sum')).reset_index()
d['days']=[calendar.monthrange(int(str(x)[:4]),int(str(x)[4:]))[1] for x in d.YEAR_MONTH]
d['time']=np.arange(40);d['month']=d.YEAR_MONTH%100
d['daily_ddd']=d.ddd/d.days;d['ddd_30_4']=d.ddd/30.4
d['daily_items']=d['items']/d.days;d['daily_rows']=d.rows/d.days
d['ddd_per_item']=d.ddd/d['items'];d['items_per_row']=d['items']/d.rows
d['unweighted_daily']=d.unweighted_ddd/d.days
for name,sub in [('sodium_only',oral[oral.CHEMICAL_SUBSTANCE_BNF_DESCR.eq('Sodium valproate')]),('solid_only',oral[oral.form.eq('oral_solid')])]:
    d[name]=d.YEAR_MONTH.map(sub.groupby('YEAR_MONTH').ddd.sum())/d.days
ref=pd.read_csv(ROOT/'06_Supplementary_Data_1_Monthly.csv')
assert list(d.columns)==list(ref.columns)
assert np.allclose(d.to_numpy(),ref.to_numpy(),rtol=1e-12,atol=1e-8)
assert np.allclose(d.daily_ddd,d.daily_rows*d.items_per_row*d.ddd_per_item,rtol=1e-12)
d.to_csv(out/'monthly_analysis.csv',index=False)
m.to_csv(out/'presentation_mapping.csv',index=False)
v.to_csv(out/'valproate_presentation_month.csv',index=False)
z.to_csv(out/'parallel_release_comparison.csv',index=False)
(ROOT/'ANALYSIS/results/reconstruction_check.json').write_text(json.dumps({'pass':True,'months':40,'valproate_cells':2393,'oral_cells':2200,'all_descriptor_cells':4044,'oral_items':int(oral['items'].sum()),'oral_rows':int(oral.n_rows.sum()),'oral_ddd':float(oral.ddd.sum())},indent=2),encoding='utf8')
print('PASS: monthly data, mapping, arithmetic and both release comparisons reproduced.')
