import json,subprocess,sys
from pathlib import Path
import pytest
from mlx_spark import core
from mlx_spark.errors import NativeCoreUnavailable,ContractError
from mlx_spark.runtime.contracts import TensorSpec,OperationCapabilities
from mlx_spark.cli import main
from check_gate import validate
ROOT=Path(__file__).resolve().parents[1]

def test_missing_native_fails_not_fallback():
 with pytest.raises(NativeCoreUnavailable):core.array([1,2])
 with pytest.raises(NativeCoreUnavailable):core.grad(lambda x:x)
 with pytest.raises(NativeCoreUnavailable):core.compile(lambda x:x)

def test_status_does_not_claim_implementation(capsys):
 assert main(['status'])==0
 s=json.loads(capsys.readouterr().out)
 assert not s['cuda_validated'] and not s['framework_training'] and s['tp2']=='deferred'

@pytest.mark.parametrize('device',['cuda:1','cluster','tp:2'])
def test_phase_one_tensor_devices(device):
 with pytest.raises(ContractError):TensorSpec((2,3),'float32',device)

def test_empty_tensor_contract():assert TensorSpec((0,3),'float32','cpu').shape==(0,3)
def test_capabilities_default_to_false():assert not OperationCapabilities().hardware_validated

def test_release_template_cannot_pass():
 e=json.loads((ROOT/'evidence/single-spark-v1.TEMPLATE.json').read_text())
 assert validate(e)

def test_network_commands_require_opt_in():
 p=subprocess.run([sys.executable,str(ROOT/'tools/resolve_sources.py')],capture_output=True,text=True)
 assert p.returncode!=0 and 'Network disabled' in p.stderr

def test_no_runtime_dependency_on_mlx_torch():
 import tomllib
 p=tomllib.loads((ROOT/'pyproject.toml').read_text())
 assert not p['project']['dependencies']
 text=(ROOT/'src/mlx_spark/core.py').read_text()
 assert 'import mlx.core' not in text and 'import torch' not in text

def test_plan_acyclic():
 p=subprocess.run([sys.executable,str(ROOT/'tools/validate_plan.py')],capture_output=True,text=True)
 assert p.returncode==0,p.stderr

def test_source_candidate_never_claims_hardware_validation():
 c=json.loads((ROOT/'configs/source-lock.candidate.json').read_text())
 assert c['status']=='candidate_not_hardware_validated'
 assert c['sources']['qwen3_8_27b']['revision'] is None

def test_shareable_evidence_has_no_junit_hostname_metadata():
 evidence_files=[p for p in (ROOT/'evidence').rglob('*') if p.is_file()]
 assert evidence_files
 for path in evidence_files:
  assert b'hostname="' not in path.read_bytes(),path
