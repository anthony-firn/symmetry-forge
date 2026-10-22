from __future__ import annotations

import math
import random
from dataclasses import dataclass
from typing import Iterable, List, Optional, Sequence, Set, Tuple

from symforge.group import Group, GroupOrder, Permutation


@dataclass(frozen=True)
class FactorSignature:
    order: int
    sample_orders: Tuple[int, ...]
    simple_flag: str
    primitive_flag: bool


def permutation_order(perm: Permutation) -> int:
    visited = [False] * len(perm.mapping)
    lcms = 1
    for i in range(len(perm.mapping)):
        if visited[i]:
            continue
        length = 0
        j = i
        while not visited[j]:
            visited[j] = True
            j = perm.mapping[j]
            length += 1
        if length > 0:
            lcms = lcm(lcms, length)
    return lcms


def lcm(a: int, b: int) -> int:
    return abs(a * b) // math.gcd(a, b)


def sample_element_orders(elements: Sequence[Permutation], limit: int = 12) -> List[int]:
    if not elements:
        return [1]
    if len(elements) <= limit:
        sample = elements
    else:
        rng = random.Random(0)
        sample = rng.sample(list(elements), limit)
    orders = sorted({permutation_order(g) for g in sample})
    return orders[:limit]


def commutator_subgroup(elements: Sequence[Permutation]) -> List[Permutation]:
    if not elements:
        return [Permutation.identity(0)]
    gens = []
    for a in elements:
        for b in elements:
            comm = a.invert().compose(b.invert()).compose(a).compose(b)
            if not comm.is_identity():
                gens.append(comm)
    if not gens:
        return [Permutation.identity(len(elements[0].mapping))]
    group = Group([g.mapping for g in gens])
    closure = group.closure(max_size=50_000)
    return closure or gens


def derived_series_orders(elements: Sequence[Permutation]) -> List[int]:
    orders = []
    current = list(elements)
    seen = set()
    while True:
        order = len(current)
        if order in seen:
            break
        seen.add(order)
        orders.append(order)
        comm = commutator_subgroup(current)
        if len(comm) == len(current):
            break
        current = comm
        if len(current) == 1:
            orders.append(1)
            break
    return orders


def is_perfect(elements: Sequence[Permutation]) -> bool:
    if not elements:
        return False
    comm = commutator_subgroup(elements)
    return len(comm) == len(elements)


def factor_signatures(group: Group, order: GroupOrder, limit: int = 12) -> List[FactorSignature]:
    closure = group.closure(max_size=50_000)
    primitive = group_is_primitive(group, closure)
    if closure is None:
        sample_orders = tuple(sorted(sample_element_orders(group.generators, limit)))
        return [
            FactorSignature(
                order=order.value,
                sample_orders=sample_orders,
                simple_flag="unknown",
                primitive_flag=primitive,
            )
        ]

    orders = derived_series_orders(closure)
    signatures: List[FactorSignature] = []
    for i in range(len(orders) - 1):
        factor_order = orders[i] // orders[i + 1]
        if factor_order == 1:
            continue
        prime_factors = prime_factorization(factor_order)
        for p in prime_factors:
            signatures.append(
                FactorSignature(
                    order=p,
                    sample_orders=(p,),
                    simple_flag="abelian",
                    primitive_flag=primitive,
                )
            )
    if is_perfect(closure):
        sample_orders = tuple(sorted(sample_element_orders(closure, limit)))
        signatures.append(
            FactorSignature(
                order=len(closure),
                sample_orders=sample_orders,
                simple_flag="perfect",
                primitive_flag=primitive,
            )
        )
    return signatures


def prime_factorization(n: int) -> List[int]:
    factors = []
    d = 2
    while d * d <= n:
        while n % d == 0:
            factors.append(d)
            n //= d
        d += 1
    if n > 1:
        factors.append(n)
    return factors


def group_is_primitive(group: Group, closure: Optional[List[Permutation]]) -> bool:
    if group.degree <= 2:
        return True
    if closure is None:
        return False
    # transitivity check
    orbits = group.orbits()
    if len(orbits) != 1:
        return False
    # compute stabilizer of point 0
    stab = [g for g in closure if g.apply(0) == 0]
    if not stab:
        return True
    stab_group = Group([g.mapping for g in stab])
    stab_orbits = stab_group.orbits()
    for orb in stab_orbits:
        if 1 < len(orb) < group.degree:
            return False
    return True


class NoveltyRegistry:
    def __init__(self) -> None:
        self.seen: Set[FactorSignature] = set()

    def assess(self, signatures: Iterable[FactorSignature]) -> Tuple[float, List[FactorSignature]]:
        new = []
        for sig in signatures:
            if sig not in self.seen:
                self.seen.add(sig)
                new.append(sig)
        bonus = float(len(new))
        return bonus, new
