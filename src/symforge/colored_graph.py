from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List, Sequence


@dataclass
class ColoredGraph:
    """Simple undirected graph with node colors."""

    n: int
    node_colors: List[int]
    adjacency: List[set[int]]

    @classmethod
    def empty(cls, n: int, node_colors: Sequence[int]) -> "ColoredGraph":
        return cls(n=n, node_colors=list(node_colors), adjacency=[set() for _ in range(n)])

    def add_edge(self, u: int, v: int) -> None:
        if u == v:
            return
        self.adjacency[u].add(v)
        self.adjacency[v].add(u)

    def edges(self) -> Iterable[tuple[int, int]]:
        for u in range(self.n):
            for v in self.adjacency[u]:
                if u < v:
                    yield u, v

    def is_automorphism(self, perm: Sequence[int]) -> bool:
        if len(perm) != self.n:
            return False
        for i, c in enumerate(self.node_colors):
            if self.node_colors[perm[i]] != c:
                return False
        for u in range(self.n):
            mapped = perm[u]
            for v in self.adjacency[u]:
                mv = perm[v]
                if mv not in self.adjacency[mapped]:
                    return False
        return True

    def canonical_adj_string(self, perm: Sequence[int]) -> bytes:
        """Adjacency serialization under a permutation."""
        order = [perm[i] for i in range(self.n)]
        bits = []
        for i in range(self.n):
            u = order[i]
            for j in range(i + 1, self.n):
                v = order[j]
                bits.append("1" if v in self.adjacency[u] else "0")
        color_part = ",".join(str(self.node_colors[i]) for i in order)
        bit_part = "".join(bits)
        return f"{color_part}|{bit_part}".encode("ascii")
