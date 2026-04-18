"""Tests for AnnotatedCheck."""
import pytest
from pipewatch.checks.base import BaseCheck, CheckResult
from pipewatch.checks.annotated import AnnotatedCheck


class _PassCheck(BaseCheck):
    def __init__(self, details=None):
        super().__init__(name="pass")
        self._details = details

    def run(self) -> CheckResult:
        return CheckResult(name=self.name, passed=True, message="ok", details=self._details)


class _FailCheck(BaseCheck):
    def __init__(self):
        super().__init__(name="fail")

    def run(self) -> CheckResult:
        return CheckResult(name=self.name, passed=False, message="bad")


def test_annotated_passes_when_wrapped_passes():
    check = AnnotatedCheck(_PassCheck(), annotations={"env": "prod"})
    result = check.run()
    assert result.passed is True


def test_annotated_fails_when_wrapped_fails():
    check = AnnotatedCheck(_FailCheck(), annotations={"env": "prod"})
    result = check.run()
    assert result.passed is False


def test_annotations_appear_in_details():
    check = AnnotatedCheck(_PassCheck(), annotations={"team": "data", "priority": 1})
    result = check.run()
    assert result.details["team"] == "data"
    assert result.details["priority"] == 1


def test_wrapped_details_are_preserved():
    inner = _PassCheck(details={"value": 42})
    check = AnnotatedCheck(inner, annotations={"env": "staging"})
    result = check.run()
    assert result.details["value"] == 42
    assert result.details["env"] == "staging"


def test_annotation_does_not_override_wrapped_details_key():
    """Wrapped check details take precedence over annotations for same key."""
    inner = _PassCheck(details={"env": "from-check"})
    check = AnnotatedCheck(inner, annotations={"env": "from-annotation"})
    result = check.run()
    assert result.details["env"] == "from-check"


def test_no_annotations_still_works():
    check = AnnotatedCheck(_PassCheck())
    result = check.run()
    assert result.passed is True


def test_custom_name_overrides_wrapped_name():
    check = AnnotatedCheck(_PassCheck(), name="custom-name")
    assert check.name == "custom-name"
    result = check.run()
    assert result.name == "custom-name"


def test_default_name_inherits_from_wrapped():
    check = AnnotatedCheck(_PassCheck())
    assert check.name == "pass"


def test_wrapped_property_returns_inner_check():
    inner = _PassCheck()
    check = AnnotatedCheck(inner)
    assert check.wrapped is inner


def test_annotations_property_returns_copy():
    ann = {"k": "v"}
    check = AnnotatedCheck(_PassCheck(), annotations=ann)
    returned = check.annotations
    returned["extra"] = "x"
    assert "extra" not in check.annotations
