"""JitteredCheck — adds a random delay before running a wrapped check.

Useful for spreading out concurrent check execution to avoid thundering herd.
"""

from __future__ import annotations

import random
import time
from typing import Optional

from pipewatch.checks.base import BaseCheck, CheckResult


class JitteredCheck(BaseCheck):
    """Wraps a check and sleeps for a random duration before running it."""

    def __init__(
        self,
        wrapped: BaseCheck,
        min_delay: float = 0.0,
        max_delay: float = 1.0,
        name: Optional[str] = None,
    ) -> None:
        if min_delay < 0 or max_delay < 0:
            raise ValueError("Delay values must be non-negative.")
        if min_delay > max_delay:
            raise ValueError("min_delay must be <= max_delay.")
        super().__init__(name=name or f"jittered({wrapped.name})")
        self._wrapped = wrapped
        self._min_delay = min_delay
        self._max_delay = max_delay

    @property
    def wrapped(self) -> BaseCheck:
        return self._wrapped

    def run(self) -> CheckResult:
        delay = random.uniform(self._min_delay, self._max_delay)
        time.sleep(delay)
        result = self._wrapped.run()
        return CheckResult(
            name=self.name,
            passed=result.passed,
            message=f"[jitter={delay:.3f}s] {result.message}",
        )
