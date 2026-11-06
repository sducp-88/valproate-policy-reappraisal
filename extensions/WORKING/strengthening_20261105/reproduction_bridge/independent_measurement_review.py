from pathlib import Path
import json,hashlib
import pandas as pd
import numpy as np
import statsmodels.api as sm

OUT=Path(__file__).resolve().parent;ROOT=OUT.parents[2];MODULE=OUT.parent/'measurement_components'
h=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
d=pd.read_csv(ROOT/'ANALYSIS/data/monthly_analysis.csv')
p=pd.read_csv(ROOT/'ANALYSIS/data/valproate_presentation_month.csv')
p=p[p.form.isin(['oral_solid','oral_liquid'])].copy()
assert len(p)==2200 and p.BNF_CODE.nunique()==58
pre=p[p.YEAR_MONTH<202311].groupby('BNF_CODE')[['items','ddd']].sum()
post=p[p.YEAR_MONTH>=202311].groupby('BNF_CODE')[['items','ddd']].sum()
common=pre.index.intersection(post.index);entrants=post.index.difference(pre.index);exits=pre.index.difference(post.index)
w0=pre.loc[common,'items']/pre['items'].sum();w1=post.loc[common,'items']/post['items'].sum()
q0=pre.loc[common,'ddd']/pre.loc[common,'items'];q1=post.loc[common,'ddd']/post.loc[common,'items']
# Counterfactual-weight sums implement the two orders of a symmetric decomposition.
a=float((w0*q0).sum());b=float((w0*q1).sum());c=float((w1*q0).sum());e=float((w1*q1).sum())
components={'within':.5*((b-a)+(e-c)),'mix':.5*((c-a)+(e-b)),'entry':float(post.loc[entrants,'ddd'].sum()/post['items'].sum()),'exit':float(-pre.loc[exits,'ddd'].sum()/pre['items'].sum())}
saved=json.loads((MODULE/'decomposition_summary.json').read_text(encoding='utf8'))
diffs={k:abs(v-saved['components'][k]['ddd_per_item']) for k,v in components.items()}
assert max(diffs.values())<1e-12
contrast=pd.read_csv(MODULE/'paired_log_ratio_contrasts.csv')
checks=[]
for br in [202311,202402]:
    k=int(d.loc[d.YEAR_MONTH==br,'time'].iloc[0]);tt=d.time.to_numpy();n=len(d)
    x=np.column_stack([np.ones(n),tt,(tt>=k).astype(int),np.maximum(tt-k,0)]+[(d.month==i).to_numpy().astype(int) for i in range(2,13)])
    L=np.zeros(x.shape[1]);L[2:4]=[1,tt[-1]-k]
    for measure,numerator,denominator in [('ddd_per_item','ddd','items'),('items_per_row','items','rows'),('ddd_per_row','ddd','rows')]:
        y=np.log(d[numerator]/d[denominator]).to_numpy()
        fit=sm.OLS(y,x).fit(cov_type='HAC',cov_kwds={'maxlags':3,'use_correction':True},use_t=True)
        test=fit.t_test(L);estimate=float(np.asarray(test.effect).item());lo,hi=map(float,test.conf_int().ravel())
        got=np.array([100*np.expm1(estimate),100*np.expm1(lo),100*np.expm1(hi)])
        row=contrast[(contrast.measure==measure)&(contrast.breakpoint==br)&(contrast.HAC_lag==3)].iloc[0]
        want=np.array([row.terminal_percent_ratio_difference,row.lower,row.upper]);err=float(np.max(abs(got-want)));assert err<1e-8
        checks.append({'measure':measure,'breakpoint':br,'max_abs_percent_interval_difference':err})
findings=[
{'item':'Population and periods','status':'PASS','detail':'Explicit oral-form filter gives2200cells/58presentations and agrees with the ddd-not-null source selection;57common,0entrants,1exit. Different22/18-month periods are pooled by prescription items as declared.'},
{'item':'Symmetric decomposition','status':'PASS','detail':'Two-order counterfactual-weight calculation independently reproduces within,composition,entry and exit contributions. The net period ratio difference is exactly recovered.'},
{'item':'Paired statistical estimand','status':'PASS_WITH_REQUIRED_INTERPRETATION','detail':'Modelling log(DDD/items) uses same-month paired data and captures numerator-denominator covariance. exp(Lbeta)-1 is a ratio change relative to continued pre-break log-ratio trend; it is not a difference between the frozen separately fitted GLS percentages or a formal retest of them.'},
{'item':'HAC implementation and intervals','status':'PASS','detail':'OLS point estimates, Bartlett Newey-West covariance with n/(n-p), residualdf25 and t intervals were independently matched using statsmodels OLS robust-results t_test for lag3 and both breakpoints.'},
{'item':'Time dependence and mean specification','status':'PASS_WITH_LIMITATION','detail':'Only40months/15coefficients. HAC changes covariance, not fitted mean; lag sensitivity does not prove adequate finite-sample interval coverage. February DDD/item lag1 ACF is approximately0.699 (lag2≈0.425), and DDD/row lag1≈0.604. These must remain limitations, not be described as resolved by HAC.'},
{'item':'Timing sensitivity','status':'RETAIN_PROMINENTLY','detail':'November DDD/item +7.50%(2.95,12.24) versus February +0.95%(-7.10,9.70) limits attribution to the November alert or packaging policy. A nonsignificant February result is not equivalence and does not refute descriptive period decomposition.'},
{'item':'Multiple ratios and correlated evidence','status':'RETAIN_PROMINENTLY','detail':'DDD/row is algebraically related to DDD/item and items/row, so the three ratios are not independent replications. November items/row interval changes from spanning0 at lag3 to just above0 at lag6; do not select the lag6 result as confirmation.'},
{'item':'Meaning of94.92%','status':'RETAIN_PROMINENTLY','detail':'94.92% is the share of an exact observed pooled-period net change accounted for by the within-BNF-presentation term, not a causal attributable fraction, person-level dose change, proportion of patients, or estimated policy effect. No sampling CI is attached to this finite aggregate identity. Share percentages depend on chosen periods/aggregation, and components can exceed100% or be negative in other datasets.'},
{'item':'Cross-period versus temporal estimand','status':'PASS_WITH_REQUIRED_INTERPRETATION','detail':'Raw pre/post DDD/item increases8.90%; modelled terminal ratio difference7.50% has a different denominator and time-trend comparison. Do not label the former as an ITS effect or claim the two estimates independently validate each other.'},
{'item':'Fixed strengths and product coding','status':'PASS_WITH_LIMITATION','detail':'Within means the same BNFpresentation code, potentially combining practices and underlying dispensing circumstances. Entrants/exits may be coding changes. Check any code-to-strength changes before attributing within movement to pack size or repeat dispensing.'}
]
review={'date_local':'2026-11-05','status':'PASS_WITH_INTERPRETIVE_LIMITATIONS','reviewer':'novelty_assessment independent agent','scope':'Only decomposition and paired-log-ratio implementation and interpretation; no original-primary-model modification','source_hashes':{str(f.relative_to(ROOT)):h(f) for f in [OUT.parent/'analyze_measurement_components.py',MODULE/'decomposition_summary.json',MODULE/'presentation_decomposition.csv',MODULE/'paired_log_ratio_contrasts.csv',MODULE/'paired_log_ratio_details.json',MODULE/'verification.json']},'independent_decomposition_max_absolute_difference':max(diffs.values()),'independent_statsmodels_robust_ttest_checks':checks,'findings':findings,'recommended_integration':'Use DDD/item as the clinically interpretable exploratory ratio; give February sensitivity alongside November. Keep rows-related ratios as supporting measurement diagnostics, preserve all executed results in supplement. Describe within-presentation94.9% as arithmetic decomposition only. No added significance tests are required to claim the finite sum identity.'}
(OUT/'independent_measurement_review.json').write_text(json.dumps(review,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print(json.dumps({'status':review['status'],'decomposition_max_error':max(diffs.values()),'contrast_checks':checks},ensure_ascii=False,indent=2))
