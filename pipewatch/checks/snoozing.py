"""SnoozingCheck — suppress a wrapped check for a fixed duration after a manual snooze.

A *snooze* is triggered by calling :meth:`SnoozingCheck.snooze`.  While
snoozed the check returns a passing result with a note explaining when the
snooze expires.  Once the snooze window has elapsed the wrapped check runs
normally again.

This is useful for silencing a known-flaky or temporarily-broken pipeline
check without disabling alerting globally.
"""

from __future__ import annotations

import time
from typing import Optional

from pipewatch.checks.base import BaseCheck, CheckResult


class SnoozingCheck(BaseCheck):
    """Wrap *wrapped* and skip execution while a snooze is active.

    Parameters
    ----------
    wrapped:
        The underlying :class:`~pipewatch.checks.base.BaseCheck` to delegate
        to when no snooze is active.
    snooze_seconds:
        How long (in seconds) a single call to :meth:`snooze` suppresses the
        wrapped check.  Defaults to ``300`` (5 minutes).
    name:
        Optional display name.  Falls back to ``"SnoozingCheck(<wrapped>)"``.
    """

    def __init__(
        self,
        wrapped: BaseCheck,
        snooze_seconds: float = 300.0,
        name: Optional[str] = None,
    ) -> None:
        super().__init__(name=name or f"SnoozingCheck({wrapped.name})")
        self._wrapped = wrapped
        self._snooze_seconds = snooze_seconds
        self._snooze_until: Optional[float] = None  # epoch seconds

    # ------------------------------------------------------------------
    # Public helpers
    # ------------------------------------------------------------------

    @property
    def wrapped(self) -> BaseCheck:
        """The underlying check that is (potentially) snoozed."""
        return self._wrapped

    @property
    def snooze_seconds(self) -> float:
        """Duration in seconds of each snooze window."""
        return self._snooze_seconds

    def snooze(self, duration: Optional[float] = None) -> None:
        """Activate (or extend) the snooze window.

        Parameters
        ----------
        duration:
            Override the default :attr:`snooze_seconds` for this particular
            snooze activation.  If *None*, :attr:`snooze_seconds` is used.
        """
        secs = duration if duration is not None else self._snooze_seconds
        self._snooze_until = time.monotonic() + secs

    def cancel_snooze(self) -> None:
        """Cancel an active snooze immediately, restoring normal execution."""
        self._snooze_until = None

    def is_snoozed(self) -> bool:
        """Return *True* if the snooze window is currently active."""
        if self._snooze_until is None:
            return False
        if time.monotonic() < self._snooze_until:
            return True
        # Snooze has expired — clean up.
        self._snooze_until = None
        return False

    def remaining_seconds(self) -> float:
        """Return seconds remaining in the current snooze, or ``0.0``."""
        if self._snooze_until is None:
            return 0.0
        remaining = self._snooze_until - time.monotonic()
        return max(0.0, remaining)

    # ------------------------------------------------------------------
    # BaseCheck interface
    # ------------------------------------------------------------------

    def run(self) -> CheckResult:
        """Run the wrapped check, or return a passing skip result if snoozed."""
        if self.is_snoozed():
            secs_left = self.remaining_seconds()
            return CheckResult(
                name=self.name,
                passed=True,
                message=(
                    f"Snoozed — wrapped check '{self._wrapped.name}' skipped; "
                    f"{secs_left:.1f}s remaining in snooze window."
                ),
            )

        result = self._wrapped.run()
        # Preserve the original check name so callers see the wrapper.
        return CheckResult(
            name=self.name,
            passed=result.passed,
            message=result.message,
        )
