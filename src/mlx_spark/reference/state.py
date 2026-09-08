from dataclasses import dataclass
import numpy as np
from ..errors import ContractError

@dataclass(frozen=True)
class ReferenceSnapshot:
    """Tiny immutable reference snapshot, not a production cache allocator."""
    position: int
    recurrent: np.ndarray
    conv_history: np.ndarray
    def __post_init__(self):
        if type(self.position) is not int or self.position<0: raise ContractError("Invalid position")
        for n in ('recurrent','conv_history'):
            a=np.array(getattr(self,n),copy=True);a.flags.writeable=False
            object.__setattr__(self,n,a)
    def fork(self):
        return ReferenceSnapshot(self.position,self.recurrent,self.conv_history)
