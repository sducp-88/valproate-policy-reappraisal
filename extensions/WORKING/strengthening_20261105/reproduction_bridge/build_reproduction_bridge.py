"""Exploratory published-to-reconstructed bridge. Never writes frozen analysis files."""
from pathlib import Path
import csv,json,hashlib,datetime
import numpy as np
import pandas as pd
from scipy.stats import t as student_t

OUT=Path(__file__).resolve().parent
ROOT=OUT.parents[2]
AMEND=OUT.parent/'AMENDMENT_BEFORE_ADDITIONAL_ANALYSIS.json'
amend=json.loads(AMEND.read_text(encoding='utf8'))
assert amend['status']=='exploratory_amendment_recorded_before_new_module_results'
assert 'reproduction_bridge' in amend['modules']
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(name,obj):(OUT/name).write_text(json.dumps(obj,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf8')
def csvsave(name,rows):
    with (OUT/name).open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
inputs=[AMEND,ROOT/'ANALYSIS/data/monthly_analysis.csv',ROOT/'ANALYSIS/data/valproate_presentation_month.csv',ROOT/'ANALYSIS/results/models.json',ROOT/'ANALYSIS/results/independent_verification.json',ROOT/'ANALYSIS/scripts/verify_models.py']
optional_sources=[ROOT/'QA/galloway_full_text.txt',ROOT/'SOURCE/literature/galloway_vor.pdf']
inputs += [p for p in optional_sources if p.exists()]
baseline={p.relative_to(ROOT).as_posix():sha(p) for p in inputs}
d=pd.read_csv(inputs[1]);p=pd.read_csv(inputs[2],dtype={'BNF_CHEMICAL_SUBSTANCE':str})
fits=json.loads(inputs[3].read_text())['fits']
prior_verify=json.loads(inputs[4].read_text())
assert len(d)==40 and (d.time.to_numpy()==np.arange(40)).all()
assert d.YEAR_MONTH.iloc[0]==202201 and d.YEAR_MONTH.iloc[-1]==202504
oral=p[p.form.isin(['oral_solid','oral_liquid'])]
na=oral[oral.BNF_CHEMICAL_SUBSTANCE=='0408010W0'].groupby('YEAR_MONTH').ddd.sum().reindex(d.YEAR_MONTH).to_numpy()/30.4
all30=d.ddd.to_numpy()/30.4
assert np.allclose(all30,d.ddd_30_4.to_numpy(),rtol=1e-12,atol=1e-8)
assert np.allclose(na,d.sodium_only.to_numpy()*d.days.to_numpy()/30.4,rtol=1e-12,atol=1e-8)
ts=d.time.to_numpy(); post=(ts>=22).astype(int);after=np.maximum(ts-22,0)
source_url='https://qualitysafety.bmj.com/content/early/2025/11/25/bmjqs-2025-019415'
supp_url='https://qualitysafety.bmj.com/content/qhc/early/2025/11/25/bmjqs-2025-019415/DC1/embed/inline-supplementary-material-1.pdf?download=true'

def design(last_season_month):
    labels=['intercept','time','post','after']+[f'month{x}' for x in range(2,last_season_month+1)]
    x=np.column_stack([np.ones(40),ts,post,after]+[(d.month.to_numpy()==x).astype(int) for x in range(2,last_season_month+1)])
    assert np.linalg.matrix_rank(x)==x.shape[1]
    return x,labels

def summarize(b,v,x,mean):
    df=40-x.shape[1];crit=float(student_t.ppf(.975,df))
    def lin(l):
        est=float(l@b);se=float(np.sqrt(l@v@l));return {'estimate':est,'se':se,'lower':est-crit*se,'upper':est+crit*se}
    out={}
    for name,idx in [('pre_slope',[1]),('immediate_level',[2]),('slope_change',[3]),('post_slope',[1,3])]:
        l=np.zeros(len(b));l[idx]=1;out[name]=lin(l)
    l=np.zeros(len(b));l[2:4]=[1,17];x0=x[-1].copy();x0[2:4]=0
    den=float(x0@b);num=float(l@b);g=100*(l/den-num*x0/den**2);se=float(np.sqrt(g@v@g));pct=100*num/den
    out.update(terminal_difference=lin(l),terminal_counterfactual=den,terminal_fitted=float(x[-1]@b),terminal_percent={'estimate':pct,'se':se,'lower':pct-crit*se,'upper':pct+crit*se},mean_outcome=float(mean),observations=40,parameters=x.shape[1],residual_df=df)
    out['descriptive_coefficients_percent_of_overall_mean']={k:100*out[k]['estimate']/float(mean) for k in ['pre_slope','immediate_level','slope_change','post_slope']}
    return out

def pw(y,last_season_month,ident,scope):
    x,labels=design(last_season_month);b=np.linalg.lstsq(x,y,rcond=None)[0]
    clipped=False
    for iteration in range(1,201):
        e=y-x@b;raw=float(e[1:]@e[:-1]/(e[:-1]@e[:-1]));rho=float(np.clip(raw,-.98,.98));clipped|=(raw!=rho)
        xx=np.vstack([np.sqrt(1-rho*rho)*x[0],x[1:]-rho*x[:-1]])
        yy=np.r_[np.sqrt(1-rho*rho)*y[0],y[1:]-rho*y[:-1]]
        bb=np.linalg.lstsq(xx,yy,rcond=None)[0];change=np.max(abs(bb-b))/(np.max(abs(b))+1);b=bb
        if change<1e-10:break
    assert change<1e-10,(ident,change)
    ee=yy-xx@b;v=np.linalg.inv(xx.T@xx)*(ee@ee/(40-x.shape[1]))
    # Independent direct GLS solve at the fitted rho checks the transformation.
    corr=rho**np.abs(ts[:,None]-ts[None,:]);w=np.linalg.inv(corr)
    direct=np.linalg.solve(x.T@w@x,x.T@w@y)
    assert np.allclose(b,direct,rtol=1e-8,atol=1e-6)
    out=summarize(b,v,x,np.mean(y))
    out.update(id=ident,scope=scope,divisor='30.4',method='Iterative Prais-Winsten approximation in Python; not an exact Stata replication',season_months=list(range(2,last_season_month+1)),rho=rho,iterations=iteration,converged=True,rho_clipping_used=clipped,max_abs_direct_gls_coefficient_difference=float(np.max(abs(b-direct))),coefficient_order=labels,coefficients=b.tolist(),covariance=v.tolist(),after_at_first_post=0,after_at_last_post=17,normalization_note='Coefficient/overall observed mean is descriptive rescaling; not an effect relative to a counterfactual and not a between-study statistical test.')
    # Sufficient to verify the delta-method formula, not to validate the model.
    l=np.zeros(len(b));l[2:4]=[1,17];x0=x[-1].copy();x0[2:4]=0
    analytic=100*(l/(x0@b)-(l@b)*x0/(x0@b)**2);numeric=[]
    for j in range(len(b)):
        eps=max(abs(b[j])*1e-5,.0001);bp=b.copy();bm=b.copy();bp[j]+=eps;bm[j]-=eps
        numeric.append(100*((l@bp)/(x0@bp)-(l@bm)/(x0@bm))/(2*eps))
    assert np.allclose(analytic,numeric,rtol=1e-5,atol=1e-8)
    out['max_abs_ratio_gradient_difference']=float(np.max(abs(analytic-numeric)))
    return out

new=[]
for scope,y in [('two_descriptors_all_oral',all30),('0408010W0_only_oral',na)]:
    for end in [12,11]:new.append(pw(y,end,f'bridge_{scope}_30_4_pw_month2_{end}',scope))
# Verify our borrowed implementation against its frozen, independently checked run.
check=pw(d.daily_ddd.to_numpy(),12,'validation_existing_daily_pw','two_descriptors_all_oral')
old=next(x for x in prior_verify['results'] if x['measure']=='daily_ddd')
for field in ['estimate','lower','upper']:assert abs(check['terminal_percent'][field]-old['Prais_Winsten'][field])<1e-8
assert abs(check['rho']-old['Prais_Winsten_rho'])<1e-10

orig={'id':'published_primary','data_source':'Public NHSBSA community dispensing, original download/version unavailable','drug_scope':'Text names Sodium valproate and Valproic acid but associates them with 0408010W0; exact executable filter unavailable','route':'Oral; injectable formulations excluded from DDD analysis','date_from':202201,'date_to':202504,'n':40,'breakpoint':202311,'divisor':30.4,'mean_outcome_narrative':14922,'mean_outcome_table1':14840,'mean_outcome_pre_table1':15054,'mean_outcome_post_table1':14578,'mean_monthly_ddd_table1':451205,'mean_monthly_items_table1':233375,'total_prescriptions_abstract_results':4879978,'total_prescriptions_methods':'9.3 million','pre_slope':{'estimate':12.6,'lower':-10.0,'upper':35.2},'immediate_level':{'estimate':-.8,'lower':-432.8,'upper':431.2},'slope_change':{'estimate':-85.2,'lower':-122.9,'upper':-47.5},'post_slope':{'estimate':-72.6,'lower':-103.5,'upper':-41.8},'terminal_counterfactual':15281,'terminal_fitted_or_actual_as_worded':13747,'terminal_percent_reported':-10.0,'terminal_percent_ci':None,'method':'Prais-Winsten stated; exact Stata command, rho estimator, options, time encoding and covariance matrix unavailable','seasonality':'Methods says February through November; whether December was actually excluded is unknown','main_source_url':source_url,'source_lines':'QA/galloway_full_text.txt:380-479,549-570,730-785','reported_outcome_label':'people prescribed per month, derived from DDDs/30.4; not observed distinct patients'}
verified=json.loads((OUT/'published_values_verified.json').read_text(encoding='utf8'))
for key in ['mean_outcome_narrative','mean_outcome_table1','pre_slope','immediate_level','slope_change','post_slope','terminal_counterfactual','terminal_fitted_or_actual_as_worded','terminal_percent_reported']:assert orig[key]==verified[key],key
orig['arithmetic_checks_from_rounded_published_numbers']={'endpoint_difference':13747-15281,'endpoint_percent':100*(13747-15281)/15281,'level_plus_17_slope_changes':-.8+17*(-85.2),'level_plus_18_slope_changes':-.8+18*(-85.2),'discrepancy_endpoint_minus_17_step':(13747-15281)-(-.8+17*(-85.2)),'discrepancy_endpoint_minus_18_step':(13747-15281)-(-.8+18*(-85.2)),'interpretation':'Rounded published endpoint difference is close to an 18-increment calculation. This cannot identify the original time encoding or establish an error; the current coding has first post after=0 and final after=17. Starting the post-break time at1 instead of0 reparameterizes the level coefficient while preserving the fitted model space. The actual definition of the published level coefficient and terminal month is unknown; this arithmetic is a request for clarification, not a finding of bias.'}
orig['descriptive_coefficients_percent_of_table1_mean']={k:100*orig[k]['estimate']/14840 for k in ['pre_slope','immediate_level','slope_change','post_slope']}
save('published_values_and_source_notes.json',orig)
save('exploratory_prais_winsten_models.json',{'date_local':'2026-11-05','status':'exploratory_source_alignment_not_exact_replication','model_count':4,'fits':new,'validation_against_existing_daily_pw':{'pass':True,'max_terminal_interval_difference':max(abs(check['terminal_percent'][f]-old['Prais_Winsten'][f]) for f in ['estimate','lower','upper']),'rho_difference':abs(check['rho']-old['Prais_Winsten_rho'])},'unchanged_primary_model':'daily_ddd_202311_month','unknown_original_choices':['actual drug filter and source version','product strength mapping','whether quantities were item-weighted','Stata commands/options and rho estimator','February-November versus February-December season indicators','first post month time coding and endpoint contrast definition']})
known=[]
for ident in ['daily_ddd_202311_month','ddd_30_4_202311_month','sodium_only_202311_month']:
    f=dict(fits[ident]);mean=float(d[f['outcome']].mean());f['mean_outcome']=mean
    f['method']='Frozen REML GLS AR(1) model; inherited unchanged';f['scope']='0408010W0_only_oral' if ident.startswith('sodium') else 'two_descriptors_all_oral';f['divisor']='30.4' if ident.startswith('ddd_30_4') else 'actual_calendar_days';f['descriptive_coefficients_percent_of_overall_mean']={k:100*f[k]['estimate']/mean for k in ['pre_slope','immediate_level','slope_change','post_slope']};known.append(f)
save('frozen_models_used_for_bridge.json',known)
flat=[]
def flatrow(f):
    z={'model':f['id'],'scope':f['scope'],'divisor':f['divisor'],'method':f['method'],'season_months':','.join(map(str,f.get('season_months',range(2,13)))),'mean_outcome':f['mean_outcome']}
    for key in ['pre_slope','immediate_level','slope_change','post_slope','terminal_difference','terminal_percent']:
        for field in ['estimate','lower','upper']:z[key+'_'+field]=f[key][field]
    z.update(terminal_counterfactual=f['terminal_counterfactual'],terminal_fitted=f['terminal_fitted'],rho=f['rho'],residual_df=f.get('residual_df'),**{'rescaled_'+k:v for k,v in f['descriptive_coefficients_percent_of_overall_mean'].items()})
    return z
for f in known+new:flat.append(flatrow(f))
csvsave('reproduction_bridge_numeric_models.csv',flat)
rows=[]
def fmt(x,digits=1):
    if isinstance(x,dict):return f"{x['estimate']:,.{digits}f} ({x['lower']:,.{digits}f} to {x['upper']:,.{digits}f})"
    return f'{x:,.{digits}f}'
frozen=known[1];pw12=new[0];pw11=new[1];na12=new[2]
for key,label,unit in [('mean_outcome','Mean monthly outcome','DDD/day equivalents'),('pre_slope','Pre-break slope','DDD/day equivalents per month'),('immediate_level','Immediate level change','DDD/day equivalents'),('slope_change','Change in slope','DDD/day equivalents per month'),('post_slope','Post-break slope','DDD/day equivalents per month'),('terminal_percent','April 2025 difference from modelled prior-trend continuation','%')]:
    o=fmt(orig['mean_outcome_table1'])+' [table 1]; '+fmt(orig['mean_outcome_narrative'])+' [text]' if key=='mean_outcome' else '-10.0 [reported; CI not supplied]' if key=='terminal_percent' else fmt(orig[key])
    rows.append({'measure':label,'unit':unit,'published_primary':o,'reconstructed_30_4_frozen_GLS':fmt(frozen[key],2 if key=='terminal_percent' else 1),'reconstructed_30_4_PW_Feb_Dec':fmt(pw12[key],2 if key=='terminal_percent' else 1),'reconstructed_30_4_PW_Feb_Nov':fmt(pw11[key],2 if key=='terminal_percent' else 1),'0408010W0_only_30_4_PW_Feb_Dec':fmt(na12[key],2 if key=='terminal_percent' else 1)})
csvsave('supplementary_table_reproduction_bridge.csv',rows)
details=[
('Observation window','January 2022-April 2025; 40 months','Same 40 frozen months','aligned','The period is not extended after inspecting results.'),
('Source snapshot','Original local CSV release/download date not available','NHSBSA SQL aggregates obtained 2 November 2026','unresolved','Source updates can change totals; cannot reconstruct the original snapshot.'),
('Drug selection','Two chemical descriptors described together with one chemical code 0408010W0','Full two-descriptor oral scope plus isolated 0408010W0 oral check','partially aligned','Published wording does not establish the exact executable filter. Three codes in current full scope.'),
('Route','Injectable formulations excluded for DDD analyses','58 retrieved oral presentations, six non-oral presentations excluded','conceptually aligned','Exact original product list and 726 reported exclusions unavailable; current 1026 nonoral items/780 rows not declared equivalent.'),
('Strength and additive quantity','1.5g DDD; full extraction/mapping/weighting code unavailable','Fixed declared-strength map; sum of TOTAL_QUANTITY or QUANTITY*ITEMS','unresolved','Item weighting is checked, not claimed as the explanation of original discrepancies.'),
('Days divisor','30.4','30.4 in aligned bridge; calendar days retained in frozen primary','aligned in bridge','A divisor match is not an original-method replication.'),
('Average monthly items','233375 (rounded, all routes)','233374.7 all routes in current extraction','reproduced to published precision','Supports source overlap but not identity of original pipeline.'),
('Mean outcome scale','14840 table1;14922 narrative','124923.5 for two-descriptor oral DDD/30.4;105891.4 for 0408010W0 only','not reproduced','Approximately 8.42 or 8.37 times published means. A constant scale difference alone does not overturn a relative policy effect.'),
('Breakpoint','November 2023','November 2023 for bridge and frozen main','aligned by month','Exact intervention-time variable coding unavailable.'),
('Seasonal controls','February-November wording, January reference','Parallel literal February-November and usual February-December specifications','ambiguity probed','Literal ten indicators pool January and December as an implicit reference; do not assert actual code omitted December.'),
('Serial correlation','Prais-Winsten; lag diagnostics0-6 described, exact command/options absent','Iterative single-rho PW with retained first observation; existing GLS displayed separately','partially aligned','No assertion that Python rho estimation/options equal Stata19 settings.'),
('Pre/level/change/post estimates','Reported coefficients and95%CIs in results','Matched four components with same labels and units in table','comparison possible','Ranges are conditional on different fitted models; differences not a formal inter-study test.'),
('Terminal contrast','13747 versus15281; reported10% reduction','Published endpoint retained; reconstructed βlevel+17*βchange at April2025','time encoding unresolved','Published rounded difference is close to level+18*change. A first-post index1 versus0 reparameterizes the level but preserves fitted space; it is not evidence of error. Exact original coefficient and endpoint definitions are needed.'),
('Outcome interpretation','People estimated as DDD/30.4','Dose equivalents explicitly labelled, no distinct patient count','concept clarified','No individual prevalence, initiation, withdrawal or clinical outcome measured.')]
csvsave('reproduction_bridge_alignment_audit.csv',[dict(component=a,published=b,current=c,status=d,interpretation=e) for a,b,c,d,e in details])
save('source_access_and_method_boundary.json',{'main_text':{'local_file_optional':'QA/galloway_full_text.txt','publisher_pdf_optional':'SOURCE/literature/galloway_vor.pdf','package_note':'Original publication files are not included; verified transcription and citation are supplied; not exact original-code replication','sha256':sha(ROOT/'SOURCE/literature/galloway_vor.pdf') if (ROOT/'SOURCE/literature/galloway_vor.pdf').exists() else None,'url':source_url},'supplement':{'url':supp_url,'full_pdf_access':'not_obtained_this_run: web403 and sandboxed urllib network blocked','official_index_excerpt_access':'Read 2026-11-05; page3 indexed text corroborates both analyses used DDD/30.4 and Prais-Winsten, November2023. It does not supply original extraction data or executable settings.','limitation':'Only retrieved indexed excerpt used; no claim full supplement independently inspected.'},'statistical_boundary':'Four new source-aligned checks are exploratory and are not an exact replication. Published normalised coefficients are descriptive only. The primary GLS estimates are unchanged.'})
checks={'date_local':'2026-11-05','pass':True,'40_month_window_unchanged':True,'source_inputs_sha256_unchanged':all(sha(ROOT/k)==v for k,v in baseline.items()),'all_new_PW_converged':all(x['converged'] for x in new),'rho_clipping_used':any(x['rho_clipping_used'] for x in new),'existing_PW_reproduced':True,'reported_endpoint_not_replaced':True,'primary_model_unchanged':sha(inputs[3])==baseline[inputs[3].relative_to(ROOT).as_posix()],'source_hashes':[{'file':x.relative_to(ROOT).as_posix(),'sha256':baseline[x.relative_to(ROOT).as_posix()]} for x in inputs]}
assert checks['source_inputs_sha256_unchanged'] and not checks['rho_clipping_used']
save('bridge_validation.json',checks)
print(json.dumps({'models':[{k:x[k] for k in ['id','mean_outcome','pre_slope','immediate_level','slope_change','post_slope','terminal_percent']} for x in new],'validation_pass':checks['pass']},ensure_ascii=False,indent=2))
