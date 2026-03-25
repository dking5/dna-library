def get_reverse_complement(sequence: str) -> str:
    complement = str.maketrans("ATCGN", "TAGCN")
    return sequence.upper().translate(complement)