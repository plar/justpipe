import asyncio
from typing import Any, Dict, List

import pytest

from justpipe import EventType, Pipe


@pytest.mark.asyncio
async def test_barrier_timeout_suppresses_late_execution() -> None:
    pipe: Pipe[Dict[str, Any], None] = Pipe()

    @pipe.step(to="combine")
    async def step_a(state: Dict[str, Any]) -> None:
        await asyncio.sleep(0.01)

    @pipe.step(to="combine")
    async def step_b(state: Dict[str, Any]) -> None:
        await asyncio.sleep(0.3)

    @pipe.step(barrier_timeout=0.05)
    async def combine(state: Dict[str, Any]) -> None:
        state["combine"] = True

    state: Dict[str, Any] = {}
    errors: List[str] = []
    async for ev in pipe.run(state):
        if ev.type == EventType.ERROR:
            errors.append(str(ev.data))

    assert errors and any("Barrier timeout" in msg for msg in errors)
    assert state.get("combine") is None
