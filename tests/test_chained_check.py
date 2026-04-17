"""Tests for ChainedCheck."""
import pytest
from pipewatch.checks.base import BaseCheck, CheckResult
from pipewatch.checks.chained import ChainedCheck


class _PassCheck(BaseCheck):
    def __init__(self, name: str = "pass"):
        super().__init__(name)

    def run(self) -> CheckResult:
        return CheckResult(passed=True, message="ok")


class _FailCheck(BaseCheck):
    def __init__(self, name: str = "fail"):
        super().__init__(name)

    def run(self) -> CheckResult:
        return CheckResult(passed=False, message="bad")


def test_empty_chain_passes():
    c = ChainedCheck("empty")
    result = c.run()
    assert result.passed


def test_all_pass_returns_last_message():
    c = ChainedCheck("chain", [_PassCheck("a"), _PassCheck("b")])
    result = c.run()
    assert result.passed
    assert result.message == "ok"


def test_stops_at_first_failure():
    counter = {"runs": 0}

    class _CountingPass(BaseCheck):
        def __init__(self):
            super().__init__("counter")

        def run(self):
            counter["runs"] += 1
            return CheckResult(passed=True, message="counted")

    c = ChainedCheck("chain", [_FailCheck("first"), _CountingPass()])
    result = c.run()
    assert not result.passed
    assert "first" in result.message
    assert counter["runs"] == 0


def test_failure_message_includes_check_name():
    c = ChainedCheck("chain", [_PassCheck("step1"), _FailCheck("step2")])
    result = c.run()
    assert not result.passed
    assert "step2" in result.message


def test_add_check():
    c = ChainedCheck("chain")
    c.add_check(_PassCheck())
    assert len(c.checks) == 1


def test_checks_property_returns_copy():
    inner = _PassCheck()
    c = ChainedCheck("chain", [inner])
    copy = c.checks
    copy.append(_FailCheck())
    assert len(c.checks) == 1


def test_pass_then_fail_then_pass_stops_at_fail():
    c = ChainedCheck("chain", [_PassCheck("a"), _FailCheck("b"), _PassCheck("c")])
    result = c.run()
    assert not result.passed
    assert "b" in result.message
