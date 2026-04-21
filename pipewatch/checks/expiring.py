"""ExpiringCheck — wraps a check and marks it as failed after a deadline.

If the current time is past `expires_at`, the check is considered failed
without running the inner check at all.
"""

from __future__ import annotations

import datetime
from typing import Optional

from pipewatch.checks.base import BaseCheck, CheckResult


class ExpiringCheck(BaseCheck):
    """Fails automatically once a wall-clock deadline has passed.

    Parameters
    ----------
    wrapped:
        The inner :class:`BaseCheck` to delegate to while still valid.
    expires_at:
        A timezone-aware (or naive UTC) :class:`datetime.datetime` after which
        the check is considered permanently failed.
    name:
        Optional display name; defaults to the wrapped check's name.
    """

    def __init__(
        self,
        wrapped: BaseCheck,
        expires_at: datetime.datetime,
        name: Optional[str] = None,
    ) -> None:
        super().__init__(name=name or wrapped.name)
        self._wrapped = wrapped
        self._expires_at = expires_at

    @property
    def wrapped(self) -> BaseCheck:
        return self._wrapped

    @property
    def expires_at(self) -> datetime.datetime:
        return self._expires_at

    def run(self) -> CheckResult:
        now = datetime.datetime.now(tz=self._expires_at.tzinfo)
        if now >= self._expires_at:
            return CheckResult(
                name=self.name,
                passed=False,
                message=(
                    f"Check expired at {self._expires_at.isoformat()}; "
                    f"current time is {now.isoformat()}"
                ),
            )
        return self._wrapped.run()
