"""Tests for :class:`pipewatch.checks.counted.CountedCheck`."""
from __future__ import annotations

import pytest

from pipewatch.checks.base import BaseCheck, CheckResult
from pipewatch.checks.counted import CountedCheck


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

class _PassCheck(BaseCheck):
    def __init__(self) -> None:
        super().__init__(name="pass")

    def run(self) -> CheckResult:
        return CheckResult(name=self.name, passed=True, message="ok")


class _FailCheck(BaseCheck):
    def __init__(self) -> None:
        super().__init__(name="fail")

    def run(self) -> CheckResult:
        return CheckResult(name=self.name, passed=False, message="nope")


# ---------------------------------------------------------------------------
# Construction
# ---------------------------------------------------------------------------

def test_counted_check_uses_wrapped_name_by_default():
    cc = CountedCheck(_PassCheck())
    assert cc.name == "pass"


def test_counted_check_accepts_custom_name():
    cc = CountedCheck(_PassCheck(), name="my_counted")
    assert cc.name == "my_counted"


def test_counted_check_raises_for_non_check():
    with pytest.raises(TypeError):
        CountedCheck("not-a-check")  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# Count tracking
# ---------------------------------------------------------------------------

def test_initial_count_is_zero():
    cc = CountedCheck(_PassCheck())
    assert cc.count == 0


def test_count_increments_on_each_run():
    cc = CountedCheck(_PassCheck())
    cc.run()
    cc.run()
    cc.run()
    assert cc.count == 3


def test_run_count_in_result_details():
    cc = CountedCheck(_PassCheck())
    result = cc.run()
    assert result.details["run_count"] == 1
    result2 = cc.run()
    assert result2.details["run_count"] == 2


# ---------------------------------------------------------------------------
# Pass / fail delegation
# ---------------------------------------------------------------------------

def test_counted_passes_when_wrapped_passes():
    cc = CountedCheck(_PassCheck())
    assert cc.run().passed is True


def test_counted_fails_when_wrapped_fails():
    cc = CountedCheck(_FailCheck())
    assert cc.run().passed is False


def test_counted_preserves_wrapped_message():
    cc = CountedCheck(_FailCheck())
    result = cc.run()
    assert result.message == "nope"


# ---------------------------------------------------------------------------
# Reset
# ---------------------------------------------------------------------------

def test_reset_sets_count_to_zero():
    cc = CountedCheck(_PassCheck())
    cc.run()
    cc.run()
    cc.reset()
    assert cc.count == 0


def test_count_resumes_after_reset():
    cc = CountedCheck(_PassCheck())
    cc.run()
    cc.reset()
    result = cc.run()
    assert cc.count == 1
    assert result.details["run_count"] == 1


# ---------------------------------------------------------------------------
# wrapped property
# ---------------------------------------------------------------------------

def test_wrapped_property_returns_inner_check():
    inner = _PassCheck()
    cc = CountedCheck(inner)
    assert cc.wrapped is inner
