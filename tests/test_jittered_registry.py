"""Ensure JitteredCheck is registered and usable via the registry."""

from __future__ import annotations

from pipewatch.checks.base import BaseCheck, CheckResult
from pipewatch.checks import registry
from pipewatch.checks.jittered import JitteredCheck


def _ensure_builtins():
    registry.register_builtins()


class _SimplePass(BaseCheck):
    def __init__(self, **kwargs):
        super().__init__(name="simple")

    def run(self) -> CheckResult:
        return CheckResult(name=self.name, passed=True, message="ok")


def test_jittered_is_in_available():
    _ensure_builtins()
    assert "jittered" in registry.available()


def test_registry_get_returns_jittered_class():
    _ensure_builtins()
    cls = registry.get("jittered")
    assert cls is JitteredCheck


def test_jittered_wraps_and_runs():
    _ensure_builtins()
    inner = _SimplePass()
    check = JitteredCheck(inner, min_delay=0.0, max_delay=0.0)
    result = check.run()
    assert result.passed is True
    assert "jitter=" in result.message
