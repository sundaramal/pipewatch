"""Tests for StaggeredCheck."""
from __future__ import annotations

import pytest

from pipewatch.checks.base import BaseCheck, CheckResult
from pipewatch.checks.staggered import StaggeredCheck


class _PassCheck(BaseCheck):
    def __init__(self, name: str = "pass") -> None:
        super().__init__(name=name)
        self.runs = 0

    def run(self) -> CheckResult:
        self.runs += 1
        return CheckResult(passed=True, name=self.name, message="ok")


class _FailCheck(BaseCheck):
    def __init__(self, name: str = "fail") -> None:
        super().__init__(name=name)
        self.runs = 0

    def run(self) -> CheckResult:
        self.runs += 1
        return CheckResult(passed=False, name=self.name, message="nope")


# ---------------------------------------------------------------------------
# construction
# ---------------------------------------------------------------------------

def test_default_name_comes_from_wrapped():
    inner = _PassCheck(name="my-check")
    sc = StaggeredCheck(inner, every=3)
    assert sc.name == "my-check"


def test_custom_name_overrides_wrapped():
    inner = _PassCheck(name="inner")
    sc = StaggeredCheck(inner, every=3, name="outer")
    assert sc.name == "outer"


def test_invalid_every_raises():
    with pytest.raises(ValueError, match="every"):
        StaggeredCheck(_PassCheck(), every=0)


def test_invalid_offset_raises():
    with pytest.raises(ValueError, match="offset"):
        StaggeredCheck(_PassCheck(), every=3, offset=3)


def test_negative_offset_raises():
    with pytest.raises(ValueError, match="offset"):
        StaggeredCheck(_PassCheck(), every=3, offset=-1)


# ---------------------------------------------------------------------------
# execution pattern
# ---------------------------------------------------------------------------

def test_fires_on_correct_slot_default_offset():
    """With every=3, offset=0 the check fires on calls 0, 3, 6, …"""
    inner = _PassCheck()
    sc = StaggeredCheck(inner, every=3, offset=0)

    r0 = sc.run()  # slot 0 — fires
    r1 = sc.run()  # slot 1 — skipped
    r2 = sc.run()  # slot 2 — skipped
    r3 = sc.run()  # slot 0 again — fires

    assert inner.runs == 2
    assert r0.passed is True
    assert r1.passed is True  # cached from r0
    assert r2.passed is True  # cached from r0
    assert r3.passed is True


def test_fires_on_correct_slot_non_zero_offset():
    inner = _PassCheck()
    sc = StaggeredCheck(inner, every=4, offset=2)

    sc.run()  # slot 0 — skip
    sc.run()  # slot 1 — skip
    sc.run()  # slot 2 — fires
    sc.run()  # slot 3 — skip
    sc.run()  # slot 0 — skip
    sc.run()  # slot 1 — skip
    sc.run()  # slot 2 — fires

    assert inner.runs == 2


def test_skipped_call_returns_last_result():
    inner = _FailCheck()
    sc = StaggeredCheck(inner, every=2, offset=0)

    r0 = sc.run()  # fires — fail
    r1 = sc.run()  # skipped — should return cached fail

    assert r0.passed is False
    assert r1.passed is False
    assert r1.message == "nope"


def test_first_skipped_call_returns_neutral_pass_when_no_prior_result():
    inner = _FailCheck()
    sc = StaggeredCheck(inner, every=3, offset=1)  # slot 0 is skipped

    r0 = sc.run()  # slot 0 — skipped, no prior result
    assert r0.passed is True
    assert "skipped" in r0.message
    assert inner.runs == 0


def test_call_count_increments_on_every_call():
    sc = StaggeredCheck(_PassCheck(), every=5)
    for i in range(7):
        sc.run()
    assert sc.call_count == 7


def test_every_one_always_fires():
    inner = _PassCheck()
    sc = StaggeredCheck(inner, every=1, offset=0)
    for _ in range(5):
        sc.run()
    assert inner.runs == 5


def test_wrapped_property():
    inner = _PassCheck()
    sc = StaggeredCheck(inner, every=2)
    assert sc.wrapped is inner


def test_every_and_offset_properties():
    sc = StaggeredCheck(_PassCheck(), every=6, offset=3)
    assert sc.every == 6
    assert sc.offset == 3
