#!/usr/bin/env python

"""\
Generate a well-behaved DNA sequence from the given protein sequence.  If a 
template DNA sequence is specified, the returned DNA sequence will be as 
similar to it as possible.  All of the given restriction sites will be removed 
from the generated sequence.  And finally, the given leading and trailing 
sequences will be appropriately concatenated.

Usage:
    klab_reverse_translate <proteins>... [options]

Arguments:
    <proteins>
        The protein sequence(s) to reverse-translate, specified in any of the 
        following formats:
        
        - A PDB file or a gzipped PDB file (see the --chain option to specify 
          which chain or chains are used).  The file extension must be either 
          '.pdb' or '.pdb.gz'.
        - A FASTA file containing one or more protein sequences.  The file 
          extension must be either '.fa', '.fas', or '.fasta'.
        - A file containing the path to a PDB or FASTA file on each line.
        - A directory containing any number of PDB or FASTA files.

Options:
    -c --chain CHAIN
        Which protein chain(s) to use in making a DNA sequence (and how those 
        chains should be combined, if using more than one):

        - If no chain is specified (the default), each specified PDB file 
          must contain only one chain.  The sequence of that chain will be used.
          
        - If a single chain is specified (e.g. "A"), only the specified chain 
          will be used.

        - If multiple chains are joined by "+" signs (e.g. "A+B"), the 
          sequences for those chains will be concatenated together in the given 
          order.  This effectively combines the chains into one.
          
        - If multiple chains are joined by "~" signs (e.g. "A~B"), the 
          indicated chains will be considered as multiple copies of the same 
          protein, and mutations from every chain will be merged into one 
          sequence.  This behavior requires the `--template-dna` option.

        Note that the --chain option only applies to protein sequences loaded 
        from PDB files, not FASTA files.  There's no way to specify different 
        chains for different PDB files, other than by calling this command more 
        than once.  It is also currently forbidden to mix "+" and "~".
        
    -o --output PATH
        Output the reverse-translated DNA sequences to the given path.  The 
        file format depends on the extension of that path.  Currently, the 
        following formats are supported:

        - *.fa, *.fas, *.fasta: FASTA
        - *.tsv, *.csv: Tab- or comma-separated values, respectively.
        
    -d --template-fasta PATH
        The path to a FASTA file containing the template DNA sequence.  See 
        `--template-dna` for more details.

    -D --template-dna DNA
        A (presumably natural) DNA sequence that should be used as a template 
        for the reverse translation process.  In other words, when applicable 
        codons from this template are used in favor of "optimized" codons.

    --leading-dna DNA
        A fixed DNA sequence to prepend to the generated sequence.

    --trailing-dna DNA
        A fixed DNA sequence to append to the generated sequence.

    --make-ytk-part ID
        Add leading and trailing sequences containing restriction sites and 
        linker sites compatible with the Yeast Toolkit.  Typically the part ID 
        would be "3", but "3a" is also allowed.  This overrides the 
        `--leading-dna` and `--trailing-dna` options.
        
    --restriction-sites SITES
        Comma-separated list of restriction sites that may not appear in the 
        generated sequence.  You may specify either case-sensitive restriction 
        site names (must be listed in digest.py) or DNA sequences.

    --manufacturer COMPANY
        Run checks and filters specific to the company that will be 
        manufacturing the DNA.  Currently options are: "gen9", "twist".
"""

from __future__ import print_function

import csv
from . import cloning, ytk
from .. import docopt, scripting
from pathlib import Path

PDB_EXT = '.pdb'
FASTA_EXT = '.fa', '.fas', '.fasta'

@scripting.catch_and_print_errors()
def main():
    args = docopt.docopt(__doc__)

    # Work out the template sequence (`None` if not specified):

    if args['--template-dna'] and args['--template-fasta']:
        raise scripting.UserError("Cannot specify both --template-dna and --template-fasta")

    template_dna = args['--template-dna']
    template_protein = None

    if args['--template-fasta']:
        template_dna = cloning.sequence_from_fasta(args['--template-fasta'])

    if template_dna:
        template_protein = cloning.translate(template_dna)

    # Work out the input sequences:

    if not args['<proteins>']:
        raise scripting.UserError("No protein sequences specified.")

    protein_seqs = {}

    def load_pdb_or_fasta(path):
        if PDB_EXT in path.suffixes:
            protein_seqs[path.name] = cloning.sequence_from_pdb(
                    path, chain=args['--chain'], ref=template_dna)

        if path.suffix in FASTA_EXT:
            protein_seqs.update(cloning.sequences_from_fasta(path))

    for path in args['<proteins>']:
        path = Path(path)

        if path.is_dir():
            for subpath in path.glob('*'):
                print(subpath)
                load_pdb_or_fasta(subpath)

        elif PDB_EXT in path.suffixes or path.suffix in FASTA_EXT:
            load_pdb_or_fasta(path)

        else:
            with path.open() as file:
                for line in file.readlines():
                    load_pdb_or_fasta(Path(line))


    # Do the reverse-translation:

    leading_seq = args['--leading-dna']
    trailing_seq = args['--trailing-dna']

    if args['--make-ytk-part']:
        leading_seq, trailing_seq = ytk.adaptors[args['--make-ytk-part']]

    try: restriction_sites = args['--restriction-sites'].split(',')
    except: restriction_sites = ()

    dna_seqs = {
            name: cloning.reverse_translate(
                protein_seq,
                template_dna=template_dna,
                leading_seq=leading_seq,
                trailing_seq=trailing_seq,
                forbidden_seqs=restriction_sites,
                manufacturer=args['--manufacturer'],
            )
            for name, protein_seq in protein_seqs.items()
    }

    # Output the results:

    if args['--output']:
        cloning.write_sequences(args['--output'], dna_seqs)
    else:
        for name, dna_seq in dna_seqs.items():
            print('>{}'.format(name))
            print(dna_seq)
