"""Tests for ParallelCheck."""
from __future__ import annotations

import time
from pipewatch.checks.base import BaseCheck, CheckResult
from pipewatch.checks.parallel import ParallelCheck


class _PassCheck(BaseCheck):
    def __init__(self, name: str = "pass") -> None:
        super().__init__(name)

    def run(self) -> CheckResult:
        return CheckResult(passed=True, message="ok")


class _FailCheck(BaseCheck):
    def __init__(self, name: str = "fail") -> None:
        super().__init__(name)

    def run(self) -> CheckResult:
        return CheckResult(passed=False, message="bad")


class _SlowCheck(BaseCheck):
    def __init__(self, delay: float, name: str = "slow") -> None:
        super().__init__(name)
        self._delay = delay

    def run(self) -> CheckResult:
        time.sleep(self._delay)
        return CheckResult(passed=True, message="done")


# ---------------------------------------------------------------------------

def test_parallel_passes_when_all_sub_checks_pass():
    pc = ParallelCheck(name="p", checks=[_PassCheck("a"), _PassCheck("b")])
    result = pc.run()
    assert result.passed


def test_parallel_fails_when_any_sub_check_fails():
    pc = ParallelCheck(name="p", checks=[_PassCheck("a"), _FailCheck("b")])
    result = pc.run()
    assert not result.passed


def test_parallel_message_contains_sub_check_names():
    pc = ParallelCheck(name="p", checks=[_PassCheck("alpha"), _FailCheck("beta")])
    result = pc.run()
    assert "alpha" in result.message
    assert "beta" in result.message


def test_parallel_no_checks_passes():
    pc = ParallelCheck(name="empty")
    result = pc.run()
    assert result.passed


def test_parallel_add_check():
    pc = ParallelCheck(name="p")
    pc.add_check(_PassCheck("x"))
    assert len(pc.checks) == 1


def test_parallel_checks_property_returns_copy():
    inner = _PassCheck("x")
    pc = ParallelCheck(name="p", checks=[inner])
    lst = pc.checks
    lst.clear()
    assert len(pc.checks) == 1


def test_parallel_runs_concurrently():
    """Three 0.2 s checks should finish well under 0.6 s if truly parallel."""
    checks = [_SlowCheck(0.2, name=f"s{i}") for i in range(3)]
    pc = ParallelCheck(name="p", checks=checks, timeout=5.0)
    start = time.monotonic()
    result = pc.run()
    elapsed = time.monotonic() - start
    assert result.passed
    assert elapsed < 0.55


def test_parallel_timeout_marks_slow_check_failed():
    pc = ParallelCheck(
        name="p",
        checks=[_SlowCheck(5.0, name="tortoise")],
        timeout=0.1,
    )
    result = pc.run()
    assert not result.passed
    assert "timed out" in result.message
