from __future__ import annotations

from dataclasses import dataclass
import os
import re
import shutil
import subprocess
from typing import Dict, List, Optional, Tuple

from symforge.colored_graph import ColoredGraph


@dataclass
class AutomorphismResult:
    canonical_label: bytes
    automorphisms: List[Tuple[int, ...]]
    exact: bool


def initial_partition(graph: ColoredGraph) -> List[List[int]]:
    buckets: Dict[int, List[int]] = {}
    for v, c in enumerate(graph.node_colors):
        buckets.setdefault(c, []).append(v)
    return [sorted(buckets[c]) for c in sorted(buckets)]


def refine_partition(graph: ColoredGraph, partition: List[List[int]]) -> List[List[int]]:
    changed = True
    while changed:
        changed = False
        cell_index = [0] * graph.n
        for idx, cell in enumerate(partition):
            for v in cell:
                cell_index[v] = idx
        new_partition: List[List[int]] = []
        for cell in partition:
            sig_map: Dict[Tuple[int, Tuple[int, ...]], List[int]] = {}
            for v in cell:
                counts = [0] * len(partition)
                for u in graph.adjacency[v]:
                    counts[cell_index[u]] += 1
                sig = (graph.node_colors[v], tuple(counts))
                sig_map.setdefault(sig, []).append(v)
            if len(sig_map) == 1:
                new_partition.append(sorted(cell))
            else:
                changed = True
                for sig in sorted(sig_map, key=lambda s: s):
                    new_partition.append(sorted(sig_map[sig]))
        partition = new_partition
    return partition


def _choose_cell(partition: List[List[int]]) -> int:
    candidates = [(len(cell), idx) for idx, cell in enumerate(partition) if len(cell) > 1]
    candidates.sort()
    return candidates[0][1]


def canonical_label(
    graph: ColoredGraph,
    max_nodes: int = 16,
    backend: Optional[str] = None,
) -> AutomorphismResult:
    backend = backend or os.getenv("SYMFORGE_AUTOMORPHISM_BACKEND", "auto")
    if backend in {"auto", "pynauty"}:
        result = _canonical_label_pynauty(graph)
        if result is not None:
            return result
        if backend == "pynauty":
            return _canonical_label_internal(graph, max_nodes=max_nodes)
    if backend in {"auto", "nauty"}:
        result = _canonical_label_nauty(graph)
        if result is not None:
            return result
        if backend == "nauty":
            # Fallback to internal if nauty is unavailable.
            return _canonical_label_internal(graph, max_nodes=max_nodes)
    return _canonical_label_internal(graph, max_nodes=max_nodes)


def _canonical_label_internal(graph: ColoredGraph, max_nodes: int = 16) -> AutomorphismResult:
    if graph.n == 0:
        return AutomorphismResult(canonical_label=b"", automorphisms=[()], exact=True)

    partition = refine_partition(graph, initial_partition(graph))

    if graph.n > max_nodes:
        order = [v for cell in partition for v in cell]
        label = graph.canonical_adj_string(order)
        return AutomorphismResult(canonical_label=label, automorphisms=[tuple(range(graph.n))], exact=False)

    best_label: bytes | None = None
    best_order: List[int] | None = None
    automorphisms: List[Tuple[int, ...]] = []

    def dfs(part: List[List[int]]) -> None:
        nonlocal best_label, best_order, automorphisms
        part = refine_partition(graph, part)
        if all(len(cell) == 1 for cell in part):
            order = [cell[0] for cell in part]
            label = graph.canonical_adj_string(order)
            if best_label is None or label < best_label:
                best_label = label
                best_order = order
                automorphisms = [tuple(range(graph.n))]
            elif label == best_label and best_order is not None:
                perm = [0] * graph.n
                for i, node in enumerate(best_order):
                    perm[node] = order[i]
                automorphisms.append(tuple(perm))
            return
        idx = _choose_cell(part)
        cell = part[idx]
        for v in cell:
            new_part = [list(c) for c in part]
            new_part[idx] = [v]
            rest = [x for x in cell if x != v]
            new_part.insert(idx + 1, rest)
            dfs(new_part)

    dfs(partition)
    if best_label is None:
        best_label = b""
    return AutomorphismResult(canonical_label=best_label, automorphisms=automorphisms, exact=True)


def _canonical_label_nauty(graph: ColoredGraph) -> Optional[AutomorphismResult]:
    if graph.n == 0:
        return AutomorphismResult(canonical_label=b"", automorphisms=[()], exact=True)
    if len(set(graph.node_colors)) != 1:
        return None
    dreadnaut = shutil.which("dreadnaut")
    if dreadnaut is None:
        return None

    lines = [f"n={graph.n}", "g"]
    for i in range(graph.n):
        neigh = " ".join(str(j) for j in sorted(graph.adjacency[i]) if j != i)
        lines.append(f"{i}: {neigh};")
    lines.append(".")
    lines.append("c")
    lines.append("x")
    lines.append("q")
    input_data = "\n".join(lines).encode("ascii")
    proc = subprocess.run(
        [dreadnaut],
        input=input_data,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if proc.returncode != 0:
        return None
    output = proc.stdout.decode("ascii", errors="ignore")
    automorphisms = _parse_nauty_generators(output, graph.n)
    if not automorphisms:
        automorphisms = [tuple(range(graph.n))]
    canonical = _parse_nauty_canonical(output)
    if canonical is None:
        # Fall back to internal canonical label if nauty output isn't parseable.
        canonical = _canonical_label_internal(graph, max_nodes=16).canonical_label
    return AutomorphismResult(canonical_label=canonical, automorphisms=automorphisms, exact=True)


def _canonical_label_pynauty(graph: ColoredGraph) -> Optional[AutomorphismResult]:
    try:
        import pynauty  # type: ignore
    except Exception:
        return None
    adj = {i: sorted(graph.adjacency[i]) for i in range(graph.n)}
    color_map: Dict[int, set[int]] = {}
    for idx, color in enumerate(graph.node_colors):
        color_map.setdefault(color, set()).add(idx)
    vertex_coloring = [color_map[c] for c in sorted(color_map)]
    g = pynauty.Graph(graph.n, adjacency_dict=adj, vertex_coloring=vertex_coloring)
    cert = pynauty.certificate(g)
    aut = pynauty.autgrp(g)
    generators = []
    if aut and aut[0]:
        for gen in aut[0]:
            generators.append(tuple(gen))
    if not generators:
        generators = [tuple(range(graph.n))]
    return AutomorphismResult(canonical_label=cert, automorphisms=generators, exact=True)


def _parse_nauty_generators(output: str, n: int) -> List[Tuple[int, ...]]:
    perms: List[Tuple[int, ...]] = []
    for line in output.splitlines():
        if "(" not in line or ")" not in line:
            continue
        perm = list(range(n))
        cycles = re.findall(r"\(([^)]*)\)", line)
        for cycle in cycles:
            items = [int(x) for x in re.findall(r"\d+", cycle)]
            if len(items) < 2:
                continue
            first = items[0]
            for i in range(len(items) - 1):
                perm[items[i]] = items[i + 1]
            perm[items[-1]] = first
        if perm != list(range(n)):
            perms.append(tuple(perm))
    return perms


def _parse_nauty_canonical(output: str) -> Optional[bytes]:
    for line in output.splitlines():
        if "canonical" in line.lower() or "labeling" in line.lower():
            nums = [int(x) for x in re.findall(r"\d+", line)]
            if nums:
                return ("|".join(str(n) for n in nums)).encode("ascii")
    return None
