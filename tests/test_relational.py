from symforge.relational import RelationalStructure, Relation, compile_to_colored_graph


def test_compiler_respects_automorphism() -> None:
    pairs = [(0, 1), (1, 0), (1, 2), (2, 1), (2, 3), (3, 2), (3, 0), (0, 3)]
    rel = Relation(name="edges", arity=2, tuples=pairs)
    structure = RelationalStructure(n=4, relations=[rel])
    perm = [1, 2, 3, 0]

    assert structure.is_automorphism(perm)
    compiled = compile_to_colored_graph(structure)
    gperm = compiled.extend_element_perm(perm)
    assert compiled.graph.is_automorphism(gperm)


def test_non_automorphism_rejected() -> None:
    pairs = [(0, 1), (1, 0), (1, 2), (2, 1), (2, 3), (3, 2), (3, 0), (0, 3)]
    rel = Relation(name="edges", arity=2, tuples=pairs)
    structure = RelationalStructure(n=4, relations=[rel])
    perm = [0, 2, 1, 3]

    assert not structure.is_automorphism(perm)
    compiled = compile_to_colored_graph(structure)
    gperm = compiled.extend_element_perm(perm)
    assert gperm is None
