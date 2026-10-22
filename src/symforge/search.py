from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Dict, Iterable, List, Optional

from symforge.logging import ResultLogger
from symforge.novelty import NoveltyRegistry
from symforge.relational import Relation, RelationalStructure
from symforge.scoring import BaselineEstimator, ScoreBreakdown, score_structure


@dataclass
class Candidate:
    structure: RelationalStructure
    meta: Dict[str, object] = field(default_factory=dict)


@dataclass
class SearchConfig:
    seed: int = 0
    budget: int = 100
    top_k: int = 5
    baseline_samples: int = 3


@dataclass
class SearchResult:
    candidate: Candidate
    score: ScoreBreakdown


class SearchEngine:
    def __init__(self, config: SearchConfig, logger: Optional[ResultLogger] = None) -> None:
        self.config = config
        self.rng = random.Random(config.seed)
        self.logger = logger
        self.baseline = BaselineEstimator(samples=config.baseline_samples)
        self.novelty = NoveltyRegistry()
        self.best: List[SearchResult] = []

    def run(self, candidates: Iterable[Candidate]) -> List[SearchResult]:
        for idx, cand in enumerate(candidates):
            if idx >= self.config.budget:
                break
            sampler = self._baseline_sampler(cand.structure)
            score = score_structure(cand.structure, self.baseline, self.novelty, sampler)
            result = SearchResult(candidate=cand, score=score)
            self._maybe_add(result)
            if self.logger:
                record = {
                    "index": idx,
                    "meta": cand.meta,
                    "n": cand.structure.n,
                    "relations": [
                        {
                            "arity": rel.arity,
                            "tuples": len(rel.tuples),
                        }
                        for rel in cand.structure.relations
                    ],
                    "score": {
                        "compress_len": score.compress_len,
                        "log_aut": score.log_aut,
                        "aut_order": score.aut_order,
                        "aut_order_exact": score.aut_order_exact,
                        "baseline_log_aut": score.baseline_log_aut,
                        "outlier_score": score.outlier_score,
                        "novelty_bonus": score.novelty_bonus,
                        "total_score": score.total_score,
                    },
                }
                self.logger.log(record)
        return self.best

    def _maybe_add(self, result: SearchResult) -> None:
        self.best.append(result)
        self.best.sort(key=lambda r: r.score.total_score, reverse=True)
        self.best = self.best[: self.config.top_k]

    def _baseline_sampler(self, structure: RelationalStructure):
        def sample() -> RelationalStructure:
            relations: List[Relation] = []
            for rel in structure.relations:
                tuples = set()
                while len(tuples) < len(rel.tuples):
                    tup = tuple(self.rng.randrange(structure.n) for _ in range(rel.arity))
                    tuples.add(tup)
                tuple_list = list(tuples)
                tuple_colors = None
                if rel.tuple_colors:
                    colors = list(rel.tuple_colors)
                    self.rng.shuffle(colors)
                    tuple_colors = colors[: len(tuple_list)]
                relations.append(
                    Relation(
                        name=rel.name,
                        arity=rel.arity,
                        tuples=tuple_list,
                        tuple_colors=tuple_colors,
                        rel_color=rel.rel_color,
                    )
                )
            return RelationalStructure(
                n=structure.n,
                relations=relations,
                element_colors=structure.element_colors,
            )

        return sample
