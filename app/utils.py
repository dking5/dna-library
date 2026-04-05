def get_reverse_complement(sequence: str) -> str:
    complement = str.maketrans("ATCGN", "TAGCN")
    return sequence.upper().translate(complement)

def generate_dna_embedding(sequence: str):
    seq = sequence.upper()
    length = len(seq)
    if length == 0:
        return [0.0, 0.0, 0.0]
    
    gc_count = seq.count('G') + seq.count('C')
    a_count = seq.count('A')

    return [
        round(gc_count / length, 4), 
        round(a_count / length, 4), 
        round(min(length / 1000, 1.0), 4)
    ]