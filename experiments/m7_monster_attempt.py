from __future__ import annotations

import argparse
from typing import Iterable, List, Tuple

from experiments.common import automorphism_group
from symforge.generators.designs import steiner_system, steiner_system_sat
from symforge.generators.graphs import random_regular_graphs, regular_graphs
from symforge.logging import ResultLogger, results_path
from symforge.monster import algebra_from_symmetry, fingerprint, glue_orbit_actions
from symforge.transformations import (
    code_from_rows,
    construction_a_min_vectors,
    dual_code,
    incidence_matrix,
    minimal_vector_graph,
    shift_search,
)


def parse_configs(text: str) -> List[Tuple[int, int]]:
    configs = []
    for item in text.split(","):
        item = item.strip()
        if not item:
            continue
        parts = item.split(":")
        if len(parts) != 2:
            raise ValueError(f"invalid config entry: {item}")
        n, degree = (int(p) for p in parts)
        configs.append((n, degree))
    return configs


def default_configs() -> List[Tuple[int, int]]:
    return [(6, 3), (7, 2)]


def design_configs() -> List[Tuple[int, int, int]]:
    return [(7, 3, 2), (8, 4, 3)]


def parse_design_configs(text: str) -> List[Tuple[int, int, int]]:
    configs = []
    for item in text.split(","):
        item = item.strip()
        if not item:
            continue
        parts = item.split(":")
        if len(parts) != 3:
            raise ValueError(f"invalid design entry: {item}")
        v, k, t = (int(p) for p in parts)
        configs.append((v, k, t))
    return configs


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--budget", type=int, default=5)
    parser.add_argument("--configs", default="", help="comma list like 6:3,7:2")
    parser.add_argument("--no-dedup", action="store_true")
    parser.add_argument("--include-designs", action="store_true")
    parser.add_argument("--design-configs", default="", help="comma list like 7:3:2,8:4:3")
    parser.add_argument("--sat-designs", action="store_true")
    parser.add_argument("--random", action="store_true", help="use random regular graphs")
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--max-tries", type=int, default=200)
    args = parser.parse_args(argv)

    logger = ResultLogger(results_path("m7_monster_attempt"))
    configs = parse_configs(args.configs) if args.configs else default_configs()
    groups = []

    for n, degree in configs:
        best = None
        if args.random:
            candidates = random_regular_graphs(
                n,
                degree,
                count=args.budget,
                seed=args.seed + n * 100 + degree,
                max_tries=args.max_tries,
                dedup=not args.no_dedup,
            )
        else:
            candidates = regular_graphs(n, degree, limit=args.budget, dedup=not args.no_dedup)
        for cand in candidates:
            group = automorphism_group(cand.structure)
            order = group.order().value
            if best is None or order > best[0]:
                best = (order, group)
        if best:
            groups.append((n, degree, best[1]))
            fp = fingerprint(best[1])
            logger.log(
                {
                    "experiment": "M7",
                    "phase": "fingerprint",
                    "n": n,
                    "degree": degree,
                    "order": fp.order,
                    "order_exact": fp.order_exact,
                    "orbit_sizes": fp.orbit_sizes,
                    "involutions": fp.involutions,
                    "primitive": fp.primitive,
                }
            )

    if args.include_designs:
        d_configs = parse_design_configs(args.design_configs) if args.design_configs else design_configs()
        for v, k, t in d_configs:
            try:
                if args.sat_designs:
                    gen = steiner_system_sat(v, k, t=t, lam=1, limit=1)
                else:
                    gen = steiner_system(v, k, t=t, lam=1, limit=1)
            except ImportError as exc:
                logger.log(
                    {
                        "experiment": "M7",
                        "phase": "design_error",
                        "v": v,
                        "k": k,
                        "t": t,
                        "error": str(exc),
                    }
                )
                continue
            try:
                for cand in gen:
                    group = automorphism_group(cand.structure)
                    fp = fingerprint(group)
                    logger.log(
                        {
                            "experiment": "M7",
                            "phase": "design",
                            "v": v,
                            "k": k,
                            "t": t,
                            "order": fp.order,
                            "order_exact": fp.order_exact,
                            "orbit_sizes": fp.orbit_sizes,
                            "involutions": fp.involutions,
                            "primitive": fp.primitive,
                        }
                    )
                    rows = incidence_matrix(cand.structure)
                    code = code_from_rows(rows, v)
                    dual = dual_code(code)
                    shift = shift_search(dual, trials=16, seed=0)
                    vectors = construction_a_min_vectors(dual, radius=2, shift=shift)
                    graph = minimal_vector_graph(vectors, dot_threshold=0.0)
                    graph_group = automorphism_group(graph)
                    fp = fingerprint(graph_group)
                    logger.log(
                        {
                            "experiment": "M7",
                            "phase": "design_lattice",
                            "v": v,
                            "k": k,
                            "t": t,
                            "vectors": len(vectors),
                            "order": fp.order,
                            "order_exact": fp.order_exact,
                            "orbit_sizes": fp.orbit_sizes,
                            "involutions": fp.involutions,
                            "primitive": fp.primitive,
                        }
                    )
            except ImportError as exc:
                logger.log(
                    {
                        "experiment": "M7",
                        "phase": "design_error",
                        "v": v,
                        "k": k,
                        "t": t,
                        "error": str(exc),
                    }
                )

    # attempt gluing within same degree if possible
    if len(groups) >= 2:
        for i in range(len(groups) - 1):
            n_a, d_a, g_a = groups[i]
            n_b, d_b, g_b = groups[i + 1]
            if n_a != n_b:
                continue
            glued = glue_orbit_actions(g_a, g_b)
            if glued is None:
                continue
            fp = fingerprint(glued)
            logger.log(
                {
                    "experiment": "M7",
                    "phase": "glue",
                    "n": n_a,
                    "degree": d_a,
                    "order": fp.order,
                    "orbit_sizes": fp.orbit_sizes,
                }
            )

    # attempt algebra from symmetry for smallest group
    if groups:
        n, degree, group = min(groups, key=lambda x: x[0])
        try:
            structure = algebra_from_symmetry(group, seed=0)
            logger.log(
                {
                    "experiment": "M7",
                    "phase": "algebra",
                    "n": n,
                    "degree": degree,
                    "tuples": len(structure.relations[0].tuples),
                }
            )
        except ValueError as exc:
            logger.log(
                {
                    "experiment": "M7",
                    "phase": "algebra",
                    "n": n,
                    "degree": degree,
                    "error": str(exc),
                }
            )

    logger.close()
    print("M7 attempt completed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
