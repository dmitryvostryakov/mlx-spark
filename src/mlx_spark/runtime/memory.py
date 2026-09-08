"""Architecture-derived arithmetic, NOT a measured runtime memory estimator."""
from dataclasses import asdict, dataclass
from ..models.qwen3_8.config import QwenTextSpec
from ..errors import ContractError

@dataclass(frozen=True)
class MemoryEstimate:
    kv_bytes: int
    recurrent_bytes: int
    conv_history_bytes: int
    logits_bytes: int
    nominal_weight_bytes: int | None
    estimate_only: bool = True
    fit_verdict: str = "UNKNOWN: workspaces, allocator overhead, conversion peaks and system reserve not measured"
    def to_dict(self): return asdict(self)

def estimate(spec: QwenTextSpec, *, tokens: int, batch: int = 1,
             kv_itemsize: int = 2, logits_positions: int = 1,
             nominal_parameters: int | None = None, weight_bits: int = 16) -> MemoryEstimate:
    for name,v in {"tokens":tokens,"batch":batch,"kv_itemsize":kv_itemsize,
                   "logits_positions":logits_positions,"weight_bits":weight_bits}.items():
        if type(v) is not int or v <= 0:
            raise ContractError(f"{name} must be a positive integer")
    if tokens > spec.max_positions:
        raise ContractError("Requested tokens exceed the snapshot's advertised context")
    if logits_positions > tokens:
        raise ContractError("logits_positions cannot exceed tokens")
    if nominal_parameters is not None and (type(nominal_parameters) is not int or nominal_parameters<=0):
        raise ContractError("nominal_parameters must be positive or omitted")
    kv = batch*tokens*2*spec.full_layers*spec.kv_heads*spec.head_dim*kv_itemsize
    recurrent = batch*spec.linear_layers*spec.linear_value_heads*spec.linear_value_dim*spec.linear_key_dim*4
    channels = 2*spec.linear_key_heads*spec.linear_key_dim + spec.linear_value_heads*spec.linear_value_dim
    # Contract choice: history-only K-1 samples in BF16. Actual implementation may allocate more.
    conv = batch*spec.linear_layers*channels*(spec.conv_kernel-1)*2
    logits = batch*logits_positions*spec.vocab_size*2
    weights = None if nominal_parameters is None else (nominal_parameters*weight_bits+7)//8
    return MemoryEstimate(kv,recurrent,conv,logits,weights)
