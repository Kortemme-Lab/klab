#!/usr/bin/env python2

from __future__ import division

import dna
import gen9

restriction_sites = {   # (fold)
        'BsaI':     'GGTCTC',
        'AarI':     'CACCTGC',
        'EcoRI':    'GAATTC',
        'HindIII':  'AAGCTT',
        'NdeI ':    'CATATG',
        'XmnI':     'GAANNNNTTC',
        'BamHI':    'GGATCC',
}


def reverse_translate(
        protein_seq,
        template_dna=None, leading_seq="", trailing_seq="",
        forbidden_seqs=(), using_gen9=False):
    """
    Generate a well-behaved DNA sequence from the given protein sequence.  If a 
    template DNA sequence is specified, the returned DNA sequence will be as 
    similar to it  as possible.  Any given restriction sites will not be 
    present in the sequence.  And finally, the given leading and trailing 
    sequences will be appropriately concatenated.
    """

    if using_gen9:
        forbidden_seqs += gen9.reserved_restriction_sites

    leading_seq = restriction_sites.get(leading_seq, leading_seq)
    trailing_seq = restriction_sites.get(trailing_seq, trailing_seq)

    codon_list = make_codon_list(protein_seq, template_dna)
    sanitize_codon_list(codon_list, forbidden_seqs)
    dna_seq = leading_seq + ''.join(codon_list) + trailing_seq

    if using_gen9:
        gen9.apply_quality_control_checks(dna_seq)

    return dna_seq

def make_codon_list(protein_seq, template_dna=None):
    """
    Return a list of codons that would be translated to the given protein 
    sequence.  Codons are picked first to minimize the mutations relative to a 
    template DNA sequence and second to prefer "optimal" codons.
    """

    codon_list = []

    if template_dna is None:
        template_dna = []

    for i, res in enumerate(protein_seq.upper()):
        try: template_codon = template_dna[3*i:3*i+3]
        except IndexError: template_codon = '---'

        # Already sorted by natural codon usage
        possible_codons = dna.ecoli_reverse_translate[res]

        # Sort by similarity.  Note that this is a stable sort.
        possible_codons.sort(
                key=lambda x: dna.num_mutations(x, template_codon))

        # Pick the best codon.
        codon_list.append(possible_codons[0])

    return codon_list

def sanitize_codon_list(codon_list, forbidden_seqs=()):
    """
    Make silent mutations to the given codon lists to remove any undesirable 
    sequences that are present within it.  Undesirable sequences include 
    restriction sites, which may be optionally specified as a second argument, 
    and homopolymers above a pre-defined length.  The return value is the 
    number of corrections made to the codon list.
    """

    # Unit test missing for:
    #   Homopolymer fixing

    for codon in codon_list:
        if len(codon) != 3:
            raise ValueError("Codons must have exactly 3 bases: '{}'".format(codon))

    # Compile a collection of all the sequences we don't want to appear in the 
    # gene.  This includes the given restriction sites and their reverse 
    # complements, plus any homopolymers above a pre-defined length.

    bad_seqs = set()
    
    bad_seqs.union(
            restriction_sites.get(seq, seq)
            for seq in forbidden_seqs)

    bad_seqs.union(
            dna.reverse_complement(seq)
            for seq in bad_seqs)

    bad_seqs.union(
            base * (gen9.homopolymer_max_lengths[base] + 1)
            for base in dna.dna_bases)

    bad_seqs = [
            dna.dna_to_re(bs)
            for bs in bad_seqs]

    # Remove every bad sequence from the gene by making silent mutations to the 
    # codon list.
    
    num_corrections = 0

    for bad_seq in bad_seqs:
        while remove_bad_sequence(codon_list, bad_seq, bad_seqs):
            num_corrections += 1

    return num_corrections
        
def remove_bad_sequence(codon_list, bad_seq, bad_seqs):
    """
    Make a silent mutation to the given codon list to remove the first instance 
    of the given bad sequence found in the gene sequence.  If the bad sequence 
    isn't found, nothing happens and the function returns false.  Otherwise the 
    function returns true.  You can use these return values to easily write a 
    loop totally purges the bad sequence from the codon list.  Both the 
    specific bad sequence in question and the list of all bad sequences are 
    expected to be regular expressions.
    """

    gene_seq = ''.join(codon_list)
    problem = bad_seq.search(gene_seq)

    if not problem:
        return False

    bs_start_codon = problem.start() // 3
    bs_end_codon = problem.end() // 3

    for i in range(bs_start_codon, bs_end_codon):
        problem_codon = codon_list[i]
        amino_acid = translate_dna(problem_codon)

        alternate_codons = [
                codon
                for codon in dna.ecoli_reverse_translate[amino_acid]
                if codon != problem_codon]

        for alternate_codon in alternate_codons:
            codon_list[i] = alternate_codon

            if problem_with_codon(i, codon_list, bad_seqs):
                codon_list[i] = problem_codon
            else:
                return True

    raise RuntimeError("Could not remove bad sequence '{}' from gene.".format(bs))

def problem_with_codon(codon_index, codon_list, bad_seqs):
    """
    Return true if the given codon overlaps with a bad sequence.
    """

    base_1 = 3 * codon_index
    base_3 = 3 * codon_index + 2

    gene_seq = ''.join(codon_list)

    for bad_seq in bad_seqs:
        problem = bad_seq.search(gene_seq)
        if problem and problem.start() < base_3 and problem.end() > base_1:
            return True

    return False


