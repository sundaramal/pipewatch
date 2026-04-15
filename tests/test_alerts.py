"""Tests for pipewatch alert handlers."""

from __future__ import annotations

import logging
from unittest.mock import MagicMock, patch

import pytest

from pipewatch.alerts import EmailAlerter, LogAlerter
from pipewatch.checks.base import CheckResult
from pipewatch.runner import RunReport


def _make_report(passed_names=(), failed_names=()) -> RunReport:
    results = [
        CheckResult(check_name=name, passed=True, message="ok")
        for name in passed_names
    ] + [
        CheckResult(check_name=name, passed=False, message="failed")
        for name in failed_names
    ]
    return RunReport(results=results)


# ---------------------------------------------------------------------------
# LogAlerter
# ---------------------------------------------------------------------------

class TestLogAlerter:
    def test_should_alert_false_when_all_pass(self):
        report = _make_report(passed_names=["check_a", "check_b"])
        alerter = LogAlerter()
        assert alerter.should_alert(report) is False

    def test_should_alert_true_when_failures(self):
        report = _make_report(passed_names=["check_a"], failed_names=["check_b"])
        alerter = LogAlerter()
        assert alerter.should_alert(report) is True

    def test_send_logs_warning_on_failure(self, caplog):
        report = _make_report(failed_names=["broken_check"])
        alerter = LogAlerter(level="WARNING")
        with caplog.at_level(logging.WARNING, logger="pipewatch.alerts"):
            alerter.send(report)
        assert "broken_check" in caplog.text
        assert "FAIL" in caplog.text

    def test_send_logs_info_when_all_pass(self, caplog):
        report = _make_report(passed_names=["check_a"])
        alerter = LogAlerter()
        with caplog.at_level(logging.INFO, logger="pipewatch.alerts"):
            alerter.send(report)
        assert "no alert needed" in caplog.text


# ---------------------------------------------------------------------------
# EmailAlerter
# ---------------------------------------------------------------------------

class TestEmailAlerter:
    def _make_alerter(self):
        return EmailAlerter(
            recipients=["ops@example.com"],
            sender="pipewatch@example.com",
            smtp_host="smtp.example.com",
            smtp_port=587,
        )

    def test_no_email_sent_when_all_pass(self):
        report = _make_report(passed_names=["check_a"])
        alerter = self._make_alerter()
        with patch("pipewatch.alerts.smtplib.SMTP") as mock_smtp:
            alerter.send(report)
        mock_smtp.assert_not_called()

    def test_email_sent_on_failure(self):
        report = _make_report(failed_names=["check_x"])
        alerter = self._make_alerter()
        mock_server = MagicMock()
        with patch("pipewatch.alerts.smtplib.SMTP") as mock_smtp:
            mock_smtp.return_value.__enter__.return_value = mock_server
            alerter.send(report)
        mock_server.send_message.assert_called_once()

    def test_email_subject_contains_failure_count(self):
        report = _make_report(passed_names=["a"], failed_names=["b", "c"])
        alerter = self._make_alerter()
        msg = alerter._build_message(report)
        assert "2/3" in msg["Subject"]
        assert "[pipewatch]" in msg["Subject"]

    def test_email_body_lists_failed_checks(self):
        report = _make_report(failed_names=["check_broken"])
        alerter = self._make_alerter()
        msg = alerter._build_message(report)
        body = msg.get_content()
        assert "check_broken" in body
        assert "FAIL" in body

    def test_smtp_error_is_caught_gracefully(self, caplog):
        report = _make_report(failed_names=["check_x"])
        alerter = self._make_alerter()
        with patch("pipewatch.alerts.smtplib.SMTP", side_effect=OSError("refused")):
            with caplog.at_level(logging.ERROR, logger="pipewatch.alerts"):
                alerter.send(report)  # should not raise
        assert "Failed to send alert email" in caplog.text
