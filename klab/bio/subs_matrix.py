from __future__ import division

def load_subs_matrix(matrix_name):
    import Bio.SubsMat.MatrixInfo as matrix_info

    # Try to get the requested substitution matrix from biopython, and 
    # complain if no such matrix exists.

    try:
        half_matrix = getattr(matrix_info, matrix_name)
    except AttributeError:
        raise ValueError("No such substitution matrix '{}'.".format(matrix_name))

    # For convenience, make sure the matrix is square (i.e. symmetrical).

    full_matrix = {}

    for i, j in half_matrix:
        full_matrix[i, j] = half_matrix[i, j]
        full_matrix[j, i] = half_matrix[i, j]

    return full_matrix

def score_gap_free_alignment(seq_1, seq_2, subs_matrix):
    if len(seq_1) != len(seq_2):
        raise ValueError("sequence lengths don't match")
    if '-' in seq_1 or '-' in seq_2:
        raise ValueError("sequences with gaps are not supported.")

    score = 0
    max_score = 0

    for aa_1, aa_2 in zip(seq_1, seq_2):
        score += subs_matrix[aa_1, aa_2]
        max_score += max(subs_matrix[aa_1, aa_1], subs_matrix[aa_2, aa_2])

    # Convert the substitution matrix score into a normalized distance.

    return 1 - max(score, 0) / max_score



