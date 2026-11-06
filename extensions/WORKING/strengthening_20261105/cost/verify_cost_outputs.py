"""Independent Decimal source summation and delivered-table consistency checks."""
from pathlib import Path
from decimal import Decimal
import csv,hashlib,json,datetime,platform
OUT=Path(__file__).resolve().parent;ROOT=OUT.parents[2]
h=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
manifest=json.loads((OUT/'full_source_manifest.json').read_text(encoding='utf8'))
frozen=list(csv.DictReader((ROOT/'ANALYSIS/data/valproate_presentation_month.csv').open(encoding='utf8')))
oral_keys={(x['YEAR_MONTH'],x['BNF_CODE'],x['BNF_DESCRIPTION']) for x in frozen if x['form'] in ['oral_solid','oral_liquid']}
raw_totals={};allcells=0;oralcells=0
for rec in manifest['resources']:
    p=OUT/rec['file'];assert h(p)==rec['sha256']
    z=json.loads(p.read_text(encoding='utf8'),parse_float=Decimal)['result'];z=z.get('result',z)
    month=rec['month'];tot={k:Decimal(0) for k in ['nic','actual_cost','items','total_quantity']}
    allcells+=len(z['records'])
    for row in z['records']:
        key=(str(row['YEAR_MONTH']),row['BNF_CODE'],row['BNF_DESCRIPTION'])
        if key in oral_keys:
            oralcells+=1
            for k in tot:tot[k]+=Decimal(str(row[k]))
    raw_totals[month]=tot
monthly=list(csv.DictReader((OUT/'monthly_cost_summary.csv').open(encoding='utf8')))
max_delta=Decimal(0)
for row in monthly:
    for k in ['nic','actual_cost','items']:
        delta=abs(Decimal(row[k])-raw_totals[row['YEAR_MONTH']][k]);max_delta=max(max_delta,delta)
        assert delta<Decimal('0.0000001'),(row['YEAR_MONTH'],k,delta)
    for k in ['nic','actual_cost','items','ddd']:
        assert abs(Decimal(row['daily_'+k])-Decimal(row[k])/Decimal(row['days']))<Decimal('0.0000001')
assert len(monthly)==40 and allcells==2393 and oralcells==2200
rows=list(csv.DictReader((OUT/'monthly_fixed_2022_price_decomposition.csv').open(encoding='utf8')))
for row in rows:
    calc=sum(Decimal(row[k]) for k in ['common_volume_component','common_mix_component','common_price_component','entry_component','exit_component'])
    direct=Decimal(row['current_daily_nic'])-Decimal(row['base_daily_nic'])
    assert abs(calc-direct)<Decimal('0.0000001')
state={'status':'PASS','date_local':'2026-11-05','verified_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'runtime':platform.python_version(),'checks':['40 raw-source hashes','independent Decimal raw source to oral monthly sum','oral scope exactly matches frozen 2200-cell set','calendar-day normalisation','five-component accounting identity','unchanged frozen input hash'],'all_route_cells':allcells,'oral_cells':oralcells,'max_source_sum_difference_gbp':str(max_delta),'figure_visual_review':{'included':False,'note':'Portable numerical replay does not create or claim visual review of figures'},'frozen_sha256':h(ROOT/'ANALYSIS/data/valproate_presentation_month.csv'),'unchanged_frozen_verified':h(ROOT/'ANALYSIS/data/valproate_presentation_month.csv')==json.loads((OUT/'full_validation.json').read_text(encoding='utf8'))['frozen_sha256'],'no_new_scientific_claim':['No causal cost-saving estimate','No cost-effectiveness or QALY analysis','No claim April2024 reporting change explains observed valproate cost trajectory']}
assert state['unchanged_frozen_verified']
(OUT/'cost_audit.json').write_text(json.dumps(state,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
files=[p for p in OUT.rglob('*') if p.is_file() and 'matplotlib_cache' not in p.parts and p.name!='MANIFEST_SHA256.csv' and '__pycache__' not in p.parts]
with (OUT/'MANIFEST_SHA256.csv').open('w',encoding='utf-8-sig',newline='') as f:
    w=csv.DictWriter(f,fieldnames=['file','bytes','sha256']);w.writeheader()
    for p in sorted(files):w.writerow({'file':p.relative_to(OUT).as_posix(),'bytes':p.stat().st_size,'sha256':h(p)})
print(json.dumps({'status':'PASS','files':len(files),'source_bytes':sum((OUT/x['file']).stat().st_size for x in manifest['resources']),'max_source_sum_difference_gbp':str(max_delta),'frozen_unchanged':True}))
