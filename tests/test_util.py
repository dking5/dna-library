import pytest
from app.utils import get_reverse_complement

def test_get_reverse_complement_standard():
    assert get_reverse_complement("ATCG") == "TAGC"
    assert get_reverse_complement("AATTCCGG") == "TTAAGGCC"

def test_get_reverse_complement_case_insensitive():
    assert get_reverse_complement("atcg") == "TAGC"
    assert get_reverse_complement("aattccgg") == "TTAAGGCC"

def test_get_reverse_complement_unknown_base():
    assert get_reverse_complement("ATCGN") == "TAGCN"

def test_get_reverse_complement_empty():
    assert get_reverse_complement("") == ""

@pytest.mark.parametrize("input_seq, expected", [
    ("AAA", "TTT"),
    ("GGG", "CCC"),
    ("TAG", "ATC"),
])
def test_get_reverse_complement_parametrized(input_seq, expected):
    assert get_reverse_complement(input_seq) == expected