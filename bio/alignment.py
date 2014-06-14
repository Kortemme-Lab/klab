#!/usr/bin/python
# encoding: utf-8
"""
alignment.py
Higher-level alignment functionality which uses the clustalo module and the PyMOL PSE builder module.

Created by Shane O'Connor 2014.

Updated in June 2014: The classes are now more general, handling multiple PDB files rather than a pair of PDB files. The
plan should be to remove the specialized classes in favor of these more general classes.
"""

import sys
sys.path.insert(0, '../../..')

if __name__ == '__main__':
    sys.path.insert(0, '../..')

from tools import colortext
from tools.bio.pymol.psebuilder import BatchBuilder, PDBContainer
from tools.bio.pymol.scaffold_model_design import ScaffoldModelDesignBuilder
from tools.bio.pdb import PDB
from tools.bio.clustalo import SequenceAligner
from tools.fs.fsio import write_file


def match_pdb_chains(pdb1, pdb1_name, pdb2, pdb2_name, cut_off = 60.0, allow_multiple_matches = False, multiple_match_error_margin = 3.0):
    '''Aligns two PDB files, returning a mapping from the chains in pdb1 to the chains of pdb2.
       If allow_multiple_matches is False, we return the best match for each chain in pdb1 if a match exists. The return
        value is a dict mapping
            chain_id_in_pdb1 -> None or a list with a single tuple (chain_id_in_pdb_2, percentage_identity_score)
       where percentage_identity_score is a float. e.g. 'A' -> [('B', 100)]. We return a list to keep the return type
       consistent with the allow_multiple_matches case. Use the match_best_pdb_chains wrapper is you only want one match.

       If allow_multiple_matches is True, we return multiple matches for each chain in pdb1 if any matches exists. The return
        value is a dict mapping
            chain_id_in_pdb1 -> None or a list of tuples of the form (chain_id_in_pdb_2, percentage_identity_score)
       where percentage_identity_score is a float. multiple_match_error_margin is the amount of percentage identity difference
       from the best match that we allow for e.g. a chain may map to chain_id1_in_pdb2 with 78% identity and chain_id2_in_pdb2
       with 76% identity. If chain_id1_in_pdb2 is the best match and multiple_match_error_margin >= 2, chain_id2_in_pdb2 will
       also be returned.

       Parameters: pdb1 and pdb2 are PDB objects from tools.bio.pdb. pdb1_name and pdb2_name are strings describing the
        structures e.g. 'Model' and 'Scaffold'. cut_off is used in the matching to discard low-matching chains.
       '''

    pdb1_chains = pdb1.atom_sequences.keys()
    pdb2_chains = pdb2.atom_sequences.keys()

    sa = SequenceAligner()

    # If these assertions do not hold we will need to fix the logic below
    assert(pdb1_name.find(':') == -1)
    assert(pdb2_name.find(':') == -1)

    for c in pdb1_chains:
        sa.add_sequence('%s:%s' % (pdb1_name, c), str(pdb1.atom_sequences[c]))
    for c in pdb2_chains:
        sa.add_sequence('%s:%s' % (pdb2_name, c), str(pdb2.atom_sequences[c]))
    sa.align()

    chain_matches = dict.fromkeys(pdb1_chains, None)
    for c in pdb1_chains:
        best_matches_by_id = sa.get_best_matches_by_id('%s:%s' % (pdb1_name, c), cut_off = cut_off)
        if best_matches_by_id:
            t = []
            for k, v in best_matches_by_id.iteritems():
                if k.startswith(pdb2_name + ':'):
                    t.append((v, k))
            if t:
                # We may have multiple best matches here. Instead of just returning one
                if allow_multiple_matches:
                    best_matches = sorted(t)
                    best_match_identity = best_matches[0][0]
                    allowed_cutoff = max(cut_off, best_match_identity - multiple_match_error_margin)
                    chain_matches[c] = []
                    for best_match in best_matches:
                        if best_match[0] >= allowed_cutoff:
                            chain_matches[c].append((best_match[1].split(':')[1], best_match[0]))
                    assert(len(chain_matches[c]) > 0)
                else:
                    best_match = sorted(t)[0]
                    chain_matches[c] = [(best_match[1].split(':')[1], best_match[0])]

    return chain_matches


def match_best_pdb_chains(pdb1, pdb1_name, pdb2, pdb2_name, cut_off = 60.0):
    '''A wrapper function for match_pdb_chains. This function only takes the best match. The return
        value is a dict mapping
            chain_id_in_pdb1 -> None or a tuple (chain_id_in_pdb_2, percentage_identity_score)
       where percentage_identity_score is a float. e.g. 'A' -> ('B', 100).'''
    d = match_pdb_chains(pdb1, pdb1_name, pdb2, pdb2_name, cut_off = cut_off, allow_multiple_matches = False)
    for k, v in d.iteritems():
        if v:
            d[k] = v[0]
    return d


class SequenceAlignmentPrinter(object):

    def __init__(self, seq1_name, seq1_sequence, seq2_name, seq2_sequence):
        self.seq1_name = seq1_name
        self.seq1_sequence = seq1_sequence
        self.seq2_name = seq2_name
        self.seq2_sequence = seq2_sequence

    def to_lines(self, width = 80, reversed = False, line_separator = '\n'):
        s = []
        label_width = max(len(self.seq1_name), len(self.seq2_name))
        if label_width + 2 < width:
            header_1 = self.seq1_name.ljust(label_width + 2)
            header_2 = self.seq2_name.ljust(label_width + 2)

            num_residues_per_line = width - label_width
            seq1_sequence_str = str(self.seq1_sequence)
            seq2_sequence_str = str(self.seq2_sequence)

            for x in range(0, len(seq1_sequence_str), num_residues_per_line):
                if reversed:
                    s.append('%s  %s' % (header_2, seq2_sequence_str[x:x + num_residues_per_line]))
                    s.append('%s  %s' % (header_1, seq1_sequence_str[x:x + num_residues_per_line]))
                else:
                    s.append('%s  %s' % (header_1, seq1_sequence_str[x:x + num_residues_per_line]))
                    s.append('%s  %s' % (header_2, seq2_sequence_str[x:x + num_residues_per_line]))
        return line_separator.join(s)

class MultipleSequenceAlignmentPrinter(object):
    '''A generalized version of SequenceAlignmentPrinter which handles multiple sequences.'''

    def __init__(self, sequence_names, sequences):
        assert(len(sequence_names) == len(sequences) and len(sequence_names) > 1)
        assert(len(set(sequence_names)) == len(sequence_names)) # sequence_names must be a list of unique names

        # Make sure that the sequence lengths are all the same size
        sequence_lengths = map(len, sequences)
        assert(len(set(sequence_lengths)) == 1)
        self.sequence_length = sequence_lengths[0]
        self.label_width = max(map(len, sequence_names))

        self.sequence_names = sequence_names
        self.sequences = sequences

    def to_lines(self, width = 80, reversed = False, line_separator = '\n'):
        s = []

        sequences, sequence_names = None, None
        if reversed:
            sequences, sequence_names = self.sequences[::-1], self.sequence_names[::-1]
        else:
            sequences, sequence_names = self.sequences, self.sequence_names

        if self.label_width + 2 < width:

            headers = [sequence_name.ljust(self.label_width + 2) for sequence_name in sequence_names]
            num_residues_per_line = width - self.label_width
            sequence_strs = map(str, sequences)

            for x in range(0, self.sequence_length, num_residues_per_line):
                for y in range(len(sequence_strs)):
                    s.append('%s  %s' % (headers[y], sequence_strs[y][x:x + num_residues_per_line]))

        return line_separator.join(s)

class BasePDBChainMapper(object):
    def get_sequence_alignment_strings(self, reversed = True, width = 80, line_separator = '\n'):
        raise Exception('Implement this function.')
    def get_sequence_alignment_strings_as_html(self, reversed = True, width = 80, line_separator = '\n'):
        raise Exception('Implement this function.')

class PDBChainMapper(BasePDBChainMapper):
    '''Uses the match_pdb_chains function to map the chains of pdb1 to the chains of pdb2. The mapping member stores
        the mapping between chains when a mapping is found. The mapping_percentage_identity member stores how close the
        mapping was in terms of percentage identity.
    '''
    def __init__(self, pdb1, pdb1_name, pdb2, pdb2_name, cut_off = 60.0):
        raise Exception('Deprecate this class in favor of PipelinePDBChainMapper.')
        self.pdb1 = pdb1
        self.pdb2 = pdb2
        self.pdb1_name = pdb1_name
        self.pdb2_name = pdb2_name
        self.mapping = {}
        self.mapping_percentage_identity = {}

        # Match each chain in pdb1 to its best match in pdb2
        self.chain_matches = match_best_pdb_chains(pdb1, pdb1_name, pdb2, pdb2_name, cut_off = cut_off)
        for k, v in self.chain_matches.iteritems():
            if v:
                self.mapping[k] = v[0]
                self.mapping_percentage_identity[k] = v[1]

        self.pdb1_differing_residue_ids = []
        self.pdb2_differing_residue_ids = []
        self.residue_id_mapping = {}
        self._map_residues()

    @staticmethod
    def from_file_paths(pdb1_path, pdb1_name, pdb2_path, pdb2_name, cut_off = 60.0):
        pdb1 = PDB.from_filepath(pdb1_path)
        pdb2 = PDB.from_filepath(pdb2_path)
        return PDBChainMapper(pdb1, pdb1_name, pdb2, pdb2_name, cut_off = cut_off)

    def _map_residues(self):
        '''
        '''
        pdb1 = self.pdb1
        pdb2 = self.pdb2
        pdb1_name = self.pdb1_name
        pdb2_name = self.pdb2_name
        residue_id_mapping = {}
        pdb1_differing_residue_ids = []
        pdb2_differing_residue_ids = []
        for pdb1_chain, pdb2_chain in self.mapping.iteritems():
            residue_id_mapping[pdb1_chain] = {}

            # Get the mapping between the sequences
            # Note: sequences and mappings are 1-based following the UniProt convention
            sa = SequenceAligner()
            pdb1_sequence = pdb1.atom_sequences[pdb1_chain]
            pdb2_sequence = pdb2.atom_sequences[pdb2_chain]
            sa.add_sequence('%s:%s' % (pdb1_name, pdb1_chain), str(pdb1_sequence))
            sa.add_sequence('%s:%s' % (pdb2_name, pdb2_chain), str(pdb2_sequence))
            mapping, match_mapping = sa.get_residue_mapping()

            for pdb1_residue_index, pdb2_residue_index in mapping.iteritems():
                pdb1_residue_id = pdb1_sequence.order[pdb1_residue_index - 1] # order is a 0-based list
                pdb2_residue_id = pdb2_sequence.order[pdb2_residue_index - 1] # order is a 0-based list
                residue_id_mapping[pdb1_chain][pdb1_residue_id] = pdb2_residue_id

            # Determine which residues of each sequence differ between the sequences
            # We ignore leading and trailing residues from both sequences
            pdb1_residue_indices = mapping.keys()
            pdb2_residue_indices = mapping.values()
            differing_pdb1_indices = range(min(pdb1_residue_indices), max(pdb1_residue_indices) + 1)
            differing_pdb2_indices = range(min(pdb2_residue_indices), max(pdb2_residue_indices) + 1)
            for pdb1_residue_index, match_details in match_mapping.iteritems():
                if match_details.clustal == 1:
                    # the residues matched
                    differing_pdb1_indices.remove(pdb1_residue_index)
                    differing_pdb2_indices.remove(mapping[pdb1_residue_index])

            # Convert the different sequence indices into PDB residue IDs
            for idx in differing_pdb1_indices:
                pdb1_differing_residue_ids.append(pdb1_sequence.order[idx - 1])
            for idx in differing_pdb2_indices:
                pdb2_differing_residue_ids.append(pdb2_sequence.order[idx - 1])

        self.residue_id_mapping = residue_id_mapping
        self.pdb1_differing_residue_ids = sorted(pdb1_differing_residue_ids)
        self.pdb2_differing_residue_ids = sorted(pdb2_differing_residue_ids)

    def get_sequence_alignment_strings(self, reversed = True, width = 80, line_separator = '\n'):
        '''Returns one sequence alignment string for each chain mapping. Each line is a concatenation of lines of the
        specified width, separated by the specified line separator.'''
        pdb1 = self.pdb1
        pdb2 = self.pdb2
        pdb1_name = self.pdb1_name
        pdb2_name = self.pdb2_name
        alignment_strings = []
        for pdb1_chain, pdb2_chain in sorted(self.mapping.iteritems()):
            sa = SequenceAligner()
            pdb1_sequence = pdb1.atom_sequences[pdb1_chain]
            pdb2_sequence = pdb2.atom_sequences[pdb2_chain]
            sa.add_sequence('%s:%s' % (pdb1_name, pdb1_chain), str(pdb1_sequence))
            sa.add_sequence('%s:%s' % (pdb2_name, pdb2_chain), str(pdb2_sequence))
            sa.align()

            pdb1_alignment_str = sa._get_alignment_lines()['%s:%s' % (pdb1_name, pdb1_chain)]
            pdb2_alignment_str = sa._get_alignment_lines()['%s:%s' % (pdb2_name, pdb2_chain)]

            sap = SequenceAlignmentPrinter('%s:%s' % (pdb1_name, pdb1_chain), pdb1_alignment_str, '%s:%s' % (pdb2_name, pdb2_chain), pdb2_alignment_str)
            alignment_strings.append(sap.to_lines(reversed = reversed, width = width, line_separator = line_separator))

        return alignment_strings

    def get_sequence_alignment_strings_as_html(self, reversed = True, width = 80, line_separator = '\n'):
        alignment_strings = self.get_sequence_alignment_strings(reversed = reversed, width = width)
        html = []
        for alignment_string in alignment_strings:
            lines = alignment_string.split('\n')

            alignment_tokens = []
            for line in lines:
                tokens = line.split()
                assert(len(tokens) == 2)
                label_tokens = tokens[0].split(':')
                #alignment_html.append('<div class="sequence_alignment_line"><span>%s</span><span>%s</span><span>%s</span></div>' % (label_tokens[0], label_tokens[1], tokens[1]))
                #alignment_tokens.append('<div class="sequence_alignment_line"><span>%s</span><span>%s</span><span>%s</span></div>' % (label_tokens[0], label_tokens[1], tokens[1]))
                alignment_tokens.append([label_tokens[0], label_tokens[1], tokens[1]])

            if len(alignment_tokens) % 2 == 0:
                passed = True
                for x in range(0, len(alignment_tokens), 2):
                    if alignment_tokens[x][0] != 'Scaffold':
                        passed = False
                    if alignment_tokens[x+1][0] != 'Model':
                        passed = False
                for x in range(0, len(alignment_tokens), 2):
                    scaffold_residues = alignment_tokens[x][2]
                    model_residues = alignment_tokens[x+1][2]
                    if passed and (len(scaffold_residues) == len(model_residues)):
                        new_scaffold_string = []
                        new_model_string = []
                        for y in range(len(scaffold_residues)):
                            if scaffold_residues[y] == model_residues[y]:
                                new_scaffold_string.append(scaffold_residues[y])
                                new_model_string.append(model_residues[y])
                            else:
                                new_scaffold_string.append('<dd>%s</dd>' % scaffold_residues[y])
                                new_model_string.append('<dd>%s</dd>' % model_residues[y])
                        alignment_tokens[x][2] = ''.join(new_scaffold_string)
                        alignment_tokens[x+1][2] = ''.join(new_model_string)


            for trpl in alignment_tokens:
                html.append('<div class="sequence_alignment_line sequence_alignment_line_%s"><span>%s</span><span>%s</span><span>%s</span></div>' % (trpl[0], trpl[0], trpl[1], trpl[2]))

            html.append('<div class="sequence_alignment_chain_separator"></div>')

        if html:
            html.pop() # remove the last chain separator div
        return '\n'.join(html)


class MatchedChainList(object):
    '''A helper class to store a list of chains related to pdb_name:chain_id and their percentage identities.'''

    def __init__(self, pdb_name, chain_id):
        self.pdb_name = pdb_name
        self.chain_id = chain_id
        self.chain_list = []

    def add_chain(self, other_pdb_id, chain_id, percentage_identity):
        self.chain_list.append((percentage_identity, other_pdb_id, chain_id))
        self.chain_list = sorted(self.chain_list)

    def get_related_chains_ids(self, other_pdb_id):
        return [e[2] for e in self.chain_list if e[1] == other_pdb_id]

    def get_related_chains_ids_and_identities(self, other_pdb_id):
        return [(e[2], e[0]) for e in self.chain_list if e[1] == other_pdb_id]

    def __repr__(self):
        s = ['Matched chain list for %s:%s' % (self.pdb_name, self.chain_id)]
        if self.chain_list:
            for mtch in self.chain_list:
                s.append('\t%s:%s at %s%%' % (mtch[1], mtch[2], mtch[0]))
        else:
            s.append('No matches.')
        return '\n'.join(s)


class PipelinePDBChainMapper(BasePDBChainMapper):
    '''Similar to PDBChainMapper except this takes a list of PDB files which should be related in some way. The matching
       is done pointwise, matching all PDBs in the list to each other.
       This class is useful for a list of structures that are the result of a linear pipeline e.g. a scaffold structure (RCSB),
       a model structure (Rosetta), and a design structure (experimental result).

       The 'chain_mapping' member stores a mapping from a pair (pdb_name1, pdb_name2) to the mapping from chain IDs in pdb_name1 to
       a MatchedChainList object. This object can be used to return the list of chain IDs in pdb_name2 related to the
       respective chain in pdb_name1 based on sequence alignment. It can also be used to return the percentage identities
       for this alignment. The old mapping and mapping_percentage_identity members of this class can be built from this member
       e.g.
            self.mapping[('Scaffold', 'ExpStructure')] == self.get_chain_mapping('Scaffold', 'ExpStructure')

       The 'residue_id_mapping' member stores a mapping from a pair (pdb_name1, pdb_name2) to a mapping
            chains_of_pdb_name_1 -> residues of that chain -> list of corresponding residues in the corresponding chain of pdb_name2
       For example, using the homodimer 3MW0 for both Scaffold and ExpStructure:
        residue_id_mapping[('Scaffold', 'ExpStructure')]['A'] -> {'A 167 ': ['A 167 ', 'B 167 '], ...}
        residue_id_mapping[('Scaffold', 'ExpStructure')]['B'] -> {'B 167 ': ['A 167 ', 'B 167 '], ...}

       Objects of this class have a differing_residue_ids mapping which maps the pair (pdb_name1, pdb_name2) to the list
       of residues *in pdb_name1* that differ from those of pdb_name2. Note: there is some subtlety here in terms of
       direction. For example, take this artificial example. We take a homodimer 3MWO as the scaffold and a monomer 1BN1
       with identical sequence as the model. We mutate A110 in 1BN1. We then take 3MWO with a mutation on A106 as the design.
         chain_mapper = ScaffoldModelDesignChainMapper.from_file_contents(retrieve_pdb('3MWO'), retrieve_pdb('1BN1').replace('ASP A 110', 'ASN A 110'), retrieve_pdb('3MWO').replace('GLU A 106', 'GLN A 106'))
       differing_residue_ids then looks like this:
         ('Model', 'ExpStructure') = ['A 106 ', 'A 110 '] # In Model, A110 is a mutation, reverted in ExpStructure. In ExpStructure, A106 is a mutation.
         ('Model', 'Scaffold') = ['A 110 '] # In Model, A110 is a mutation.

         ('ExpStructure', 'Model') =  ['A 106 ', 'A 110 ', 'B 110 '] # In ExpStructure, A106 is a mutation. A110 and B110 are revertant mutations from the Model.
         ('ExpStructure', 'Scaffold') = ['A 106 '] # In ExpStructure, A106 is a mutation.

         ('Scaffold', 'ExpStructure') = ['A 106 ', 'B 106 '] # Note: In Scaffold, A106 is the wildtype which was mutated in ExpStructure. Since B106 also maps to A106, that is added to the list of differing residues.
         ('Scaffold', 'Model') = ['A 110 ', 'B 110 '] # In Scaffold, A110 and B110 are the wildtypes which was mutated in Model.
       There is a subtlety here - the differing residue ids from Scaffold to ExpStructure are A106 and B106 corresponding to the
       mutated A106 in the ExpStructure. However, the differing residue ids from ExpStructure to Scaffold has only one member - A106. This
       makes sense as it is the only mutation however this may not be the desired behavior - one may wish instead to close
       the list of residues over the relations mapping the residues between the structures i.e. to generate an equivalence
       relation from the relation described by the mappings Scaffold->ExpStructure and ExpStructure->Scaffold. If that were done, then
       ('ExpStructure', 'Scaffold') would be ['A 106 ', 'B 106 '] as ExpStructure:A106 -> {Scaffold:A106, Scaffold:B106} and
       Scaffold:B106 -> {ExpStructure:A106, ExpStructure:B106} so ExpStructure:A106 and ExpStructure:B106 are in the same equivalence class.
       '''

    # Constructors

    @staticmethod
    def from_file_paths(pdb_paths, pdb_names, cut_off = 60.0):
        pdbs = [PDB.from_filepath(pdb_path) for pdb_path in pdb_paths]
        return PipelinePDBChainMapper(pdbs, pdb_names, cut_off = cut_off)


    def __init__(self, pdbs, pdb_names, cut_off = 60.0):

        assert(len(pdbs) == len(pdb_names) and len(pdbs) > 1)
        assert(len(set(pdb_names)) == len(pdb_names)) # pdb_names must be a list of unique names

        self.pdbs = pdbs
        self.pdb_names = pdb_names

        self.pdb_name_to_structure_mapping = {}
        for x in range(len(pdb_names)):
            self.pdb_name_to_structure_mapping[pdb_names[x]] = pdbs[x]

        # differing_residue_ids is a mapping from (pdb_name1, pdb_name2) to the list of residues *in pdb_name1* that differ from those of pdb_name2
        self.differing_residue_ids = {}
        self.chain_mapping = {}

        # For each pair of adjacent PDB files in the list, match each chain in the first pdb to its best match in the second pdb
        for x in range(len(pdbs) - 1):
            for y in range(x + 1, len(pdbs)):
                pdb1, pdb2 = pdbs[x], pdbs[y]
                pdb1_name, pdb2_name = pdb_names[x], pdb_names[y]

                mapping_key = (pdb1_name, pdb2_name)
                self.chain_mapping[mapping_key] = {}
                self.differing_residue_ids[mapping_key] = {}

                # To allow for X cases, we allow the matcher to return multiple matches
                # An artificial example X case would be 3MWO -> 1BN1 -> 3MWO where 3MWO:A and 3MWO:B both map to 1BN1:A
                # In this case, we would like 1BN1:A to map to both 3MWO:A and 3MWO:B.
                chain_matches = match_pdb_chains(pdb1, pdb1_name, pdb2, pdb2_name, cut_off = cut_off, allow_multiple_matches = True, multiple_match_error_margin = 3.0)
                for pdb1_chain_id, list_of_matches in chain_matches.iteritems():
                    if list_of_matches:
                        mcl = MatchedChainList(pdb1_name, pdb1_chain_id)
                        for l in list_of_matches:
                            mcl.add_chain(pdb2_name, l[0], l[1])
                        self.chain_mapping[mapping_key][pdb1_chain_id] = mcl

                # todo: We could create the reverse entry from the results above which would be more efficient (match_pdb_chains
                # performs a sequence alignment) but I will just repeat the logic here for now.
                mapping_key = (pdb2_name, pdb1_name)
                self.chain_mapping[mapping_key] = {}
                self.differing_residue_ids[mapping_key] = {}

                chain_matches = match_pdb_chains(pdb2, pdb2_name, pdb1, pdb1_name, cut_off = cut_off, allow_multiple_matches = True, multiple_match_error_margin = 3.0)
                for pdb2_chain_id, list_of_matches in chain_matches.iteritems():
                    if list_of_matches:
                        mcl = MatchedChainList(pdb2_name, pdb2_chain_id)
                        for l in list_of_matches:
                            mcl.add_chain(pdb1_name, l[0], l[1])
                    self.chain_mapping[mapping_key][pdb2_chain_id] = mcl

        self.residue_id_mapping = {}
        self._map_residues()


    # Private functions


    def _map_residues(self):
        '''For each pair of PDB files, match the residues of the first chain to the residues of the second chain.

            Note: we do a lot of repeated work here. Some of the lookups e.g. atom_sequences here could be cached.
            If the sequences are expected to be similar of have lots of repeats, we could use a list of unique sequences
            as equivalence class representatives and then duplicate the matching for the other equivalent sequences.'''

        pdbs = self.pdbs
        pdb_names = self.pdb_names

        for x in range(len(pdbs) - 1):
            for y in range(x + 1, len(pdbs)):
                pdb1, pdb2 = pdbs[x], pdbs[y]
                pdb1_name, pdb2_name = pdb_names[x], pdb_names[y]
                mapping_key = (pdb1_name, pdb2_name)
                reverse_mapping_key = mapping_key[::-1]

                residue_id_mapping = {}
                pdb1_differing_residue_ids = []
                pdb2_differing_residue_ids = []

                for pdb1_chain, pdb2_chains in self.get_chain_mapping(mapping_key[0], mapping_key[1]).iteritems():
                #for pdb1_chain, pdb2_chain in self.chain_mapping[mapping_key].iteritems():

                    residue_id_mapping[pdb1_chain] = {}
                    pdb1_sequence = pdb1.atom_sequences[pdb1_chain]
                    for pdb2_chain in pdb2_chains:
                        # Get the mapping between the sequences
                        # Note: sequences and mappings are 1-based following the UniProt convention
                        sa = SequenceAligner()
                        pdb2_sequence = pdb2.atom_sequences[pdb2_chain]
                        sa.add_sequence('%s:%s' % (pdb1_name, pdb1_chain), str(pdb1_sequence))
                        sa.add_sequence('%s:%s' % (pdb2_name, pdb2_chain), str(pdb2_sequence))
                        mapping, match_mapping = sa.get_residue_mapping()

                        for pdb1_residue_index, pdb2_residue_index in mapping.iteritems():
                            pdb1_residue_id = pdb1_sequence.order[pdb1_residue_index - 1] # order is a 0-based list
                            pdb2_residue_id = pdb2_sequence.order[pdb2_residue_index - 1] # order is a 0-based list

                            # We store a list of corresponding residues i.e. if pdb1_chain matches pdb2_chain_1 and pdb2_chain_2
                            # then we may map a residue in pdb1_chain to a residue in each of those chains
                            residue_id_mapping[pdb1_chain][pdb1_residue_id] = residue_id_mapping[pdb1_chain].get(pdb1_residue_id, [])
                            residue_id_mapping[pdb1_chain][pdb1_residue_id].append(pdb2_residue_id)

                        # Determine which residues of each sequence differ between the sequences
                        # We ignore leading and trailing residues from both sequences
                        pdb1_residue_indices = mapping.keys()
                        pdb2_residue_indices = mapping.values()
                        differing_pdb1_indices = range(min(pdb1_residue_indices), max(pdb1_residue_indices) + 1)
                        differing_pdb2_indices = range(min(pdb2_residue_indices), max(pdb2_residue_indices) + 1)
                        for pdb1_residue_index, match_details in match_mapping.iteritems():
                            if match_details.clustal == 1:
                                # The residues matched
                                differing_pdb1_indices.remove(pdb1_residue_index)
                                differing_pdb2_indices.remove(mapping[pdb1_residue_index])

                        # Convert the different sequence indices into PDB residue IDs
                        for idx in differing_pdb1_indices:
                            pdb1_differing_residue_ids.append(pdb1_sequence.order[idx - 1])
                        for idx in differing_pdb2_indices:
                            pdb2_differing_residue_ids.append(pdb2_sequence.order[idx - 1])

                self.residue_id_mapping[mapping_key] = residue_id_mapping
                self.differing_residue_ids[mapping_key] = pdb1_differing_residue_ids
                self.differing_residue_ids[reverse_mapping_key] = pdb2_differing_residue_ids

        for k, v in sorted(self.differing_residue_ids.iteritems()):
            self.differing_residue_ids[k] = sorted(set(v)) # the list of residues may not be unique in general so we make it unique here


    # Public functions


    def get_chain_mapping(self, pdb_name1, pdb_name2):
        '''This replaces the old mapping member by constructing it from self.chain_mapping. This function returns a mapping from
        chain IDs in pdb_name1 to chain IDs in pdb_name2.'''
        d = {}
        for pdb1_chain_id, matched_chain_list in self.chain_mapping[(pdb_name1, pdb_name2)].iteritems():
            d[pdb1_chain_id] = matched_chain_list.get_related_chains_ids(pdb_name2)
        return d


    def get_differing_residue_ids(self, pdb_name, pdb_list):
        '''Returns a list of residues in pdb_name which differ from the pdbs corresponding to the names in pdb_list.'''

        assert(pdb_name in self.pdb_names)
        assert(set(pdb_list).intersection(set(self.pdb_names)) == set(pdb_list)) # the names in pdb_list must be in pdb_names

        differing_residue_ids = set()
        for other_pdb in pdb_list:
            differing_residue_ids = differing_residue_ids.union(set(self.differing_residue_ids[(pdb_name, other_pdb)]))

        return sorted(differing_residue_ids)


    def get_sequence_alignment_strings(self, pdb_list, reversed = True, width = 80, line_separator = '\n'):
        '''Takes a list of pdb names e.g. ['Model', 'Scaffold', ...] with which the object was created.
            Using the first element of this list as a base, get the sequence alignments with chains in other members
            of the list. For simplicity, if a chain in the first PDB matches multiple chains in another PDB, we only
            return the alignment for one of the chains.

            Returns one sequence alignment string for each chain mapping. Each line is a concatenation of lines of the
            specified width, separated by the specified line separator.'''

        assert(len(set(pdb_list)) == len(pdb_list) and (len(pdb_list) > 1))
        assert(set(pdb_list).intersection(set(self.pdb_names)) == set(pdb_list))

        primary_pdb = self.pdb_name_to_structure_mapping[pdb_list[0]]
        primary_pdb_name = pdb_list[0]
        primary_pdb_chains = sorted(primary_pdb.chain_atoms.keys())

        alignment_strings = []
        for primary_pdb_chain in primary_pdb_chains:

            sa = SequenceAligner()

            # Add the primary PDB's sequence for the chain
            primary_pdb_sequence = primary_pdb.atom_sequences[primary_pdb_chain]
            sa.add_sequence('%s:%s' % (primary_pdb_name, primary_pdb_chain), str(primary_pdb_sequence))

            for other_pdb_name in pdb_list[1:]:
                other_pdb = self.pdb_name_to_structure_mapping[other_pdb_name]

                other_chains = self.get_chain_mapping(primary_pdb_name, other_pdb_name).get(primary_pdb_chain)
                #other_chain = self.mapping[(primary_pdb_name, other_pdb_name)].get(primary_pdb_chain)
                if other_chains:
                    other_chain = sorted(other_chains)[0]
                    other_pdb_sequence = other_pdb.atom_sequences[other_chain]
                    sa.add_sequence('%s:%s' % (other_pdb_name, other_chain), str(other_pdb_sequence))

            if len(sa.records) > 1:
                # If there are no corresponding sequences in any other PDB, do not return the non-alignment
                sa.align()

                #pdb1_alignment_str = sa._get_alignment_lines()['%s:%s' % (primary_pdb_name, pdb1_chain)]
                #pdb2_alignment_str = sa._get_alignment_lines()['%s:%s' % (pdb2_name, pdb2_chain)]

                sequence_names, sequences = [], []
                sequence_names.append('%s:%s' % (primary_pdb_name, primary_pdb_chain))
                sequences.append(sa._get_alignment_lines()['%s:%s' % (primary_pdb_name, primary_pdb_chain)])
                for other_pdb_name in pdb_list[1:]:
                    #other_chain = self.mapping[(primary_pdb_name, other_pdb_name)].get(primary_pdb_chain)
                    other_chains = self.get_chain_mapping(primary_pdb_name, other_pdb_name).get(primary_pdb_chain)
                    other_chain = sorted(other_chains)[0]
                    sequence_names.append('%s:%s' % (other_pdb_name, other_chain))
                    sequences.append(sa._get_alignment_lines()['%s:%s' % (other_pdb_name, other_chain)])

                sap = MultipleSequenceAlignmentPrinter(sequence_names, sequences)
                alignment_strings.append(sap.to_lines(reversed = reversed, width = width, line_separator = line_separator))

        return alignment_strings

    def get_sequence_alignment_strings_as_html(self, pdb_list, reversed = True, width = 80, line_separator = '\n'):
        alignment_strings = self.get_sequence_alignment_strings(pdb_list, reversed = reversed, width = width)
        html = []
        for alignment_string in alignment_strings:
            lines = alignment_string.split('\n')

            alignment_tokens = []
            for line in lines:
                tokens = line.split()
                assert(len(tokens) == 2)
                label_tokens = tokens[0].split(':')
                #alignment_html.append('<div class="sequence_alignment_line"><span>%s</span><span>%s</span><span>%s</span></div>' % (label_tokens[0], label_tokens[1], tokens[1]))
                #alignment_tokens.append('<div class="sequence_alignment_line"><span>%s</span><span>%s</span><span>%s</span></div>' % (label_tokens[0], label_tokens[1], tokens[1]))
                alignment_tokens.append([label_tokens[0], label_tokens[1], tokens[1]])

            if reversed:
                pdb_list = pdb_list[::-1]

            if len(alignment_tokens) % len(pdb_list) == 0:

                passed = True
                for x in range(0, len(alignment_tokens), len(pdb_list)):
                    for y in range(0, len(pdb_list)):
                        if alignment_tokens[x + y][0] != pdb_list[y]:
                            passed = False

                for x in range(0, len(alignment_tokens), len(pdb_list)):

                    residue_sublist = []
                    for y in range(0, len(pdb_list)):
                        residue_sublist.append(alignment_tokens[x + y][2])

                    #scaffold_residues = alignment_tokens[x][2]
                    #model_residues = alignment_tokens[x+1][2]
                    if passed and (len(set(map(len, residue_sublist))) == 1): # check that the lengths of all subsequences are the same
                        #new_scaffold_string = []
                        #new_model_string = []
                        residue_substrings = []
                        for y in range(0, len(pdb_list)):
                            residue_substrings.append([])

                        for z in range(len(residue_sublist[0])):
                            residues = set([residue_sublist[y][z] for y in range(0, len(pdb_list))])

                            if len(residues) == 1:
                                # all residues are the same
                                for y in range(0, len(pdb_list)):
                                    residue_substrings[y].append(residue_sublist[y][z])
                            else:
                                for y in range(0, len(pdb_list)):
                                    residue_substrings[y].append('<dd>%s</dd>' % residue_sublist[y][z])

                        for y in range(0, len(pdb_list)):
                            alignment_tokens[x + y][2] = ''.join(residue_substrings[y])

            for trpl in alignment_tokens:
                html.append('<div class="sequence_alignment_line sequence_alignment_line_%s"><span>%s</span><span>%s</span><span>%s</span></div>' % (trpl[0], trpl[0], trpl[1], trpl[2]))

            html.append('<div class="sequence_alignment_chain_separator"></div>')

        if html:
            html.pop() # remove the last chain separator div
        return '\n'.join(html)


class ScaffoldModelChainMapper(PDBChainMapper):
    '''A convenience class for the special case where we are mapping specifically from a model structure to a scaffold structure.'''
    def __init__(self, scaffold_pdb, model_pdb, cut_off = 60.0):
        raise Exception('Rewrite this class to use PipelinePDBChainMapper.')
        self.model_pdb = model_pdb
        self.scaffold_pdb = scaffold_pdb
        super(ScaffoldModelChainMapper, self).__init__(model_pdb, 'Model', scaffold_pdb, 'Scaffold', cut_off)

    @staticmethod
    def from_file_paths(scaffold_pdb_path, model_pdb_path, cut_off = 60.0):
        scaffold_pdb = PDB.from_filepath(scaffold_pdb_path)
        model_pdb = PDB.from_filepath(model_pdb_path)
        return ScaffoldModelChainMapper(scaffold_pdb, model_pdb, cut_off = cut_off)

    @staticmethod
    def from_file_contents(scaffold_pdb_contents, model_pdb_contents, cut_off = 60.0):
        scaffold_pdb = PDB(scaffold_pdb_contents)
        model_pdb = PDB(model_pdb_contents)
        return ScaffoldModelChainMapper(scaffold_pdb, model_pdb, cut_off = cut_off)

    def get_differing_model_residue_ids(self):
        return self.pdb1_differing_residue_ids

    def get_differing_scaffold_residue_ids(self):
        return self.pdb2_differing_residue_ids

    def generate_pymol_session(self, design_pdb = None, pymol_executable = None, settings = {}):
        b = BatchBuilder(pymol_executable = pymol_executable)

        structures_list = [
            ('Scaffold', self.scaffold_pdb.pdb_content, self.get_differing_scaffold_residue_ids()),
            ('Model', self.model_pdb.pdb_content, self.get_differing_model_residue_ids()),
        ]

        if design_pdb:
            structures_list.append(('ExpStructure', design_pdb.pdb_content, self.get_differing_scaffold_residue_ids()))

        PSE_files = b.run(ScaffoldModelDesignBuilder, [PDBContainer.from_content_triple(structures_list)], settings = settings)
        return PSE_files[0]


class ScaffoldModelDesignChainMapper(PipelinePDBChainMapper):
    '''A convenience class for the special case where we are mapping specifically from a model structure to a scaffold structure and a design structure.'''
    def __init__(self, scaffold_pdb, model_pdb, design_pdb, cut_off = 60.0):
        self.scaffold_pdb = scaffold_pdb
        self.model_pdb = model_pdb
        self.design_pdb = design_pdb
        super(ScaffoldModelDesignChainMapper, self).__init__([scaffold_pdb, model_pdb, design_pdb], ['Scaffold', 'Model', 'ExpStructure'], cut_off)

    @staticmethod
    def from_file_paths(scaffold_pdb_path, model_pdb_path, design_pdb_path, cut_off = 60.0):
        scaffold_pdb = PDB.from_filepath(scaffold_pdb_path)
        model_pdb = PDB.from_filepath(model_pdb_path)
        design_pdb = PDB.from_filepath(design_pdb_path)
        return ScaffoldModelDesignChainMapper(scaffold_pdb, model_pdb, design_pdb, cut_off = cut_off)

    @staticmethod
    def from_file_contents(scaffold_pdb_contents, model_pdb_contents, design_pdb_contents, cut_off = 60.0):
        scaffold_pdb = PDB(scaffold_pdb_contents)
        model_pdb = PDB(model_pdb_contents)
        design_pdb = PDB(design_pdb_contents)
        return ScaffoldModelDesignChainMapper(scaffold_pdb, model_pdb, design_pdb, cut_off = cut_off)

    def get_differing_model_residue_ids(self):
        return self.get_differing_residue_ids('Model', ['Scaffold', 'ExpStructure'])

    def get_differing_scaffold_residue_ids(self):
        return self.get_differing_residue_ids('Scaffold', ['Model', 'ExpStructure'])

    def get_differing_design_residue_ids(self):
        return self.get_differing_residue_ids('ExpStructure', ['Scaffold', 'Model'])

    def generate_pymol_session(self, pymol_executable = 'pymol', settings = {}):
        ''' Generates the PyMOL session for the scaffold, model, and design structures.
            Returns this session and the script which generated it.'''
        b = BatchBuilder(pymol_executable = pymol_executable)

        structures_list = [
            ('Scaffold', self.scaffold_pdb.pdb_content, self.get_differing_scaffold_residue_ids()),
            ('Model', self.model_pdb.pdb_content, self.get_differing_model_residue_ids()),
            ('ExpStructure', self.design_pdb.pdb_content, self.get_differing_design_residue_ids ()),
        ]

        PSE_files = b.run(ScaffoldModelDesignBuilder, [PDBContainer.from_content_triple(structures_list)], settings = settings)

        return PSE_files[0], b.PSE_scripts[0]


if __name__ == '__main__':
    from tools.fs.fsio import read_file

    from rcsb import retrieve_pdb

    colortext.message('match_pdb_chains: 3MW0 -> 1BN1')
    print(match_pdb_chains(PDB(retrieve_pdb('3MWO')), '3MWO', PDB(retrieve_pdb('1BN1')), '1BN1', cut_off = 60.0, allow_multiple_matches = True))

    colortext.warning('match_pdb_chains: 1BN1 -> 3MW0')
    print(match_pdb_chains(PDB(retrieve_pdb('1BN1')), '1BN1', PDB(retrieve_pdb('3MWO')), '3MWO', cut_off = 60.0, allow_multiple_matches = True))

    if False:
        # Example of how to create a mapper from file paths
        chain_mapper = ScaffoldModelChainMapper.from_file_paths('../.testdata/1z1s_DIG5_scaffold.pdb', '../.testdata/DIG5_1_model.pdb')

        # Example of how to create a mapper from file contents
        chain_mapper = ScaffoldModelChainMapper.from_file_contents(read_file('../.testdata/1z1s_DIG5_scaffold.pdb'), read_file('../.testdata/DIG5_1_model.pdb'))

        # 3MWO -> 1BN1 test case (3MWO:A and 3MWO:B map to 1BN1:A)
        chain_mapper = ScaffoldModelDesignChainMapper.from_file_contents(retrieve_pdb('3MWO'), retrieve_pdb('1BN1').replace('ASP A 110', 'ASN A 110'), retrieve_pdb('3MWO').replace('GLU A 106', 'GLN A 106'))

    # Example of how to create a mapper from file contents
    chain_mapper = ScaffoldModelDesignChainMapper.from_file_contents(read_file('../.testdata/1x42_BH3_scaffold.pdb'), read_file('../.testdata/1x42_foldit2_BH32_design.pdb'), read_file('../.testdata/3U26.pdb'))

    colortext.message('''chain_mapper.get_differing_residue_ids('ExpStructure', ['Model', 'Scaffold'])''')
    print(chain_mapper.get_differing_residue_ids('ExpStructure', ['Model', 'Scaffold']))

    colortext.message('''chain_mapper.get_differing_model_residue_ids()''')
    print(chain_mapper.get_differing_model_residue_ids())

    colortext.message('''chain_mapper.get_differing_scaffold_residue_ids()''')
    print(chain_mapper.get_differing_scaffold_residue_ids())

    colortext.message('''\nchain_mapper.chain_mapping''')
    print(chain_mapper.chain_mapping)

    colortext.message('''\nresidue_id_mapping''')
    print(chain_mapper.residue_id_mapping)

    # Example of how to get residue -> residue mapping
    for chain_id, mapping in sorted(chain_mapper.residue_id_mapping.iteritems()):
        for model_res, scaffold_res in sorted(mapping.iteritems()):
            print("\t'%s' -> '%s'" % (model_res, scaffold_res))

    # Example of how to list the PDB residue IDs for the positions in the model which differ
    colortext.message('Residues IDs for the residues which differ in the model.')
    print(chain_mapper.get_differing_model_residue_ids())

    # Example of how to list the PDB residue IDs for the positions in the scaffold which differ
    colortext.message('Residues IDs for the residues which differ in the scaffold.')
    print(chain_mapper.get_differing_scaffold_residue_ids())

    # Example of how to print out a plaintext sequence alignment
    colortext.warning('Sequence alignment - plain formatting, width = 120.')
    print('\n\n'.join(chain_mapper.get_sequence_alignment_strings(['Model', 'Scaffold', 'ExpStructure'], width = 120)))

    # Example of how to print out a HTML formatted alignment. This output would require CSS for an appropriate presentation.
    colortext.warning('Sequence alignment - HTML formatting, width = 100.')
    colortext.message(chain_mapper.get_sequence_alignment_strings_as_html(['Model', 'Scaffold', 'ExpStructure'], width = 100))

    # Example of how to generate a PyMOL session
    PSE_file, PSE_script = chain_mapper.generate_pymol_session(pymol_executable = 'pymol', settings = {'background-color' : 'black'})
    if PSE_file:
        print('Length of PSE file: %d' % len(PSE_file))
    else:
        print('No PSE file was generated.')

    print(PSE_script)
    write_file('alignment_test.pse', PSE_file, ftype = 'wb')

