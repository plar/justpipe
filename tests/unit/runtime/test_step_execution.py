from typing import Any, cast

from justpipe._internal.runtime.execution.step_error_store import _StepErrorStore
from justpipe._internal.runtime.execution.step_execution_coordinator import (
    _StepExecutionCoordinator,
)
from justpipe.types import EventType

from tests.unit.runtime.fakes import (
    CompletedCall,
    _FakeCoordinatorPort,
    _InvokerFailure,
    _InvokerFailureWithMeta,
    _InvokerSuccess,
    _InvokerWithMeta,
)


async def test_execute_step_emits_start_and_completes() -> None:
    step_errors = _StepErrorStore()
    port = _FakeCoordinatorPort(state={"state": 1}, context={"context": 1})
    coordinator = _StepExecutionCoordinator[Any, Any](
        invoker=cast(Any, _InvokerSuccess()),
        orch=port,
        step_errors=step_errors,
    )

    await coordinator.execute_step("step_a", "owner_a", {"x": 1})

    assert port.emitted == [(EventType.STEP_START, "step_a", None)]
    assert port.completed[0].name == "step_a"
    assert port.completed[0].owner == "owner_a"
    assert port.completed[0].payload == {"x": 1}
    assert port.completed[0].track_owner is True
    assert port.completed[0].invocation is not None
    assert port.completed[0].already_terminal is False
    assert not port.failures


async def test_execute_step_captures_step_meta() -> None:
    """Step meta written during execution is captured and passed to complete_step."""
    step_errors = _StepErrorStore()
    port = _FakeCoordinatorPort(state=None, context=None)
    coordinator = _StepExecutionCoordinator[Any, Any](
        invoker=cast(Any, _InvokerWithMeta()),
        orch=port,
        step_errors=step_errors,
    )

    await coordinator.execute_step("step_a", "owner_a")

    assert len(port.completed) == 1
    meta = port.completed[0].step_meta
    assert meta is not None
    assert meta["data"]["model"] == "gpt-4"
    assert meta["metrics"]["latency"] == [1.5]
    # Framework timing is always present
    assert "framework" in meta
    assert meta["framework"]["status"] == "success"
    assert meta["framework"]["attempt"] == 1
    assert isinstance(meta["framework"]["duration_s"], float)
    assert meta["framework"]["duration_s"] >= 0


async def test_execute_step_no_user_meta_has_framework_only() -> None:
    """When no user step meta is written, step_meta still contains framework timing."""
    step_errors = _StepErrorStore()
    port = _FakeCoordinatorPort(state=None, context=None)
    coordinator = _StepExecutionCoordinator[Any, Any](
        invoker=cast(Any, _InvokerSuccess()),
        orch=port,
        step_errors=step_errors,
    )

    await coordinator.execute_step("step_a", "owner_a")

    assert len(port.completed) == 1
    meta = port.completed[0].step_meta
    assert meta is not None
    assert "framework" in meta
    assert meta["framework"]["status"] == "success"
    assert meta["framework"]["attempt"] == 1
    assert isinstance(meta["framework"]["duration_s"], float)
    # No user data keys
    assert "data" not in meta
    assert "tags" not in meta


async def test_fail_step_records_error_and_emits_terminal_step() -> None:
    step_errors = _StepErrorStore()
    port = _FakeCoordinatorPort()

    async def _raise_if_called(*_: Any, **__: Any) -> None:
        raise AssertionError(
            "handle_execution_failure should not be called in fail_step"
        )

    port.handle_execution_failure = _raise_if_called  # type: ignore[method-assign]

    coordinator = _StepExecutionCoordinator[Any, Any](
        invoker=cast(Any, _InvokerSuccess()),
        orch=port,
        step_errors=step_errors,
    )

    err = RuntimeError("x")
    await coordinator.fail_step("step_a", "owner_a", err, track_owner=False)

    assert step_errors.consume("step_a") is err
    assert port.emitted == [(EventType.STEP_ERROR, "step_a", "x")]
    assert port.completed == [
        CompletedCall(
            name="step_a",
            owner="owner_a",
            result=None,
            payload=None,
            track_owner=False,
            invocation=None,
            already_terminal=True,
            step_meta=None,
        )
    ]


async def test_fail_step_with_step_meta() -> None:
    """fail_step passes step_meta to STEP_ERROR emit and complete_step."""
    step_errors = _StepErrorStore()
    port = _FakeCoordinatorPort()

    async def _raise_if_called(*_: Any, **__: Any) -> None:
        raise AssertionError("handle_execution_failure should not be called")

    port.handle_execution_failure = _raise_if_called  # type: ignore[method-assign]

    coordinator = _StepExecutionCoordinator[Any, Any](
        invoker=cast(Any, _InvokerSuccess()),
        orch=port,
        step_errors=step_errors,
    )

    meta = {"data": {"partial": True}}
    await coordinator.fail_step("step_a", "owner_a", RuntimeError("x"), step_meta=meta)

    # step_meta passed through to complete_step
    assert port.completed[0].step_meta == meta


async def test_execute_step_failure_delegates_to_failure_handler() -> None:
    step_errors = _StepErrorStore()
    port = _FakeCoordinatorPort(state={"s": 1}, context={"c": 1})

    async def _raise_if_called(*_: Any, **__: Any) -> None:
        raise AssertionError("complete_step should not be called on failure path")

    port.complete_step = _raise_if_called  # type: ignore[method-assign]

    coordinator = _StepExecutionCoordinator[Any, Any](
        invoker=cast(Any, _InvokerFailure()),
        orch=port,
        step_errors=step_errors,
    )

    await coordinator.execute_step("step_a", "owner_a")

    assert port.emitted == [(EventType.STEP_START, "step_a", None)]
    assert len(port.failures) == 1
    assert port.failures[0].name == "step_a"
    assert port.failures[0].owner == "owner_a"
    assert isinstance(port.failures[0].error, ValueError)
    assert port.failures[0].state == {"s": 1}
    assert port.failures[0].context == {"c": 1}
    assert port.failures[0].invocation is not None
    # Framework timing present even without user meta
    meta = port.failures[0].step_meta
    assert meta is not None
    assert meta["framework"]["status"] == "error"


async def test_execute_step_failure_carries_partial_step_meta() -> None:
    """When a step fails after writing meta, the partial meta is passed to handle_execution_failure."""
    step_errors = _StepErrorStore()
    port = _FakeCoordinatorPort(state=None, context=None)

    async def _raise_if_called(*_: Any, **__: Any) -> None:
        raise AssertionError("complete_step should not be called on failure path")

    port.complete_step = _raise_if_called  # type: ignore[method-assign]

    coordinator = _StepExecutionCoordinator[Any, Any](
        invoker=cast(Any, _InvokerFailureWithMeta()),
        orch=port,
        step_errors=step_errors,
    )

    await coordinator.execute_step("step_a", "owner_a")

    assert len(port.failures) == 1
    meta = port.failures[0].step_meta
    assert meta is not None
    assert meta["data"]["partial"] is True
    assert meta["counters"]["processed"] == 3
    # Framework timing on error path
    assert meta["framework"]["status"] == "error"
    assert meta["framework"]["attempt"] == 1
    assert isinstance(meta["framework"]["duration_s"], float)
