"""CountedCheck — wraps another check and tracks how many times it has run.

The result includes a 'run_count' key in its metadata so downstream
consumers (alerters, history, dashboards) can observe invocation frequency.
"""
from __future__ import annotations

from pipewatch.checks.base import BaseCheck, CheckResult


class CountedCheck(BaseCheck):
    """Decorator-style check that counts total invocations.

    Parameters
    ----------
    wrapped:
        The inner :class:`BaseCheck` to delegate to.
    name:
        Optional display name; defaults to the wrapped check's name.
    """

    def __init__(self, wrapped: BaseCheck, *, name: str | None = None) -> None:
        if not isinstance(wrapped, BaseCheck):
            raise TypeError("wrapped must be a BaseCheck instance")
        super().__init__(name=name or wrapped.name)
        self._wrapped = wrapped
        self._count: int = 0

    @property
    def wrapped(self) -> BaseCheck:
        """The inner check being counted."""
        return self._wrapped

    @property
    def count(self) -> int:
        """Total number of times :meth:`run` has been called."""
        return self._count

    def run(self) -> CheckResult:
        """Delegate to the wrapped check and increment the counter.

        The returned :class:`CheckResult` carries a ``run_count`` entry in
        its ``details`` dict so callers can inspect how often this check
        has fired.
        """
        self._count += 1
        result = self._wrapped.run()
        details = dict(result.details) if result.details else {}
        details["run_count"] = self._count
        return CheckResult(
            name=self.name,
            passed=result.passed,
            message=result.message,
            details=details,
        )

    def reset(self) -> None:
        """Reset the invocation counter back to zero."""
        self._count = 0
