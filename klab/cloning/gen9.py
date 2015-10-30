#!/usr/bin/env python2

min_gene_length = 500 # base pairs
max_gene_length = 1000 # base pairs

global_gc_content_min = 0.40
global_gc_content_max = 0.65

local_gc_content_min = 0.30
local_gc_content_max = 0.75
local_gc_window_size = 100 # base pairs

reserved_restriction_sites = 'BasI', 'AarI'

homopolymer_max_lengths = {'A': 8, 'C': 8, 'G': 5, 'T': 8}

def apply_quality_control_checks(
        seq,
        check_gen9_seqs=True,
        check_short_length=True,
        check_local_gc_content=True,
        check_global_gc_content=True):
    """
    Raise a ValueError if the given sequence doesn't pass all of the Gen9 
    quality control design guidelines.  Certain checks can be enabled or 
    disabled via the command line.
    """

    seq = seq.upper()
    failure_reasons = []
    
    # Minimum length
    if check_short_length:
        if len(seq) < min_gene_length:
            failure_reasons.append('minimum_length: Sequence is %d bp long and needs to be at least %d bp'%(len(seq),min_gene_length))

    # Maximum length
    if len(seq) > max_gene_length:
        failure_reasons.append('maximum_length: Sequence is %d bp long and needs to be shorter than %d bp'%(len(seq),max_gene_length))

    # Gen9 restricted sequences
    if check_gen9_seqs:
        for site in reserved_restriction_sites:
            pattern = dna.dna_to_re(site)
            reverse_site = dna.reverse_complement(site)
            reverse_pattern = dna.dna_to_re(reverse_site)

            if pattern.match(seq):
                failure_reasons.append('gen9_restricted_sequences: Reserved sequence %s is present'%(site))
            if reverse_pattern.match(seq):
                failure_reasons.append('gen9_restricted_sequences: Reverse-complement of reserved sequence %s is present'%(site))

    # Global GC content
    if check_global_gc_content:
        gc_content = dna.gc_content(seq)

        if gc_content < global_gc_content_min:
            failure_reasons.append('global_gc_content_min: Global GC content is %.3f%% and must be at least %.3f%%'%(gc_content,global_gc_content_min))

        if gc_content > global_gc_content_max:
            failure_reasons.append('global_gc_content_max: Global GC content is %.3f%% and must be less than %.3f%%'%(gc_content,global_gc_content_max))

    # Local GC content (windows)
    if check_local_gc_content:
        windows = [seq]

        if local_gc_window_size < len(seq):
            windows = dna.sliding_window(seq, local_gc_window_size)

        for seq_window in windows:
            lgc_content = dna.gc_content(seq_window)

            if lgc_content < local_gc_content_min:
                failure_reasons.append('local_gc_content_min: Local GC content is %.3f%% and must be at least %.3f%%'%(lgc_content,local_gc_content_min))
                break
            if lgc_content > local_gc_content_max:
                failure_reasons.append('local_gc_content_max: Local GC content is %.3f%% and must be less than %.3f%%'%(lgc_content,local_gc_content_max))
                break

    # Homopolymers
    for base in dna.dna_bases:
        homopolymer = base * homopolymer_max_lengths[base]
        if homopolymer in seq:
            failure_reasons.append('max_%s_homopolymer: %s'%(
                base.lower(), dna.case_highlight(seq,a_homopolymer)))

    # Make sure all the checks passed.
    if failure_reasons:
        intro = "The given sequence fails following Gen9 design guidelines:"
        raise ValueError('\n'.join([intro] + failure_reasons))


