"""Exploratory measurement supplement. Preserves the frozen primary analysis."""
from pathlib import Path
import json,hashlib,datetime,shutil
import numpy as np
import pandas as pd
from scipy.stats import t
import statsmodels.api as sm
from statsmodels.stats.sandwich_covariance import cov_hac

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
OUT=HERE/'measurement_components';OUT.mkdir(exist_ok=True)
def save(name,x):(OUT/name).write_text(json.dumps(x,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf8')
h=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
inputs={x:h(ROOT/x) for x in ['ANALYSIS/data/monthly_analysis.csv','ANALYSIS/data/valproate_presentation_month.csv','ANALYSIS/data/presentation_mapping.csv','ANALYSIS/results/models.json']}
save('input_manifest.json',{'recorded_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'files':inputs,'amendment_sha256':h(HERE/'AMENDMENT_BEFORE_ADDITIONAL_ANALYSIS.json')})
d=pd.read_csv(ROOT/'ANALYSIS/data/monthly_analysis.csv')
p=pd.read_csv(ROOT/'ANALYSIS/data/valproate_presentation_month.csv')
assert len(d)==40 and np.array_equal(d.time,np.arange(40))
# Same oral analysis population as the frozen preparation; inspect formula tags.
p=p[p.ddd.notna()].copy()
g=p.groupby('YEAR_MONTH')[['items','ddd','n_rows']].sum().reindex(d.YEAR_MONTH)
assert np.allclose(g['items'],d['items']) and np.allclose(g.ddd,d.ddd) and np.allclose(g.n_rows,d.rows)
assert (p['items']>0).all() and (p['ddd']>0).all()
p['period']=np.where(p.YEAR_MONTH<202311,'pre','post')
ag=p.groupby(['BNF_CODE','period'],observed=True).agg(items=('items','sum'),ddd=('ddd','sum')).unstack('period').fillna(0)
for period in ['pre','post']:
    ag[('share',period)]=ag[('items',period)]/ag[('items',period)].sum()
    ag[('ratio',period)]=np.where(ag[('items',period)]>0,ag[('ddd',period)]/ag[('items',period)],np.nan)
pre_i=ag[('items','pre')];post_i=ag[('items','post')]
common=(pre_i>0)&(post_i>0);entrant=(pre_i==0)&(post_i>0);exit_=(pre_i>0)&(post_i==0)
sp=ag[('share','pre')];sa=ag[('share','post')];qp=ag[('ratio','pre')];qa=ag[('ratio','post')]
within=np.where(common,(sp+sa)/2*(qa-qp),0)
mix=np.where(common,(qp+qa)/2*(sa-sp),0)
entry=np.where(entrant,sa*qa,0);leave=np.where(exit_,-sp*qp,0)
meta=p.sort_values('YEAR_MONTH').drop_duplicates('BNF_CODE',keep='last').set_index('BNF_CODE')
res=pd.DataFrame({'BNF_CODE':ag.index,'BNF_DESCRIPTION':meta.reindex(ag.index).BNF_DESCRIPTION,'form':meta.reindex(ag.index).form,'items_pre':pre_i,'items_post':post_i,'share_pre':sp,'share_post':sa,'ddd_per_item_pre':qp,'ddd_per_item_post':qa,'within_contribution':within,'mix_contribution':mix,'entry_contribution':entry,'exit_contribution':leave}).reset_index(drop=True)
res['total_contribution']=res[['within_contribution','mix_contribution','entry_contribution','exit_contribution']].sum(axis=1)
res.to_csv(OUT/'presentation_decomposition.csv',index=False)
pre=p[p.period=='pre'];post=p[p.period=='post']
R0=pre.ddd.sum()/pre['items'].sum();R1=post.ddd.sum()/post['items'].sum();change=R1-R0
assert abs(res.total_contribution.sum()-change)<1e-10
# Independently reconstruct the difference as sum of each product's contribution
# to DDDs per overall prescription item, without using the decomposition formula.
direct=ag[('ddd','post')]/post['items'].sum()-ag[('ddd','pre')]/pre['items'].sum()
assert np.allclose(res.total_contribution,direct,atol=1e-12)
summary={'pre_months':22,'post_months':18,'oral_cells':len(p),'presentations':len(ag),'common_presentations':int(common.sum()),'entrants':int(entrant.sum()),'exits':int(exit_.sum()),'pre_ddd_per_item':R0,'post_ddd_per_item':R1,'absolute_change':change,'relative_change_percent':100*(R1/R0-1),'pre_items':float(pre['items'].sum()),'post_items':float(post['items'].sum()),'common_item_share_pre':float(sp[common].sum()),'common_item_share_post':float(sa[common].sum()),'components':{k:{'ddd_per_item':float(res[k+'_contribution'].sum()),'percent_of_net_change':float(100*res[k+'_contribution'].sum()/change)} for k in ['within','mix','entry','exit']},'verification_max_product_identity_error':float(np.max(np.abs(res.total_contribution.to_numpy()-direct.to_numpy()))),'interpretation':'Symmetric exact decomposition of pooled period DDD/item ratios; not a causal decomposition or a change in individual dose/treatment duration. Product-code entry/exit may include coding changes.'}
save('decomposition_summary.json',summary)
# All paired ratios use the same monthly observations and exactly the same X.
ys={'ddd_per_item':np.log(d.ddd/d['items']),'items_per_row':np.log(d['items']/d.rows),'ddd_per_row':np.log(d.ddd/d.rows)}
assert np.allclose(ys['ddd_per_item']+ys['items_per_row'],ys['ddd_per_row'],atol=1e-14)
records=[];curves=[];details=[];checks=[]
for br in [202311,202402]:
    k=int(d.loc[d.YEAR_MONTH==br,'time'].iloc[0]);time=d.time.to_numpy(float)
    X=np.column_stack([np.ones(40),time,time>=k,np.maximum(time-k,0)]+[(d.month==m).astype(int) for m in range(2,13)])
    assert np.linalg.matrix_rank(X)==X.shape[1]
    n,q=X.shape;df=n-q;crit=t.ppf(.975,df);L=np.zeros(q);L[2:4]=[1,39-k]
    C=X.copy();C[:,2:4]=0;coeff={}
    for name,y in ys.items():
        y=np.asarray(y);b=np.linalg.lstsq(X,y,rcond=None)[0];coeff[name]=b
        residual=y-X@b;z=X*residual[:,None];bread=np.linalg.inv(X.T@X)
        other=sm.OLS(y,X).fit()
        for lag in [1,3,6]:
            meat=z.T@z
            for j in range(1,lag+1):
                cross=z[j:].T@z[:-j];meat+=(1-j/(lag+1))*(cross+cross.T)
            V=bread@meat@bread*n/df
            Vs=cov_hac(other,nlags=lag,use_correction=True)
            assert np.allclose(V,Vs,rtol=1e-7,atol=1e-12)
            estimate=float(L@b);se=float(np.sqrt(L@V@L))
            row={'measure':name,'breakpoint':br,'HAC_lag':lag,'n_months':n,'parameters':q,'residual_df':df,'terminal_log_difference':estimate,'se_log':se,'terminal_percent_ratio_difference':100*np.expm1(estimate),'lower':100*np.expm1(estimate-crit*se),'upper':100*np.expm1(estimate+crit*se),'role':'primary_exploratory' if br==202311 and lag==3 else 'sensitivity','covariance_max_difference_vs_statsmodels':float(np.max(np.abs(V-Vs)))}
            records.append(row)
            if lag==3:details.append({**row,'coefficients':b.tolist(),'covariance':V.tolist(),'residual_acf':sm.tsa.acf(residual,nlags=6,fft=False).tolist()})
        for i in range(n):curves.append({'measure':name,'breakpoint':br,'YEAR_MONTH':int(d.YEAR_MONTH.iloc[i]),'observed_ratio':float(np.exp(y[i])),'fitted_geometric_ratio':float(np.exp(X[i]@b)),'prior_trend_projection':float(np.exp(C[i]@b))})
    err=float(np.max(np.abs(coeff['ddd_per_item']+coeff['items_per_row']-coeff['ddd_per_row'])))
    assert err<1e-12;checks.append({'breakpoint':br,'max_coefficient_identity_error':err})
pd.DataFrame(records).to_csv(OUT/'paired_log_ratio_contrasts.csv',index=False)
pd.DataFrame(curves).to_csv(OUT/'paired_log_ratio_curves.csv',index=False)
save('paired_log_ratio_details.json',{'amendment':'Exploratory 2026-11-05, after primary results known','method':'OLS log ratios; Bartlett Newey-West lag3, n/(n-p) covariance correction and t(df=25) intervals; lags1/6 and February break sensitivity','interpretation':'Percent difference in the fitted ratio relative to projected pre-break ratio trend. This is not a significance test comparing frozen separate-outcome GLS terminal percentages. Short-series uncertainty remains. Exponentiated fitted logs describe geometric ratios.','details':details,'identity_checks':checks})
assert all(h(ROOT/k)==v for k,v in inputs.items())
save('verification.json',{'status':'PASS','frozen_inputs_unchanged':True,'aggregation_matches_frozen_primary':True,'decomposition_identity':True,'paired_covariance_independently_matches_statsmodels':True,'log_identity_checks':checks})
print(json.dumps({'decomposition':summary,'primary_ratio_results':[r for r in records if r['role']=='primary_exploratory']},ensure_ascii=False,indent=2))
