# Architecture

## Object model

- `RelationalStructure`: finite set of elements `0..n-1` with one or more relations.
- `Relation`: arity `k`, tuple list, optional tuple colors, and optional position colors.
- Optional element coloring supports pre-partitioning for constrained symmetries.

## Compiler to colored graphs

- `compile_to_colored_graph` encodes structures into a colored graph with:
  - element nodes
  - tuple nodes for each relation tuple
  - position/edge nodes to encode tuple membership
- Colors encode element colors, relation type + tuple color, and (optionally) position
  colors; this preserves automorphisms of the original structure.

## Automorphism oracle

- `canonical_label` performs color refinement + backtracking individualization.
- Returns a canonical adjacency serialization and a set of automorphisms.
- Optional pynauty backend can be used for faster canonicalization (colored graphs supported).
- Optional nauty backend can be used when `dreadnaut` is installed (uncolored graphs).
- For larger graphs it falls back to a refinement-only label and marks the result
  as approximate.

## Group utilities

- `Permutation` implements compose/invert/apply.
- `Group` can compute closure for small groups; otherwise it estimates order via
  a basic Schreier–Sims routine.

## Search & scoring

- `SearchEngine` iterates over candidate generators, evaluates, logs, and keeps
  top-K results.
- `ScoreBreakdown` combines:
  - compressibility of canonical serialization
  - invariance outlier score: log(|Aut|) against a random baseline
  - novelty bonus from unseen factor signatures

## Generators

- `regular_graphs`: backtracking generator for regular graphs with canonical
  rejection.
- `random_regular_graphs`: configuration-model sampler for larger regular graphs.
- `strongly_regular_graphs`: constraint-based generator for small SRGs.
- `steiner_system`: exact-cover generator for Steiner systems.
- `steiner_system_sat`: optional PySAT-backed generator.
- `commutative_magma_tables`: enumerates small commutative magma tables.

## Frontier exploration

- `experiments/e4_frontier.py` samples constraint families without name lookup
  and logs outlier/novelty scores to expand the search beyond known directions.

## Transformations

- `incidence_matrix` → `Code` (GF(2) span)
- `dual_code`
- Construction A lattice vectors with a lightweight shift search
- `minimal_vector_graph` to feed the automorphism engine

## Monster attempt toolkit

- `fingerprint`: order, orbits, involutions, primitivity heuristic
- `glue_orbit_actions`: minimal action gluing attempt
- `algebra_from_symmetry`: builds a commutative algebra invariant under a group
