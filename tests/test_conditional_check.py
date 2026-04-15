"""Tests for :class:`pipewatch.checks.conditional.ConditionalCheck`."""

from __future__ import annotations

from pipewatch.checks.base import BaseCheck, CheckResult
from pipewatch.checks.conditional import ConditionalCheck


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

class _PassCheck(BaseCheck):
    def __init__(self) -> None:
        super().__init__(name="inner_pass")

    def run(self) -> CheckResult:
        return CheckResult(check_name=self.name, passed=True, message="ok")


class _FailCheck(BaseCheck):
    def __init__(self) -> None:
        super().__init__(name="inner_fail")

    def run(self) -> CheckResult:
        return CheckResult(check_name=self.name, passed=False, message="bad")


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_runs_inner_when_condition_true() -> None:
    check = ConditionalCheck(inner=_PassCheck(), condition=lambda: True)
    result = check.run()
    assert result.passed is True
    assert "inner_pass" in result.check_name


def test_skips_inner_when_condition_false() -> None:
    check = ConditionalCheck(inner=_FailCheck(), condition=lambda: False)
    result = check.run()
    # Should pass (skipped), not propagate the inner failure
    assert result.passed is True


def test_skip_message_appears_in_result() -> None:
    msg = "env is not production"
    check = ConditionalCheck(
        inner=_FailCheck(), condition=lambda: False, skip_message=msg
    )
    result = check.run()
    assert result.message == msg


def test_failure_propagates_when_condition_true() -> None:
    check = ConditionalCheck(inner=_FailCheck(), condition=lambda: True)
    result = check.run()
    assert result.passed is False
    assert result.message == "bad"


def test_name_includes_inner_name() -> None:
    inner = _PassCheck()
    check = ConditionalCheck(inner=inner, condition=lambda: True)
    assert inner.name in check.name


def test_wrapped_property_returns_inner() -> None:
    inner = _PassCheck()
    check = ConditionalCheck(inner=inner, condition=lambda: True)
    assert check.wrapped is inner


def test_condition_evaluated_each_run() -> None:
    """Condition is re-evaluated on every call, not cached."""
    calls = [False, True]
    iterator = iter(calls)
    check = ConditionalCheck(inner=_FailCheck(), condition=lambda: next(iterator))

    first = check.run()   # condition=False → skip → pass
    second = check.run()  # condition=True  → run inner → fail

    assert first.passed is True
    assert second.passed is False


def test_conditional_registered_as_builtin() -> None:
    from pipewatch.checks.registry import available, register_builtins
    register_builtins()
    assert "conditional" in available()
