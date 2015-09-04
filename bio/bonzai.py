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
import pprint
import numpy

if __name__ == '__main__':
    sys.path.insert(0, os.path.join('..', '..'))

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
        removable_xyz_records_types_with_atom_serial_numbers = set(['ATOM  ', 'HETATM'])
        xs, ys, zs = [], [], []

        # atoms maps ATOM/HETATM serial numbers to Atom objects. Atom objects know which Residue object they belong to and Residue objects maintain a list of their Atoms.
        atoms = {}

        # atoms maps chain -> residue IDs to Residue objects. Residue objects remember which ATOM/HETATM/ANISOU records (stored as Atom objects) belong to them
        residues = {}

        for line in self.lines:
            record_type = line[:6]
            if record_type in removable_records_types_with_atom_serial_numbers:

                #altLoc = line[16]
                atom_name = line[12:16]
                chain = line[21]
                resid = line[22:27] # residue ID + insertion code
                serial_number = int(line[6:11])

                residues[chain] = residues.get(chain, {})
                residues[chain][resid] = residues[chain].get(resid, Residue())
                new_atom = Atom(residues[chain][resid], atom_name, serial_number)
                residues[chain][resid].add(record_type.strip(), new_atom)

                if record_type in removable_xyz_records_types_with_atom_serial_numbers:
                    x, y, z = float(line[30:38]), float(line[38:46]), float(line[46:54])
                    xs.append(x)
                    ys.append(y)
                    zs.append(z)
                    assert(serial_number not in atoms) # the logic of this class relies on this assertion - that placed records have a unique identifier
                    atoms[serial_number] = new_atom
                    atoms[serial_number].place(x, y, z)
                    indexed_lines.append((record_type, serial_number, line, new_atom))
                else:
                    indexed_lines.append((record_type, serial_number, line))
            else:
                if record_type == 'MODEL ':
                    MODEL_count += 1
                    if MODEL_count > 1:
                        raise Exception('This code needs to be updated to properly handle NMR structures.')
                indexed_lines.append((None, line))

        if not xs:
            raise Exception('No coordinates found.')

        min_x, min_y, min_z, max_x, max_y, max_z = min(xs), min(ys), min(zs), max(xs), max(ys), max(zs)
        print(min_x, min_y, min_z, max_x, max_y, max_z)
        #pprint.pprint(residues)

        residue_atoms = residues['A'][' 210 '].get('ATOM')
        atom_range = len(residue_atoms)
        for x in range(0, atom_range - 1):
            for y in range(x + 1, atom_range):
                print(x, y, residue_atoms[x], residue_atoms[y], residue_atoms[x] - residue_atoms[y])



class Residue(object):


    def __init__(self):
        self.records = dict(ATOM = [], HETATM = [], ANISOU = [])


    def add(self, record_type, atom):
        self.records[record_type].append(atom)


    def get(self, record_type):
        return self.records[record_type]


    def __repr__(self):
        return pprint.pformat(self.records)
        #atom 1- residue A 1-452, 501,502,1001-1424



class Atom(object):


    def __init__(self, residue, name, serial_number):
        self.residue = residue
        self.x, self.y, self.z = None, None, None
        self.point = None
        self.serial_number = serial_number
        self.name = name.strip()


    def place(self, x, y, z):
        self.x = x
        self.y = y
        self.z = z
        self.point = numpy.array([x, y, z])


    def __sub__(self, other):
        '''Returns the distance (Euclidean/Frobenius norm) between this point and the other point.'''
        return numpy.linalg.norm(self.point - other.point)


    def __repr__(self):
        if self.point is None:
            return '{0} {1}'.format(self.name, self.serial_number)
        else:
            return '{0} {1} at ({2}, {3}, {4})'.format(self.name, self.serial_number, self.x, self.y, self.z)



if __name__ == '__main__':

    b = Bonzai.retrieve('1a8d', cache_dir='/tmp')
