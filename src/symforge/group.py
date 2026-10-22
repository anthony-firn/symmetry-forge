from __future__ import annotations

from dataclasses import dataclass
from math import prod
from typing import Dict, Iterable, List, Optional, Sequence, Set, Tuple


@dataclass(frozen=True)
class Permutation:
    mapping: Tuple[int, ...]

    @staticmethod
    def identity(n: int) -> "Permutation":
        return Permutation(tuple(range(n)))

    def compose(self, other: "Permutation") -> "Permutation":
        # self after other
        return Permutation(tuple(self.mapping[i] for i in other.mapping))

    def invert(self) -> "Permutation":
        inv = [0] * len(self.mapping)
        for i, v in enumerate(self.mapping):
            inv[v] = i
        return Permutation(tuple(inv))

    def apply(self, point: int) -> int:
        return self.mapping[point]

    def is_identity(self) -> bool:
        return all(i == v for i, v in enumerate(self.mapping))


@dataclass
class GroupOrder:
    value: int
    exact: bool
    method: str


class Group:
    def __init__(self, generators: Iterable[Sequence[int]]) -> None:
        gens = [Permutation(tuple(g)) for g in generators]
        self.generators = gens
        self.degree = len(gens[0].mapping) if gens else 0

    def closure(self, max_size: int = 200_000) -> Optional[List[Permutation]]:
        if not self.generators:
            return [Permutation.identity(self.degree)]
        seen: Set[Tuple[int, ...]] = set()
        queue: List[Permutation] = []
        ident = Permutation.identity(self.degree)
        seen.add(ident.mapping)
        queue.append(ident)
        gens = self.generators
        while queue:
            g = queue.pop()
            for h in gens:
                gh = g.compose(h)
                if gh.mapping not in seen:
                    seen.add(gh.mapping)
                    if len(seen) > max_size:
                        return None
                    queue.append(gh)
        return [Permutation(m) for m in seen]

    def order(self, max_size: int = 200_000) -> GroupOrder:
        closure = self.closure(max_size=max_size)
        if closure is not None:
            return GroupOrder(value=len(closure), exact=True, method="closure")
        value = schreier_sims_order(self.generators, self.degree)
        return GroupOrder(value=value, exact=True, method="schreier_sims")

    def orbits(self) -> List[List[int]]:
        if self.degree == 0:
            return []
        unvisited = set(range(self.degree))
        orbits = []
        while unvisited:
            start = next(iter(unvisited))
            orbit = _orbit(start, self.generators, self.degree)
            for v in orbit:
                unvisited.discard(v)
            orbits.append(sorted(orbit))
        return orbits


def _orbit(start: int, gens: List[Permutation], n: int) -> Set[int]:
    if not gens:
        return {start}
    seen = {start}
    queue = [start]
    while queue:
        v = queue.pop()
        for g in gens:
            w = g.apply(v)
            if w not in seen:
                seen.add(w)
                queue.append(w)
    return seen


def schreier_tree(base: int, gens: List[Permutation], n: int) -> Tuple[List[int], Dict[int, Permutation]]:
    orbit = [base]
    transv: Dict[int, Permutation] = {base: Permutation.identity(n)}
    queue = [base]
    while queue:
        v = queue.pop()
        g_to_v = transv[v]
        for g in gens:
            w = g.apply(v)
            if w not in transv:
                transv[w] = g.compose(g_to_v)
                orbit.append(w)
                queue.append(w)
    return orbit, transv


def sift(g: Permutation, base: List[int], transversals: List[Dict[int, Permutation]]) -> Permutation:
    h = g
    for level, b in enumerate(base):
        image = h.apply(b)
        transv = transversals[level]
        if image not in transv:
            return h
        u = transv[image]
        h = u.invert().compose(h)
    return h


def schreier_sims_order(gens: List[Permutation], n: int, base: Optional[List[int]] = None) -> int:
    if not gens:
        return 1
    if base is None:
        base = list(range(n))
    strong_gens: List[List[Permutation]] = [list(gens)]
    transversals: List[Dict[int, Permutation]] = []
    orbits: List[List[int]] = []

    for level, b in enumerate(base):
        while True:
            orbit, transv = schreier_tree(b, strong_gens[level], n)
            added = False
            for g in list(strong_gens[level]):
                for beta in orbit:
                    u = transv[beta]
                    beta_g = g.apply(beta)
                    v = transv[beta_g]
                    schreier = u.invert().compose(g).compose(v)
                    if schreier.is_identity():
                        continue
                    residual = sift(schreier, base[:level], transversals)
                    if not residual.is_identity():
                        strong_gens[level].append(residual)
                        added = True
            if not added:
                transversals.append(transv)
                orbits.append(orbit)
                break
        stabilizer_gens = [g for g in strong_gens[level] if g.apply(b) == b]
        strong_gens.append(stabilizer_gens)

    return prod(len(orbit) for orbit in orbits) if orbits else 1
