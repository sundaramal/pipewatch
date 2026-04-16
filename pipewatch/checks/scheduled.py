"""Scheduled check: only runs during a specified time window."""

from __future__ import annotations

from datetime import time, datetime
from typing import Optional

from pipewatch.checks.base import BaseCheck, CheckResult


class ScheduledCheck(BaseCheck):
    """Wraps another check and only executes it within a time window.

    Outside the window the check is skipped (reported as passed with a note).
    """

    def __init__(
        self,
        wrapped: BaseCheck,
        start: time,
        end: time,
        name: Optional[str] = None,
    ) -> None:
        super().__init__(name=name or wrapped.name)
        self._wrapped = wrapped
        self._start = start
        self._end = end

    # ------------------------------------------------------------------
    def _in_window(self, now: time) -> bool:
        if self._start <= self._end:
            return self._start <= now <= self._end
        # overnight window e.g. 22:00 – 06:00
        return now >= self._start or now <= self._end

    def run(self) -> CheckResult:
        now = datetime.now().time().replace(second=0, microsecond=0)
        if not self._in_window(now):
            return CheckResult(
                passed=True,
                message=(
                    f"Skipped: outside scheduled window "
                    f"{self._start.strftime('%H:%M')}–{self._end.strftime('%H:%M')}"
                ),
            )
        return self._wrapped.run()

    @property
    def wrapped(self) -> BaseCheck:
        return self._wrapped
