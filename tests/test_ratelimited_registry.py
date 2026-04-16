"""Integration tests: RateLimitedCheck via registry and factory."""

from __future__ import annotations

import pytest

from pipewatch.checks.base import BaseCheck, CheckResult
from pipewatch.checks import registry
from pipewatch.checks.ratelimited import RateLimitedCheck


def _ensure_builtins():
    registry.register_builtins()


def test_ratelimited_is_in_available():
    _ensure_builtins()
    assert "ratelimited" in registry.available()


def test_registry_get_returns_ratelimited_class():
    _ensure_builtins()
    assert registry.get("ratelimited") is RateLimitedCheck


def test_ratelimited_wraps_and_skips(monkeypatch):
    """End-to-end: construct via class, confirm skip behaviour."""
    _ensure_builtins()

    class _Counter(BaseCheck):
        def __init__(self):
            super().__init__(name="counter")
            self.calls = 0

        def run(self) -> CheckResult:
            self.calls += 1
            return CheckResult(name=self.name, passed=True, message="ok")

    inner = _Counter()
    check = RateLimitedCheck(inner, min_interval=100)
    r1 = check.run()
    r2 = check.run()

    assert r1.passed
    assert r2.passed
    assert "Skipped" in r2.message
    assert inner.calls == 1
