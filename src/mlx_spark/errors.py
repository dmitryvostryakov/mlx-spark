class SparkError(RuntimeError):
    """Base error for actionable failures."""

class NativeCoreUnavailable(SparkError):
    pass

class FeatureUnavailable(SparkError):
    pass

class ContractError(ValueError):
    pass
