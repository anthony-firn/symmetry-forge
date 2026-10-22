from __future__ import annotations

from typing import Iterator, List, Optional

from symforge.automorphism import canonical_label
from symforge.relational import Relation, RelationalStructure, compile_to_colored_graph
from symforge.search import Candidate


def commutative_magma_tables(
    n: int,
    limit: Optional[int] = None,
    idempotent: bool = True,
    dedup: bool = True,
) -> Iterator[Candidate]:
    table: List[List[int]] = [[-1 for _ in range(n)] for _ in range(n)]
    seen = set()
    produced = 0

    def set_value(i: int, j: int, val: int) -> None:
        table[i][j] = val
        table[j][i] = val

    def unset_value(i: int, j: int) -> None:
        table[i][j] = -1
        table[j][i] = -1

    pairs = [(i, j) for i in range(n) for j in range(i, n)]

    def recurse(idx: int) -> Iterator[Candidate]:
        nonlocal produced
        if limit is not None and produced >= limit:
            return
        if idx == len(pairs):
            tuples = []
            for i in range(n):
                for j in range(n):
                    tuples.append((i, j, table[i][j]))
            rel = Relation(name="mul", arity=3, tuples=tuples)
            struct = RelationalStructure(n=n, relations=[rel])
            if dedup:
                compiled = compile_to_colored_graph(struct)
                label = canonical_label(compiled.graph, max_nodes=200).canonical_label
                if label in seen:
                    return
                seen.add(label)
            produced += 1
            yield Candidate(structure=struct, meta={"generator": "commutative_magma", "n": n})
            return

        i, j = pairs[idx]
        if idempotent and i == j:
            set_value(i, j, i)
            yield from recurse(idx + 1)
            unset_value(i, j)
            return
        for val in range(n):
            set_value(i, j, val)
            yield from recurse(idx + 1)
            unset_value(i, j)

    yield from recurse(0)
