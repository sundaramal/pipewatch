"""Tests for FallbackCheck."""

import pytest
from pipewatch.checks.base import BaseCheck, CheckResult
from pipewatch.checks.fallback import FallbackCheck


class _PassCheck(BaseCheck):
    def __init__(self, msg="ok"):
        super().__init__(name="pass")
        self._msg = msg

    def run(self) -> CheckResult:
        return CheckResult(name=self.name, passed=True, message=self._msg)


class _FailCheck(BaseCheck):
    def __init__(self, msg="fail"):
        super().__init__(name="fail")
        self._msg = msg

    def run(self) -> CheckResult:
        return CheckResult(name=self.name, passed=False, message=self._msg)


class _RaisingCheck(BaseCheck):
    def __init__(self):
        super().__init__(name="raiser")

    def run(self) -> CheckResult:
        raise RuntimeError("boom")


def test_fallback_passes_when_primary_passes():
    fc = FallbackCheck(_PassCheck(), _FailCheck())
    result = fc.run()
    assert result.passed


def test_fallback_uses_fallback_when_primary_fails():
    fc = FallbackCheck(_FailCheck(), _PassCheck(msg="recovered"))
    result = fc.run()
    assert result.passed
    assert "recovered" in result.message


def test_fallback_fails_when_both_fail():
    fc = FallbackCheck(_FailCheck(msg="p"), _FailCheck(msg="f"))
    result = fc.run()
    assert not result.passed
    assert "p" in result.message


def test_fallback_catches_primary_exception():
    fc = FallbackCheck(_RaisingCheck(), _PassCheck(msg="safe"))
    result = fc.run()
    assert result.passed
    assert "boom" in result.message


def test_fallback_name_default():
    fc = FallbackCheck(_PassCheck(), _PassCheck())
    assert fc.name == "fallback"


def test_fallback_custom_name():
    fc = FallbackCheck(_PassCheck(), _PassCheck(), name="my_fallback")
    assert fc.name == "my_fallback"


def test_fallback_wrapped_property():
    primary = _PassCheck()
    fc = FallbackCheck(primary, _FailCheck())
    assert fc.wrapped is primary


def test_fallback_fallback_property():
    fallback = _PassCheck()
    fc = FallbackCheck(_FailCheck(), fallback)
    assert fc.fallback is fallback
