"""MemoizedCheck — wraps a check and memoizes results by a key function.

Unlike CachedCheck (which caches by time), MemoizedCheck caches by an
arbitrary key derived from runtime context, allowing the same logical
check to be skipped when the same key has already been seen in a session.
"""
from __future__ import annotations

from typing import Any, Callable, Dict, Optional

from pipewatch.checks.base import BaseCheck, CheckResult


class MemoizedCheck(BaseCheck):
    """Run *wrapped* at most once per unique key value.

    Parameters
    ----------
    wrapped:
        The underlying check to delegate to.
    key_fn:
        Callable that returns a hashable key.  Called with no arguments
        each time ``run()`` is invoked.  Defaults to a constant ``None``
        (i.e. memoize globally — run exactly once).
    name:
        Optional display name; falls back to the wrapped check's name.
    """

    def __init__(
        self,
        wrapped: BaseCheck,
        key_fn: Optional[Callable[[], Any]] = None,
        name: Optional[str] = None,
    ) -> None:
        super().__init__(name=name or wrapped.name)
        self._wrapped = wrapped
        self._key_fn: Callable[[], Any] = key_fn if key_fn is not None else lambda: None
        self._cache: Dict[Any, CheckResult] = {}

    @property
    def wrapped(self) -> BaseCheck:
        return self._wrapped

    def run(self) -> CheckResult:
        key = self._key_fn()
        if key in self._cache:
            cached = self._cache[key]
            return CheckResult(
                name=self.name,
                passed=cached.passed,
                message=f"[memoized] {cached.message}",
            )
        result = self._wrapped.run()
        self._cache[key] = result
        return CheckResult(name=self.name, passed=result.passed, message=result.message)

    def invalidate(self, key: Any = None) -> None:
        """Remove a specific key (or all keys if *key* is ``...``)."""
        if key is ...:
            self._cache.clear()
        else:
            self._cache.pop(key, None)
