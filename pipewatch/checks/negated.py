"""NegatedCheck — inverts the pass/fail result of a wrapped check."""

from pipewatch.checks.base import BaseCheck, CheckResult


class NegatedCheck(BaseCheck):
    """Wraps another check and inverts its result.

    Useful when you want to assert that a condition does *not* hold,
    e.g. a value should NOT be within a threshold.

    Params (via BaseCheck.params):
        check (BaseCheck): the wrapped check instance.
        fail_message (str, optional): override message on failure.
    """

    def __init__(self, name: str, params: dict | None = None) -> None:
        super().__init__(name, params)
        wrapped = self.params.get("check")
        if wrapped is None:
            raise ValueError("NegatedCheck requires a 'check' param")
        if not isinstance(wrapped, BaseCheck):
            raise TypeError(
                f"'check' must be a BaseCheck instance, got {type(wrapped).__name__}"
            )
        self._wrapped: BaseCheck = wrapped
        self._fail_message: str | None = self.params.get("fail_message")

    @property
    def wrapped(self) -> BaseCheck:
        return self._wrapped

    def run(self) -> CheckResult:
        inner: CheckResult = self._wrapped.run()
        if not inner.passed:
            # inner failed → negated passes
            return CheckResult(
                check_name=self.name,
                passed=True,
                message=f"(negated) {inner.message}",
            )
        # inner passed → negated fails
        fail_msg = self._fail_message or f"(negated) {inner.message}"
        return CheckResult(
            check_name=self.name,
            passed=False,
            message=fail_msg,
        )
