#!/usr/bin/python
# encoding: utf-8
"""
pdbml.py
Basic parsing for the PDBML format. This is currently used to map PDB ATOM residues to indices within the SEQRES sequence.

Created by Shane O'Connor 2013

Thanks to Kale Kundert for his suggestion of using xml.sax!
"""

import os
import types

import xml
from xml.sax import parse as parse_xml

from basics import IdentifyingPDBResidue, SequenceMap, residue_type_3to1_map, protonated_residue_type_3to1_map, non_canonical_amino_acids
from pdb import PDB, cases_with_ACE_residues_we_can_ignore
import rcsb
from klab.fs.fsio import read_file, write_file
from klab.parsers.xml import parse_singular_float, parse_singular_int, parse_singular_alphabetic_character, parse_singular_string
from klab.debug.profile import ProfileTimer

int_type = types.IntType

xsd_versions = {
    'pdbx-v40.xsd'  : 4.0,
    'pdbx-v32.xsd'  : 3.2,
    'pdbx.xsd'      : 3.1,
}

# Old, slow class using xml.dom.minidom
from xml.dom.minidom import parse, parseString
class PDBML_slow(object):

    def __init__(self, xml_contents, pdb_contents):
        '''The PDB contents should be passed so that we can deal with HETATM records as the XML does not contain the necessary information.'''

        self.pdb_id = None
        self.contents = xml_contents
        self.xml_version = None

        self._dom = parseString(xml_contents)

        self.deprecated = False
        self.replacement_pdb_id = None

        self.modified_residues = PDB(pdb_contents).modified_residues

        self.main_tag = None

        self.parse_header()
        self.parse_deprecation()
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
        return PDBML_slow(xml_contents, pdb_contents)

    def parse_header(self):
        main_tags = self._dom.getElementsByTagName("PDBx:datablock")
        assert(len(main_tags) == 1)
        self.main_tag = main_tags[0]

        if self.main_tag.hasAttribute('datablockName'):
            self.pdb_id = self.main_tag.getAttribute('datablockName').upper()

        xsd_version = os.path.split(self.main_tag.getAttribute('xmlns:PDBx'))[1]
        if xsd_versions.get(xsd_version):
            self.xml_version = xsd_versions[xsd_version]
        else:
            raise Exception("XML version is %s. This module only handles versions %s so far." % (xsd_version, ", ".join(xsd_versions.keys())))

    def parse_deprecation(self):
        '''Checks to see if the PDB file has been deprecated and, if so, what the new ID is.'''
        deprecation_tag = self.main_tag.getElementsByTagName("PDBx:pdbx_database_PDB_obs_sprCategory")
        assert(len(deprecation_tag) <= 1)
        if deprecation_tag:
            deprecation_tag = deprecation_tag[0]

            deprecation_subtag = deprecation_tag.getElementsByTagName("PDBx:pdbx_database_PDB_obs_spr")
            assert(len(deprecation_subtag) == 1)
            deprecation_subtag = deprecation_subtag[0]
            assert(deprecation_subtag.hasAttribute('replace_pdb_id'))
            assert(deprecation_subtag.hasAttribute('pdb_id'))
            old_pdb_id = deprecation_subtag.getAttribute('replace_pdb_id').upper()
            new_pdb_id = deprecation_subtag.getAttribute('pdb_id').upper()

            if self.pdb_id == old_pdb_id:
                self.deprecated = True
                self.replacement_pdb_id = new_pdb_id
            else:
                assert(self.pdb_id == new_pdb_id)

    def parse_atoms(self):
        '''All ATOM lines are parsed even though only one per residue needs to be parsed. The reason for parsing all the
           lines is just to sanity-checks that the ATOMs within one residue are consistent with each other.'''

        atom_site_header_tag = self.main_tag.getElementsByTagName("PDBx:atom_siteCategory")
        assert(len(atom_site_header_tag) == 1)
        atom_site_header_tag = atom_site_header_tag[0]

        atom_site_tags = atom_site_header_tag.getElementsByTagName("PDBx:atom_site")

        residue_map = {}
        residues_read = {}
        int_type = types.IntType
        for t in atom_site_tags:
            r, seqres, ResidueAA, Residue3AA = PDBML_slow.parse_atom_site(t, self.modified_residues)
            if r:
                # skip certain ACE residues
                if not(self.pdb_id in cases_with_ACE_residues_we_can_ignore and Residue3AA == 'ACE'):
                    full_residue_id = str(r)
                    if residues_read.get(full_residue_id):
                        assert(residues_read[full_residue_id] == (r.ResidueAA, seqres))
                    else:
                        residues_read[full_residue_id] = (r.ResidueAA, seqres)
                        residue_map[r.Chain] = residue_map.get(r.Chain, {})
                        assert(type(seqres) == int_type)
                        residue_map[r.Chain][str(r)] = seqres

        ## Create SequenceMap objects to map the ATOM Sequences to the SEQRES Sequences
        atom_to_seqres_sequence_maps = {}
        for chain_id, atom_seqres_mapping in residue_map.iteritems():
            atom_to_seqres_sequence_maps[chain_id] = SequenceMap.from_dict(atom_seqres_mapping)

        self.atom_to_seqres_sequence_maps = atom_to_seqres_sequence_maps

    @staticmethod
    def parse_atom_site(t, modified_residues):

        # Only parse ATOM records
        if parse_singular_string(t, 'PDBx:group_PDB') == 'HETATM':
            return None, None, None, None
        assert(parse_singular_string(t, 'PDBx:group_PDB') == 'ATOM')

        # NOTE: x, y, z values are per-ATOM but we do not use them yet
        x, y, z = parse_singular_float(t, "PDBx:Cartn_x"), parse_singular_float(t, "PDBx:Cartn_y"), parse_singular_float(t, "PDBx:Cartn_z")

        PDB_chain_id = parse_singular_alphabetic_character(t, 'PDBx:auth_asym_id')
        ATOM_residue_id = parse_singular_int(t, 'PDBx:auth_seq_id')

        # Parse insertion code. Sometimes this tag exists but is set as nil in its attributes (xsi:nil = "true").
        PDB_insertion_code = " "
        insertion_code_tags = t.getElementsByTagName('PDBx:pdbx_PDB_ins_code')
        if insertion_code_tags:
            assert(len(insertion_code_tags) == 1)
            insertion_code_tag = insertion_code_tags[0]
            if not(insertion_code_tag.hasAttribute('xsi:nil') and insertion_code_tag.getAttribute('xsi:nil') == 'true'):
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

        return r, SEQRES_index, residue_1_letter, residue_3_letter


class AtomSite(object):
    # Same as AtomSite but no x, y, z data
    fields = [
        # Field name                    PDBML tag name          Values                                      Expected type that we store
        'IsHETATM',                 #   PDBx:group_PDB          True iff record type is HETATM              Boolean
        'IsATOM',                   #   PDBx:group_PDB          True iff record type is ATOM                Boolean
        'PDBChainID',               #   PDBx:auth_asym_id       PDB chain ID                                Character (alphanumeric)
        'PDBChainIDIsNull',         #   PDBx:auth_asym_id       PDB chain ID                                Boolean
        'ATOMResidueID',            #   PDBx:auth_seq_id        Residue ID (not including insertion code)   Int
        'ATOMResidueiCode',         #   PDBx:pdbx_PDB_ins_code  Residue insertion code                      Character (alpha)
        'ATOMResidueiCodeIsNull',   #   PDBx:pdbx_PDB_ins_code  Need to determine if icode is nil           Boolean
        'SEQRESIndex',              #   PDBx:label_seq_id       The SEQRES index                            Int
        'ATOMResidueAA',            #   PDBx:auth_comp_id       The residue type in the ATOM sequence       String (we seem to assume 3 letter protein residues here...)
        'ATOMSeqresResidueAA',      #   PDBx:label_comp_id      The residue type in the SEQRES sequence     String (we seem to assume 3 letter protein residues here...)
    ]


    def __init__(self):
        self.clear()


    def clear(self):
        d = self.__dict__
        for f in self.__class__.fields:
            d[f] = None
        d['IsHETATM'] = False
        d['IsATOM'] = False
        d['ATOMResidueiCode'] = ' '
        #self.__dict__['ATOMResidueiCodeIsNull'] = True


    def get_pdb_residue_id(self):
        d = self.__dict__
        residue_identifier = '%s%s%s' % (d['PDBChainID'], str(d['ATOMResidueID']).rjust(4), d['ATOMResidueiCode'])
        assert(len(residue_identifier) == 6)
        return residue_identifier


    def validate(self):
        # Assertions
        assert(not(self.IsHETATM and self.IsATOM))
        assert(self.IsHETATM or self.IsATOM)

        if self.ATOMResidueiCode != ' ':                        # Sometimes the insertion code tag exists but is empty. In this case, its attribute xsi:nil should be "true"
            assert(self.ATOMResidueiCodeIsNull == None)
            assert(len(self.ATOMResidueiCode) == 1)
            assert(self.ATOMResidueiCode.isalpha())
        if self.ATOMResidueiCodeIsNull:
            assert(self.ATOMResidueiCode == ' ')

        assert(self.ATOMResidueAA == self.ATOMSeqresResidueAA)

        assert(len(self.PDBChainID) == 1)
        assert(self.PDBChainID.isalnum() or self.PDBChainID == ' ') # e.g. 2MBP


    def convert_to_residue(self, modified_residues):
        residue_3_letter = self.ATOMResidueAA
        residue_1_letter = residue_type_3to1_map.get(residue_3_letter) or protonated_residue_type_3to1_map.get(residue_3_letter) or non_canonical_amino_acids.get(residue_3_letter)

        if not residue_1_letter:
            residue_identifier = self.get_pdb_residue_id()
            if modified_residues.get(residue_identifier):
                residue_1_letter = modified_residues[residue_identifier]['original_residue_1']
        if not residue_1_letter:
            '''Too many cases to worry about... we will have to use residue_3_letter to sort those out.'''
            residue_1_letter = 'X'

        pdb_residue = IdentifyingPDBResidue(self.PDBChainID, ("%d%s" % (self.ATOMResidueID, self.ATOMResidueiCode)).rjust(5), residue_1_letter, None, residue_3_letter)
        return pdb_residue, self.SEQRESIndex, residue_1_letter, residue_3_letter


    def __repr__(self):
        # For debugging
        return '\n'.join([('%s : %s' % (f.ljust(23), self.__dict__[f])) for f in self.__class__.fields if self.__dict__[f] != None])


class AtomSite_xyz(AtomSite):
    fields = [
        # Field name                    PDBML tag name          Values                                      Expected type that we store
        'IsHETATM',                 #   PDBx:group_PDB          True iff record type is HETATM              Boolean
        'IsATOM',                   #   PDBx:group_PDB          True iff record type is ATOM                Boolean
        'PDBChainID',               #   PDBx:auth_asym_id       PDB chain ID                                Character (alphanumeric)
        'ATOMResidueID',            #   PDBx:auth_seq_id        Residue ID (not including insertion code)   Int
        'ATOMResidueiCode',         #   PDBx:pdbx_PDB_ins_code  Residue insertion code                      Character (alpha)
        'ATOMResidueiCodeIsNull',   #   PDBx:pdbx_PDB_ins_code  Need to determine if icode is nil           Boolean
        'x',                        #   PDBx:Cartn_x            x coordinate                                Float
        'y',                        #   PDBx:Cartn_y            y coordinate                                Float
        'z',                        #   PDBx:Cartn_z            z coordinate                                Float
        'SEQRESIndex',              #   PDBx:label_seq_id       The SEQRES index                            Int
        'ATOMResidueAA',            #   PDBx:auth_comp_id       The residue type in the ATOM sequence       String (we seem to assume 3 letter protein residues here...)
        'ATOMSeqresResidueAA',      #   PDBx:label_comp_id      The residue type in the SEQRES sequence     String (we seem to assume 3 letter protein residues here...)
    ]

    def convert_to_residue(self, modified_residues):
        residue_3_letter = self.ATOMResidueAA
        residue_1_letter = residue_type_3to1_map.get(residue_3_letter) or protonated_residue_type_3to1_map.get(residue_3_letter) or non_canonical_amino_acids.get(residue_3_letter)

        if not residue_1_letter:
            residue_identifier = self.get_pdb_residue_id()
            if modified_residues.get(residue_identifier):
                residue_1_letter = modified_residues[residue_identifier]['original_residue_1']
        if not residue_1_letter:
            '''Too many cases to worry about... we will have to use residue_3_letter to sort those out.'''
            residue_1_letter = 'X'

        pdb_residue = IdentifyingPDBResidue(self.PDBChainID, ("%d%s" % (self.ATOMResidueID, self.ATOMResidueiCode)).rjust(5), residue_1_letter, None, residue_3_letter)
        pdb_residue.add_position(self.x, self.y, self.z)
        return pdb_residue, self.SEQRESIndex, residue_1_letter, residue_3_letter


# Faster classes using xml.sax

class PDBML(xml.sax.handler.ContentHandler):

    def __init__(self, xml_contents, pdb_contents, bio_cache = None, pdb_id = None):
        '''The PDB contents should be passed so that we can deal with HETATM records as the XML does not contain the necessary information.'''

        self.xml_contents = xml_contents
        self.atom_to_seqres_sequence_maps = {}
        self.counters = {}
        self.pdb_id = pdb_id
        self.xml_version = None
        self.tag_data = []
        self.in_atom_sites_block = False
        self._residue_map = {}
        self._residues_read = {}
        self._BLOCK = None                      # This is used to create a simple FSA for the parsing
        self.current_atom_site = AtomSite()
        self.bio_cache = bio_cache

        # Create the PDB
        if bio_cache and pdb_id:
            self.modified_residues = bio_cache.get_pdb_object(pdb_id).modified_residues
        else:
            self.modified_residues = PDB(pdb_contents).modified_residues

        self.deprecated = True
        self.replacement_pdb_id = None

        self._start_handlers = {
            1 : self.parse_deprecated_tags,
            2 : self.parse_atom_site,
        }
        self._end_handlers = {
            1 : None,
            2 : self.parse_atom_tag_data,
        }
        assert(xml_contents.find('encoding="UTF-8"') != -1)


    @staticmethod
    def retrieve(pdb_id, cache_dir = None, bio_cache = None):
        '''Creates a PDBML object by using a cached copy of the files if they exists or by retrieving the files from the RCSB.'''

        pdb_contents = None
        xml_contents = None
        pdb_id = pdb_id.upper()

        if bio_cache:
            pdb_contents = bio_cache.get_pdb_contents(pdb_id)
            xml_contents = bio_cache.get_pdbml_contents(pdb_id)

        if cache_dir:
            if not pdb_contents:
                # Check to see whether we have a cached copy of the PDB file
                filename = os.path.join(cache_dir, "%s.pdb" % pdb_id)
                if os.path.exists(filename):
                    pdb_contents = read_file(filename)

            if not xml_contents:
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
        handler = PDBML(xml_contents, pdb_contents, bio_cache = bio_cache, pdb_id = pdb_id)
        xml.sax.parseString(xml_contents, handler)
        return handler


    def start_document(self): pass


    def start_element(self, name, attributes):
        self.tag_data = []

        if self._BLOCK != None:
            self._start_handlers[self._BLOCK](name, attributes)

        elif name == 'PDBx:atom_site':
            # All ATOM lines are parsed even though only one per residue needs to be parsed. The reason for parsing all the
            # lines is just to sanity-checks that the ATOMs within one residue are consistent with each other.
            self._BLOCK = 2
            self.current_atom_site.clear()
            assert(self.in_atom_sites_block)

        elif name == 'PDBx:atom_siteCategory':
            self.in_atom_sites_block = True
            self.counters['PDBx:atom_siteCategory'] = self.counters.get('PDBx:atom_siteCategory', 0) + 1

        elif name == 'PDBx:datablock':
            self.counters['PDBx:datablock'] = self.counters.get('PDBx:datablock', 0) + 1
            self.parse_header(attributes)

        elif name == "PDBx:pdbx_database_PDB_obs_sprCategory":
            self._BLOCK = 1
            self.counters['PDBx:pdbx_database_PDB_obs_sprCategory'] = self.counters.get('PDBx:pdbx_database_PDB_obs_sprCategory', 0) + 1

    def parse_deprecated_tags(self, name, attributes):
        '''Checks to see if the PDB file has been deprecated and, if so, what the new ID is.'''
        if name == 'PDBx:pdbx_database_PDB_obs_spr':
            self.counters['PDBx:pdbx_database_PDB_obs_spr'] = self.counters.get('PDBx:pdbx_database_PDB_obs_spr', 0) + 1
            old_pdb_id = attributes.get('replace_pdb_id').upper()
            new_pdb_id = attributes.get('pdb_id').upper()
            assert(old_pdb_id and new_pdb_id)

            if self.pdb_id == old_pdb_id:
                self.deprecated = True
                self.replacement_pdb_id = new_pdb_id
            else:
                assert(self.pdb_id == new_pdb_id)

    def end_element(self, name):
        tag_content = ("".join(self.tag_data)).strip()

        if self._BLOCK != None:
            handler = self._end_handlers.get(self._BLOCK)
            if handler:
                handler(name, tag_content)

        if name == 'PDBx:atom_site' or name == "PDBx:pdbx_database_PDB_obs_sprCategory":
            self._BLOCK = None

        elif name == 'PDBx:atom_siteCategory':
            self.in_atom_sites_block = False
            ## Create SequenceMap objects to map the ATOM Sequences to the SEQRES Sequences
            atom_to_seqres_sequence_maps = {}
            for chain_id, atom_seqres_mapping in self._residue_map.iteritems():
                atom_to_seqres_sequence_maps[chain_id] = SequenceMap.from_dict(atom_seqres_mapping)
            self.atom_to_seqres_sequence_maps = atom_to_seqres_sequence_maps

    def parse_header(self, attributes):
        if attributes.get('datablockName'):
            pdb_id = attributes.get('datablockName').upper()
            if self.pdb_id:
                assert(pdb_id == self.pdb_id)
            self.pdb_id = pdb_id

        xsd_version = os.path.split(attributes.get('xmlns:PDBx'))[1]
        if xsd_versions.get(xsd_version):
            self.xml_version = xsd_versions[xsd_version]
        else:
            raise Exception("XML version is %s. This module only handles versions %s so far." % (xsd_version, ", ".join(xsd_versions.keys())))

    def parse_atom_site(self, name, attributes):
        '''Parse the atom tag attributes. Most atom tags do not have attributes.'''
        if name == "PDBx:pdbx_PDB_ins_code":
            assert(not(self.current_atom_site.ATOMResidueiCodeIsNull))
            if attributes.get('xsi:nil') == 'true':
                self.current_atom_site.ATOMResidueiCodeIsNull = True
        if name == "PDBx:auth_asym_id":
            assert(not(self.current_atom_site.PDBChainIDIsNull))
            if attributes.get('xsi:nil') == 'true':
                self.current_atom_site.PDBChainIDIsNull = True

    def parse_atom_tag_data(self, name, tag_content):
        '''Parse the atom tag data.'''
        current_atom_site = self.current_atom_site
        if current_atom_site.IsHETATM:
            # Early out - do not parse HETATM records
            return

        elif name == 'PDBx:atom_site':
            # We have to handle the atom_site close tag here since we jump based on self._BLOCK first in end_element

            #'''Add the residue to the residue map.'''
            self._BLOCK = None
            current_atom_site = self.current_atom_site
            current_atom_site.validate()
            if current_atom_site.IsATOM:
                # Only parse ATOM records
                r, seqres, ResidueAA, Residue3AA = current_atom_site.convert_to_residue(self.modified_residues)
                if r:
                    if not(self.pdb_id in cases_with_ACE_residues_we_can_ignore and Residue3AA == 'ACE'):
                        # skip certain ACE residues
                        full_residue_id = str(r)
                        if self._residues_read.get(full_residue_id):
                            assert(self._residues_read[full_residue_id] == (r.ResidueAA, seqres))
                        else:
                            self._residues_read[full_residue_id] = (r.ResidueAA, seqres)
                            self._residue_map[r.Chain] = self._residue_map.get(r.Chain, {})
                            assert(type(seqres) == int_type)
                            self._residue_map[r.Chain][str(r)] = seqres

        # Record type
        elif name == 'PDBx:group_PDB':
            # ATOM or HETATM
            if tag_content == 'ATOM':
                current_atom_site.IsATOM = True
            elif tag_content == 'HETATM':
                current_atom_site.IsHETATM = True
            else:
                raise Exception("PDBx:group_PDB was expected to be 'ATOM' or 'HETATM'. '%s' read instead." % tag_content)

        # Residue identifier - chain ID, residue ID, insertion code
        elif name == 'PDBx:auth_asym_id':
            assert(not(current_atom_site.PDBChainID))
            current_atom_site.PDBChainID = tag_content
            if not tag_content:
                assert(current_atom_site.PDBChainIDIsNull)
                if self.pdb_id.upper() == '2MBP':
                    current_atom_site.PDBChainID = 'A' # e.g. 2MBP
                else:
                    current_atom_site.PDBChainID = ' '

        elif name == 'PDBx:auth_seq_id':
            assert(not(current_atom_site.ATOMResidueID))
            current_atom_site.ATOMResidueID = int(tag_content)
        elif name == "PDBx:pdbx_PDB_ins_code":
            if current_atom_site.ATOMResidueiCodeIsNull:
                assert(len(tag_content) == 0)
            else:
                assert(current_atom_site.ATOMResidueiCode == ' ')
                current_atom_site.ATOMResidueiCode = tag_content
        elif name == "PDBx:auth_comp_id":
            assert(not(current_atom_site.ATOMResidueAA))
            current_atom_site.ATOMResidueAA = tag_content

        elif name == "PDBx:label_seq_id":
            assert(not(current_atom_site.SEQRESIndex))
            current_atom_site.SEQRESIndex = int(tag_content)
        elif name == "PDBx:label_comp_id":
            assert(not(current_atom_site.ATOMSeqresResidueAA))
            current_atom_site.ATOMSeqresResidueAA = tag_content

    def create_atom_data(self):
        '''The atom site work is split into two parts. This function type-converts the tags.'''

        current_atom_site = self.current_atom_site

        # Only parse ATOM records
        if current_atom_site.IsHETATM:
            # Early out - do not parse HETATM records
            return None, None, None, None
        elif current_atom_site.IsATOM:
            return current_atom_site.convert_to_residue(self.modified_residues)
        else:
            raise Exception('current_atom_site')

    def end_document(self):
        assert(self.counters.get('PDBx:datablock') == 1)
        assert(self.counters.get('PDBx:atom_siteCategory') == 1)
        assert(self.counters.get('PDBx:pdbx_database_PDB_obs_sprCategory', 0) <= 1)
        assert(self.counters.get('PDBx:pdbx_database_PDB_obs_spr', 0) >= self.counters.get('PDBx:pdbx_database_PDB_obs_sprCategory', 0))

    def characters(self, chrs):
        # Note: I use a list to store self.tag_data, append to the list, then join the contents into a string. In general,
        # this is a better approach than string concatenation since there is less garbage created. However, if the strings
        # are small and the list only ever contains one string (which could be the case with this particular class), my
        # approach may create more garbage. I tested this with 3ZKB is a good single test case and there is no noticeable
        # difference in the amount of garbage created (1 extra piece of garbage was created).
        self.tag_data.append(chrs)

    startDocument = start_document
    endDocument = end_document
    startElement = start_element
    endElement = end_element



class PDBML_xyz(PDBML):
    '''A subclass which parses x, y, z coordinates (we do not use this at present.'''

    def __init__(self, xml_contents, pdb_contents):
        super(PDBML_xyz, self).__init__(xml_contents, pdb_contents)
        self.current_atom_site = AtomSite()

    def parse_atom_tag_data(self, name, tag_content):
        '''Parse the atom tag data.'''
        current_atom_site = self.current_atom_site
        if current_atom_site.IsHETATM:
            # Early out - do not parse HETATM records
            return

        elif name == 'PDBx:atom_site':
            # We have to handle the atom_site close tag here since we jump based on self._BLOCK first in end_element
            # To keep the code a little neater, I separate the logic out into end_atom_tag at the cost of one function call per atom

            #self.end_atom_tag()
            #'''Add the residue to the residue map.'''
            self._BLOCK = None
            current_atom_site = self.current_atom_site
            current_atom_site.validate()
            if current_atom_site.IsATOM:
                # Only parse ATOM records
                r, seqres, ResidueAA, Residue3AA = current_atom_site.convert_to_residue(self.modified_residues)
                if r:
                    if not(self.pdb_id in cases_with_ACE_residues_we_can_ignore and Residue3AA == 'ACE'):
                        # skip certain ACE residues
                        full_residue_id = str(r)
                        if self._residues_read.get(full_residue_id):
                            assert(self._residues_read[full_residue_id] == (r.ResidueAA, seqres))
                        else:
                            self._residues_read[full_residue_id] = (r.ResidueAA, seqres)
                            self._residue_map[r.Chain] = self._residue_map.get(r.Chain, {})
                            assert(type(seqres) == int_type)
                            self._residue_map[r.Chain][str(r)] = seqres

        # Record type
        elif name == 'PDBx:group_PDB':
            # ATOM or HETATM
            if tag_content == 'ATOM':
                current_atom_site.IsATOM = True
            elif tag_content == 'HETATM':
                current_atom_site.IsHETATM = True
            else:
                raise Exception("PDBx:group_PDB was expected to be 'ATOM' or 'HETATM'. '%s' read instead." % tag_content)

        # Residue identifier - chain ID, residue ID, insertion code
        elif name == 'PDBx:auth_asym_id':
            assert(not(current_atom_site.PDBChainID))
            current_atom_site.PDBChainID = tag_content
        elif name == 'PDBx:auth_seq_id':
            assert(not(current_atom_site.ATOMResidueID))
            current_atom_site.ATOMResidueID = int(tag_content)
        elif name == "PDBx:pdbx_PDB_ins_code":
            if current_atom_site.ATOMResidueiCodeIsNull:
                assert(len(tag_content) == 0)
            else:
                assert(current_atom_site.ATOMResidueiCode == ' ')
                current_atom_site.ATOMResidueiCode = tag_content
        elif name == "PDBx:auth_comp_id":
            assert(not(current_atom_site.ATOMResidueAA))
            current_atom_site.ATOMResidueAA = tag_content

        elif name == "PDBx:label_seq_id":
            assert(not(current_atom_site.SEQRESIndex))
            current_atom_site.SEQRESIndex = int(tag_content)
        elif name == "PDBx:label_comp_id":
            assert(not(current_atom_site.ATOMSeqresResidueAA))
            current_atom_site.ATOMSeqresResidueAA = tag_content

        # Coordinates
        elif name == "PDBx:Cartn_x":
            assert(not(current_atom_site.x))
            current_atom_site.x = float(tag_content)
        elif name == "PDBx:Cartn_y":
            assert(not(current_atom_site.y))
            current_atom_site.y = float(tag_content)
        elif name == "PDBx:Cartn_z":
            assert(not(current_atom_site.z))
            current_atom_site.z = float(tag_content)