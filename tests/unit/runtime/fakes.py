"""Reusable fakes for runtime unit tests."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from justpipe._internal.runtime.meta import _current_step_meta_var
from justpipe._internal.runtime.orchestration.control import InvocationContext
from justpipe.types import EventType, NodeKind


@dataclass
class CompletedCall:
    name: str
    owner: str
    result: Any
    payload: dict[str, Any] | None
    track_owner: bool
    invocation: InvocationContext | None
    already_terminal: bool
    step_meta: dict[str, Any] | None


@dataclass
class FailureCall:
    name: str
    owner: str
    error: Exception
    state: Any
    context: Any
    invocation: InvocationContext | None
    step_meta: dict[str, Any] | None


class _FakeCoordinatorPort:
    """Minimal fake satisfying CoordinatorOrchestrator."""

    def __init__(self, state: Any = None, context: Any = None):
        self.emitted: list[tuple[EventType, str, Any]] = []
        self.completed: list[CompletedCall] = []
        self.failures: list[FailureCall] = []
        self._state = state
        self._context = context

    @property
    def state(self) -> Any:
        return self._state

    @property
    def context(self) -> Any:
        return self._context

    async def emit(
        self,
        event_type: EventType,
        stage: str,
        payload: Any = None,
        **_: Any,
    ) -> None:
        self.emitted.append((event_type, stage, payload))

    async def complete_step(
        self,
        name: str,
        owner: str,
        result: Any,
        payload: dict[str, Any] | None = None,
        track_owner: bool = True,
        invocation: InvocationContext | None = None,
        already_terminal: bool = False,
        step_meta: dict[str, Any] | None = None,
    ) -> None:
        self.completed.append(
            CompletedCall(
                name=name,
                owner=owner,
                result=result,
                payload=payload,
                track_owner=track_owner,
                invocation=invocation,
                already_terminal=already_terminal,
                step_meta=step_meta,
            )
        )

    async def handle_execution_failure(
        self,
        name: str,
        owner: str,
        error: Exception,
        payload: dict[str, Any] | None = None,
        state: Any = None,
        context: Any = None,
        invocation: InvocationContext | None = None,
        step_meta: dict[str, Any] | None = None,
    ) -> None:
        self.failures.append(
            FailureCall(
                name=name,
                owner=owner,
                error=error,
                state=state,
                context=context,
                invocation=invocation,
                step_meta=step_meta,
            )
        )


class _InvokerSuccess:
    def get_node_kind(self, name: str) -> NodeKind:
        return NodeKind.STEP

    async def execute(
        self,
        name: str,
        orchestrator: Any,
        state: Any,
        context: Any,
        payload: dict[str, Any] | None = None,
    ) -> Any:
        return {"ok": True, "name": name, "payload": payload}


class _InvokerWithMeta:
    """Invoker that writes step meta during execution."""

    def get_node_kind(self, name: str) -> NodeKind:
        return NodeKind.STEP

    async def execute(
        self,
        name: str,
        orchestrator: Any,
        state: Any,
        context: Any,
        payload: dict[str, Any] | None = None,
    ) -> Any:
        meta = _current_step_meta_var.get()
        if meta is not None:
            meta.set("model", "gpt-4")
            meta.record_metric("latency", 1.5)
        return None


class _InvokerFailure:
    def get_node_kind(self, name: str) -> NodeKind:
        return NodeKind.STEP

    async def execute(
        self,
        name: str,
        orchestrator: Any,
        state: Any,
        context: Any,
        payload: dict[str, Any] | None = None,
    ) -> Any:
        raise ValueError("boom")


class _InvokerFailureWithMeta:
    """Invoker that writes step meta then fails."""

    def get_node_kind(self, name: str) -> NodeKind:
        return NodeKind.STEP

    async def execute(
        self,
        name: str,
        orchestrator: Any,
        state: Any,
        context: Any,
        payload: dict[str, Any] | None = None,
    ) -> Any:
        meta = _current_step_meta_var.get()
        if meta is not None:
            meta.set("partial", True)
            meta.increment("processed", 3)
        raise ValueError("boom after meta")
