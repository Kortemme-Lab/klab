#!/usr/bin/python
# encoding: utf-8
"""
fasta.py
Functions dealing with FASTA files. This will probably deprecate the FASTA code in rcsb.py.

Created by Shane O'Connor 2013
"""

import os
from httplib import HTTPConnection

if __name__ == '__main__':
    import sys
    sys.path.insert(0, '../..')

from klab import colortext
from klab.fs.fsio import read_file, write_file
import rcsb
from basics import Sequence

visible_colors = [
    'lightblue',
    'lightgreen',
    'yellow',
    'pink',
    'cyan',
    'lightpurple',
    'white',
    'aqua',
    'green',
    'orange',
    'purple',
    'grey',
    'silver',
    ]

class FASTA(dict):
    ''' This class may replace the one in rcsb.py. I am trying to make the class more generally useful.

        This class inherits from dict. This lets us use some useful shortcuts e.g.
           f = FASTA.retrieve('1A2C', cache_dir = '~/temp')
           print(f['1A2C']['I'])
        will print the sequence for chain I. We index by both the PDB ID and chain ID as FASTA files could be
        merged and chain letters may not be unique identifiers.

        When you print the object, the chains are color-coded such that chains with the same sequence have the same color.
    '''

    fasta_chain_header_ = "|PDBID|CHAIN|SEQUENCE"

    def __init__(self, fasta_contents, strict = True, *args, **kw):
        super(FASTA,self).__init__(*args, **kw)
        self.fasta_contents = fasta_contents
        self.strict = strict
        self.itemlist = super(FASTA,self).keys()
        self.unique_sequences = {}
        self.sequences = []
        self.sequence_string_length = 120
        self._parse(fasta_contents)
        self._find_identical_sequences()

    def replace_sequence(self, pdb_ID, chain_id, replacement_sequence):
        '''Replaces a sequence with another. Typically not useful but I use it in the ResidueRelatrix to make sure that the FASTA and SEQRES sequences match.'''
        old_sequences = self.sequences
        old_unique_sequences = self.unique_sequences
        self.sequences = []
        self.unique_sequences = {}
        for s in old_sequences:
            if s[0] == pdb_ID and s[1] == chain_id:
                self._add_sequence(pdb_ID, chain_id, replacement_sequence)
            else:
                self._add_sequence(s[0], s[1], s[2])

        self._find_identical_sequences()

    def __add__(self, other):
        return FASTA("\n".join([self.fasta_contents, other.fasta_contents]))

    @staticmethod
    def combine(pdb_ids, cache_dir = None):
        if pdb_ids:
            FASTAs = [FASTA.retrieve(pdb_id, cache_dir) for pdb_id in pdb_ids]
            f = FASTAs[0]
            for x in range(1, len(FASTAs)):
                f = f + FASTAs[x]
            return f
        return None

    @staticmethod
    def retrieve(pdb_id, cache_dir = None, bio_cache = None):
        '''Creates a FASTA object by using a cached copy of the file if it exists or by retrieving the file from the RCSB.'''

        pdb_id = pdb_id.upper()

        if bio_cache:
            return FASTA(bio_cache.get_fasta_contents(pdb_id))

        # Check to see whether we have a cached copy
        if cache_dir:
            filename = os.path.join(cache_dir, "%s.fasta" % pdb_id)
            if os.path.exists(filename):
                return FASTA(read_file(filename))
            else:
                filename += ".txt"
                if os.path.exists(filename):
                    return FASTA(read_file(filename))

        # Get a copy from the RCSB
        contents = rcsb.retrieve_fasta(pdb_id)

        # Create a cached copy if appropriate
        if cache_dir:
            write_file(os.path.join(cache_dir, "%s.fasta" % pdb_id), contents)

        # Return the object
        return FASTA(contents)

    ### Private methods

    def _parse(self, fasta_contents):
        sequences = []
        chains = [c for c in fasta_contents.split(">") if c]
        for c in chains:
            if self.strict:
                assert(c[4:5] == ":")
                assert(c[6:].startswith(FASTA.fasta_chain_header_))
                self._add_sequence(c[0:4], c[5:6], c[6 + len(FASTA.fasta_chain_header_):].replace("\n","").strip())
            else:
                lines = c.split('\n')
                header = lines[0]
                sequence = ''.join(lines[1:]).replace("\n","").strip()
                tokens = header.split('|')
                pdbID, chain = tokens[0], ' '
                if len(tokens) > 1 and len(tokens[1]) == 1:
                    chain = tokens[1]
                self._add_sequence(pdbID, chain, sequence)


    def _add_sequence(self, pdbID, chainID, sequence):
        '''This is a 'private' function. If you call it directly, call _find_identical_sequences() afterwards to update identical_sequences.'''
        pdbID = pdbID.upper()
        self[pdbID] = self.get(pdbID, {})
        self[pdbID][chainID] = sequence
        self.sequences.append((pdbID, chainID, sequence))
        if not self.unique_sequences.get(sequence):
            self.unique_sequences[sequence] = visible_colors[len(self.unique_sequences) % len(visible_colors)]
        self.identical_sequences = None

    def _find_identical_sequences(self):
        ''' Stores the identical sequences in a map with the structure pdb_id -> chain_id -> List(identical chains)
            where the identical chains have the format 'pdb_id:chain_id'
            e.g. for 1A2P, we get {'1A2P': {'A': ['1A2P:B', '1A2P:C'], 'C': ['1A2P:A', '1A2P:B'], 'B': ['1A2P:A', '1A2P:C']}}
        '''

        sequences = self.sequences
        identical_sequences = {}
        numseq = len(self.sequences)
        for x in range(numseq):
            for y in range(x + 1, numseq):
                pdbID1 = sequences[x][0]
                pdbID2 = sequences[y][0]
                chain1 = sequences[x][1]
                chain2 = sequences[y][1]
                if sequences[x][2] == sequences[y][2]:
                    identical_sequences[pdbID1] = identical_sequences.get(pdbID1, {})
                    identical_sequences[pdbID1][chain1]=identical_sequences[pdbID1].get(chain1, [])
                    identical_sequences[pdbID1][chain1].append("%s:%s" % (pdbID2, chain2))
                    identical_sequences[pdbID2] = identical_sequences.get(pdbID2, {})
                    identical_sequences[pdbID2][chain2]=identical_sequences[pdbID2].get(chain2, [])
                    identical_sequences[pdbID2][chain2].append("%s:%s" % (pdbID1, chain1))
        self.identical_sequences = identical_sequences

    ### Public methods
    def get_sequences(self, pdb_id = None):
        '''Create Sequence objects for each FASTA sequence.'''
        sequences = {}
        if pdb_id:
            for chain_id, sequence in self.get(pdb_id, {}).iteritems():
                sequences[chain_id] = Sequence.from_sequence(chain_id, sequence)
        else:
            for pdb_id, v in self.iteritems():
                sequences[pdb_id] = {}
                for chain_id, sequence in v.iteritems():
                    sequences[pdb_id][chain_id] = Sequence.from_sequence(chain_id, sequence)
        return sequences

    def get_number_of_unique_sequences(self):
        return len(self.unique_sequences)

    def get_chain_ids(self, pdb_id = None, safe_call = False):
        '''If the FASTA file only has one PDB ID, pdb_id does not need to be specified. Otherwise, the list of chains identifiers for pdb_id is returned.'''

        if pdb_id == None and len(self.keys()) == 1:
            return self[self.keys()[0]].keys()

        pdbID = pdbID.upper()
        if not self.get(pdbID):
            if not safe_call:
                raise Exception("FASTA object does not contain sequences for PDB %s." % pdbID)
            else:
                return []
        return self[pdbID].keys()

    def match(self, other):
        ''' This is a noisy terminal-printing function at present since there is no need to make it a proper API function.'''
        colortext.message("FASTA Match")
        for frompdbID, fromchains in sorted(self.iteritems()):
            matched_pdbs = {}
            matched_chains = {}
            for fromchain, fromsequence in fromchains.iteritems():
                for topdbID, tochains in other.iteritems():
                    for tochain, tosequence in tochains.iteritems():
                        if fromsequence == tosequence:
                            matched_pdbs[topdbID] = matched_pdbs.get(topdbID, set())
                            matched_pdbs[topdbID].add(fromchain)
                            matched_chains[fromchain] = matched_chains.get(fromchain, [])
                            matched_chains[fromchain].append((topdbID, tochain))
            foundmatches = []
            colortext.printf("  %s" % frompdbID, color="silver")
            for mpdbID, mchains in matched_pdbs.iteritems():
                if mchains == set(fromchains.keys()):
                    foundmatches.append(mpdbID)
                    colortext.printf("  PDB %s matched PDB %s on all chains" % (mpdbID, frompdbID), color="white")
            if foundmatches:
                for fromchain, fromsequence in fromchains.iteritems():
                    colortext.printf("    %s" % (fromchain), color = "silver")
                    colortext.printf("      %s" % (fromsequence), color = self.unique_sequences[fromsequence])
                    mstr = []
                    for mchain in matched_chains[fromchain]:
                        if mchain[0] in foundmatches:
                            mstr.append("%s chain %s" % (mchain[0], mchain[1]))
                    colortext.printf("	  Matches: %s" % ", ".join(mstr))
            else:
                colortext.error("    No matches found.")

    def __repr__(self):
        splitsize = self.sequence_string_length
        self._find_identical_sequences()
        identical_sequences = self.identical_sequences
        s = []
        s.append(colortext.make("FASTA: Contains these PDB IDs - %s" % ", ".join(self.keys()), color="green"))
        s.append("Number of unique sequences : %d" % len(self.unique_sequences))
        s.append("Chains:")
        for pdbID, chains_dict in sorted(self.iteritems()):
            s.append("  %s" % pdbID)
            for chainID, sequence in chains_dict.iteritems():
                s.append("    %s" % chainID)
                color = self.unique_sequences[sequence]
                split_sequence = [sequence[i:i+splitsize] for i in range(0, len(sequence), splitsize)]
                for seqpart in split_sequence:
                    s.append(colortext.make("      %s" % seqpart, color=color))
                if identical_sequences.get(pdbID) and identical_sequences[pdbID].get(chainID):
                    iseqas = identical_sequences[pdbID][chainID]
                    s.append("	  Identical sequences: %s" % ", ".join(iseqas))

        return "\n".join(s)

if __name__ == '__main__':
    f = FASTA.retrieve('1A2P', cache_dir = '/tmp')
    g = FASTA.retrieve('1A2C', cache_dir = '/tmp')
    h = FASTA.retrieve('3U80', cache_dir = '/tmp')
    i = FASTA.retrieve('3U8O', cache_dir = '/tmp')
    print(f+g+h+i)

    fastas = FASTA.combine(['1A2P', '1A2C', '3U80', '3U8O'], cache_dir = '/tmp')
    print(fastas)