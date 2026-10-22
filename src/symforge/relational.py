from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

from symforge.colored_graph import ColoredGraph


@dataclass
class Relation:
    name: str
    arity: int
    tuples: List[Tuple[int, ...]]
    tuple_colors: Optional[List[int]] = None
    rel_color: Optional[int] = None
    position_colors: Optional[List[int]] = None


@dataclass
class RelationalStructure:
    n: int
    relations: List[Relation]
    element_colors: Optional[List[int]] = None

    def validate(self) -> None:
        if self.element_colors is not None and len(self.element_colors) != self.n:
            raise ValueError("element_colors length mismatch")
        for rel in self.relations:
            for tup in rel.tuples:
                if len(tup) != rel.arity:
                    raise ValueError("tuple arity mismatch")
                if any(not (0 <= x < self.n) for x in tup):
                    raise ValueError("tuple element out of range")
            if rel.tuple_colors is not None and len(rel.tuple_colors) != len(rel.tuples):
                raise ValueError("tuple_colors length mismatch")
            if rel.position_colors is not None and len(rel.position_colors) != rel.arity:
                raise ValueError("position_colors length mismatch")

    def is_automorphism(self, perm: Sequence[int]) -> bool:
        if len(perm) != self.n:
            return False
        if self.element_colors is not None:
            for i, c in enumerate(self.element_colors):
                if self.element_colors[perm[i]] != c:
                    return False
        for rel in self.relations:
            tuple_set = {tup for tup in rel.tuples}
            for tup in rel.tuples:
                mapped = tuple(perm[i] for i in tup)
                if mapped not in tuple_set:
                    return False
        return True


@dataclass
class CompiledStructure:
    graph: ColoredGraph
    element_nodes: List[int]
    tuple_nodes: Dict[Tuple[int, Tuple[int, ...]], int]
    edge_nodes: Dict[Tuple[int, Tuple[int, ...], int], int]

    def extend_element_perm(self, perm: Sequence[int], strict: bool = True) -> Optional[List[int]]:
        full = [0] * self.graph.n
        for idx, node in enumerate(self.element_nodes):
            full[node] = self.element_nodes[perm[idx]]
        for (rel_idx, tup), node in self.tuple_nodes.items():
            mapped = tuple(perm[i] for i in tup)
            if (rel_idx, mapped) not in self.tuple_nodes:
                if strict:
                    return None
                continue
            full[node] = self.tuple_nodes[(rel_idx, mapped)]
        for (rel_idx, tup, pos), node in self.edge_nodes.items():
            mapped = tuple(perm[i] for i in tup)
            if (rel_idx, mapped, pos) not in self.edge_nodes:
                if strict:
                    return None
                continue
            full[node] = self.edge_nodes[(rel_idx, mapped, pos)]
        return full


class _ColorAllocator:
    def __init__(self) -> None:
        self._map: Dict[Tuple[str, int, int], int] = {}

    def color_id(self, key: Tuple[str, int, int]) -> int:
        if key not in self._map:
            self._map[key] = len(self._map)
        return self._map[key]


def compile_to_colored_graph(structure: RelationalStructure) -> CompiledStructure:
    structure.validate()
    color_alloc = _ColorAllocator()

    element_colors = structure.element_colors or [0] * structure.n
    node_colors: List[int] = []

    element_nodes = list(range(structure.n))
    for c in element_colors:
        node_colors.append(color_alloc.color_id(("elem", c, 0)))

    tuple_nodes: Dict[Tuple[int, Tuple[int, ...]], int] = {}
    edge_nodes: Dict[Tuple[int, Tuple[int, ...], int], int] = {}
    adjacency: List[set[int]] = [set() for _ in range(structure.n)]

    def add_node(color: int) -> int:
        node_id = len(adjacency)
        adjacency.append(set())
        node_colors.append(color)
        return node_id

    for rel_idx, rel in enumerate(structure.relations):
        tuple_colors = rel.tuple_colors or [0] * len(rel.tuples)
        for tup, tcolor in zip(rel.tuples, tuple_colors):
            tcolor_id = color_alloc.color_id(("tuple", rel_idx, tcolor))
            tuple_node = add_node(tcolor_id)
            tuple_nodes[(rel_idx, tup)] = tuple_node
            for pos, elem in enumerate(tup):
                pos_color = rel.position_colors[pos] if rel.position_colors else pos
                ecol = color_alloc.color_id(("edge", rel_idx, pos_color))
                edge_node = add_node(ecol)
                edge_nodes[(rel_idx, tup, pos)] = edge_node
                adjacency[tuple_node].add(edge_node)
                adjacency[edge_node].add(tuple_node)
                adjacency[edge_node].add(element_nodes[elem])
                adjacency[element_nodes[elem]].add(edge_node)

    graph = ColoredGraph(n=len(adjacency), node_colors=node_colors, adjacency=adjacency)
    return CompiledStructure(
        graph=graph,
        element_nodes=element_nodes,
        tuple_nodes=tuple_nodes,
        edge_nodes=edge_nodes,
    )


def relation_from_pairs(name: str, pairs: Iterable[Tuple[int, int]]) -> Relation:
    tuples = [(a, b) for a, b in pairs]
    return Relation(name=name, arity=2, tuples=tuples)
