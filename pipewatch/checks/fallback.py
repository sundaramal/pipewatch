"""FallbackCheck: runs a primary check and falls back to a secondary on failure."""

from pipewatch.checks.base import BaseCheck, CheckResult


class FallbackCheck(BaseCheck):
    """Runs primary check; if it fails or errors, runs fallback check instead."""

    def __init__(self, primary: BaseCheck, fallback: BaseCheck, name: str = "fallback"):
        super().__init__(name=name)
        self._primary = primary
        self._fallback = fallback

    @property
    def wrapped(self) -> BaseCheck:
        return self._primary

    @property
    def fallback(self) -> BaseCheck:
        return self._fallback

    def run(self) -> CheckResult:
        try:
            result = self._primary.run()
        except Exception as exc:  # noqa: BLE001
            result = CheckResult(
                name=self._primary.name,
                passed=False,
                message=f"Primary raised exception: {exc}",
            )

        if not result.passed:
            fallback_result = self._fallback.run()
            return CheckResult(
                name=self.name,
                passed=fallback_result.passed,
                message=(
                    f"Primary failed ({result.message}); "
                    f"fallback: {fallback_result.message}"
                ),
                details=fallback_result.details,
            )

        return CheckResult(
            name=self.name,
            passed=True,
            message=result.message,
            details=result.details,
        )
