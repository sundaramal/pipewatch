"""Tests for LabeledCheck."""
import pytest
from pipewatch.checks.base import BaseCheck, CheckResult
from pipewatch.checks.labeled import LabeledCheck


class _PassCheck(BaseCheck):
    def __init__(self, name="pass"):
        super().__init__(name=name)

    def run(self) -> CheckResult:
        return CheckResult(passed=True, message="ok")


class _FailCheck(BaseCheck):
    def __init__(self, name="fail"):
        super().__init__(name=name)

    def run(self) -> CheckResult:
        return CheckResult(passed=False, message="bad")


class _EmptyMessageCheck(BaseCheck):
    def __init__(self):
        super().__init__(name="empty")

    def run(self) -> CheckResult:
        return CheckResult(passed=True, message="")


def test_labeled_passes_through_pass():
    check = LabeledCheck(_PassCheck(), labels={"env": "prod"})
    result = check.run()
    assert result.passed is True


def test_labeled_passes_through_fail():
    check = LabeledCheck(_FailCheck(), labels={"env": "prod"})
    result = check.run()
    assert result.passed is False


def test_labeled_appends_labels_to_message():
    check = LabeledCheck(_PassCheck(), labels={"env": "prod", "team": "data"})
    result = check.run()
    assert "env=prod" in result.message
    assert "team=data" in result.message


def test_labeled_original_message_preserved():
    check = LabeledCheck(_PassCheck(), labels={"env": "prod"})
    result = check.run()
    assert result.message.startswith("ok")


def test_labeled_no_labels_returns_original_result():
    inner = _PassCheck()
    check = LabeledCheck(inner, labels={})
    result = check.run()
    assert result.message == "ok"


def test_labeled_empty_message_with_labels():
    check = LabeledCheck(_EmptyMessageCheck(), labels={"x": "1"})
    result = check.run()
    assert "x=1" in result.message


def test_labeled_inherits_wrapped_name_by_default():
    inner = _PassCheck(name="my_check")
    check = LabeledCheck(inner)
    assert check.name == "my_check"


def test_labeled_custom_name_overrides():
    inner = _PassCheck(name="my_check")
    check = LabeledCheck(inner, name="override")
    assert check.name == "override"


def test_labeled_wrapped_property():
    inner = _PassCheck()
    check = LabeledCheck(inner)
    assert check.wrapped is inner


def test_labeled_labels_property_returns_copy():
    labels = {"a": "1"}
    check = LabeledCheck(_PassCheck(), labels=labels)
    returned = check.labels
    returned["b"] = "2"
    assert "b" not in check.labels
