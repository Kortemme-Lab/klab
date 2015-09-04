#!/usr/bin/python
# encoding: utf-8
"""
bonzai.py
Functions to help remove particular side-chains or atoms from a PDB structure

Created by Shane O'Connor 2015.
This module is complementary to pdb.py but its data structure is better suited for the purposes here (removing atoms while
retaining document order).
"""


import re
import sys
import os
import types
import string
import types
import numpy

from basics import Residue, PDBResidue, Sequence, SequenceMap, residue_type_3to1_map, protonated_residue_type_3to1_map, non_canonical_amino_acids, protonated_residues_types_3, residue_types_3, Mutation, ChainMutation, SimpleMutation
from basics import dna_nucleotides, rna_nucleotides, dna_nucleotides_3to1_map, dna_nucleotides_2to1_map, non_canonical_dna, non_canonical_rna, all_recognized_dna, all_recognized_rna
from tools import colortext
from tools.fs.fsio import read_file, write_file
from tools.pymath.stats import get_mean_and_standard_deviation
from tools.pymath.cartesian import spatialhash
from tools.rosetta.map_pdb_residues import get_pdb_contents_to_pose_residue_map
import rcsb
from tools.general.strutil import remove_trailing_line_whitespace as normalize_pdb_file


class Bonzai(object):


    ### Constructors

    def __init__(self, pdb_content):
        '''Takes either a pdb file, a list of strings = lines of a pdb file, or another object.'''

        self.pdb_content = pdb_content
        self.lines = pdb_content.split("\n")
        self.parse()


    @staticmethod
    def from_filepath(filepath):
        '''A function to replace the old constructor call where a filename was passed in.'''
        assert(os.path.exists(filepath))
        return Bonzai(read_file(filepath))


    @staticmethod
    def from_lines(pdb_file_lines):
        '''A function to replace the old constructor call where a list of the file's lines was passed in.'''
        return Bonzai("\n".join(pdb_file_lines))


    @staticmethod
    def retrieve(pdb_id, cache_dir = None):
        '''Creates a PDB object by using a cached copy of the file if it exists or by retrieving the file from the RCSB.'''

        # Check to see whether we have a cached copy
        pdb_id = pdb_id.upper()
        if cache_dir:
            filename = os.path.join(cache_dir, "%s.pdb" % pdb_id)
            if os.path.exists(filename):
                return Bonzai(read_file(filename))

        # Get a copy from the RCSB
        contents = rcsb.retrieve_pdb(pdb_id)

        # Create a cached copy if appropriate
        if cache_dir:
            write_file(os.path.join(cache_dir, "%s.pdb" % pdb_id), contents)

        # Return the object
        return Bonzai(contents)


    ### Initialization


    def parse(self, lines = None):
        '''Builds a quadtree and an indexed representation of the PDB file.

           ATOM serial numbers appear to be sequential within a model regardless of alternate locations (altLoc, see 1ABE). This
           code assumes that this holds as this serial number is used as an index.
           If an ATOM has a corresponding ANISOU record, the latter record uses the same serial number.
        '''
        indexed_lines = []
        MODEL_count = 0
        records_types_with_atom_serial_numbers = set(['ATOM  ', 'HETATM', 'TER   ', 'ANISOU'])
        removable_records_types_with_atom_serial_numbers = set(['ATOM  ', 'HETATM', 'ANISOU'])
        inf, ninf = float("inf"), -float("inf")
        min_x, min_y, min_z, max_x, max_y, max_z = inf, inf, inf, ninf, ninf, ninf
        xs, ys, zs = [], [], []
        for line in self.lines:
            record_type = line[:6]
            if record_type in removable_records_types_with_atom_serial_numbers:
                serial_number = int(line[6:11])
                x, y, z = float(line[30:38]), float(line[38:46]), float(line[46:54])
                xs.append(x)
                ys.append(y)
                zs.append(z)
                indexed_lines.append((record_type, serial_number, line, x, y, z))
            else:
                if record_type == 'MODEL ':
                    MODEL_count += 1
                    if MODEL_count > 1:
                        raise Exception('This code needs to be updated to properly handle NMR structures.')
                indexed_lines.append((None, line))

        print(min(xs), min(ys), min(zs))

        self.pdb_content.split("\n")


if __name__ == '__main__':

    b = Bonzai.retrieve('1a8d', cache_dir='/tmp')
