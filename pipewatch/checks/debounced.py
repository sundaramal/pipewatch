"""DebouncedCheck: only fail after N consecutive failures."""
from __future__ import annotations

from pipewatch.checks.base import BaseCheck, CheckResult


class DebouncedCheck(BaseCheck):
    """Wraps a check and only reports failure after `threshold` consecutive failures."""

    def __init__(self, name: str, wrapped: BaseCheck, threshold: int = 3) -> None:
        super().__init__(name)
        if threshold < 1:
            raise ValueError("threshold must be >= 1")
        self._wrapped = wrapped
        self._threshold = threshold
        self._consecutive_failures = 0

    @property
    def wrapped(self) -> BaseCheck:
        return self._wrapped

    @property
    def threshold(self) -> int:
        return self._threshold

    def run(self) -> CheckResult:
        result = self._wrapped.run()
        if not result.passed:
            self._consecutive_failures += 1
            if self._consecutive_failures >= self._threshold:
                return CheckResult(
                    name=self.name,
                    passed=False,
                    message=(
                        f"{result.message} "
                        f"(failed {self._consecutive_failures} consecutive times, "
                        f"threshold={self._threshold})"
                    ),
                )
            return CheckResult(
                name=self.name,
                passed=True,
                message=(
                    f"Debounced: failure {self._consecutive_failures}/{self._threshold} "
                    f"— suppressed"
                ),
            )
        self._consecutive_failures = 0
        return CheckResult(name=self.name, passed=True, message=result.message)
