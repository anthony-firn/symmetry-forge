# Symmetry Forge

An experimental Python toolkit for generating small combinatorial structures,
computing graph automorphisms, and comparing simple symmetry-based novelty
scores. It is intended for reproducible exploration and education, not as a
source of new mathematical results or a substitute for proof.

The included experiments cover Steiner systems, graphs, relational structures,
and a bounded attempt at code-lattice/Monster-inspired constructions. They
write local JSONL output; their samples are useful starting points rather than
validated discoveries.

## Status

Version 0.1.0 is an early research prototype. The standard-library core and
test suite run without optional dependencies. Larger searches can take a long
time, and optional `pynauty`, `dreadnaut`, and `python-sat` integrations are
not required for the basic examples.

## Install

```bash
pip install -e .[dev]
```

If you prefer not to install, run with `PYTHONPATH=src`.

Optional extras:

```bash
pip install -e .[nauty,sat]
```

## Quickstart

```bash
PYTHONPATH=src python -m symforge.cli --version
PYTHONPATH=src python -m symforge.cli experiment experiments.e1_fano --limit 1
```

## Optional faster automorphisms (nauty)

If you have `pynauty` installed, you can use it for faster automorphisms
and canonical labels (colored graphs supported):

```bash
SYMFORGE_AUTOMORPHISM_BACKEND=pynauty PYTHONPATH=src python -m symforge.cli experiment experiments.e3_outlier
```

If you have `dreadnaut` on your PATH, you can enable the nauty backend for
uncolored graphs:

```bash
SYMFORGE_AUTOMORPHISM_BACKEND=nauty PYTHONPATH=src python -m symforge.cli experiment experiments.e3_outlier
```

## Experiments

```bash
PYTHONPATH=src python -m symforge.cli experiment experiments.e1_fano
PYTHONPATH=src python -m symforge.cli experiment experiments.e2_design
PYTHONPATH=src python -m symforge.cli experiment experiments.e3_outlier --n 6 --degree 3
PYTHONPATH=src python -m symforge.cli experiment experiments.e3_outlier --n 10 --degree 3 --random --budget 50
PYTHONPATH=src python -m symforge.cli experiment experiments.e4_frontier --budget 20
PYTHONPATH=src python -m symforge.cli experiment experiments.m6_code_lattice
PYTHONPATH=src python -m symforge.cli experiment experiments.m7_monster_attempt
PYTHONPATH=src python -m symforge.cli experiment experiments.m7_monster_attempt \\
  --configs 8:3,9:4,10:3 --random --budget 50 --max-tries 500
```

## Results logging

Experiments write JSONL logs into `results/`. Each line records parameters,
scores, and computed invariants. The directory is ignored so local runs do not
change the working tree.

## Symmetry map (SVG)

Render the progress map from results:

```bash
python tools/render_symmetry_map.py --input docs/symmetry_map.json --results results --output docs/symmetry_map.svg
```

## Develop

```bash
pip install -e ".[dev]"
make lint
make test
```

Contributions should include a focused test and should distinguish a computed
experiment from a proved or externally validated result.

## License

MIT. See [LICENSE](LICENSE).
