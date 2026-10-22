from symforge.transformations import Code, dual_code, shift_search


def dot_mod2(a: int, b: int) -> int:
    return bin(a & b).count("1") % 2


def test_dual_code_orthogonality() -> None:
    code = Code(length=3, basis=[0b011])
    dual = dual_code(code)
    for w in code.codewords(max_words=8):
        for d in dual.codewords(max_words=8):
            assert dot_mod2(w, d) == 0


def test_shift_search_length() -> None:
    code = Code(length=4, basis=[0b0011])
    shift = shift_search(code, trials=4, seed=1)
    assert len(shift) == 4
