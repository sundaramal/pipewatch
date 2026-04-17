"""Tests for JitteredCheck."""

from __future__ import annotations

import pytest

from pipewatch.checks.base import BaseCheck, CheckResult
from pipewatch.checks.jittered import JitteredCheck


class _PassCheck(BaseCheck):
    def __init__(self):
        super().__init__(name="pass")

    def run(self) -> CheckResult:
        return CheckResult(name=self.name, passed=True, message="ok")


class _FailCheck(BaseCheck):
    def __init__(self):
        super().__init__(name="fail")

    def run(self) -> CheckResult:
        return CheckResult(name=self.name, passed=False, message="bad")


def test_jittered_passes_when_wrapped_passes():
    check = JitteredCheck(_PassCheck(), min_delay=0.0, max_delay=0.0)
    result = check.run()
    assert result.passed is True


def test_jittered_fails_when_wrapped_fails():
    check = JitteredCheck(_FailCheck(), min_delay=0.0, max_delay=0.0)
    result = check.run()
    assert result.passed is False


def test_jittered_message_contains_jitter_prefix():
    check = JitteredCheck(_PassCheck(), min_delay=0.0, max_delay=0.0)
    result = check.run()
    assert "jitter=" in result.message


def test_jittered_default_name_reflects_wrapped():
    check = JitteredCheck(_PassCheck())
    assert "pass" in check.name


def test_jittered_custom_name():
    check = JitteredCheck(_PassCheck(), name="my_jittered")
    assert check.name == "my_jittered"


def test_jittered_wrapped_property():
    inner = _PassCheck()
    check = JitteredCheck(inner, min_delay=0.0, max_delay=0.0)
    assert check.wrapped is inner


def test_jittered_raises_for_negative_min_delay():
    with pytest.raises(ValueError, match="non-negative"):
        JitteredCheck(_PassCheck(), min_delay=-0.1, max_delay=1.0)


def test_jittered_raises_for_negative_max_delay():
    with pytest.raises(ValueError, match="non-negative"):
        JitteredCheck(_PassCheck(), min_delay=0.0, max_delay=-1.0)


def test_jittered_raises_when_min_exceeds_max():
    with pytest.raises(ValueError, match="min_delay"):
        JitteredCheck(_PassCheck(), min_delay=2.0, max_delay=1.0)


def test_jittered_result_name_matches_check_name():
    check = JitteredCheck(_PassCheck(), min_delay=0.0, max_delay=0.0, name="j")
    result = check.run()
    assert result.name == "j"
