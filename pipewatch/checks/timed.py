"""TimedCheck: records elapsed time of a wrapped check and optionally fails if it exceeds a limit."""
from __future__ import annotations

import time
from typing import Optional

from pipewatch.checks.base import BaseCheck, CheckResult


class TimedCheck(BaseCheck):
    """Wraps a check and records elapsed time in the result message.

    If *max_seconds* is given and the wrapped check takes longer, the result
    is forced to a failure regardless of the wrapped outcome.
    """

    def __init__(
        self,
        wrapped: BaseCheck,
        max_seconds: Optional[float] = None,
        name: Optional[str] = None,
    ) -> None:
        super().__init__(name=name or f"timed({wrapped.name})")
        self._wrapped = wrapped
        self._max_seconds = max_seconds

    @property
    def wrapped(self) -> BaseCheck:
        return self._wrapped

    def run(self) -> CheckResult:
        start = time.monotonic()
        result = self._wrapped.run()
        elapsed = time.monotonic() - start

        msg = f"{result.message} [elapsed={elapsed:.3f}s]"

        if self._max_seconds is not None and elapsed > self._max_seconds:
            return CheckResult(
                passed=False,
                message=(
                    f"{result.message} [elapsed={elapsed:.3f}s "
                    f"exceeds max={self._max_seconds}s]"
                ),
            )

        return CheckResult(passed=result.passed, message=msg)
