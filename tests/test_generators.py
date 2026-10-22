from symforge.generators.algebra import commutative_magma_tables
from symforge.generators.designs import steiner_system
from symforge.generators.graphs import (
    random_regular_graphs,
    regular_graphs,
    strongly_regular_graphs,
)


def test_regular_graph_generator() -> None:
    graphs = list(regular_graphs(4, 2, limit=3, dedup=True))
    assert len(graphs) == 1
    assert graphs[0].structure.n == 4


def test_steiner_system_fano_exists() -> None:
    systems = list(steiner_system(7, 3, t=2, lam=1, limit=1))
    assert len(systems) == 1
    rel = systems[0].structure.relations[0]
    assert len(rel.tuples) == 7


def test_commutative_magma_exists() -> None:
    tables = list(commutative_magma_tables(2, limit=1))
    assert len(tables) == 1


def test_random_regular_graph_degrees() -> None:
    cand = next(random_regular_graphs(6, 3, count=1, seed=1))
    rel = cand.structure.relations[0]
    deg = [0] * cand.structure.n
    for u, v in rel.tuples:
        deg[u] += 1
    assert all(d == 3 for d in deg)


def test_strongly_regular_graph_small() -> None:
    graphs = list(strongly_regular_graphs(4, 1, 0, 0, limit=1))
    assert graphs
    rel = graphs[0].structure.relations[0]
    n = graphs[0].structure.n
    adj = [[0 for _ in range(n)] for _ in range(n)]
    for u, v in rel.tuples:
        adj[u][v] = 1
    for i in range(n):
        assert sum(adj[i]) == 1
    for i in range(n):
        for j in range(i + 1, n):
            cn = 0
            for w in range(n):
                if w == i or w == j:
                    continue
                if adj[i][w] and adj[j][w]:
                    cn += 1
            if adj[i][j]:
                assert cn == 0
            else:
                assert cn == 0


def test_steiner_sat_optional() -> None:
    try:
        from pysat.solvers import Solver  # noqa: F401
    except Exception:
        from symforge.generators.designs import steiner_system_sat

        try:
            list(steiner_system_sat(4, 2, t=1, lam=1, limit=1))
        except ImportError:
            return
        assert False, "Expected ImportError when PySAT is unavailable"
    else:
        from symforge.generators.designs import steiner_system_sat

        systems = list(steiner_system_sat(4, 2, t=1, lam=1, limit=1))
        assert len(systems) == 1
