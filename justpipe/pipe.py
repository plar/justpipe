import inspect
from typing import (
    Any,
    AsyncGenerator,
    Callable,
    Dict,
    Generic,
    Iterator,
    List,
    Optional,
    TypeVar,
    Union,
    get_args,
)

from justpipe.middleware import Middleware, tenacity_retry_middleware
from justpipe.runner import _PipelineRunner
from justpipe.graph import _validate_routing_target
from justpipe.types import (
    Event,
    Stop,
    StepContext,
    StepInfo,
    _Map,
    _Next,
    _resolve_name,
    _Run,
    _Stop,
)
from justpipe.utils import _analyze_signature
from justpipe.visualization import generate_mermaid_graph

StateT = TypeVar("StateT")
ContextT = TypeVar("ContextT")


class Pipe(Generic[StateT, ContextT]):
    def __init__(
        self,
        name: str = "Pipe",
        middleware: Optional[List[Middleware]] = None,
        queue_size: int = 0,
        validate_on_run: bool = False,
    ):
        self.name = name
        self.queue_size = queue_size
        self.middleware = (
            list(middleware) if middleware is not None else [tenacity_retry_middleware]
        )
        self._validate_on_run = validate_on_run
        self._steps: Dict[str, Callable[..., Any]] = {}
        self._topology: Dict[str, List[str]] = {}
        self._startup: List[Callable[..., Any]] = []
        self._shutdown: List[Callable[..., Any]] = []
        self._on_error: Optional[Callable[..., Any]] = None
        self._injection_metadata: Dict[str, Dict[str, str]] = {}
        self._step_metadata: Dict[str, Dict[str, Any]] = {}
        self._event_hooks: List[Callable[[Event], Event]] = []

    def _get_types(self) -> tuple[Any, Any]:
        orig = getattr(self, "__orig_class__", None)
        if orig:
            args = get_args(orig)
            if len(args) == 2:
                return args[0], args[1]
        return Any, Any

    def add_middleware(self, mw: Middleware) -> None:
        self.middleware.append(mw)

    def add_event_hook(self, hook: Callable[[Event], Event]) -> None:
        """Add a hook that can transform events before they are yielded."""
        self._event_hooks.append(hook)

    def on_startup(self, func: Callable[..., Any]) -> Callable[..., Any]:
        self._startup.append(func)
        return func

    def on_shutdown(self, func: Callable[..., Any]) -> Callable[..., Any]:
        self._shutdown.append(func)
        return func

    def on_error(self, func: Callable[..., Any]) -> Callable[..., Any]:
        self._on_error = func
        state_type, context_type = self._get_types()
        self._injection_metadata["system:on_error"] = _analyze_signature(
            func, state_type, context_type, expected_unknowns=0
        )
        return func

    def _register_step_config(
        self,
        name_or_func: Union[str, Callable[..., Any]],
        func: Callable[..., Any],
        to: Union[
            str, List[str], Callable[..., Any], List[Callable[..., Any]], None
        ] = None,
        barrier_timeout: Optional[float] = None,
        on_error: Optional[Callable[..., Any]] = None,
        expected_unknowns: int = 1,
        **kwargs: Any,
    ) -> str:
        """Common logic for registering a step's configuration and metadata."""
        stage_name = _resolve_name(name_or_func)
        self._step_metadata[stage_name] = {
            **kwargs,
            "barrier_timeout": barrier_timeout,
            "on_error": on_error,
        }

        state_type, context_type = self._get_types()
        self._injection_metadata[stage_name] = _analyze_signature(
            func,
            state_type,
            context_type,
            expected_unknowns=expected_unknowns,
        )

        if on_error:
            self._injection_metadata[f"{stage_name}:on_error"] = _analyze_signature(
                on_error, state_type, context_type, expected_unknowns=0
            )

        if to:
            _validate_routing_target(to)
            self._topology[stage_name] = [
                _resolve_name(t) for t in (to if isinstance(to, list) else [to])
            ]

        return stage_name

    def _wrap_step(
        self, stage_name: str, func: Callable[..., Any], kwargs: Dict[str, Any]
    ) -> None:
        """Apply middleware stack and store the step."""
        wrapped = func
        ctx = StepContext(name=stage_name, kwargs=kwargs, pipe_name=self.name)
        for mw in self.middleware:
            wrapped = mw(wrapped, ctx)
        self._steps[stage_name] = wrapped

    def step(
        self,
        name: Union[str, Callable[..., Any], None] = None,
        to: Union[
            str, List[str], Callable[..., Any], List[Callable[..., Any]], None
        ] = None,
        barrier_timeout: Optional[float] = None,
        on_error: Optional[Callable[..., Any]] = None,
        **kwargs: Any,
    ) -> Callable[..., Any]:
        def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
            stage_name = self._register_step_config(
                name or func, func, to, barrier_timeout, on_error, **kwargs
            )
            self._wrap_step(stage_name, func, kwargs)
            return func

        if callable(name) and to is None and not kwargs:
            return decorator(name)
        return decorator

    def map(
        self,
        name: Union[str, Callable[..., Any], None] = None,
        using: Union[str, Callable[..., Any], None] = None,
        to: Union[
            str, List[str], Callable[..., Any], List[Callable[..., Any]], None
        ] = None,
        barrier_timeout: Optional[float] = None,
        on_error: Optional[Callable[..., Any]] = None,
        **kwargs: Any,
    ) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        if using is None:
            raise ValueError("@pipe.map requires 'using' parameter")

        _validate_routing_target(using)

        def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
            target_name = _resolve_name(using)
            stage_name = self._register_step_config(
                name or func,
                func,
                to,
                barrier_timeout,
                on_error,
                map_target=target_name,
                **kwargs,
            )

            async def map_wrapper(**inner_kwargs: Any) -> _Map:
                if inspect.isasyncgenfunction(func):
                    items = [item async for item in func(**inner_kwargs)]
                    return _Map(items=items, target=target_name)

                result = await func(**inner_kwargs)
                try:
                    items = list(result)
                except TypeError:
                    raise ValueError(
                        f"Step '{stage_name}' decorated with @pipe.map "
                        f"must return an iterable, got {type(result)}"
                    )
                return _Map(items=items, target=target_name)

            self._wrap_step(stage_name, map_wrapper, kwargs)
            return func

        return decorator

    def switch(
        self,
        name: Union[str, Callable[..., Any], None] = None,
        routes: Union[
            Dict[
                Any,
                Union[
                    str,
                    Callable[..., Any],
                    _Stop,
                ],
            ],
            Callable[[Any], Union[str, _Stop]],
            None,
        ] = None,
        default: Union[str, Callable[..., Any], None] = None,
        barrier_timeout: Optional[float] = None,
        on_error: Optional[Callable[..., Any]] = None,
        **kwargs: Any,
    ) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        if routes is None:
            raise ValueError("@pipe.switch requires 'routes' parameter")

        _validate_routing_target(routes)
        if default:
            _validate_routing_target(default)

        def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
            normalized_routes = {}
            if isinstance(routes, dict):
                for key, target in routes.items():
                    normalized_routes[key] = (
                        "Stop" if isinstance(target, _Stop) else _resolve_name(target)
                    )

            stage_name = self._register_step_config(
                name or func,
                func,
                None,
                barrier_timeout,
                on_error,
                switch_routes=normalized_routes
                if isinstance(routes, dict)
                else "dynamic",
                switch_default=_resolve_name(default) if default else None,
                **kwargs,
            )

            async def switch_wrapper(**inner_kwargs: Any) -> Any:
                result = await func(**inner_kwargs)
                target = (
                    routes.get(result, default)
                    if isinstance(routes, dict)
                    else routes(result)
                )

                if target is None:
                    raise ValueError(
                        f"Step '{stage_name}' (switch) returned {result}, "
                        f"which matches no route and no default was provided."
                    )

                return Stop if isinstance(target, _Stop) else _Next(target)

            self._wrap_step(stage_name, switch_wrapper, kwargs)
            return func

        return decorator

    def sub(
        self,
        name: Union[str, Callable[..., Any], None] = None,
        using: Any = None,
        to: Union[
            str, List[str], Callable[..., Any], List[Callable[..., Any]], None
        ] = None,
        barrier_timeout: Optional[float] = None,
        on_error: Optional[Callable[..., Any]] = None,
        **kwargs: Any,
    ) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        if using is None:
            raise ValueError("@pipe.sub requires 'using' parameter")

        _validate_routing_target(using)

        def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
            stage_name = self._register_step_config(
                name or func,
                func,
                to,
                barrier_timeout,
                on_error,
                sub_pipeline=using.name if hasattr(using, "name") else "SubPipe",
                sub_pipeline_obj=using,
                **kwargs,
            )

            async def sub_wrapper(**inner_kwargs: Any) -> _Run:
                result = await func(**inner_kwargs)
                return _Run(pipe=using, state=result)

            self._wrap_step(stage_name, sub_wrapper, kwargs)
            return func

        return decorator

    def graph(self) -> str:
        return generate_mermaid_graph(
            self._steps,
            self._topology,
            self._step_metadata,
            startup_hooks=self._startup,
            shutdown_hooks=self._shutdown,
        )

    def steps(self) -> Iterator[StepInfo]:
        """Iterate over registered steps with their configuration."""
        for name, meta in self._step_metadata.items():
            # Determine the kind of step
            if "map_target" in meta:
                kind = "map"
            elif "switch_routes" in meta:
                kind = "switch"
            elif "sub_pipeline" in meta:
                kind = "sub"
            else:
                kind = "step"

            # Collect targets from topology and special routing
            targets = list(self._topology.get(name, []))
            if "map_target" in meta:
                targets.append(meta["map_target"])
            if "switch_routes" in meta and isinstance(meta["switch_routes"], dict):
                targets.extend(t for t in meta["switch_routes"].values() if t != "Stop")
            if meta.get("switch_default"):
                targets.append(meta["switch_default"])

            yield StepInfo(
                name=name,
                timeout=meta.get("timeout"),
                retries=meta.get("retries", 0) if meta.get("retries") else 0,
                barrier_timeout=meta.get("barrier_timeout"),
                has_error_handler=meta.get("on_error") is not None,
                targets=targets,
                kind=kind,
            )

    @property
    def topology(self) -> Dict[str, List[str]]:
        """Read-only view of the execution graph."""
        return dict(self._topology)

    def validate(self) -> None:
        """
        Validate the pipeline graph integrity.
        Raises:
            ValueError: if any unresolvable references or integrity issues are found.
        """
        from justpipe.graph import _DependencyGraph

        graph = _DependencyGraph(self._steps, self._topology, self._step_metadata)
        graph.validate()

    async def run(
        self,
        state: StateT,
        context: Optional[ContextT] = None,
        start: Union[str, Callable[..., Any], None] = None,
        queue_size: Optional[int] = None,
    ) -> AsyncGenerator[Event, None]:
        if self._validate_on_run:
            self.validate()
        runner: _PipelineRunner[StateT, ContextT] = _PipelineRunner(
            self._steps,
            self._topology,
            self._injection_metadata,
            self._step_metadata,
            self._startup,
            self._shutdown,
            on_error=self._on_error,
            queue_size=queue_size if queue_size is not None else self.queue_size,
            event_hooks=self._event_hooks,
        )
        async for event in runner.run(state, context, start):
            yield event