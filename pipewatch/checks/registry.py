"""Registry mapping check-type strings to BaseCheck subclasses."""
from __future__ import annotations

from typing import Dict, List, Type

from pipewatch.checks.base import BaseCheck

_registry: Dict[str, Type[BaseCheck]] = {}


def register(type_name: str, cls: Type[BaseCheck]) -> None:
    """Register *cls* under *type_name*.

    Raises ``ValueError`` if the name is already taken by a different class.
    """
    existing = _registry.get(type_name)
    if existing is not None and existing is not cls:
        raise ValueError(
            f"Check type '{type_name}' is already registered by {existing!r}."
        )
    _registry[type_name] = cls


def get(type_name: str) -> Type[BaseCheck]:
    """Return the class registered under *type_name*.

    Raises ``KeyError`` if the type is not registered.
    """
    try:
        return _registry[type_name]
    except KeyError:
        raise KeyError(
            f"Unknown check type '{type_name}'. "
            f"Available types: {available()}"
        ) from None


def available() -> List[str]:
    """Return a sorted list of all registered type names."""
    return sorted(_registry)


def register_builtins() -> None:
    """Register all built-in check types (idempotent)."""
    from pipewatch.checks.builtin import FreshnessCheck, ThresholdCheck
    from pipewatch.checks.composite import CompositeCheck

    register("threshold", ThresholdCheck)
    register("freshness", FreshnessCheck)
    register("composite", CompositeCheck)
