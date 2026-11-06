from pathlib import Path
import csv,hashlib
ROOT=Path(__file__).resolve().parent
rows=list(csv.DictReader((ROOT/'INPUT_MANIFEST_SHA256.csv').open(encoding='utf-8-sig',newline='')))
for x in rows:
 p=ROOT/x['file'];assert p.stat().st_size==int(x['bytes']) and hashlib.sha256(p.read_bytes()).hexdigest()==x['sha256'],x['file']
print('PASS: immutable scientific and provenance inputs',len(rows))
