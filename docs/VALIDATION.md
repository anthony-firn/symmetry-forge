# Validation

## Test suite

```bash
pytest
```

## Rediscovery experiments

E1: Fano-like Steiner system S(2,3,7)

```bash
PYTHONPATH=src python -m symforge.cli experiment experiments.e1_fano --limit 1
```

E2: Steiner system S(3,4,8)

```bash
PYTHONPATH=src python -m symforge.cli experiment experiments.e2_design --limit 1
```

E3: Outlier search on small regular graphs

```bash
PYTHONPATH=src python -m symforge.cli experiment experiments.e3_outlier --n 6 --degree 3 --budget 10
```

E4: Frontier exploration across constraint families

```bash
PYTHONPATH=src python -m symforge.cli experiment experiments.e4_frontier --budget 20
```

## Expected outputs

- JSONL logs appear in `results/`.
- E1/E2 logs include an automorphism order consistent with known invariants
  (checked in tests, not baked into generators).
