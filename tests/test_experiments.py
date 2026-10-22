from experiments import e1_fano, e2_design, e4_frontier
from experiments.common import automorphism_order
from symforge.generators.designs import steiner_system


def test_e1_fano_runs() -> None:
    assert e1_fano.main(["--limit", "1"]) == 0


def test_e2_design_runs() -> None:
    assert e2_design.main(["--limit", "1"]) == 0


def test_e1_fano_aut_order() -> None:
    cand = next(steiner_system(7, 3, t=2, lam=1, limit=1))
    assert automorphism_order(cand.structure) == 168


def test_e2_design_aut_order() -> None:
    cand = next(steiner_system(8, 4, t=3, lam=1, limit=1))
    assert automorphism_order(cand.structure) == 1344


def test_e4_frontier_runs() -> None:
    assert e4_frontier.main(["--budget", "2", "--per-spec", "1", "--min-n", "6", "--max-n", "7"]) == 0
