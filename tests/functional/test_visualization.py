from typing import Any
from justpipe import Pipe


def test_empty_graph() -> None:
    pipe: Pipe[Any, Any] = Pipe()
    mermaid = pipe.graph()
    assert "No steps registered" in mermaid


def test_linear_graph() -> None:
    pipe: Pipe[Any, Any] = Pipe()

    @pipe.step("a", to="b")
    def a() -> None:
        pass

    @pipe.step("b")
    def b() -> None:
        pass

    mermaid = pipe.graph()
    # Check for node labels (Title cased)
    assert '["A"]' in mermaid
    assert '["B"]' in mermaid
    # Check for connection
    assert "-->" in mermaid
    assert "Start -->" in mermaid
    assert "--> End" in mermaid


def test_branching_graph() -> None:
    pipe: Pipe[Any, Any] = Pipe()

    @pipe.step("start", to=["left", "right"])
    def start() -> None:
        pass

    @pipe.step("left", to="end")
    def left() -> None:
        pass

    @pipe.step("right", to="end")
    def right() -> None:
        pass

    @pipe.step("end")
    def end() -> None:
        pass

    mermaid = pipe.graph()
    assert '["Start"]' in mermaid
    assert '["Left"]' in mermaid
    assert '["Right"]' in mermaid
    assert "subgraph parallel" in mermaid


def test_isolated_steps() -> None:
    pipe: Pipe[Any, Any] = Pipe()

    @pipe.step("main")
    def main() -> None:
        pass

    @pipe.step("orphan")
    def orphan() -> None:
        pass

    mermaid = pipe.graph()
    # Both steps are roots, so neither is isolated
    assert "subgraph utilities" not in mermaid
    assert "Start -->" in mermaid
    assert "Main" in mermaid
    assert "Orphan" in mermaid
    assert '["Orphan"]' in mermaid


def test_streaming_styling() -> None:
    pipe: Pipe[Any, Any] = Pipe()

    @pipe.step("streamer")
    async def streamer() -> Any:
        yield 1

    mermaid = pipe.graph()
    assert '["Streamer ⚡"]' in mermaid
    assert "class" in mermaid and "streaming" in mermaid


def test_custom_theme() -> None:
    from justpipe.visualization import MermaidTheme, generate_mermaid_graph

    theme = MermaidTheme(step_fill="#000000")
    pipe: Pipe[Any, Any] = Pipe()

    @pipe.step("a")
    def a() -> None:
        pass

    mermaid = generate_mermaid_graph(pipe._steps, pipe._topology, theme=theme)
    assert "#000000" in mermaid


def test_complex_dag() -> None:
    pipe: Pipe[Any, Any] = Pipe()

    #      /-> B -> D
    # A --+
    #      \-> C -> E
    # F (isolated)

    @pipe.step("A", to=["B", "C"])
    def step_a() -> None:
        pass

    @pipe.step("B", to="D")
    def step_b() -> None:
        pass

    @pipe.step("C", to="E")
    def step_c() -> None:
        pass

    @pipe.step("D")
    def step_d() -> None:
        pass

    @pipe.step("E")
    def step_e() -> None:
        pass

    @pipe.step("F")
    def step_f() -> None:
        pass

    graph = pipe.graph()

    # Structural checks (Labels)
    assert '["A"]' in graph
    assert '["B"]' in graph
    assert '["C"]' in graph

    # Styling checks
    assert "class" in graph and "step;" in graph
    assert "subgraph utilities" in graph
    assert '["F"]' in graph


def test_graph_direction() -> None:
    from justpipe.visualization import generate_mermaid_graph

    pipe: Pipe[Any, Any] = Pipe()

    @pipe.step("a")
    def a() -> None:
        pass

    graph = generate_mermaid_graph(pipe._steps, pipe._topology, direction="LR")
    assert "graph LR" in graph


def test_id_sanitization() -> None:
    pipe: Pipe[Any, Any] = Pipe()

    @pipe.step("my step")
    def my_step() -> None:
        pass

    @pipe.step("step-2")
    def step_2() -> None:
        pass

    graph = pipe.graph()
    # IDs should be safe (n0, n1, etc)
    assert "n0" in graph
    assert "n1" in graph
    # Labels should be preserved (Title cased)
    assert "My Step" in graph
    assert "Step-2" in graph
