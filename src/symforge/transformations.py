from __future__ import annotations

import itertools
import random
from dataclasses import dataclass
from typing import Iterable, List, Optional, Sequence, Tuple

from symforge.relational import Relation, RelationalStructure


@dataclass
class Code:
    length: int
    basis: List[int]

    def codewords(self, max_words: int = 4096) -> List[int]:
        if len(self.basis) > 20:
            max_words = min(max_words, 2048)
        words = [0]
        for vec in self.basis:
            words += [w ^ vec for w in list(words)]
            if len(words) >= max_words:
                break
        return words


def incidence_matrix(structure: RelationalStructure) -> List[int]:
    if not structure.relations:
        return []
    rel = structure.relations[0]
    rows = []
    for block in rel.tuples:
        row = 0
        for v in block:
            row |= 1 << v
        rows.append(row)
    return rows


def row_echelon(rows: Iterable[int], n: int) -> Tuple[List[int], List[int]]:
    basis = []
    pivots = []
    rows = list(set(rows))
    for col in range(n - 1, -1, -1):
        mask = 1 << col
        pivot = None
        for i, row in enumerate(rows):
            if row & mask:
                pivot = row
                rows.pop(i)
                break
        if pivot is None:
            continue
        for i, row in enumerate(rows):
            if row & mask:
                rows[i] ^= pivot
        basis.append(pivot)
        pivots.append(col)
    return basis, pivots


def code_from_rows(rows: Iterable[int], n: int) -> Code:
    basis, _ = row_echelon(rows, n)
    return Code(length=n, basis=basis)


def dual_code(code: Code) -> Code:
    basis, pivots = row_echelon(code.basis, code.length)
    pivot_set = set(pivots)
    free_cols = [c for c in range(code.length) if c not in pivot_set]
    dual_basis = []
    for free in free_cols:
        vec = 1 << free
        for row, pivot_col in zip(basis, pivots):
            if row & (1 << free):
                vec |= 1 << pivot_col
        dual_basis.append(vec)
    return Code(length=code.length, basis=dual_basis)


def construction_a_min_vectors(
    code: Code,
    radius: int = 2,
    shift: Optional[Sequence[float]] = None,
) -> List[Tuple[float, ...]]:
    n = code.length
    shift_vec = shift or [0.0] * n
    words = code.codewords(max_words=2048)
    vectors = []
    for word in words:
        base = [(1.0 if (word >> i) & 1 else 0.0) + shift_vec[i] for i in range(n)]
        for z in itertools.product([-1, 0, 1], repeat=n):
            vec = [base[i] + 2 * z[i] for i in range(n)]
            norm2 = sum(x * x for x in vec)
            if norm2 <= radius * radius:
                vectors.append(tuple(vec))
    if not vectors:
        return []
    min_norm = min(sum(x * x for x in v) for v in vectors)
    return [v for v in vectors if abs(sum(x * x for x in v) - min_norm) < 1e-9]


def shift_search(code: Code, trials: int = 32, seed: int = 0) -> List[float]:
    rng = random.Random(seed)
    n = code.length
    best_shift = [0.0] * n
    best_min = 0.0
    for _ in range(trials):
        shift = [0.5 if rng.random() < 0.5 else 0.0 for _ in range(n)]
        words = code.codewords(max_words=256)
        norms = []
        for word in words:
            vec = [(1.0 if (word >> i) & 1 else 0.0) + shift[i] for i in range(n)]
            norms.append(sum(x * x for x in vec))
        min_norm = min(norms) if norms else 0.0
        if min_norm > best_min:
            best_min = min_norm
            best_shift = shift
    return best_shift


def minimal_vector_graph(vectors: List[Tuple[float, ...]], dot_threshold: float = 0.0) -> RelationalStructure:
    n = len(vectors)
    edges = []
    for i in range(n):
        for j in range(i + 1, n):
            dot = sum(a * b for a, b in zip(vectors[i], vectors[j]))
            if abs(dot - dot_threshold) < 1e-9:
                edges.append((i, j))
                edges.append((j, i))
    rel = Relation(name="orthogonal", arity=2, tuples=edges)
    return RelationalStructure(n=n, relations=[rel])
