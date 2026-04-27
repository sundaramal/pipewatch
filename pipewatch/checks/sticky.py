"""StickyCheck — once a check fails, it stays failed until explicitly reset."""
from __future__ import annotations

from pipewatch.checks.base import BaseCheck, CheckResult


class StickyCheck(BaseCheck):
    """Wraps a check so that a failure latches: subsequent runs return the
    cached failure without executing the inner check again.  Call
    :py:meth:`reset` to clear the latch and allow the inner check to run.

    Args:
        check: The inner :class:`BaseCheck` to wrap.
        name:  Optional display name; defaults to the inner check's name.
    """

    def __init__(self, check: BaseCheck, *, name: str | None = None) -> None:
        super().__init__(name=name or check.name)
        self._wrapped = check
        self._stuck: CheckResult | None = None

    @property
    def wrapped(self) -> BaseCheck:
        """The inner check being wrapped."""
        return self._wrapped

    @property
    def is_stuck(self) -> bool:
        """``True`` when a failure has been latched."""
        return self._stuck is not None

    def reset(self) -> None:
        """Clear the latched failure so the inner check can run again."""
        self._stuck = None

    def run(self) -> CheckResult:
        """Return the latched failure if present; otherwise run the inner check.

        If the inner check fails for the first time the result is latched and
        returned for every subsequent call until :py:meth:`reset` is called.
        """
        if self._stuck is not None:
            return self._stuck

        result = self._wrapped.run()
        if not result.passed:
            self._stuck = result
        return result
