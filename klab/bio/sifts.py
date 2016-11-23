#!/usr/bin/python
# encoding: utf-8
"""
sifts.py
Basic parsing for the SIFTS XML format.
This is currently used to map PDB ATOM residues to indices within the UniParc sequence.
We also extract the region maps for each chain i.e. the mappings from parts of the chain to Pfam and SCOP domains etc.

Created by Shane O'Connor 2013
"""

import time
import os
import xml
import traceback

from xml.sax import parse as parse_xml

from klab import colortext
from klab.fs.fsio import read_file, write_file, read_gzip_in_memory
from klab.comms.ftp import get_insecure_resource, FTPException550
from klab.general.strutil import parse_range, merge_range_pairs
from klab.bio import rcsb
from klab.bio.pdb import PDB#, cases_with_ACE_residues_we_can_ignore
from klab.bio.basics import Sequence, SequenceMap, PDBUniParcSequenceMap, residue_type_3to1_map, protonated_residue_type_3to1_map, non_canonical_amino_acids
from klab.bio.uniprot import uniprot_map, UniParcEntry


# Patches for known bad cases (only up-to-date at the time of commit)
overridden_cases = {
    '1HJA' : {
        'region_mapping' : {
            'A' : {
                u'UniProt': {u'P00766': [(1, 13)]}
            },
        },
        'residue_mapping_change' : {
            u'UniProt' : [
                ('P00767', 1, 13, 'P00766'),
            ]
        }
    }
}

# Known bad cases (only up-to-date at the time of commit)
BadSIFTSMappingCases = set([
    '1N02', # PDB residues 'A   4 ' -> 'A  49 ' should map to indices 54->99 of the UniParc sequence
])
CircularPermutantSIFTSMappingCases = {
    '3DA7' : '1BRS', # compare to 1BRS - the sequence is shifted circularly (with a cysteine insertion). See Figure 1 of PubMed #19260676.
}
NoSIFTSPDBUniParcMappingCases = set([
    '2IMM',
])

expected_residue_numbering_schemes = {
    'PDB'          : u'PDBresnum',
    'CATH'         : u'PDBresnum',
    'SCOP'         : u'PDBresnum',
    'UniProt'      : u'UniProt',
    'GO'           : u'UniProt',
    'InterPro'     : u'UniProt',
    'Pfam'         : u'UniProt',
}



# Methods

def retrieve_file_from_EBI(resource, silent = True):
    '''Retrieve a file from the RCSB.'''
    #import sys
    #import traceback
    #print(resource)
    #print('\n'.join(traceback.format_stack()))
    #sys.exit(0)
    if not silent:
        colortext.printf("Retrieving %s from EBI" % os.path.split(resource)[1], color = "aqua")
    attempts = 10
    while attempts > 0:
        try:
            return get_insecure_resource("ftp.ebi.ac.uk", resource)
        except:
            print('FAILED, RETRYING')
            attempts -= 1
            time.sleep(3)


def retrieve_xml(pdb_id, silent = True, unzip = True):
    if unzip:
        return read_gzip_in_memory(retrieve_file_from_EBI("/pub/databases/msd/sifts/xml/%s.xml.gz" % pdb_id.lower(), silent))
    else:
        return retrieve_file_from_EBI("/pub/databases/msd/sifts/xml/%s.xml.gz" % pdb_id.lower(), silent)


def download_xml(pdb_id, dest_dir, silent = True, filename = None, unzip = False):
    assert(os.path.exists(dest_dir))
    lower_case_gz_filename = os.path.join(dest_dir, '{0}.sifts.xml.gz'.format(pdb_id.lower()))
    upper_case_gz_filename = os.path.join(dest_dir, '{0}.sifts.xml.gz'.format(pdb_id.upper()))
    lower_case_filename = os.path.join(dest_dir, '{0}.sifts.xml'.format(pdb_id.lower()))
    upper_case_filename = os.path.join(dest_dir, '{0}.sifts.xml'.format(pdb_id.upper()))

    if filename:
        requested_filename = os.path.join(dest_dir, filename)
        if os.path.exists(requested_filename):
            return read_file(requested_filename)

    if unzip == True:
        if os.path.exists(lower_case_filename):
            contents = read_file(lower_case_filename)
        elif os.path.exists(upper_case_filename):
            contents = read_file(upper_case_filename)
        elif os.path.exists(lower_case_gz_filename):
            contents = read_gzip_in_memory(read_file(lower_case_gz_filename))
        elif os.path.exists(upper_case_gz_filename):
            contents = read_gzip_in_memory(read_file(upper_case_gz_filename))
        else:
            contents = retrieve_xml(pdb_id, silent = silent, unzip = True)
            write_file(os.path.join(dest_dir, filename or '{0}.sifts.xml'.format(pdb_id)), contents)
        return contents
    else:
        if os.path.exists(lower_case_gz_filename):
            contents = read_file(lower_case_gz_filename) # Note: read_file already unzips .gz files
        if os.path.exists(upper_case_gz_filename):
            contents = read_file(upper_case_gz_filename) # Note: read_file already unzips .gz files
        else:
            gzip_contents = retrieve_xml(pdb_id, silent = silent, unzip = False)
            write_file(os.path.join(dest_dir, filename or '{0}.sifts.xml.gz'.format(pdb_id)), gzip_contents)
            contents = read_gzip_in_memory(gzip_contents)
        return contents


# Classes
class MissingSIFTSRecord(Exception): pass
class BadSIFTSMapping(Exception): pass
class PotentialBadSIFTSMapping(Exception): pass
class NoSIFTSPDBUniParcMapping(Exception): pass



class DomainMatch(object):

    def __init__(self, domain_accession, domain_type):
        self.domain_accession = domain_accession
        self.domain_type = domain_type
        self.matches = {}


    def add(self, domain_accession, domain_type, match_quality):
        '''match_quality should be a value between 0 and 1.'''
        self.matches[domain_type] = self.matches.get(domain_type, {})
        self.matches[domain_type][domain_accession] = match_quality


    def get_matches(self, domain_type):
        return set(self.matches.get(domain_type, {}).keys())


    def to_dict(self):
        d = {}
        for other_domain_type, v in sorted(self.matches.iteritems()):
            for domain_accession, match_quality in sorted(v.iteritems()):
                d[other_domain_type] = d.get(other_domain_type, set())
                d[other_domain_type].add(domain_accession)
        return {self.domain_accession : d}


    def __repr__(self):
        s = ''
        for other_domain_type, v in sorted(self.matches.iteritems()):
            s += '%s -> %s\n' % (self.domain_type, other_domain_type)
            for domain_accession, match_quality in sorted(v.iteritems()):
                s += '  %s -> %s: matched at %0.2f\n' % (self.domain_accession, domain_accession, match_quality)
        return s


class SIFTSResidue(object):
    # Same as AtomSite but no x, y, z data
    fields = [
        # Field name                SIFTS attribute name        Values                              Expected type that we store

        # SEQRES / FASTA fields
        'PDBeChainID',          #   residue                     PDB chain ID                        Character
        'PDBeResidueID',        #   residue                     PDBe sequence index                 Integer
        'PDBeResidue3AA',       #   residue                     PDBe residue type                   String (length=3)
        # ATOM record fields
        'PDBChainID',           #   dbChainId                   PDB chain ID                        Character
        'PDBResidueID',         #   dbResNum                    PDB residue ID                      String (alphanumeric)
        'PDBResidue3AA',        #   dbResName                   PDB residue type                    String (length=3)
        'WasNotObserved',        #   residueDetail.Annotation    Not_Observed                        Boolean
        # UniProt record fields
        'UniProtAC',            #   dbAccessionId               AC e.g. "P00734"                    String (length=6 or length=10), see http://www.uniprot.org/help/accession_numbers
        'UniProtResidueIndex',  #   dbResNum                    UniProt/UniParc sequence index      Integer
        'UniProtResidue1AA',    #   dbResName                   UniProt/UniParc residue type        Character
    ]

    def __init__(self, PDBeChainID, PDBeResidueID, PDBeResidue3AA):
        self.clear()
        self._add_pdbe_residue(PDBeChainID, PDBeResidueID, PDBeResidue3AA)


    def equal_up_to_modification(self, other, modified_residues = {}):
        '''Tests whether residues are equal modulo modifications.
           Use case: 2FI5 has two entries for residue E 115, each for a different conformation.
                     In one conformation, the residue type is IAS, beta-l-aspartic acid which we map to 'D' in the sequence.
                     In the other conformation, the residue type is ASP.
                     The difference is to do with the crystallization and/or protein and is valid. We handle this by checking
                     whether the residues are somewhat similar according to our non-canonical mappings.
                     Related case: 2FTM, residue A 115.
        '''
        equalish = True
        for f in self.__class__.fields:
            sv = self.__dict__[f]
            ov = other.__dict__[f]
            if equalish and (sv != ov):
                if f == 'PDBeResidue3AA':
                    s_pdb_residue_type = residue_type_3to1_map.get(sv) or modified_residues.get(sv) or protonated_residue_type_3to1_map.get(sv) or non_canonical_amino_acids.get(sv)
                    o_pdb_residue_type = residue_type_3to1_map.get(ov) or modified_residues.get(ov) or protonated_residue_type_3to1_map.get(ov) or non_canonical_amino_acids.get(ov)
                    equalish = equalish and (s_pdb_residue_type == o_pdb_residue_type)
                elif f == 'PDBResidue3AA':
                    s_pdb_residue_type = residue_type_3to1_map.get(sv) or modified_residues.get(sv) or protonated_residue_type_3to1_map.get(sv) or non_canonical_amino_acids.get(sv)
                    o_pdb_residue_type = residue_type_3to1_map.get(ov) or modified_residues.get(ov) or protonated_residue_type_3to1_map.get(ov) or non_canonical_amino_acids.get(ov)
                    equalish = equalish and (s_pdb_residue_type == o_pdb_residue_type)
                else:
                    return False
        return equalish


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

    def _add_pdbe_residue(self, PDBeChainID, PDBeResidueID, PDBeResidue3AA):

        assert(not(self.PDBeChainID))
        assert(len(PDBeChainID) <= 4) # SIFTS XML and mmCIF entries can have up to four characters in the chain ID

        assert(not(self.PDBeResidueID))
        assert(PDBeResidueID.isdigit())

        assert(not(self.PDBeResidue3AA))
        assert(len(PDBeResidue3AA) == 3)

        self.PDBeChainID, self.PDBeResidueID, self.PDBeResidue3AA = PDBeChainID, int(PDBeResidueID), PDBeResidue3AA


    def add_uniprot_residue(self, UniProtAC, UniProtResidueIndex, UniProtResidue1AA):

        try:
            assert(not(self.UniProtAC))
            assert(len(UniProtAC) == 6 or len(UniProtAC) == 10) # todo: the proper check would be against [OPQ][0-9][A-Z0-9]{3}[0-9]|[A-NR-Z][0-9]([A-Z][A-Z0-9]{2}[0-9]){1,2} as defined in http://www.uniprot.org/help/accession_numbers e.g. A2BC19, P12345, A0A022YWF9

            assert(not(self.UniProtResidueIndex))
            assert(UniProtResidueIndex.isdigit())

            assert(not(self.UniProtResidue1AA))
            assert(len(UniProtResidue1AA) == 1)
        except Exception, e:
            raise colortext.Exception('Unexpected input parsing UniProtAC "{0}", UniProtResidueIndex "{1}", UniProtResidue1AA "{2}".\nError: "{3}".\n{4}'.format(UniProtAC, UniProtResidueIndex, UniProtResidue1AA, str(e), traceback.format_exc()))

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


    def __init__(self, xml_contents, pdb_contents, acceptable_sequence_percentage_match = 70.0, cache_dir = None, domain_overlap_cutoff = 0.88, require_uniprot_residue_mapping = True, restrict_match_percentage_errors_to_these_uniparc_ids = None, bio_cache = None, pdb_id = None):
        ''' The PDB contents should be passed so that we can deal with HETATM records as the XML does not contain the necessary information.
            If require_uniprot_residue_mapping is set and there is no PDB residue -> UniProt sequence index mapping (e.g. 2IMM at the time of writing) then we raise an exception.
            Otherwise, we store the information we can which can still be useful e.g. SCOP domain data.
            bio_cache should be a klab.bio.cache.py::BioCache object and is used to avoid reading/downloading cached files repeatedly.

            This class throws an error if chains match below acceptable_sequence_percentage_match. However, if  restrict_match_percentage_errors_to_these_uniparc_ids
            is set then we only require a sequence match on chains matching those UniParc IDs.
        '''

        self.atom_to_uniparc_sequence_maps = {} # PDB Chain -> PDBUniParcSequenceMap(PDB ResidueID -> (UniParc ID, UniParc sequence index)) where the UniParc sequence index is 1-based (first element has index 1)

        # Note: These maps map from PDB residue IDs to PDBe residue IDs
        self.atom_to_seqres_sequence_maps = {} # PDB Chain -> SequenceMap(PDB ResidueID -> SEQRES sequence index) where the SEQRES sequence index is 1-based (first element has index 1)

        self.seqres_to_uniparc_sequence_maps = {} # PDB Chain -> PDBUniParcSequenceMap(SEQRES index -> (UniParc ID, UniParc sequence index)) where the SEQRES index and UniParc sequence index is 1-based (first element has index 1)
        self.counters = {}
        self.pdb_id = pdb_id
        self.bio_cache = bio_cache
        self.acceptable_sequence_percentage_match = acceptable_sequence_percentage_match
        self.tag_data = []
        self.cache_dir = cache_dir
        self.uniparc_sequences = {}
        self.uniparc_objects = {}
        self.pdb_chain_to_uniparc_id_map = {}
        self.region_mapping = {}
        self.region_map_coordinate_systems = {}
        self.domain_overlap_cutoff = domain_overlap_cutoff # the percentage (measured in the range [0, 1.0]) at which we consider two domains to be the same e.g. if a Pfam domain of length 60 overlaps with a SCOP domain on 54 residues then the overlap would be 54/60 = 0.9
        self.require_uniprot_residue_mapping = require_uniprot_residue_mapping
        self.restrict_match_percentage_errors_to_these_uniparc_ids = restrict_match_percentage_errors_to_these_uniparc_ids
        self.xml_contents = xml_contents
        self.pdb_contents = pdb_contents

        if bio_cache and pdb_id:
            self.modified_residues = bio_cache.get_pdb_object(pdb_id).modified_residues
        else:
            self.modified_residues = PDB(pdb_contents).modified_residues

        self._STACK = []                        # This is used to create a simple FSA for the parsing
        self.current_residue = None
        self.residues = []
        self.reading_unobserved_property = False
        self.uniparc_ids = set()

        assert(0 <= acceptable_sequence_percentage_match <= 100)
        assert(xml_contents.find("encoding='UTF-8'") != -1)


    def _create_inverse_maps(self):
        '''todo: This should get called automatically after atom_to_seqres_sequence_maps is constructed and this code should be called by the relatrix.'''
        self.seqres_to_atom_sequence_maps = {}
        for chain_id, sequence_map in self.atom_to_seqres_sequence_maps.iteritems():
            s = SequenceMap()
            for k, v, substitution_match in sequence_map:
                s.add(v, k, substitution_match)
            self.seqres_to_atom_sequence_maps[chain_id] = s


    def get_pdb_chain_to_uniparc_id_map(self):
        if self.pdb_chain_to_uniparc_id_map:
            return self.pdb_chain_to_uniparc_id_map
        else:
            self.pdb_chain_to_uniparc_id_map = {}

            for c, mp in self.atom_to_uniparc_sequence_maps.iteritems():
                self.pdb_chain_to_uniparc_id_map[c] = self.pdb_chain_to_uniparc_id_map.get(c, set())
                for _, v, _ in mp:
                    self.pdb_chain_to_uniparc_id_map[c].add(v[0])

            for c, mp in self.seqres_to_uniparc_sequence_maps.iteritems():
                self.pdb_chain_to_uniparc_id_map[c] = self.pdb_chain_to_uniparc_id_map.get(c, set())
                for _, v, _ in mp:
                    self.pdb_chain_to_uniparc_id_map[c].add(v[0])

            for c, s in self.pdb_chain_to_uniparc_id_map.iteritems():
                self.pdb_chain_to_uniparc_id_map[c] = sorted(s)

            #import pprint
            #colortext.pcyan('DDDDDDDDDDDDDDD' * 10)
            #pprint.pprint(self.pdb_chain_to_uniparc_id_map)

            return self.pdb_chain_to_uniparc_id_map


    def get_uniparc_sequences(self):
        if self.uniparc_sequences:
            return self.uniparc_sequences
        else:
            self.uniparc_sequences = {}
            self.uniparc_objects = {}
            for UniParcID in self.uniparc_ids:
                entry = UniParcEntry(UniParcID, cache_dir = self.cache_dir)
                self.uniparc_sequences[entry.UniParcID] = Sequence.from_sequence(entry.UniParcID, entry.sequence)
                self.uniparc_objects[entry.UniParcID] = entry

            #import pprint
            #colortext.pcyan('EEEEEEEEEEEEEEE' * 10)
            #pprint.pprint(self.uniparc_sequences)

            return self.uniparc_sequences


    @staticmethod
    def retrieve(pdb_id, cache_dir = None, acceptable_sequence_percentage_match = 70.0, require_uniprot_residue_mapping = True, bio_cache = None, restrict_match_percentage_errors_to_these_uniparc_ids = None):
        '''Creates a PDBML object by using a cached copy of the files if they exists or by retrieving the files from the RCSB.
           bio_cache should be a klab.bio.cache.py::BioCache object and is used to avoid reading/downloading cached files repeatedly.
        '''

        pdb_contents = None
        xml_contents = None
        pdb_id = pdb_id.upper()

        l_pdb_id = pdb_id.lower()

        if len(pdb_id) != 4 or not pdb_id.isalnum():
            raise Exception("Bad PDB identifier '%s'." % pdb_id)

        if bio_cache:
            pdb_contents = bio_cache.get_pdb_contents(pdb_id)
            xml_contents = bio_cache.get_sifts_xml_contents(pdb_id)

        if cache_dir:
            if not pdb_contents:
                # Check to see whether we have a cached copy of the PDB file
                filename = os.path.join(cache_dir, "%s.pdb" % pdb_id)
                if os.path.exists(filename):
                    pdb_contents = read_file(filename)

            if not xml_contents:
                # Check to see whether we have a cached copy of the XML file
                filename = os.path.join(cache_dir, "%s.sifts.xml.gz" % l_pdb_id)
                if os.path.exists(filename):
                    print(filename)
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
                raise MissingSIFTSRecord('The file "%s.sifts.xml.gz" could not be found on the EBI FTP server.' % l_pdb_id)

        xml_contents = xml_contents

        # Return the object
        handler = SIFTS(xml_contents, pdb_contents, acceptable_sequence_percentage_match = acceptable_sequence_percentage_match, cache_dir = cache_dir, require_uniprot_residue_mapping = require_uniprot_residue_mapping, bio_cache = bio_cache, pdb_id = pdb_id, restrict_match_percentage_errors_to_these_uniparc_ids = restrict_match_percentage_errors_to_these_uniparc_ids)
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


    def start_document(self):
        '''"The SAX parser will invoke this method only once, before any other methods in this interface or in DTDHandler (except for setDocumentLocator())."'''
        pass

    a='''
<entity type="protein" entityId="A">
    <segment segId="1aqt_A_1_2" start="1" end="2">
      <listResidue>

<listMapRegion>
        <mapRegion start="3" end="138">
          <db dbSource="PDB" dbCoordSys="PDBresnum" dbAccessionId="1aqt" dbChainId="A" start="3" end="138"/>
        </mapRegion>'''



    def add_region_mapping(self, attributes):
        chain_id = (self._get_current_PDBe_chain())
        mapRegion_attributes = self._STACK[3][1]
        segment_range = (int(mapRegion_attributes['start']), int(mapRegion_attributes['end']))
        dbSource = attributes['dbSource']
        dbAccessionId = attributes['dbAccessionId']
        self.region_mapping[chain_id] = self.region_mapping.get(chain_id, {})
        self.region_mapping[chain_id][dbSource] = self.region_mapping[chain_id].get(dbSource, {})
        self.region_mapping[chain_id][dbSource][dbAccessionId] = self.region_mapping[chain_id][dbSource].get(dbAccessionId, [])
        self.region_mapping[chain_id][dbSource][dbAccessionId].append(segment_range)

        # Note: I do not currently store the coordinate system type on a range level since I am assuming that each mapping uses one coordinate system
        if attributes.get('dbCoordSys'):
            self.region_map_coordinate_systems[dbSource] = self.region_map_coordinate_systems.get(dbSource, set())
            self.region_map_coordinate_systems[dbSource].add(attributes['dbCoordSys'])

        #import pprint
        #colortext.pcyan('FFFFFFFFFFFFFFFFF' * 10)
        #pprint.pprint(self.region_mapping)
        #pprint.pprint(self.region_map_coordinate_systems)


    def start_element(self, name, attributes):
        self.tag_data = ''

        # Residue details and mappings

        if name == 'crossRefDb':
            self.start_crossRefDb(attributes)

        elif name == 'residueDetail':
            self.stack_push(4, None)
            self.start_residueDetail(attributes)

        elif name == 'residue':
            self.stack_push(3, None)
            assert(attributes.get('dbSource'))
            assert(attributes.get('dbCoordSys'))
            assert(attributes.get('dbResNum'))
            assert(attributes.get('dbResName'))
            assert(attributes['dbSource'] == 'PDBe')
            assert(attributes['dbCoordSys'] == 'PDBe')
            self.current_residue = SIFTSResidue(self._get_current_PDBe_chain(), attributes['dbResNum'], attributes['dbResName'])

        elif name == 'listResidue':
            self.stack_push(2, None)

        # Region mappings

        elif name == 'db':
            if len(self._STACK) == 4 and self._STACK[3][1].get('nodeType') == 'mapRegion':
                assert(attributes.get('dbSource'))
                assert(attributes.get('dbAccessionId'))
                self.add_region_mapping(attributes)

        elif name == 'mapRegion':
            assert(attributes.get('start'))
            assert(attributes.get('end'))
            self.stack_push(3, dict(start=attributes['start'], end=attributes['end'], nodeType = 'mapRegion'))

        elif name == 'listMapRegion':
            self.stack_push(2, None)

        # Entities and segments

        elif name == 'segment':
            assert(attributes.get('segId'))
            assert(attributes.get('start'))
            assert(attributes.get('end'))
            self.stack_push(1, dict(segId=attributes['segId'], start=attributes['start'], end=attributes['end']))

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
            pdb_id = attributes.get('dbAccessionId').upper()
            if self.pdb_id:
                assert(self.pdb_id.upper() == pdb_id)
            self.pdb_id = pdb_id
        else:
            raise Exception('Could not verify the PDB ID from the <entry> tag.')


    def start_residueDetail(self, attributes):
        self.check_stack(5)
        self.reading_unobserved_property = False
        dbSource = attributes.get('dbSource')
        assert(dbSource)
        if dbSource == 'PDBe':
            residue_detail_property = attributes.get('property')
            if residue_detail_property and residue_detail_property == 'Annotation':
                self.reading_unobserved_property = True


    def start_crossRefDb(self, attributes):
        self.check_stack(4)
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
                #assert(dbChainId == self._STACK[0][1]) # this is not always true e.g. 1lmb has entityId="C" but dbChainId="3"
                if not dbChainId == self._STACK[0][1]: # use the dbChainId chain ID since that is what is used in the logic later on. Note: this may introduce bugs if the dbChainIds differ amongst themselves
                    self._STACK[0] = (0, dbChainId)

                assert(dbCoordSys and dbAccessionId and dbResNum and dbResName and dbChainId )
                current_residue.add_pdb_residue(dbChainId, dbResNum, dbResName)

            elif dbSource == 'UniProt':
                assert(dbCoordSys and dbAccessionId and dbResNum and dbResName)
                assert(dbCoordSys == "UniProt")
                assert(dbCoordSys and dbAccessionId and dbResNum and dbResName)

                # Override bad mappings
                try:
                    residue_range_maps = overridden_cases[self.pdb_id.upper()]['residue_mapping_change'][u'UniProt']
                    for rrm in residue_range_maps:
                        if (rrm[0] == dbAccessionId) and (rrm[1] <= int(dbResNum) <= rrm[2]):
                            dbAccessionId = rrm[3]
                except KeyError, e:
                    pass #print(str(e))

                current_residue.add_uniprot_residue(dbAccessionId, dbResNum, dbResName)


    def _get_current_PDBe_chain(self):
        return self._STACK[0][1]


    def _get_current_segment_range(self):
        return (self._STACK[1][1]['start'], self._STACK[1][1]['end'])


    def end_element(self, name):
        tag_content = self.tag_data

        # Residue details and mappings

        if name == 'residueDetail':
            self.stack_pop(4)
            if self.reading_unobserved_property and (tag_content == 'Not_Observed'):
                self.current_residue.WasNotObserved = True
            self.reading_unobserved_property = False

        elif name == 'residue':
            self.stack_pop(3)
            current_residue = self.current_residue
            #assert(self._get_current_PDBe_chain() == current_residue.PDBChainID) # this is not always true e.g. 1lmb has entityId="C" but dbChainId="3"
            self.residues.append(current_residue)
            self.current_residue = None

        elif name == 'listResidue':
            self.stack_pop(2)

        # Region mappings

        elif name == 'mapRegion':
            self.stack_pop(3)

        elif name == 'listMapRegion':
            self.stack_pop(2)

        # Entities and segments

        elif name == 'segment':
            self.stack_pop(1)

        elif name == 'entity':
            self.stack_pop(0)


    def _apply_patches(self):
        pdb_id = self.pdb_id.upper()
        if pdb_id in overridden_cases:
            overrides = overridden_cases[pdb_id]
            if 'region_mapping' in overrides:
                #print('OVERRIDE' * 30)
                #import pprint
                #pprint.pprint(self.region_mapping)
                region_mapping = overrides['region_mapping']
                for chain_id, mapping in sorted(region_mapping.iteritems()):
                    for mapping_type, mapping in sorted(mapping.iteritems()):
                        self.region_mapping[chain_id][mapping_type] = mapping
                #pprint.pprint(self.region_mapping)


    def end_document(self):
        assert(self.counters['entry'] == 1)

        residue_count = 0
        residues_matched = {}
        residues_encountered = {}
        atom_to_uniparc_residue_map = {}
        atom_to_seqres_residue_map = {}
        seqres_to_uniparc_residue_map = {}

        UniProtACs = set()
        for r in self.residues:
            if r.UniProtAC:
                UniProtACs.add(r.UniProtAC)

        #print(UniProtACs)

        if self.pdb_id:
            self._apply_patches()

        ACC_to_UPARC_mapping = uniprot_map('ACC', 'UPARC', list(UniProtACs), cache_dir = self.cache_dir)
        assert(sorted(ACC_to_UPARC_mapping.keys()) == sorted(list(UniProtACs)))
        for k, v in ACC_to_UPARC_mapping.iteritems():
            assert(len(v) == 1)
            ACC_to_UPARC_mapping[k] = v[0]

        map_chains = set()
        residue_count_per_chain = {}
        for r in self.residues:
            if not(r.PDBResidueID.isalnum() and int(r.PDBResidueID.isalnum()) < 0):
                # These are not valid PDB residue IDs - the SIFTS XML convention sometimes assigns negative residue IDs to unobserved residues before the first ATOM record
                # (only if the first residue ID is 1?)
                pass

            #print(r)
            #print('')
            # Get the residue ID (including chain and insertion code)
            full_pdb_residue_ID = r.get_pdb_residue_id()

            # Make sure we only have at most one match per PDB residue
            if full_pdb_residue_ID in residues_encountered:
                if r.equal_up_to_modification(residues_encountered[full_pdb_residue_ID], self.modified_residues):
                    # The residues differ but this is likely to be a crystallization artifact rather than a bug in SIFTS
                    # and we may still be able to treat them the same.
                    # e.g. in 2FI5, residue E 115 (PDB ATOM numbering), conformation A has an IAS residue whereas conformation
                    #      B has an ASP residue. Similarly for 2FTM, residue A 115.
                    colortext.pcyan('{0} was encountered multiple times in the SIFTS file for {1} but the cases resolve ({2} ~= {3}).'.format(full_pdb_residue_ID, self.pdb_id, residues_encountered[full_pdb_residue_ID].PDBResidue3AA, r.PDBResidue3AA))
                    continue
                else:
                    raise Exception('{0} was encountered multiple times in the SIFTS file for {1}.'.format(full_pdb_residue_ID, self.pdb_id))
            residues_encountered[full_pdb_residue_ID] = r

            # Store the PDB->UniProt mapping
            UniParcID, UniProtAC = None, None
            if r.has_pdb_to_uniprot_mapping():
                UniProtAC = r.UniProtAC
                UniParcID = ACC_to_UPARC_mapping[UniProtAC]
                self.uniparc_ids.add(UniParcID)

            PDBChainID = r.PDBChainID
            map_chains.add(PDBChainID)
            residues_matched[PDBChainID] = residues_matched.get(PDBChainID, 0)
            residue_count_per_chain[PDBChainID] = residue_count_per_chain.get(PDBChainID, 0)

            if not r.WasNotObserved:
                # Do not add ATOM mappings when the ATOM data does not exist
                if r.has_pdb_to_uniprot_mapping():
                    atom_to_uniparc_residue_map[PDBChainID] = atom_to_uniparc_residue_map.get(PDBChainID, {})
                    atom_to_uniparc_residue_map[PDBChainID][full_pdb_residue_ID] = (UniParcID, r.UniProtResidueIndex)

                atom_to_seqres_residue_map[PDBChainID] = atom_to_seqres_residue_map.get(PDBChainID, {})
                atom_to_seqres_residue_map[PDBChainID][full_pdb_residue_ID] = r.PDBeResidueID

            if r.has_pdb_to_uniprot_mapping():
                seqres_to_uniparc_residue_map[PDBChainID] = seqres_to_uniparc_residue_map.get(PDBChainID, {})
                seqres_to_uniparc_residue_map[PDBChainID][r.PDBeResidueID] = (UniParcID, r.UniProtResidueIndex)

            # Count the number of exact sequence matches
            PDBResidue3AA = r.PDBResidue3AA
            pdb_residue_type = residue_type_3to1_map.get(PDBResidue3AA) or self.modified_residues.get(PDBResidue3AA) or protonated_residue_type_3to1_map.get(PDBResidue3AA) or non_canonical_amino_acids.get(PDBResidue3AA)

            residues_was_matched = False
            if r.has_pdb_to_uniprot_mapping():
                if pdb_residue_type == r.UniProtResidue1AA:
                    residues_matched[PDBChainID] += 1
                    residues_was_matched = True

            if (residues_was_matched) or not(self.restrict_match_percentage_errors_to_these_uniparc_ids) or (UniParcID and (UniParcID in self.restrict_match_percentage_errors_to_these_uniparc_ids)):
                # Count all successes. Else, if we are not restricting matches, count this residue. Else, only count this residue if its associated UniParc ID is in the set of considered UniParc IDs.
                residue_count_per_chain[PDBChainID] += 1
                residue_count += 1

        import pprint
        #pprint.pprint(seqres_to_uniparc_residue_map)
        #sys.exit(0)

        # Create the SequenceMaps
        uniparc_sequences = self.get_uniparc_sequences()
        percentage_residues_matched_per_chain = {}
        for c in map_chains:
            percentage_residues_matched_per_chain[c] = 0
            if residue_count_per_chain[c] > 0:
                assert(0 <= residues_matched[c] <= residue_count_per_chain[c])
                percentage_residues_matched_per_chain[c] = float(residues_matched[c])*100.0/float(residue_count_per_chain[c])
            if residues_matched[c] > 0:
                # 1IR3 has chains A,
                # Chain A has mappings from atom and seqres (PDBe) residues to UniParc as usual
                # Chain B (18 residues long) has mappings from atom to seqres residues but not to UniParc residues
                self.atom_to_uniparc_sequence_maps[c] = PDBUniParcSequenceMap.from_dict(atom_to_uniparc_residue_map[c])
                self.seqres_to_uniparc_sequence_maps[c] = PDBUniParcSequenceMap.from_dict(seqres_to_uniparc_residue_map[c])


                # In some cases, the SEQRES sequences are longer than the UniParc sequences e.g. 1AHW. In these cases, we
                # would consider the percentage residues matched based on the percentage of the UniParc sequence that was
                # matched rather than the length of the SEQRES sequence.
                uniparc_sequence_counts = {}
                for pc_id, up_tpl, sub_score in self.seqres_to_uniparc_sequence_maps[c]:
                    uniparc_sequence_counts[up_tpl[0]] = uniparc_sequence_counts.get(up_tpl[0], 0)
                    uniparc_sequence_counts[up_tpl[0]] += 1
                if len(uniparc_sequence_counts) == 1:
                    matched_uniparc_id = uniparc_sequence_counts.keys()[0]
                    num_matched_uniparc_id_residues = uniparc_sequence_counts[matched_uniparc_id]
                    percentage_residues_matched_per_chain[c] = max(percentage_residues_matched_per_chain[c], float(num_matched_uniparc_id_residues)*100.0/float(len(uniparc_sequences[matched_uniparc_id])))

            self.atom_to_seqres_sequence_maps[c] = SequenceMap.from_dict(atom_to_seqres_residue_map[c])

        #print('percentage_residues_matched_per_chain')
        #colortext.pcyan(pprint.pformat(percentage_residues_matched_per_chain))

        # Check the per-chain match percentage
        uniparc_sequences = self.get_uniparc_sequences()
        pprint.pprint(uniparc_sequences)
        pprint.pprint(PDB(self.pdb_contents).seqres_sequences)
        pprint.pprint(percentage_residues_matched_per_chain)
        pprint.pprint(residue_count_per_chain)
        print('***')


        for c in map_chains:
            if residue_count_per_chain[c] > 0:
                print(residue_count_per_chain[c], percentage_residues_matched_per_chain[c])
                if percentage_residues_matched_per_chain[c] < self.acceptable_sequence_percentage_match:
                    if self.pdb_id and self.pdb_id in BadSIFTSMappingCases:
                        raise BadSIFTSMapping('The PDB file %s has a known bad SIFTS mapping at the time of writing.' % self.pdb_id)
                    elif self.pdb_id and self.pdb_id in CircularPermutantSIFTSMappingCases:
                        raise BadSIFTSMapping('The PDB file {0} is a circular permutant of {1} so should be discounted at present.'.format(self.pdb_id, CircularPermutantSIFTSMappingCases[self.pdb_id]))
                    else:
                        raise PotentialBadSIFTSMapping('Expected {0:.2f}% sequence match on matched residues but the SIFTS results only gave us {1:.2f}% on chain {2}. Investigate this case and if it is problematic e.g. a chimeric sequence or a circular permutant like 3DA7 then add it to BadSIFTSMappingCases.'.format(self.acceptable_sequence_percentage_match, percentage_residues_matched_per_chain[c], c))


        # Check the total match percentage
        total_residues_matched = sum([residues_matched[c] for c in residues_matched.keys()])
        if total_residues_matched == 0:
            if self.pdb_id and self.pdb_id in NoSIFTSPDBUniParcMappingCases:
                if self.require_uniprot_residue_mapping:
                    raise NoSIFTSPDBUniParcMapping('The PDB file %s has a bad or missing SIFTS mapping at the time of writing.' % self.pdb_id)
                else:
                    colortext.error('Warning: The PDB file %s has a a bad or missing SIFTS mapping at the time of writing so there is no PDB -> UniProt residue mapping.' % self.pdb_id)
            else:
                if self.require_uniprot_residue_mapping:
                    raise Exception('No residue information matching PDB residues to UniProt residues was found.')
                else:
                    colortext.error('Warning: No residue information matching PDB residues to UniProt residues was found.')
        else:
            import pprint
            pprint.pprint(percentage_residues_matched_per_chain)
            pprint.pprint(residue_count_per_chain)
            print(total_residues_matched, residue_count)
            percentage_matched = 0
            if residue_count == 0:
                colortext.warning('Potential error: the total residue count is zero.')
            else:
                percentage_matched = float(total_residues_matched)*100.0/float(residue_count)
            if percentage_matched < self.acceptable_sequence_percentage_match:
                if self.pdb_id and self.pdb_id in BadSIFTSMappingCases:
                    raise BadSIFTSMapping('The PDB file %s has a known bad SIFTS mapping at the time of writing.' % self.pdb_id)
                elif self.pdb_id and self.pdb_id in CircularPermutantSIFTSMappingCases:
                    raise BadSIFTSMapping('The PDB file {0} is a circular permutant of {1} so should be discounted at present.'.format(self.pdb_id, CircularPermutantSIFTSMappingCases[self.pdb_id]))
                else:
                    raise PotentialBadSIFTSMapping('Expected %.2f%% sequence match on matched residues but the SIFTS results only gave us %.2f%%. Investigate this case and if it is problematic e.g. a chimeric sequence or a circular permutant like 3DA7 then add it to BadSIFTSMappingCases.' % (self.acceptable_sequence_percentage_match, percentage_matched))

        # Merge the ranges for the region mappings i.e. so [1-3],[3-86] becomes [1-86]
        region_mapping = self.region_mapping
        for chain_id, chain_details in region_mapping.iteritems():
            for dbSource, source_details in chain_details.iteritems():
                for dbAccessionId, range_list in source_details.iteritems():
                    source_details[dbAccessionId] = merge_range_pairs(range_list)

        # Check to see if the expected numbering schemes hold
        for k, v in expected_residue_numbering_schemes.iteritems():
            if self.region_map_coordinate_systems.get(k):
                assert(self.region_map_coordinate_systems[k] == set([v]))

        pfam_scop_mapping = {}
        scop_pfam_mapping = {}
        for chain_id, chain_details in region_mapping.iteritems():
            if chain_details.get('Pfam') and chain_details.get('SCOP'):
                for pfamAccessionId, pfam_range_lists in chain_details['Pfam'].iteritems():
                    pfam_residues = parse_range(','.join(['%d-%d' % (r[0], r[1]) for r in pfam_range_lists]))
                    for scopAccessionId, scop_range_lists in chain_details['SCOP'].iteritems():
                        scop_residues = parse_range(','.join(['%d-%d' % (r[0], r[1]) for r in scop_range_lists]))
                        num_same_residues = len(set(pfam_residues).intersection(set(scop_residues)))
                        if num_same_residues > 10:
                            Pfam_match_quality = float(num_same_residues) / float(len(pfam_residues))
                            SCOP_match_quality = float(num_same_residues) / float(len(scop_residues))
                            if (Pfam_match_quality >= self.domain_overlap_cutoff) or (SCOP_match_quality >= self.domain_overlap_cutoff):
                                pfam_scop_mapping[pfamAccessionId] = pfam_scop_mapping.get(pfamAccessionId, DomainMatch(pfamAccessionId, 'Pfam'))
                                pfam_scop_mapping[pfamAccessionId].add(scopAccessionId, 'SCOP', SCOP_match_quality)
                                scop_pfam_mapping[scopAccessionId] = scop_pfam_mapping.get(scopAccessionId, DomainMatch(scopAccessionId, 'SCOP'))
                                scop_pfam_mapping[scopAccessionId].add(pfamAccessionId, 'Pfam', Pfam_match_quality)

        self.pfam_scop_mapping = pfam_scop_mapping
        self.scop_pfam_mapping = scop_pfam_mapping

        self._validate()


    def _validate(self):
        '''Tests that the maps agree through composition.'''

        # I used to use the assertion "self.atom_to_uniparc_sequence_maps.keys() == self.atom_to_seqres_sequence_maps.keys() == self.seqres_to_uniparc_sequence_maps.keys()"
        # but that failed for 2IMM where "self.atom_to_uniparc_sequence_maps.keys() == self.seqres_to_uniparc_sequence_maps.keys() == []" but THAT fails for 1IR3 so I removed
        # the assertions entirely.
        for c, m in self.atom_to_seqres_sequence_maps.iteritems():
            if self.seqres_to_uniparc_sequence_maps.keys():
                atom_uniparc_keys = set(self.atom_to_uniparc_sequence_maps.get(c, {}).keys())
                atom_seqres_keys = set(self.atom_to_seqres_sequence_maps.get(c, {}).keys())
                assert(atom_uniparc_keys.intersection(atom_seqres_keys) == atom_uniparc_keys)
                for k, v in m.map.iteritems():
                    uparc_id_1, uparc_id_2 = None, None
                    try:
                        uparc_id_1 = self.seqres_to_uniparc_sequence_maps[c].map[v]
                        uparc_id_2 = self.atom_to_uniparc_sequence_maps[c].map[k]
                    except:
                        continue
                    assert(uparc_id_1 == uparc_id_2)


    def characters(self, chrs):
        self.tag_data += chrs


    startDocument = start_document
    endDocument = end_document
    startElement = start_element
    endElement = end_element
