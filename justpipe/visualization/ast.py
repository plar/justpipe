"""Semantic AST model for pipeline visualization."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class NodeKind(Enum):
    """Kind of pipeline node."""

    STEP = "step"
    STREAMING = "streaming"
    MAP = "map"
    SWITCH = "switch"
    SUB = "sub"


@dataclass
class VisualNode:
    """A single step in the pipeline."""

    id: str
    name: str
    kind: NodeKind
    is_entry: bool = False
    is_terminal: bool = False
    is_isolated: bool = False
    is_map_target: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)
    sub_graph: Optional["VisualAST"] = None


@dataclass
class VisualEdge:
    """Connection between nodes."""

    source: str
    target: str
    label: Optional[str] = None
    is_map_edge: bool = False


@dataclass
class ParallelGroup:
    """A group of nodes that execute in parallel."""

    id: str
    source_id: str
    node_ids: List[str]


@dataclass
class VisualAST:
    """Semantic representation of pipeline structure."""

    nodes: Dict[str, VisualNode]
    edges: List[VisualEdge]
    parallel_groups: List[ParallelGroup]
    startup_hooks: List[str] = field(default_factory=list)
    shutdown_hooks: List[str] = field(default_factory=list)
