"""Rate-limited check wrapper: skips execution if called too frequently."""

from __future__ import annotations

import time
from typing import Optional

from pipewatch.checks.base import BaseCheck, CheckResult


class RateLimitedCheck(BaseCheck):
    """Wraps a check and skips it if it was run within *min_interval* seconds."""

    def __init__(
        self,
        wrapped: BaseCheck,
        min_interval: float,
        name: Optional[str] = None,
    ) -> None:
        super().__init__(name=name or wrapped.name)
        self._wrapped = wrapped
        self._min_interval = min_interval
        self._last_run: Optional[float] = None

    @property
    def wrapped(self) -> BaseCheck:
        return self._wrapped

    def run(self) -> CheckResult:
        now = time.monotonic()
        if self._last_run is not None:
            elapsed = now - self._last_run
            if elapsed < self._min_interval:
                return CheckResult(
                    name=self.name,
                    passed=True,
                    message=(
                        f"Skipped (rate-limited): {elapsed:.2f}s < "
                        f"{self._min_interval}s interval"
                    ),
                )
        self._last_run = now
        return self._wrapped.run()
