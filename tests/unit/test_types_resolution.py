"""Unit tests for name resolution utilities."""

import pytest
from justpipe.types import _resolve_name


def test_resolve_name_string() -> None:
    assert _resolve_name("foo") == "foo"


def test_resolve_name_callable() -> None:
    def bar() -> None:
        pass

    assert _resolve_name(bar) == "bar"


def test_resolve_name_invalid() -> None:
    with pytest.raises(ValueError):
        _resolve_name(123)  # type: ignore
