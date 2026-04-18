"""Verify AnnotatedCheck is registered and usable via the registry."""
import pytest
from pipewatch.checks.registry import get, available, register_builtins
from pipewatch.checks.annotated import AnnotatedCheck
from pipewatch.checks.base import BaseCheck, CheckResult


def _ensure_builtins():
    register_builtins()


class _SimplePass(BaseCheck):
    def __init__(self):
        super().__init__(name="simple")

    def run(self) -> CheckResult:
        return CheckResult(name=self.name, passed=True, message="ok")


def test_annotated_is_in_available():
    _ensure_builtins()
    assert "annotated" in available()


def test_registry_get_returns_annotated_class():
    _ensure_builtins()
    cls = get("annotated")
    assert cls is AnnotatedCheck


def test_annotated_instantiated_via_registry_runs():
    _ensure_builtins()
    cls = get("annotated")
    check = cls(wrapped=_SimplePass(), annotations={"source": "registry-test"})
    result = check.run()
    assert result.passed is True
    assert result.details["source"] == "registry-test"
