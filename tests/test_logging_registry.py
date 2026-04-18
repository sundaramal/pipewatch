"""Ensure LoggingCheck is registered and usable via the registry."""
from __future__ import annotations

from pipewatch.checks.base import BaseCheck, CheckResult
from pipewatch.checks import registry


def _ensure_builtins():
    registry.register_builtins()


class _SimplePass(BaseCheck):
    def __init__(self):
        super().__init__(name="sp")

    def run(self) -> CheckResult:
        return CheckResult(passed=True, message="ok")


def test_logging_is_in_available():
    _ensure_builtins()
    assert "logging" in registry.available()


def test_registry_get_returns_logging_class():
    _ensure_builtins()
    from pipewatch.checks.logging_check import LoggingCheck
    assert registry.get("logging") is LoggingCheck


def test_logging_check_via_registry_run_pass():
    _ensure_builtins()
    cls = registry.get("logging")
    inner = _SimplePass()
    lc = cls(check=inner)
    result = lc.run()
    assert result.passed is True
