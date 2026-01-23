"""Functional tests for routing logic (switches, dynamic returns)."""

import pytest
from typing import Any, List
from justpipe import Pipe, EventType, Stop
from justpipe.types import _Next


@pytest.mark.asyncio
async def test_dynamic_routing(state: Any) -> None:
    pipe: Pipe[Any, Any] = Pipe()
    executed: List[bool] = []

    @pipe.step("start")
    async def start() -> _Next:
        return _Next("target")

    @pipe.step("target")
    async def target() -> None:
        executed.append(True)

    async for _ in pipe.run(state):
        pass
    assert executed


@pytest.mark.asyncio
async def test_declarative_switch(state: Any) -> None:
    pipe: Pipe[Any, Any] = Pipe()
    executed: List[str] = []

    @pipe.switch("start", routes={"a": "step_a", "b": "step_b"})
    async def start() -> str:
        return "b"

    @pipe.step("step_a")
    async def step_a() -> None:
        executed.append("a")

    @pipe.step("step_b")
    async def step_b() -> None:
        executed.append("b")

    async for _ in pipe.run(state):
        pass
    assert executed == ["b"]


@pytest.mark.asyncio
async def test_switch_callable_routes() -> None:
    pipe: Pipe[Any, Any] = Pipe()

    @pipe.step("a")
    async def a() -> None:
        pass

    @pipe.step("b")
    async def b() -> None:
        pass

    def route_logic(val: bool) -> str:
        return "a" if val else "b"

    @pipe.switch("switch", routes=route_logic)
    async def switch() -> bool:
        return True

    # We just ensure it runs without error and routes correctly (implied by no error)
    async for _ in pipe.run(None):
        pass


@pytest.mark.asyncio
async def test_switch_no_match_no_default() -> None:
    pipe: Pipe[Any, Any] = Pipe()

    @pipe.switch("switch", routes={"x": "y"})
    async def switch() -> str:
        return "z"  # No match

    events = []
    async for ev in pipe.run(None):
        if ev.type == EventType.ERROR:
            events.append(ev)

    assert len(events) > 0
    assert "matches no route" in str(events[0].data)


@pytest.mark.asyncio
async def test_switch_returns_stop() -> None:
    pipe: Pipe[Any, Any] = Pipe()

    @pipe.switch("switch", routes={"stop": Stop})
    async def switch() -> str:
        return "stop"

    events = []
    async for ev in pipe.run(None):
        events.append(ev)


@pytest.mark.asyncio
async def test_switch_callable_returns_stop() -> None:
    pipe: Pipe[Any, Any] = Pipe()

    @pipe.switch("switch", routes=lambda x: Stop)
    async def switch() -> str:
        return "ignored"

    # Should run without error and stop
    async for _ in pipe.run(None):
        pass
