"""Shared helpers for functional tests."""

from __future__ import annotations

from typing import Any

from justpipe import EventType, Pipe


async def _collect_events(
    pipe: Pipe[Any, Any], state: Any = None, **kwargs: Any
) -> list[Any]:
    return [e async for e in pipe.run(state, **kwargs)]


def _types(events: list[Any]) -> list[EventType]:
    return [e.type for e in events]


def _stages(events: list[Any], event_type: EventType) -> list[str]:
    return [e.stage for e in events if e.type == event_type]


def _finish(events: list[Any]) -> Any:
    finishes = [e for e in events if e.type == EventType.FINISH]
    assert len(finishes) == 1, f"Expected exactly 1 FINISH, got {len(finishes)}"
    return finishes[0]
