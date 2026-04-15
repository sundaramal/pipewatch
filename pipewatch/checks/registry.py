"""Registry for check classes, keyed by string type names."""

from __future__ import annotations

from typing import Dict, List, Type

from pipewatch.checks.base import BaseCheck

_REGISTRY: Dict[str, Type[BaseCheck]] = {}


def register(name: str, cls: Type[BaseCheck]) -> None:
    """Register *cls* under *name*."""
    _REGISTRY[name] = cls


def get(name: str) -> Type[BaseCheck]:
    """Return the class registered under *name*.

    Raises
    ------
    KeyError
        If no check is registered with the given name.
    """
    try:
        return _REGISTRY[name]
    except KeyError:
        raise KeyError(f"No check registered with name '{name}'") from None


def available() -> List[str]:
    """Return a sorted list of all registered check type names."""
    return sorted(_REGISTRY.keys())


def register_builtins() -> None:
    """Register all built-in and bundled check types."""
    from pipewatch.checks.builtin import FreshnessCheck, ThresholdCheck
    from pipewatch.checks.composite import CompositeCheck
    from pipewatch.checks.timeout import TimeoutCheck
    from pipewatch.checks.retry import RetryCheck

    register("threshold", ThresholdCheck)
    register("freshness", FreshnessCheck)
    register("composite", CompositeCheck)
    register("timeout", TimeoutCheck)
    register("retry", RetryCheck)
