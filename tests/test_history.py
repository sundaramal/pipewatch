"""Tests for pipewatch.history."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from pipewatch.checks.base import CheckResult
from pipewatch.history import HistoryEntry, HistoryStore
from pipewatch.runner import RunReport


def _make_report(passed: int, failed: int) -> RunReport:
    results = [CheckResult(name=f"c{i}", passed=True, message="ok") for i in range(passed)]
    results += [CheckResult(name=f"f{i}", passed=False, message="fail") for i in range(failed)]
    return RunReport(results=results)


@pytest.fixture
def store(tmp_path: Path) -> HistoryStore:
    return HistoryStore(path=tmp_path / "history.jsonl")


def test_record_creates_file(store: HistoryStore) -> None:
    report = _make_report(3, 0)
    store.record(report, pipeline="my_pipeline")
    assert store.path.exists()


def test_record_entry_fields(store: HistoryStore) -> None:
    report = _make_report(2, 1)
    entry = store.record(report, pipeline="pipe_a")
    assert entry.pipeline == "pipe_a"
    assert entry.total == 3
    assert entry.num_passed == 2
    assert entry.num_failed == 1
    assert entry.passed is False


def test_load_returns_all_entries(store: HistoryStore) -> None:
    store.record(_make_report(1, 0), pipeline="p")
    store.record(_make_report(0, 1), pipeline="p")
    entries = store.load()
    assert len(entries) == 2


def test_load_filters_by_pipeline(store: HistoryStore) -> None:
    store.record(_make_report(1, 0), pipeline="alpha")
    store.record(_make_report(1, 0), pipeline="beta")
    entries = store.load(pipeline="alpha")
    assert len(entries) == 1
    assert entries[0].pipeline == "alpha"


def test_load_respects_limit(store: HistoryStore) -> None:
    for _ in range(10):
        store.record(_make_report(1, 0), pipeline="p")
    entries = store.load(limit=3)
    assert len(entries) == 3


def test_load_empty_when_no_file(store: HistoryStore) -> None:
    assert store.load() == []


def test_clear_removes_file(store: HistoryStore) -> None:
    store.record(_make_report(1, 0), pipeline="p")
    store.clear()
    assert not store.path.exists()


def test_entry_round_trips_json() -> None:
    entry = HistoryEntry(
        timestamp="2024-01-01T00:00:00+00:00",
        pipeline="demo",
        total=4,
        num_passed=3,
        num_failed=1,
        passed=False,
    )
    restored = HistoryEntry.from_json(entry.to_json())
    assert restored == entry


def test_load_skips_corrupt_lines(store: HistoryStore) -> None:
    store.path.write_text("not json\n{\"bad\": true}\n", encoding="utf-8")
    entries = store.load()
    assert entries == []
