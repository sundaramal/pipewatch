"""Tests that ChainedCheck is registered and usable via the registry."""
import pytest
from pipewatch.checks.registry import get, available, register_builtins
from pipewatch.checks.chained import ChainedCheck
from pipewatch.checks.base import BaseCheck, CheckResult


def _ensure_builtins():
    register_builtins()


def test_chained_is_in_available():
    _ensure_builtins()
    assert "chained" in available()


def test_registry_get_returns_chained_class():
    _ensure_builtins()
    assert get("chained") is ChainedCheck


def test_chained_via_registry_all_pass():
    _ensure_builtins()
    cls = get("chained")

    class _P(BaseCheck):
        def __init__(self):
            super().__init__("p")
        def run(self):
            return CheckResult(passed=True, message="ok")

    c = cls("chain", checks=[_P(), _P()])
    result = c.run()
    assert result.passed


def test_chained_via_registry_stops_on_fail():
    _ensure_builtins()
    cls = get("chained")

    class _F(BaseCheck):
        def __init__(self):
            super().__init__("f")
        def run(self):
            return CheckResult(passed=False, message="fail")

    c = cls("chain", checks=[_F()])
    result = c.run()
    assert not result.passed
