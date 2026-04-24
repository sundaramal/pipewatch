"""WindowedCheck — only counts failures within a sliding time window.

If the wrapped check has failed fewer than `threshold` times in the
last `window_seconds` seconds the result is reported as passed;
otherwise the most-recent failure result is propagated.
"""
from __future__ import annotations

import time
from collections import deque
from typing import Deque, Optional

from pipewatch.checks.base import BaseCheck, CheckResult


class WindowedCheck(BaseCheck):
    """Wrap a check and suppress failures until they exceed a threshold
    within a rolling time window.

    Parameters
    ----------
    check:
        The inner :class:`BaseCheck` to delegate to.
    window_seconds:
        Length of the rolling window in seconds (default 60).
    threshold:
        Minimum number of failures inside the window required before
        the result is reported as failed (default 3).
    name:
        Optional override for the check name.
    """

    def __init__(
        self,
        check: BaseCheck,
        window_seconds: float = 60.0,
        threshold: int = 3,
        name: Optional[str] = None,
    ) -> None:
        super().__init__(name=name or f"windowed({check.name})")
        self._check = check
        self._window_seconds = window_seconds
        self._threshold = threshold
        # Each entry is a (timestamp, CheckResult) pair for a *failure*.
        self._failures: Deque[tuple[float, CheckResult]] = deque()

    # ------------------------------------------------------------------
    # Public helpers
    # ------------------------------------------------------------------

    @property
    def wrapped(self) -> BaseCheck:
        return self._check

    @property
    def window_seconds(self) -> float:
        return self._window_seconds

    @property
    def threshold(self) -> int:
        return self._threshold

    # ------------------------------------------------------------------
    # Core logic
    # ------------------------------------------------------------------

    def _evict_stale(self, now: float) -> None:
        """Remove failure records that have fallen outside the window."""
        cutoff = now - self._window_seconds
        while self._failures and self._failures[0][0] < cutoff:
            self._failures.popleft()

    def run(self) -> CheckResult:
        result = self._check.run()
        now = time.monotonic()
        self._evict_stale(now)

        if not result.passed:
            self._failures.append((now, result))

        recent_failures = len(self._failures)
        if recent_failures >= self._threshold:
            # Propagate the most-recent failure.
            latest = self._failures[-1][1]
            return CheckResult(
                passed=False,
                name=self.name,
                message=(
                    f"{recent_failures} failures in the last "
                    f"{self._window_seconds}s (threshold={self._threshold}): "
                    f"{latest.message}"
                ),
            )

        return CheckResult(passed=True, name=self.name, message=result.message)
