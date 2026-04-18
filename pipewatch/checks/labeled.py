"""LabeledCheck — attaches key/value labels to a check result's message."""
from __future__ import annotations
from typing import Any
from pipewatch.checks.base import BaseCheck, CheckResult


class LabeledCheck(BaseCheck):
    """Wraps a check and appends labels to the result message."""

    def __init__(
        self,
        wrapped: BaseCheck,
        labels: dict[str, Any] | None = None,
        name: str | None = None,
    ) -> None:
        label_map = labels or {}
        super().__init__(name=name or wrapped.name)
        self._wrapped = wrapped
        self._labels = label_map

    @property
    def wrapped(self) -> BaseCheck:
        return self._wrapped

    @property
    def labels(self) -> dict[str, Any]:
        return dict(self._labels)

    def run(self) -> CheckResult:
        result = self._wrapped.run()
        if self._labels:
            label_str = " ".join(f"{k}={v}" for k, v in self._labels.items())
            new_message = f"{result.message} [{label_str}]" if result.message else f"[{label_str}]"
            return CheckResult(passed=result.passed, message=new_message)
        return result
