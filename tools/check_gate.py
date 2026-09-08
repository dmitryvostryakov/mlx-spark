"""Fail-closed evidence checker. Authenticity still requires independent review."""
import argparse,hashlib,json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def validate(evidence, root=ROOT):
    required=json.loads((root/'configs/release-gates.json').read_text())['single_spark_v1']
    errors=[]
    if evidence.get('schema_version')!=1: errors.append('schema_version must be 1')
    if evidence.get('gate')!='single_spark_v1': errors.append('wrong gate')
    if evidence.get('synthetic') is not False: errors.append('synthetic/missing evidence cannot pass')
    if evidence.get('hardware')!={'platform':'DGX Spark','compute_capability':'12.1','nodes':1}:
        errors.append('real single-Spark hardware declaration required')
    if not re.fullmatch('[0-9a-f]{40}',str(evidence.get('implementation_commit',''))):errors.append('immutable implementation commit required')
    if not evidence.get('reviewer') or evidence.get('reviewer')==evidence.get('implementer'):errors.append('independent reviewer required')
    records=evidence.get('checks',{})
    for name in required:
        rec=records.get(name,{})
        if rec.get('status')!='pass': errors.append(name+': not passed');continue
        if rec.get('skipped',0)!=0:errors.append(name+': skipped cases do not close a gate')
        artifacts=rec.get('artifacts',[])
        if not artifacts:errors.append(name+': no artifacts')
        for item in artifacts:
            rel=item.get('path','');path=(root/rel).resolve()
            if not rel or not path.is_relative_to(root) or not path.is_file():
                errors.append(name+': missing/unsafe artifact');continue
            if hashlib.sha256(path.read_bytes()).hexdigest()!=item.get('sha256'):
                errors.append(name+': artifact hash mismatch')
    return errors

def main():
    p=argparse.ArgumentParser();p.add_argument('--evidence',type=Path,required=True)
    a=p.parse_args()
    if not a.evidence.exists():raise SystemExit('Gate closed: evidence file missing')
    errors=validate(json.loads(a.evidence.read_text()))
    print(json.dumps({'pass':not errors,'errors':errors,'note':'Hash validation is not proof that results are genuine.'},indent=2))
    return 2 if errors else 0
if __name__=='__main__':raise SystemExit(main())
