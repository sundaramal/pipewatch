"""ProfiledCheck — wraps a check and records memory + CPU usage during execution."""
from __future__ import annotations

import resource
import time
from typing import Optional

from pipewatch.checks.base import BaseCheck, CheckResult


class ProfiledCheck(BaseCheck):
    """Decorator check that runs *wrapped* and attaches resource-usage metadata.

    Extra keys added to ``CheckResult.details``:
    - ``profile_wall_seconds``  – wall-clock elapsed time in seconds
    - ``profile_ru_utime``      – user CPU time (seconds) from ``resource.getrusage``
    - ``profile_ru_stime``      – system CPU time (seconds)
    - ``profile_ru_maxrss``     – peak RSS memory (kilobytes on Linux, bytes on macOS)
    """

    def __init__(
        self,
        wrapped: BaseCheck,
        name: Optional[str] = None,
    ) -> None:
        super().__init__(name=name or f"profiled({wrapped.name})")
        self._wrapped = wrapped

    @property
    def wrapped(self) -> BaseCheck:
        return self._wrapped

    def run(self) -> CheckResult:
        usage_before = resource.getrusage(resource.RUSAGE_SELF)
        t0 = time.perf_counter()

        result = self._wrapped.run()

        elapsed = time.perf_counter() - t0
        usage_after = resource.getrusage(resource.RUSAGE_SELF)

        profile = {
            "profile_wall_seconds": round(elapsed, 6),
            "profile_ru_utime": round(usage_after.ru_utime - usage_before.ru_utime, 6),
            "profile_ru_stime": round(usage_after.ru_stime - usage_before.ru_stime, 6),
            "profile_ru_maxrss": usage_after.ru_maxrss,
        }

        merged_details = {**(result.details or {}), **profile}
        return CheckResult(
            name=self.name,
            passed=result.passed,
            message=result.message,
            details=merged_details,
        )
