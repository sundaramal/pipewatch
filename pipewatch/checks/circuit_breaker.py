"""Circuit breaker check wrapper.

Opens the circuit (skips the check) after a configurable number of
consecutive failures, and resets after a cooldown period.
"""
from __future__ import annotations

import time
from typing import Optional

from pipewatch.checks.base import BaseCheck, CheckResult


class CircuitBreakerCheck(BaseCheck):
    """Wraps a check and opens the circuit after *threshold* consecutive failures.

    While the circuit is open the check is skipped (returns a passing result
    with a note) until *reset_timeout* seconds have elapsed.
    """

    def __init__(
        self,
        wrapped: BaseCheck,
        threshold: int = 3,
        reset_timeout: float = 60.0,
        name: Optional[str] = None,
    ) -> None:
        super().__init__(name=name or f"circuit_breaker({wrapped.name})")
        self._wrapped = wrapped
        self._threshold = threshold
        self._reset_timeout = reset_timeout
        self._consecutive_failures: int = 0
        self._opened_at: Optional[float] = None

    @property
    def wrapped(self) -> BaseCheck:
        return self._wrapped

    @property
    def threshold(self) -> int:
        return self._threshold

    @property
    def reset_timeout(self) -> float:
        return self._reset_timeout

    def _is_open(self) -> bool:
        if self._opened_at is None:
            return False
        if time.monotonic() - self._opened_at >= self._reset_timeout:
            # Half-open: allow a probe
            self._opened_at = None
            self._consecutive_failures = 0
            return False
        return True

    def run(self) -> CheckResult:
        if self._is_open():
            return CheckResult(
                passed=True,
                message=f"Circuit open for '{self._wrapped.name}'; skipping.",
            )

        result = self._wrapped.run()

        if not result.passed:
            self._consecutive_failures += 1
            if self._consecutive_failures >= self._threshold:
                self._opened_at = time.monotonic()
        else:
            self._consecutive_failures = 0
            self._opened_at = None

        return result
