from __future__ import annotations

from itertools import combinations
from typing import Dict, Iterator, List, Optional, Set

from symforge.relational import Relation, RelationalStructure
from symforge.search import Candidate


def steiner_system(
    v: int,
    k: int,
    t: int = 2,
    lam: int = 1,
    limit: Optional[int] = None,
) -> Iterator[Candidate]:
    if lam != 1:
        raise ValueError("only lambda=1 is supported in this generator")

    points = list(range(v))
    blocks = list(combinations(points, k))
    required = list(combinations(points, t))
    req_index = {req: idx for idx, req in enumerate(required)}

    row_cols: Dict[int, List[int]] = {}
    col_rows: Dict[int, Set[int]] = {i: set() for i in range(len(required))}

    for row_id, block in enumerate(blocks):
        cols = [req_index[req] for req in combinations(block, t)]
        row_cols[row_id] = cols
        for c in cols:
            col_rows[c].add(row_id)

    columns = set(col_rows.keys())
    solution: List[int] = []
    produced = 0

    def search(col_rows_map: Dict[int, Set[int]], columns_left: Set[int]) -> Iterator[List[int]]:
        nonlocal produced
        if limit is not None and produced >= limit:
            return
        if not columns_left:
            produced += 1
            yield list(solution)
            return
        col = min(columns_left, key=lambda c: len(col_rows_map[c]))
        for row in list(col_rows_map[col]):
            if limit is not None and produced >= limit:
                return
            solution.append(row)
            covered_cols = row_cols[row]
            removed_columns = []
            removed_rows: Dict[int, Set[int]] = {}
            new_columns_left = set(columns_left)
            for c in covered_cols:
                if c not in new_columns_left:
                    continue
                new_columns_left.remove(c)
                removed_columns.append(c)
                removed_rows[c] = col_rows_map[c]
            new_col_rows = {c: set(rset) for c, rset in col_rows_map.items() if c in new_columns_left}
            for c in removed_columns:
                for r in removed_rows[c]:
                    for c2 in row_cols[r]:
                        if c2 in new_col_rows:
                            new_col_rows[c2].discard(r)
            if any(len(rows) == 0 for rows in new_col_rows.values()):
                solution.pop()
                continue
            yield from search(new_col_rows, new_columns_left)
            solution.pop()

    for sol in search(col_rows, columns):
        block_list = [blocks[i] for i in sol]
        rel = Relation(
            name="block",
            arity=k,
            tuples=[tuple(block) for block in block_list],
            position_colors=[0] * k,
        )
        struct = RelationalStructure(n=v, relations=[rel])
        yield Candidate(
            structure=struct,
            meta={"generator": "steiner_system", "v": v, "k": k, "t": t, "lambda": lam},
        )


def steiner_system_sat(
    v: int,
    k: int,
    t: int = 2,
    lam: int = 1,
    limit: Optional[int] = None,
) -> Iterator[Candidate]:
    if lam != 1:
        raise ValueError("only lambda=1 is supported in this generator")
    try:
        from pysat.formula import CNF
        from pysat.solvers import Solver
    except Exception as exc:  # pragma: no cover - optional dependency
        raise ImportError("PySAT not available") from exc

    points = list(range(v))
    blocks = list(combinations(points, k))
    required = list(combinations(points, t))

    block_vars = {block: i + 1 for i, block in enumerate(blocks)}
    cnf = CNF()

    for req in required:
        covering = [block_vars[block] for block in blocks if set(req).issubset(block)]
        cnf.append(covering)
        for i in range(len(covering)):
            for j in range(i + 1, len(covering)):
                cnf.append([-covering[i], -covering[j]])

    produced = 0
    with Solver(bootstrap_with=cnf) as solver:
        while solver.solve():
            model = solver.get_model()
            chosen = [block for block in blocks if block_vars[block] in model]
            rel = Relation(
                name="block",
                arity=k,
                tuples=[tuple(block) for block in chosen],
                position_colors=[0] * k,
            )
            struct = RelationalStructure(n=v, relations=[rel])
            yield Candidate(
                structure=struct,
                meta={"generator": "steiner_system_sat", "v": v, "k": k, "t": t, "lambda": lam},
            )
            produced += 1
            if limit is not None and produced >= limit:
                break
            # block this solution
            solver.add_clause([-block_vars[block] for block in chosen])
