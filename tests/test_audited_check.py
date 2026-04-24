"""Tests for pipewatch.checks.audited.AuditedCheck."""

from __future__ import annotations

import time

import pytest

from pipewatch.checks.base import BaseCheck, CheckResult
from pipewatch.checks.audited import AuditedCheck, AuditEntry


class _PassCheck(BaseCheck):
    def __init__(self, name: str = "pass") -> None:
        super().__init__(name=name)

    def run(self) -> CheckResult:
        return CheckResult(passed=True, message="ok")


class _FailCheck(BaseCheck):
    def __init__(self, name: str = "fail") -> None:
        super().__init__(name=name)

    def run(self) -> CheckResult:
        return CheckResult(passed=False, message="not ok")


# ---------------------------------------------------------------------------
# Basic delegation
# ---------------------------------------------------------------------------

def test_audited_passes_through_pass():
    check = AuditedCheck(_PassCheck())
    result = check.run()
    assert result.passed is True


def test_audited_passes_through_fail():
    check = AuditedCheck(_FailCheck())
    result = check.run()
    assert result.passed is False


# ---------------------------------------------------------------------------
# Audit log population
# ---------------------------------------------------------------------------

def test_audit_log_empty_before_run():
    check = AuditedCheck(_PassCheck())
    assert check.audit_log == []


def test_audit_log_has_one_entry_after_one_run():
    check = AuditedCheck(_PassCheck())
    check.run()
    assert len(check.audit_log) == 1


def test_audit_log_entry_fields_on_pass():
    check = AuditedCheck(_PassCheck(name="my_check"))
    check.run()
    entry: AuditEntry = check.audit_log[0]
    assert entry.name == "my_check"
    assert entry.passed is True
    assert entry.message == "ok"


def test_audit_log_entry_fields_on_fail():
    check = AuditedCheck(_FailCheck(name="bad_check"))
    check.run()
    entry: AuditEntry = check.audit_log[0]
    assert entry.passed is False
    assert entry.message == "not ok"


def test_audit_log_grows_with_multiple_runs():
    check = AuditedCheck(_PassCheck())
    for _ in range(5):
        check.run()
    assert len(check.audit_log) == 5


def test_audit_log_is_snapshot_not_live():
    """Mutating the returned list must not affect the internal log."""
    check = AuditedCheck(_PassCheck())
    check.run()
    snapshot = check.audit_log
    snapshot.clear()
    assert len(check.audit_log) == 1


# ---------------------------------------------------------------------------
# max_entries eviction
# ---------------------------------------------------------------------------

def test_max_entries_limits_log_size():
    check = AuditedCheck(_PassCheck(), max_entries=3)
    for _ in range(6):
        check.run()
    assert len(check.audit_log) == 3


def test_max_entries_drops_oldest():
    """After eviction the log should contain only the most recent entries."""
    inner_results = [True, False, True, False]

    class _SequenceCheck(BaseCheck):
        def __init__(self):
            super().__init__(name="seq")
            self._idx = 0

        def run(self) -> CheckResult:
            val = inner_results[self._idx % len(inner_results)]
            self._idx += 1
            return CheckResult(passed=val, message=str(val))

    check = AuditedCheck(_SequenceCheck(), max_entries=2)
    for _ in range(4):
        check.run()
    log = check.audit_log
    assert len(log) == 2
    # Last two results: True (idx=2), False (idx=3)
    assert log[0].passed is True
    assert log[1].passed is False


# ---------------------------------------------------------------------------
# clear()
# ---------------------------------------------------------------------------

def test_clear_empties_log():
    check = AuditedCheck(_PassCheck())
    check.run()
    check.run()
    check.clear()
    assert check.audit_log == []


# ---------------------------------------------------------------------------
# name override
# ---------------------------------------------------------------------------

def test_name_defaults_to_wrapped_name():
    check = AuditedCheck(_PassCheck(name="inner"))
    assert check.name == "inner"


def test_name_can_be_overridden():
    check = AuditedCheck(_PassCheck(name="inner"), name="outer")
    assert check.name == "outer"


# ---------------------------------------------------------------------------
# wrapped property
# ---------------------------------------------------------------------------

def test_wrapped_returns_inner_check():
    inner = _PassCheck()
    check = AuditedCheck(inner)
    assert check.wrapped is inner
