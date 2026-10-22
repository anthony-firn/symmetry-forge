from symforge.group import Group
from symforge.monster import algebra_from_symmetry, fingerprint


def test_fingerprint_simple_group() -> None:
    group = Group([(1, 0)])
    fp = fingerprint(group)
    assert fp.order == 2


def test_algebra_from_symmetry_runs() -> None:
    group = Group([(1, 0)])
    structure = algebra_from_symmetry(group, seed=1)
    assert structure.n == 2
    assert structure.relations
