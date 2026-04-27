"""HedgedCheck — runs a primary check and, if it exceeds a deadline,
launches a secondary (hedge) check concurrently and returns whichever
finishes first with a conclusive result."""
from __future__ import annotations

import threading
import time
from typing import Optional

from pipewatch.checks.base import BaseCheck, CheckResult


class HedgedCheck(BaseCheck):
    """Run *primary*; if it hasn't finished within *hedge_after* seconds,
    also start *secondary*.  Return the first conclusive (non-skipped)
    result; fall back to whatever finishes last.

    Args:
        primary:     The main check to run.
        secondary:   The hedge check launched after the deadline.
        hedge_after: Seconds to wait before launching the secondary check.
        name:        Optional display name.
    """

    def __init__(
        self,
        primary: BaseCheck,
        secondary: BaseCheck,
        hedge_after: float = 1.0,
        name: Optional[str] = None,
    ) -> None:
        super().__init__(name=name or f"hedged({primary.name})")
        self._primary = primary
        self._secondary = secondary
        self._hedge_after = hedge_after

    @property
    def wrapped(self) -> BaseCheck:
        return self._primary

    @property
    def secondary(self) -> BaseCheck:
        return self._secondary

    @property
    def hedge_after(self) -> float:
        return self._hedge_after

    def run(self) -> CheckResult:
        results: list[Optional[CheckResult]] = [None, None]
        winner: list[Optional[CheckResult]] = [None]
        lock = threading.Lock()

        def _run(check: BaseCheck, slot: int) -> None:
            result = check.run()
            with lock:
                results[slot] = result
                if winner[0] is None:
                    winner[0] = result

        primary_thread = threading.Thread(target=_run, args=(self._primary, 0), daemon=True)
        primary_thread.start()

        primary_thread.join(timeout=self._hedge_after)

        if primary_thread.is_alive():
            # Primary is slow — launch the hedge.
            secondary_thread = threading.Thread(
                target=_run, args=(self._secondary, 1), daemon=True
            )
            secondary_thread.start()
            # Wait for both to finish.
            primary_thread.join()
            secondary_thread.join()
        
        result = winner[0]
        if result is None:
            # Both threads somehow produced nothing (shouldn't happen).
            return CheckResult(passed=False, message="hedged: no result returned", name=self.name)

        return CheckResult(passed=result.passed, message=result.message, name=self.name)
