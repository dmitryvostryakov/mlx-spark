"""Summary/identity validation for measured timings; does not run a model."""
from dataclasses import dataclass
from math import isfinite
from statistics import median,mean,pstdev
from typing import Mapping,Any
from .errors import ContractError

IDENTITY_FIELDS=('model_revision','input_ids_sha256','weight_format','kv_dtype','state_dtype',
                 'prompt_tokens','generated_tokens','batch','math_mode','sampling_hash','warm_state')

@dataclass(frozen=True)
class TimingSeries:
    seconds: tuple[float,...]
    tokens: int
    def __post_init__(self):
        if len(self.seconds)<2 or any(not isfinite(x) or x<=0 for x in self.seconds):
            raise ContractError('At least two positive, finite measured times required')
        if type(self.tokens) is not int or self.tokens<=0:raise ContractError('tokens must be positive')
    def summary(self):
        ordered=sorted(self.seconds);pos=.95*(len(ordered)-1);lo=int(pos);hi=min(lo+1,len(ordered)-1)
        p95=ordered[lo]+(ordered[hi]-ordered[lo])*(pos-lo)
        return {'trials':len(ordered),'median_seconds':median(ordered),'mean_seconds':mean(ordered),
                'std_seconds':pstdev(ordered),'p95_seconds':p95,
                'tokens_per_second_at_median':self.tokens/median(ordered),
                'interpretation':'descriptive only; not a confidence interval or proof of speedup'}

def validate_comparison(a: Mapping[str,Any],b: Mapping[str,Any]):
    for record in (a,b):
        if record.get('synthetic') is not False:raise ContractError('Templates/synthetic data cannot produce a hardware comparison')
        if record.get('kind')!='spark_measured':raise ContractError('Only explicit measured Spark records are comparable here')
        if record.get('nodes')!=1 or record.get('gpu_compute_capability')!='12.1':
            raise ContractError('Phase 1 comparison must declare one GB10')
        if record.get('synchronized') is not True:raise ContractError('Measured GPU timing must declare synchronization')
        for k in IDENTITY_FIELDS:
            if k not in record or record[k] is None:raise ContractError('Missing identity field: '+k)
    mismatch=[k for k in IDENTITY_FIELDS if a[k]!=b[k]]
    if mismatch:raise ContractError('Non-comparable benchmark identity: '+', '.join(mismatch))
