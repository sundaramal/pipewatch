"""Retry wrapper for checks that may transiently fail."""

from __future__ import annotations

import time
from typing import Optional

from pipewatch.checks.base import BaseCheck, CheckResult


class RetryCheck(BaseCheck):
    """Wraps another check and retries it up to *max_attempts* times.

    Parameters
    ----------
    check:
        The underlying :class:`BaseCheck` instance to run.
    max_attempts:
        Total number of attempts (must be >= 1).  Defaults to 3.
    delay:
        Seconds to wait between attempts.  Defaults to 0 (no delay).
    """

    def __init__(
        self,
        check: BaseCheck,
        max_attempts: int = 3,
        delay: float = 0.0,
    ) -> None:
        if max_attempts < 1:
            raise ValueError("max_attempts must be >= 1")
        super().__init__(name=f"retry({check.name})")
        self._check = check
        self.max_attempts = max_attempts
        self.delay = delay

    # ------------------------------------------------------------------
    # BaseCheck interface
    # ------------------------------------------------------------------

    def run(self) -> CheckResult:
        """Run the wrapped check, retrying on failure.

        Returns the first passing result, or the last failing result if
        all attempts are exhausted.
        """
        result: Optional[CheckResult] = None
        for attempt in range(1, self.max_attempts + 1):
            result = self._check.run()
            if result.passed:
                return result
            if attempt < self.max_attempts and self.delay > 0:
                time.sleep(self.delay)
        # result is guaranteed to be set (max_attempts >= 1)
        assert result is not None
        return CheckResult(
            name=self.name,
            passed=False,
            message=(
                f"Failed after {self.max_attempts} attempt(s): {result.message}"
            ),
        )

    # ------------------------------------------------------------------
    # Convenience property
    # ------------------------------------------------------------------

    @property
    def wrapped(self) -> BaseCheck:
        """Return the underlying check being retried."""
        return self._check
