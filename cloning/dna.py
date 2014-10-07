#!/usr/bin/env python2

from __future__ import division
import re, random

dna_bases = 'ACGT'
dna_complement = {   # (fold)
        'A': 'T',  'a': 't',
        'C': 'G',  'c': 'g',
        'T': 'A',  't': 'a',
        'G': 'C',  'g': 'c',
}

genetic_code = {   # (fold)
        # Source - http://adamcoster.com/2011/01/13/python-clean-up-and-translate-nucleotide-sequences/
        'ATA': 'I', 'ATC': 'I', 'ATT': 'I', 'ATG': 'M',
        'ACA': 'T', 'ACC': 'T', 'ACG': 'T', 'ACT': 'T',
        'AAC': 'N', 'AAT': 'N', 'AAA': 'K', 'AAG': 'K',
        'AGC': 'S', 'AGT': 'S', 'AGA': 'R', 'AGG': 'R',
        'CTA': 'L', 'CTC': 'L', 'CTG': 'L', 'CTT': 'L',
        'CCA': 'P', 'CCC': 'P', 'CCG': 'P', 'CCT': 'P',
        'CAC': 'H', 'CAT': 'H', 'CAA': 'Q', 'CAG': 'Q',
        'CGA': 'R', 'CGC': 'R', 'CGG': 'R', 'CGT': 'R',
        'GTA': 'V', 'GTC': 'V', 'GTG': 'V', 'GTT': 'V',
        'GCA': 'A', 'GCC': 'A', 'GCG': 'A', 'GCT': 'A',
        'GAC': 'D', 'GAT': 'D', 'GAA': 'E', 'GAG': 'E',
        'GGA': 'G', 'GGC': 'G', 'GGG': 'G', 'GGT': 'G',
        'TCA': 'S', 'TCC': 'S', 'TCG': 'S', 'TCT': 'S',
        'TTC': 'F', 'TTT': 'F', 'TTA': 'L', 'TTG': 'L',
        'TAC': 'Y', 'TAT': 'Y', 'TAA': '.', 'TAG': '.',
        'TGC': 'C', 'TGT': 'C', 'TGA': '.', 'TGG': 'W',
}

ecoli_reverse_translate={   # (fold)
        'F': ['TTT', 'TTC'], 
        'L': ['CTG', 'TTA', 'TTG', 'CTT', 'CTC', 'CTA'], 
        'I': ['ATT', 'ATC', 'ATA'], 
        'M': ['ATG'], 
        'V': ['GTG', 'GTT', 'GTC', 'GTA'], 
        'S': ['AGC', 'TCT', 'TCC', 'TCG', 'AGT', 'TCA'], 
        'P': ['CCG', 'CCA', 'CCT', 'CCC'], 
        'T': ['ACC', 'ACG', 'ACT', 'ACA'], 
        'A': ['GCG', 'GCC', 'GCA', 'GCT'], 
        'Y': ['TAT', 'TAC'], 
        'H': ['CAT', 'CAC'], 
        'Q': ['CAG', 'CAA'], 
        'N': ['AAC', 'AAT'], 
        'K': ['AAA', 'AAG'], 
        'D': ['GAT', 'GAC'], 
        'E': ['GAA', 'GAG'], 
        'C': ['TGC', 'TGT'], 
        'W': ['TGG'], 
        'R': ['CGT', 'CGC', 'CGG', 'CGA', 'AGA', 'AGG'], 
        'G': ['GGC', 'GGT', 'GGG', 'GGA'], 
        '.': ['TAA', 'TGA', 'TAG']
}

ecoli_codon_usage={   # (fold)
        # From http://www.sci.sdsu.edu/~smaloy/MicrobialGenetics/topics/in-vitro-genetics/codon-usage.html
        'TTT': 0.51, 'TTC': 0.49, 
        'CTG': 0.55, 'TTA': 0.11, 'TTG': 0.11, 'CTT': 0.10, 'CTC': 0.10, 'CTA': 0.03, 
        'ATT': 0.47, 'ATC': 0.46, 'ATA': 0.07, 
        'ATG': 1.00, 
        'GTG': 0.34, 'GTT': 0.29, 'GTC': 0.20, 'GTA': 0.17, 
        'AGC': 0.27, 'TCT': 0.19, 'TCC': 0.17, 'TCG': 0.13, 'AGT': 0.13, 'TCA': 0.12, 
        'CCG': 0.55, 'CCA': 0.20, 'CCT': 0.16, 'CCC': 0.10, 
        'ACC': 0.44, 'ACA': 0.13, 'ACG': 0.27, 'ACT': 0.17, # special data source for threonine - http: //openwetware.org/wiki/Escherichia_coli/Codon_usage
        'GCG': 0.34, 'GCC': 0.25, 'GCA': 0.22, 'GCT': 0.19, 
        'TAT': 0.53, 'TAC': 0.47, 
        'CAT': 0.52, 'CAC': 0.48, 
        'CAG': 0.69, 'CAA': 0.31, 
        'AAC': 0.61, 'AAT': 0.39, 
        'AAA': 0.76, 'AAG': 0.24, 
        'GAT': 0.59, 'GAC': 0.41, 
        'GAA': 0.70, 'GAG': 0.30, 
        'TGC': 0.57, 'TGT': 0.43, 
        'TGG': 1.00, 
        'CGT': 0.42, 'CGC': 0.37, 'CGG': 0.08, 'CGA': 0.05, 'AGA': 0.04, 'AGG': 0.03, 
        'GGC': 0.40, 'GGT': 0.38, 'GGG': 0.13, 'GGA': 0.09, 
        'TAA': 0.62, 'TGA': 0.30, 'TAG': 0.09
}


def forward_complement(seq):
    return ''.join(dna_complement[x] for x in seq)

def reverse_complement(seq):
    return reverse(forward_complement(seq))

def reverse(seq):
    return seq[::-1]

def random_dna(desired_length):
    return ''.join(random.choice(dna_bases) for i in range(desired_length))

def is_dna(seq):
    return all(x in dna_bases for x in seq)

def gc_content(seq):
    gc_count = sum(x in 'GC' for x in seq)
    return gc_count / len(seq)

def sliding_window(sequence, win_size, step=1):
    """
    Returns a generator that will iterate through
    the defined chunks of input sequence.  Input sequence
    must be iterable.

    Credit: http://scipher.wordpress.com/2010/12/02/simple-sliding-window-iterator-in-python/
    https://github.com/xguse/scipherPyProj/blob/master/scipherSrc/defs/basicDefs.py
    """
    
    # Verify the inputs
    try:
        it = iter(sequence)
    except TypeError:
        raise ValueError("sequence must be iterable.")
    if not isinstance(win_size, int):
        raise ValueError("type(win_size) must be int.")
    if not isinstance(step, int):
        raise ValueError("type(step) must be int.")
    if step > win_size:
        raise ValueError("step must not be larger than win_size.")
    if win_size > len(sequence):
        raise ValueError("win_size must not be larger than sequence length.")
    
    # Pre-compute number of chunks to emit
    num_chunks = ((len(sequence) - win_size) / step) + 1
    
    # Do the work
    for i in range(0, num_chunks * step, step):
        yield sequence[i:i+win_size]

def num_mutations(seq_1, seq_2):
    diff_lengths = abs(len(seq_1) - len(seq_2))
    diff_bases = sum(x != y for x, y in zip(seq_1, seq_2))
    return diff_lengths + diff_bases

def dna_to_re(seq):
    """
    Return a compiled regular expression that will match anything described by 
    the input sequence.  For example, a sequence that contains a 'N' matched 
    any base at that position.
    """

    seq = seq.replace('K', '[GT]')
    seq = seq.replace('M', '[AC]')
    seq = seq.replace('R', '[AG]')
    seq = seq.replace('Y', '[CT]')
    seq = seq.replace('S', '[CG]')
    seq = seq.replace('W', '[AT]')
    seq = seq.replace('B', '[CGT]')
    seq = seq.replace('V', '[ACG]')
    seq = seq.replace('H', '[ACT]')
    seq = seq.replace('D', '[AGT]')
    seq = seq.replace('X', '[GATC]')
    seq = seq.replace('N', '[GATC]')

    return re.compile(seq)

def case_highlight(seq, subseq):
    """
    Highlights all instances of subseq in seq by making them uppercase and 
    everything else lowercase.
    """
    return re.subs(subseq.lower(), subseq.upper(), seq.lower())


