"""RetryingFallbackCheck — retries a wrapped check N times, then falls back to a secondary check."""
from __future__ import annotations

import time
from typing import Optional

from pipewatch.checks.base import BaseCheck, CheckResult


class RetryingFallbackCheck(BaseCheck):
    """Run *wrapped* up to *retries* times; if all attempts fail, run *fallback* instead.

    Parameters
    ----------
    wrapped:
        Primary check to attempt.
    fallback:
        Secondary check executed only when every retry of *wrapped* fails.
    retries:
        Maximum number of attempts for *wrapped* (must be >= 1).
    delay:
        Seconds to wait between retry attempts (default 0).
    name:
        Optional override for the check name.
    """

    def __init__(
        self,
        wrapped: BaseCheck,
        fallback: BaseCheck,
        retries: int = 3,
        delay: float = 0.0,
        name: Optional[str] = None,
    ) -> None:
        if retries < 1:
            raise ValueError("retries must be >= 1")
        super().__init__(name=name or f"retrying_fallback({wrapped.name})")
        self._wrapped = wrapped
        self._fallback = fallback
        self._retries = retries
        self._delay = delay

    @property
    def wrapped(self) -> BaseCheck:
        return self._wrapped

    @property
    def fallback(self) -> BaseCheck:
        return self._fallback

    @property
    def retries(self) -> int:
        return self._retries

    def run(self) -> CheckResult:
        last_result: Optional[CheckResult] = None
        for attempt in range(self._retries):
            last_result = self._wrapped.run()
            if last_result.passed:
                return last_result
            if attempt < self._retries - 1 and self._delay > 0:
                time.sleep(self._delay)
        # All retries exhausted — delegate to fallback
        fallback_result = self._fallback.run()
        return CheckResult(
            passed=fallback_result.passed,
            message=(
                f"Primary check failed after {self._retries} attempt(s) "
                f"(last: {last_result.message}); "
                f"fallback: {fallback_result.message}"
            ),
        )
