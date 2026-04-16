"""Tests for NegatedCheck."""

import pytest

from pipewatch.checks.base import BaseCheck, CheckResult
from pipewatch.checks.negated import NegatedCheck


class _PassCheck(BaseCheck):
    def __init__(self):
        super().__init__("inner_pass", {})

    def run(self) -> CheckResult:
        return CheckResult(check_name=self.name, passed=True, message="ok")


class _FailCheck(BaseCheck):
    def __init__(self):
        super().__init__("inner_fail", {})

    def run(self) -> CheckResult:
        return CheckResult(check_name=self.name, passed=False, message="bad")


def test_negated_fails_when_inner_passes():
    check = NegatedCheck("neg", {"check": _PassCheck()})
    result = check.run()
    assert not result.passed


def test_negated_passes_when_inner_fails():
    check = NegatedCheck("neg", {"check": _FailCheck()})
    result = check.run()
    assert result.passed


def test_negated_message_contains_inner_message_on_pass():
    check = NegatedCheck("neg", {"check": _FailCheck()})
    result = check.run()
    assert "bad" in result.message


def test_negated_message_contains_inner_message_on_fail():
    check = NegatedCheck("neg", {"check": _PassCheck()})
    result = check.run()
    assert "ok" in result.message


def test_negated_custom_fail_message():
    check = NegatedCheck(
        "neg", {"check": _PassCheck(), "fail_message": "should not pass"}
    )
    result = check.run()
    assert result.message == "should not pass"


def test_negated_check_name_in_result():
    check = NegatedCheck("my_negated", {"check": _FailCheck()})
    result = check.run()
    assert result.check_name == "my_negated"


def test_negated_raises_without_check_param():
    with pytest.raises(ValueError, match="requires a 'check' param"):
        NegatedCheck("neg", {})


def test_negated_raises_for_non_basecheck():
    with pytest.raises(TypeError, match="BaseCheck instance"):
        NegatedCheck("neg", {"check": "not-a-check"})


def test_wrapped_property_returns_inner_check():
    inner = _PassCheck()
    check = NegatedCheck("neg", {"check": inner})
    assert check.wrapped is inner
