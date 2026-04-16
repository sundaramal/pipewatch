"""Tests for TaggedCheck."""

import pytest

from pipewatch.checks.base import BaseCheck, CheckResult
from pipewatch.checks.tagged import TaggedCheck


class _PassCheck(BaseCheck):
    def __init__(self):
        super().__init__(name="inner")

    def run(self) -> CheckResult:
        return CheckResult(passed=True, message="all good")


class _FailCheck(BaseCheck):
    def __init__(self):
        super().__init__(name="inner")

    def run(self) -> CheckResult:
        return CheckResult(passed=False, message="broken")


def test_tags_appended_to_message_on_pass():
    check = TaggedCheck(_PassCheck(), tags={"env": "prod", "team": "data"})
    result = check.run()
    assert result.passed
    assert "env=prod" in result.message
    assert "team=data" in result.message


def test_tags_appended_to_message_on_fail():
    check = TaggedCheck(_FailCheck(), tags={"env": "staging"})
    result = check.run()
    assert not result.passed
    assert "env=staging" in result.message


def test_empty_tags_leaves_message_unchanged():
    check = TaggedCheck(_PassCheck(), tags={})
    result = check.run()
    assert result.message == "all good"


def test_name_defaults_to_wrapped_name():
    check = TaggedCheck(_PassCheck(), tags={})
    assert check.name == "inner"


def test_name_override():
    check = TaggedCheck(_PassCheck(), tags={}, name="overridden")
    assert check.name == "overridden"


def test_wrapped_property():
    inner = _PassCheck()
    check = TaggedCheck(inner, tags={"x": "1"})
    assert check.wrapped is inner


def test_tags_are_sorted_in_output():
    check = TaggedCheck(_PassCheck(), tags={"z": "last", "a": "first"})
    result = check.run()
    idx_a = result.message.index("a=first")
    idx_z = result.message.index("z=last")
    assert idx_a < idx_z
