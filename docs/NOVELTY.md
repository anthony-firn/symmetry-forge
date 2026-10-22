# Novelty

## Criteria

Novelty is measured without any name lookup or catalog matching:

- A new factor signature appears in the automorphism group.
- The action is primitive with unusual orbit structure.
- The invariance outlier score is large relative to same-size random baselines.

## Factor signatures

A factor signature records:

- estimated order
- a small sample of element orders
- a simple/perfect/unknown flag
- a primitive-action flag

Composition factors are approximated via derived-series heuristics for groups
with full closure; large groups fall back to sampled signatures.

## Limitations

- Derived-series heuristics can merge several factors into a single signature.
- For large groups the signature is approximate and may miss rare factors.
- Primitivity checks are exact only when closure is available.

## Frontier exploration

The `E4` frontier experiment samples broad constraint families (regular, SRG,
design, algebra) without targeting known objects, then prioritizes candidates
by novelty/outlier scores.
