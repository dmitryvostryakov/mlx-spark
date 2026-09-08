from dataclasses import dataclass
from enum import Enum
from typing import Protocol, Sequence
from ..errors import ContractError

class AllocationKind(str, Enum):
    HOST = "host"
    SHARED = "shared"
    DEVICE = "device"

@dataclass(frozen=True)
class TensorSpec:
    shape: tuple[int, ...]
    dtype: str
    device: str
    def __post_init__(self):
        if any(type(n) is not int or n < 0 for n in self.shape):
            raise ContractError("Shape dimensions must be nonnegative integers")
        if self.device not in {"cpu", "cuda:0"}:
            raise ContractError("Phase 1 supports cpu and one explicitly selected GPU only")

@dataclass(frozen=True)
class OperationCapabilities:
    forward: bool = False
    vjp: bool = False
    jvp: bool = False
    vmap: bool = False
    higher_order: bool = False
    compiled: bool = False
    hardware_validated: bool = False

class Primitive(Protocol):
    """Conceptual protocol; implementation must retain autodiff and lazy semantics."""
    name: str
    capabilities: OperationCapabilities
    def infer(self, inputs: Sequence[TensorSpec]) -> Sequence[TensorSpec]: ...
