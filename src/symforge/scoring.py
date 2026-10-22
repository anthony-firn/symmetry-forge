from __future__ import annotations

import gzip
import math
from dataclasses import dataclass
from typing import Dict, Tuple

from symforge.automorphism import canonical_label
from symforge.group import Group
from symforge.novelty import NoveltyRegistry, factor_signatures
from symforge.relational import RelationalStructure, compile_to_colored_graph


@dataclass
class ScoreBreakdown:
    compress_len: int
    log_aut: float
    aut_order: int
    aut_order_exact: bool
    baseline_log_aut: float
    outlier_score: float
    novelty_bonus: float
    total_score: float


class BaselineEstimator:
    def __init__(self, samples: int = 5) -> None:
        self.samples = samples
        self.cache: Dict[Tuple[int, Tuple[Tuple[int, int], ...]], float] = {}

    def baseline_log_aut(self, signature: Tuple[int, Tuple[Tuple[int, int], ...]], sampler) -> float:
        if signature in self.cache:
            return self.cache[signature]
        values = []
        for _ in range(self.samples):
            structure = sampler()
            compiled = compile_to_colored_graph(structure)
            aut = canonical_label(compiled.graph)
            node_to_elem = {node: idx for idx, node in enumerate(compiled.element_nodes)}
            element_perms = []
            for perm in aut.automorphisms:
                mapped = [0] * structure.n
                for idx, node in enumerate(compiled.element_nodes):
                    mapped[idx] = node_to_elem[perm[node]]
                element_perms.append(tuple(mapped))
            group = Group(element_perms)
            order = group.order()
            values.append(math.log(max(order.value, 1)))
        baseline = sum(values) / len(values) if values else 0.0
        self.cache[signature] = baseline
        return baseline


def compress_len(data: bytes) -> int:
    return len(gzip.compress(data))


def structure_signature(structure: RelationalStructure) -> Tuple[int, Tuple[Tuple[int, int], ...]]:
    rel_sig = tuple(sorted((rel.arity, len(rel.tuples)) for rel in structure.relations))
    return structure.n, rel_sig


def score_structure(
    structure: RelationalStructure,
    baseline_estimator: BaselineEstimator,
    novelty_registry: NoveltyRegistry,
    baseline_sampler,
) -> ScoreBreakdown:
    compiled = compile_to_colored_graph(structure)
    aut = canonical_label(compiled.graph)
    node_to_elem = {node: idx for idx, node in enumerate(compiled.element_nodes)}
    element_perms = []
    for perm in aut.automorphisms:
        mapped = [0] * structure.n
        for idx, node in enumerate(compiled.element_nodes):
            mapped[idx] = node_to_elem[perm[node]]
        element_perms.append(tuple(mapped))
    group = Group(element_perms)
    order = group.order()
    label_bytes = aut.canonical_label
    comp_len = compress_len(label_bytes)
    log_aut = math.log(max(order.value, 1))
    signature = structure_signature(structure)
    baseline = baseline_estimator.baseline_log_aut(signature, baseline_sampler)
    outlier = log_aut - baseline
    signatures = factor_signatures(group, order)
    novelty_bonus, _new = novelty_registry.assess(signatures)
    total = outlier + novelty_bonus - 0.01 * comp_len
    return ScoreBreakdown(
        compress_len=comp_len,
        log_aut=log_aut,
        aut_order=order.value,
        aut_order_exact=order.exact,
        baseline_log_aut=baseline,
        outlier_score=outlier,
        novelty_bonus=novelty_bonus,
        total_score=total,
    )
