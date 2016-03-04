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
import pprint

if __name__ == '__main__':
    sys.path.insert(0, '../..')

from klab import colortext
from klab.bio.pymolmod.psebuilder import BatchBuilder, PDBContainer
from klab.bio.pymolmod.colors import PyMOLStructure
from klab.bio.pymolmod.scaffold_model_design import ScaffoldModelDesignBuilder
from klab.bio.pymolmod.multi_structure_builder import MultiStructureBuilder
from klab.bio.pdb import PDB
from klab.bio.clustalo import SequenceAligner
from klab.bio.basics import residue_type_1to3_map
from klab.fs.fsio import write_file
from klab.bio.pdb import PDBParsingException, NonCanonicalResidueException, PDBValidationException

class ChainMatchingException(Exception): pass

def match_pdb_chains(pdb1, pdb1_name, pdb2, pdb2_name, cut_off = 60.0, allow_multiple_matches = False, multiple_match_error_margin = 3.0, use_seqres_sequences_if_possible = True):
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

       Parameters: pdb1 and pdb2 are PDB objects from klab.bio.pdb. pdb1_name and pdb2_name are strings describing the
        structures e.g. 'Model' and 'Scaffold'. cut_off is used in the matching to discard low-matching chains.

       If use_seqres_sequences_if_possible is set, we will use the SEQRES sequences for the mapping when those sequences
       exist. At present, it is possible to match a SEQRES sequence in pdb1 against an ATOM sequence in pdb2 if pdb1 has
       a SEQRES sequence for that chain in question and pdb2 does not. We may want to change this behavior in the future
       i.e. only match SEQRES to SEQRES and ATOM to ATOM.
       If use_seqres_sequences_if_possible and a SEQRES sequence does not exist for a chain, we fall back to the ATOM
       sequence.
       '''

    try:
        pdb1_chains = [c for c in pdb1.atom_chain_order]
        pdb2_chains = [c for c in pdb2.atom_chain_order]
        unrecognized_residues = set(['X'])

        # Extend the list of chains by the SEQRES chain IDs. These will typically be the same list but, just in case, we take
        # the set union.
        if use_seqres_sequences_if_possible:
            pdb1_chains.extend(pdb1.seqres_chain_order)
            pdb1_chains = sorted(set(pdb1_chains))
            pdb2_chains.extend(pdb2.seqres_chain_order)
            pdb2_chains = sorted(set(pdb2_chains))

        sa = SequenceAligner()

        # This is a hack to ensure that the assertions below hold. The alternative is to fix the logic below (maybe allow the separator character to be a parameter).
        pdb1_name = pdb1_name.replace('_', chr(254))
        pdb2_name = pdb2_name.replace('_', chr(254))

        assert(pdb1_name.find('_') == -1)
        assert(pdb2_name.find('_') == -1)

        kept_chains = []
        for c in pdb1_chains:
            # We do not handle chains with all HETATMs (and not ATOMs) well, generally. These conditions allow for those chains
            seq1 = pdb1.get_chain_sequence_string(c, use_seqres_sequences_if_possible, raise_Exception_if_not_found = False)

            if seq1 and str(seq1) and set(str(seq1)) != unrecognized_residues:
                sa.add_sequence('%s_%s' % (pdb1_name, c), str(seq1))
                kept_chains.append(c)
        pdb1_chains = kept_chains

        kept_chains = []
        for c in pdb2_chains:
            # We do not handle chains with all HETATMs (and not ATOMs) well, generally. These conditions allow for those chains
            seq2 = pdb2.get_chain_sequence_string(c, use_seqres_sequences_if_possible, raise_Exception_if_not_found = False)

            if seq2 and str(seq2) and set(str(seq2)) != unrecognized_residues:
                sa.add_sequence('%s_%s' % (pdb2_name, c), str(seq2))
                kept_chains.append(c)
        pdb2_chains = kept_chains

        if not(pdb1_chains):
            raise ChainMatchingException('No valid sequences were found in %s. Alignment failed.' % pdb1_name)
        elif not(pdb2_chains):
            raise ChainMatchingException('No valid sequences were found in %s. Alignment failed.' % pdb2_name)
        else:
            sa.align()

        chain_matches = dict.fromkeys(pdb1_chains, None)
        for c in pdb1_chains:
            best_matches_by_id = sa.get_best_matches_by_id('%s_%s' % (pdb1_name, c), cut_off = cut_off)
            if best_matches_by_id:
                t = []
                for k, v in best_matches_by_id.iteritems():
                    if k.startswith(pdb2_name + '_'):
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
                                chain_matches[c].append((best_match[1].split('_')[1], best_match[0]))
                        assert(len(chain_matches[c]) > 0)
                    else:
                        best_match = sorted(t)[0]
                        chain_matches[c] = [(best_match[1].split('_')[1], best_match[0])]

        return chain_matches
    except ChainMatchingException, e:
        raise
    except Exception, e:
        raise ChainMatchingException()


def match_RCSB_pdb_chains(pdb_id1, pdb_id2, cut_off = 60.0, allow_multiple_matches = False, multiple_match_error_margin = 3.0, use_seqres_sequences_if_possible = True, strict = True):
    '''A convenience function for match_pdb_chains. The required arguments are two PDB IDs from the RCSB.'''
    try:
        stage = pdb_id1
        pdb_1 = PDB(retrieve_pdb(pdb_id1), strict = strict)
        stage = pdb_id2
        pdb_2 = PDB(retrieve_pdb(pdb_id2), strict = strict)
    except (PDBParsingException, NonCanonicalResidueException, PDBValidationException), e:
        raise PDBParsingException("An error occurred while loading %s: '%s'" % (stage, str(e)))

    return match_pdb_chains(pdb_1, pdb_id1, pdb_2, pdb_id2, cut_off = cut_off, allow_multiple_matches = allow_multiple_matches, multiple_match_error_margin = multiple_match_error_margin, use_seqres_sequences_if_possible = use_seqres_sequences_if_possible)


def match_best_pdb_chains(pdb1, pdb1_name, pdb2, pdb2_name, cut_off = 60.0, use_seqres_sequences_if_possible = True):
    '''A wrapper function for match_pdb_chains. This function only takes the best match. The return
        value is a dict mapping
            chain_id_in_pdb1 -> None or a tuple (chain_id_in_pdb_2, percentage_identity_score)
       where percentage_identity_score is a float. e.g. 'A' -> ('B', 100).'''
    d = match_pdb_chains(pdb1, pdb1_name, pdb2, pdb2_name, cut_off = cut_off, allow_multiple_matches = False, use_seqres_sequences_if_possible = use_seqres_sequences_if_possible)
    for k, v in d.iteritems():
        if v:
            d[k] = v[0]
    return d


class SingleSequencePrinter(object):
    '''A class for generating formatted strings for a single sequence in the same fashion as the MultipleSequenceAlignmentPrinter.'''

    def __init__(self, sequence_name, sequence, sequence_tooltips = None):

        # Make sure that if the sequence has tooltips then there is an injection between the residues and the tooltips (a tooltip
        # may be None rather than a string)
        if sequence_tooltips:
            assert(len(str(sequence).replace('-', '')) == len(sequence_tooltips))

        # Make sure that the sequence lengths are all the same size
        self.sequence_length = len(str(sequence))
        self.label_width = len(sequence_name)
        self.sequence_name = sequence_name
        self.sequence = sequence
        print(type(self.sequence))
        self.sequence_tooltips = sequence_tooltips

    def to_lines(self, width = 80, reversed = False, line_separator = '\n'): raise Exception('I have not written this function yet.')

    def to_html(self, width = 80, header_separator = '_', add_tooltips = True, extra_tooltip_class = ''):
        html = []
        html.append('<div class="chain_alignment">')

        sequence, sequence_name, sequence_tooltips = self.sequence, self.sequence_name, self.sequence_tooltips
        # Turn off tooltips if requested
        if not(add_tooltips):
            sequence_tooltips = None

        if self.label_width + 2 < width:
            # headers is a list of pairs split by header_separator. If header_separator is not specified then the
            # second element will be an empty string
            if header_separator:
                headers = sequence_name.split(header_separator)
            else:
                headers = [sequence_name, '']
            print(headers)

            num_residues_per_line = width - self.label_width
            sequence_str = str(sequence)

            # x iterates over a chunk of the sequence alignment
            for x in range(0, self.sequence_length, num_residues_per_line):
                html.append('<div class="sequence_block">')

                # Create a list, subsequence_list, where each entry corresponds to the chunk of the sequence alignment for each sequenec
                residue_substring = []
                subsequence = sequence_str[x:x+num_residues_per_line]

                # Iterate over all residues in the subsequences, marking up residues that differ
                for z in range(len(subsequence)):
                    residue_type = subsequence[z]
                    if sequence_tooltips:
                        residue_substring.append('<span class="%s" title="%s %s">%s</span>' % (extra_tooltip_class, residue_type_1to3_map[residue_type], tooltip.strip(), residue_type))
                    elif sequence_tooltips:
                        residue_substring.append('<span class="%s missing_ATOMs" title="No ATOM records">%s</span>' % (extra_tooltip_class, residue_type))
                    else:
                        residue_substring.append(residue_type)

                html.append('<div class="sequence_alignment_line sequence_alignment_line_%s"><span>%s</span><span>%s</span><span>%s</span></div>' % (headers[0], headers[0], headers[1], ''.join(residue_substring)))
                html.append('</div>') # sequence_block
        else:
            raise Exception('The width (%d characters) is not large enough to display the sequence alignment.' % width)

        html.append('</div>')
        return '\n'.join(html).replace(' class=""', '')


class MultipleSequenceAlignmentPrinter(object):
    '''A class for generating formatted strings from a multiple sequence alignment. These strings should be the result
       of an MSA i.e. they should all have the same length.
       '''

    def __init__(self, sequence_names, sequences, sequence_tooltips = None):

        if not sequence_tooltips:
            sequence_tooltips = [None] * len(sequences)

        assert(len(sequence_names) == len(sequences) and len(sequences) == len(sequence_tooltips) and len(sequence_names) > 1) # The sequence names must correspond with the number of sequences and we require at least two sequences
        assert(len(set(sequence_names)) == len(sequence_names)) # sequence_names must be a list of unique names

        # Make sure that if a sequence has tooltips then there is an injection between the residues and the tooltips (a tooltip
        # may be None rather than a string)
        for x in range(len(sequences)):
            if sequence_tooltips[x]:
                assert(len(str(sequences[x]).replace('-', '')) == len(sequence_tooltips[x]))

        # Make sure that the sequence lengths are all the same size
        sequence_lengths = map(len, sequences)
        assert(len(set(sequence_lengths)) == 1)

        self.sequence_length = sequence_lengths[0]
        self.label_width = max(map(len, sequence_names))

        self.sequence_names = sequence_names
        self.sequences = sequences
        self.sequence_tooltips = sequence_tooltips

    def to_lines(self, width = 80, reversed = False, line_separator = '\n'):
        s = []

        sequences, sequence_names = self.sequences, self.sequence_names
        if reversed:
            sequences, sequence_names = self.sequences[::-1], self.sequence_names[::-1]

        if self.label_width + 2 < width:

            headers = [sequence_name.ljust(self.label_width + 2) for sequence_name in sequence_names]
            num_residues_per_line = width - self.label_width
            sequence_strs = map(str, sequences)

            for x in range(0, self.sequence_length, num_residues_per_line):
                for y in range(len(sequence_strs)):
                    s.append('%s  %s' % (headers[y], sequence_strs[y][x:x + num_residues_per_line]))
        else:
            raise Exception('The width (%d characters) is not large enough to display the sequence alignment.' % width)

        return line_separator.join(s)


    def to_html(self, width = 80, reversed = False, line_separator = '\n', header_separator = '_', add_tooltips = True, extra_tooltip_class = ''):
        html = []
        html.append('<div class="chain_alignment">')

        sequences, sequence_names, sequence_tooltips = self.sequences, self.sequence_names, self.sequence_tooltips
        num_sequences = len(sequences)
        # Turn off tooltips if requested
        if not(add_tooltips):
            sequence_tooltips = [None] * num_sequences

        residue_counters = [0] * num_sequences
        if reversed:
            sequences, sequence_names = self.sequences[::-1], self.sequence_names[::-1], self.sequence_tooltips[::-1]

        if self.label_width + 2 < width:
            # headers is a list of pairs split by header_separator. If header_separator is not specified then the
            # second element will be an empty string
            if header_separator:
                headers = [sequence_name.split(header_separator) for sequence_name in sequence_names]
            else:
                headers = [[sequence_name, ''] for sequence_name in sequence_names]

            num_residues_per_line = width - self.label_width
            sequence_strs = map(str, sequences)

            # x iterates over a chunk of the sequence alignment
            for x in range(0, self.sequence_length, num_residues_per_line):
                html.append('<div class="sequence_block">')

                # Create a list, subsequence_list, where each entry corresponds to the chunk of the sequence alignment for each sequence
                subsequence_list = []
                residue_substrings = []
                for y in range(num_sequences):
                    subsequence_list.append(self.sequences[y][x:x+num_residues_per_line])
                    residue_substrings.append([])

                # check that the subsequences are the same length
                subsequence_lengths = set(map(len, [rs for rs in subsequence_list]))
                assert(len(subsequence_lengths) == 1)
                subsequence_length = subsequence_lengths.pop()

                # Iterate over all residues in the subsequences, marking up residues that differ
                for z in range(subsequence_length):
                    residues = set([subsequence_list[y][z] for y in range(num_sequences) if subsequence_list[y][z] != '-'])

                    if len(residues) == 1:
                        # all residues are the same
                        for y in range(num_sequences):
                            tooltip = ''
                            tooltips = sequence_tooltips[y]
                            if subsequence_list[y][z] != '-':
                                residue_index = residue_counters[y]
                                if tooltips and tooltips[residue_index] != None:
                                    tooltip = tooltips[residue_index]
                                residue_counters[y] += 1
                            residue_type = subsequence_list[y][z]
                            if tooltip:
                                residue_substrings[y].append('<span class="%s" title="%s %s">%s</span>' % (extra_tooltip_class, residue_type_1to3_map[residue_type], tooltip.strip(), residue_type))
                            elif tooltips:
                                residue_substrings[y].append('<span class="%s missing_ATOMs" title="No ATOM records">%s</span>' % (extra_tooltip_class, residue_type))
                            else:
                                residue_substrings[y].append(residue_type)
                    else:
                        # The residues differ - mark up the
                        for y in range(num_sequences):
                            tooltip = ''
                            tooltips = sequence_tooltips[y]
                            if subsequence_list[y][z] != '-':
                                residue_index = residue_counters[y]
                                if tooltips and tooltips[residue_index] != None:
                                    tooltip = tooltips[residue_index]
                                residue_counters[y] += 1
                            if tooltip:
                                residue_type = subsequence_list[y][z]
                                residue_substrings[y].append('<span class="%s differing_residue" title="%s %s">%s</span>' % (extra_tooltip_class, residue_type_1to3_map[residue_type], tooltip.strip(), residue_type))
                            elif tooltips:
                                residue_substrings[y].append('<span class="%s differing_residue missing_ATOMs" title="No ATOM records">%s</span>' % (extra_tooltip_class, residue_type))
                            else:
                                residue_substrings[y].append('<span class="differing_residue">%s</span>' % (subsequence_list[y][z]))

                for y in range(num_sequences):
                    html.append('<div class="sequence_alignment_line sequence_alignment_line_%s"><span>%s</span><span>%s</span><span>%s</span></div>' % (headers[y][0], headers[y][0], headers[y][1], ''.join(residue_substrings[y])))

                html.append('</div>') # sequence_block
        else:
            raise Exception('The width (%d characters) is not large enough to display the sequence alignment.' % width)

        html.append('</div>')

        # Sanity check our tooltipping logic - ensure that the number of times we tried to assign a tooltip for a residue in a sequence matches the length of the sequence
        assert(residue_counters == [len([c for c in str(seq).strip() if c != '-' ]) for seq in sequences])

        return '\n'.join(html).replace(' class=""', '')


class BasePDBChainMapper(object):
    def get_sequence_alignment_strings(self, reversed = True, width = 80, line_separator = '\n'):
        raise Exception('Implement this function.')
    def get_sequence_alignment_strings_as_html(self, reversed = True, width = 80, line_separator = '\n', extra_tooltip_class = ''):
        raise Exception('Implement this function.')


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
        s = ['Matched chain list for %s_%s' % (self.pdb_name, self.chain_id)]
        if self.chain_list:
            for mtch in self.chain_list:
                s.append('\t%s_%s at %s%%' % (mtch[1], mtch[2], mtch[0]))
        else:
            s.append('No matches.')
        return '\n'.join(s)


class PipelinePDBChainMapper(BasePDBChainMapper):
    '''Similar to the removed PDBChainMapper class except this takes a list of PDB files which should be related in some way.
       The matching is done pointwise, matching all PDBs in the list to each other.
       This class is useful for a list of structures that are the result of a linear pipeline e.g. a scaffold structure (RCSB),
       a model structure (Rosetta), and a design structure (experimental result).

       The 'chain_mapping' member stores a mapping from a pair (pdb_name1, pdb_name2) to the mapping from chain IDs in pdb_name1 to
       a MatchedChainList object. This object can be used to return the list of chain IDs in pdb_name2 related to the
       respective chain in pdb_name1 based on sequence alignment. It can also be used to return the percentage identities
       for this alignment. The old mapping and mapping_percentage_identity members of this class can be built from this member
       e.g.
            self.mapping[('Scaffold', 'ExpStructure')] == self.get_chain_mapping('Scaffold', 'ExpStructure')

       The 'residue_id_mapping' member stores a mapping from a pair (pdb_name1, pdb_name2) to a mapping
            'ATOM' -> chains_of_pdb_name_1 -> ATOM residues of that chain -> list of corresponding ATOM residues in the corresponding chains of pdb_name2
            'SEQRES' -> chains_of_pdb_name_1 -> SEQRES residues of that chain -> pairs of (chain_id, corresponding SEQRES residue_id) in the corresponding chains of pdb_name2
       For example, using the homodimer 3MW0 for both Scaffold and ExpStructure:
        residue_id_mapping[('Scaffold', 'ExpStructure')]['ATOM']['A'] -> {'A 167 ': ['A 167 ', 'B 167 '], ...}
        residue_id_mapping[('Scaffold', 'ExpStructure')]['SEQRES']['B'] -> {167 : [('A', 167), ('C', 167)], ...}

       Objects of this class have a differing_atom_residue_ids mapping which maps the pair (pdb_name1, pdb_name2) to the list
       of ATOM residues *in pdb_name1* that differ from those of pdb_name2. Note: there is some subtlety here in terms of
       direction. For example, take this artificial example. We take a homodimer 3MWO as the scaffold and a monomer 1BN1
       with identical sequence as the model. We mutate A110 in 1BN1. We then take 3MWO with a mutation on A106 as the design.
         chain_mapper = ScaffoldModelDesignChainMapper.from_file_contents(retrieve_pdb('3MWO'), retrieve_pdb('1BN1').replace('ASP A 110', 'ASN A 110'), retrieve_pdb('3MWO').replace('GLU A 106', 'GLN A 106'))
       differing_atom_residue_ids then looks like this:
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

       If use_seqres_sequences_if_possible is set, the alignment will use the SEQRES sequences when available. See match_pdb_chains
       for more information.
       '''

    # Constructors

    @staticmethod
    def from_file_paths(pdb_paths, pdb_names, cut_off = 60.0, use_seqres_sequences_if_possible = True, strict = True):
        assert(len(pdb_paths) == len(pdb_names) and len(pdb_paths) > 1)

        pdbs = []
        stage = None
        try:
            for x in range(len(pdb_paths)):
                stage = pdb_names[x]
                pdb_path = pdb_paths[x]
                pdbs.append(PDB.from_filepath(pdb_path), strict = strict)
        except (PDBParsingException, NonCanonicalResidueException, PDBValidationException), e:
            raise PDBParsingException("An error occurred while loading the %s structure: '%s'" % (stage, str(e)))

        return PipelinePDBChainMapper(pdbs, pdb_names, cut_off = cut_off, use_seqres_sequences_if_possible = use_seqres_sequences_if_possible, strict = strict)


    def __init__(self, pdbs, pdb_names, cut_off = 60.0, use_seqres_sequences_if_possible = True, strict = True):

        assert(len(pdbs) == len(pdb_names) and len(pdbs) > 1)
        assert(len(set(pdb_names)) == len(pdb_names)) # pdb_names must be a list of unique names

        self.pdbs = pdbs
        self.pdb_names = pdb_names
        self.use_seqres_sequences_if_possible = use_seqres_sequences_if_possible
        self.strict = strict

        self.pdb_name_to_structure_mapping = {}
        for x in range(len(pdb_names)):
            self.pdb_name_to_structure_mapping[pdb_names[x]] = pdbs[x]

        # differing_atom_residue_ids is a mapping from (pdb_name1, pdb_name2) to the list of ATOM residues *in pdb_name1* that differ from those of pdb_name2
        self.differing_atom_residue_ids = {}

        # chain_mapping is a mapping from (equivalence_class_id_1, equivalence_class_id_2) to the list of ATOM residues *in equivalence_class_id_1* that differ from those of equivalence_class_id_2
        self.chain_mapping = {}

        # Partition the set of PDBs over the ATOM coordinates i.e. if two PDBs have the same ATOM residues then they are
        # part of the same equivalence class.
        # equivalence_classes is a list of tuples [x, y] where:
        #   - x is map from chain ID to a Sequence object (using the ATOM sequence);
        #   - y is a subset of pdb_names;
        # where given two distinct tuples [x_1, y_1] and [x_2, y_2],  y_1 is mutually exclusive from y_2
        # i.e. we have partitioned the set of PDB structures using an equivalence relation on the chain Sequences.

        # todo: to agree with the old logic (which mapped all sequences and did not use an equivalence relation), we should consider structures to be equivalent
        #       if *both* their SEQRES and ATOM Sequences agree. However, requiring that their ATOM Sequences agree is generally strict enough as these sequences
        #       are more likely to vary (e.g. same sequence but missing coordinates)
        equivalence_classes = []
        sorted_objects = [(pdb_name, pdb_object) for pdb_name, pdb_object in sorted(self.pdb_name_to_structure_mapping.iteritems())]
        for pp in sorted_objects:
            pdb_object = pp[1]
            s = pdb_object.atom_sequences

            found_class = None
            p_sequences = pdb_object.atom_sequences
            for tpl in equivalence_classes:
                atom_sequence_set = tpl[0]
                if atom_sequence_set == p_sequences:
                    tpl[1].append(pp[0])
                    found_class = True

            if not found_class:
                atom_sequence_set = pdb_object.atom_sequences
                equivalence_classes.append([atom_sequence_set, [pp[0]]])

        # partition_by_sequence is a map pdb_name -> Int where two pdb names in the same equivalence class map to the same integer (i.e. it is a partition)
        # representative_pdbs is a map Int -> pdb_object mapping the equivalence classes (represented by an integer) to a representative PDB file
        partition_by_sequence = {}
        representative_pdbs = {}
        for x in range(len(equivalence_classes)):
            representative_pdbs[x] = self.pdb_name_to_structure_mapping[equivalence_classes[x][1][0]]
            for pdb_name in equivalence_classes[x][1]:
                partition_by_sequence[pdb_name] = x
        self.partition_by_sequence = partition_by_sequence
        self.representative_pdbs = representative_pdbs

        # For each pair of equivalence classes, match each chain in the first representative pdb to its best match in the second representative pdb
        # This section just creates the chain id->chain id mapping
        representative_ids = sorted(representative_pdbs.keys())
        for x in range(len(representative_ids) - 1):
            for y in range(x + 1, len(representative_ids)):
                representative_pdb_id_1 = representative_ids[x]
                representative_pdb_id_2 = representative_ids[y]
                rpdb_object_1 = representative_pdbs[representative_pdb_id_1]
                rpdb_object_2 = representative_pdbs[representative_pdb_id_2]

                mapping_key = (representative_pdb_id_1, representative_pdb_id_2)
                reverse_mapping_key = (representative_pdb_id_2, representative_pdb_id_1)

                self.chain_mapping[mapping_key] = {}
                self.chain_mapping[reverse_mapping_key] = {}

                # To allow for X cases, we allow the matcher to return multiple matches
                # An artificial example X case would be 3MWO -> 1BN1 -> 3MWO where 3MWO_A and 3MWO_B both map to 1BN1_A
                # In this case, we would like 1BN1_A to map to both 3MWO_A and 3MWO_B.
                rpdb_name_1, rpdb_name_2 = 'EC{0}'.format(representative_pdb_id_1), 'EC{0}'.format(representative_pdb_id_2) # EC = "equivalence class"
                chain_matches = match_pdb_chains(rpdb_object_1, rpdb_name_1, rpdb_object_2, rpdb_name_2, cut_off = cut_off, allow_multiple_matches = True, multiple_match_error_margin = 3.0, use_seqres_sequences_if_possible = self.use_seqres_sequences_if_possible)

                reverse_mapping = {}
                for rpdb1_chain_id, list_of_matches in chain_matches.iteritems():
                    if list_of_matches:
                        mcl = MatchedChainList(rpdb_name_1, rpdb1_chain_id)
                        for l in list_of_matches:
                            mcl.add_chain(rpdb_name_2, l[0], l[1])
                            reverse_mapping[l[0]] = reverse_mapping.get(l[0], [])
                            reverse_mapping[l[0]].append((rpdb1_chain_id, l[1])) # reverse_mapping: chain in pdb2 -> list(tpl(chain in pdb1, %match)
                        self.chain_mapping[mapping_key][rpdb1_chain_id] = mcl

                # Add the reverse mapping. For residues, we would want to realign the sequences in case the second sequence
                # had an inserted residue which does not exist in the first sequences i.e. the relation is not symmetric.
                # However, we treat the chain mapping as symmetric w.r.t. sequence identity (this saves computation as
                # we do not realign the sequences).
                for rpdb2_chain_id, list_of_matches in reverse_mapping.iteritems():
                    mcl = MatchedChainList(rpdb_name_2, rpdb2_chain_id)
                    for l in list_of_matches:
                        mcl.add_chain(rpdb_name_1, l[0], l[1])
                    self.chain_mapping[reverse_mapping_key][rpdb2_chain_id] = mcl

        self.residue_id_mapping = {}

        # Create the residue ID -> residue ID mapping based on the chain mapping
        self._map_residues()


    # Private functions


    def _map_residues(self):
        '''For each pair of equivalence classes, match the residues of a chain in the first class to the residues of appropriate chains in the second class.

            Note: we do a lot of repeated work here. Some of the lookups e.g. atom_sequences/seqres_sequences here could be cached.'''

        pdbs = self.pdbs
        pdb_names = self.pdb_names
        partition_by_sequence = self.partition_by_sequence
        representative_pdbs = self.representative_pdbs
        representative_ids = sorted(representative_pdbs.keys())

        # Map the SEQRES sequences to the ATOM sequences
        # Note: The correct way to do this for RCSB files would be to use the SIFTS information like the ResidueRelatrix
        # does. However, we have to consider the case where users upload PDB files which have not yet been deposited in
        # the PDB so we have to resort to automatic sequence alignments. Ideally, we would store these alignments in a
        # database and then do a lookup at this point. This would not only speed up the computation here but also allow
        # us to manually fix misalignments (which will probably only occur due to gaps rather than mismatches).
        seqres_to_atom_maps = {}
        atom_to_seqres_maps = {}
        for x in range(len(representative_ids)):
            representative_id = representative_ids[x]
            pdb_object = representative_pdbs[representative_id]
            seqres_to_atom_map, atom_to_seqres_map = pdb_object.construct_seqres_to_atom_residue_map()

            # todo: I tested the remainder of this class on PDBs with no SEQRES records so any code related to these maps is untested
            #       when these assertions fail, remove them and fix the code below accordingly

            seqres_to_atom_maps[representative_id] = seqres_to_atom_map
            atom_to_seqres_maps[representative_id] = atom_to_seqres_map


        # Iterate over all pairs of representative PDBs and determine the residue mapping and sets of differing ATOM residues

        # self.residue_id_mapping maps tuples of representative ids e.g. (0, 1) to residue_id_mapping where
        #            residue_id_mapping is a mapping: 'ATOM' -> chain_1_id -> residue_1_id -> tuple(chain_2_id, residue_2_id)
        # where chain_x_id and residue_x_id are associated to representative_id_x

        # self.differing_atom_residue_ids maps tuples of representative ids e.g. (0, 1) to PDB residues IDs which differ between
        # the two representatives
        for x in range(len(representative_ids) - 1):
            for y in range(x + 1, len(representative_ids)):
                representative_pdb_id_1 = representative_ids[x]
                representative_pdb_id_2 = representative_ids[y]
                rpdb_object_1 = representative_pdbs[representative_pdb_id_1]
                rpdb_object_2 = representative_pdbs[representative_pdb_id_2]

                mapping_key = (representative_pdb_id_1, representative_pdb_id_2)
                reverse_mapping_key = mapping_key[::-1]

                residue_id_mapping = {'ATOM' : {}, 'SEQRES' : {}} # todo: add the other types of mapping here e.g. FASTA and Rosetta
                pdb1_differing_atom_residue_ids = []
                pdb2_differing_atom_residue_ids = []

                for pdb1_chain, pdb2_chains in self.get_representative_chain_mapping(mapping_key[0], mapping_key[1]).iteritems():
                    # e.g. pdb1_chain = 'A', pdb2_chains = ['A', 'E']

                    residue_id_mapping['ATOM'][pdb1_chain] = {}
                    residue_id_mapping['SEQRES'][pdb1_chain] = {}

                    # Use the SEQRES or ATOM sequence appropriately
                    pdb1_chain_sequence_type, pdb1_chain_sequence = rpdb_object_1.get_annotated_chain_sequence_string(pdb1_chain, self.use_seqres_sequences_if_possible)

                    for pdb2_chain in pdb2_chains:
                        # Get the mapping between the sequences
                        # Note: sequences and mappings are 1-based following the UniProt convention
                        # The mapping returned from sa.get_residue_mapping is an abstract mapping between *sequences of characters*
                        # and knows nothing about residue identifiers e.g. ATOM residue IDs or whether the sequences are
                        # SEQRES or ATOM sequences

                        sa = SequenceAligner()
                        pdb2_chain_sequence_type, pdb2_chain_sequence = rpdb_object_2.get_annotated_chain_sequence_string(pdb2_chain, self.use_seqres_sequences_if_possible)

                        sa.add_sequence('%s_%s' % (representative_pdb_id_1, pdb1_chain), str(pdb1_chain_sequence))
                        sa.add_sequence('%s_%s' % (representative_pdb_id_2, pdb2_chain), str(pdb2_chain_sequence))
                        mapping, match_mapping = sa.get_residue_mapping()

                        # Since the mapping is only between sequences and we wish to use the original residue identifiers of
                        # the sequence e.g. the PDB/ATOM residue ID, we look this information up in the order mapping of the
                        # Sequence objects
                        for pdb1_residue_index, pdb2_residue_index in mapping.iteritems():
                            pdb1_residue_id = pdb1_chain_sequence.order[pdb1_residue_index - 1] # order is a 0-based list
                            pdb2_residue_id = pdb2_chain_sequence.order[pdb2_residue_index - 1] # order is a 0-based list
                            pdb1_atom_residue_id, pdb2_atom_residue_id = None, None

                            if pdb1_chain_sequence_type == 'SEQRES' and pdb2_chain_sequence_type == 'SEQRES':
                                residue_id_mapping['SEQRES'][pdb1_chain][pdb1_residue_id] = residue_id_mapping['SEQRES'][pdb1_chain].get(pdb1_residue_id, [])
                                residue_id_mapping['SEQRES'][pdb1_chain][pdb1_residue_id].append((pdb2_chain, pdb2_residue_id))

                                pdb1_atom_residue_id = seqres_to_atom_maps.get(representative_pdb_id_1, {}).get(pdb1_chain, {}).get(pdb1_residue_id)
                                pdb2_atom_residue_id = seqres_to_atom_maps.get(representative_pdb_id_2, {}).get(pdb2_chain, {}).get(pdb2_residue_id)
                                if pdb1_atom_residue_id != None and pdb2_atom_residue_id != None:
                                    residue_id_mapping['ATOM'][pdb1_chain][pdb1_atom_residue_id] = residue_id_mapping['ATOM'][pdb1_chain].get(pdb1_atom_residue_id, [])
                                    residue_id_mapping['ATOM'][pdb1_chain][pdb1_atom_residue_id].append(pdb2_atom_residue_id)

                            elif pdb1_chain_sequence_type == 'SEQRES' and pdb2_chain_sequence_type == 'ATOM':
                                pdb1_atom_residue_id = seqres_to_atom_maps.get(representative_pdb_id_1, {}).get(pdb1_chain, {}).get(pdb1_residue_id)
                                if pdb1_atom_residue_id != None:
                                    residue_id_mapping['ATOM'][pdb1_chain][pdb1_atom_residue_id] = residue_id_mapping['ATOM'][pdb1_chain].get(pdb1_atom_residue_id, [])
                                    residue_id_mapping['ATOM'][pdb1_chain][pdb1_atom_residue_id].append(pdb2_residue_id)

                            elif pdb1_chain_sequence_type == 'ATOM' and pdb2_chain_sequence_type == 'SEQRES':
                                pdb2_atom_residue_id = seqres_to_atom_maps.get(representative_pdb_id_2, {}).get(pdb2_chain, {}).get(pdb2_residue_id)
                                if pdb2_atom_residue_id != None:
                                    residue_id_mapping['ATOM'][pdb1_chain][pdb1_residue_id] = residue_id_mapping['ATOM'][pdb1_chain].get(pdb1_residue_id, [])
                                    residue_id_mapping['ATOM'][pdb1_chain][pdb1_residue_id].append(pdb2_atom_residue_id)

                            elif pdb1_chain_sequence_type == 'ATOM' and pdb2_chain_sequence_type == 'ATOM':
                                residue_id_mapping['ATOM'][pdb1_chain][pdb1_residue_id] = residue_id_mapping['ATOM'][pdb1_chain].get(pdb1_residue_id, [])
                                residue_id_mapping['ATOM'][pdb1_chain][pdb1_residue_id].append(pdb2_residue_id)
                            else:
                                raise Exception('An exception occurred.') # this should not happen

                            # We store a *list* of corresponding residues i.e. if pdb1_chain matches pdb2_chain_1 and pdb2_chain_2
                            # then we may map a residue in pdb1_chain to a residue in each of those chains
                            #residue_id_mapping[pdb1_chain][pdb1_residue_id] = residue_id_mapping[pdb1_chain].get(pdb1_residue_id, [])
                            #residue_id_mapping[pdb1_chain][pdb1_residue_id].append(pdb2_residue_id)

                        # Determine which residues of each sequence differ between the sequences
                        # We ignore leading and trailing residues from both sequences
                        pdb1_residue_indices = mapping.keys()
                        pdb2_residue_indices = mapping.values()
                        differing_pdb1_indices = []
                        differing_pdb2_indices = []
                        for pdb1_residue_index, match_details in match_mapping.iteritems():
                            if match_details.clustal == 0 or match_details.clustal == -1 or match_details.clustal == -2:
                                # The residues differed
                                differing_pdb1_indices.append(pdb1_residue_index)
                                differing_pdb2_indices.append(mapping[pdb1_residue_index])

                        # Convert the different sequence indices into PDB ATOM residue IDs. Sometimes there may not be a
                        # mapping from SEQRES residues to the ATOM residues e.g. missing density
                        for idx in differing_pdb1_indices:
                            if pdb1_chain_sequence_type == 'SEQRES':
                                pdb1_seqres_residue_id = pdb1_chain_sequence.order[idx - 1]
                                pdb1_atom_residue_id = seqres_to_atom_maps.get(representative_pdb_id_1, {}).get(pdb1_chain, {}).get(pdb1_seqres_residue_id)
                                if pdb1_atom_residue_id != None:
                                    pdb1_differing_atom_residue_ids.append(pdb1_atom_residue_id)
                            elif pdb1_chain_sequence_type == 'ATOM':
                                pdb1_differing_atom_residue_ids.append(pdb1_chain_sequence.order[idx - 1])
                        for idx in differing_pdb2_indices:
                            if pdb2_chain_sequence_type == 'SEQRES':
                                pdb2_seqres_residue_id = pdb2_chain_sequence.order[idx - 1]
                                pdb2_atom_residue_id = seqres_to_atom_maps.get(representative_pdb_id_2, {}).get(pdb2_chain, {}).get(pdb2_seqres_residue_id)
                                if pdb2_atom_residue_id != None:
                                    pdb2_differing_atom_residue_ids.append(pdb2_atom_residue_id)
                            elif pdb2_chain_sequence_type == 'ATOM':
                                pdb2_differing_atom_residue_ids.append(pdb2_chain_sequence.order[idx - 1])

                self.residue_id_mapping[mapping_key] = residue_id_mapping
                self.differing_atom_residue_ids[mapping_key] = pdb1_differing_atom_residue_ids
                self.differing_atom_residue_ids[reverse_mapping_key] = pdb2_differing_atom_residue_ids

        for k, v in sorted(self.differing_atom_residue_ids.iteritems()):
            self.differing_atom_residue_ids[k] = sorted(set(v)) # the list of residues may not be unique in general so we make it unique here

        self.seqres_to_atom_maps = seqres_to_atom_maps
        self.atom_to_seqres_maps = atom_to_seqres_maps


    # Public functions


    def get_representative_chain_mapping(self, representative_id_1, representative_id_2):
        '''This replaces the old mapping member by constructing it from self.chain_mapping. This function returns a mapping from
        chain IDs in pdb_name1 to chain IDs in pdb_name2.'''
        d = {}
        for pdb1_chain_id, matched_chain_list in self.chain_mapping[(representative_id_1, representative_id_2)].iteritems():
            d[pdb1_chain_id] = matched_chain_list.get_related_chains_ids('EC{0}'.format(representative_id_2))
        return d


    def get_chain_mapping(self, pdb_name1, pdb_name2):
        '''This replaces the old mapping member by constructing it from self.chain_mapping. This function returns a mapping from
        chain IDs in pdb_name1 to chain IDs in pdb_name2.'''
        raise Exception('Implement. Map pdb_namex to its equivalence class, call get_representative_chain_mapping, and something something.')
        pprint.pprint(self.chain_mapping)

        d = {}
        for pdb1_chain_id, matched_chain_list in self.chain_mapping[(pdb_name1, pdb_name2)].iteritems():
            d[pdb1_chain_id] = matched_chain_list.get_related_chains_ids(pdb_name2)
        return d


    def get_differing_atom_residue_ids(self, pdb_name, pdb_list = []):
        '''Returns a list of residues in pdb_name which differ from the pdbs corresponding to the names in pdb_list.'''

        # partition_by_sequence is a map pdb_name -> Int where two pdb names in the same equivalence class map to the same integer (i.e. it is a partition)
        # representative_pdbs is a map Int -> pdb_object mapping the equivalence classes (represented by an integer) to a representative PDB file
        # self.pdb_name_to_structure_mapping : pdb_name -> pdb_object

        # Sanity checks
        assert(pdb_name in self.pdb_names)
        assert(set(pdb_list).intersection(set(self.pdb_names)) == set(pdb_list)) # the names in pdb_list must be in pdb_names

        # 1. Get the representative structure for pdb_name
        representative_pdb_id = self.partition_by_sequence[pdb_name]
        representative_pdb = self.representative_pdbs[representative_pdb_id]

        # 2. Get the other representative structures as dictated by pdb_list
        other_representative_pdbs = set()
        other_representative_pdb_ids = set()
        if not pdb_list:
            pdb_list = self.pdb_names
        for opdb_name in pdb_list:
            orepresentative_pdb_id = self.partition_by_sequence[opdb_name]
            other_representative_pdb_ids.add(orepresentative_pdb_id)
            other_representative_pdbs.add(self.representative_pdbs[orepresentative_pdb_id])
        other_representative_pdbs.discard(representative_pdb)
        other_representative_pdb_ids.discard(representative_pdb_id)

        # Early out if pdb_list was empty (or all pdbs were in the same equivalence class)
        if not other_representative_pdbs:
            return []

        # 3. Return all residues of pdb_name's representative which differ from all the other representatives
        differing_atom_residue_ids = set()
        for other_representative_pdb_id in other_representative_pdb_ids:
            differing_atom_residue_ids = differing_atom_residue_ids.union(set(self.differing_atom_residue_ids[(representative_pdb_id, other_representative_pdb_id)]))

        return sorted(differing_atom_residue_ids)


    def get_sequence_alignment_printer_objects(self, pdb_list = [], reversed = True, width = 80, line_separator = '\n'):
        '''Takes a list, pdb_list, of pdb names e.g. ['Model', 'Scaffold', ...] with which the object was created.
            Using the first element of this list as a base, get the sequence alignments with chains in other members
            of the list. For simplicity, if a chain in the first PDB matches multiple chains in another PDB, we only
            return the alignment for one of the chains. If pdb_list is empty then the function defaults to the object's
            members.

            Returns a list of tuples (chain_id, sequence_alignment_printer_object). Each sequence_alignment_printer_object
            can be used to generate a printable version of the sequence alignment. '''

        raise Exception('Re-implement using the equivalence classes.')

        if not pdb_list:
            pdb_list = self.pdb_names

        assert(len(set(pdb_list)) == len(pdb_list) and (len(pdb_list) > 1))
        assert(sorted(set(pdb_list).intersection(set(self.pdb_names))) == sorted(set(pdb_list)))

        primary_pdb = self.pdb_name_to_structure_mapping[pdb_list[0]]
        primary_pdb_name = pdb_list[0]
        primary_pdb_chains = sorted(primary_pdb.chain_atoms.keys())

        sequence_alignment_printer_objects = []
        for primary_pdb_chain in primary_pdb_chains:

            sa = SequenceAligner()

            # Add the primary PDB's sequence for the chain
            primary_pdb_sequence_type, primary_pdb_sequence = primary_pdb.get_annotated_chain_sequence_string(primary_pdb_chain, self.use_seqres_sequences_if_possible)
            sa.add_sequence('%s_%s' % (primary_pdb_name, primary_pdb_chain), str(primary_pdb_sequence))
            other_chain_types_and_sequences = {}
            for other_pdb_name in pdb_list[1:]:
                other_pdb = self.pdb_name_to_structure_mapping[other_pdb_name]
                other_chains = self.get_chain_mapping(primary_pdb_name, other_pdb_name).get(primary_pdb_chain)
                #other_chain = self.mapping[(primary_pdb_name, other_pdb_name)].get(primary_pdb_chain)
                if other_chains:
                    other_chain = sorted(other_chains)[0]
                    other_pdb_sequence_type, other_pdb_sequence = other_pdb.get_annotated_chain_sequence_string(other_chain, self.use_seqres_sequences_if_possible)
                    other_chain_types_and_sequences[other_pdb_name] = (other_pdb_sequence_type, other_pdb_sequence)
                    sa.add_sequence('%s_%s' % (other_pdb_name, other_chain), str(other_pdb_sequence))

            if len(sa.records) > 1:
                # If there are no corresponding sequences in any other PDB, do not return the non-alignment
                sa.align()

                #pdb1_alignment_str = sa._get_alignment_lines()['%s:%s' % (primary_pdb_name, pdb1_chain)]
                #pdb2_alignment_str = sa._get_alignment_lines()['%s:%s' % (pdb2_name, pdb2_chain)]

                sequence_names, sequences, sequence_tooltips = [], [], []

                sequence_names.append('%s_%s' % (primary_pdb_name, primary_pdb_chain))
                primary_pdb_alignment_lines = sa._get_alignment_lines()['%s_%s' % (primary_pdb_name, primary_pdb_chain)]
                sequences.append(primary_pdb_alignment_lines)
                sequence_tooltips.append(self.get_sequence_tooltips(primary_pdb, primary_pdb_sequence, primary_pdb_sequence_type, primary_pdb_name, primary_pdb_chain, primary_pdb_alignment_lines))
                for other_pdb_name in pdb_list[1:]:
                    #other_chain = self.mapping[(primary_pdb_name, other_pdb_name)].get(primary_pdb_chain)
                    other_pdb = self.pdb_name_to_structure_mapping[other_pdb_name]
                    other_chains = self.get_chain_mapping(primary_pdb_name, other_pdb_name).get(primary_pdb_chain)
                    if other_chains:
                        other_chain = sorted(other_chains)[0]
                        sequence_names.append('%s_%s' % (other_pdb_name, other_chain))
                        other_pdb_alignment_lines = sa._get_alignment_lines()['%s_%s' % (other_pdb_name, other_chain)]
                        sequences.append(other_pdb_alignment_lines)
                        other_pdb_sequence_type, other_pdb_sequence = other_chain_types_and_sequences[other_pdb_name]
                        sequence_tooltips.append(self.get_sequence_tooltips(other_pdb, other_pdb_sequence, other_pdb_sequence_type, other_pdb_name, other_chain, other_pdb_alignment_lines))

                sap = MultipleSequenceAlignmentPrinter(sequence_names, sequences, sequence_tooltips)
                sequence_alignment_printer_objects.append((primary_pdb_chain, sap))

        return sequence_alignment_printer_objects


    def get_sequence_tooltips(self, pdb_object, pdb_sequence, pdb_sequence_type, pdb_name, pdb_chain, pdb_alignment_lines):
        '''pdb_sequence is a Sequence object. pdb_sequence_type is a type returned by PDB.get_annotated_chain_sequence_string,
           pdb_name is the name of the PDB used throughout this object e.g. 'Scaffold', pdb_chain is the chain of interest,
           pdb_alignment_lines are the lines returned by SequenceAligner._get_alignment_lines.

           This function returns a set of tooltips corresponding to the residues in the sequence. The tooltips are the ATOM
           residue IDs. These tooltips can be used to generate useful (and/or interactive using JavaScript) sequence alignments
           in HTML.
           '''

        raise Exception('Re-implement using the equivalence classes.')

        tooltips = None
        atom_sequence = pdb_object.atom_sequences.get(pdb_chain)

        try:
            if pdb_sequence_type == 'SEQRES':
                seqres_to_atom_map = self.seqres_to_atom_maps.get(pdb_name, {}).get(pdb_chain, {})
                tooltips = []
                if seqres_to_atom_map:
                    idx = 1
                    for aligned_residue in pdb_alignment_lines.strip():
                        if aligned_residue != '-':
                            atom_residue = seqres_to_atom_map.get(idx)
                            if atom_residue:
                                # This is a sanity check to make sure that the tooltips are mapping the correct residues types to
                                # the correct residues types
                                assert(aligned_residue == atom_sequence.sequence[atom_residue].ResidueAA)
                            tooltips.append(atom_residue)
                            idx += 1
                    assert(len(tooltips) == len(str(pdb_sequence)))
            elif pdb_sequence_type == 'ATOM':
                tooltips = []
                idx = 0
                for aligned_residue in pdb_alignment_lines.strip():
                    if aligned_residue != '-':
                        # This is a sanity check to make sure that the tooltips are mapping the correct residues types to
                        # the correct residues types
                        assert(aligned_residue == pdb_sequence.sequence[pdb_sequence.order[idx]].ResidueAA)
                        tooltips.append(pdb_sequence.order[idx])
                        idx += 1
                assert(len(tooltips) == len(str(pdb_sequence)))
        except:
            raise Exception('An error occurred during HTML tooltip creation for the multiple sequence alignment.')

        return tooltips


    def get_sequence_alignment_strings(self, pdb_list = [], reversed = True, width = 80, line_separator = '\n'):
        '''Takes a list, pdb_list, of pdb names e.g. ['Model', 'Scaffold', ...] with which the object was created.
            Using the first element of this list as a base, get the sequence alignments with chains in other members
            of the list. For simplicity, if a chain in the first PDB matches multiple chains in another PDB, we only
            return the alignment for one of the chains. If pdb_list is empty then the function defaults to the object's
            members.

            Returns one sequence alignment string for each chain mapping. Each line is a concatenation of lines of the
            specified width, separated by the specified line separator.'''

        raise Exception('Re-implement using the equivalence classes.')

        sequence_alignment_printer_tuples = self.get_sequence_alignment_printer_objects(pdb_list = pdb_list, reversed = reversed, width = width, line_separator = line_separator)
        alignment_strings = []
        for sequence_alignment_printer_tuple in sequence_alignment_printer_tuples:
            primary_pdb_chain = sequence_alignment_printer_tuple[0]
            sap = sequence_alignment_printer_tuple[1]
            alignment_strings.append(sap.to_lines(reversed = reversed, width = width, line_separator = line_separator))

        return alignment_strings


    def get_sequence_alignment_strings_as_html(self, pdb_list = [], reversed = False, width = 80, line_separator = '\n', extra_tooltip_class = ''):
        '''Takes a list, pdb_list, of pdb names e.g. ['Model', 'Scaffold', ...] with which the object was created.
            Using the first element of this list as a base, get the sequence alignments with chains in other members
            of the list. For simplicity, if a chain in the first PDB matches multiple chains in another PDB, we only
            return the alignment for one of the chains. If pdb_list is empty then the function defaults to the object's
            members.

            Returns HTML for the sequence alignments and an empty string if no alignments were made.'''

        raise Exception('Re-implement using the equivalence classes.')

        sequence_alignment_printer_tuples = self.get_sequence_alignment_printer_objects(pdb_list = pdb_list, reversed = reversed, width = width, line_separator = line_separator)
        if not sequence_alignment_printer_tuples:
            return ''
        html = []
        for sequence_alignment_printer_tuple in sequence_alignment_printer_tuples:
            primary_pdb_chain = sequence_alignment_printer_tuple[0]
            sap = sequence_alignment_printer_tuple[1]
            html.append(sap.to_html(reversed = reversed, width = width, line_separator = line_separator, extra_tooltip_class = extra_tooltip_class))

        return '\n'.join(html)


class ScaffoldModelChainMapper(PipelinePDBChainMapper):
    '''A convenience class for the special case where we are mapping specifically from a model structure to a scaffold structure and a design structure.'''


    def __init__(self, scaffold_pdb, model_pdb, cut_off = 60.0, use_seqres_sequences_if_possible = True, strict = True, structure_1_name = None, structure_2_name = None):
        self.scaffold_pdb = scaffold_pdb
        self.model_pdb = model_pdb
        self.structure_1_name = structure_1_name or 'Scaffold'
        self.structure_2_name = structure_2_name or 'Model'
        super(ScaffoldModelChainMapper, self).__init__([scaffold_pdb, model_pdb], [self.structure_1_name, self.structure_2_name], cut_off = cut_off, use_seqres_sequences_if_possible = use_seqres_sequences_if_possible, strict = strict)


    @staticmethod
    def from_file_paths(scaffold_pdb_path, model_pdb_path, cut_off = 60.0, strict = True, structure_1_name = None, structure_2_name = None):
        try:
            stage = 'scaffold'
            scaffold_pdb = PDB.from_filepath(scaffold_pdb_path, strict = strict)
            stage = 'model'
            model_pdb = PDB.from_filepath(model_pdb_path, strict = strict)
        except (PDBParsingException, NonCanonicalResidueException, PDBValidationException), e:
            raise PDBParsingException("An error occurred while loading the %s structure: '%s'" % (stage, str(e)))

        return ScaffoldModelChainMapper(scaffold_pdb, model_pdb, cut_off = cut_off, strict = strict, structure_1_name = structure_1_name, structure_2_name = structure_2_name)


    @staticmethod
    def from_file_contents(scaffold_pdb_contents, model_pdb_contents, cut_off = 60.0, strict = True, structure_1_name = None, structure_2_name = None):
        try:
            stage = 'scaffold'
            scaffold_pdb = PDB(scaffold_pdb_contents, strict = strict)
            stage = 'model'
            model_pdb = PDB(model_pdb_contents, strict = strict)
        except (PDBParsingException, NonCanonicalResidueException, PDBValidationException), e:
            raise PDBParsingException("An error occurred while loading the %s structure: '%s'" % (stage, str(e)))

        return ScaffoldModelChainMapper(scaffold_pdb, model_pdb, cut_off = cut_off, strict = strict, structure_1_name = structure_1_name, structure_2_name = structure_2_name)


    def get_differing_model_residue_ids(self):
        return self.get_differing_atom_residue_ids(self.structure_2_name, [self.structure_1_name])

    def get_differing_scaffold_residue_ids(self):
        return self.get_differing_atom_residue_ids(self.structure_1_name, [self.structure_2_name])

    def generate_pymol_session(self, pymol_executable = 'pymol', settings = {}):
        ''' Generates the PyMOL session for the scaffold, model, and design structures.
            Returns this session and the script which generated it.'''
        b = BatchBuilder(pymol_executable = pymol_executable)

        structures_list = [
            (self.structure_1_name, self.scaffold_pdb.pdb_content, self.get_differing_scaffold_residue_ids()),
            (self.structure_2_name, self.model_pdb.pdb_content, self.get_differing_model_residue_ids()),
        ]

        PSE_files = b.run(ScaffoldModelDesignBuilder, [PDBContainer.from_content_triple(structures_list)], settings = settings)

        return PSE_files[0], b.PSE_scripts[0]


class ScaffoldModelDesignChainMapper(PipelinePDBChainMapper):
    '''A convenience class for the special case where we are mapping specifically from a model structure to a scaffold structure and a design structure.
       The scaffold structure is allowed to be missing.
    '''
    def __init__(self, scaffold_pdb, model_pdb, design_pdb, cut_off = 60.0, use_seqres_sequences_if_possible = True, strict = True):
        self.scaffold_pdb = scaffold_pdb
        self.model_pdb = model_pdb
        self.design_pdb = design_pdb
        if self.scaffold_pdb:
            super(ScaffoldModelDesignChainMapper, self).__init__([scaffold_pdb, model_pdb, design_pdb], ['Scaffold', 'Model', 'ExpStructure'], cut_off = cut_off, use_seqres_sequences_if_possible = use_seqres_sequences_if_possible, strict = strict)
        else:
            super(ScaffoldModelDesignChainMapper, self).__init__([model_pdb, design_pdb], ['Model', 'ExpStructure'], cut_off = cut_off, use_seqres_sequences_if_possible = use_seqres_sequences_if_possible, strict = strict)

    @staticmethod
    def from_file_paths(scaffold_pdb_path, model_pdb_path, design_pdb_path, cut_off = 60.0, strict = True):
        try:
            stage = 'scaffold'
            scaffold_pdb = None
            if scaffold_pdb_path:
                # Allow the scaffold to be null
                scaffold_pdb = PDB.from_filepath(scaffold_pdb_path, strict = strict)
            stage = 'model'
            model_pdb = PDB.from_filepath(model_pdb_path, strict = strict)
            stage = 'design'
            design_pdb = PDB.from_filepath(design_pdb_path, strict = strict)
        except (PDBParsingException, NonCanonicalResidueException, PDBValidationException), e:
            raise PDBParsingException("An error occurred while loading the %s structure: '%s'" % (stage, str(e)))

        return ScaffoldModelDesignChainMapper(scaffold_pdb, model_pdb, design_pdb, cut_off = cut_off, strict = strict)

    @staticmethod
    def from_file_contents(scaffold_pdb_contents, model_pdb_contents, design_pdb_contents, cut_off = 60.0, strict = True):

        try:
            stage = 'scaffold'
            scaffold_pdb = None
            if scaffold_pdb_contents:
                # Allow the scaffold to be null
                scaffold_pdb = PDB(scaffold_pdb_contents, strict = strict)
            stage = 'model'
            model_pdb = PDB(model_pdb_contents, strict = strict)
            stage = 'design'
            design_pdb = PDB(design_pdb_contents, strict = strict)
        except (PDBParsingException, NonCanonicalResidueException, PDBValidationException), e:
            #import traceback
            #colortext.warning(traceback.format_exc())
            raise PDBParsingException("An error occurred while loading the %s structure: '%s'" % (stage, str(e)))

        return ScaffoldModelDesignChainMapper(scaffold_pdb, model_pdb, design_pdb, cut_off = cut_off, strict = strict)

    def get_differing_model_residue_ids(self):
        if self.scaffold_pdb:
            return self.get_differing_atom_residue_ids('Model', ['Scaffold', 'ExpStructure'])
        else:
            return self.get_differing_atom_residue_ids('Model', ['ExpStructure'])

    def get_differing_scaffold_residue_ids(self):
        if self.scaffold_pdb:
            return self.get_differing_atom_residue_ids('Scaffold', ['Model', 'ExpStructure'])

    def get_differing_design_residue_ids(self):
        if self.scaffold_pdb:
            return self.get_differing_atom_residue_ids('ExpStructure', ['Scaffold', 'Model'])
        else:
            return self.get_differing_atom_residue_ids('ExpStructure', ['Model'])

    def generate_pymol_session(self, pymol_executable = 'pymol', settings = {}):
        ''' Generates the PyMOL session for the scaffold, model, and design structures.
            Returns this session and the script which generated it.'''
        b = BatchBuilder(pymol_executable = pymol_executable)

        if self.scaffold_pdb:
            structures_list = [
                ('Scaffold', self.scaffold_pdb.pdb_content, self.get_differing_scaffold_residue_ids()),
                ('Model', self.model_pdb.pdb_content, self.get_differing_model_residue_ids()),
                ('ExpStructure', self.design_pdb.pdb_content, self.get_differing_design_residue_ids ()),
            ]
        else:
            structures_list = [
                ('Model', self.model_pdb.pdb_content, self.get_differing_model_residue_ids()),
                ('ExpStructure', self.design_pdb.pdb_content, self.get_differing_design_residue_ids ()),
            ]

        PSE_files = b.run(ScaffoldModelDesignBuilder, [PDBContainer.from_content_triple(structures_list)], settings = settings)

        return PSE_files[0], b.PSE_scripts[0]


class DecoyChainMapper(PipelinePDBChainMapper):
    '''A convenience class for the special case where we are mapping specifically from structures which are based on the
       protein but may include a small number mutations.
       Use cases:
         - creating PyMOL sessions for backrub ensembles;
         - creating PyMOL sessions for wildtype and mutant ensembles;
         - creating PyMOL sessions for mutants/designs from the same scaffold.
    '''


    def __init__(self, cut_off = 60.0, use_seqres_sequences_if_possible = True, strict = True):
        self.cut_off = cut_off
        self.use_seqres_sequences_if_possible = use_seqres_sequences_if_possible
        self.strict = strict
        self.structures = []
        self.fixed = False
        self.structure_names = set()


    def finalize_colors(self):
        pass


    def add(self, pdb_object, structure_name, chain_seed_color = None, backbone_color = None, sidechain_color = None, backbone_display = 'cartoon', sidechain_display = 'sticks'):
        if structure_name in self.structure_names:
            raise Exception('Structure names must be unique. The name {0} has already been used.'.format(structure_name))
        self.structure_names.add(structure_name)
        self.structures.append(PyMOLStructure(pdb_object, structure_name, chain_seed_color = chain_seed_color, backbone_color = backbone_color, sidechain_color = sidechain_color,
                                                backbone_display = backbone_display, sidechain_display = sidechain_display, residues_of_interest = []))


    def fix(self):
        if self.fixed:
            raise Exception('This object has already been aligned. It cannot be aligned again.')

        super(DecoyChainMapper, self).__init__(
            [s.pdb_object for s in self.structures],
            [s.structure_name for s in self.structures],
            cut_off = self.cut_off, use_seqres_sequences_if_possible = self.use_seqres_sequences_if_possible, strict = self.strict)
        self.fixed = True


    def generate_pymol_session(self, pymol_executable = 'pymol', settings = {}):
        ''' Generates the PyMOL session for the scaffold, model, and design structures.
            Returns this session and the script which generated it.'''

        if not self.fixed:
            self.fix()

        b = BatchBuilder(pymol_executable = pymol_executable)

        for s in self.structures:
            s.add_residues_of_interest(self.get_differing_atom_residue_ids(s.structure_name))

        PSE_files = b.run(MultiStructureBuilder, [self.structures], settings = settings)

        return PSE_files[0], b.PSE_scripts[0]


if __name__ == '__main__':
    from klab.fs.fsio import read_file

    from rcsb import retrieve_pdb

    #sa = SequenceAligner()

    #sa.add_sequence('1ki1_D', '''DMLTPTERKRQGYIHELIVTEENYVNDLQLVTEIFQKPLMESELLTEKEVAMIFVNWKELIMCNIKLLKALRVRKKMSGEKMPVKMIGDILSAQLPHMQPYIRFCSRQLNGAALIQQKTDEAPDFKEFVKRLEMDPRCKGMPLSSFILKPMQRVTRYPLIIKNILENTPENHPDHSHLKHALEKAEELCSQVNEGVREKENSDRLEWIQAHVQCEGLSEQLVFNSVTNCLGPRKFLHSGKLYKAKNNKELYGFLFNDFLLLTQITKPLGSSGTDKVFSPKSNLQYMYKTPIFLNEVLVKLPTDPSGDEPIFHISHIDRVYTLRAESINERTAWVQKIKAASELYIETEKKKR''')
    #sa.add_sequence('3qbv_B', '''DMLTPTERKRQGYIHELIVTEENYVNDLQLVTEIFQKPLMESELLTEKEVAMIFVNWKELIMCNIKLLKALRVRKKMSGEKMPVKMIGDILSAQLPHMQPYIRFCSRQLNGAALIQQKTDEAPDFKEFVKRLAMDPRCKGMPLSEFILKPMQRVTRYPLIIKNILENTPENHPDHSHLKHALEKAEELCSQVNEGVREKENSDRLEWIQAHVQCEGLSEQLVFNSVTNCLGPRKFLHSGKLYKAKSNKELYGFLFNDFLLLTQITKPLGSSGTDKVFSPKSNLQYKMYKTPIFLNEVLVKLPTDPSGDEPIFHISHIDRVYTLRAESINERTAWVQKIKAASELYIETEKK''')

    #sa.align()


    #sys.exit(0)

    if False:

        colortext.message('match_pdb_chains: 3MW0 -> 1BN1')
        print(match_pdb_chains(PDB(retrieve_pdb('3MWO')), '3MWO', PDB(retrieve_pdb('1BN1')), '1BN1', cut_off = 60.0, allow_multiple_matches = True))

        colortext.warning('match_pdb_chains: 1BN1 -> 3MW0')
        print(match_pdb_chains(PDB(retrieve_pdb('1BN1')), '1BN1', PDB(retrieve_pdb('3MWO')), '3MWO', cut_off = 60.0, allow_multiple_matches = True))

        # Example of how to create a mapper from file paths
        chain_mapper = ScaffoldModelChainMapper.from_file_paths('../.testdata/1z1s_DIG5_scaffold.pdb', '../.testdata/DIG5_1_model.pdb')

        # Example of how to create a mapper from file contents
        chain_mapper = ScaffoldModelChainMapper.from_file_contents(read_file('../.testdata/1z1s_DIG5_scaffold.pdb'), read_file('../.testdata/DIG5_1_model.pdb'))

        # 3MWO -> 1BN1 test case (3MWO_A and 3MWO_B map to 1BN1_A)
        chain_mapper = ScaffoldModelDesignChainMapper.from_file_contents(retrieve_pdb('3MWO'), retrieve_pdb('1BN1').replace('ASP A 110', 'ASN A 110'), retrieve_pdb('3MWO').replace('GLU A 106', 'GLN A 106'))

    if False:
        # Test case for bad tooltips in 1KI1 vs 3QBV. There is a jump in the HTML generated for chain B of the scaffold from TYR B1513 to MET B1515 - the latter should be MET B1514. Similarly, ILE B1520 should be ILE B1519 in the exp. structure
        sequence_names = ['Scaffold_D', 'Model_B', 'ExpStructure_B']
        sequences = ['DMLTPTERKRQGYIHELIVTEENYVNDLQLVTEIFQKPLMESELLTEKEVAMIFVNWKELIMCNIKLLKALRVRKKMSGEKMPVKMIGDILSAQLPHMQPYIRFCSRQLNGAALIQQKTDEAPDFKEFVKRLEMDPRCKGMPLSSFILKPMQRVTRYPLIIKNILENTPENHPDHSHLKHALEKAEELCSQVNEGVREKENSDRLEWIQAHVQCEGLSEQLVFNSVTNCLGPRKFLHSGKLYKAKNNKELYGFLFNDFLLLTQITKPLGSSGTDKVFSPKSNLQY-MYKTPIFLNEVLVKLPTDPSGDEPIFHISHIDRVYTLRAESINERTAWVQKIKAASELYIETEKKKR',
         'DMLTPTERKRQGYIHELIVTEENYVNDLQLVTEIFQKPLMESELLTEKEVAMIFVNWKELIMCNIKLLKALRVRKKMSGEKMPVKMIGDILSAQLPHMQPYIRFCSRQLNGAALIQQKTDEAPDFKEFVKRLEMDPRCKGMPLSEFILKPMQRVTRYPLIIKNILENTPENHPDHSHLKHALEKAEELCSQVNEGVREKENSDRLEWIQAHVQCEGLSEQLVFNSVTNCLGPRKFLHSGKLYKAKNNKELYGFLFNDFLLLTQITKP-------KVFSPKSNLQY-MYKTPIFLNEVLVKLPTDPSGD---FHISHIDRVYTLRAESINERTAWVQKIKAASELYIETEKKKR',
         'DMLTPTERKRQGYIHELIVTEENYVNDLQLVTEIFQKPLMESELLTEKEVAMIFVNWKELIMCNIKLLKALRVRKKMSGEKMPVKMIGDILSAQLPHMQPYIRFCSRQLNGAALIQQKTDEAPDFKEFVKRLAMDPRCKGMPLSEFILKPMQRVTRYPLIIKNILENTPENHPDHSHLKHALEKAEELCSQVNEGVREKENSDRLEWIQAHVQCEGLSEQLVFNSVTNCLGPRKFLHSGKLYKAKSNKELYGFLFNDFLLLTQITKPLGSSGTDKVFSPKSNLQYKMYKTPIFLNEVLVKLPTDPSGDEPIFHISHIDRVYTLRAESINERTAWVQKIKAASELYIETEKK--'
        ]
        sequence_tooltips = [
            ['D1229 ', 'D1230 ', 'D1231 ', 'D1232 ', 'D1233 ', 'D1234 ', 'D1235 ', 'D1236 ', 'D1237 ', 'D1238 ', 'D1239 ', 'D1240 ', 'D1241 ', 'D1242 ', 'D1243 ', 'D1244 ', 'D1245 ', 'D1246 ', 'D1247 ', 'D1248 ', 'D1249 ', 'D1250 ', 'D1251 ', 'D1252 ', 'D1253 ', 'D1254 ', 'D1255 ', 'D1256 ', 'D1257 ', 'D1258 ', 'D1259 ', 'D1260 ', 'D1261 ', 'D1262 ', 'D1263 ', 'D1264 ', 'D1265 ', 'D1266 ', 'D1267 ', 'D1268 ', 'D1269 ', 'D1270 ', 'D1271 ', 'D1272 ', 'D1273 ', 'D1274 ', 'D1275 ', 'D1276 ', 'D1277 ', 'D1278 ', 'D1279 ', 'D1280 ', 'D1281 ', 'D1282 ', 'D1283 ', 'D1284 ', 'D1285 ', 'D1286 ', 'D1287 ', 'D1288 ', 'D1289 ', 'D1290 ', 'D1291 ', 'D1292 ', 'D1293 ', 'D1294 ', 'D1295 ', 'D1296 ', 'D1297 ', 'D1298 ', 'D1299 ', 'D1300 ', 'D1301 ', 'D1302 ', 'D1303 ', 'D1304 ', 'D1305 ', 'D1306 ', 'D1307 ', 'D1308 ', 'D1309 ', 'D1310 ', 'D1311 ', 'D1312 ', 'D1313 ', 'D1314 ', 'D1315 ', 'D1316 ', 'D1317 ', 'D1318 ', 'D1319 ', 'D1320 ', 'D1321 ', 'D1322 ', 'D1323 ', 'D1324 ', 'D1325 ', 'D1326 ', 'D1327 ', 'D1328 ', 'D1329 ', 'D1330 ', 'D1331 ', 'D1332 ', 'D1333 ', 'D1334 ', 'D1335 ', 'D1336 ', 'D1337 ', 'D1338 ', 'D1339 ', 'D1340 ', 'D1341 ', 'D1342 ', 'D1343 ', 'D1344 ', 'D1345 ', 'D1346 ', 'D1347 ', 'D1348 ', 'D1349 ', 'D1350 ', 'D1351 ', 'D1352 ', 'D1353 ', 'D1354 ', 'D1355 ', 'D1356 ', 'D1357 ', 'D1358 ', 'D1359 ', 'D1360 ', 'D1361 ', 'D1362 ', 'D1363 ', 'D1364 ', 'D1365 ', 'D1366 ', 'D1367 ', 'D1368 ', 'D1369 ', 'D1370 ', 'D1371 ', 'D1372 ', 'D1373 ', 'D1374 ', 'D1375 ', 'D1376 ', 'D1377 ', 'D1378 ', 'D1379 ', 'D1380 ', 'D1381 ', 'D1382 ', 'D1383 ', 'D1384 ', 'D1385 ', 'D1386 ', 'D1387 ', 'D1388 ', 'D1389 ', 'D1390 ', 'D1391 ', 'D1392 ', 'D1393 ', 'D1394 ', 'D1395 ', 'D1396 ', 'D1397 ', 'D1398 ', 'D1399 ', 'D1400 ', 'D1401 ', 'D1402 ', 'D1403 ', 'D1404 ', 'D1405 ', 'D1406 ', 'D1407 ', 'D1408 ', 'D1409 ', 'D1410 ', 'D1411 ', 'D1412 ', 'D1413 ', 'D1414 ', 'D1415 ', 'D1416 ', 'D1417 ', 'D1418 ', 'D1419 ', 'D1420 ', 'D1421 ', 'D1422 ', 'D1423 ', 'D1424 ', 'D1425 ', 'D1426 ', 'D1427 ', 'D1428 ', 'D1429 ', 'D1430 ', 'D1431 ', 'D1432 ', 'D1433 ', 'D1434 ', 'D1435 ', 'D1436 ', 'D1437 ', 'D1438 ', 'D1439 ', 'D1440 ', 'D1441 ', 'D1442 ', 'D1443 ', 'D1444 ', 'D1445 ', 'D1446 ', 'D1447 ', 'D1448 ', 'D1449 ', 'D1450 ', 'D1451 ', 'D1452 ', 'D1453 ', 'D1454 ', 'D1455 ', 'D1456 ', 'D1457 ', 'D1458 ', 'D1459 ', 'D1460 ', 'D1461 ', 'D1462 ', 'D1463 ', 'D1464 ', 'D1465 ', 'D1466 ', 'D1467 ', 'D1468 ', 'D1469 ', 'D1470 ', 'D1471 ', 'D1472 ', 'D1473 ', 'D1474 ', 'D1475 ', 'D1476 ', 'D1477 ', 'D1478 ', 'D1479 ', 'D1480 ', 'D1481 ', 'D1482 ', 'D1483 ', 'D1484 ', 'D1485 ', 'D1486 ', 'D1487 ', 'D1488 ', 'D1489 ', 'D1490 ', 'D1491 ', 'D1492 ', 'D1493 ', 'D1494 ', 'D1495 ', None, None, None, None, None, None, None, 'D1503 ', 'D1504 ', 'D1505 ', 'D1506 ', 'D1507 ', 'D1508 ', 'D1509 ', 'D1510 ', 'D1511 ', 'D1512 ', 'D1513 ', 'D1515 ', 'D1516 ', 'D1517 ', 'D1518 ', 'D1519 ', 'D1520 ', 'D1521 ', 'D1522 ', 'D1523 ', 'D1524 ', 'D1525 ', 'D1526 ', 'D1527 ', 'D1528 ', 'D1529 ', 'D1530 ', 'D1531 ', 'D1532 ', 'D1533 ', 'D1534 ', 'D1535 ', None, None, None, 'D1539 ', 'D1540 ', 'D1541 ', 'D1542 ', 'D1543 ', 'D1544 ', 'D1545 ', 'D1546 ', 'D1547 ', 'D1548 ', 'D1549 ', 'D1550 ', 'D1551 ', 'D1552 ', 'D1553 ', 'D1554 ', 'D1555 ', 'D1556 ', 'D1557 ', 'D1558 ', 'D1559 ', 'D1560 ', 'D1561 ', 'D1562 ', 'D1563 ', 'D1564 ', 'D1565 ', 'D1566 ', 'D1567 ', 'D1568 ', 'D1569 ', 'D1570 ', 'D1571 ', 'D1572 ', 'D1573 ', 'D1574 ', 'D1575 ', 'D1576 ', 'D1577 ', 'D1578 ', 'D1579 ', 'D1580 ', None],
            ['B1229 ', 'B1230 ', 'B1231 ', 'B1232 ', 'B1233 ', 'B1234 ', 'B1235 ', 'B1236 ', 'B1237 ', 'B1238 ', 'B1239 ', 'B1240 ', 'B1241 ', 'B1242 ', 'B1243 ', 'B1244 ', 'B1245 ', 'B1246 ', 'B1247 ', 'B1248 ', 'B1249 ', 'B1250 ', 'B1251 ', 'B1252 ', 'B1253 ', 'B1254 ', 'B1255 ', 'B1256 ', 'B1257 ', 'B1258 ', 'B1259 ', 'B1260 ', 'B1261 ', 'B1262 ', 'B1263 ', 'B1264 ', 'B1265 ', 'B1266 ', 'B1267 ', 'B1268 ', 'B1269 ', 'B1270 ', 'B1271 ', 'B1272 ', 'B1273 ', 'B1274 ', 'B1275 ', 'B1276 ', 'B1277 ', 'B1278 ', 'B1279 ', 'B1280 ', 'B1281 ', 'B1282 ', 'B1283 ', 'B1284 ', 'B1285 ', 'B1286 ', 'B1287 ', 'B1288 ', 'B1289 ', 'B1290 ', 'B1291 ', 'B1292 ', 'B1293 ', 'B1294 ', 'B1295 ', 'B1296 ', 'B1297 ', 'B1298 ', 'B1299 ', 'B1300 ', 'B1301 ', 'B1302 ', 'B1303 ', 'B1304 ', 'B1305 ', 'B1306 ', 'B1307 ', 'B1308 ', 'B1309 ', 'B1310 ', 'B1311 ', 'B1312 ', 'B1313 ', 'B1314 ', 'B1315 ', 'B1316 ', 'B1317 ', 'B1318 ', 'B1319 ', 'B1320 ', 'B1321 ', 'B1322 ', 'B1323 ', 'B1324 ', 'B1325 ', 'B1326 ', 'B1327 ', 'B1328 ', 'B1329 ', 'B1330 ', 'B1331 ', 'B1332 ', 'B1333 ', 'B1334 ', 'B1335 ', 'B1336 ', 'B1337 ', 'B1338 ', 'B1339 ', 'B1340 ', 'B1341 ', 'B1342 ', 'B1343 ', 'B1344 ', 'B1345 ', 'B1346 ', 'B1347 ', 'B1348 ', 'B1349 ', 'B1350 ', 'B1351 ', 'B1352 ', 'B1353 ', 'B1354 ', 'B1355 ', 'B1356 ', 'B1357 ', 'B1358 ', 'B1359 ', 'B1360 ', 'B1361 ', 'B1362 ', 'B1363 ', 'B1364 ', 'B1365 ', 'B1366 ', 'B1367 ', 'B1368 ', 'B1369 ', 'B1370 ', 'B1371 ', 'B1372 ', 'B1373 ', 'B1374 ', 'B1375 ', 'B1376 ', 'B1377 ', 'B1378 ', 'B1379 ', 'B1380 ', 'B1381 ', 'B1382 ', 'B1383 ', 'B1384 ', 'B1385 ', 'B1386 ', 'B1387 ', 'B1388 ', 'B1389 ', 'B1390 ', 'B1391 ', 'B1392 ', 'B1393 ', 'B1394 ', 'B1395 ', 'B1396 ', 'B1397 ', 'B1398 ', 'B1399 ', 'B1400 ', 'B1401 ', 'B1402 ', 'B1403 ', 'B1404 ', 'B1405 ', 'B1406 ', 'B1407 ', 'B1408 ', 'B1409 ', 'B1410 ', 'B1411 ', 'B1412 ', 'B1413 ', 'B1414 ', 'B1415 ', 'B1416 ', 'B1417 ', 'B1418 ', 'B1419 ', 'B1420 ', 'B1421 ', 'B1422 ', 'B1423 ', 'B1424 ', 'B1425 ', 'B1426 ', 'B1427 ', 'B1428 ', 'B1429 ', 'B1430 ', 'B1431 ', 'B1432 ', 'B1433 ', 'B1434 ', 'B1435 ', 'B1436 ', 'B1437 ', 'B1438 ', 'B1439 ', 'B1440 ', 'B1441 ', 'B1442 ', 'B1443 ', 'B1444 ', 'B1445 ', 'B1446 ', 'B1447 ', 'B1448 ', 'B1449 ', 'B1450 ', 'B1451 ', 'B1452 ', 'B1453 ', 'B1454 ', 'B1455 ', 'B1456 ', 'B1457 ', 'B1458 ', 'B1459 ', 'B1460 ', 'B1461 ', 'B1462 ', 'B1463 ', 'B1464 ', 'B1465 ', 'B1466 ', 'B1467 ', 'B1468 ', 'B1469 ', 'B1470 ', 'B1471 ', 'B1472 ', 'B1473 ', 'B1474 ', 'B1475 ', 'B1476 ', 'B1477 ', 'B1478 ', 'B1479 ', 'B1480 ', 'B1481 ', 'B1482 ', 'B1483 ', 'B1484 ', 'B1485 ', 'B1486 ', 'B1487 ', 'B1488 ', 'B1489 ', 'B1490 ', 'B1491 ', 'B1492 ', 'B1493 ', 'B1494 ', 'B1495 ', 'B1503 ', 'B1504 ', 'B1505 ', 'B1506 ', 'B1507 ', 'B1508 ', 'B1509 ', 'B1510 ', 'B1511 ', 'B1512 ', 'B1513 ', 'B1514 ', 'B1515 ', 'B1516 ', 'B1517 ', 'B1518 ', 'B1519 ', 'B1520 ', 'B1521 ', 'B1522 ', 'B1523 ', 'B1524 ', 'B1525 ', 'B1526 ', 'B1527 ', 'B1528 ', 'B1529 ', 'B1530 ', 'B1531 ', 'B1532 ', 'B1533 ', 'B1534 ', 'B1535 ', 'B1539 ', 'B1540 ', 'B1541 ', 'B1542 ', 'B1543 ', 'B1544 ', 'B1545 ', 'B1546 ', 'B1547 ', 'B1548 ', 'B1549 ', 'B1550 ', 'B1551 ', 'B1552 ', 'B1553 ', 'B1554 ', 'B1555 ', 'B1556 ', 'B1557 ', 'B1558 ', 'B1559 ', 'B1560 ', 'B1561 ', 'B1562 ', 'B1563 ', 'B1564 ', 'B1565 ', 'B1566 ', 'B1567 ', 'B1568 ', 'B1569 ', 'B1570 ', 'B1571 ', 'B1572 ', 'B1573 ', 'B1574 ', 'B1575 ', 'B1576 ', 'B1577 ', 'B1578 ', 'B1579 ', 'B1580 '],
            ['B1229 ', 'B1230 ', 'B1231 ', 'B1232 ', 'B1233 ', 'B1234 ', 'B1235 ', 'B1236 ', 'B1237 ', 'B1238 ', 'B1239 ', 'B1240 ', 'B1241 ', 'B1242 ', 'B1243 ', 'B1244 ', 'B1245 ', 'B1246 ', 'B1247 ', 'B1248 ', 'B1249 ', 'B1250 ', 'B1251 ', 'B1252 ', 'B1253 ', 'B1254 ', 'B1255 ', 'B1256 ', 'B1257 ', 'B1258 ', 'B1259 ', 'B1260 ', 'B1261 ', 'B1262 ', 'B1263 ', 'B1264 ', 'B1265 ', 'B1266 ', 'B1267 ', 'B1268 ', 'B1269 ', 'B1270 ', 'B1271 ', 'B1272 ', 'B1273 ', 'B1274 ', 'B1275 ', 'B1276 ', 'B1277 ', 'B1278 ', 'B1279 ', 'B1280 ', 'B1281 ', 'B1282 ', 'B1283 ', 'B1284 ', 'B1285 ', 'B1286 ', 'B1287 ', 'B1288 ', 'B1289 ', 'B1290 ', 'B1291 ', 'B1292 ', 'B1293 ', 'B1294 ', 'B1295 ', 'B1296 ', 'B1297 ', 'B1298 ', 'B1299 ', 'B1300 ', 'B1301 ', 'B1302 ', 'B1303 ', 'B1304 ', 'B1305 ', 'B1306 ', 'B1307 ', 'B1308 ', 'B1309 ', 'B1310 ', 'B1311 ', 'B1312 ', 'B1313 ', 'B1314 ', 'B1315 ', 'B1316 ', 'B1317 ', 'B1318 ', 'B1319 ', 'B1320 ', 'B1321 ', 'B1322 ', 'B1323 ', 'B1324 ', 'B1325 ', 'B1326 ', 'B1327 ', 'B1328 ', 'B1329 ', 'B1330 ', 'B1331 ', 'B1332 ', 'B1333 ', 'B1334 ', 'B1335 ', 'B1336 ', 'B1337 ', 'B1338 ', 'B1339 ', 'B1340 ', 'B1341 ', 'B1342 ', 'B1343 ', 'B1344 ', 'B1345 ', 'B1346 ', 'B1347 ', 'B1348 ', 'B1349 ', 'B1350 ', 'B1351 ', 'B1352 ', 'B1353 ', 'B1354 ', 'B1355 ', 'B1356 ', 'B1357 ', 'B1358 ', 'B1359 ', 'B1360 ', 'B1361 ', 'B1362 ', 'B1363 ', 'B1364 ', 'B1365 ', 'B1366 ', 'B1367 ', 'B1368 ', 'B1369 ', 'B1370 ', 'B1371 ', 'B1372 ', 'B1373 ', 'B1374 ', 'B1375 ', 'B1376 ', 'B1377 ', 'B1378 ', 'B1379 ', 'B1380 ', 'B1381 ', 'B1382 ', 'B1383 ', 'B1384 ', 'B1385 ', 'B1386 ', 'B1387 ', 'B1388 ', 'B1389 ', 'B1390 ', 'B1391 ', 'B1392 ', 'B1393 ', 'B1394 ', 'B1395 ', 'B1396 ', 'B1397 ', 'B1398 ', 'B1399 ', 'B1400 ', 'B1401 ', 'B1402 ', 'B1403 ', 'B1404 ', 'B1405 ', 'B1406 ', 'B1407 ', 'B1408 ', 'B1409 ', 'B1410 ', 'B1411 ', 'B1412 ', 'B1413 ', 'B1414 ', 'B1415 ', 'B1416 ', 'B1417 ', 'B1418 ', 'B1419 ', 'B1420 ', 'B1421 ', 'B1422 ', 'B1423 ', 'B1424 ', 'B1425 ', 'B1426 ', 'B1427 ', 'B1428 ', 'B1429 ', 'B1430 ', 'B1431 ', 'B1432 ', 'B1433 ', 'B1434 ', 'B1435 ', 'B1436 ', 'B1437 ', 'B1438 ', 'B1439 ', 'B1440 ', 'B1441 ', 'B1442 ', 'B1443 ', 'B1444 ', None, None, None, 'B1448 ', 'B1449 ', 'B1450 ', 'B1451 ', 'B1452 ', 'B1453 ', 'B1454 ', 'B1455 ', 'B1456 ', 'B1457 ', 'B1458 ', 'B1459 ', 'B1460 ', 'B1461 ', 'B1462 ', 'B1463 ', 'B1464 ', 'B1465 ', 'B1466 ', 'B1467 ', 'B1468 ', 'B1469 ', 'B1470 ', 'B1471 ', 'B1472 ', 'B1473 ', 'B1474 ', None, None, 'B1477 ', 'B1478 ', 'B1479 ', 'B1480 ', 'B1481 ', 'B1482 ', 'B1483 ', 'B1484 ', 'B1485 ', 'B1486 ', 'B1487 ', 'B1488 ', 'B1489 ', 'B1490 ', 'B1491 ', 'B1492 ', 'B1493 ', 'B1494 ', None, None, None, None, None, None, None, None, None, None, 'B1505 ', 'B1506 ', 'B1507 ', 'B1508 ', 'B1509 ', 'B1510 ', 'B1511 ', 'B1512 ', 'B1513 ', None, None, None, None, None, None, 'B1520 ', 'B1521 ', 'B1522 ', 'B1523 ', 'B1524 ', 'B1525 ', 'B1526 ', 'B1527 ', 'B1528 ', None, None, None, None, None, None, None, None, None, None, 'B1539 ', 'B1540 ', 'B1541 ', 'B1542 ', 'B1543 ', None, None, 'B1546 ', 'B1547 ', 'B1548 ', 'B1549 ', None, None, None, None, None, None, None, None, None, None, None, 'B1561 ', 'B1562 ', 'B1563 ', 'B1564 ', 'B1565 ', 'B1566 ', 'B1567 ', 'B1568 ', 'B1569 ', 'B1570 ', 'B1571 ', 'B1572 ', 'B1573 ', 'B1574 ', 'B1575 ', 'B1576 ', 'B1577 ', 'B1578 ', None]
        ]
        msap = MultipleSequenceAlignmentPrinter(sequence_names, sequences, sequence_tooltips)
        print(msap.to_html())

    if False:
        # Example of how to create a mapper from file contents
        #chain_mapper = ScaffoldModelDesignChainMapper.from_file_contents(read_file('../.testdata/1x42_BH3_scaffold.pdb'), read_file('../.testdata/1x42_foldit2_BH32_design.pdb'), read_file('../.testdata/3U26.pdb'))

        print(match_RCSB_pdb_chains('1ki1', '3QBV', cut_off = 60.0, allow_multiple_matches = False, multiple_match_error_margin = 3.0))

    chain_mapper = ScaffoldModelDesignChainMapper.from_file_contents(retrieve_pdb('1ki1'), read_file('../.testdata/Sens_backrub_design.pdb'), retrieve_pdb('3QBV'))
    chain_mapper.get_sequence_alignment_printer_objects()
    sys.exit(0)

    print('---')
    colortext.message('''chain_mapper.get_differing_atom_residue_ids('ExpStructure', ['Model', 'Scaffold'])''')

    print(chain_mapper.get_differing_atom_residue_ids('ExpStructure', ['Model', 'Scaffold']))
    colortext.message('''chain_mapper.get_differing_atom_residue_ids('Scaffold', ['Model', 'ExpStructure'])''')
    print(chain_mapper.get_differing_atom_residue_ids('Scaffold', ['Model', 'ExpStructure']))
    colortext.message('''chain_mapper.get_differing_atom_residue_ids('Model', ['Scaffold', 'ExpStructure'])''')
    print(chain_mapper.get_differing_atom_residue_ids('Model', ['Scaffold', 'ExpStructure']))

    PSE_file, PSE_script = chain_mapper.generate_pymol_session(pymol_executable = 'pymol', settings = {'colors' : {'global' : {'background-color' : 'black'}}})
    colortext.warning(PSE_script)

    if PSE_file:
        print('Length of PSE file: %d' % len(PSE_file))
        write_file('alignment_test.pse', PSE_file, ftype = 'wb')
    else:
        print('No PSE file was generated.')


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
    #print('\n\n'.join(chain_mapper.get_sequence_alignment_strings(['Model', 'Scaffold', 'ExpStructure'], width = 120)))
    print('\n\n'.join(chain_mapper.get_sequence_alignment_strings(['Scaffold', 'Model', 'ExpStructure'], width = 120)))

    # Example of how to print out a HTML formatted alignment. This output would require CSS for an appropriate presentation.
    colortext.warning('Sequence alignment - HTML formatting, width = 100.')
    colortext.message(chain_mapper.get_sequence_alignment_strings_as_html(['Model', 'Scaffold', 'ExpStructure'], width = 100))
    sys.exit(0)

    # Example of how to generate a PyMOL session
    PSE_file, PSE_script = chain_mapper.generate_pymol_session(pymol_executable = 'pymol', settings = {'colors' : {'global' : {'background-color' : 'black'}}})
    if PSE_file:
        print('Length of PSE file: %d' % len(PSE_file))
        write_file('alignment_test.pse', PSE_file, ftype = 'wb')
    else:
        print('No PSE file was generated.')

    print(PSE_script)

















#### Deprecated ####

# todo: remove this class in favor of PipelinePDBChainMapper
#       PipelinePDBChainMapper quotients the set of structures by ATOM sequence
#       This allows it to scale better for cases with large numbers of structures but with few unique structures up to ATOM sequence
#       The only reason to keep PipelinePDBChainMapper_old in use is in case PipelinePDBChainMapper breaks any existing code and we want a quick fix
class PipelinePDBChainMapper_old(BasePDBChainMapper):
    '''Similar to the removed PDBChainMapper class except this takes a list of PDB files which should be related in some way.
       The matching is done pointwise, matching all PDBs in the list to each other.
       This class is useful for a list of structures that are the result of a linear pipeline e.g. a scaffold structure (RCSB),
       a model structure (Rosetta), and a design structure (experimental result).

       The 'chain_mapping' member stores a mapping from a pair (pdb_name1, pdb_name2) to the mapping from chain IDs in pdb_name1 to
       a MatchedChainList object. This object can be used to return the list of chain IDs in pdb_name2 related to the
       respective chain in pdb_name1 based on sequence alignment. It can also be used to return the percentage identities
       for this alignment. The old mapping and mapping_percentage_identity members of this class can be built from this member
       e.g.
            self.mapping[('Scaffold', 'ExpStructure')] == self.get_chain_mapping('Scaffold', 'ExpStructure')

       The 'residue_id_mapping' member stores a mapping from a pair (pdb_name1, pdb_name2) to a mapping
            'ATOM' -> chains_of_pdb_name_1 -> ATOM residues of that chain -> list of corresponding ATOM residues in the corresponding chains of pdb_name2
            'SEQRES' -> chains_of_pdb_name_1 -> SEQRES residues of that chain -> pairs of (chain_id, corresponding SEQRES residue_id) in the corresponding chains of pdb_name2
       For example, using the homodimer 3MW0 for both Scaffold and ExpStructure:
        residue_id_mapping[('Scaffold', 'ExpStructure')]['ATOM']['A'] -> {'A 167 ': ['A 167 ', 'B 167 '], ...}
        residue_id_mapping[('Scaffold', 'ExpStructure')]['SEQRES']['B'] -> {167 : [('A', 167), ('C', 167)], ...}

       Objects of this class have a differing_atom_residue_ids mapping which maps the pair (pdb_name1, pdb_name2) to the list
       of ATOM residues *in pdb_name1* that differ from those of pdb_name2. Note: there is some subtlety here in terms of
       direction. For example, take this artificial example. We take a homodimer 3MWO as the scaffold and a monomer 1BN1
       with identical sequence as the model. We mutate A110 in 1BN1. We then take 3MWO with a mutation on A106 as the design.
         chain_mapper = ScaffoldModelDesignChainMapper.from_file_contents(retrieve_pdb('3MWO'), retrieve_pdb('1BN1').replace('ASP A 110', 'ASN A 110'), retrieve_pdb('3MWO').replace('GLU A 106', 'GLN A 106'))
       differing_atom_residue_ids then looks like this:
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

       If use_seqres_sequences_if_possible is set, the alignment will use the SEQRES sequences when available. See match_pdb_chains
       for more information.
       '''

    # Constructors

    @staticmethod
    def from_file_paths(pdb_paths, pdb_names, cut_off = 60.0, use_seqres_sequences_if_possible = True, strict = True):
        assert(len(pdb_paths) == len(pdb_names) and len(pdb_paths) > 1)

        pdbs = []
        stage = None
        try:
            for x in range(len(pdb_paths)):
                stage = pdb_names[x]
                pdb_path = pdb_paths[x]
                pdbs.append(PDB.from_filepath(pdb_path), strict = strict)
        except (PDBParsingException, NonCanonicalResidueException, PDBValidationException), e:
            raise PDBParsingException("An error occurred while loading the %s structure: '%s'" % (stage, str(e)))

        return PipelinePDBChainMapper(pdbs, pdb_names, cut_off = cut_off, use_seqres_sequences_if_possible = use_seqres_sequences_if_possible, strict = strict)


    def __init__(self, pdbs, pdb_names, cut_off = 60.0, use_seqres_sequences_if_possible = True, strict = True):

        assert(len(pdbs) == len(pdb_names) and len(pdbs) > 1)
        assert(len(set(pdb_names)) == len(pdb_names)) # pdb_names must be a list of unique names

        self.pdbs = pdbs
        self.pdb_names = pdb_names
        self.use_seqres_sequences_if_possible = use_seqres_sequences_if_possible
        self.strict = strict

        self.pdb_name_to_structure_mapping = {}
        for x in range(len(pdb_names)):
            self.pdb_name_to_structure_mapping[pdb_names[x]] = pdbs[x]

        # differing_atom_residue_ids is a mapping from (pdb_name1, pdb_name2) to the list of ATOM residues *in pdb_name1* that differ from those of pdb_name2
        self.differing_atom_residue_ids = {}
        self.chain_mapping = {}

        # For each pair of adjacent PDB files in the list, match each chain in the first pdb to its best match in the second pdb
        # This section just creates the chain id->chain id mapping
        for x in range(len(pdbs) - 1):
            for y in range(x + 1, len(pdbs)):
                pdb1, pdb2 = pdbs[x], pdbs[y]
                pdb1_name, pdb2_name = pdb_names[x], pdb_names[y]

                mapping_key = (pdb1_name, pdb2_name)
                self.chain_mapping[mapping_key] = {}
                self.differing_atom_residue_ids[mapping_key] = {}

                # To allow for X cases, we allow the matcher to return multiple matches
                # An artificial example X case would be 3MWO -> 1BN1 -> 3MWO where 3MWO_A and 3MWO_B both map to 1BN1_A
                # In this case, we would like 1BN1_A to map to both 3MWO_A and 3MWO_B.
                chain_matches = match_pdb_chains(pdb1, pdb1_name, pdb2, pdb2_name, cut_off = cut_off, allow_multiple_matches = True, multiple_match_error_margin = 3.0, use_seqres_sequences_if_possible = self.use_seqres_sequences_if_possible)

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
                self.differing_atom_residue_ids[mapping_key] = {}

                chain_matches = match_pdb_chains(pdb2, pdb2_name, pdb1, pdb1_name, cut_off = cut_off, allow_multiple_matches = True, multiple_match_error_margin = 3.0, use_seqres_sequences_if_possible = self.use_seqres_sequences_if_possible)
                for pdb2_chain_id, list_of_matches in chain_matches.iteritems():
                    if list_of_matches:
                        mcl = MatchedChainList(pdb2_name, pdb2_chain_id)
                        for l in list_of_matches:
                            mcl.add_chain(pdb1_name, l[0], l[1])
                        self.chain_mapping[mapping_key][pdb2_chain_id] = mcl

        self.residue_id_mapping = {}

        # Create the residue ID -> residue ID mapping based on the chain mapping
        self._map_residues()


    # Private functions


    def _map_residues(self):
        '''For each pair of PDB files, match the residues of a chain in the first PDB to the residues of appropriate chains in the second PDB.

            Note: we do a lot of repeated work here. Some of the lookups e.g. atom_sequences/seqres_sequences here could be cached.
            If speed is important and the sequences are expected to be similar or have lots of repeats, we could use a list of unique sequences
            as equivalence class representatives and then duplicate the matching for the other equivalent sequences.'''

        pdbs = self.pdbs
        pdb_names = self.pdb_names

        # Map the SEQRES sequences to the ATOM sequences
        # Note: The correct way to do this for RCSB files would be to use the SIFTS information like the ResidueRelatrix
        # does. However, we have to consider the case where users upload PDB files which have not yet been deposited in
        # the PDB so we have to resort to automatic sequence alignments. Ideally, we would store these alignments in a
        # database and then do a lookup at this point. This would not only speed up the computation here but also allow
        # us to manually fix misalignments (which will probably only occur due to gaps rather than mismatches).
        seqres_to_atom_maps = {}
        atom_to_seqres_maps = {}
        for x in range(len(pdbs)):
            pdb_object = pdbs[x]
            pdb_name = pdb_names[x]
            seqres_to_atom_map, atom_to_seqres_map = pdb_object.construct_seqres_to_atom_residue_map()
            seqres_to_atom_maps[pdb_name] = seqres_to_atom_map
            atom_to_seqres_maps[pdb_name] = atom_to_seqres_map

        # Iterate over all pairs of PDBs and determine the residue mapping and sets of differing ATOM residues
        for x in range(len(pdbs) - 1):
            for y in range(x + 1, len(pdbs)):
                pdb1, pdb2 = pdbs[x], pdbs[y]
                pdb1_name, pdb2_name = pdb_names[x], pdb_names[y]
                mapping_key = (pdb1_name, pdb2_name)
                reverse_mapping_key = mapping_key[::-1]

                residue_id_mapping = {'ATOM' : {}, 'SEQRES' : {}} # todo: add the other types of mapping here e.g. FASTA and Rosetta
                pdb1_differing_atom_residue_ids = []
                pdb2_differing_atom_residue_ids = []

                for pdb1_chain, pdb2_chains in self.get_chain_mapping(mapping_key[0], mapping_key[1]).iteritems():
                #for pdb1_chain, pdb2_chain in self.chain_mapping[mapping_key].iteritems():

                    residue_id_mapping['ATOM'][pdb1_chain] = {}
                    residue_id_mapping['SEQRES'][pdb1_chain] = {}

                    # Use the SEQRES or ATOM sequence appropriately
                    pdb1_chain_sequence_type, pdb1_chain_sequence = pdb1.get_annotated_chain_sequence_string(pdb1_chain, self.use_seqres_sequences_if_possible)

                    for pdb2_chain in pdb2_chains:
                        # Get the mapping between the sequences
                        # Note: sequences and mappings are 1-based following the UniProt convention
                        # The mapping returned from sa.get_residue_mapping is an abstract mapping between *sequences of characters*
                        # and knows nothing about residue identifiers e.g. ATOM residue IDs or whether the sequences are
                        # SEQRES or ATOM sequences

                        sa = SequenceAligner()
                        pdb2_chain_sequence_type, pdb2_chain_sequence = pdb2.get_annotated_chain_sequence_string(pdb2_chain, self.use_seqres_sequences_if_possible)

                        sa.add_sequence('%s_%s' % (pdb1_name, pdb1_chain), str(pdb1_chain_sequence))
                        sa.add_sequence('%s_%s' % (pdb2_name, pdb2_chain), str(pdb2_chain_sequence))
                        mapping, match_mapping = sa.get_residue_mapping()

                        # Since the mapping is only between sequences and we wish to use the original residue identifiers of
                        # the sequence e.g. the PDB/ATOM residue ID, we look this information up in the order mapping of the
                        # Sequence objects
                        for pdb1_residue_index, pdb2_residue_index in mapping.iteritems():
                            pdb1_residue_id = pdb1_chain_sequence.order[pdb1_residue_index - 1] # order is a 0-based list
                            pdb2_residue_id = pdb2_chain_sequence.order[pdb2_residue_index - 1] # order is a 0-based list
                            pdb1_atom_residue_id, pdb2_atom_residue_id = None, None

                            if pdb1_chain_sequence_type == 'SEQRES' and pdb2_chain_sequence_type == 'SEQRES':
                                residue_id_mapping['SEQRES'][pdb1_chain][pdb1_residue_id] = residue_id_mapping['SEQRES'][pdb1_chain].get(pdb1_residue_id, [])
                                residue_id_mapping['SEQRES'][pdb1_chain][pdb1_residue_id].append((pdb2_chain, pdb2_residue_id))

                                pdb1_atom_residue_id = seqres_to_atom_maps.get(pdb1_name, {}).get(pdb1_chain, {}).get(pdb1_residue_id)
                                pdb2_atom_residue_id = seqres_to_atom_maps.get(pdb2_name, {}).get(pdb2_chain, {}).get(pdb2_residue_id)
                                if pdb1_atom_residue_id != None and pdb2_atom_residue_id != None:
                                    residue_id_mapping['ATOM'][pdb1_chain][pdb1_atom_residue_id] = residue_id_mapping['ATOM'][pdb1_chain].get(pdb1_atom_residue_id, [])
                                    residue_id_mapping['ATOM'][pdb1_chain][pdb1_atom_residue_id].append(pdb2_atom_residue_id)

                            elif pdb1_chain_sequence_type == 'SEQRES' and pdb2_chain_sequence_type == 'ATOM':
                                pdb1_atom_residue_id = seqres_to_atom_maps.get(pdb1_name, {}).get(pdb1_chain, {}).get(pdb1_residue_id)
                                if pdb1_atom_residue_id != None:
                                    residue_id_mapping['ATOM'][pdb1_chain][pdb1_atom_residue_id] = residue_id_mapping['ATOM'][pdb1_chain].get(pdb1_atom_residue_id, [])
                                    residue_id_mapping['ATOM'][pdb1_chain][pdb1_atom_residue_id].append(pdb2_residue_id)

                            elif pdb1_chain_sequence_type == 'ATOM' and pdb2_chain_sequence_type == 'SEQRES':
                                pdb2_atom_residue_id = seqres_to_atom_maps.get(pdb2_name, {}).get(pdb2_chain, {}).get(pdb2_residue_id)
                                if pdb2_atom_residue_id != None:
                                    residue_id_mapping['ATOM'][pdb1_chain][pdb1_residue_id] = residue_id_mapping['ATOM'][pdb1_chain].get(pdb1_residue_id, [])
                                    residue_id_mapping['ATOM'][pdb1_chain][pdb1_residue_id].append(pdb2_atom_residue_id)

                            elif pdb1_chain_sequence_type == 'ATOM' and pdb2_chain_sequence_type == 'ATOM':
                                residue_id_mapping['ATOM'][pdb1_chain][pdb1_residue_id] = residue_id_mapping['ATOM'][pdb1_chain].get(pdb1_residue_id, [])
                                residue_id_mapping['ATOM'][pdb1_chain][pdb1_residue_id].append(pdb2_residue_id)
                            else:
                                raise Exception('An exception occurred.') # this should not happen

                            # We store a *list* of corresponding residues i.e. if pdb1_chain matches pdb2_chain_1 and pdb2_chain_2
                            # then we may map a residue in pdb1_chain to a residue in each of those chains
                            #residue_id_mapping[pdb1_chain][pdb1_residue_id] = residue_id_mapping[pdb1_chain].get(pdb1_residue_id, [])
                            #residue_id_mapping[pdb1_chain][pdb1_residue_id].append(pdb2_residue_id)

                        # Determine which residues of each sequence differ between the sequences
                        # We ignore leading and trailing residues from both sequences
                        pdb1_residue_indices = mapping.keys()
                        pdb2_residue_indices = mapping.values()
                        differing_pdb1_indices = []
                        differing_pdb2_indices = []
                        for pdb1_residue_index, match_details in match_mapping.iteritems():
                            if match_details.clustal == 0 or match_details.clustal == -1 or match_details.clustal == -2:
                                # The residues differed
                                differing_pdb1_indices.append(pdb1_residue_index)
                                differing_pdb2_indices.append(mapping[pdb1_residue_index])

                        # Convert the different sequence indices into PDB ATOM residue IDs. Sometimes there may not be a
                        # mapping from SEQRES residues to the ATOM residues e.g. missing density
                        for idx in differing_pdb1_indices:
                            if pdb1_chain_sequence_type == 'SEQRES':
                                pdb1_seqres_residue_id = pdb1_chain_sequence.order[idx - 1]
                                pdb1_atom_residue_id = seqres_to_atom_maps.get(pdb1_name, {}).get(pdb1_chain, {}).get(pdb1_seqres_residue_id)
                                if pdb1_atom_residue_id != None:
                                    pdb1_differing_atom_residue_ids.append(pdb1_atom_residue_id)
                            elif pdb1_chain_sequence_type == 'ATOM':
                                pdb1_differing_atom_residue_ids.append(pdb1_chain_sequence.order[idx - 1])
                        for idx in differing_pdb2_indices:
                            if pdb2_chain_sequence_type == 'SEQRES':
                                pdb2_seqres_residue_id = pdb2_chain_sequence.order[idx - 1]
                                pdb2_atom_residue_id = seqres_to_atom_maps.get(pdb2_name, {}).get(pdb2_chain, {}).get(pdb2_seqres_residue_id)
                                if pdb2_atom_residue_id != None:
                                    pdb2_differing_atom_residue_ids.append(pdb2_atom_residue_id)
                            elif pdb2_chain_sequence_type == 'ATOM':
                                pdb2_differing_atom_residue_ids.append(pdb2_chain_sequence.order[idx - 1])

                self.residue_id_mapping[mapping_key] = residue_id_mapping
                self.differing_atom_residue_ids[mapping_key] = pdb1_differing_atom_residue_ids
                self.differing_atom_residue_ids[reverse_mapping_key] = pdb2_differing_atom_residue_ids

        for k, v in sorted(self.differing_atom_residue_ids.iteritems()):
            self.differing_atom_residue_ids[k] = sorted(set(v)) # the list of residues may not be unique in general so we make it unique here

        self.seqres_to_atom_maps = seqres_to_atom_maps
        self.atom_to_seqres_maps = atom_to_seqres_maps

    # Public functions


    def get_chain_mapping(self, pdb_name1, pdb_name2):
        '''This replaces the old mapping member by constructing it from self.chain_mapping. This function returns a mapping from
        chain IDs in pdb_name1 to chain IDs in pdb_name2.'''
        d = {}
        for pdb1_chain_id, matched_chain_list in self.chain_mapping[(pdb_name1, pdb_name2)].iteritems():
            d[pdb1_chain_id] = matched_chain_list.get_related_chains_ids(pdb_name2)
        return d


    def get_differing_atom_residue_ids(self, pdb_name, pdb_list):
        '''Returns a list of residues in pdb_name which differ from the pdbs corresponding to the names in pdb_list.'''

        assert(pdb_name in self.pdb_names)
        assert(set(pdb_list).intersection(set(self.pdb_names)) == set(pdb_list)) # the names in pdb_list must be in pdb_names

        differing_atom_residue_ids = set()
        for other_pdb in pdb_list:
            differing_atom_residue_ids = differing_atom_residue_ids.union(set(self.differing_atom_residue_ids[(pdb_name, other_pdb)]))

        return sorted(differing_atom_residue_ids)


    def get_sequence_alignment_printer_objects(self, pdb_list = [], reversed = True, width = 80, line_separator = '\n'):
        '''Takes a list, pdb_list, of pdb names e.g. ['Model', 'Scaffold', ...] with which the object was created.
            Using the first element of this list as a base, get the sequence alignments with chains in other members
            of the list. For simplicity, if a chain in the first PDB matches multiple chains in another PDB, we only
            return the alignment for one of the chains. If pdb_list is empty then the function defaults to the object's
            members.

            Returns a list of tuples (chain_id, sequence_alignment_printer_object). Each sequence_alignment_printer_object
            can be used to generate a printable version of the sequence alignment. '''

        if not pdb_list:
            pdb_list = self.pdb_names

        assert(len(set(pdb_list)) == len(pdb_list) and (len(pdb_list) > 1))
        assert(sorted(set(pdb_list).intersection(set(self.pdb_names))) == sorted(set(pdb_list)))

        primary_pdb = self.pdb_name_to_structure_mapping[pdb_list[0]]
        primary_pdb_name = pdb_list[0]
        primary_pdb_chains = sorted(primary_pdb.chain_atoms.keys())

        sequence_alignment_printer_objects = []
        for primary_pdb_chain in primary_pdb_chains:

            sa = SequenceAligner()

            # Add the primary PDB's sequence for the chain
            primary_pdb_sequence_type, primary_pdb_sequence = primary_pdb.get_annotated_chain_sequence_string(primary_pdb_chain, self.use_seqres_sequences_if_possible)
            sa.add_sequence('%s_%s' % (primary_pdb_name, primary_pdb_chain), str(primary_pdb_sequence))
            other_chain_types_and_sequences = {}
            for other_pdb_name in pdb_list[1:]:
                other_pdb = self.pdb_name_to_structure_mapping[other_pdb_name]
                other_chains = self.get_chain_mapping(primary_pdb_name, other_pdb_name).get(primary_pdb_chain)
                #other_chain = self.mapping[(primary_pdb_name, other_pdb_name)].get(primary_pdb_chain)
                if other_chains:
                    other_chain = sorted(other_chains)[0]
                    other_pdb_sequence_type, other_pdb_sequence = other_pdb.get_annotated_chain_sequence_string(other_chain, self.use_seqres_sequences_if_possible)
                    other_chain_types_and_sequences[other_pdb_name] = (other_pdb_sequence_type, other_pdb_sequence)
                    sa.add_sequence('%s_%s' % (other_pdb_name, other_chain), str(other_pdb_sequence))

            if len(sa.records) > 1:
                # If there are no corresponding sequences in any other PDB, do not return the non-alignment
                sa.align()

                #pdb1_alignment_str = sa._get_alignment_lines()['%s:%s' % (primary_pdb_name, pdb1_chain)]
                #pdb2_alignment_str = sa._get_alignment_lines()['%s:%s' % (pdb2_name, pdb2_chain)]

                sequence_names, sequences, sequence_tooltips = [], [], []

                sequence_names.append('%s_%s' % (primary_pdb_name, primary_pdb_chain))
                primary_pdb_alignment_lines = sa._get_alignment_lines()['%s_%s' % (primary_pdb_name, primary_pdb_chain)]
                sequences.append(primary_pdb_alignment_lines)
                sequence_tooltips.append(self.get_sequence_tooltips(primary_pdb, primary_pdb_sequence, primary_pdb_sequence_type, primary_pdb_name, primary_pdb_chain, primary_pdb_alignment_lines))
                for other_pdb_name in pdb_list[1:]:
                    #other_chain = self.mapping[(primary_pdb_name, other_pdb_name)].get(primary_pdb_chain)
                    other_pdb = self.pdb_name_to_structure_mapping[other_pdb_name]
                    other_chains = self.get_chain_mapping(primary_pdb_name, other_pdb_name).get(primary_pdb_chain)
                    if other_chains:
                        other_chain = sorted(other_chains)[0]
                        sequence_names.append('%s_%s' % (other_pdb_name, other_chain))
                        other_pdb_alignment_lines = sa._get_alignment_lines()['%s_%s' % (other_pdb_name, other_chain)]
                        sequences.append(other_pdb_alignment_lines)
                        other_pdb_sequence_type, other_pdb_sequence = other_chain_types_and_sequences[other_pdb_name]
                        sequence_tooltips.append(self.get_sequence_tooltips(other_pdb, other_pdb_sequence, other_pdb_sequence_type, other_pdb_name, other_chain, other_pdb_alignment_lines))

                sap = MultipleSequenceAlignmentPrinter(sequence_names, sequences, sequence_tooltips)
                sequence_alignment_printer_objects.append((primary_pdb_chain, sap))

        return sequence_alignment_printer_objects

    def get_sequence_tooltips(self, pdb_object, pdb_sequence, pdb_sequence_type, pdb_name, pdb_chain, pdb_alignment_lines):
        '''pdb_sequence is a Sequence object. pdb_sequence_type is a type returned by PDB.get_annotated_chain_sequence_string,
           pdb_name is the name of the PDB used throughout this object e.g. 'Scaffold', pdb_chain is the chain of interest,
           pdb_alignment_lines are the lines returned by SequenceAligner._get_alignment_lines.

           This function returns a set of tooltips corresponding to the residues in the sequence. The tooltips are the ATOM
           residue IDs. These tooltips can be used to generate useful (and/or interactive using JavaScript) sequence alignments
           in HTML.
           '''
        tooltips = None
        atom_sequence = pdb_object.atom_sequences.get(pdb_chain)

        try:
            if pdb_sequence_type == 'SEQRES':
                seqres_to_atom_map = self.seqres_to_atom_maps.get(pdb_name, {}).get(pdb_chain, {})
                tooltips = []
                if seqres_to_atom_map:
                    idx = 1
                    for aligned_residue in pdb_alignment_lines.strip():
                        if aligned_residue != '-':
                            atom_residue = seqres_to_atom_map.get(idx)
                            if atom_residue:
                                # This is a sanity check to make sure that the tooltips are mapping the correct residues types to
                                # the correct residues types
                                assert(aligned_residue == atom_sequence.sequence[atom_residue].ResidueAA)
                            tooltips.append(atom_residue)
                            idx += 1
                    assert(len(tooltips) == len(str(pdb_sequence)))
            elif pdb_sequence_type == 'ATOM':
                tooltips = []
                idx = 0
                for aligned_residue in pdb_alignment_lines.strip():
                    if aligned_residue != '-':
                        # This is a sanity check to make sure that the tooltips are mapping the correct residues types to
                        # the correct residues types
                        assert(aligned_residue == pdb_sequence.sequence[pdb_sequence.order[idx]].ResidueAA)
                        tooltips.append(pdb_sequence.order[idx])
                        idx += 1
                assert(len(tooltips) == len(str(pdb_sequence)))
        except:
            raise Exception('An error occurred during HTML tooltip creation for the multiple sequence alignment.')

        return tooltips


    def get_sequence_alignment_strings(self, pdb_list = [], reversed = True, width = 80, line_separator = '\n'):
        '''Takes a list, pdb_list, of pdb names e.g. ['Model', 'Scaffold', ...] with which the object was created.
            Using the first element of this list as a base, get the sequence alignments with chains in other members
            of the list. For simplicity, if a chain in the first PDB matches multiple chains in another PDB, we only
            return the alignment for one of the chains. If pdb_list is empty then the function defaults to the object's
            members.

            Returns one sequence alignment string for each chain mapping. Each line is a concatenation of lines of the
            specified width, separated by the specified line separator.'''

        sequence_alignment_printer_tuples = self.get_sequence_alignment_printer_objects(pdb_list = pdb_list, reversed = reversed, width = width, line_separator = line_separator)
        alignment_strings = []
        for sequence_alignment_printer_tuple in sequence_alignment_printer_tuples:
            primary_pdb_chain = sequence_alignment_printer_tuple[0]
            sap = sequence_alignment_printer_tuple[1]
            alignment_strings.append(sap.to_lines(reversed = reversed, width = width, line_separator = line_separator))

        return alignment_strings


    def get_sequence_alignment_strings_as_html(self, pdb_list = [], reversed = False, width = 80, line_separator = '\n', extra_tooltip_class = ''):
        '''Takes a list, pdb_list, of pdb names e.g. ['Model', 'Scaffold', ...] with which the object was created.
            Using the first element of this list as a base, get the sequence alignments with chains in other members
            of the list. For simplicity, if a chain in the first PDB matches multiple chains in another PDB, we only
            return the alignment for one of the chains. If pdb_list is empty then the function defaults to the object's
            members.

            Returns HTML for the sequence alignments and an empty string if no alignments were made.'''
        sequence_alignment_printer_tuples = self.get_sequence_alignment_printer_objects(pdb_list = pdb_list, reversed = reversed, width = width, line_separator = line_separator)
        if not sequence_alignment_printer_tuples:
            return ''
        html = []
        for sequence_alignment_printer_tuple in sequence_alignment_printer_tuples:
            primary_pdb_chain = sequence_alignment_printer_tuple[0]
            sap = sequence_alignment_printer_tuple[1]
            html.append(sap.to_html(reversed = reversed, width = width, line_separator = line_separator, extra_tooltip_class = extra_tooltip_class))

        return '\n'.join(html)
