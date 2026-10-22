from __future__ import annotations

import argparse

from symforge.generators.graphs import random_regular_graphs, regular_graphs
from symforge.logging import ResultLogger, results_path
from symforge.search import SearchConfig, SearchEngine


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--n", type=int, default=6)
    parser.add_argument("--degree", type=int, default=3)
    parser.add_argument("--budget", type=int, default=10)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--random", action="store_true")
    parser.add_argument("--max-tries", type=int, default=500)
    args = parser.parse_args(argv)

    logger = ResultLogger(results_path("e3_outlier"))
    engine = SearchEngine(
        SearchConfig(seed=args.seed, budget=args.budget, top_k=5, baseline_samples=2),
        logger=logger,
    )
    if args.random:
        candidates = random_regular_graphs(
            args.n,
            args.degree,
            count=args.budget,
            seed=args.seed,
            max_tries=args.max_tries,
            dedup=False,
        )
    else:
        candidates = regular_graphs(args.n, args.degree, limit=args.budget, dedup=True)
    results = engine.run(candidates)
    for rank, result in enumerate(results, start=1):
        logger.log(
            {
                "experiment": "E3",
                "rank": rank,
                "meta": result.candidate.meta,
                "score": result.score.total_score,
                "aut_order": result.score.aut_order,
                "outlier": result.score.outlier_score,
            }
        )
    logger.close()
    print(f"E3 completed: {len(results)} top candidates")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
