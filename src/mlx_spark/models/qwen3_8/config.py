from dataclasses import dataclass
from typing import Any, Mapping
from ...errors import ContractError

@dataclass(frozen=True)
class QwenTextSpec:
    layers: tuple[str, ...]
    hidden_size: int
    intermediate_size: int
    attention_heads: int
    kv_heads: int
    head_dim: int
    linear_key_heads: int
    linear_value_heads: int
    linear_key_dim: int
    linear_value_dim: int
    conv_kernel: int
    vocab_size: int
    max_positions: int
    state_dtype: str
    has_vision: bool
    mtp_layers: int

    @classmethod
    def from_mapping(cls, raw: Mapping[str, Any]) -> "QwenTextSpec":
        if raw.get("model_type") != "qwen3_5":
            raise ContractError("Expected Qwen3.8 checkpoint declaring model_type=qwen3_5")
        c = raw.get("text_config")
        if not isinstance(c, Mapping):
            raise ContractError("text_config is required; no architecture guessing")
        def positive(key):
            v=c.get(key)
            if type(v) is not int or v <= 0:
                raise ContractError(f"{key} must be a positive integer")
            return v
        layers=c.get("layer_types")
        if not isinstance(layers,list) or any(x not in {"linear_attention","full_attention"} for x in layers):
            raise ContractError("Explicit supported layer_types are required")
        if len(layers)!=positive("num_hidden_layers"):
            raise ContractError("num_hidden_layers does not match layer_types")
        if c.get("mamba_ssm_dtype") != "float32":
            raise ContractError("The first approved state policy requires float32")
        spec=cls(tuple(layers),positive("hidden_size"),positive("intermediate_size"),
            positive("num_attention_heads"),positive("num_key_value_heads"),positive("head_dim"),
            positive("linear_num_key_heads"),positive("linear_num_value_heads"),
            positive("linear_key_head_dim"),positive("linear_value_head_dim"),
            positive("linear_conv_kernel_dim"),positive("vocab_size"),positive("max_position_embeddings"),
            "float32",isinstance(raw.get("vision_config"),Mapping),positive("mtp_num_hidden_layers"))
        if spec.attention_heads % spec.kv_heads or spec.linear_value_heads % spec.linear_key_heads:
            raise ContractError("Head grouping must be integral")
        return spec

    @property
    def linear_layers(self): return self.layers.count("linear_attention")
    @property
    def full_layers(self): return self.layers.count("full_attention")
