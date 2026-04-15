"""Timeout wrapper check: fails if the wrapped check takes too long."""

from __future__ import annotations

import signal
import threading
from typing import Optional

from pipewatch.checks.base import BaseCheck, CheckResult


class TimeoutError(Exception):  # noqa: A001
    """Raised when a check exceeds its allotted time."""


class TimeoutCheck(BaseCheck):
    """Runs a wrapped check and fails it if it exceeds *timeout_seconds*.

    Parameters
    ----------
    check:
        The :class:`BaseCheck` instance to run with a time limit.
    timeout_seconds:
        Maximum number of seconds to allow the wrapped check to run.
    name:
        Optional override for the check name (defaults to wrapped check name).
    """

    def __init__(
        self,
        check: BaseCheck,
        timeout_seconds: float,
        name: Optional[str] = None,
    ) -> None:
        super().__init__(name=name or check.name)
        if timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be a positive number")
        self._check = check
        self._timeout_seconds = timeout_seconds

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def run(self) -> CheckResult:
        """Execute the wrapped check, returning a failure if it times out."""
        result_holder: list[CheckResult] = []
        exc_holder: list[BaseException] = []

        def _target() -> None:
            try:
                result_holder.append(self._check.run())
            except Exception as exc:  # noqa: BLE001
                exc_holder.append(exc)

        thread = threading.Thread(target=_target, daemon=True)
        thread.start()
        thread.join(timeout=self._timeout_seconds)

        if thread.is_alive():
            return CheckResult(
                name=self.name,
                passed=False,
                message=(
                    f"Check '{self._check.name}' timed out after "
                    f"{self._timeout_seconds}s"
                ),
            )

        if exc_holder:
            return CheckResult(
                name=self.name,
                passed=False,
                message=f"Check raised an exception: {exc_holder[0]}",
            )

        return result_holder[0]

    @property
    def wrapped(self) -> BaseCheck:
        """The underlying check being guarded by this timeout wrapper."""
        return self._check
