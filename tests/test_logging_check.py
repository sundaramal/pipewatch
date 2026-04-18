"""Tests for LoggingCheck."""
from __future__ import annotations

import logging

import pytest

from pipewatch.checks.base import BaseCheck, CheckResult
from pipewatch.checks.logging_check import LoggingCheck


class _PassCheck(BaseCheck):
    def __init__(self):
        super().__init__(name="inner_pass")

    def run(self) -> CheckResult:
        return CheckResult(passed=True, message="all good")


class _FailCheck(BaseCheck):
    def __init__(self):
        super().__init__(name="inner_fail")

    def run(self) -> CheckResult:
        return CheckResult(passed=False, message="something broke")


def test_logging_check_passes_through_pass_result():
    lc = LoggingCheck(_PassCheck())
    result = lc.run()
    assert result.passed is True
    assert result.message == "all good"


def test_logging_check_passes_through_fail_result():
    lc = LoggingCheck(_FailCheck())
    result = lc.run()
    assert result.passed is False
    assert result.message == "something broke"


def test_logging_check_uses_inner_name_by_default():
    lc = LoggingCheck(_PassCheck())
    assert lc.name == "inner_pass"


def test_logging_check_uses_custom_name():
    lc = LoggingCheck(_PassCheck(), name="my_check")
    assert lc.name == "my_check"


def test_logging_check_wrapped_property():
    inner = _PassCheck()
    lc = LoggingCheck(inner)
    assert lc.wrapped is inner


def test_logging_check_logs_pass(caplog):
    with caplog.at_level(logging.INFO, logger="pipewatch.checks.logging_check"):
        LoggingCheck(_PassCheck()).run()
    assert any("PASS" in r.message and "inner_pass" in r.message for r in caplog.records)


def test_logging_check_logs_fail_as_warning(caplog):
    with caplog.at_level(logging.WARNING, logger="pipewatch.checks.logging_check"):
        LoggingCheck(_FailCheck()).run()
    warns = [r for r in caplog.records if r.levelno == logging.WARNING]
    assert any("FAIL" in r.message for r in warns)


def test_logging_check_custom_level_debug(caplog):
    with caplog.at_level(logging.DEBUG, logger="pipewatch.checks.logging_check"):
        LoggingCheck(_PassCheck(), level="DEBUG").run()
    debug_records = [r for r in caplog.records if r.levelno == logging.DEBUG]
    assert any("PASS" in r.message for r in debug_records)
