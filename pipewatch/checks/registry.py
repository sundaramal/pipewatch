"""Registry for mapping check type names to check classes."""

from typing import Dict, Type
from pipewatch.checks.base import BaseCheck

_REGISTRY: Dict[str, Type[BaseCheck]] = {}


def register(name: str, check_cls: Type[BaseCheck]) -> None:
    """Register a check class under the given type name."""
    if not issubclass(check_cls, BaseCheck):
        raise TypeError(f"{check_cls} must be a subclass of BaseCheck")
    _REGISTRY[name] = check_cls


def get(name: str) -> Type[BaseCheck]:
    """Retrieve a check class by type name.

    Raises KeyError if the name is not registered.
    """
    if name not in _REGISTRY:
        raise KeyError(
            f"Unknown check type: '{name}'. "
            f"Available types: {sorted(_REGISTRY.keys())}"
        )
    return _REGISTRY[name]


def available() -> list:
    """Return a sorted list of all registered check type names."""
    return sorted(_REGISTRY.keys())


def register_builtins() -> None:
    """Register all built-in check types."""
    from pipewatch.checks.builtin import ThresholdCheck, FreshnessCheck

    register("threshold", ThresholdCheck)
    register("freshness", FreshnessCheck)


# Auto-register builtins when this module is imported
register_builtins()
