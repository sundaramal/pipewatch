"""CachedCheck: wraps a check and caches its result for a TTL period."""

from __future__ import annotations

import time
from typing import Optional

from pipewatch.checks.base import BaseCheck, CheckResult


class CachedCheck(BaseCheck):
    """Wraps another check and returns a cached result within a TTL window.

    Params:
        wrapped (BaseCheck): the check to cache.
        ttl (float): seconds to cache the last result (default 60).
    """

    def __init__(
        self,
        name: str,
        wrapped: BaseCheck,
        ttl: float = 60.0,
    ) -> None:
        super().__init__(name)
        self._wrapped = wrapped
        self._ttl = ttl
        self._cached_result: Optional[CheckResult] = None
        self._cached_at: Optional[float] = None

    @property
    def wrapped(self) -> BaseCheck:
        return self._wrapped

    def _cache_valid(self) -> bool:
        if self._cached_result is None or self._cached_at is None:
            return False
        return (time.monotonic() - self._cached_at) < self._ttl

    def run(self) -> CheckResult:
        if self._cache_valid():
            assert self._cached_result is not None
            return CheckResult(
                name=self.name,
                passed=self._cached_result.passed,
                message=f"[cached] {self._cached_result.message}",
            )
        result = self._wrapped.run()
        self._cached_result = result
        self._cached_at = time.monotonic()
        return CheckResult(
            name=self.name,
            passed=result.passed,
            message=result.message,
        )

    def invalidate(self) -> None:
        """Clear the cached result, forcing a fresh run next call."""
        self._cached_result = None
        self._cached_at = None
