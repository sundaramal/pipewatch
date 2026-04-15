"""Registry mapping check-type strings to :class:`BaseCheck` subclasses."""

from __future__ import annotations

from typing import Dict, List, Type

from pipewatch.checks.base import BaseCheck

_registry: Dict[str, Type[BaseCheck]] = {}


def register(name: str, cls: Type[BaseCheck]) -> None:
    """Register *cls* under the given *name*."""
    _registry[name] = cls


def get(name: str) -> Type[BaseCheck]:
    """Return the class registered as *name*.

    Raises
    ------
    KeyError
        If *name* has not been registered.
    """
    if name not in _registry:
        raise KeyError(f"No check registered with name '{name}'")
    return _registry[name]


def available() -> List[str]:
    """Return a sorted list of all registered check names."""
    return sorted(_registry.keys())


def register_builtins() -> None:
    """Populate the registry with all built-in check types."""
    from pipewatch.checks.builtin import FreshnessCheck, ThresholdCheck
    from pipewatch.checks.composite import CompositeCheck
    from pipewatch.checks.conditional import ConditionalCheck  # noqa: F401 – side-effect import
    from pipewatch.checks.retry import RetryCheck
    from pipewatch.checks.timeout import TimeoutCheck

    register("threshold", ThresholdCheck)
    register("freshness", FreshnessCheck)
    register("composite", CompositeCheck)
    register("retry", RetryCheck)
    register("timeout", TimeoutCheck)
    register("conditional", ConditionalCheck)
