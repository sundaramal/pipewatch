"""Verify that CompositeCheck is registered and buildable via the factory."""
from __future__ import annotations

import pytest

from pipewatch.checks import registry
from pipewatch.checks.composite import CompositeCheck
from pipewatch.checks.factory import CheckBuildError, build_check


@pytest.fixture(autouse=True)
def _ensure_builtins():
    registry.register_builtins()


def test_composite_is_in_available():
    assert "composite" in registry.available()


def test_registry_get_returns_composite_class():
    cls = registry.get("composite")
    assert cls is CompositeCheck


def test_build_check_raises_for_composite_without_checks_param():
    """factory should surface the missing 'checks' kwarg gracefully."""
    with pytest.raises((CheckBuildError, TypeError)):
        build_check("composite", "no_subchecks", {})


def test_composite_via_registry_run_all_pass(monkeypatch):
    """Build a CompositeCheck manually and confirm it runs correctly."""
    from pipewatch.checks.base import BaseCheck, CheckResult

    class _P(BaseCheck):
        def run(self):
            return CheckResult(name=self.name, passed=True, detail="ok")

    cls = registry.get("composite")
    check = cls(name="reg_composite", checks=[_P("sub1"), _P("sub2")])
    result = check.run()
    assert result.passed is True
    assert result.name == "reg_composite"


def test_composite_via_registry_run_with_failure():
    from pipewatch.checks.base import BaseCheck, CheckResult

    class _F(BaseCheck):
        def run(self):
            return CheckResult(name=self.name, passed=False, detail="nope")

    cls = registry.get("composite")
    check = cls(name="reg_fail", checks=[_F("bad")])
    result = check.run()
    assert result.passed is False
