"""StaggeredCheck — runs a wrapped check only every N-th call.

Useful for spreading load when many checks are polled on the same
schedule: each instance can be given a different offset so they fire
at different ticks.
"""
from __future__ import annotations

from pipewatch.checks.base import BaseCheck, CheckResult


class StaggeredCheck(BaseCheck):
    """Wrap a check so it only executes on every *n*-th invocation.

    On skipped calls the previous result is returned (or a passing
    placeholder if the check has never been run yet).

    Args:
        wrapped:  The underlying :class:`BaseCheck` to delegate to.
        every:    Period — the check fires when ``call_count % every == offset``.
        offset:   Which slot within the period triggers execution (default 0).
        name:     Optional display name; falls back to the wrapped check's name.
    """

    def __init__(
        self,
        wrapped: BaseCheck,
        every: int = 2,
        offset: int = 0,
        name: str | None = None,
    ) -> None:
        if every < 1:
            raise ValueError("'every' must be >= 1")
        if not (0 <= offset < every):
            raise ValueError("'offset' must satisfy 0 <= offset < every")

        super().__init__(name=name or wrapped.name)
        self._wrapped = wrapped
        self._every = every
        self._offset = offset
        self._call_count: int = 0
        self._last_result: CheckResult | None = None

    @property
    def wrapped(self) -> BaseCheck:
        return self._wrapped

    @property
    def every(self) -> int:
        return self._every

    @property
    def offset(self) -> int:
        return self._offset

    @property
    def call_count(self) -> int:
        return self._call_count

    def run(self) -> CheckResult:
        idx = self._call_count % self._every
        self._call_count += 1

        if idx == self._offset:
            self._last_result = self._wrapped.run()
            return self._last_result

        if self._last_result is not None:
            return self._last_result

        # First ever call but not in the active slot — return a neutral pass.
        return CheckResult(
            passed=True,
            name=self.name,
            message="staggered: skipped (no prior result)",
        )
