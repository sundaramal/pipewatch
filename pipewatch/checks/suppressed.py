"""SuppressedCheck — wraps a check and suppresses failures during a given time window.

If the current time falls within the suppression window, failures are
converted to a passing result with a note explaining the suppression.
Outside the window the wrapped check result is returned unchanged.
"""

from __future__ import annotations

import datetime
from typing import Optional

from pipewatch.checks.base import BaseCheck, CheckResult


class SuppressedCheck(BaseCheck):
    """Suppress failures from *wrapped* between *start* and *end* each day.

    Parameters
    ----------
    wrapped:
        The inner :class:`BaseCheck` whose result may be suppressed.
    start:
        UTC time-of-day at which suppression begins (``datetime.time``).
    end:
        UTC time-of-day at which suppression ends (``datetime.time``).
    name:
        Optional display name; defaults to ``"suppressed(<wrapped.name>)"``.
    """

    def __init__(
        self,
        wrapped: BaseCheck,
        start: datetime.time,
        end: datetime.time,
        name: Optional[str] = None,
    ) -> None:
        if not isinstance(wrapped, BaseCheck):
            raise TypeError("wrapped must be a BaseCheck instance")
        if not isinstance(start, datetime.time) or not isinstance(end, datetime.time):
            raise TypeError("start and end must be datetime.time instances")
        super().__init__(name=name or f"suppressed({wrapped.name})")
        self._wrapped = wrapped
        self._start = start
        self._end = end

    @property
    def wrapped(self) -> BaseCheck:
        return self._wrapped

    @property
    def start(self) -> datetime.time:
        return self._start

    @property
    def end(self) -> datetime.time:
        return self._end

    def _in_window(self, now: Optional[datetime.datetime] = None) -> bool:
        """Return True if *now* (UTC) falls within the suppression window."""
        t = (now or datetime.datetime.utcnow()).time()
        if self._start <= self._end:
            return self._start <= t < self._end
        # overnight window, e.g. 22:00 – 06:00
        return t >= self._start or t < self._end

    def run(self) -> CheckResult:
        result = self._wrapped.run()
        if not result.passed and self._in_window():
            return CheckResult(
                passed=True,
                name=self.name,
                message=(
                    f"[suppressed] failure hidden during maintenance window "
                    f"({self._start}–{self._end} UTC): {result.message}"
                ),
            )
        return CheckResult(passed=result.passed, name=self.name, message=result.message)
