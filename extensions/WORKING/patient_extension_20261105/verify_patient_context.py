"""Independently recompute patient descriptive outputs from raw UI and frozen month data, without root functions."""
from pathlib import Path
import json,csv,datetime,hashlib
from decimal import Decimal
D=Decimal;BASE=Path(__file__).resolve().parent;ROOT=BASE.parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def nextmonth(t):return datetime.date(t.year+1,1,1) if t.month==12 else datetime.date(t.year,t.month+1,1)
def prevmonth(t):return datetime.date(t.year-1,12,1) if t.month==1 else datetime.date(t.year,t.month-1,1)
def dat(s):return datetime.datetime.strptime(s,'%b %y').date().replace(day=1)
def fmt(t):return t.strftime('%Y-%m')
monthly_path=ROOT/'ANALYSIS/data/monthly_analysis.csv'
frozen=json.loads((BASE/'frozen_inputs_manifest.json').read_text(encoding='utf8'))
assert sha(monthly_path)==frozen['ANALYSIS/data/monthly_analysis.csv']
monthly={datetime.datetime.strptime(x['YEAR_MONTH'],'%Y%m').date():x for x in csv.DictReader(monthly_path.open(encoding='utf-8-sig',newline=''))}
assert len(monthly)==40
raw=json.loads((BASE/'acquisition/vpa1_raw_ui_rows.json').read_text(encoding='utf8'))
# Independently verify all 94 raw rows before restricting the analysis period.
from decimal import ROUND_HALF_UP
history=list(csv.DictReader((BASE/'acquisition/vpa1_history.csv').open(encoding='utf-8-sig',newline='')))
assert len(history)==len(raw['rows'])==94
ends=[]
for rawline,saved in zip(raw['rows'],history):
 line=[x.strip() for x in rawline.splitlines() if x.strip()];assert len(line)==4
 st,en=map(dat,line[0].split('-'));assert nextmonth(nextmonth(st))==en
 n=int(line[1].replace(',',''));den=int(line[2].replace(',',''));assert 0<=n<den
 rate=D(1000)*n/den;assert rate.quantize(D('0.01'),rounding=ROUND_HALF_UP)==D(line[3])
 assert saved['period_label']==line[0] and saved['period_start_month']==fmt(st) and saved['period_end_month']==fmt(en)
 assert int(saved['numerator'])==n and int(saved['denominator'])==den and D(saved['published_value'])==D(line[3])
 assert saved['indicator']=='VPA1' and saved['age_band']=='13-54' and saved['sex']=='female' and saved['geography']=='National'
 ends.append(en)
assert len(set(ends))==94 and all(nextmonth(a)==b for a,b in zip(ends,ends[1:]))
ind=[]
for s in raw['rows']:
    line=[z.strip() for z in s.splitlines() if z.strip()];st,en=map(dat,line[0].split('-'))
    if st<datetime.date(2022,1,1) or en>datetime.date(2025,4,1):continue
    dates=[st,nextmonth(st),nextmonth(nextmonth(st))];assert dates[-1]==en
    ms=[monthly[z] for z in dates];days=[(nextmonth(z)-z).days for z in dates]
    assert all(int(m['days'])==n for m,n in zip(ms,days))
    nd=sum(days);N=int(line[1].replace(',',''));den=int(line[2].replace(',',''));ddd=sum(D(m['ddd']) for m in ms);items=sum(int(m['items']) for m in ms);rows=sum(int(m['rows']) for m in ms)
    ind.append({'period_label':line[0],'period_start_month':fmt(st),'period_end_month':fmt(en),'numerator':D(N),'denominator':D(den),'calculated_rate_per_1000':D(1000)*N/den,'window_days':D(nd),'oral_ddd':ddd,'oral_items':D(items),'oral_rows':D(rows),'oral_daily_ddd':ddd/nd,'oral_daily_items':D(items)/nd,'oral_daily_rows':D(rows)/nd,'quarter':st.month in (1,4,7,10)})
assert len(ind)==38
q=[a for a in ind if a['quarter']];assert len(q)==13
numkeys=['numerator','denominator','calculated_rate_per_1000','window_days','oral_ddd','oral_items','oral_rows','oral_daily_ddd','oral_daily_items','oral_daily_rows']
maxerr={k:D(0) for k in numkeys}
for filename,expected in [('patient_context_38_windows.csv',ind),('patient_context_13_quarters.csv',q)]:
    actual=list(csv.DictReader((BASE/'analysis'/filename).open(encoding='utf-8-sig',newline='')));assert len(actual)==len(expected)
    for a,b in zip(expected,actual):
        assert all(a[k]==b[k] for k in ('period_label','period_start_month','period_end_month'))
        assert (b['nonoverlapping_calendar_quarter']=='True')==a['quarter']
        for k in numkeys:
            error=abs(a[k]-D(b[k]));maxerr[k]=max(maxerr[k],error)
            tol=D('0') if k in ('numerator','denominator','window_days','oral_items','oral_rows') else (D('1e-12') if k=='calculated_rate_per_1000' else D('1e-7'))
            assert error<=tol,(filename,a['period_label'],k,error)
    assert actual[-1]['window_role']==('latest_overlapping_window_not_extra_quarter' if len(actual)==38 else 'calendar_quarter')
assert [int(a['window_days']) for a in q if a['period_start_month']=='2024-01']==[91]
assert int(monthly[datetime.date(2024,2,1)]['days'])==29
summary=json.loads((BASE/'analysis/patient_context_summary.json').read_text(encoding='utf8'))
recomputed=[]
for a in summary['comparisons']:
    k=a['measure'];v0=q[0][k];v1=q[-1][k];vlast=ind[-1][k];pct=D(100)*(v1/v0-1)
    exp={'Q1_2022':v0,'Q1_2025':v1,'absolute_change_Q1_2022_to_Q1_2025':v1-v0,'percent_change_Q1_2022_to_Q1_2025':pct,'Feb_Apr_2025':vlast}
    for field,value in exp.items():assert abs(D(str(a[field]))-value)<D('1e-7'),(k,field)
    recomputed.append({'measure':k,**{n:str(v) for n,v in exp.items()}})
checkpath=BASE/'portable_patient_check.json';check={'status':'PASS','independent_verification':'Raw VPA1 UI text and frozen month data independently reconstructed; root functions not imported. No model or causal effect fitted.'}
check['descriptive_recomputation']={'status':'PASS','method':'Independently parsed original VPA1 UI text and frozen monthly CSV with Decimal; days computed as date differences to next month. Did not import root analyse_patient_context.py or acquisition functions.','all_38_window_rows_match':True,'all_13_quarter_rows_match':True,'max_absolute_numeric_differences':{k:str(v) for k,v in maxerr.items()},'leap_year_2024':{'february_days':29,'Q1_days':91,'passed':True},'all_fixed_endpoint_comparisons_match':True,'recomputed_comparisons':recomputed,'frozen_monthly_sha256':sha(monthly_path),'script_sha256':sha(Path(__file__)),'output_hashes':{f:sha(BASE/'analysis'/f) for f in ['patient_context_38_windows.csv','patient_context_13_quarters.csv','patient_context_summary.json']}}
check['scope_exclusion']='Does not certify source clinical validity, national unique-person counts, historical linkage completeness or causal interpretation. Excluded indicator series are not analysed.'
checkpath.write_text(json.dumps(check,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print(json.dumps({'status':'PASS','all_38_and_13_match':True,'leap_year_days':91,'comparisons':recomputed},ensure_ascii=False,indent=2))
