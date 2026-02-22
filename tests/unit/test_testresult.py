from __future__ import annotations

from justpipe.testing import TestResult
from justpipe.types import Event, EventType


def _ev(event_type: EventType, stage: str, payload: object = None) -> Event:
    """Shorthand factory for Event construction."""
    return Event(type=event_type, stage=stage, payload=payload)


# -- filter() ----------------------------------------------------------------


def test_filter_returns_matching_events():
    events = [
        _ev(EventType.STEP_START, "a"),
        _ev(EventType.STEP_END, "a", payload={"x": 1}),
        _ev(EventType.STEP_START, "b"),
    ]
    result = TestResult(events=events, final_state={})

    filtered = result.filter(EventType.STEP_START)

    assert len(filtered) == 2
    assert all(e.type == EventType.STEP_START for e in filtered)
    assert [e.stage for e in filtered] == ["a", "b"]


def test_filter_returns_empty_list_when_no_matches():
    events = [
        _ev(EventType.STEP_START, "a"),
        _ev(EventType.STEP_END, "a"),
    ]
    result = TestResult(events=events, final_state={})

    assert result.filter(EventType.TOKEN) == []


# -- step_starts -------------------------------------------------------------


def test_step_starts_returns_stage_names():
    events = [
        _ev(EventType.START, "pipeline"),
        _ev(EventType.STEP_START, "load"),
        _ev(EventType.STEP_END, "load"),
        _ev(EventType.STEP_START, "transform"),
        _ev(EventType.STEP_END, "transform"),
        _ev(EventType.FINISH, "pipeline"),
    ]
    result = TestResult(events=events, final_state={})

    assert result.step_starts == ["load", "transform"]


def test_step_starts_returns_empty_list_when_no_step_starts():
    events = [
        _ev(EventType.START, "pipeline"),
        _ev(EventType.FINISH, "pipeline"),
    ]
    result = TestResult(events=events, final_state={})

    assert result.step_starts == []


# -- tokens -------------------------------------------------------------------


def test_tokens_returns_payloads():
    events = [
        _ev(EventType.STEP_START, "stream"),
        _ev(EventType.TOKEN, "stream", payload="chunk1"),
        _ev(EventType.TOKEN, "stream", payload="chunk2"),
        _ev(EventType.TOKEN, "stream", payload="chunk3"),
        _ev(EventType.STEP_END, "stream"),
    ]
    result = TestResult(events=events, final_state={})

    assert result.tokens == ["chunk1", "chunk2", "chunk3"]


def test_tokens_returns_empty_list_when_no_tokens():
    events = [
        _ev(EventType.STEP_START, "a"),
        _ev(EventType.STEP_END, "a"),
    ]
    result = TestResult(events=events, final_state={})

    assert result.tokens == []


# -- was_called() -------------------------------------------------------------


def test_was_called_returns_true_and_false():
    events = [
        _ev(EventType.STEP_START, "fetch"),
        _ev(EventType.STEP_END, "fetch"),
    ]
    result = TestResult(events=events, final_state={})

    assert result.was_called("fetch") is True
    assert result.was_called("missing_step") is False


# -- find_error() -------------------------------------------------------------


def test_find_error_no_stage_returns_first_error():
    events = [
        _ev(EventType.STEP_START, "a"),
        _ev(EventType.STEP_ERROR, "a", payload=ValueError("boom")),
        _ev(EventType.STEP_START, "b"),
        _ev(EventType.STEP_ERROR, "b", payload=RuntimeError("crash")),
    ]
    result = TestResult(events=events, final_state={})

    assert result.find_error() == "boom"


def test_find_error_with_stage_returns_matching_error_or_none():
    events = [
        _ev(EventType.STEP_ERROR, "a", payload=ValueError("first")),
        _ev(EventType.STEP_ERROR, "b", payload=RuntimeError("second")),
    ]
    result = TestResult(events=events, final_state={})

    assert result.find_error(stage="b") == "second"
    assert result.find_error(stage="nonexistent") is None
