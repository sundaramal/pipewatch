"""Ensure TransformedCheck integrates with the registry and factory."""
import pytest
from pipewatch.checks.registry import get, available, register_builtins
from pipewatch.checks.transformed import TransformedCheck
from pipewatch.checks.base import BaseCheck, CheckResult


def _ensure_builtins():
    register_builtins()


class _SimpleCheck(BaseCheck):
    def __init__(self, name, value=1, min_val=0, **kwargs):
        super().__init__(name)
        self._value = value
        self._min_val = min_val

    def run(self) -> CheckResult:
        passed = self._value >= self._min_val
        return CheckResult(self.name, passed, str(self._value))


def test_transformed_check_can_be_instantiated_directly():
    inner = _SimpleCheck("s", value=-1, min_val=0)
    tc = TransformedCheck("t", transform="abs", wrapped=inner)
    result = tc.run()
    assert result.passed


def test_all_builtin_transforms_work():
    transforms = {
        "abs": (-5, 0, True),
        "negate": (5, 0, False),
        "percent_of_100": (0.5, 40, True),
    }
    for name, (val, min_val, expected) in transforms.items():
        inner = _SimpleCheck("s", value=val, min_val=min_val)
        tc = TransformedCheck("t", transform=name, wrapped=inner)
        assert tc.run().passed == expected, f"Failed for transform '{name}'"


def test_transform_does_not_mutate_wrapped_permanently():
    inner = _SimpleCheck("s", value=-10, min_val=0)
    tc = TransformedCheck("t", transform="abs", wrapped=inner)
    tc.run()
    tc.run()
    assert inner._value == -10
