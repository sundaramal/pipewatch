"""TransformedCheck — applies a transform function to a metric before checking."""
from typing import Callable, Any
from pipewatch.checks.base import BaseCheck, CheckResult


class TransformedCheck(BaseCheck):
    """Wraps a check and applies a transform to the metric value before running.

    Useful for unit conversions, normalisation, or extracting a sub-field.

    Config params:
        transform (str): name of a built-in transform ('abs', 'negate', 'percent_of_100')
        checks (list): sub-check configs (forwarded to the wrapped check)
    """

    BUILTIN_TRANSFORMS: dict[str, Callable[[Any], Any]] = {
        "abs": abs,
        "negate": lambda x: -x,
        "percent_of_100": lambda x: x * 100,
    }

    def __init__(self, name: str, transform: str | Callable, wrapped: BaseCheck, **kwargs):
        super().__init__(name, **kwargs)
        if callable(transform):
            self._transform = transform
        elif transform in self.BUILTIN_TRANSFORMS:
            self._transform = self.BUILTIN_TRANSFORMS[transform]
        else:
            raise ValueError(
                f"Unknown transform '{transform}'. "
                f"Available: {list(self.BUILTIN_TRANSFORMS)}"
            )
        self._wrapped = wrapped

    @property
    def wrapped(self) -> BaseCheck:
        return self._wrapped

    def run(self) -> CheckResult:
        inner = self._wrapped.run()
        # Re-run with transformed value by patching metric temporarily
        original = getattr(self._wrapped, "_value", None)
        if original is None:
            # Cannot transform; return inner result as-is
            return CheckResult(
                check_name=self.name,
                passed=inner.passed,
                message=f"[transformed] {inner.message}",
                details=inner.details,
            )
        transformed = self._transform(original)
        self._wrapped._value = transformed
        result = self._wrapped.run()
        self._wrapped._value = original
        return CheckResult(
            check_name=self.name,
            passed=result.passed,
            message=f"[transformed] {result.message}",
            details=result.details,
        )
