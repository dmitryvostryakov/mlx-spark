"""Reserved optimizers API; porting is a tracked implementation task."""
from ..errors import FeatureUnavailable

def __getattr__(name: str):
    if name.startswith("__"):
        raise AttributeError(name)
    raise FeatureUnavailable("mlx_spark.optimizers." + name + " is not implemented in the scaffold")
