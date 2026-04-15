"""Tests for CheckRunner and RunReport."""

import pytest

from pipewatch.checks.base import BaseCheck, CheckResult
from pipewatch.runner import CheckRunner, RunReport


class _PassCheck(BaseCheck):
    def run(self) -> CheckResult:
        return CheckResult(passed=True, message="ok")


class _FailCheck(BaseCheck):
    def run(self) -> CheckResult:
        return CheckResult(passed=False, message="not ok")


def test_runner_all_pass():
    runner = CheckRunner([_PassCheck("a"), _PassCheck("b")])
    report = runner.run_all()
    assert report.passed
    assert report.num_passed == 2
    assert report.num_failed == 0


def test_runner_some_fail():
    runner = CheckRunner([_PassCheck("a"), _FailCheck("b"), _FailCheck("c")])
    report = runner.run_all()
    assert not report.passed
    assert report.num_passed == 1
    assert report.num_failed == 2


def test_runner_empty():
    runner = CheckRunner([])
    report = runner.run_all()
    assert report.passed
    assert report.total == 0


def test_runner_add_check():
    runner = CheckRunner([_PassCheck("a")])
    runner.add_check(_FailCheck("b"))
    report = runner.run_all()
    assert report.total == 2
    assert report.num_failed == 1


def test_run_report_summary_pass():
    runner = CheckRunner([_PassCheck("a")])
    report = runner.run_all()
    summary = report.summary()
    assert "PASS" in summary
    assert "1/1" in summary


def test_run_report_summary_fail():
    runner = CheckRunner([_PassCheck("a"), _FailCheck("b")])
    report = runner.run_all()
    summary = report.summary()
    assert "FAIL" in summary
    assert "1/2" in summary
    assert "1 failed" in summary
