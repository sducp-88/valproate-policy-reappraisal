from pathlib import Path
import sys,subprocess,json,datetime,platform,importlib.metadata
ROOT=Path(__file__).resolve().parent
D='WORKING/patient_extension_20261105/'
steps=[['verify_inputs.py'],['run_strengthening.py'],['WORKING/strengthening_20261105/make_supplement_figure.py'],[D+'acquisition/parse_ui_rows.py','vpa1'],[D+'analyse_patient_context.py'],[D+'verify_patient_context.py'],[D+'make_patient_context_figure.py','--input-dir',D+'analysis','--output-dir','FIGURES','--source-dir',D+'figure_source','--basename','Figure_S3'],['verify_inputs.py']]
logs=ROOT/'RUN_LOGS_17';logs.mkdir(exist_ok=True);results=[]
for i,args in enumerate(steps,1):
 r=subprocess.run([sys.executable,str(ROOT/args[0]),*args[1:]],cwd=ROOT,capture_output=True,text=True,encoding='utf8',errors='replace')
 output=r.stdout+'\n'+r.stderr
 for prefix in [str(ROOT),str(ROOT).replace('\\','/')]:output=output.replace(prefix,'<package_root>')
 (logs/f'{i:02}_{Path(args[0]).stem}.log').write_text(output,encoding='utf8')
 results.append({'arguments':args,'returncode':r.returncode});print(args[0],r.returncode,flush=True)
 if r.returncode:raise RuntimeError('Replay failed; inspect RUN_LOGS_17')
versions={p:importlib.metadata.version(p) for p in ['numpy','pandas','scipy','statsmodels','matplotlib','Pillow']}
report={'status':'PASS','executed_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'python':platform.python_version(),'libraries':versions,'steps':results,'network_required':False,'primary_frozen_GLS_refitted':False,'patient_causal_models_fitted':False}
(ROOT/'REPLAY_EXECUTION_17.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf8')
