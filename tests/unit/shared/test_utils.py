"""Unit tests for shared utilities."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from justpipe._internal.shared.utils import resolve_storage_path


def test_resolve_storage_path_respects_env(monkeypatch: Any, tmp_path: Path) -> None:
    monkeypatch.setenv("JUSTPIPE_STORAGE_PATH", str(tmp_path))
    assert resolve_storage_path() == tmp_path


def test_resolve_storage_path_default(monkeypatch: Any) -> None:
    monkeypatch.delenv("JUSTPIPE_STORAGE_PATH", raising=False)
    assert resolve_storage_path() == Path.home() / ".justpipe"
