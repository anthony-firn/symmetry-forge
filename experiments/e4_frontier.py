from __future__ import annotations

import argparse
import random
from dataclasses import dataclass
from typing import Iterator, Optional

from symforge.generators.algebra import commutative_magma_tables
from symforge.generators.designs import steiner_system, steiner_system_sat
from symforge.generators.graphs import (
    random_regular_graphs,
    strongly_regular_graphs,
)
from symforge.logging import ResultLogger, results_path
from symforge.novelty import NoveltyRegistry
from symforge.relational import Relation, RelationalStructure
from symforge.scoring import BaselineEstimator, ScoreBreakdown, score_structure


@dataclass
class ConstraintSpec:
    kind: str
    n: int
    degree: Optional[int] = None
    lambda_: Optional[int] = None
    mu: Optional[int] = None
    k: Optional[int] = None
    t: Optional[int] = None


def baseline_sampler(structure: RelationalStructure, rng: random.Random):
    def sample() -> RelationalStructure:
        relations = []
        for rel in structure.relations:
            tuples = set()
            while len(tuples) < len(rel.tuples):
                tup = tuple(rng.randrange(structure.n) for _ in range(rel.arity))
                tuples.add(tup)
            tuple_list = list(tuples)
            relations.append(
                Relation(
                    name=rel.name,
                    arity=rel.arity,
                    tuples=tuple_list,
                    tuple_colors=rel.tuple_colors,
                    rel_color=rel.rel_color,
                )
            )
        return RelationalStructure(
            n=structure.n,
            relations=relations,
            element_colors=structure.element_colors,
        )

    return sample


def sample_srg_spec(rng: random.Random, n: int) -> Optional[ConstraintSpec]:
    if n < 4:
        return None
    for _ in range(100):
        degree = rng.randint(2, n - 2)
        lambda_ = rng.randint(0, max(0, degree - 1))
        denom = n - degree - 1
        if denom <= 0:
            continue
        numer = degree * (degree - lambda_ - 1)
        if numer % denom != 0:
            continue
        mu = numer // denom
        if mu < 0 or mu >= n:
            continue
        return ConstraintSpec(kind="srg", n=n, degree=degree, lambda_=lambda_, mu=mu)
    return None


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--budget", type=int, default=30)
    parser.add_argument("--per-spec", type=int, default=3)
    parser.add_argument("--min-n", type=int, default=6)
    parser.add_argument("--max-n", type=int, default=12)
    parser.add_argument("--srg-max-n", type=int, default=8)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--include-algebra", action="store_true")
    parser.add_argument("--use-sat", action="store_true")
    parser.add_argument("--skip-srg", action="store_true")
    parser.add_argument("--skip-design", action="store_true")
    args = parser.parse_args(argv)

    rng = random.Random(args.seed)
    logger = ResultLogger(results_path("e4_frontier"))
    baseline = BaselineEstimator(samples=2)
    novelty = NoveltyRegistry()

    best: list[tuple[float, ScoreBreakdown, ConstraintSpec]] = []

    for step in range(args.budget):
        families = ["regular"]
        if not args.skip_srg:
            families.append("srg")
        if not args.skip_design:
            families.append("design")
        if args.include_algebra:
            families.append("algebra")
        family = rng.choice(families)
        n = rng.randint(args.min_n, args.max_n)
        spec: Optional[ConstraintSpec] = None
        candidates: Iterator

        if family == "regular":
            degree = rng.randint(2, min(n - 1, max(2, n // 2)))
            spec = ConstraintSpec(kind="regular", n=n, degree=degree)
            candidates = random_regular_graphs(
                n,
                degree,
                count=args.per_spec,
                seed=args.seed + step * 100 + degree,
                max_tries=500,
                dedup=False,
            )
        elif family == "srg":
            if n > args.srg_max_n:
                continue
            spec = sample_srg_spec(rng, n)
            if spec is None:
                continue
            candidates = strongly_regular_graphs(
                spec.n,
                spec.degree or 0,
                spec.lambda_ or 0,
                spec.mu or 0,
                limit=args.per_spec,
                dedup=True,
            )
        elif family == "design":
            k = rng.randint(3, min(4, n - 1))
            spec = ConstraintSpec(kind="design", n=n, k=k, t=2)
            if args.use_sat:
                try:
                    candidates = steiner_system_sat(n, k, t=2, lam=1, limit=args.per_spec)
                except ImportError:
                    continue
            else:
                candidates = steiner_system(n, k, t=2, lam=1, limit=args.per_spec)
        else:
            spec = ConstraintSpec(kind="algebra", n=n)
            candidates = commutative_magma_tables(n=min(4, n), limit=args.per_spec)

        for cand in candidates:
            sampler = baseline_sampler(cand.structure, rng)
            score = score_structure(cand.structure, baseline, novelty, sampler)
            logger.log(
                {
                    "experiment": "E4",
                    "step": step,
                    "family": family,
                    "spec": spec.__dict__ if spec else {},
                    "score": {
                        "total": score.total_score,
                        "outlier": score.outlier_score,
                        "novelty": score.novelty_bonus,
                        "aut_order": score.aut_order,
                    },
                }
            )
            best.append((score.total_score, score, spec))
            best.sort(key=lambda x: x[0], reverse=True)
            best = best[:10]

    for rank, (_total, score, spec) in enumerate(best, start=1):
        logger.log(
            {
                "experiment": "E4",
                "phase": "top",
                "rank": rank,
                "spec": spec.__dict__ if spec else {},
                "score": {
                    "total": score.total_score,
                    "outlier": score.outlier_score,
                    "novelty": score.novelty_bonus,
                    "aut_order": score.aut_order,
                },
            }
        )

    logger.close()
    print("E4 frontier completed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
