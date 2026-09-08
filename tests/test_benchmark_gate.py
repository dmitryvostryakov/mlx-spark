import copy,hashlib,json
from pathlib import Path
import pytest
from mlx_spark.benchmark import TimingSeries,validate_comparison,IDENTITY_FIELDS
from mlx_spark.errors import ContractError
from check_gate import validate
ROOT=Path(__file__).resolve().parents[1]

def record():
 # Synthetic unit-test dictionary only, never emitted as a benchmark artifact.
 d={k:'unit-test-only' for k in IDENTITY_FIELDS}
 d.update(kind='spark_measured',synthetic=False,nodes=1,gpu_compute_capability='12.1',synchronized=True)
 return d

def test_summary_arithmetic():
 s=TimingSeries((1.,2.,3.),120).summary()
 assert s['median_seconds']==2 and s['tokens_per_second_at_median']==60
 assert s['p95_seconds']==pytest.approx(2.9)

@pytest.mark.parametrize('times',[(0.,1.),(float('nan'),1.),(-1.,1.),(1.,)])
def test_bad_times(times):
 with pytest.raises(ContractError):TimingSeries(times,10)

def test_noncomparable_format_rejected():
 a=record();b=record();b['weight_format']='different'
 with pytest.raises(ContractError):validate_comparison(a,b)

def test_template_rejected():
 a=json.loads((ROOT/'benchmarks/MEASUREMENT.TEMPLATE.json').read_text())
 with pytest.raises(ContractError):validate_comparison(a,a)

def test_unsynchronized_rejected():
 a=record();b=record();b['synchronized']=False
 with pytest.raises(ContractError):validate_comparison(a,b)

def test_release_gate_rejects_skipped_and_wrong_hash(tmp_path):
 (tmp_path/'configs').mkdir()
 (tmp_path/'configs/release-gates.json').write_text(json.dumps({'single_spark_v1':['demo']}))
 (tmp_path/'proof.txt').write_text('unit test, not hardware evidence')
 e={'schema_version':1,'gate':'single_spark_v1','synthetic':False,
    'hardware':{'platform':'DGX Spark','compute_capability':'12.1','nodes':1},
    'implementation_commit':'a'*40,'implementer':'A','reviewer':'B',
    'checks':{'demo':{'status':'pass','skipped':0,'artifacts':[{'path':'proof.txt','sha256':'bad'}]}}}
 assert any('hash mismatch' in x for x in validate(e,tmp_path))
 e['checks']['demo']['artifacts'][0]['sha256']=hashlib.sha256((tmp_path/'proof.txt').read_bytes()).hexdigest()
 assert validate(e,tmp_path)==[] # validates checker mechanics only, not authenticity
 e['checks']['demo']['skipped']=1
 assert any('skipped' in x for x in validate(e,tmp_path))
