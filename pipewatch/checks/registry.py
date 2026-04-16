"""Registry for check classes."""

from __future__ import annotations

from typing import Dict, List, Type

from pipewatch.checks.base import BaseCheck

_REGISTRY: Dict[str, Type[BaseCheck]] = {}


def register(name: str, cls: Type[BaseCheck]) -> None:
    """Register a check class under *name*."""
    _REGISTRY[name] = cls


def get(name: str) -> Type[BaseCheck]:
    """Return the class registered under *name*, raising KeyError if absent."""
    if name not in _REGISTRY:
        raise KeyError(f"No check registered under '{name}'")
    return _REGISTRY[name]


def available() -> List[str]:
    """Return sorted list of registered check names."""
    return sorted(_REGISTRY.keys())


def register_builtins() -> None:
    """Register all built-in check types."""
    from pipewatch.checks.builtin import FreshnessCheck, ThresholdCheck
    from pipewatch.checks.composite import CompositeCheck
    from pipewatch.checks.conditional import ConditionalCheck
    from pipewatch.checks.ratelimited import RateLimitedCheck
    from pipewatch.checks.retry import RetryCheck
    from pipewatch.checks.scheduled import ScheduledCheck
    from pipewatch.checks.tagged import TaggedCheck
    from pipewatch.checks.timeout import TimeoutCheck

    register("threshold", ThresholdCheck)
    register("freshness", FreshnessCheck)
    register("composite", CompositeCheck)
    register("retry", RetryCheck)
    register("timeout", TimeoutCheck)
    register("conditional", ConditionalCheck)
    register("scheduled", ScheduledCheck)
    register("tagged", TaggedCheck)
    register("ratelimited", RateLimitedCheck)
