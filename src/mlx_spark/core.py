"""Reserved public tensor API. Never silently imports mlx, torch, or NumPy.

The future independently packaged extension is mlx_spark._core. The scaffold
must fail clearly rather than implementing a fake grad/compile decorator.
"""
from importlib import import_module
from .errors import NativeCoreUnavailable


def __getattr__(name: str):
    if name.startswith("__"):
        raise AttributeError(name)
    try:
        native = import_module("mlx_spark._core")
    except ModuleNotFoundError as exc:
        if exc.name != "mlx_spark._core":
            raise
        raise NativeCoreUnavailable(
            "MLX-Spark native tensor core is not built. This bundle is an "
            "engineering scaffold, not a working MLX replacement. Complete "
            "tasks FND-03 through CORE-06; do not substitute installed mlx/torch."
        ) from exc
    return getattr(native, name)
