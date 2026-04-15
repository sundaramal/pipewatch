"""Alert handlers for pipewatch pipeline check results."""

from __future__ import annotations

import smtplib
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from email.message import EmailMessage
from typing import List

from pipewatch.checks.base import CheckResult
from pipewatch.runner import RunReport

logger = logging.getLogger(__name__)


class BaseAlerter(ABC):
    """Abstract base class for alert handlers."""

    @abstractmethod
    def send(self, report: RunReport) -> None:
        """Send an alert based on the run report."""
        raise NotImplementedError

    def should_alert(self, report: RunReport) -> bool:
        """Return True if any checks failed."""
        return report.num_failed > 0


@dataclass
class LogAlerter(BaseAlerter):
    """Alerts by logging failed checks to the standard logger."""

    level: str = "WARNING"

    def send(self, report: RunReport) -> None:
        if not self.should_alert(report):
            logger.info("All %d checks passed — no alert needed.", report.total)
            return

        log_fn = getattr(logger, self.level.lower(), logger.warning)
        log_fn(
            "Pipeline check failures detected: %d/%d checks failed.",
            report.num_failed,
            report.total,
        )
        for result in report.results:
            if not result.passed:
                log_fn("  FAIL [%s]: %s", result.check_name, result.message)


@dataclass
class EmailAlerter(BaseAlerter):
    """Alerts by sending an email summary of failed checks."""

    recipients: List[str]
    sender: str = "pipewatch@localhost"
    smtp_host: str = "localhost"
    smtp_port: int = 25
    subject_prefix: str = "[pipewatch]"

    def _build_message(self, report: RunReport) -> EmailMessage:
        msg = EmailMessage()
        msg["From"] = self.sender
        msg["To"] = ", ".join(self.recipients)
        msg["Subject"] = (
            f"{self.subject_prefix} Pipeline alert: "
            f"{report.num_failed}/{report.total} checks failed"
        )
        lines = [f"Pipeline run completed: {report.num_failed} failure(s).\n"]
        for result in report.results:
            status = "PASS" if result.passed else "FAIL"
            lines.append(f"  [{status}] {result.check_name}: {result.message}")
        msg.set_content("\n".join(lines))
        return msg

    def send(self, report: RunReport) -> None:
        if not self.should_alert(report):
            logger.info("No failures — skipping email alert.")
            return

        msg = self._build_message(report)
        try:
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.send_message(msg)
            logger.info("Alert email sent to %s.", self.recipients)
        except OSError as exc:
            logger.error("Failed to send alert email: %s", exc)
