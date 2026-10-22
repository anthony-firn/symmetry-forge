from __future__ import annotations

from symforge.automorphism import canonical_label
from symforge.group import Group
from symforge.relational import RelationalStructure, compile_to_colored_graph


def automorphism_group(structure: RelationalStructure) -> Group:
    compiled = compile_to_colored_graph(structure)
    aut = canonical_label(compiled.graph, max_nodes=200)
    node_to_elem = {node: idx for idx, node in enumerate(compiled.element_nodes)}
    element_perms = []
    for perm in aut.automorphisms:
        mapped = [0] * structure.n
        for idx, node in enumerate(compiled.element_nodes):
            mapped[idx] = node_to_elem[perm[node]]
        element_perms.append(tuple(mapped))
    return Group(element_perms)


def automorphism_order(structure: RelationalStructure) -> int:
    return automorphism_group(structure).order().value
