#!/usr/bin/python
# encoding: utf-8
"""
pdbml.py
Basic parsing for the PDBML format. This is currently used to map PDB ATOM residues to indices within the SEQRES sequence.

Created by Shane O'Connor 2013
"""

import os
from xml.dom.minidom import parse, parseString

from basics import IdentifyingPDBResidue, residue_type_3to1_map, protonated_residue_type_3to1_map, non_canonical_amino_acids
from pdb import PDB
import rcsb
from tools.fs.io import read_file, write_file
from tools.parsers.xml import parse_singular_float, parse_singular_int, parse_singular_alphabetic_character, parse_singular_string

xsd_versions = {
    'pdbx-v40.xsd' : 4.0,
}

class PDBML(object):

    def __init__(self, xml_contents, pdb_contents):
        '''The PDB contents should be passed so that we can deal with HETATM records as the XML does not contain the necessary information.'''
        self.contents = xml_contents
        self.lines = xml_contents.split("\n")
        self.parsed_lines = {}
        self.structure_lines = [] # For ATOM and HETATM records
        self.xml_version = None
        self.schema = None
        self._dom = parseString(xml_contents)
        self.residue_map = {}

        self.modified_residues = PDB(pdb_contents).modified_residues

        self.main_tag = None
        self.parse_header()
        self.parse_atoms()

    @staticmethod
    def retrieve(pdb_id, cache_dir = None):
        '''Creates a PDBML object by using a cached copy of the files if they exists or by retrieving the files from the RCSB.'''

        pdb_contents = None
        xml_contents = None
        pdb_id = pdb_id.upper()

        if cache_dir:
            # Check to see whether we have a cached copy of the PDB file
            filename = os.path.join(cache_dir, "%s.pdb" % pdb_id)
            if os.path.exists(filename):
                pdb_contents = read_file(filename)

            # Check to see whether we have a cached copy of the XML file
            filename = os.path.join(cache_dir, "%s.xml" % pdb_id)
            if os.path.exists(filename):
                xml_contents = read_file(filename)

        # Get any missing files from the RCSB and create cached copies if appropriate
        if not pdb_contents:
            pdb_contents = rcsb.retrieve_pdb(pdb_id)
            if cache_dir:
                write_file(os.path.join(cache_dir, "%s.pdb" % pdb_id), pdb_contents)

        if not xml_contents:
            xml_contents = rcsb.retrieve_xml(pdb_id)
            if cache_dir:
                write_file(os.path.join(cache_dir, "%s.xml" % pdb_id), xml_contents)

        # Return the object
        return PDBML(xml_contents, pdb_contents)

    def parse_header(self):
        main_tags = self._dom.getElementsByTagName("PDBx:datablock")
        assert(len(main_tags) == 1)
        self.main_tag = main_tags[0]
        xsd_version = os.path.split(self.main_tag.getAttribute('xmlns:PDBx'))[1]
        if xsd_versions.get(xsd_version):
            self.xml_version = xsd_versions[xsd_version]
        else:
            raise Exception("XML version is %s. This module only handles versions %s so far." % (xsd_version, ", ".join(xsd_versions.keys())))

    def parse_atoms(self):
        '''All ATOM lines are parsed even though only one per residue needs to be parsed. The reason for parsing all the
           lines is just to sanity-checks that the ATOMs within one residue are consistent with each other.'''

        atom_site_header_tag = self.main_tag.getElementsByTagName("PDBx:atom_siteCategory")
        assert(len(atom_site_header_tag) == 1)
        atom_site_header_tag = atom_site_header_tag[0]

        atom_site_tags = atom_site_header_tag.getElementsByTagName("PDBx:atom_site")

        residue_map = {}
        residues_read = {}
        for t in atom_site_tags:
            r, seqres, ResidueAA = PDBML.parse_atom_site(t, self.modified_residues)
            if r:
                full_residue_id = str(r)
                if residues_read.get(full_residue_id):
                    assert(residues_read[full_residue_id] == (r.ResidueAA, seqres))
                else:
                    residues_read[full_residue_id] = (r.ResidueAA, seqres)
                    residue_map[r] = seqres

        self.residue_map = residue_map

    @staticmethod
    def parse_atom_site(t, modified_residues):

        # Only parse ATOM records
        if parse_singular_string(t, 'PDBx:group_PDB') == 'HETATM':
            return None, None, None
        assert(parse_singular_string(t, 'PDBx:group_PDB') == 'ATOM')

        x, y, z = parse_singular_float(t, "PDBx:Cartn_x"), parse_singular_float(t, "PDBx:Cartn_y"), parse_singular_float(t, "PDBx:Cartn_z")

        PDB_chain_id = parse_singular_alphabetic_character(t, 'PDBx:auth_asym_id')
        ATOM_residue_id = parse_singular_int(t, 'PDBx:auth_seq_id')
        PDB_insertion_code = " "
        if t.getElementsByTagName('PDBx:pdbx_PDB_ins_code'):
            PDB_insertion_code = parse_singular_alphabetic_character(t, 'PDBx:pdbx_PDB_ins_code')

        SEQRES_index = parse_singular_int(t, 'PDBx:label_seq_id')

        residue_a = parse_singular_string(t, 'PDBx:auth_comp_id')
        residue_b = parse_singular_string(t, 'PDBx:label_comp_id')
        assert(residue_a == residue_b)
        residue_3_letter = residue_a

        residue_1_letter = residue_type_3to1_map.get(residue_3_letter) or protonated_residue_type_3to1_map.get(residue_3_letter) or non_canonical_amino_acids.get(residue_3_letter)
        if not residue_1_letter:
            residue_identifier = '%s%s%s' % (PDB_chain_id, str(ATOM_residue_id).rjust(4), PDB_insertion_code)
            if modified_residues.get(residue_identifier):
                residue_1_letter = modified_residues[residue_identifier]['original_residue_1']
        if not residue_1_letter:
            '''Too many cases to worry about... we will have to use residue_3_letter to sort those out.'''
            residue_1_letter = 'X'

        r = IdentifyingPDBResidue(PDB_chain_id, ("%d%s" % (ATOM_residue_id, PDB_insertion_code)).rjust(5), residue_1_letter, None, residue_3_letter)
        r.add_position(x, y, z)

        return r, SEQRES_index, residue_1_letter
