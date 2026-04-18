"""ThrottledCheck — skip execution if called more than N times in a window."""
from __future__ import annotations

import time
from collections import deque
from typing import Deque

from pipewatch.checks.base import BaseCheck, CheckResult


class ThrottledCheck(BaseCheck):
    """Wrap a check so it runs at most *max_calls* times per *window_seconds*.

    When the rate cap is exceeded the check is skipped (returns a passing
    CheckResult with a note in the message).
    """

    def __init__(
        self,
        wrapped: BaseCheck,
        max_calls: int = 1,
        window_seconds: float = 60.0,
        name: str | None = None,
    ) -> None:
        super().__init__(name=name or f"throttled({wrapped.name})")
        self._wrapped = wrapped
        self._max_calls = max_calls
        self._window = window_seconds
        self._timestamps: Deque[float] = deque()

    @property
    def wrapped(self) -> BaseCheck:
        return self._wrapped

    def run(self) -> CheckResult:
        now = time.monotonic()
        cutoff = now - self._window
        # Evict timestamps outside the current window
        while self._timestamps and self._timestamps[0] < cutoff:
            self._timestamps.popleft()

        if len(self._timestamps) >= self._max_calls:
            return CheckResult(
                passed=True,
                name=self.name,
                message=(
                    f"throttled: skipped (>{self._max_calls} calls "
                    f"in {self._window}s window)"
                ),
            )

        self._timestamps.append(now)
        result = self._wrapped.run()
        return CheckResult(passed=result.passed, name=self.name, message=result.message)
