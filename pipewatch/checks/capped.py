"""CappedCheck — limits the number of consecutive failures reported.

Once the failure cap is reached, subsequent failures are still reported
as failures but the ``details`` field notes that the cap has been hit so
alert systems can avoid flooding operators with repeated messages.
"""
from __future__ import annotations

from pipewatch.checks.base import BaseCheck, CheckResult


class CappedCheck(BaseCheck):
    """Wraps another check and caps consecutive failure reports.

    Args:
        wrapped: The inner :class:`BaseCheck` to delegate to.
        cap: Maximum number of consecutive failures to report distinctly.
             After *cap* failures the result is still ``passed=False`` but
             ``details`` is prefixed with a cap-hit notice.
        name: Optional display name; defaults to the wrapped check's name.
    """

    def __init__(self, wrapped: BaseCheck, cap: int = 3, name: str | None = None) -> None:
        if cap < 1:
            raise ValueError("cap must be >= 1")
        super().__init__(name=name or wrapped.name)
        self._wrapped = wrapped
        self._cap = cap
        self._consecutive_failures = 0

    @property
    def wrapped(self) -> BaseCheck:
        return self._wrapped

    @property
    def cap(self) -> int:
        return self._cap

    @property
    def consecutive_failures(self) -> int:
        return self._consecutive_failures

    def reset(self) -> None:
        """Reset the consecutive-failure counter."""
        self._consecutive_failures = 0

    def run(self) -> CheckResult:
        result = self._wrapped.run()

        if result.passed:
            self._consecutive_failures = 0
            return result

        self._consecutive_failures += 1

        if self._consecutive_failures > self._cap:
            capped_details = (
                f"[cap={self._cap} hit, consecutive={self._consecutive_failures}] "
                + (result.details or "")
            )
            return CheckResult(
                passed=False,
                name=result.name,
                details=capped_details,
            )

        return result
