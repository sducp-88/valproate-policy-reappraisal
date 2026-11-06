from pathlib import Path
import argparse,subprocess,sys
p=argparse.ArgumentParser();p.add_argument('--rscript',default='Rscript');a=p.parse_args()
root=Path(__file__).resolve().parent
steps=[('primary',[sys.executable,'11_Supplementary_Code_Reconstruct.py']),('primary',[a.rscript,'12_Supplementary_Code_Models.R','.']),('primary',[sys.executable,'13_Supplementary_Code_Verify.py']),('primary',[sys.executable,'14_Supplementary_Code_Figures.py']),('extensions',[sys.executable,'run_all.py'])]
for folder,command in steps:
    print(folder,command[1],flush=True)
    subprocess.run(command,cwd=root/folder,check=True)
