from pathlib import Path
import csv,hashlib
root=Path(__file__).resolve().parent
with (root/'MANIFEST_SHA256.csv').open(encoding='utf-8-sig',newline='') as stream:
    rows=list(csv.DictReader(stream))
for row in rows:
    p=root/row['file']
    assert p.stat().st_size==int(row['bytes']) and hashlib.sha256(p.read_bytes()).hexdigest()==row['sha256'],row['file']
print('PASS:',len(rows),'initial repository files')
