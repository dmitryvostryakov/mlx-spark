"""Compare normalized model metadata, not raw file hashes; review all differences."""
import argparse,json
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('snapshot',type=Path);p.add_argument('downloaded',type=Path)
a=p.parse_args();x=json.loads(a.snapshot.read_text());y=json.loads(a.downloaded.read_text())
def diff(x,y,p=''):
 if isinstance(x,dict) and isinstance(y,dict):
  out=[]
  for k in sorted(x.keys()|y.keys()):
   if k not in x or k not in y:out.append(p+'/'+k)
   else:out+=diff(x[k],y[k],p+'/'+k)
  return out
 return [] if x==y else [p]
d=diff(x,y);print(json.dumps({'equal':not d,'changed_paths':d},indent=2));raise SystemExit(1 if d else 0)
