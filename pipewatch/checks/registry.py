"""Registry for check classes."""

from __future__ import annotations

from typing import Dict, Type

from pipewatch.checks.base import BaseCheck

_REGISTRY: Dict[str, Type[BaseCheck]] = {}


def register(name: str, cls: Type[BaseCheck]) -> None:
    _REGISTRY[name] = cls


def get(name: str) -> Type[BaseCheck]:
    if name not in _REGISTRY:
        raise KeyError(f"Unknown check type: {name!r}")
    return _REGISTRY[name]


def available() -> list:
    return list(_REGISTRY.keys())


def register_builtins() -> None:
    from pipewatch.checks.builtin import ThresholdCheck, FreshnessCheck
    from pipewatch.checks.composite import CompositeCheck
    from pipewatch.checks.retry import RetryCheck
    from pipewatch.checks.timeout import TimeoutCheck
    from pipewatch.checks.conditional import ConditionalCheck
    from pipewatch.checks.scheduled import ScheduledCheck
    from pipewatch.checks.tagged import TaggedCheck

    for name, cls in [
        ("threshold", ThresholdCheck),
        ("freshness", FreshnessCheck),
        ("composite", CompositeCheck),
        ("retry", RetryCheck),
        ("timeout", TimeoutCheck),
        ("conditional", ConditionalCheck),
        ("scheduled", ScheduledCheck),
        ("tagged", TaggedCheck),
    ]:
        register(name, cls)
