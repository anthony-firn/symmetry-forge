from __future__ import annotations

import argparse

from experiments.common import automorphism_order
from symforge.generators.designs import steiner_system
from symforge.logging import ResultLogger, results_path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=1)
    args = parser.parse_args(argv)

    logger = ResultLogger(results_path("e1_fano"))
    count = 0
    for cand in steiner_system(7, 3, t=2, lam=1, limit=args.limit):
        order = automorphism_order(cand.structure)
        logger.log(
            {
                "experiment": "E1",
                "object": "steiner_system",
                "params": {"v": 7, "k": 3, "t": 2, "lambda": 1},
                "aut_order": order,
                "blocks": len(cand.structure.relations[0].tuples),
            }
        )
        count += 1
    logger.close()
    print(f"E1 completed: {count} designs")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
