"""Independent direct GLS, finite-difference delta, Prais-Winsten and HAC checks."""
from pathlib import Path
import json,sys
import numpy as np
import pandas as pd
from scipy.stats import t
ROOT=Path(__file__).resolve().parents[2]
d=pd.read_csv(ROOT/'ANALYSIS/data/monthly_analysis.csv')
models=json.loads((ROOT/'ANALYSIS/results/models.json').read_text())['fits']
tt=d.time.to_numpy();X=np.column_stack([np.ones(40),tt,(tt>=22)*1,np.maximum(tt-22,0)]+[(d.month==m)*1 for m in range(2,13)])
df=40-X.shape[1];crit=t.ppf(.975,df)
L=np.zeros(X.shape[1]);L[2:4]=[1,17];last=X[-1].copy();last[2:4]=0
def percentage(b,V):
    den=last@b;delta=L@b;g=L/den-delta*last/den**2
    se=np.sqrt(g@V@g)*100;p=delta/den*100
    return {'estimate':float(p),'lower':float(p-crit*se),'upper':float(p+crit*se)}
out=[]
for measure in ['daily_ddd','unweighted_daily','rows','items']:
    y=d[measure].to_numpy(float);r=models[measure+'_202311_month'];rho=r['rho']
    corr=rho**np.abs(tt[:,None]-tt[None,:]);W=np.linalg.inv(corr)
    direct=np.linalg.solve(X.T@W@X,X.T@W@y)
    rb=np.array([r['coefficients'][n] for n in r['coefficient_order']])
    assert np.allclose(direct,rb,rtol=1e-8,atol=1e-6)
    V=np.array(r['covariance']);gp=L/(last@rb)-(L@rb)*last/(last@rb)**2
    numeric=[]
    for j in range(len(rb)):
        eps=max(abs(rb[j])*1e-5,.0001);plus=rb.copy();minus=rb.copy();plus[j]+=eps;minus[j]-=eps
        numeric.append(((L@plus)/(last@plus)-(L@minus)/(last@minus))/(2*eps))
    assert np.allclose(numeric,gp,rtol=1e-5,atol=1e-9)
    b=np.linalg.lstsq(X,y,rcond=None)[0]
    for iteration in range(200):
        e=y-X@b;rho=float(np.clip(e[1:]@e[:-1]/(e[:-1]@e[:-1]),-.98,.98))
        xx=np.vstack([np.sqrt(1-rho**2)*X[0],X[1:]-rho*X[:-1]])
        yy=np.r_[np.sqrt(1-rho**2)*y[0],y[1:]-rho*y[:-1]]
        bb=np.linalg.lstsq(xx,yy,rcond=None)[0];change=np.max(abs(bb-b))/(np.max(abs(b))+1);b=bb
        if change<1e-10:break
    e=yy-xx@b;V=np.linalg.inv(xx.T@xx)*(e@e/df)
    rec={'measure':measure,'direct_GLS_max_coefficient_difference':float(np.max(abs(direct-rb))), 'gradient_max_abs_error':float(np.max(abs(np.array(numeric)-gp))), 'Prais_Winsten_rho':rho,'Prais_Winsten':percentage(b,V),'HAC':[]}
    b=np.linalg.lstsq(X,y,rcond=None)[0];e=y-X@b;z=X*e[:,None];bread=np.linalg.inv(X.T@X)
    for lag in [1,3,6]:
        meat=z.T@z
        for k in range(1,lag+1):
            c=z[k:].T@z[:-k];meat+=(1-k/(lag+1))*(c+c.T)
        V=bread@meat@bread*40/df
        rec['HAC'].append({'lag':lag,**percentage(b,V)})
    out.append(rec)
res={'date':'2026-11-02','observations':40,'df':df,'pass':True,'results':out}
(ROOT/'ANALYSIS/results/independent_verification.json').write_text(json.dumps(res,indent=2))
print(json.dumps(res,indent=2))
