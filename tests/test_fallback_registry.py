"""Tests that FallbackCheck integrates with the registry and factory."""

import pytest
from pipewatch.checks.registry import available, get, register_builtins
from pipewatch.checks.fallback import FallbackCheck
from pipewatch.checks.factory import build_check
from pipewatch.checks.base import BaseCheck, CheckResult


def _ensure_builtins():
    register_builtins()


class _SimplePass(BaseCheck):
    def __init__(self, **kwargs):
        super().__init__(name=kwargs.get("name", "simple"))

    def run(self) -> CheckResult:
        return CheckResult(name=self.name, passed=True, message="ok")


def test_fallback_is_in_available():
    _ensure_builtins()
    assert "fallback" in available()


def test_registry_get_returns_fallback_class():
    _ensure_builtins()
    assert get("fallback") is FallbackCheck


def test_fallback_via_factory_runs():
    _ensure_builtins()
    from pipewatch.checks.registry import register
    register("_simple_pass", _SimplePass)

    check = build_check(
        "fallback",
        {
            "primary": {"type": "_simple_pass"},
            "fallback": {"type": "_simple_pass"},
        },
    )
    result = check.run()
    assert result.passed
