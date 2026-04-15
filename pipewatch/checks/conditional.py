"""Conditional check: only runs a wrapped check if a guard condition is met."""

from __future__ import annotations

from typing import Callable, Optional

from pipewatch.checks.base import BaseCheck, CheckResult


class ConditionalCheck(BaseCheck):
    """Runs *inner* only when *condition* returns True.

    If the condition is not met the check is reported as passed with a
    descriptive message so it still appears in run reports.

    Parameters
    ----------
    inner:
        The :class:`BaseCheck` to execute when the condition is satisfied.
    condition:
        A zero-argument callable that returns a bool.  Evaluated fresh on
        every call to :meth:`run`.
    skip_message:
        Human-readable explanation shown when the condition is not met.
    """

    def __init__(
        self,
        inner: BaseCheck,
        condition: Callable[[], bool],
        skip_message: str = "Condition not met – check skipped",
    ) -> None:
        name = f"conditional({inner.name})"
        super().__init__(name=name)
        self._inner = inner
        self._condition = condition
        self._skip_message = skip_message

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def run(self) -> CheckResult:
        if not self._condition():
            return CheckResult(
                check_name=self.name,
                passed=True,
                message=self._skip_message,
            )
        result = self._inner.run()
        # Re-stamp the name so callers see the conditional wrapper.
        return CheckResult(
            check_name=self.name,
            passed=result.passed,
            message=result.message,
        )

    @property
    def wrapped(self) -> BaseCheck:
        """The inner check that may be executed."""
        return self._inner
