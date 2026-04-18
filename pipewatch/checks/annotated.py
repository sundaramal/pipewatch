"""AnnotatedCheck — wraps a check and attaches metadata annotations to the result."""
from __future__ import annotations
from typing import Any
from pipewatch.checks.base import BaseCheck, CheckResult


class AnnotatedCheck(BaseCheck):
    """Wraps a check and merges extra metadata into the CheckResult."""

    def __init__(
        self,
        wrapped: BaseCheck,
        annotations: dict[str, Any] | None = None,
        name: str | None = None,
    ) -> None:
        super().__init__(name=name or wrapped.name)
        self._wrapped = wrapped
        self._annotations: dict[str, Any] = annotations or {}

    @property
    def wrapped(self) -> BaseCheck:
        return self._wrapped

    @property
    def annotations(self) -> dict[str, Any]:
        return dict(self._annotations)

    def run(self) -> CheckResult:
        result = self._wrapped.run()
        merged = {**self._annotations, **(result.details or {})}
        return CheckResult(
            name=self.name,
            passed=result.passed,
            message=result.message,
            details=merged if merged else None,
        )
