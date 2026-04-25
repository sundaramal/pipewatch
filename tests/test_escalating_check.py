"""Tests for EscalatingCheck."""
from __future__ import annotations

import pytest

from pipewatch.checks.base import BaseCheck, CheckResult
from pipewatch.checks.escalating import EscalatingCheck


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

class _PassCheck(BaseCheck):
    def __init__(self) -> None:
        super().__init__(name="pass")

    def run(self) -> CheckResult:
        return CheckResult(passed=True, message="ok")


class _FailCheck(BaseCheck):
    def __init__(self) -> None:
        super().__init__(name="fail")

    def run(self) -> CheckResult:
        return CheckResult(passed=False, message="bad")


class _ToggleCheck(BaseCheck):
    """Fails on odd-numbered calls, passes on even."""

    def __init__(self) -> None:
        super().__init__(name="toggle")
        self._calls = 0

    def run(self) -> CheckResult:
        self._calls += 1
        if self._calls % 2 == 1:
            return CheckResult(passed=False, message="odd fail")
        return CheckResult(passed=True, message="even pass")


# ---------------------------------------------------------------------------
# Basic behaviour
# ---------------------------------------------------------------------------

def test_pass_through_on_success():
    check = EscalatingCheck(_PassCheck())
    result = check.run()
    assert result.passed
    assert check.level == 0


def test_level_increments_on_each_failure():
    check = EscalatingCheck(_FailCheck(), max_level=5)
    for expected_level in range(1, 4):
        result = check.run()
        assert not result.passed
        assert check.level == expected_level


def test_level_capped_at_max_level():
    check = EscalatingCheck(_FailCheck(), max_level=2)
    check.run()
    check.run()
    check.run()  # would be 3, should stay at 2
    assert check.level == 2


def test_level_message_contains_level_info():
    check = EscalatingCheck(_FailCheck(), max_level=3)
    check.run()  # level 1
    result = check.run()  # level 2
    assert "level 2/3" in result.message
    assert "bad" in result.message


def test_level_resets_after_pass():
    check = EscalatingCheck(_ToggleCheck(), max_level=5)
    check.run()  # fail → level 1
    check.run()  # pass → level 0
    assert check.level == 0


def test_level_resumes_after_reset_and_new_failure():
    check = EscalatingCheck(_ToggleCheck(), max_level=5)
    check.run()  # fail → 1
    check.run()  # pass → 0
    check.run()  # fail → 1
    assert check.level == 1


def test_manual_reset():
    check = EscalatingCheck(_FailCheck(), max_level=3)
    check.run()
    check.run()
    assert check.level == 2
    check.reset()
    assert check.level == 0


# ---------------------------------------------------------------------------
# Constructor validation
# ---------------------------------------------------------------------------

def test_invalid_max_level_raises():
    with pytest.raises(ValueError, match="max_level"):
        EscalatingCheck(_PassCheck(), max_level=0)


def test_default_name_includes_wrapped_name():
    check = EscalatingCheck(_PassCheck())
    assert "pass" in check.name


def test_custom_name_is_used():
    check = EscalatingCheck(_PassCheck(), name="my_escalating")
    assert check.name == "my_escalating"


def test_wrapped_property_returns_inner_check():
    inner = _FailCheck()
    check = EscalatingCheck(inner)
    assert check.wrapped is inner


def test_max_level_property():
    check = EscalatingCheck(_PassCheck(), max_level=7)
    assert check.max_level == 7
