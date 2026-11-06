"""Parse preserved UI text; does not retrieve remote data or fit models."""
from pathlib import Path
import json, csv, hashlib, re, datetime

ROOT = Path(__file__).resolve().parent
MONTHS = {m:i+1 for i,m in enumerate('Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec'.split())}

def month(s):
    m, y = s.split()
    return f'20{y}-{MONTHS[m]:02d}'

def ordinal(s):
    y,m=map(int,s.split('-'))
    return y*12+m

def fnv32(s):
    h=2166136261
    for c in s:
        h=((h^ord(c))*16777619)&0xffffffff
    return f'{h:x}'

def parse(name):
    source=ROOT/f'{name}_raw_ui_rows.json'
    j=json.loads(source.read_text(encoding='utf-8'))
    indicator=j['indicator']
    parsed=[]
    for text in j['rows']:
        fields=[x.strip() for x in text.splitlines() if x.strip()]
        assert len(fields)==(4 if indicator=='VPA1' else 2), fields
        start,end=fields[0].split('-')
        row=dict(indicator=indicator,period_label=fields[0],period_start_month=month(start),period_end_month=month(end),numerator=int(fields[1].replace(',','')),denominator=int(fields[2].replace(',','')) if indicator=='VPA1' else '',published_value=fields[-1],age_band=j['age_band'],sex='female',geography=j['geography'],provenance_status='UI_TEXT_EXTRACTION')
        assert ordinal(row['period_end_month'])-ordinal(row['period_start_month'])==2
        parsed.append(row)
    assert len({x['period_end_month'] for x in parsed})==len(parsed)
    assert all(ordinal(b['period_end_month'])-ordinal(a['period_end_month'])==1 for a,b in zip(parsed,parsed[1:]))
    study=[x for x in parsed if '2022-01'<=x['period_end_month']<='2025-04']
    assert len(study)==40
    for suffix,rows in [('history',parsed),('study_40_endmonths',study)]:
        with (ROOT/f'{name}_{suffix}.csv').open('w',encoding='utf-8-sig',newline='') as f:
            w=csv.DictWriter(f,fieldnames=list(parsed[0]));w.writeheader();w.writerows(rows)
    q=dict(indicator=indicator,total_rows=len(parsed),first_period=parsed[0]['period_label'],last_period=parsed[-1]['period_label'],study_rows=len(study),study_first=study[0]['period_label'],study_last=study[-1]['period_label'],unique_endmonths=True,continuous_months=True,three_month_width_all=True,missing_cells=0,suppressed_cells=0,raw_rows_fnv1a32=fnv32(json.dumps(j['rows'],ensure_ascii=False,separators=(',',':'))),original_csv_export_obtained=False,provenance_status='UI_TEXT_EXTRACTION',captured_at=j['captured_at'])
    if 'raw_rows_fnv1a32' in j:
        assert q['raw_rows_fnv1a32']==j['raw_rows_fnv1a32'], 'Saved raw rows differ from browser-side checksum'
    if indicator=='VPA1':
        expected={'Sep 18-Nov 18':(34188,15785959,'2.17'),'Nov 21-Jan 22':(24180,15713358,'1.54'),'Feb 25-Apr 25':(17597,15672560,'1.12'),'Jun 26-Aug 26':(15574,15228956,'1.02')}
        q['known_four_rows_match']=all((r['numerator'],r['denominator'],r['published_value'])==expected[r['period_label']] for r in parsed if r['period_label'] in expected)
        assert q['known_four_rows_match']
        q['all_rates_within_published_two_decimal_rounding']=all(abs(float(r['published_value'])-r['numerator']/r['denominator']*1000)<0.00501 for r in parsed)
        assert q['all_rates_within_published_two_decimal_rounding']
        assert q['raw_rows_fnv1a32']=='a412498f', 'Saved raw rows differ from browser-side checksum'
    q['assets']=[{'file':f.name,'bytes':f.stat().st_size,'sha256':hashlib.sha256(f.read_bytes()).hexdigest()} for f in [source,ROOT/f'{name}_history.csv',ROOT/f'{name}_study_40_endmonths.csv']]
    (ROOT/f'{name}_qa.json').write_text(json.dumps(q,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    return q

if __name__=='__main__':
    import sys
    for name in sys.argv[1:] or ['vpa1']:
        q=parse(name)
        print(json.dumps({k:v for k,v in q.items() if k!='assets'},ensure_ascii=False))
