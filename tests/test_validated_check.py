"""Tests for ValidatedCheck."""
from __future__ import annotations

import pytest

from pipewatch.checks.base import BaseCheck, CheckResult
from pipewatch.checks.validated import ValidatedCheck


class _PassCheck(BaseCheck):
    def __init__(self, msg: str = "ok"):
        super().__init__(name="pass")
        self._msg = msg

    def run(self) -> CheckResult:
        return CheckResult(passed=True, message=self._msg)


class _FailCheck(BaseCheck):
    def __init__(self, msg: str = "bad"):
        super().__init__(name="fail")
        self._msg = msg

    def run(self) -> CheckResult:
        return CheckResult(passed=False, message=self._msg)


# ---------------------------------------------------------------------------
# Basic pass-through behaviour
# ---------------------------------------------------------------------------

def test_validated_passes_when_validator_accepts():
    check = ValidatedCheck(_PassCheck(), validator=lambda r: True)
    result = check.run()
    assert result.passed is True


def test_validated_fails_when_validator_rejects():
    check = ValidatedCheck(_PassCheck(), validator=lambda r: False, message="nope")
    result = check.run()
    assert result.passed is False
    assert "nope" in result.message


def test_validated_fails_when_validator_raises():
    def boom(r):
        raise RuntimeError("explodedn    check = ValidatedCheck(_PassCheck(), validator=boom)
    result = check.run()
    assert result.passed is False
    assert "exploded" in result.message


def test_validated_propagates_inner_fail = _FailCheck(msg="inner error")
    check = ValidatedCheck(inner, validator=lambda r: True)
    result = check.run()
    # validator accepts, so inner result passes through unchanged
    assert result.passed is False
    assert result.message == "inner error"


def test_validated_rejects_passing_inner_with_require_fail_validator():
    check = ValidatedCheck(_PassCheck(), validator=lambda r: not r.passed)
    result = check.run()
    assert result.passed is False


def test_validated_name_defaults_to_wrapped_name():
    check = ValidatedCheck(_PassCheck(), validator=lambda r: True)
    assert "pass" in check.name


def test_validated_name_override():
    check = ValidatedCheck(_PassCheck(), validator=lambda r: True, name="my_check")
    assert check.name == "my_check"


def test_wrapped_property_returns_inner_check():
    inner = _PassCheck()
    check = ValidatedCheck(inner, validator=lambda r: True)
    assert check.wrapped is inner


def test_validator_receives_actual_result_object():
    received = []

    def capturing_validator(r: CheckResult) -> bool:
        received.append(r)
        return True

    inner = _PassCheck(msg="hello")
    check = ValidatedCheck(inner, validator=capturing_validator)
    check.run()
    assert len(received) == 1
    assert received[0].message == "hello"
