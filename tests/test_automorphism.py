from symforge.automorphism import canonical_label
from symforge.colored_graph import ColoredGraph
from symforge.group import Group


def make_graph(n: int, edges: list[tuple[int, int]]) -> ColoredGraph:
    g = ColoredGraph.empty(n=n, node_colors=[0] * n)
    for u, v in edges:
        g.add_edge(u, v)
    return g


def group_order_from_autos(autos: list[tuple[int, ...]]) -> int:
    if not autos:
        return 1
    group = Group(autos)
    return group.order().value


def test_cycle_c5_order() -> None:
    edges = [(i, (i + 1) % 5) for i in range(5)]
    g = make_graph(5, edges)
    result = canonical_label(g)
    assert group_order_from_autos(result.automorphisms) == 10


def test_complete_k4_order() -> None:
    edges = [(i, j) for i in range(4) for j in range(i + 1, 4)]
    g = make_graph(4, edges)
    result = canonical_label(g)
    assert group_order_from_autos(result.automorphisms) == 24


def test_two_edges_order() -> None:
    edges = [(0, 1), (2, 3)]
    g = make_graph(4, edges)
    result = canonical_label(g)
    assert group_order_from_autos(result.automorphisms) == 8


def test_nauty_backend_fallback() -> None:
    edges = [(0, 1), (1, 2), (2, 0)]
    g = make_graph(3, edges)
    result = canonical_label(g, backend="nauty")
    assert group_order_from_autos(result.automorphisms) == 6


def test_pynauty_backend() -> None:
    edges = [(0, 1), (1, 2), (2, 0)]
    g = make_graph(3, edges)
    result = canonical_label(g, backend="pynauty")
    assert group_order_from_autos(result.automorphisms) == 6
