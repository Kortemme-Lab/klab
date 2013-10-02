#!/usr/bin/python
# encoding: utf-8
"""
sifts.py
Basic parsing for the SIFTS XML format. This is currently used to map PDB ATOM residues to indices within the UniParc sequence.

Created by Shane O'Connor 2013
"""

import os
import xml
from xml.sax import parse as parse_xml

from tools.fs.io import read_file, write_file, safe_gz_unzip
from tools.comms.ftp import get_insecure_resource, FTPException550
from tools import colortext
import rcsb
from pdb import PDB#, cases_with_ACE_residues_we_can_ignore
from basics import SequenceMap, residue_type_3to1_map, protonated_residue_type_3to1_map, non_canonical_amino_acids


# Methods

def retrieve_file_from_EBI(resource, silent = True):
    '''Retrieve a file from the RCSB.'''
    if not silent:
        colortext.printf("Retrieving %s from EBI" % os.path.split(resource)[1], color = "aqua")
    return get_insecure_resource("ftp.ebi.ac.uk", resource)

def retrieve_xml(pdb_id, silent = True):
    return retrieve_file_from_EBI("/pub/databases/msd/sifts/xml/%s.xml.gz" % pdb_id.lower(), silent)


# Classes


class SIFTSResidue(object):
    # Same as AtomSite but no x, y, z data
    fields = [
        # Field name                SIFTS attribute name        Values                              Expected type that we store
        'PDBChainID',           #   dbChainId                   PDB chain ID                        Character
        'PDBResidueID',         #   dbResNum                    PDB residue ID                      String (alphanumeric)
        'PDBResidue3AA',        #   dbResName                   PDB residue type                    String (length=3)
        'UniProtAC',            #   dbAccessionId               AC e.g. "P00734"                    String (length=6)
        'UniProtResidueIndex',  #   dbResNum                    UniProt/UniParc sequence index      Integer
        'UniProtResidue1AA',    #   dbResName                   UniProt/UniParc residue type        Character
        'WasNotObserved',        #   residueDetail.Annotation    Not_Observed                        Boolean
    ]

    def __init__(self):
        self.clear()

    def clear(self):
        d = self.__dict__
        for f in self.__class__.fields:
            d[f] = None
        d['WasNotObserved'] = False

    def add_pdb_residue(self, PDBChainID, PDBResidueID, PDBResidue3AA):

        assert(not(self.PDBChainID))
        assert(len(PDBChainID) == 1)

        assert(not(self.PDBResidueID))
        assert(PDBResidueID.isalnum() or int(PDBResidueID) != None)

        assert(not(self.PDBResidue3AA))
        assert(len(PDBResidue3AA) == 3)

        self.PDBChainID, self.PDBResidueID, self.PDBResidue3AA = PDBChainID, PDBResidueID, PDBResidue3AA

    def add_uniprot_residue(self, UniProtAC, UniProtResidueIndex, UniProtResidue1AA):

        assert(not(self.UniProtAC))
        assert(len(UniProtAC) == 6)

        assert(not(self.UniProtResidueIndex))
        assert(UniProtResidueIndex.isdigit())

        assert(not(self.UniProtResidue1AA))
        assert(len(UniProtResidue1AA) == 1)

        self.UniProtAC, self.UniProtResidueIndex, self.UniProtResidue1AA = UniProtAC, int(UniProtResidueIndex), UniProtResidue1AA

    def has_pdb_to_uniprot_mapping(self):
        return self.PDBChainID and self.UniProtAC

    def get_pdb_residue_id(self):
        d = self.__dict__
        if d['PDBResidueID'].isdigit():
            residue_identifier = '%s%s ' % (d['PDBChainID'], str(d['PDBResidueID']).rjust(4))
        else:
            residue_identifier = '%s%s' % (d['PDBChainID'], str(d['PDBResidueID']).rjust(5))
        assert(len(residue_identifier) == 6)
        return residue_identifier

    def __repr__(self):
        # For debugging
        return '\n'.join([('%s : %s' % (f.ljust(23), self.__dict__[f])) for f in self.__class__.fields if self.__dict__[f] != None])


class SIFTS(xml.sax.handler.ContentHandler):

    def __init__(self, xml_contents, pdb_contents, acceptable_sequence_percentage_match = 70.0):
        '''The PDB contents should be passed so that we can deal with HETATM records as the XML does not contain the necessary information.'''

        self.atom_to_uniparc_sequence_maps = {} # UniProt AC -> SequenceMap(PDB ResidueID -> UniParc sequence index) where the UniParc sequence index is 1-based (first element has index 1)
        self.counters = {}
        self.pdb_id = None
        self.acceptable_sequence_percentage_match = acceptable_sequence_percentage_match
        self.tag_data = []

        self.modified_residues = PDB(pdb_contents).modified_residues

        self._STACK = []                        # This is used to create a simple FSA for the parsing
        self.current_residue = None
        self.residues = []
        self.reading_unobserved_property = False

        assert(0 <= acceptable_sequence_percentage_match <= 100)
        assert(xml_contents.find("encoding='UTF-8'") != -1)

    @staticmethod
    def retrieve(pdb_id, cache_dir = None, acceptable_sequence_percentage_match = 70.0):
        '''Creates a PDBML object by using a cached copy of the files if they exists or by retrieving the files from the RCSB.'''

        pdb_contents = None
        xml_contents = None
        pdb_id = pdb_id.upper()
        l_pdb_id = pdb_id.lower()

        if len(pdb_id) != 4 or not pdb_id.isalnum():
            raise Exception("Bad PDB identifier '%s'." % pdb_id)

        if cache_dir:
            # Check to see whether we have a cached copy of the PDB file
            filename = os.path.join(cache_dir, "%s.pdb" % pdb_id)
            if os.path.exists(filename):
                pdb_contents = read_file(filename)

            # Check to see whether we have a cached copy of the XML file
            filename = os.path.join(cache_dir, "%s.sifts.xml.gz" % l_pdb_id)
            if os.path.exists(filename):
                xml_contents = read_file(filename)

        # Get any missing files from the RCSB and create cached copies if appropriate
        if not pdb_contents:
            pdb_contents = rcsb.retrieve_pdb(pdb_id)
            if cache_dir:
                write_file(os.path.join(cache_dir, "%s.pdb" % pdb_id), pdb_contents)

        if not xml_contents:
            try:
                xml_contents = retrieve_xml(pdb_id, silent = False)
                if cache_dir:
                    write_file(os.path.join(cache_dir, "%s.sifts.xml.gz" % l_pdb_id), xml_contents)
            except FTPException550:
                raise Exception('The file "%s.sifts.xml.gz" could not be found on the EBI FTP server.' % l_pdb_id)

        xml_contents = safe_gz_unzip(xml_contents)

        # Return the object
        handler = SIFTS(xml_contents, pdb_contents, acceptable_sequence_percentage_match = acceptable_sequence_percentage_match)
        xml.sax.parseString(xml_contents, handler)
        return handler

    def stack_push(self, lvl, data):
        if lvl == 0:
            assert(not(self._STACK))
        else:
            assert(self._STACK and (len(self._STACK) == lvl))
            for x in range(lvl):
                assert(self._STACK[x][0] == x)

        self._STACK.append((lvl, data))

    def stack_pop(self, lvl):
        num_levels = lvl + 1
        assert(self._STACK and (len(self._STACK) == num_levels))
        for x in range(num_levels):
            assert(self._STACK[x][0] == x)
        self._STACK.pop()
        if lvl == 0:
            assert(not(self._STACK))

    def check_stack(self, lvl):
        assert(self._STACK and (len(self._STACK) == lvl))
        for x in range(lvl):
            assert(self._STACK[x][0] == x)

    def start_document(self): pass

    def start_element(self, name, attributes):
        self.tag_data = ''

        if name == 'crossRefDb':
            self.start_crossRefDb(attributes)

        elif name == 'residueDetail':
            self.stack_push(3, None)
            self.start_residueDetail(attributes)

        elif name == 'residue':
            self.stack_push(2, None)
            self.current_residue = SIFTSResidue()

        elif name == 'listResidue':
            self.stack_push(1, None)

        elif name == 'entity':
            assert(attributes.get('type'))
            entityId = None
            if attributes['type'] == 'protein':
                entityId = attributes.get('entityId')
            self.stack_push(0, entityId)

        elif name == 'entry':
            self.counters['entry'] = self.counters.get('entry', 0) + 1
            self.parse_header(attributes)

    def parse_header(self, attributes):
        if attributes.get('dbAccessionId'):
            self.pdb_id = attributes.get('dbAccessionId').upper()
        else:
            raise Exception('Could not verify the PDB ID from the <entry> tag.')

    def start_residueDetail(self, attributes):
        self.check_stack(4)
        self.reading_unobserved_property = False
        dbSource = attributes.get('dbSource')
        assert(dbSource)
        if dbSource == 'PDBe':
            residue_detail_property = attributes.get('property')
            if residue_detail_property and residue_detail_property == 'Annotation':
                self.reading_unobserved_property = True

    def start_crossRefDb(self, attributes):
        self.check_stack(3)
        dbSource = attributes.get('dbSource')
        assert(dbSource)

        if dbSource == 'PDB' or dbSource == 'UniProt':
            current_residue = self.current_residue

            dbCoordSys = attributes.get('dbCoordSys')
            dbAccessionId = attributes.get('dbAccessionId')
            dbResNum = attributes.get('dbResNum')
            dbResName = attributes.get('dbResName')

            if dbSource == 'PDB':
                dbChainId = attributes.get('dbChainId')
                assert(dbCoordSys == "PDBresnum")
                assert(dbAccessionId.upper() == self.pdb_id.upper())
                assert(dbChainId == self._STACK[0][1])
                assert(dbCoordSys and dbAccessionId and dbResNum and dbResName and dbChainId )
                current_residue.add_pdb_residue(dbChainId, dbResNum, dbResName)

            elif dbSource == 'UniProt':
                assert(dbCoordSys and dbAccessionId and dbResNum and dbResName)
                assert(dbCoordSys == "UniProt")
                assert(dbCoordSys and dbAccessionId and dbResNum and dbResName)
                current_residue.add_uniprot_residue(dbAccessionId, dbResNum, dbResName)

    def end_element(self, name):
        tag_content = self.tag_data

        if name == 'residueDetail':
            self.stack_pop(3)
            if self.reading_unobserved_property and (tag_content == 'Not_Observed'):
                self.current_residue.WasNotObserved = True
            self.reading_unobserved_property = False

        elif name == 'residue':
            self.stack_pop(2)
            if self.current_residue.has_pdb_to_uniprot_mapping():
                self.residues.append(self.current_residue)
            self.current_residue = None

        elif name == 'listResidue':
            self.stack_pop(1)

        elif name == 'entity':
            self.stack_pop(0)

    def end_document(self):
        assert(self.counters['entry'] == 1)

        residue_count = 0
        residues_matched = 0
        residue_maps = {}
        residues_encountered = set()
        for r in self.residues:

            if not(r.PDBResidueID.isalnum() and int(r.PDBResidueID.isalnum()) < 0):
                # These are not valid PDB residue IDs - the SIFTS XML convention sometimes assigns negative residue IDs to unobserved residues before the first ATOM record
                # (only if the first residue ID is 1?)
                pass

            # Store the PDB->UniProt mapping
            UniProtAC = r.UniProtAC
            full_pdb_residue_ID = r.get_pdb_residue_id()
            residue_maps[UniProtAC] = residue_maps.get(UniProtAC, {})
            residue_maps[UniProtAC][full_pdb_residue_ID] = r.UniProtResidueIndex

            # Make sure we only have at most one match per PDB residue
            assert(full_pdb_residue_ID not in residues_encountered)
            residues_encountered.add(full_pdb_residue_ID)

            # Count the number of exact sequence matches
            PDBResidue3AA = r.PDBResidue3AA
            pdb_residue_type = residue_type_3to1_map.get(PDBResidue3AA) or self.modified_residues.get(PDBResidue3AA) or protonated_residue_type_3to1_map.get(PDBResidue3AA) or non_canonical_amino_acids.get(PDBResidue3AA)
            if pdb_residue_type == r.UniProtResidue1AA:
                residues_matched += 1
            residue_count += 1

        # Create the SequenceMaps
        self.atom_to_uniparc_sequence_maps = {}
        for UniProtAC, atom_uniparc_mapping in residue_maps.iteritems():
            self.atom_to_uniparc_sequence_maps[UniProtAC] = SequenceMap.from_dict(atom_uniparc_mapping)

        # Check the match percentage
        if residue_count == 0:
            raise Exception('No residue information matching PDB residues to UniProt residues was found.')
        else:
            percentage_matched = float(residues_matched)*100.0/float(residue_count)
            if percentage_matched < self.acceptable_sequence_percentage_match:
                raise Exception('Expected %.2f%% sequence match on matched residues but the SIFTS results only gave us %.2f%%.' % (self.acceptable_sequence_percentage_match, percentage_matched))

    def characters(self, chrs):
        self.tag_data += chrs

    startDocument = start_document
    endDocument = end_document
    startElement = start_element
    endElement = end_element