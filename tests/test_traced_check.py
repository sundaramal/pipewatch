"""Tests for TracedCheck."""

from __future__ import annotations

import pytest

from pipewatch.checks.base import BaseCheck, CheckResult
from pipewatch.checks.traced import TracedCheck, TraceEntry


class _PassCheck(BaseCheck):
    def __init__(self) -> None:
        super().__init__(name="pass")

    def run(self) -> CheckResult:
        return CheckResult(passed=True, message="ok")


class _FailCheck(BaseCheck):
    def __init__(self) -> None:
        super().__init__(name="fail")

    def run(self) -> CheckResult:
        return CheckResult(passed=False, message="boom")


def test_traced_passes_through_pass_result():
    tc = TracedCheck(_PassCheck())
    result = tc.run()
    assert result.passed is True


def_fail_result():
    tc = TracedCheck(_FailCheck())
    result = tc.run()
    assert result.passed is False


def test_trace_records_entry_after_run():
    tc = TracedCheck(_PassCheck())
    assert tc.trace == []
    tc.run()
    assert len(tc.trace) == 1


def test_trace_entry_fields():
    tc = TracedCheck(_PassCheck())
    tc.run()
    entry = tc.trace[0]
    assert isinstance(entry, TraceEntry)
    assert entry.passed is True
    assert entry.message == "ok"
    assert entry.duration_seconds >= 0
    assert entry.started_at > 0


def test_trace_accumulates_multiple_runs():
    tc = TracedCheck(_PassCheck())
    for _ in range(5):
        tc.run()
    assert len(tc.trace) == 5


def test_trace_respects_max_entries():
    tc = TracedCheck(_PassCheck(), max_entries=3)
    for _ in range(10):
        tc.run()
    assert len(tc.trace) == 3


def test_trace_drops_oldest_when_full():
    tc = TracedCheck(_FailCheck(), max_entries=2)
    # First run — fail
    tc.run()
    # Swap to pass via a fresh check — simulate by running twice more
    tc2 = TracedCheck(_PassCheck(), max_entries=2)
    tc2.run()
    tc2.run()
    # Only the 2 most recent should remain
    assert len(tc2.trace) == 2


def test_trace_unlimited_when_max_entries_none():
    tc = TracedCheck(_PassCheck(), max_entries=None)
    for _ in range(200):
        tc.run()
    assert len(tc.trace) == 200


def test_clear_trace_empties_entries():
    tc = TracedCheck(_PassCheck())
    tc.run()
    tc.run()
    tc.clear_trace()
    assert tc.trace == []


def test_trace_returns_copy():
    tc = TracedCheck(_PassCheck())
    tc.run()
    copy = tc.trace
    copy.clear()
    assert len(tc.trace) == 1


def test_default_name_includes_wrapped_name():
    tc = TracedCheck(_PassCheck())
    assert "pass" in tc.name


def test_custom_name_is_used():
    tc = TracedCheck(_PassCheck(), name="my_traced")
    assert tc.name == "my_traced"


def test_wrapped_property_returns_inner_check():
    inner = _PassCheck()
    tc = TracedCheck(inner)
    assert tc.wrapped is inner
