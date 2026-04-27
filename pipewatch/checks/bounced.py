"""BouncedCheck — skip execution if the wrapped check ran too recently.

Unlike RateLimitedCheck (which counts calls per window) BouncedCheck
enforces a minimum *gap* between consecutive executions.  If the gap
has not elapsed the previous result is returned unchanged.
"""
from __future__ import annotations

import time
from typing import Optional

from pipewatch.checks.base import BaseCheck, CheckResult


class BouncedCheck(BaseCheck):
    """Wrap *check* and enforce a minimum *gap_seconds* between runs.

    Parameters
    ----------
    check:
        The inner check to delegate to.
    gap_seconds:
        Minimum number of seconds that must pass between executions.
    name:
        Optional display name; defaults to the wrapped check's name.
    """

    def __init__(
        self,
        check: BaseCheck,
        gap_seconds: float,
        name: Optional[str] = None,
    ) -> None:
        if gap_seconds < 0:
            raise ValueError("gap_seconds must be >= 0")
        super().__init__(name=name or check.name)
        self._check = check
        self._gap_seconds = gap_seconds
        self._last_run: Optional[float] = None
        self._last_result: Optional[CheckResult] = None

    @property
    def wrapped(self) -> BaseCheck:
        return self._check

    @property
    def gap_seconds(self) -> float:
        return self._gap_seconds

    def run(self) -> CheckResult:
        now = time.monotonic()
        if (
            self._last_run is not None
            and (now - self._last_run) < self._gap_seconds
            and self._last_result is not None
        ):
            # Return a skipped/cached result without re-running.
            return CheckResult(
                name=self.name,
                passed=self._last_result.passed,
                message=f"[bounced] {self._last_result.message}",
            )
        result = self._check.run()
        self._last_run = time.monotonic()
        self._last_result = result
        return CheckResult(
            name=self.name,
            passed=result.passed,
            message=result.message,
        )
