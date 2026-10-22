from __future__ import annotations

import random
from typing import Iterator, List, Optional, Set, Tuple

from symforge.automorphism import canonical_label
from symforge.relational import Relation, RelationalStructure, compile_to_colored_graph
from symforge.search import Candidate


def _pairs(n: int) -> List[Tuple[int, int]]:
    return [(i, j) for i in range(n) for j in range(i + 1, n)]


def regular_graphs(
    n: int,
    degree: int,
    limit: Optional[int] = None,
    dedup: bool = True,
) -> Iterator[Candidate]:
    if n * degree % 2 != 0:
        return
    target_edges = n * degree // 2
    pairs = _pairs(n)
    degrees = [0] * n
    edges: List[Tuple[int, int]] = []
    seen: Set[bytes] = set()
    produced = 0

    def remaining_possible(start_idx: int) -> List[int]:
        remaining = [0] * n
        for u, v in pairs[start_idx:]:
            remaining[u] += 1
            remaining[v] += 1
        return remaining

    def recurse(idx: int) -> Iterator[Candidate]:
        nonlocal produced
        if limit is not None and produced >= limit:
            return
        if len(edges) > target_edges:
            return
        if idx == len(pairs):
            if len(edges) != target_edges:
                return
            if any(d != degree for d in degrees):
                return
            rel_edges = []
            for u, v in edges:
                rel_edges.append((u, v))
                rel_edges.append((v, u))
            rel = Relation(name="edge", arity=2, tuples=rel_edges)
            struct = RelationalStructure(n=n, relations=[rel])
            if dedup:
                compiled = compile_to_colored_graph(struct)
                label = canonical_label(compiled.graph, max_nodes=200).canonical_label
                if label in seen:
                    return
                seen.add(label)
            produced += 1
            yield Candidate(structure=struct, meta={"generator": "regular_graph", "n": n, "degree": degree})
            return

        remaining = remaining_possible(idx)
        for v in range(n):
            if degrees[v] > degree or degrees[v] + remaining[v] < degree:
                return

        u, v = pairs[idx]
        # branch: include edge
        if degrees[u] < degree and degrees[v] < degree:
            edges.append((u, v))
            degrees[u] += 1
            degrees[v] += 1
            yield from recurse(idx + 1)
            edges.pop()
            degrees[u] -= 1
            degrees[v] -= 1
        # branch: skip edge
        yield from recurse(idx + 1)

    yield from recurse(0)


def random_regular_graphs(
    n: int,
    degree: int,
    count: int,
    seed: int = 0,
    max_tries: int = 200,
    dedup: bool = False,
) -> Iterator[Candidate]:
    if n * degree % 2 != 0:
        return
    rng = random.Random(seed)
    seen: Set[bytes] = set()
    attempts = 0
    produced = 0
    while produced < count and attempts < max_tries:
        attempts += 1
        stubs = [i for i in range(n) for _ in range(degree)]
        rng.shuffle(stubs)
        edges = set()
        valid = True
        for i in range(0, len(stubs), 2):
            u = stubs[i]
            v = stubs[i + 1]
            if u == v:
                valid = False
                break
            a, b = (u, v) if u < v else (v, u)
            if (a, b) in edges:
                valid = False
                break
            edges.add((a, b))
        if not valid:
            continue
        rel_edges = []
        for u, v in edges:
            rel_edges.append((u, v))
            rel_edges.append((v, u))
        rel = Relation(name="edge", arity=2, tuples=rel_edges)
        struct = RelationalStructure(n=n, relations=[rel])
        if dedup:
            compiled = compile_to_colored_graph(struct)
            label = canonical_label(compiled.graph, max_nodes=200).canonical_label
            if label in seen:
                continue
            seen.add(label)
        produced += 1
        yield Candidate(
            structure=struct,
            meta={
                "generator": "random_regular_graph",
                "n": n,
                "degree": degree,
                "seed": seed,
                "attempt": attempts,
            },
        )


def strongly_regular_graphs(
    n: int,
    degree: int,
    lambda_: int,
    mu: int,
    limit: Optional[int] = None,
    dedup: bool = True,
) -> Iterator[Candidate]:
    if n <= 0 or degree >= n:
        return
    if degree * (degree - lambda_ - 1) != (n - degree - 1) * mu:
        return
    pairs = _pairs(n)
    adjacency: List[List[Optional[int]]] = [[None for _ in range(n)] for _ in range(n)]
    degrees = [0] * n
    remaining = [n - 1] * n
    produced = 0
    seen: Set[bytes] = set()

    def get_edge(i: int, j: int) -> Optional[int]:
        return adjacency[i][j] if i < j else adjacency[j][i]

    def set_edge(i: int, j: int, val: int | None) -> None:
        if i < j:
            adjacency[i][j] = val
        else:
            adjacency[j][i] = val

    def check_common_bounds() -> bool:
        for i in range(n):
            for j in range(i + 1, n):
                cn = 0
                cn_max = 0
                for w in range(n):
                    if w == i or w == j:
                        continue
                    a = get_edge(i, w)
                    b = get_edge(j, w)
                    if a == 1 and b == 1:
                        cn += 1
                    if a != 0 and b != 0:
                        cn_max += 1
                edge = get_edge(i, j)
                if edge == 1:
                    if cn > lambda_ or cn_max < lambda_:
                        return False
                elif edge == 0:
                    if cn > mu or cn_max < mu:
                        return False
                else:
                    if not ((cn <= lambda_ <= cn_max) or (cn <= mu <= cn_max)):
                        return False
        return True

    def recurse(idx: int) -> Iterator[Candidate]:
        nonlocal produced
        if limit is not None and produced >= limit:
            return
        if idx == len(pairs):
            if any(d != degree for d in degrees):
                return
            if not check_common_bounds():
                return
            rel_edges = []
            for u in range(n):
                for v in range(u + 1, n):
                    if get_edge(u, v) == 1:
                        rel_edges.append((u, v))
                        rel_edges.append((v, u))
            rel = Relation(name="edge", arity=2, tuples=rel_edges)
            struct = RelationalStructure(n=n, relations=[rel])
            if dedup:
                compiled = compile_to_colored_graph(struct)
                label = canonical_label(compiled.graph, max_nodes=200).canonical_label
                if label in seen:
                    return
                seen.add(label)
            produced += 1
            yield Candidate(
                structure=struct,
                meta={
                    "generator": "strongly_regular_graph",
                    "n": n,
                    "degree": degree,
                    "lambda": lambda_,
                    "mu": mu,
                },
            )
            return

        u, v = pairs[idx]
        remaining[u] -= 1
        remaining[v] -= 1
        for val in (1, 0):
            if val == 1 and (degrees[u] >= degree or degrees[v] >= degree):
                continue
            set_edge(u, v, val)
            if val == 1:
                degrees[u] += 1
                degrees[v] += 1
            feasible = True
            if degrees[u] > degree or degrees[v] > degree:
                feasible = False
            if degrees[u] + remaining[u] < degree or degrees[v] + remaining[v] < degree:
                feasible = False
            if feasible and check_common_bounds():
                yield from recurse(idx + 1)
            if val == 1:
                degrees[u] -= 1
                degrees[v] -= 1
            set_edge(u, v, None)
        remaining[u] += 1
        remaining[v] += 1

    yield from recurse(0)
