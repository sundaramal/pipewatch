"""TracedCheck — wraps a check and records a trace of each run with timing and result."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import List, Optional

from pipewatch.checks.base import BaseCheck, CheckResult


@dataclass
class TraceEntry:
    """A single recorded execution of the wrapped check."""

    started_at: float
    duration_seconds: float
    passed: bool
    message: str

    def __repr__(self) -> str:  # pragma: no cover
        status = "PASS" if self.passed else "FAIL"
        return (
            f"TraceEntry(status={status}, duration={self.duration_seconds:.4f}s, "
            f"message={self.message!r})"
        )


class TracedCheck(BaseCheck):
    """Decorator that records a trace log of every run of the wrapped check.

    Parameters
    ----------
    check:
        The :class:`BaseCheck` to wrap.
    max_entries:
        Maximum number of trace entries to keep (oldest are dropped). ``None``
        means unlimited.
    name:
        Optional override for the check name.
    """

    def __init__(
        self,
        check: BaseCheck,
        *,
        max_entries: Optional[int] = 100,
        name: Optional[str] = None,
    ) -> None:
        super().__init__(name=name or f"traced({check.name})")
        self._wrapped = check
        self._max_entries = max_entries
        self._trace: List[TraceEntry] = []

    @property
    def wrapped(self) -> BaseCheck:
        return self._wrapped

    @property
    def trace(self) -> List[TraceEntry]:
        """Return a copy of the recorded trace entries."""
        return list(self._trace)

    def clear_trace(self) -> None:
        """Remove all recorded trace entries."""
        self._trace.clear()

    def run(self) -> CheckResult:
        started = time.monotonic()
        result = self._wrapped.run()
        duration = time.monotonic() - started

        entry = TraceEntry(
            started_at=started,
            duration_seconds=duration,
            passed=result.passed,
            message=result.message,
        )
        self._trace.append(entry)

        if self._max_entries is not None and len(self._trace) > self._max_entries:
            self._trace.pop(0)

        return result
