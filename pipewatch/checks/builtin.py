"""Built-in check implementations for common pipeline health scenarios."""

from datetime import datetime, timezone
from typing import Any, Optional

from pipewatch.checks.base import BaseCheck, CheckResult


class ThresholdCheck(BaseCheck):
    """Passes if a numeric value is within an acceptable range."""

    def __init__(
        self,
        name: str,
        value: float,
        min_value: Optional[float] = None,
        max_value: Optional[float] = None,
        description: str = "",
    ) -> None:
        super().__init__(name=name, description=description)
        self.value = value
        self.min_value = min_value
        self.max_value = max_value

    def run(self) -> CheckResult:
        if self.min_value is not None and self.value < self.min_value:
            return CheckResult(
                passed=False,
                message=f"Value {self.value} is below minimum {self.min_value}",
            )
        if self.max_value is not None and self.value > self.max_value:
            return CheckResult(
                passed=False,
                message=f"Value {self.value} exceeds maximum {self.max_value}",
            )
        return CheckResult(passed=True, message=f"Value {self.value} is within range")


class FreshnessCheck(BaseCheck):
    """Passes if a timestamp is recent enough (within max_age_seconds)."""

    def __init__(
        self,
        name: str,
        last_updated: datetime,
        max_age_seconds: int,
        description: str = "",
    ) -> None:
        super().__init__(name=name, description=description)
        self.last_updated = last_updated
        self.max_age_seconds = max_age_seconds

    def run(self) -> CheckResult:
        now = datetime.now(timezone.utc)
        last = self.last_updated
        if last.tzinfo is None:
            last = last.replace(tzinfo=timezone.utc)
        age_seconds = (now - last).total_seconds()
        if age_seconds > self.max_age_seconds:
            return CheckResult(
                passed=False,
                message=(
                    f"Data is {age_seconds:.0f}s old; "
                    f"maximum allowed is {self.max_age_seconds}s"
                ),
            )
        return CheckResult(
            passed=True,
            message=f"Data is fresh ({age_seconds:.0f}s old)",
        )


class NullRateCheck(BaseCheck):
    """Passes if the null rate in a column is below the given threshold."""

    def __init__(
        self,
        name: str,
        total_rows: int,
        null_rows: int,
        max_null_rate: float = 0.05,
        description: str = "",
    ) -> None:
        super().__init__(name=name, description=description)
        self.total_rows = total_rows
        self.null_rows = null_rows
        self.max_null_rate = max_null_rate

    def run(self) -> CheckResult:
        if self.total_rows == 0:
            return CheckResult(passed=False, message="No rows to evaluate")
        rate = self.null_rows / self.total_rows
        if rate > self.max_null_rate:
            return CheckResult(
                passed=False,
                message=(
                    f"Null rate {rate:.2%} exceeds maximum {self.max_null_rate:.2%}"
                ),
            )
        return CheckResult(
            passed=True,
            message=f"Null rate {rate:.2%} is acceptable",
        )
