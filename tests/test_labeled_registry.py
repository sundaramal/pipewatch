"""Ensure LabeledCheck is registered and accessible via the registry."""
import pytest
from pipewatch.checks import registry
from pipewatch.checks.labeled import LabeledCheck


def _ensure_builtins():
    registry.register_builtins()


def test_labeled_is_in_available():
    _ensure_builtins()
    assert "labeled" in registry.available()


def test_registry_get_returns_labeled_class():
    _ensure_builtins()
    assert registry.get("labeled") is LabeledCheck


def test_labeled_via_registry_run_pass():
    from pipewatch.checks.base import BaseCheck, CheckResult

    _ensure_builtins()

    class _P(BaseCheck):
        def __init__(self):
            super().__init__(name="p")
        def run(self):
            return CheckResult(passed=True, message="fine")

    check = LabeledCheck(wrapped=_P(), labels={"x": "y"})
    result = check.run()
    assert result.passed is True
    assert "x=y" in result.message
