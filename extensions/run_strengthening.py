from pathlib import Path
import sys,subprocess,json,hashlib,platform,datetime
import numpy,pandas,scipy,statsmodels
ROOT=Path(__file__).resolve().parent
paths=['WORKING/strengthening_20261105/analyze_measurement_components.py','WORKING/strengthening_20261105/reproduction_bridge/build_reproduction_bridge.py','WORKING/strengthening_20261105/reproduction_bridge/build_table_s5.py','WORKING/strengthening_20261105/reproduction_bridge/independent_measurement_review.py','WORKING/strengthening_20261105/cost/prepare_cost_from_raw.py','WORKING/strengthening_20261105/cost/analyse_cost_aggregates.py','WORKING/strengthening_20261105/cost/verify_cost_outputs.py']
logs=ROOT/'RUN_LOGS';logs.mkdir(exist_ok=True)
out=[]
for i,p in enumerate(paths,1):
 r=subprocess.run([sys.executable,str(ROOT/p)],cwd=ROOT,capture_output=True,text=True,encoding='utf8',errors='replace')
 (logs/f'{i:02}_{Path(p).stem}.log').write_text(r.stdout+'\n'+r.stderr,encoding='utf8')
 out.append({'script':p,'returncode':r.returncode})
 print(p,r.returncode,flush=True)
 if r.returncode:raise RuntimeError('Replay failed; inspect RUN_LOGS')
report={'status':'PASS','date_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'runtime':{'python':platform.python_version(),'numpy':numpy.__version__,'pandas':pandas.__version__,'scipy':scipy.__version__,'statsmodels':statsmodels.__version__},'steps':out,'network_required':False,'original_author_code_replication':False}
(ROOT/'REPLAY_EXECUTION.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf8')
