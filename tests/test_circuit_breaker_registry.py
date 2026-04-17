"""Ensure CircuitBreakerCheck is registered and usable via the registry."""
from __future__ import annotations

import pytest

from pipewatch.checks.base import BaseCheck, CheckResult
from pipewatch.checks import registry
from pipewatch.checks.circuit_breaker import CircuitBreakerCheck


def _ensure_builtins():
    registry.register_builtins()


class _SimplePass(BaseCheck):
    def __init__(self, **kwargs):
        super().__init__(name="simple")

    def run(self) -> CheckResult:
        return CheckResult(passed=True, message="ok")


def test_circuit_breaker_is_in_available():
    _ensure_builtins()
    assert "circuit_breaker" in registry.available()


def test_registry_get_returns_circuit_breaker_class():
    _ensure_builtins()
    cls = registry.get("circuit_breaker")
    assert cls is CircuitBreakerCheck


def test_circuit_breaker_instantiation_via_registry():
    _ensure_builtins()
    cls = registry.get("circuit_breaker")
    inner = _SimplePass()
    cb = cls(wrapped=inner, threshold=2, reset_timeout=30)
    assert isinstance(cb, CircuitBreakerCheck)
    result = cb.run()
    assert result.passed is True
