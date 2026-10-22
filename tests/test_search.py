from symforge.relational import Relation, RelationalStructure
from symforge.search import Candidate, SearchConfig, SearchEngine


def test_search_runs() -> None:
    tri = Relation(name="edges", arity=2, tuples=[(0, 1), (1, 2), (2, 0)])
    line = Relation(name="edges", arity=2, tuples=[(0, 1), (1, 2)])
    c1 = Candidate(structure=RelationalStructure(n=3, relations=[tri]))
    c2 = Candidate(structure=RelationalStructure(n=3, relations=[line]))
    engine = SearchEngine(SearchConfig(budget=2, top_k=1))
    results = engine.run([c1, c2])
    assert len(results) == 1
