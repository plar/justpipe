"""Integration tests for SQLiteBackend."""

from __future__ import annotations

import sqlite3
import tempfile
from pathlib import Path

import pytest

from justpipe.storage.sqlite import SQLiteBackend
from justpipe.types import PipelineTerminalStatus
from tests.factories import make_events, make_run


def test_sqlite_run_with_error() -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        backend = SQLiteBackend(Path(tmpdir) / "runs.db")
        run = make_run(
            "err1",
            status=PipelineTerminalStatus.FAILED,
            error_message="step exploded",
            error_step="step_a",
        )
        backend.save_run(run, make_events())
        result = backend.get_run("err1")
        assert result is not None
        assert result.status == PipelineTerminalStatus.FAILED
        assert result.error_message == "step exploded"
        assert result.error_step == "step_a"


def test_sqlite_run_meta_stored() -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        backend = SQLiteBackend(Path(tmpdir) / "runs.db")
        run = make_run(
            "meta1",
            run_meta='{"run": {"data": {"key": "val"}}}',
        )
        backend.save_run(run, [])
        result = backend.get_run("meta1")
        assert result is not None
        assert result.run_meta == '{"run": {"data": {"key": "val"}}}'


# ---------------------------------------------------------------------------
# SQLite error path tests
# ---------------------------------------------------------------------------


def test_sqlite_corrupt_db_raises_on_init() -> None:
    """Corrupt database file raises on schema initialization."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "runs.db"
        db_path.write_bytes(b"this is not a sqlite database")

        with pytest.raises(sqlite3.DatabaseError):
            SQLiteBackend(db_path)


def test_sqlite_duplicate_run_id_raises() -> None:
    """Inserting a run with a duplicate ID raises IntegrityError."""
    with tempfile.TemporaryDirectory() as tmpdir:
        backend = SQLiteBackend(Path(tmpdir) / "runs.db")
        backend.save_run(make_run("dup-1"), [])

        with pytest.raises(sqlite3.IntegrityError):
            backend.save_run(make_run("dup-1"), [])


@pytest.mark.parametrize(
    ("run_id", "create_run"),
    [
        pytest.param("empty-run", True, id="empty_run"),
        pytest.param("does-not-exist", False, id="nonexistent_run"),
    ],
)
def test_sqlite_get_events_returns_empty(run_id: str, create_run: bool) -> None:
    """Run with zero events or nonexistent run returns empty list."""
    with tempfile.TemporaryDirectory() as tmpdir:
        backend = SQLiteBackend(Path(tmpdir) / "runs.db")
        if create_run:
            backend.save_run(make_run(run_id), [])
        assert backend.get_events(run_id) == []


def test_sqlite_read_only_after_close() -> None:
    """Backend creates new connections per operation, so separate instances work."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "runs.db"
        backend1 = SQLiteBackend(db_path)
        backend1.save_run(make_run("shared"), make_events())

        # Second instance reads same data
        backend2 = SQLiteBackend(db_path)
        result = backend2.get_run("shared")
        assert result is not None
        assert result.run_id == "shared"
