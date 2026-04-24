"""AuditedCheck — wraps a check and records an audit trail of every run.

Each audit entry captures the check name, timestamp, result passed/failed,
and the result message so operators can review historical decisions.
"""

from __future__ import annotations

import datetime
from dataclasses import dataclass, field
from typing import List, Optional

from pipewatch.checks.base import BaseCheck, CheckResult


@dataclass
class AuditEntry:
    """A single recorded run of the audited check."""

    name: str
    timestamp: datetime.datetime
    passed: bool
    message: str

    def __repr__(self) -> str:  # pragma: no cover
        status = "PASS" if self.passed else "FAIL"
        ts = self.timestamp.isoformat(timespec="seconds")
        return f"AuditEntry({self.name!r}, {ts}, {status}, {self.message!r})"


class AuditedCheck(BaseCheck):
    """Decorator that records an audit log of every check execution.

    Parameters
    ----------
    check:
        The inner :class:`BaseCheck` to delegate to.
    max_entries:
        Maximum number of audit entries to keep in memory.  Oldest entries
        are dropped once the limit is reached.  ``0`` means unlimited.
    name:
        Optional override for the check name; defaults to the wrapped
        check's name.
    """

    def __init__(
        self,
        check: BaseCheck,
        *,
        max_entries: int = 0,
        name: Optional[str] = None,
    ) -> None:
        super().__init__(name=name or check.name)
        self._wrapped = check
        self._max_entries = max_entries
        self._log: List[AuditEntry] = []

    @property
    def wrapped(self) -> BaseCheck:
        return self._wrapped

    @property
    def audit_log(self) -> List[AuditEntry]:
        """Return a snapshot of the current audit log (oldest first)."""
        return list(self._log)

    def run(self) -> CheckResult:
        result: CheckResult = self._wrapped.run()
        entry = AuditEntry(
            name=self.name,
            timestamp=datetime.datetime.utcnow(),
            passed=result.passed,
            message=result.message,
        )
        self._log.append(entry)
        if self._max_entries > 0 and len(self._log) > self._max_entries:
            self._log.pop(0)
        return result

    def clear(self) -> None:
        """Discard all stored audit entries."""
        self._log.clear()
