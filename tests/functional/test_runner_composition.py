"""Functional tests for runner composition — exercises the full pipeline execution path."""

from justpipe._internal.runtime.engine.pipeline_runner import _PipelineRunner
from justpipe._internal.runtime.engine.composition import build_runner
from justpipe.types import EventType
from tests.unit.runtime.conftest import _empty_config


async def test_build_runner_returns_runnable_runner() -> None:
    runner = build_runner(_empty_config(queue_size=3))
    assert isinstance(runner, _PipelineRunner)
    assert runner._tracker is not None

    events = [event async for event in runner.run(state={})]
    assert any(event.type == EventType.STEP_ERROR for event in events)
    assert events[-1].type is EventType.FINISH
