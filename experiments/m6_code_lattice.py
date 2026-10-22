from __future__ import annotations

import argparse

from experiments.common import automorphism_order
from symforge.generators.designs import steiner_system
from symforge.logging import ResultLogger, results_path
from symforge.transformations import (
    code_from_rows,
    construction_a_min_vectors,
    dual_code,
    incidence_matrix,
    minimal_vector_graph,
    shift_search,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=1)
    args = parser.parse_args(argv)

    logger = ResultLogger(results_path("m6_code_lattice"))
    count = 0
    for cand in steiner_system(7, 3, t=2, lam=1, limit=args.limit):
        rows = incidence_matrix(cand.structure)
        code = code_from_rows(rows, cand.structure.n)
        dual = dual_code(code)
        shift = shift_search(dual, trials=16, seed=0)
        vectors = construction_a_min_vectors(dual, radius=2, shift=shift)
        graph = minimal_vector_graph(vectors, dot_threshold=0.0)
        aut_order = automorphism_order(graph)
        logger.log(
            {
                "experiment": "M6",
                "code_basis": len(code.basis),
                "dual_basis": len(dual.basis),
                "vectors": len(vectors),
                "aut_order": aut_order,
            }
        )
        count += 1
    logger.close()
    print(f"M6 completed: {count} lattices")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
