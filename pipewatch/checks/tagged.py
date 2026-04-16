"""Tagged check: attaches metadata tags to a check result."""

from __future__ import annotations

from typing import Dict, Optional

from pipewatch.checks.base import BaseCheck, CheckResult


class TaggedCheck(BaseCheck):
    """Wraps a check and injects tags into the result message."""

    def __init__(
        self,
        wrapped: BaseCheck,
        tags: Dict[str, str],
        name: Optional[str] = None,
    ) -> None:
        super().__init__(name=name or wrapped.name)
        self._wrapped = wrapped
        self.tags = dict(tags)

    def run(self) -> CheckResult:
        result = self._wrapped.run()
        tag_str = ", ".join(f"{k}={v}" for k, v in sorted(self.tags.items()))
        new_message = f"{result.message} [{tag_str}]" if tag_str else result.message
        return CheckResult(passed=result.passed, message=new_message)

    @property
    def wrapped(self) -> BaseCheck:
        return self._wrapped
