# Monster Attempt

## Pipeline

1. Generate highly symmetric candidates from regular graph searches.
2. Extract group fingerprints (order, orbits, involutions, primitivity).
3. Attempt gluing of compatible actions along shared orbits.
4. Attempt to synthesize a commutative algebra invariant under a discovered group.

## What is implemented

- Fingerprint summaries from permutation generators.
- A minimal gluing attempt based on orbit-structure compatibility.
- An algebra-from-symmetry constructor that enforces commutativity and group
  invariance over GF(2).
- A `m7_monster_attempt` experiment that logs intermediate artifacts.

## Running larger attempts

Use `m7_monster_attempt` with explicit configs and optional design lifts:

```bash
PYTHONPATH=src:. symforge experiment experiments.m7_monster_attempt \\
  --configs 6:3,7:2,8:3,9:4,10:3 \\
  --budget 20 --no-dedup --include-designs
```

For random regular sampling and SAT-backed designs:

```bash
PYTHONPATH=src:. symforge experiment experiments.m7_monster_attempt \\
  --configs 10:3,12:3 --random --budget 50 --max-tries 500 \\
  --include-designs --sat-designs --design-configs 9:3:2,10:4:2
```

To explore broader constraint families without targeting known objects:

```bash
PYTHONPATH=src:. symforge experiment experiments.e4_frontier --budget 50 --per-spec 3
```

## Limitations

- The current gluing search is coarse and only matches identical orbit
  decompositions.
- The algebra construction does not enforce associativity or special identities.
- Scaling to the Monster will require stronger canonicalization and a more
  aggressive search curriculum.

## Next scaling steps

- Integrate a faster automorphism engine (nauty/Traces) to scale beyond
  backtracking.
- Expand gluing to partial isomorphisms and stabilizer chains.
- Add a SAT-based solver for algebra identities (e.g., axial algebras).
