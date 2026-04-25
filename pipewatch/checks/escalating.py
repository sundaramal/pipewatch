"""EscalatingCheck — increases severity metadata on repeated failures.

Wraps an inner check and tracks consecutive failures. Each time the
inner check fails the *level* increments (1, 2, 3 …) up to a
configurable ceiling. On a pass the level resets to 0.  The level is
exposed both as an attribute and injected into the result message so
alerters / reporters can act on it.
"""
from __future__ import annotations

from pipewatch.checks.base import BaseCheck, CheckResult


class EscalatingCheck(BaseCheck):
    """Wrap *wrapped* and escalate a severity level on repeated failures."""

    def __init__(
        self,
        wrapped: BaseCheck,
        max_level: int = 3,
        name: str | None = None,
    ) -> None:
        if max_level < 1:
            raise ValueError("max_level must be >= 1")
        super().__init__(name=name or f"escalating({wrapped.name})")
        self._wrapped = wrapped
        self._max_level = max_level
        self._level: int = 0

    # ------------------------------------------------------------------
    # Public read-only properties
    # ------------------------------------------------------------------

    @property
    def wrapped(self) -> BaseCheck:
        return self._wrapped

    @property
    def max_level(self) -> int:
        return self._max_level

    @property
    def level(self) -> int:
        """Current escalation level (0 = no active failure streak)."""
        return self._level

    # ------------------------------------------------------------------
    # Core logic
    # ------------------------------------------------------------------

    def run(self) -> CheckResult:
        result = self._wrapped.run()

        if not result.passed:
            self._level = min(self._level + 1, self._max_level)
            message = (
                f"[level {self._level}/{self._max_level}] {result.message}"
            )
            return CheckResult(passed=False, message=message)

        # Inner check passed — reset streak.
        self._level = 0
        return result

    def reset(self) -> None:
        """Manually reset the escalation level to zero."""
        self._level = 0
