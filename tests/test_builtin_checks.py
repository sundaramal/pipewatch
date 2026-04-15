"""Tests for built-in check implementations."""

from datetime import datetime, timedelta, timezone

import pytest

from pipewatch.checks.builtin import FreshnessCheck, NullRateCheck, ThresholdCheck


# ---------------------------------------------------------------------------
# ThresholdCheck
# ---------------------------------------------------------------------------

def test_threshold_check_passes_within_range():
    check = ThresholdCheck("rows", value=50, min_value=10, max_value=100)
    result = check.run()
    assert result.passed


def test_threshold_check_fails_below_min():
    check = ThresholdCheck("rows", value=5, min_value=10)
    result = check.run()
    assert not result.passed
    assert "below minimum" in result.message


def test_threshold_check_fails_above_max():
    check = ThresholdCheck("rows", value=200, max_value=100)
    result = check.run()
    assert not result.passed
    assert "exceeds maximum" in result.message


def test_threshold_check_no_bounds_always_passes():
    check = ThresholdCheck("rows", value=9999)
    result = check.run()
    assert result.passed


# ---------------------------------------------------------------------------
# FreshnessCheck
# ---------------------------------------------------------------------------

def test_freshness_check_passes_for_recent_data():
    recent = datetime.now(timezone.utc) - timedelta(seconds=30)
    check = FreshnessCheck("pipeline", last_updated=recent, max_age_seconds=60)
    result = check.run()
    assert result.passed
    assert "fresh" in result.message


def test_freshness_check_fails_for_stale_data():
    stale = datetime.now(timezone.utc) - timedelta(seconds=120)
    check = FreshnessCheck("pipeline", last_updated=stale, max_age_seconds=60)
    result = check.run()
    assert not result.passed
    assert "maximum allowed" in result.message


def test_freshness_check_handles_naive_datetime():
    naive = datetime.utcnow() - timedelta(seconds=10)
    check = FreshnessCheck("pipeline", last_updated=naive, max_age_seconds=60)
    result = check.run()
    assert result.passed


# ---------------------------------------------------------------------------
# NullRateCheck
# ---------------------------------------------------------------------------

def test_null_rate_check_passes_low_nulls():
    check = NullRateCheck("email_col", total_rows=1000, null_rows=10)
    result = check.run()
    assert result.passed


def test_null_rate_check_fails_high_nulls():
    check = NullRateCheck("email_col", total_rows=100, null_rows=20, max_null_rate=0.1)
    result = check.run()
    assert not result.passed
    assert "exceeds maximum" in result.message


def test_null_rate_check_fails_on_zero_rows():
    check = NullRateCheck("email_col", total_rows=0, null_rows=0)
    result = check.run()
    assert not result.passed
    assert "No rows" in result.message
