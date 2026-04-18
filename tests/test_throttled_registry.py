"""Verify ThrottledCheck is registered and usable via the registry."""
from __future__ import annotations

from pipewatch.checks.base import BaseCheck, CheckResult
from pipewatch.checks import registry
from pipewatch.checks.throttled import ThrottledCheck


def _ensure_builtins():
    registry.register_builtins()


class _SimplePass(BaseCheck):
    def __init__(self):
        super().__init__(name="simple")

    def run(self) -> CheckResult:
        return CheckResult(passed=True, name=self.name, message="ok")


def test_throttled_is_in_available():
    _ensure_builtins()
    assert "throttled" in registry.available()


def test_registry_get_returns_throttled_class():
    _ensure_builtins()
    cls = registry.get("throttled")
    assert cls is ThrottledCheck


def test_throttled_via_registry_run_pass():
    _ensure_builtins()
    cls = registry.get("throttled")
    inner = _SimplePass()
    check = cls(wrapped=inner, max_calls=2, window_seconds=30)
    result = check.run()
    assert result.passed
