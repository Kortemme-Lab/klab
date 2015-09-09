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

import rcsb
from basics import Residue, PDBResidue, Sequence, SequenceMap, residue_type_3to1_map, protonated_residue_type_3to1_map, non_canonical_amino_acids, protonated_residues_types_3, residue_types_3, Mutation, ChainMutation, SimpleMutation
from basics import dna_nucleotides, rna_nucleotides, dna_nucleotides_3to1_map, dna_nucleotides_2to1_map, non_canonical_dna, non_canonical_rna, all_recognized_dna, all_recognized_rna
from tools import colortext
from tools.fs.fsio import read_file, write_file
from tools.pymath.stats import get_mean_and_standard_deviation
from tools.pymath.cartesian import spatialhash
from tools.rosetta.map_pdb_residues import get_pdb_contents_to_pose_residue_map
from tools.general.strutil import remove_trailing_line_whitespace as normalize_pdb_file
from tools.rosetta.input_files import LoopsFile

pymol_load_failed = False
try:
    from tools.bio.pymolmod.psebuilder import BatchBuilder, PDBContainer
    from tools.bio.pymolmod.loop_removal import LoopRemovalBuilder
except Exception, e:
    pymol_load_failed = True



backbone_atoms = set(['N', 'CA', 'C', 'O'])


class Residue(object):


    def __init__(self, chain, resid):
        self.chain = chain
        self.residue_id = resid
        self.records = dict(ATOM = [], HETATM = [], ANISOU = [])


    def add(self, record_type, atom):
        self.records[record_type].append(atom)


    def get(self, record_type):
        return self.records[record_type]


    def id(self):
        return self.chain, self.residue_id


    def __repr__(self):
        return pprint.pformat(self.records)



class Atom(object):


    def __init__(self, residue, name, group, serial_number):
        self.residue = residue
        self.x, self.y, self.z = None, None, None
        self.point = None
        self.serial_number = serial_number
        self.name = name
        self.group = group
        self.bin = None
        self.record_type = None


    def place(self, x, y, z, record_type = None):
        self.x = x
        self.y = y
        self.z = z
        self.record_type = record_type
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
            return '{0}: {1} {2} at ({3}, {4}, {5})'.format(self.record_type, self.name, self.serial_number, self.x, self.y, self.z)


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


class Bonsai(object):


    ### Constructors

    def __init__(self, pdb_content, buffer = 0.05, bin_size = 5.1, safe_mode = True):
        '''Takes either a pdb file, a list of strings = lines of a pdb file, or another object.
           safe_mode checks to make sure that certain assertions holds but adds to the runtime.

           residues only contains residue details for ATOM, HETATM, and ANISOU records.
           atoms only contains ATOM or HETATM records.
           indexed_lines is a document-order tagged list of PDB file lines
           Each item in the list is one of three types:
               ATOM and HETATM records correspond to a quadruple (record_type, serial_number, line, new_atom)
               ANISOU records correspond to a triple (record_type, serial_number, line)
               Other lines correspond to a double (None, line)
        '''

        self.pdb_content = pdb_content
        self.lines = pdb_content.split("\n")
        self.min_x, self.min_y, self.min_z, self.max_x, self.max_y, self.max_z, self.max_dimension = None, None, None, None, None, None, None
        self.buffer = buffer
        self.bin_size = float(bin_size)
        self.atom_bins = None
        self.indexed_lines = None
        self.atom_bin_dimensions = None
        self.atom_name_to_group = {}
        self.safe_mode = safe_mode
        self.parse()
        self.bin_atoms()
        if self.safe_mode:
            self.check_residues()


    @staticmethod
    def from_filepath(filepath):
        '''A function to replace the old constructor call where a filename was passed in.'''
        assert(os.path.exists(filepath))
        return Bonsai(read_file(filepath))


    @staticmethod
    def from_lines(pdb_file_lines):
        '''A function to replace the old constructor call where a list of the file's lines was passed in.'''
        return Bonsai("\n".join(pdb_file_lines))


    @staticmethod
    def retrieve(pdb_id, cache_dir = None):
        '''Creates a PDB object by using a cached copy of the file if it exists or by retrieving the file from the RCSB.'''

        # Check to see whether we have a cached copy
        pdb_id = pdb_id.upper()
        if cache_dir:
            filename = os.path.join(cache_dir, "%s.pdb" % pdb_id)
            if os.path.exists(filename):
                return Bonsai(read_file(filename))

        # Get a copy from the RCSB
        contents = rcsb.retrieve_pdb(pdb_id)

        # Create a cached copy if appropriate
        if cache_dir:
            write_file(os.path.join(cache_dir, "%s.pdb" % pdb_id), contents)

        # Return the object
        return Bonsai(contents)


    ### Initialization


    def parse(self, lines = None):
        '''Parses the PDB file into a indexed representation (a tagged list of lines, see constructor docstring).
           A set of Atoms is created, including x, y, z coordinates when applicable. These atoms are grouped into Residues.
           Finally, the limits of the 3D space are calculated to be used for Atom binning.

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

        atom_name_to_group = {}
        for line in self.lines:
            record_type = line[:6].strip()
            if record_type in removable_records_types_with_atom_serial_numbers:

                #altLoc = line[16]
                atom_name = line[12:16].strip()
                chain = line[21]
                resid = line[22:27] # residue ID + insertion code
                serial_number = int(line[6:11])
                atom_group = None
                if record_type == 'ATOM':
                    atom_group = atom_name_to_group.get(atom_name)
                    if not atom_group:
                        # The convention seems to be that the first alphabetic character is the group
                        for c in atom_name:
                            if c.isalpha():
                                atom_name_to_group[atom_name] = c
                                atom_group = c
                                break

                residues[chain] = residues.get(chain, {})
                residues[chain][resid] = residues[chain].get(resid, Residue(chain, resid))
                new_atom = Atom(residues[chain][resid], atom_name, atom_group, serial_number)
                residues[chain][resid].add(record_type.strip(), new_atom)

                if record_type in removable_xyz_records_types_with_atom_serial_numbers:
                    x, y, z = float(line[30:38]), float(line[38:46]), float(line[46:54])
                    xs.append(x)
                    ys.append(y)
                    zs.append(z)
                    assert(serial_number not in atoms) # the logic of this class relies on this assertion - that placed records have a unique identifier
                    atoms[serial_number] = new_atom
                    atoms[serial_number].place(x, y, z, record_type)
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
        self.atom_name_to_group = atom_name_to_group


    def bin_atoms(self):
        '''This function bins the Atoms into fixed-size sections of the protein space in 3D.'''

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
        if self.safe_mode:
            num_atoms = 0
            for x in range(int(atom_bin_dimensions[0])):
                for y in range(int(atom_bin_dimensions[1])):
                    for z in range(int(atom_bin_dimensions[2])):
                        num_atoms += len(atom_bins[x][y][z])
            assert(num_atoms == len(self.atoms))

        # Snip empty sections (saves a little space after garbage collection - space savings increase with the number of empty arrays in the matrix)
        blank_section = ()
        for x in range(int(atom_bin_dimensions[0])):
            for y in range(int(atom_bin_dimensions[1])):
                for z in range(int(atom_bin_dimensions[2])):
                    if not atom_bins[x][y][z]:
                        atom_bins[x][y][z] = blank_section

        self.atom_bins = atom_bins


    ### Queries


    def get_atom_names_by_group(self, groups):
        names = set()
        groups = set(groups)
        for nm, g in self.atom_name_to_group.iteritems():
            if g in groups:
                names.add(nm)
        return names


    ### Base functionality


    def find_heavy_atoms_near_atom(self, source_atom, search_radius, atom_hit_cache = set()):
        '''atom_hit_cache is a set of atom serial numbers which have already been tested. We keep track of these to avoid recalculating the distance.
        '''
        #todo: Benchmark atom_hit_cache to see if it actually speeds up the search

        non_heavy_atoms = self.get_atom_names_by_group(set(['H', 'D', 'T']))
        return self.find_atoms_near_atom(source_atom, search_radius, atom_names_to_exclude = non_heavy_atoms, atom_hit_cache = atom_hit_cache)


    def find_atoms_near_atom(self, source_atom, search_radius, atom_hit_cache = set(), atom_names_to_include = set(), atom_names_to_exclude = set()):
        '''It is advisable to set up and use an atom hit cache object. This reduces the number of distance calculations and gives better performance.
           See find_sidechain_atoms_within_radius_of_residue_objects for an example of how to set this up e.g.
               atom_hit_cache = set()
               for x in some_loop:
                   this_object.find_atoms_near_atom(source_atom, search_radius, atom_hit_cache = atom_hit_cache)
        '''

        if len(atom_names_to_include) > 0 and len(atom_names_to_exclude) > 0:
            raise Exception('Error: either one of the set of atoms types to include or the set of atom types to exclude can be set but not both.')

        atom_names_to_exclude = set(atom_names_to_exclude)
        if atom_names_to_include:
            atom_names_to_exclude = set(self.atom_name_to_group.keys()).difference(atom_names_to_include)

        radius = float(search_radius) + self.buffer # add buffer to account for edge cases in searching
        bin_size = self.bin_size
        atom_bins = self.atom_bins
        if source_atom:
            bin_radius = int(math.ceil(radius / bin_size)) # search this many bins in all directions
            xrange = range(max(0, source_atom.bin.x - bin_radius), min(self.atom_bin_dimensions[0], source_atom.bin.x + bin_radius) + 1)
            yrange = range(max(0, source_atom.bin.y - bin_radius), min(self.atom_bin_dimensions[1], source_atom.bin.y + bin_radius) + 1)
            zrange = range(max(0, source_atom.bin.z - bin_radius), min(self.atom_bin_dimensions[2], source_atom.bin.z + bin_radius) + 1)
            for x in xrange:
                for y in yrange:
                    for z in zrange:
                        for atom in atom_bins[x][y][z]:
                            if atom not in atom_hit_cache:
                                if (source_atom - atom <= search_radius) and (atom.name not in atom_names_to_exclude):
                                    atom_hit_cache.add(atom)

            return atom_hit_cache


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


    ### Main functionality


    def find_sidechain_atoms_within_radius_of_residues(self, source_residue_ids, search_radius):
        #for residue in all residues:
        #    for all heavy atoms in residue
        #        find all heavy atoms within radius which are within residues (ATOM records)
        #             return the residue ID
        #for all found residues
        #    identify all non-backbone_atoms
        #    split the Bonsai by these atoms
        pass


    def find_sidechain_atoms_within_radius_of_residue_objects(self, source_residues, search_radius, find_ATOM_atoms = True, find_HETATM_atoms = False):
        '''for residue in source_residues:
             for all heavy atoms in residue
               find all heavy atoms within radius which are within residues (ATOM records)
           for all heavy atoms found
             determing the associated residue
           for all found residues not in source_residues
             identify all non-backbone atoms
           return the non-backbone atoms'''

        atom_hit_cache = set()
        for residue in source_residues:
            if find_ATOM_atoms:
                for aatom in residue.get('ATOM'):
                    self.find_heavy_atoms_near_atom(aatom, search_radius, atom_hit_cache = atom_hit_cache)
            if find_HETATM_atoms:
                for hatom in residue.get('HETATM'):
                    self.find_heavy_atoms_near_atom(hatom, search_radius, atom_hit_cache = atom_hit_cache)

        # Get the list of source_residues
        loop_residue_ids = set()
        for sres in source_residues:
            loop_residue_ids.add(sres.id())

        # Get the list of atoms to be removed (all sidechain atoms - including non-heavy atoms - of the found residues which are not in source_residues)
        sidechain_atom_serial_numbers = set()
        nearby_residues = set()
        nearby_residue_ids = set()
        for a in atom_hit_cache:
            residue_id = a.residue.id()
            if residue_id not in loop_residue_ids:
                nearby_residues.add(a.residue)
                nearby_residue_ids.add(residue_id)
        for nearby_residue in nearby_residues:
            for aatom in nearby_residue.get('ATOM'):
                if aatom.name not in backbone_atoms:
                    sidechain_atom_serial_numbers.add(aatom.serial_number)
        assert(len(nearby_residue_ids.intersection(loop_residue_ids)) == 0)
        return sidechain_atom_serial_numbers


    ### Higher-level functionality


    def prune_structure_according_to_loops_file(self, loops_file_content, search_radius, expected_loop_length = None, generate_pymol_session = True):
        lf = LoopsFile(loops_file_content)
        assert(len(lf.data) == 1) # todo: remove

        # Extract the list of Residues defined in the loops file
        loop_residues = []
        for loop in lf.data:

            # Identify the Residues corresponding to the loops file definition
            start_id = str(loop['start'])
            end_id = str(loop['end'])
            start = []
            end = []
            for chain, chain_residues in self.residues.iteritems():
                for res, residue_object in chain_residues.iteritems():
                    if res.strip() == start_id:
                        start.append((chain, res, residue_object))
                    if res.strip() == end_id:
                        end.append((chain, res, residue_object))
            if len(start) != len(end) != 1:
                raise Exception('The PDB is ambiguous with respect to the loops file i.e. more than one PDB residue corresponds to the start or end residue defined in the loops file.')
            start, end = start[0], end[0]

            # We assume that the loops file identifies a range in document order
            loop_start = False
            for l in self.indexed_lines:
                if l[0] == 'ATOM' or l[0] == 'HETATM':
                    atom_residue = l[3].residue
                    if not loop_start:
                        if atom_residue == start[2]:
                            loop_start = True
                            if atom_residue not in loop_residues:
                                loop_residues.append(atom_residue)
                    else:
                        if atom_residue not in loop_residues:
                            loop_residues.append(atom_residue)
                        if atom_residue == end[2]:
                            break
        if expected_loop_length != None and expected_loop_length != len(loop_residues):
            raise Exception('Expected to identify {0} residues but {1} were identified.'.format(expected_loop_length, len(loop_residues)))

        # Determine the sidechain atoms to be removed
        sidechain_atom_serial_numbers = self.find_sidechain_atoms_within_radius_of_residue_objects(loop_residues, search_radius)

        # Determine the loop residue atoms to be removed
        loop_residues_ids = set()
        loop_atom_serial_numbers = set()
        for loop_residue in loop_residues:
            for aatom in loop_residue.get('ATOM'):
                loop_atom_serial_numbers.add(aatom.serial_number)
        assert(len(sidechain_atom_serial_numbers.intersection(loop_atom_serial_numbers)) == 0)

        return self.prune(loop_atom_serial_numbers, sidechain_atom_serial_numbers, generate_pymol_session = generate_pymol_session)


    def prune(self, arbitrary_atom_serial_numbers, sidechain_atom_serial_numbers = set(), keep_CA_in_cutting = True, generate_pymol_session = True, bonsai_label = 'Bonsai', cutting_label = 'Cutting', pymol_executable = 'pymol'):
        '''Returns the content of two PDB files.
           The first object is missing the ATOM (and any related ANISOU) and HETATM records identified by atom_serial_numbers.
           The second object only contains ATOM, ANISOU, and HETATM records which are identified by atom_serial_numbers.
           Both PDB objects contain all records from the original PDB which are not ATOM, ANISOU, or HETATM records.'''
        bonsai = []
        cutting = []

        sidechain_residues = set()
        if sidechain_atom_serial_numbers:
            for line in self.indexed_lines:
                if line[0] == 'ATOM' and line[1] in sidechain_atom_serial_numbers:
                    residue_id = line[3].residue.id()
                    sidechain_residues.add(residue_id[0] + residue_id[1])

        atom_serial_numbers_to_remove = arbitrary_atom_serial_numbers.union(sidechain_atom_serial_numbers)
        for line in self.indexed_lines:
            if line[0]: # record type
                PDB_line = line[2]
                if line[1] in atom_serial_numbers_to_remove:
                    cutting.append(PDB_line)
                else:
                    if keep_CA_in_cutting and PDB_line[21:27] in sidechain_residues and PDB_line[12:16] == ' CA ':
                        cutting.append(PDB_line)
                    bonsai.append(PDB_line)
            else:
                bonsai.append(line[1])
                cutting.append(line[1])
        bonsai_pdb_content = '\n'.join(bonsai)
        cutting_pdb_content = '\n'.join(cutting)
        PSE_file, PSE_script = None, None
        try:
            PSE_file, PSE_script = self.generate_pymol_session(bonsai_pdb_content, cutting_pdb_content, bonsai_label = bonsai_label, cutting_label = cutting_label, pymol_executable = pymol_executable, settings = {})
        except Exception, e:
            colortext.error('Failed to generate the PyMOL session: "{0}"'.format(e))

        return bonsai_pdb_content, cutting_pdb_content, PSE_file, PSE_script


    def generate_pymol_session(self, bonsai_pdb_content, cutting_pdb_content, bonsai_label = 'Bonsai', cutting_label = 'Cutting', pymol_executable = 'pymol', settings = {}):
        ''' Generates the PyMOL session for the scaffold, model, and design structures.
            Returns this session and the script which generated it.'''
        if not pymol_load_failed:
            b = BatchBuilder(pymol_executable = pymol_executable)

            loop_residues = set()
            for l in cutting_pdb_content.split('\n'):
                if l.startswith('ATOM  ') and l[12:16] == ' C  ':
                    loop_residues.add(l[21:27])
            loop_residues = sorted(loop_residues)

            structures_list = [
                (bonsai_label, bonsai_pdb_content, set()),
                (cutting_label, cutting_pdb_content, loop_residues),
            ]
            settings['Main'] = bonsai_label
            settings['Loop'] = cutting_label
            PSE_files = b.run(LoopRemovalBuilder, [PDBContainer.from_content_triple(structures_list)], settings = settings)
            return PSE_files[0], b.PSE_scripts[0]


    @staticmethod
    def convert_to_pse(bonzai, cutting):
        '''Returns a PyMOL session containing the two parts of the PDB file split using prune.'''
        pass


    ### Safety checks


    def check_residues(self):
        '''Checks to make sure that each atom type is unique per residue.'''
        for chain, residue_ids in self.residues.iteritems():
            for residue_id, residue in residue_ids.iteritems():
                for record_type, atoms in residue.records.iteritems():
                    freq = {}
                    for atom in atoms:
                        freq[atom.name] = freq.get(atom.name, 0)
                        freq[atom.name] += 1
                    for atom_type, count in freq.items():
                        if count > 1:
                            raise Exception('{0} occurrences of atom type {1} for record type {2} occur in residue {3} in chain {4}.'.format(count, atom_type, record_type, residue_id.strip(), chain))



if __name__ == '__main__':

    # 1a8d is an example from the loops benchmark
    # 1lfa contains hydrogens
    b = Bonsai.retrieve('1lfa', cache_dir='/tmp')

    search_radius = 10.0

    atom_of_interest = b.get_atom(1095)
    nearby_atoms = b.find_atoms_near_atom(atom_of_interest, search_radius)
    for na in nearby_atoms:
        assert(na - atom_of_interest <= search_radius)
    for fa in b.get_atom_set_complement(nearby_atoms):
        assert(fa - atom_of_interest > search_radius)

    # Get all heavy atoms within the radius (including HETATM)
    nearby_heavy_atoms = b.find_heavy_atoms_near_atom(atom_of_interest, search_radius)

    # Get all C-alpha atoms within the radius
    nearby_ca_atoms = b.find_atoms_near_atom(atom_of_interest, search_radius, atom_names_to_include = ['CA'])

    # Get all carbon atoms within the radius
    nearby_c_atoms = b.find_atoms_near_atom(atom_of_interest, search_radius, atom_names_to_include = b.get_atom_names_by_group(['C']))

    b = Bonsai.retrieve('1a8d', cache_dir='/tmp')
    bonsai, cutting, PSE_file, PSE_script = b.prune_structure_according_to_loops_file('LOOP 155 166 166 0 1', search_radius, expected_loop_length = 12, generate_pymol_session = True)
    #write_file('1a8d.pse', PSE_file)
    #write_file('1a8d_without_loop.pdb', bonsai)
    #write_file('1a8d_loop.pdb', cutting)



