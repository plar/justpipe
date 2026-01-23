"""Functional tests for core pipeline execution."""

import pytest
import asyncio
from typing import Any, List, AsyncGenerator
from justpipe import Pipe, EventType


@pytest.mark.asyncio
async def test_linear_execution_flow(state: Any) -> None:
    pipe: Pipe[Any, Any] = Pipe()
    events: List[Any] = []

    @pipe.step("start", to="step2")
    async def start() -> None:
        return None

    @pipe.step("step2")
    async def step2() -> None:
        pass

    async for event in pipe.run(state):
        events.append(event)

    types = [e.type for e in events]
    assert EventType.START in types
    assert EventType.FINISH in types
    assert [e.stage for e in events if e.type == EventType.STEP_START] == [
        "start",
        "step2",
    ]


@pytest.mark.asyncio
async def test_streaming_execution(state: Any) -> None:
    pipe: Pipe[Any, Any] = Pipe()
    tokens: List[Any] = []

    @pipe.step("streamer")
    async def streamer() -> AsyncGenerator[str, None]:
        yield "a"
        yield "b"

    async for event in pipe.run(state):
        if event.type == EventType.TOKEN:
            tokens.append(event.data)
    assert tokens == ["a", "b"]


@pytest.mark.asyncio
async def test_step_not_found(state: Any) -> None:
    pipe: Pipe[Any, Any] = Pipe()
    errors: List[Any] = []

    @pipe.step("start", to="non_existent")
    async def start() -> None:
        pass

    async for event in pipe.run(state):
        if event.type == EventType.ERROR:
            errors.append(event)
    assert any("Step not found" in str(e.data) for e in errors)


@pytest.mark.asyncio
async def test_step_timeout_execution() -> None:
    pipe: Pipe[Any, Any] = Pipe()

    @pipe.step("slow", timeout=0.1)
    async def slow() -> None:
        await asyncio.sleep(0.5)

    events: List[Any] = []
    async for ev in pipe.run(None):
        if ev.type == EventType.ERROR:
            events.append(ev)

    assert len(events) == 1
    assert "timed out" in str(events[0].data)


def test_async_gen_retry_warning() -> None:
    pipe: Pipe[Any, Any] = Pipe()
    with pytest.warns(UserWarning, match="cannot retry automatically"):

        @pipe.step("stream", retries=3)
        async def stream() -> AsyncGenerator[int, None]:
            yield 1


def test_advanced_retry_config() -> None:
    pipe: Pipe[Any, Any] = Pipe()

    # Should not raise
    @pipe.step("retry", retries={"stop": 1})
    async def retry_step() -> None:
        pass

    assert "retry" in pipe._steps