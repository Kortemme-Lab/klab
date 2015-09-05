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
import math
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

    def __init__(self, pdb_content, buffer = 0.05, bin_size = 5.1):
        '''Takes either a pdb file, a list of strings = lines of a pdb file, or another object.'''

        self.pdb_content = pdb_content
        self.lines = pdb_content.split("\n")
        self.min_x, self.min_y, self.min_z, self.max_x, self.max_y, self.max_z, self.max_dimension = None, None, None, None, None, None, None
        self.buffer = buffer
        self.bin_size = float(bin_size)
        self.atom_bins = None
        self.indexed_lines = None
        self.atom_bin_dimensions = None
        self.parse()
        self.bin_atoms()


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
        records_types_with_atom_serial_numbers = set(['ATOM', 'HETATM', 'TER', 'ANISOU'])
        removable_records_types_with_atom_serial_numbers = set(['ATOM', 'HETATM', 'ANISOU'])
        removable_xyz_records_types_with_atom_serial_numbers = set(['ATOM', 'HETATM'])
        xs, ys, zs = [], [], []

        # atoms maps ATOM/HETATM serial numbers to Atom objects. Atom objects know which Residue object they belong to and Residue objects maintain a list of their Atoms.
        atoms = {}

        # atoms maps chain -> residue IDs to Residue objects. Residue objects remember which ATOM/HETATM/ANISOU records (stored as Atom objects) belong to them
        residues = {}

        for line in self.lines:
            record_type = line[:6].strip()
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

        # Calculate the side size needed for a cube to contain all of the points, with buffers to account for edge-cases
        min_x, min_y, min_z, max_x, max_y, max_z = min(xs), min(ys), min(zs), max(xs), max(ys), max(zs)
        self.min_x, self.min_y, self.min_z, self.max_x, self.max_y, self.max_z = min(xs)-self.buffer, min(ys)-self.buffer, min(zs)-self.buffer, max(xs)+self.buffer, max(ys)+self.buffer, max(zs)+self.buffer
        self.max_dimension = (self.buffer * 4) + max(self.max_x - self.min_x, self.max_y - self.min_y, self.max_z - self.min_z)
        self.residues = residues
        self.atoms = atoms
        self.indexed_lines = indexed_lines


    def bin_atoms(self):

        # Create the atom bins
        low_point = numpy.array([self.min_x, self.min_y, self.min_z])
        high_point = numpy.array([self.max_x, self.max_y, self.max_z])
        atom_bin_dimensions = numpy.ceil((high_point - low_point) / self.bin_size)
        self.atom_bin_dimensions = (int(atom_bin_dimensions[0]) - 1, int(atom_bin_dimensions[1]) - 1, int(atom_bin_dimensions[2]) - 1)
        atom_bins = []
        for x in range(int(atom_bin_dimensions[0])):
            atom_bins.append([])
            for y in range(int(atom_bin_dimensions[1])):
                atom_bins[x].append([])
                for z in range(int(atom_bin_dimensions[2])):
                    atom_bins[x][y].append(Bin(x, y, z))

        # Assign each Atom to a bin
        for serial_number, atom in self.atoms.iteritems():
            bin_location = numpy.trunc((atom.point - low_point) / self.bin_size)
            bin = atom_bins[int(bin_location[0])][int(bin_location[1])][int(bin_location[2])]
            bin.append(atom)
            atom.set_bin(bin)

        # Sanity_check
        num_atoms = 0
        for x in range(int(atom_bin_dimensions[0])):
            for y in range(int(atom_bin_dimensions[1])):
                for z in range(int(atom_bin_dimensions[2])):
                    num_atoms += len(atom_bins[x][y][z])
        assert(num_atoms == len(self.atoms))

        self.atom_bins = atom_bins


    def find_atoms_near_atom(self, source_atom, search_radius):
        radius = float(search_radius) + self.buffer # add buffer to account for edge cases in searching
        bin_size = self.bin_size
        atom_bins = self.atom_bins
        hits = []
        if source_atom:
            bin_radius = int(math.ceil(radius / bin_size)) # search this many bins in all directions
            xrange = range(max(0, source_atom.bin.x - bin_radius), min(self.atom_bin_dimensions[0], source_atom.bin.x + bin_radius) + 1)
            yrange = range(max(0, source_atom.bin.y - bin_radius), min(self.atom_bin_dimensions[1], source_atom.bin.y + bin_radius) + 1)
            zrange = range(max(0, source_atom.bin.z - bin_radius), min(self.atom_bin_dimensions[2], source_atom.bin.z + bin_radius) + 1)
            for x in xrange:
                for y in yrange:
                    for z in zrange:
                        for atom in atom_bins[x][y][z]:
                            if source_atom - atom <= search_radius:
                                hits.append(atom)
            return hits


    def get_atom(self, atom_serial_number):
        source_atom = self.atoms.get(atom_serial_number)
        if source_atom:
            return source_atom
        else:
            raise Exception('ATOM {0} was not found.'.format(atom_serial_number))


    def get_atom_set_complement(self, atoms):
        complement = set()
        serial_numbers = set([a.serial_number for a in atoms])
        for serial_number, atom in self.atoms.iteritems():
            if serial_number not in serial_numbers:
                complement.add(atom)
        return complement


#(None, 'REMARK 280  (PH 7.0). LARGE CRYSTALS (0.2 X 0.2 X 0.5 MM) WERE GROWN BY         ')
#('ATOM', 3212, 'ATOM   3212  CB  ASP A 397      47.343  47.896  35.182  1.00 31.31           C  ', CB 3212 at (47.343, 47.896, 35.182))
#('HETATM', 4082, 'HETATM 4082  O   HOH A1422      59.725  49.320  51.258  1.00 68.31           O  ', O 4082 at (59.725, 49.32, 51.258))
#('ANISOU', 4082, 'ANISOU 4082  O   HOH A1422     8865   8777   8311    969   1113   -375       O  ')

    def build_quadtree(self, radius_):

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
        self.bin = None


    def place(self, x, y, z):
        self.x = x
        self.y = y
        self.z = z
        self.point = numpy.array([x, y, z])


    def set_bin(self, bin):
        assert(self.bin == None or self.bin == bin)
        self.bin = bin


    def __sub__(self, other):
        '''Returns the distance (Euclidean/Frobenius norm) between this point and the other point.'''
        return numpy.linalg.norm(self.point - other.point)


    def __repr__(self):
        if self.point is None:
            return '{0} {1}'.format(self.name, self.serial_number)
        else:
            return '{0} {1} at ({2}, {3}, {4})'.format(self.name, self.serial_number, self.x, self.y, self.z)


class Bin(object):

    def __init__(self, x, y, z):
        self.x, self.y, self.z = x, y, z
        self.items = []

    def append(self, i):
        self.items.append(i)

    def __len__(self):
        return len(self.items)

    def __iter__(self):
        return self.items.__iter__()


if __name__ == '__main__':

    b = Bonzai.retrieve('1a8d', cache_dir='/tmp')
    search_radius = 10.0
    atom_of_interest = b.get_atom(1095)
    nearby_atoms = b.find_atoms_near_atom(atom_of_interest, search_radius)
    for na in nearby_atoms:
        assert(na - atom_of_interest <= search_radius)
    for fa in b.get_atom_set_complement(nearby_atoms):
        assert(fa - atom_of_interest > search_radius)

