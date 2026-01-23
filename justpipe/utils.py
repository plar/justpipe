import inspect
from typing import Any, Callable, Dict

from justpipe.types import DefinitionError

STATE_ALIASES: frozenset[str] = frozenset({"s", "state"})
CONTEXT_ALIASES: frozenset[str] = frozenset({"c", "ctx", "context"})
ERROR_ALIASES: frozenset[str] = frozenset({"e", "error", "exception"})
STEP_NAME_ALIASES: frozenset[str] = frozenset({"step_name", "stage"})


def _analyze_signature(
    func: Callable[..., Any],
    state_type: Any,
    context_type: Any,
    expected_unknowns: int = 0,
) -> Dict[str, str]:
    """Analyze function signature and map parameters to state or context."""
    mapping = {}
    sig = inspect.signature(func)
    unknowns = []
    for name, param in sig.parameters.items():
        # 1. Match by Type (skip if type is Any to avoid collisions)
        if param.annotation is state_type and state_type is not Any:
            mapping[name] = "state"
        elif param.annotation is context_type and context_type is not Any:
            mapping[name] = "context"
        # 2. Match by Name (Fallback)
        elif name in STATE_ALIASES:
            mapping[name] = "state"
        elif name in CONTEXT_ALIASES:
            mapping[name] = "context"
        elif name in ERROR_ALIASES:
            mapping[name] = "error"
        elif name in STEP_NAME_ALIASES:
            mapping[name] = "step_name"
        # 3. Handle parameters with default values
        elif param.default is not inspect.Parameter.empty:
            continue
        else:
            mapping[name] = "unknown"
            unknowns.append(name)

    if len(unknowns) > expected_unknowns:
        raise DefinitionError(
            f"Step '{func.__name__}' has {len(unknowns)} unrecognized parameters: {unknowns}. "
            f"Expected {expected_unknowns} unknown parameter(s) for this step type. "
            f"Parameters must be typed as {state_type} or {context_type}, "
            f"or named 'state'/'context'/'error'/'step_name'."
        )

    return mapping
