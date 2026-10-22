from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

from symforge.group import Group, Permutation
from symforge.relational import Relation, RelationalStructure


@dataclass
class Fingerprint:
    order: int
    order_exact: bool
    orbit_sizes: List[int]
    involutions: int
    primitive: bool


def involutions(group: Group, max_samples: int = 2000) -> List[Permutation]:
    closure = group.closure(max_size=max_samples)
    if closure is None:
        return []
    return [g for g in closure if _perm_order(g) == 2]


def centralizer(group: Group, element: Permutation, max_samples: int = 2000) -> List[Permutation]:
    closure = group.closure(max_size=max_samples)
    if closure is None:
        return []
    return [g for g in closure if g.compose(element).mapping == element.compose(g).mapping]


def fingerprint(group: Group) -> Fingerprint:
    order = group.order()
    invs = involutions(group)
    orbit_sizes = [len(o) for o in group.orbits()]
    primitive = False
    closure = group.closure(max_size=50_000)
    if closure is not None:
        primitive = _is_primitive(group, closure)
    return Fingerprint(
        order=order.value,
        order_exact=order.exact,
        orbit_sizes=orbit_sizes,
        involutions=len(invs),
        primitive=primitive,
    )


def glue_orbit_actions(group_a: Group, group_b: Group) -> Optional[Group]:
    if group_a.degree != group_b.degree or group_a.degree == 0:
        return None
    if group_a.orbits() != group_b.orbits():
        return None
    merged = list(group_a.generators) + list(group_b.generators)
    return Group([g.mapping for g in merged])


def algebra_from_symmetry(group: Group, seed: int = 0) -> RelationalStructure:
    rng = random.Random(seed)
    n = group.degree
    closure = group.closure(max_size=50_000)
    if closure is None:
        raise ValueError("group too large for algebra search")

    # compute orbit reps for unordered pairs
    pairs = [(i, j) for i in range(n) for j in range(i, n)]
    pair_orbit_rep: Dict[Tuple[int, int], Tuple[int, int]] = {}
    pair_to_g: Dict[Tuple[int, int], Permutation] = {}
    reps: List[Tuple[int, int]] = []

    for pair in pairs:
        if pair in pair_orbit_rep:
            continue
        reps.append(pair)
        pair_orbit_rep[pair] = pair
        pair_to_g[pair] = Permutation.identity(n)
        for g in closure:
            mapped = tuple(sorted((g.apply(pair[0]), g.apply(pair[1]))))
            if mapped not in pair_orbit_rep:
                pair_orbit_rep[mapped] = pair
                pair_to_g[mapped] = g

    outputs: Dict[Tuple[int, int], int] = {}
    for rep in reps:
        stabilizer = [g for g in closure if tuple(sorted((g.apply(rep[0]), g.apply(rep[1])))) == rep]
        stab_group = Group([g.mapping for g in stabilizer])
        stab_orbits = stab_group.orbits() if stabilizer else [[i] for i in range(n)]
        vec = 0
        for orb in stab_orbits:
            if rng.random() < 0.5:
                for v in orb:
                    vec |= 1 << v
        outputs[rep] = vec

    tuples: List[Tuple[int, int, int]] = []
    for pair in pairs:
        rep = pair_orbit_rep[pair]
        g = pair_to_g[pair]
        vec = outputs[rep]
        # transport vector by g
        mapped_vec = 0
        for i in range(n):
            if vec & (1 << i):
                mapped_vec |= 1 << g.apply(i)
        for k in range(n):
            if mapped_vec & (1 << k):
                tuples.append((pair[0], pair[1], k))
                if pair[0] != pair[1]:
                    tuples.append((pair[1], pair[0], k))

    rel = Relation(name="mul", arity=3, tuples=tuples)
    return RelationalStructure(n=n, relations=[rel])


def _perm_order(perm: Permutation) -> int:
    seen = [False] * len(perm.mapping)
    order = 1
    for i in range(len(perm.mapping)):
        if seen[i]:
            continue
        length = 0
        j = i
        while not seen[j]:
            seen[j] = True
            j = perm.mapping[j]
            length += 1
        if length > 0:
            order = _lcm(order, length)
    return order


def _lcm(a: int, b: int) -> int:
    import math

    return abs(a * b) // math.gcd(a, b)


def _is_primitive(group: Group, closure: List[Permutation]) -> bool:
    if group.degree <= 2:
        return True
    if len(group.orbits()) != 1:
        return False
    stab = [g for g in closure if g.apply(0) == 0]
    if not stab:
        return True
    stab_group = Group([g.mapping for g in stab])
    for orb in stab_group.orbits():
        if 1 < len(orb) < group.degree:
            return False
    return True
