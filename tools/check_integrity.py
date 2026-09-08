"""Verify a delivered immutable bundle; regenerate manifests after intentional edits."""
from pathlib import Path
import hashlib, json, sys
ROOT=Path(__file__).resolve().parents[1]
f=ROOT/'MANIFEST.sha256'
if not f.exists(): raise SystemExit('No MANIFEST.sha256')
errors=[]
for line in f.read_text().splitlines():
    expected,rel=line.split('  ',1)
    path=(ROOT/rel).resolve()
    if not path.is_relative_to(ROOT) or not path.is_file(): errors.append(rel+': missing/unsafe');continue
    if hashlib.sha256(path.read_bytes()).hexdigest()!=expected:errors.append(rel+': mismatch')
print(json.dumps({'checked':len(f.read_text().splitlines()),'errors':errors},indent=2))
raise SystemExit(1 if errors else 0)
