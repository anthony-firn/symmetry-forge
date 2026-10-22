from __future__ import annotations

import argparse

from experiments.common import automorphism_order
from symforge.generators.designs import steiner_system
from symforge.logging import ResultLogger, results_path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=1)
    args = parser.parse_args(argv)

    logger = ResultLogger(results_path("e2_design"))
    count = 0
    for cand in steiner_system(8, 4, t=3, lam=1, limit=args.limit):
        order = automorphism_order(cand.structure)
        logger.log(
            {
                "experiment": "E2",
                "object": "steiner_system",
                "params": {"v": 8, "k": 4, "t": 3, "lambda": 1},
                "aut_order": order,
                "blocks": len(cand.structure.relations[0].tuples),
            }
        )
        count += 1
    logger.close()
    print(f"E2 completed: {count} designs")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
