#!/usr/bin/env python2

"""\
Generate a well-behaved DNA sequence from the given protein sequence.  If a 
template DNA sequence is specified, the returned DNA sequence will be as 
similar to it as possible.  All of the given restriction sites will be removed 
from the generated sequence.  And finally, the given leading and trailing 
sequences will be appropriately concatenated.

Usage:
    protein_to_dna.py [options] <protein_seq>

Options:
    --template-dna DNA
        A (presumably natural) DNA sequence that should be used as a template 
        for the reverse translation process.  In other words, when applicable 
        codons from this template are used in favor of "optimized" codons.

    --leading-dna DNA
        A fixed DNA sequence to prepend to the generated sequence.

    --trailing-dna DNA
        A fixed DNA sequence to append to the generated sequence.

    --restriction-sites SITES
        Comma-separated list of restriction sites that may not appear in the 
        generated sequence.  You may specify either case-sensitive restriction 
        site names (must be listed in cloning.py) or DNA sequences.

    --using-gen9
        Indicate that this gene is going to be ordered from Gen9.  This enables 
        a number of checks and filters that are specific to Gen9.

"""

import docopt
import cloning

arguments = docopt.docopt(__doc__)

protein_seq = arguments['<protein_seq>']
template_dna = arguments['--template-dna']
leading_dna = arguments['--leading-dna'] or ""
trailing_dna = arguments['--trailing-dna'] or ""
try: restriction_sites = arguments['--restriction-sites'].split(',')
except: restriction_sites = ()
using_gen9 = arguments['--using-gen9']

print cloning.reverse_translate(
        protein_seq,
        template_dna,
        leading_dna,
        trailing_dna,
        restriction_sites)
