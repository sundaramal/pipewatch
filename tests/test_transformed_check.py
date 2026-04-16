"""Tests for TransformedCheck."""
import pytest
from pipewatch.checks.base import BaseCheck, CheckResult
from pipewatch.checks.transformed import TransformedCheck


class _ValueCheck(BaseCheck):
    """Check that passes when _value >= min_val."""

    def __init__(self, name, value, min_val=0):
        super().__init__(name)
        self._value = value
        self._min_val = min_val

    def run(self) -> CheckResult:
        passed = self._value >= self._min_val
        return CheckResult(
            check_name=self.name,
            passed=passed,
            message=f"{self._value} >= {self._min_val}" if passed else f"{self._value} < {self._min_val}",
        )


def test_transform_abs_makes_negative_pass():
    inner = _ValueCheck("inner", value=-5, min_val=0)
    check = TransformedCheck("tc", transform="abs", wrapped=inner)
    result = check.run()
    assert result.passed
    assert "transformed" in result.message


def test_transform_negate_makes_positive_fail():
    inner = _ValueCheck("inner", value=3, min_val=0)
    check = TransformedCheck("tc", transform="negate", wrapped=inner)
    result = check.run()
    assert not result.passed


def test_transform_percent_of_100():
    inner = _ValueCheck("inner", value=0.95, min_val=90)
    check = TransformedCheck("tc", transform="percent_of_100", wrapped=inner)
    result = check.run()
    assert result.passed  # 0.95 * 100 = 95 >= 90


def test_transform_callable():
    inner = _ValueCheck("inner", value=10, min_val=0)
    check = TransformedCheck("tc", transform=lambda x: x - 20, wrapped=inner)
    result = check.run()
    assert not result.passed  # 10 - 20 = -10 < 0


def test_unknown_transform_raises():
    inner = _ValueCheck("inner", value=1, min_val=0)
    with pytest.raises(ValueError, match="Unknown transform"):
        TransformedCheck("tc", transform="nonexistent", wrapped=inner)


def test_wrapped_property():
    inner = _ValueCheck("inner", value=1, min_val=0)
    check = TransformedCheck("tc", transform="abs", wrapped=inner)
    assert check.wrapped is inner


def test_original_value_restored_after_run():
    inner = _ValueCheck("inner", value=-3, min_val=0)
    check = TransformedCheck("tc", transform="abs", wrapped=inner)
    check.run()
    assert inner._value == -3


def test_check_name_propagated():
    inner = _ValueCheck("inner", value=5, min_val=0)
    check = TransformedCheck("my_transform", transform="abs", wrapped=inner)
    result = check.run()
    assert result.check_name == "my_transform"
