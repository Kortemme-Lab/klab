#!/usr/bin/env python2
# encoding: utf-8

# The MIT License (MIT)
#
# Copyright (c) 2016 Kyle Barlow
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

from lxml import etree
import os
import gzip
import sys
import numpy as np

one_letter = {
    'VAL':'V', 'ILE':'I', 'LEU':'L', 'GLU':'E', 'GLN':'Q',
    'ASP':'D', 'ASN':'N', 'HIS':'H', 'TRP':'W', 'PHE':'F', 'TYR':'Y',
    'ARG':'R', 'LYS':'K', 'SER':'S', 'THR':'T', 'MET':'M', 'ALA':'A',
    'GLY':'G', 'PRO':'P', 'CYS':'C'
}

class Residue:
    def __init__ (self, atom_data):
        self.atoms = {}
        atom_num, entity_id, chain, resn, resi, x, y, z = atom_data
        self.entity_id = entity_id
        self.chain = chain
        self.resn = resn
        self.resi = resi
        self.add_atom(atom_data)

    def add_atom(self, atom_data):
        atom_num, entity_id, chain, resn, resi, x, y, z = atom_data
        # print atom_data
        # print self.entity_id, self.selection_tup
        assert( self.entity_id == entity_id )
        assert( self.chain == chain )
        assert( self.resn == resn )
        assert( self.resi == resi )
        assert( atom_num not in self.atoms )
        self.atoms[atom_num] = np.array( (x, y, z) )

    def within_dist(self, other, dist_cutoff):
        for self_atom in self.atoms.values():
            for other_atom in other.atoms.values():
                if np.linalg.norm( self_atom - other_atom ) <= dist_cutoff:
                    return True
        return False

    @property
    def selection_tup(self):
        return (self.resi, self.resn, self.chain)

class xmlpdb:
    def __init__(self, xml_pdb_path, remove_dup_alt_ids = False):
        assert( os.path.isfile(xml_pdb_path) )
        if xml_pdb_path.endswith('.gz'):
            with gzip.open(xml_pdb_path, 'rb') as f:
                et = etree.parse(f)
        else:
            with open(xml_pdb_path, 'r') as f:
                et = etree.parse(f)
        root = et.getroot()
        ns = root.nsmap

        # Get entity to chain mapping
        # self.entity_to_chain_mapping = {}
        # struct_asymCategory_tag = etree.QName(ns['PDBx'], 'struct_asymCategory').text
        # struct_asym_tag = etree.QName(ns['PDBx'], 'struct_asym').text
        # entity_id_tag = etree.QName(ns['PDBx'], 'entity_id').text
        # struct_asymCategory = root.find(struct_asymCategory_tag)
        # for struct_asym in struct_asymCategory.iter(struct_asym_tag):
        #     chain = struct_asym.attrib['id']
        #     entity_id = long( struct_asym.findtext(entity_id_tag) )
        #     print entity_id, chain
        # sys.exit(0)

        # Tags for later searching
        atom_tag = etree.QName(ns['PDBx'], 'atom_site').text
        atom_name_tag = etree.QName(ns['PDBx'], 'label_atom_id').text
        entity_tag = etree.QName(ns['PDBx'], 'label_entity_id').text
        resn_tag = etree.QName(ns['PDBx'], 'label_comp_id').text
        resi_tag = etree.QName(ns['PDBx'], 'auth_seq_id').text
        chain_tag = etree.QName(ns['PDBx'], 'label_asym_id').text
        x_tag = etree.QName(ns['PDBx'], 'Cartn_x').text
        y_tag = etree.QName(ns['PDBx'], 'Cartn_y').text
        z_tag = etree.QName(ns['PDBx'], 'Cartn_z').text

        # for child in root:
        #     print child.tag, child.attrib

        self.residues = {}
        if remove_dup_alt_ids:
            previously_seen_atoms = set()
        for atom_site in root.iter(atom_tag):
            atom_name = atom_site.findtext(atom_name_tag).strip()
            atom_num = long( atom_site.attrib['id'] )
            entity_id = long( atom_site.findtext(entity_tag) )
            chain = atom_site.findtext(chain_tag)
            resn = atom_site.findtext(resn_tag)
            resi = long( atom_site.findtext(resi_tag) )
            x = float( atom_site.findtext(x_tag) )
            y = float( atom_site.findtext(y_tag) )
            z = float( atom_site.findtext(z_tag) )

            if remove_dup_alt_ids:
                previously_seen_atom_tup = (atom_name, resn, chain, resi)
                if previously_seen_atom_tup in previously_seen_atoms:
                    continue
                else:
                    previously_seen_atoms.add( previously_seen_atom_tup )

            atom_data = (atom_num, entity_id, chain, resn, resi, x, y, z)

            if chain not in self.residues:
                self.residues[chain] = {}
            if resi in self.residues[chain]:
                # print
                # print chain, resi
                self.residues[chain][resi].add_atom( atom_data )
            else:
                self.residues[chain][resi] = Residue( atom_data )


    def get_neighbors_by_chain(self, neighbor_chains, dist_cutoff, protein_only = True):
        # Returns a selection of any residues within dist_cutoff (angstroms) of given neighbor chains
        # Return selection format: (residue number, three letter wildtype residue type, chain letter)
        selection = set()
        all_chains = sorted( self.residues.keys() )
        for search_chain in neighbor_chains:
            for search_resi, search_residue in self.residues[search_chain].iteritems():
                if not protein_only or search_residue.resn in one_letter:
                    for chain in all_chains:
                        if chain not in neighbor_chains:
                            for resi, residue in self.residues[chain].iteritems():
                                if not protein_only or residue.resn in one_letter:
                                    selection_tup = residue.selection_tup
                                    if selection_tup not in selection:
                                        if search_residue.within_dist(residue, dist_cutoff):
                                            selection.add( selection_tup )
        return sorted( selection )

    def get_neighbors_at_dimer_interface(self, interface_chains, dist_cutoff, protein_only = True, filter_only_chains = []):
        # Returns a selection of any residues within dist_cutoff (angstroms) of given neighbor chains
        # Return selection format: (residue number, three letter wildtype residue type, chain letter)
        selection = set()
        all_chains = sorted( self.residues.keys() )
        for search_chain in interface_chains:
            for search_resi, search_residue in self.residues[search_chain].iteritems():
                if not protein_only or search_residue.resn in one_letter:
                    for chain in interface_chains:
                        if len( filter_only_chains ) > 0 and chain not in filter_only_chains:
                            continue
                        if chain != search_chain:
                            for resi, residue in self.residues[chain].iteritems():
                                if not protein_only or residue.resn in one_letter:
                                    selection_tup = residue.selection_tup
                                    if selection_tup not in selection:
                                        if search_residue.within_dist(residue, dist_cutoff):
                                            selection.add( selection_tup )
        return sorted( selection )
