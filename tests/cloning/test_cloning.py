#!/usr/bin/env python3

import pytest
from klab import cloning, scripting
from pathlib import Path

def test_translate():
    f = cloning.translate

    assert f('atgaacacc') == 'MNT'
    assert f('atgaataca') == 'MNT'
    assert f('ATGAACACC') == 'MNT'
    assert f('ATGAATACA') == 'MNT'


def test_all_same_length():
    f = cloning.all_seqs_same_length

    assert f([])
    assert f(['A'])
    assert f(['A', 'B'])
    assert not f(['A', 'AB'])
    assert not f(['AB', 'A'])

def test_merge_sequences():
    f = cloning.merge_sequences

    assert f('AAA') == 'AAA'
    assert f('AAA', 'ABA') == 'ABA'
    assert f('AAA', 'ABA', 'ABA') == 'ABA'
    assert f('AAA', 'ABA', 'AAB') == 'ABB'
    assert f('AAA', 'ABA', 'AAB', 'BAA') == 'BBB'

    with pytest.raises(ValueError):
        f('AAA', 'ABA', 'ACA')

def test_chains_from_pdb():
    f = cloning.chains_from_pdb

    assert f('mnt.pdb') == {'A': 'MNT'}
    assert f('mnt_mat.pdb') == {'A': 'MNT', 'B': 'MAT'}

def test_sequence_from_pdb():
    f = cloning.sequence_from_pdb

    assert f('mnt.pdb') == 'MNT'

    with pytest.raises(scripting.UserError):
        f('mnt_mat.pdb')  # Need to specify chain if ambiguous.

    assert f('mnt_mat.pdb', chain='A') == 'MNT'
    assert f('mnt_mat.pdb', chain='B') == 'MAT'

    assert f('mnt_mat.pdb', chain='A+B') == 'MNTMAT'
    assert f('mnt_mat.pdb', chain='B+A') == 'MATMNT'

    assert f('mnt_mat.pdb', chain='A~B', ref='MNA') == 'MAT'
    assert f('mnt_mat.pdb', chain='A~B', ref='MAA') == 'MNT'

    with pytest.raises(ValueError):
        # Three options (N/A/E) for position 2.
        f('mnt_mat.pdb', chain='A|B', ref='MET')

def test_sequences_from_fasta():
    f = cloning.sequences_from_fasta

    assert f('mnt.fa') == {'A': 'MNT'}
    assert f('mnt_mat.fa') == {'A': 'MNT', 'B': 'MAT'}

def test_sequence_from_fasta():
    assert cloning.sequence_from_fasta('mnt.fa') == 'MNT'


def test_write_sequences(tmpdir):
    seqs = {
            'A': 'MNT',
            'B': 'MAT',
    }
    tmpdir = Path(tmpdir)
    fasta = tmpdir / 'test.fa'
    tsv = tmpdir / 'test.tsv'
    csv = tmpdir / 'test.csv'
    xlsx = tmpdir / 'test.xlsx'
    no_ext = tmpdir / 'test'

    cloning.write_sequences(fasta, seqs)
    assert fasta.read_text() == """\
>A
MNT
>B
MAT
"""

    cloning.write_sequences(tsv, seqs)
    assert tsv.read_text() == """\
A\tMNT
B\tMAT
"""

    cloning.write_sequences(csv, seqs)
    assert csv.read_text() == """\
A,MNT
B,MAT
"""

    import pandas as pd
    cloning.write_sequences(xlsx, seqs)
    df = pd.read_excel(xlsx, header=None)
    assert df.iloc[0,0] == 'A'
    assert df.iloc[0,1] == 'MNT'
    assert df.iloc[1,0] == 'B'
    assert df.iloc[1,1] == 'MAT'

    with pytest.raises(scripting.UserError):
        cloning.write_sequences(no_ext, seqs)



