"""QuarantinedCheck — skips a wrapped check for a fixed duration after a failure.

Once the wrapped check fails, it is quarantined for `quarantine_seconds`.
During quarantine, `run()` returns a skipped/pass result without executing
the inner check.  After the window expires the check runs normally again.
"""
from __future__ import annotations

import time
from typing import Optional

from pipewatch.checks.base import BaseCheck, CheckResult


class QuarantinedCheck(BaseCheck):
    """Wraps a check and suppresses it for *quarantine_seconds* after a failure."""

    def __init__(
        self,
        check: BaseCheck,
        quarantine_seconds: float = 60.0,
        name: Optional[str] = None,
    ) -> None:
        if quarantine_seconds <= 0:
            raise ValueError("quarantine_seconds must be positive")
        super().__init__(name=name or f"quarantined({check.name})")
        self._check = check
        self._quarantine_seconds = quarantine_seconds
        self._quarantine_until: Optional[float] = None

    @property
    def wrapped(self) -> BaseCheck:
        return self._check

    @property
    def quarantine_seconds(self) -> float:
        return self._quarantine_seconds

    @property
    def is_quarantined(self) -> bool:
        if self._quarantine_until is None:
            return False
        return time.monotonic() < self._quarantine_until

    def run(self) -> CheckResult:
        if self.is_quarantined:
            remaining = self._quarantine_until - time.monotonic()  # type: ignore[operator]
            return CheckResult(
                passed=True,
                name=self.name,
                message=(
                    f"quarantined — skipping for another {remaining:.1f}s"
                ),
            )

        result = self._check.run()

        if not result.passed:
            self._quarantine_until = time.monotonic() + self._quarantine_seconds

        return CheckResult(passed=result.passed, name=self.name, message=result.message)
