#!/usr/bin/python
# encoding: utf-8
"""
alignment.py
Higher-level alignment functionality which uses the clustalo module and the PyMOL PSE builder module.

Created by Shane O'Connor 2014.
"""

import sys
sys.path.insert(0, '../../..')

from tools import colortext
from tools.bio.pymol.psebuilder import BatchBuilder, PDBContainer
from tools.bio.pymol.scaffold_design_crystal import ScaffoldDesignCrystalBuilder
from tools.bio.pdb import PDB
from tools.bio.clustalo import SequenceAligner

def match_pdb_chains(pdb1, pdb1_name, pdb2, pdb2_name, cut_off = 60.0):
    '''Aligns two PDB files, returning a mapping from the chains in pdb1 to the chains of pdb2.
       We return the best match for each chain in pdb1 if a match exists. The return value is a dict mapping
            chain_id_in_pdb1 -> None or a tuple (chain_id_in_pdb_2, percentage_identity_score)
       where percentage_identity_score is a float.

       Parameters: pdb1 and pdb2 are PDB objects from tools.bio.pdb. pdb1_name and pdb2_name are strings describing the
        structures e.g. 'Design' and 'Scaffold'. cut_off is used in the matching to discard low-matching chains.
       '''

    pdb1_chains = pdb1.atom_sequences.keys()
    pdb2_chains = pdb2.atom_sequences.keys()

    sa = SequenceAligner()
    for c in pdb1_chains:
        sa.add_sequence('%s:%s' % (pdb1_name, c), str(pdb1.atom_sequences[c]))
    for c in pdb2_chains:
        sa.add_sequence('%s:%s' % (pdb2_name, c), str(pdb2.atom_sequences[c]))
    sa.align()

    chain_matches = dict.fromkeys(pdb2_chains, None)
    for c in pdb1_chains:
        best_matches_by_id = sa.get_best_matches_by_id('%s:%s' % (pdb1_name, c), cut_off = cut_off)
        if best_matches_by_id:
            t = []
            for k, v in best_matches_by_id.iteritems():
                if k.startswith(pdb2_name):
                    t.append((v, k))
            if t:
                best_match = sorted(t)[0]
                chain_matches[c] = (best_match[1].split(':')[1], best_match[0])

    return chain_matches

class SequenceAlignmentPrinter(object):

    def __init__(self, seq1_name, seq1_sequence, seq2_name, seq2_sequence):
        self.seq1_name = seq1_name
        self.seq1_sequence = seq1_sequence
        self.seq2_name = seq2_name
        self.seq2_sequence = seq2_sequence

    def to_lines(self, width = 80, reversed = False, line_separator = '\n'):
        s = []
        label_width = max(len(self.seq1_name), len(self.seq2_name))
        if label_width + 2 < width and len(self.seq1_name) == len(self.seq1_name):
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

class PDBChainMapper(object):
    '''Uses the match_pdb_chains function to map the chains of pdb1 to the chains of pdb2. The mapping member stores
        the mapping between chains when a mapping is found. The mapping_percentage_identity member stores how close the
        mapping was in terms of percentage identity.
    '''
    def __init__(self, pdb1, pdb1_name, pdb2, pdb2_name, cut_off = 60.0):
        self.pdb1 = pdb1
        self.pdb2 = pdb2
        self.pdb1_name = pdb1_name
        self.pdb2_name = pdb2_name
        self.mapping = {}
        self.mapping_percentage_identity = {}

        # Match each chain in pdb1 to its best match in pdb2
        self.chain_matches = match_pdb_chains(pdb1, pdb1_name, pdb2, pdb2_name, cut_off = cut_off)
        for k, v in self.chain_matches.iteritems():
            self.mapping[k] = v[0]
            self.mapping_percentage_identity[k] = v[1]

        self.pdb1_differing_residue_ids = []
        self.pdb2_differing_residue_ids = []
        self.residue_id_mapping = {}
        self.map_residues()

    @staticmethod
    def from_file_paths(pdb1_path, pdb1_name, pdb2_path, pdb2_name, cut_off = 60.0):
        pdb1 = PDB.from_filepath(pdb1_path)
        pdb2 = PDB.from_filepath(pdb2_path)
        return PDBChainMapper(pdb1, pdb1_name, pdb2, pdb2_name, cut_off = cut_off)

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
            for line in lines:
                tokens = line.split()
                assert(len(tokens) == 2)
                html.append('<div class="sequence_alignment_line"><span>%s</span><span>%s</span></div>' % (tokens[0], tokens[1]))
            html.append('<div class="sequence_alignment_chain_separator"></div>')

        html.pop() # remove the last chain separator div
        return '\n'.join(html)

    def map_residues(self):
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

class ScaffoldDesignChainMapper(PDBChainMapper):
    '''A convenience class for the special case where we are mapping specifically from a design structure to a scaffold structure.'''
    def __init__(self, scaffold_pdb, design_pdb, cut_off = 60.0):
        self.design_pdb = design_pdb
        self.scaffold_pdb = scaffold_pdb
        super(ScaffoldDesignChainMapper, self).__init__(design_pdb, 'Design', scaffold_pdb, 'Scaffold', cut_off)

    @staticmethod
    def from_file_paths(scaffold_pdb_path, design_pdb_path, cut_off = 60.0):
        scaffold_pdb = PDB.from_filepath(scaffold_pdb_path)
        design_pdb = PDB.from_filepath(design_pdb_path)
        return ScaffoldDesignChainMapper(scaffold_pdb, design_pdb, cut_off = cut_off)

    @staticmethod
    def from_file_contents(scaffold_pdb_contents, design_pdb_contents, cut_off = 60.0):
        scaffold_pdb = PDB(scaffold_pdb_contents)
        design_pdb = PDB(design_pdb_contents)
        return ScaffoldDesignChainMapper(scaffold_pdb, design_pdb, cut_off = cut_off)

    def get_differing_design_residue_ids(self):
        return self.pdb1_differing_residue_ids

    def get_differing_scaffold_residue_ids(self):
        return self.pdb2_differing_residue_ids

    def generate_pymol_session(self, crystal_pdb = None):
        b = BatchBuilder()
        structures_list = [
            ('Scaffold', self.scaffold_pdb.pdb_content, self.get_differing_scaffold_residue_ids()),
            ('Design', self.design_pdb.pdb_content, self.get_differing_design_residue_ids()),
        ]

        if crystal_pdb:
            structures_list.append(('Crystal', crystal_pdb.pdb_content, self.get_differing_scaffold_residue_ids()))

        PSE_files = b.run(ScaffoldDesignCrystalBuilder, [PDBContainer.from_content_triple(structures_list)])
        return PSE_files[0]

if __name__ == '__main__':
    from tools.fs.fsio import read_file

    # Example of how to create a mapper from file paths
    chain_mapper = ScaffoldDesignChainMapper.from_file_paths('../.testdata/1z1s_DIG5_scaffold.pdb', '../.testdata/DIG5_1_model.pdb')

    # Example of how to create a mapper from file contents
    chain_mapper = ScaffoldDesignChainMapper.from_file_contents(read_file('../.testdata/1z1s_DIG5_scaffold.pdb'), read_file('../.testdata/DIG5_1_model.pdb'))

    # Example of how to get residue -> residue mapping
    for chain_id, mapping in sorted(chain_mapper.residue_id_mapping.iteritems()):
        colortext.message('Mapping from chain %s of the design to the scaffold' % chain_id)
        for design_res, scaffold_res in sorted(mapping.iteritems()):
            print("\t'%s' -> '%s'" % (design_res, scaffold_res))

    # Example of how to list the PDB residue IDs for the positions in the design which differ
    colortext.message('Residues IDs for the residues which differ in the design.')
    print(chain_mapper.get_differing_design_residue_ids())

    # Example of how to list the PDB residue IDs for the positions in the scaffold which differ
    colortext.message('Residues IDs for the residues which differ in the scaffold.')
    print(chain_mapper.get_differing_scaffold_residue_ids())

    # Example of how to print out a plaintext sequence alignment
    colortext.warning('Sequence alignment - plain formatting, width = 120.')
    print('\n\n'.join(chain_mapper.get_sequence_alignment_strings(width = 120)))

    # Example of how to print out a HTML formatted alignment. This output would require CSS for an appropriate presentation.
    colortext.warning('Sequence alignment - HTML formatting, width = 100.')
    colortext.message(chain_mapper.get_sequence_alignment_strings_as_html(width = 100))

    # Example of how to generate a PyMOL session
    PSE_file = chain_mapper.generate_pymol_session()

