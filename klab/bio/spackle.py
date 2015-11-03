#!/usr/bin/python
# encoding: utf-8
"""
spackle.py
Functions to add missing structure to a PDB structure.
These functions are not intended to do anything clever just add information to allow computational methods to run.

Created by Shane O'Connor 2015.
These functions rely on the PDB class but it seems to make sense to separate them.
"""

import re
import sys
import os
import types
import string
import types
import pprint
import math
import numpy
import json

from klab import colortext
from klab.bio import rcsb
from klab.bio.basics import Residue, PDBResidue, Sequence, SequenceMap, residue_type_1to3_map, residue_type_3to1_map, protonated_residue_type_3to1_map, non_canonical_amino_acids, protonated_residues_types_3, residue_types_3, Mutation, ChainMutation, SimpleMutation
from klab.bio.basics import dna_nucleotides, rna_nucleotides, dna_nucleotides_3to1_map, dna_nucleotides_2to1_map, non_canonical_dna, non_canonical_rna, all_recognized_dna, all_recognized_rna
from klab.bio.pdb import PDB
from klab.bio.fasta import FASTA
from klab.bio.bonsai import Bonsai
from klab.fs.fsio import read_file, write_file
from klab.general.strutil import remove_trailing_line_whitespace as normalize_pdb_file
from klab.pymath.stats import get_mean_and_standard_deviation
from klab.pymath.cartesian import spatialhash
from klab.rosetta.input_files import LoopsFile
from klab.rosetta.map_pdb_residues import get_pdb_contents_to_pose_residue_map


class Spackler(Bonsai):


    def __init__(self, pdb_content, buffer = 0.05, bin_size = 5.1, safe_mode = True, FASTA_line_length = 80):
        super(Spackler, self).__init__(pdb_content, buffer = buffer, bin_size = bin_size, safe_mode = safe_mode, FASTA_line_length = FASTA_line_length)
        self.pdb = PDB(pdb_content)


    def add_backbone_atoms_linearly_from_loop_filepaths(self, loop_json_filepath, fasta_filepath, residue_ids):
        '''A utility wrapper around add_backbone_atoms_linearly. Adds backbone atoms in a straight line from the first to
           the last residue of residue_ids.

           loop_json_filepath is a path to a JSON file using the JSON format for Rosetta loops files. This file identifies
           the insertion points of the sequence.

           fasta_filepath is a path to a FASTA file with one sequence. This sequence will be used as the sequence for
           the inserted residues (between the start and stop residues defined in loop_json_filepath).

           residue_ids is a list of PDB chain residues (columns 22-27 of ATOM lines in the PDB format). It is assumed that
           they are sequential although the logic does not depend on that. This list should have the length length as the
           sequence identified in the FASTA file.
        '''

        # Parse the loop file
        loop_def = json.loads(read_file(loop_json_filepath))
        assert(len(loop_def['LoopSet']) == 1)
        start_res = loop_def['LoopSet'][0]['start']
        end_res = loop_def['LoopSet'][0]['stop']
        start_res = PDB.ChainResidueID2String(start_res['chainID'], (str(start_res['resSeq']) + start_res['iCode']).strip())
        end_res = PDB.ChainResidueID2String(end_res['chainID'], (str(end_res['resSeq']) + end_res['iCode']).strip())
        assert(start_res in residue_ids)
        assert(end_res in residue_ids)

        # Parse the FASTA file and extract the sequence
        f = FASTA(read_file(fasta_filepath), strict = False)
        assert(len(f.get_sequences()) == 1)
        insertion_sequence = f.sequences[0][2]
        if not len(residue_ids) == len(insertion_sequence):
            raise Exception('The sequence in the FASTA file must have the same length as the list of residues.')

        # Create the insertion sequence (a sub-sequence of the FASTA sequence)
        # The post-condition is that the start and end residues are the first and last elements of kept_residues respectively
        kept_residues = []
        insertion_residue_map = {}
        in_section = False
        found_end = False
        for x in range(len(residue_ids)):
            residue_id = residue_ids[x]
            if residue_id == start_res:
                in_section = True
            if in_section:
                kept_residues.append(residue_id)
                insertion_residue_map[residue_id] = insertion_sequence[x]
                if residue_id == end_res:
                    found_end = True
                    break
        if not kept_residues:
            raise Exception('The insertion sequence is empty (check the start and end residue ids).')
        if not found_end:
            raise Exception('The end residue was not encountered when iterating over the insertion sequence (check the start and end residue ids).')

        # Identify the start and end Residue objects
        try:
            start_res = self.residues[start_res[0]][start_res[1:]]
            end_res = self.residues[end_res[0]][end_res[1:]]
        except Exception, e:
            raise Exception('The start or end residue could not be found in the PDB file.')

        return self.add_backbone_atoms_linearly(start_res, end_res, kept_residues, insertion_residue_map)


    def add_backbone_atoms_linearly(self, start_residue, end_residue, insertion_residues, insertion_residue_map):
        '''This function returns the PDB content for a structure with the missing backbone atoms - i.e. it adds the
           N, Ca, C atoms spaced evenly between the last existing backbone atom of start_residue and the first existing
           backbone atom of end_residue. O-atoms are not currently added although we could arbitrarily add them at 90
           degrees to the plane: If resiC_x + x = resjC_x and resiC_y + y = resjC_y, i + 1 = j, then the resiO atom could
           have coordinates (resiC_x - y,  resiC_y + x).

           Adds backbone atoms for insertion_residues in a straight line from start_residue to end_residue. This is useful
           for some computational methods which do not require the atoms to be in the correct coordinates but expect N, CA, and C backbone atoms
           to exist for all residues (O-atoms are currently ignored here).

           start_residue and end_residue are Residue objects. insertion_residues is a list of PDB residue IDs (columns 22-27
           of ATOM lines in the PDB format). insertion_residue_map is a mapping from PDB residue IDs to 1-letter amino acid
           codes. The keys of insertion_residue_map must be insertion_residues.

           start_residue and end_residue must exist in insertion_residues and the PDB file. There is no technical requirement for this;
           we just do not handle the alternate case yet. residue_ids are presumed to be ordered in sequence (N -> C) order.
           Existing N, CA, and C atoms corresponding to these two residues will be retained as long as their atoms which
           connect to the side of those residues not identified by residue_ids are present e.g.
              - if the CA atom of the first residue is present, it will be kept as long as the N atom is present and regardless of whether the C atom is present
              - if the CA atom of the last residue is present, it will be kept as long as the C atom is present and regardless of whether the N atom is present
           All O atoms of residues in residue_ids are discarded. ANISOU records corresponding to any removed ATOMS will be removed.

                   1st    2nd          n-1      n
             ... N-CA-C- N-CA-C- ... N-CA-C- N-CA-C- ..

           Note: This function currently only supports canonical amino acids.
        '''

        assert(sorted(insertion_residues) == sorted(insertion_residue_map.keys()))
        assert(start_residue.chain + start_residue.residue_id in insertion_residues)
        assert(end_residue.chain + end_residue.residue_id in insertion_residues)
        assert(start_residue.chain == end_residue.chain)

        atoms_to_remove = []

        discarded_atoms = []

        # Remove atoms from the segment's N-terminus residue
        # if N and CA and C, keep C else discard C
        start_res_atoms_ids = self.get_atom_serial_numbers_from_pdb_residue_ids([insertion_residues[0]])
        start_res_atoms = [self.atoms[id] for id in start_res_atoms_ids]
        start_res_atom_types = [a.name for a in start_res_atoms]
        start_atoms = [None, None, None]
        for a in start_res_atoms:
            if a.name == 'N': start_atoms[0] = a
            elif a.name == 'CA': start_atoms[1] = a
            elif a.name == 'C': start_atoms[2] = a
            else: discarded_atoms.append(a.serial_number)
        if 'C' in start_res_atom_types and 'CA' not in start_res_atom_types:
            discarded_atoms += start_atoms[2].serial_number
            start_atoms[2] = None
        if not start_atoms[0]:
            raise Exception('The N atom for the start residue must exist.')
        start_atoms = [a for a in start_atoms if a]
        start_atom = start_atoms[-1]

        # Remove atoms from the segment's C-terminus residue
        # if N and CA and C, keep N else discard N
        end_res_atoms_ids = self.get_atom_serial_numbers_from_pdb_residue_ids([insertion_residues[-1]])
        end_res_atoms = [self.atoms[id] for id in end_res_atoms_ids]
        end_res_atom_types = [a.name for a in end_res_atoms]
        end_atoms = [None, None, None]
        for a in end_res_atoms:
            if a.name == 'N': end_atoms[0] = a
            elif a.name == 'CA': end_atoms[1] = a
            elif a.name == 'C': end_atoms[2] = a
            else: discarded_atoms.append(a.serial_number)
        if 'N' in end_res_atom_types and 'CA' not in end_res_atom_types:
            discarded_atoms += end_atoms[0].serial_number
            end_atoms[0] = None
        if not end_atoms[-1]:
            raise Exception('The C atom for the end residue must exist.')
        end_atoms = [a for a in end_atoms if a]
        end_atom = end_atoms[0]

        # Remove all atoms from the remainder of the segment
        discarded_atoms += self.get_atom_serial_numbers_from_pdb_residue_ids(insertion_residues[1:-1])

        # Remove the atoms from the PDB
        bonsai_pdb_content, cutting_pdb_content, PSE_file, PSE_script = self.prune(set(discarded_atoms), generate_pymol_session = False)
        self.__init__(bonsai_pdb_content, buffer = self.buffer, bin_size = self.bin_size, safe_mode = self.safe_mode)

        # Create a list of all N, CA, C atoms for the insertion residues not including those present in the start and end residue
        # Find last of N CA C of first residue
        # Find last of N CA C of first residue
        new_atoms = []
        assert(len(start_atoms) >= 1) # N is guaranteed to exist
        if len(start_atoms) == 2:
            # add a C atom
            residue_id = insertion_residues[0]
            residue_type = insertion_residue_map[residue_id]
            assert(residue_type != 'X' and residue_type in residue_type_1to3_map)
            new_atoms.append((residue_id, residue_type_1to3_map[residue_type], 'C'))
        for insertion_residue in insertion_residues[1:-1]:
            # add an N, CA, C atoms
            residue_type = insertion_residue_map[insertion_residue]
            assert(residue_type != 'X' and residue_type in residue_type_1to3_map)
            residue_type = residue_type_1to3_map[residue_type]
            new_atoms.append((insertion_residue, residue_type, 'N'))
            new_atoms.append((insertion_residue, residue_type, 'CA'))
            new_atoms.append((insertion_residue, residue_type, 'C'))
        assert(len(end_atoms) >= 1) # C is guaranteed to exist
        if len(end_atoms) == 2:
            # add an N atom
            residue_id = insertion_residues[-1]
            residue_type = insertion_residue_map[residue_id]
            assert(residue_type != 'X' and residue_type in residue_type_1to3_map)
            new_atoms.append((residue_id, residue_type_1to3_map[residue_type], 'N'))

        return self.add_atoms_linearly(start_atom, end_atom, new_atoms)


    def add_atoms_linearly(self, start_atom, end_atom, new_atoms, jitterbug = 0.2):
        '''A low-level function which adds new_atoms between start_atom and end_atom. This function does not validate the
           input i.e. the calling functions are responsible for ensuring that the insertion makes sense.

           Returns the PDB file content with the new atoms added. These atoms are given fresh serial numbers, starting
           from the first serial number larger than the current serial numbers i.e. the ATOM serial numbers do not now
           necessarily increase in document order.

           The jitter adds some X, Y, Z variability to the new atoms. This is important in the Rosetta software suite when
           placing backbone atoms as colinearly placed atoms will break the dihedral angle calculations (the dihedral angle
           over 4 colinear atoms is undefined).
           '''

        atom_name_map = {
            'CA' : ' CA ',
            'C' :  ' C  ',
            'N' :  ' N  ',
            'O' :  ' O  ',
        }

        assert(start_atom.residue.chain == end_atom.residue.chain)
        chain_id = start_atom.residue.chain

        # Initialize steps
        num_new_atoms = float(len(new_atoms))
        X, Y, Z = start_atom.x, start_atom.y, start_atom.z
        x_step = (end_atom.x - X) / (num_new_atoms + 1.0)
        y_step = (end_atom.y - Y) / (num_new_atoms + 1.0)
        z_step = (end_atom.z - Z) / (num_new_atoms + 1.0)
        D = math.sqrt(x_step * x_step + y_step * y_step + z_step * z_step)
        jitter = 0
        if jitterbug:
            jitter = (((x_step + y_step + z_step) / 3.0) * jitterbug) / D

        new_lines = []
        next_serial_number = max(sorted(self.atoms.keys())) + 1
        round = 0
        for new_atom in new_atoms:
            X, Y, Z = X + x_step, Y + y_step, Z + z_step
            if jitter:
                if round % 3 == 0:
                    X, Y = X + jitter, Y - jitter
                elif round % 3 == 1:
                    Y, Z = Y + jitter, Z - jitter
                elif round % 3 == 2:
                    Z, X = Z + jitter, X - jitter
                round += 1
            residue_id, residue_type, atom_name = new_atom
            assert(len(residue_type) == 3)
            assert(len(residue_id) == 6)
            new_lines.append('ATOM  {0} {1} {2} {3}   {4:>8.3f}{5:>8.3f}{6:>8.3f}  1.00  0.00              '.format(str(next_serial_number).rjust(5), atom_name_map[atom_name], residue_type, residue_id, X, Y, Z))
            next_serial_number += 1

        new_pdb = []
        in_start_residue = False
        for l in self.indexed_lines:
            if l[0] and l[3].serial_number == start_atom.serial_number:
                in_start_residue = True
            if in_start_residue and l[3].serial_number != start_atom.serial_number:
                new_pdb.extend(new_lines)
                #colortext.warning('\n'.join(new_lines))
                in_start_residue = False
            if l[0]:
                #print(l[2])
                new_pdb.append(l[2])
            else:
                #print(l[1])
                new_pdb.append(l[1])

        return '\n'.join(new_pdb)




