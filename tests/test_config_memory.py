import copy,json
from pathlib import Path
import pytest
from mlx_spark.models.qwen3_8.config import QwenTextSpec
from mlx_spark.runtime.memory import estimate
from mlx_spark.errors import ContractError
ROOT=Path(__file__).resolve().parents[1]

def raw():return json.loads((ROOT/'configs/models/qwen3.8-27b.config.snapshot.json').read_text())
def spec():return QwenTextSpec.from_mapping(raw())

def test_observed_architecture():
 s=spec();assert s.full_layers==16 and s.linear_layers==48
 assert s.hidden_size==5120 and s.head_dim==256 and s.attention_heads==24
 # hidden_size/heads is NOT head_dim for this model.
 assert s.has_vision and s.mtp_layers==1

def test_memory_arithmetic():
 s=spec();e=estimate(s,tokens=32768)
 assert e.kv_bytes==2*1024**3
 assert e.recurrent_bytes==144*1024**2
 assert e.conv_history_bytes==48*10240*3*2
 assert e.logits_bytes==248320*2
 assert e.nominal_weight_bytes is None and e.estimate_only
 assert e.fit_verdict.startswith('UNKNOWN')

def test_weight_arithmetic_is_lower_bound():
 e=estimate(spec(),tokens=128,nominal_parameters=27_000_000_000,weight_bits=4)
 assert e.nominal_weight_bytes==13_500_000_000

def test_all_logits_cost():
 e=estimate(spec(),tokens=32768,logits_positions=32768)
 assert e.logits_bytes==16_273_899_520

@pytest.mark.parametrize('field,value',[('num_hidden_layers',63),('num_key_value_heads',5),('linear_num_value_heads',47),('mamba_ssm_dtype','bfloat16')])
def test_bad_configuration_rejected(field,value):
 c=raw();c['text_config'][field]=value
 with pytest.raises(ContractError):QwenTextSpec.from_mapping(c)

@pytest.mark.parametrize('kwargs',[{'tokens':0},{'tokens':-1},{'tokens':300000},{'tokens':2,'batch':0},{'tokens':2,'logits_positions':3},{'tokens':True}])
def test_bad_budget_rejected(kwargs):
 with pytest.raises(ContractError):estimate(spec(),**kwargs)
