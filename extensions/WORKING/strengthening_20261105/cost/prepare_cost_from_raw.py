"""Rebuild cost aggregates from the40 supplied national raw responses; offline only."""
from pathlib import Path
import json,hashlib,sys
import pandas as pd
OUT=Path(__file__).resolve().parent;ROOT=OUT.parents[2]
h=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
manifest=json.loads((OUT/'full_source_manifest.json').read_text(encoding='utf8'))
records=manifest['resources'];MODE='full';MONTHS=[x['month'] for x in records]
assert len(records)==40 and manifest['complete']
for rec in records:assert h(OUT/rec['file'])==rec['sha256']
data=[]
for rec in records:
    x=json.loads((OUT/rec['file']).read_bytes())['result'];x=x.get('result',x);data.extend(x['records'])
new=pd.DataFrame(data)
numeric=['YEAR_MONTH','n_rows','items','total_quantity','quantity_times_items','nic','actual_cost','nic_null_rows','actual_cost_null_rows']
for key in numeric:new[key]=pd.to_numeric(new[key],errors='raise')
keys=['YEAR_MONTH','BNF_CODE','BNF_DESCRIPTION']
assert not new.duplicated(keys).any()
frozen=pd.read_csv(ROOT/'ANALYSIS/data/valproate_presentation_month.csv')
frozen=frozen[frozen.YEAR_MONTH.astype(str).isin(MONTHS)]
paired=new.merge(frozen,on=keys,how='outer',suffixes=('_new','_frozen'),indicator=True,validate='one_to_one')
checks={'all_cells_matched':bool(paired._merge.eq('both').all()),'no_missing_costs':bool(new[['nic','actual_cost']].notna().all().all()),'no_source_null_cost_rows':bool(new[['nic_null_rows','actual_cost_null_rows']].eq(0).all().all()),'nonnegative_costs':bool(new[['nic','actual_cost']].ge(0).all().all()),'arithmetic_identity':bool(new.total_quantity.eq(new.quantity_times_items).all())}
for field in ['items','total_quantity','n_rows']:
    checks[field+'_exact_match_frozen']=bool(paired[field+'_new'].eq(paired[field+'_frozen']).all())
validation={'status':'PASS' if all(checks.values()) else 'STOP_REQUIRES_REVIEW','mode':MODE,'months':MONTHS,'cells':len(new),'checks':checks,'frozen_source':'ANALYSIS/data/valproate_presentation_month.csv','frozen_sha256':h(ROOT/'ANALYSIS/data/valproate_presentation_month.csv'),'nic_total_all_routes':float(new.nic.sum()),'actual_cost_total_all_routes':float(new.actual_cost.sum()),'interpretation':'NIC and Actual Cost are supplied summed amounts, never multiplied again by ITEMS.'}
new.to_csv(OUT/f'{MODE}_all_route_presentation_month.csv',index=False)
(OUT/f'{MODE}_validation.json').write_text(json.dumps(validation,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print(json.dumps(validation,ensure_ascii=False),flush=True)
if validation['status']!='PASS':sys.exit(3)
