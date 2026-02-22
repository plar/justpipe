from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from justpipe._internal.runtime.engine.run_context import _RunContext
from justpipe._internal.runtime.orchestration.orchestrator import _Orchestrator
from justpipe._internal.shared.execution_tracker import _ExecutionTracker


def _make_orchestrator() -> _Orchestrator:
    ctx = _RunContext()
    kernel = MagicMock()
    tracker = _ExecutionTracker()
    metrics = MagicMock()
    return _Orchestrator(ctx=ctx, kernel=kernel, tracker=tracker, metrics=metrics)


def test_wire_called_twice_raises() -> None:
    orch = _make_orchestrator()
    orch.wire(step_execution=MagicMock(), failure_handler=MagicMock())

    with pytest.raises(RuntimeError, match="already wired"):
        orch.wire(step_execution=MagicMock(), failure_handler=MagicMock())


async def test_fail_step_before_wire_raises() -> None:
    orch = _make_orchestrator()

    with pytest.raises(RuntimeError, match="not wired"):
        await orch.fail_step("step_a", "owner_a", RuntimeError("boom"))


async def test_execute_step_before_wire_raises() -> None:
    orch = _make_orchestrator()

    with pytest.raises(RuntimeError, match="not wired"):
        await orch.execute_step("step_a", "owner_a")


async def test_handle_execution_failure_before_wire_raises() -> None:
    orch = _make_orchestrator()

    with pytest.raises(RuntimeError, match="not wired"):
        await orch.handle_execution_failure(
            "step_a", "owner_a", RuntimeError("boom"), payload=None, state=None, context=None
        )
