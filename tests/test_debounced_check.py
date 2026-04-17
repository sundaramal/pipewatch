"""Tests for DebouncedCheck."""
import pytest
from pipewatch.checks.base import BaseCheck, CheckResult
from pipewatch.checks.debounced import DebouncedCheck


class _PassCheck(BaseCheck):
    def __init__(self):
        super().__init__("pass")

    def run(self) -> CheckResult:
        return CheckResult(name=self.name, passed=True, message="ok")


class _FailCheck(BaseCheck):
    def __init__(self):
        super().__init__("fail")

    def run(self) -> CheckResult:
        return CheckResult(name=self.name, passed=False, message="bad")


def test_debounced_passes_when_wrapped_passes():
    check = DebouncedCheck("d", _PassCheck(), threshold=2)
    assert check.run().passed


def test_debounced_suppresses_first_failure():
    check = DebouncedCheck("d", _FailCheck(), threshold=3)
    result = check.run()
    assert result.passed, "first failure should be suppressed"
    assert "suppressed" in result.message


def test_debounced_suppresses_until_threshold():
    check = DebouncedCheck("d", _FailCheck(), threshold=3)
    check.run()  # 1 — suppressed
    result = check.run()  # 2 — suppressed
    assert result.passed


def test_debounced_fails_at_threshold():
    check = DebouncedCheck("d", _FailCheck(), threshold=3)
    check.run()
    check.run()
    result = check.run()  # 3rd — should fail
    assert not result.passed
    assert "threshold=3" in result.message


def test_debounced_continues_failing_beyond_threshold():
    check = DebouncedCheck("d", _FailCheck(), threshold=2)
    check.run()
    for _ in range(5):
        result = check.run()
        assert not result.passed


def test_debounced_resets_counter_on_pass():
    class _Flaky(BaseCheck):
        def __init__(self):
            super().__init__("flaky")
            self._calls = 0

        def run(self) -> CheckResult:
            self._calls += 1
            passed = self._calls % 3 != 0
            return CheckResult(name=self.name, passed=passed, message="")

    check = DebouncedCheck("d", _Flaky(), threshold=2)
    check.run()   # call 1 — pass
    check.run()   # call 2 — pass
    result = check.run()  # call 3 — fail (1st consecutive)
    assert result.passed, "first failure suppressed after reset"


def test_debounced_threshold_one_fails_immediately():
    check = DebouncedCheck("d", _FailCheck(), threshold=1)
    result = check.run()
    assert not result.passed


def test_debounced_invalid_threshold_raises():
    with pytest.raises(ValueError):
        DebouncedCheck("d", _PassCheck(), threshold=0)


def test_debounced_wrapped_property():
    inner = _PassCheck()
    check = DebouncedCheck("d", inner, threshold=2)
    assert check.wrapped is inner
    assert check.threshold == 2
