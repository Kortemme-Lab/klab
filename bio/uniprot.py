#!/usr/bin/python
# encoding: utf-8
"""
uniprot.py
For functions relating to getting data from UniProt.

Created by Shane O'Connor 2013
"""

import sys
import os
import string
import urllib,urllib2
import simplejson
from xml.dom.minidom import parse, parseString

if __name__ == '__main__':
    sys.path.insert(0, "../..")
from tools.comms.http import get as http_get
from tools import colortext
from tools.hash import CRC64
from tools.fs.io import read_file, write_file

def uniprot_map(from_scheme, to_scheme, list_of_from_ids, cache_dir = None):
    '''Maps from one ID scheme to another using the UniProt service.
        list_of_ids should be a list of strings.
        This function was adapted from http://www.uniprot.org/faq/28#id_mapping_examples which also gives examples of
        valid values for from_scheme and to_scheme.
        Note that some conversions are not directly possible e.g. PDB_ID (PDB) to UPARC (UniParc). They need to go through
        an intermediary format like ACC (UniProtKB AC) or ID (UniProtKB ID).
        This function returns a dict mapping the IDs in from_scheme to a list of sorted IDs in to_scheme.
    '''

    full_mapping = {}
    cached_mapping_file = None
    if cache_dir:
        cached_mapping_file = os.path.join(cache_dir, '%s.%s' % (from_scheme, to_scheme))
        if os.path.exists(cached_mapping_file):
            full_mapping = simplejson.loads(read_file(cached_mapping_file))

    list_of_from_ids = set(list_of_from_ids)

    requested_mapping = {}
    remaining_ids = []
    for id in list_of_from_ids:
        if full_mapping.get(id):
            requested_mapping[id] = full_mapping[id]
        else:
            remaining_ids.append(id)
    assert(set(remaining_ids + requested_mapping.keys()) == set(list_of_from_ids))

    if remaining_ids:
        url = 'http://www.uniprot.org/mapping/'
        params = {
            'from'      : from_scheme,
            'to'        : to_scheme,
            'format'    : 'tab',
            'query'     : ' '.join(sorted(list(list_of_from_ids))),
        }
        data = urllib.urlencode(params)
        request = urllib2.Request(url, data)
        contact = "" # Please set your email address here to help us debug in case of problems.
        request.add_header('User-Agent', 'Python %s' % contact)
        response = urllib2.urlopen(request)
        page = response.read(200000)
        lines = page.split("\n")
        assert(lines[-1] == '')
        assert(lines[0].split("\t") == ['From', 'To'])
        for line in lines[1:-1]:
            tokens = line.split("\t")
            assert(len(tokens) == 2)
            assert(tokens[0] in list_of_from_ids)
            full_mapping[tokens[0]] = full_mapping.get(tokens[0], [])
            full_mapping[tokens[0]].append(tokens[1])
            requested_mapping[tokens[0]] = requested_mapping.get(tokens[0], [])
            requested_mapping[tokens[0]].append(tokens[1])

    # Sort the IDs
    for k, v in requested_mapping.iteritems():
        assert(len(v) == len(set(v)))
        requested_mapping[k] = sorted(v)
    for k, v in full_mapping.iteritems():
        assert(len(v) == len(set(v)))
        full_mapping[k] = sorted(v)

    if cached_mapping_file:
        write_file(cached_mapping_file, simplejson.dumps(full_mapping))
    return requested_mapping

def pdb_to_uniparc(pdb_ids, silent = True):
    '''Returns a mapping {PDB ID -> List(UniParcEntry)}'''

    # Map PDB IDs to UniProtKB AC
    if not silent:
        colortext.write("Retrieving PDB to UniProtKB AC mapping: ", 'cyan')
    pdb_ac_mapping = uniprot_map('PDB_ID', 'ACC', pdb_ids)
    if not silent:
        colortext.write("done\n", 'green')

    # Get a list of AC_IDs
    if not silent:
        colortext.write("Retrieving UniProtKB AC to UniProtKB ID mapping: ", 'cyan')
    AC_IDs = set()
    for k, v in pdb_ac_mapping.iteritems():
        AC_IDs = AC_IDs.union(set(v))
    AC_IDs = list(AC_IDs)
    if not silent:
        colortext.write("done\n", 'green')

    # Map UniProtKB ACs to UniParc IDs
    if not silent:
        colortext.write("Retrieving UniProtKB AC to UniParc ID mapping: ", 'cyan')
    ac_uniparc_mapping = uniprot_map('ACC', 'UPARC', AC_IDs)
    for k, v in ac_uniparc_mapping.iteritems():
        assert(len(v) == 1)
        ac_uniparc_mapping[k] = v[0]
    if not silent:
        colortext.write("done\n", 'green')

    # Map UniProtKB ACs to UniProtKB IDs
    ac_id_mapping = uniprot_map('ACC', 'ID', AC_IDs)
    for k, v in ac_id_mapping.iteritems():
        assert(len(v) == 1)
        ac_id_mapping[k] = v[0]

    # Create mapping from PDB IDs to UniParcEntry objects
    m = {}
    if not silent:
        colortext.message("\nRetrieving FASTA sequences for the %d PDB IDs." % len(pdb_ids))
    for pdb_id, ACs in pdb_ac_mapping.iteritems():
        if not silent:
            colortext.write("%s: " % pdb_id, "orange")
        m[pdb_id] = []
        for AC in ACs:
            entry = UniParcEntry(ac_uniparc_mapping[AC], [AC], [ac_id_mapping[AC]])
            m[pdb_id].append(entry.to_dict())
            if not silent:
                colortext.write(".", "green")
        if not silent:
            print("")

    return m

class UniProtACEntry(object):
    def __init__(self, UniProtAC, XML = None, cache_dir = None):
        if cache_dir and not(os.path.exists(cache_dir)):
            raise Exception("The cache directory %s does not exist." % cache_dir)

        # Get XML
        if XML == None:
            protein_xml = None
            cached_filepath = None
            if cache_dir:
                cached_filepath = os.path.join(cache_dir, '%s.xml' % UniProtAC)
            if os.path.exists(cached_filepath):
                protein_xml = read_file(cached_filepath)
            else:
                url = 'http://www.uniprot.org/uniprot/%s.xml' % UniProtAC
                protein_xml = http_get(url)
                if cached_filepath:
                    write_file(cached_filepath, protein_xml)
            self.XML = protein_xml
        else:
            self.XML = XML

        self.recommended_name = None
        self.submitted_names = []
        self.alternative_names = []

        self._dom = parseString(protein_xml)
        self._parse_sequence_tag()
        self._parse_protein_tag()

    def _parse_sequence_tag(self):
        '''Parses the sequence and atomic mass.'''
        main_tags = self._dom.getElementsByTagName("uniprot")
        assert(len(main_tags) == 1)
        entry_tags = main_tags[0].getElementsByTagName("entry")
        assert(len(entry_tags) == 1)
        entry_tag = entry_tags[0]
        # only get sequence tags that are direct children of the entry tag (sequence tags can also be children of entry.comment.conflict)
        sequence_tags = [child for child in entry_tag.childNodes if child.nodeType == child.ELEMENT_NODE and child.tagName == 'sequence']
        assert(len(sequence_tags) == 1)
        sequence_tag = sequence_tags[0]

        # atomic mass, sequence, CRC64 digest
        self.atomic_mass = float(sequence_tag.getAttribute("mass"))
        self.sequence = "".join(sequence_tag.firstChild.nodeValue.strip().split("\n"))
        self.CRC64Digest = sequence_tag.getAttribute("checksum")

    def _parse_protein_tag(self):
        '''Parses the protein tag to get the names and EC numbers.'''

        protein_nodes = self._dom.getElementsByTagName('protein')
        assert(len(protein_nodes) == 1)
        self.protein_node = protein_nodes[0]

        self._get_recommended_name()
        self._get_submitted_names()
        self._get_recommended_name()
        self._get_alternative_names()

    def get_names(self):
        if self.recommended_name:
            return [self.recommended_name] + self.alternative_names + self.submitted_names
        else:
            return self.alternative_names + self.submitted_names

    @staticmethod
    def parse_names(tags):
        names = []
        for tag in tags:
            fullNames = tag.getElementsByTagName('fullName')
            assert(len(fullNames) == 1)
            fullName = fullNames[0].firstChild.nodeValue

            EC_numbers = []
            EC_number_tags = tag.getElementsByTagName('ecNumber')
            for EC_number_tag in EC_number_tags:
                EC_numbers.append(EC_number_tag.firstChild.nodeValue)

            short_names = []
            short_name_tags = tag.getElementsByTagName('shortName')
            for short_name_tag in short_name_tags:
                short_names.append(short_name_tag.firstChild.nodeValue)

            names.append({'Name' : fullName, 'EC numbers' : EC_numbers, 'Short names' : EC_numbers})
        return names

    def _get_recommended_name(self):
        # only get recommendedName tags that are direct children of the protein tag (recommendedName tags can also be children of protein.component tags)
        recommended_names = [child for child in self.protein_node.childNodes if child.nodeType == child.ELEMENT_NODE and child.tagName == 'recommendedName']
        if recommended_names:
            assert(len(recommended_names) == 1)
            recommended_names = UniProtACEntry.parse_names(recommended_names)
            assert(len(recommended_names) == 1)
            self.recommended_name = recommended_names[0]

    def _get_submitted_names(self):
        submitted_names = self.protein_node.getElementsByTagName('submittedName')
        if submitted_names:
            for submitted_name in submitted_names:
                # According to the schema (http://www.uniprot.org/docs/uniprot.xsd), submitted names have no short names
                assert(len(submitted_name.getElementsByTagName('shortName')) == 0)
            self.submitted_names = UniProtACEntry.parse_names(submitted_names)

    def _get_alternative_names(self):
        alternative_names = self.protein_node.getElementsByTagName('alternativeName')
        if alternative_names:
             self.alternative_names = UniProtACEntry.parse_names(alternative_names)


class UniParcEntry(object):

    def __init__(self, UniParcID, UniProtACs = None, UniProtKBs = None, cache_dir = None):
        if cache_dir and not(os.path.exists(os.path.abspath(cache_dir))):
            raise Exception("The cache directory %s does not exist." % os.path.abspath(cache_dir))

        self.UniParcID = UniParcID
        self.cache_dir = cache_dir

        # Get AC mapping
        if not UniProtACs:
            mapping = uniprot_map('UPARC', 'ACC', [UniParcID], cache_dir = cache_dir)[UniParcID]
            self.UniProtACs = mapping
        else:
            self.UniProtACs = UniProtACs

        # Get ID mapping
        if not UniProtKBs:
            mapping = uniprot_map('UPARC', 'ID', [UniParcID], cache_dir = cache_dir)[UniParcID]
            self.UniProtKBs = mapping
        else:
            self.UniProtKBs = UniProtKBs

        # Get FASTA
        cached_filepath = None
        if cache_dir:
            cached_filepath = os.path.join(cache_dir, '%s.fasta' % UniParcID)
        if os.path.exists(cached_filepath):
            fasta = read_file(cached_filepath)
        else:
            url = 'http://www.uniprot.org/uniparc/%s.fasta' % UniParcID
            fasta = http_get(url)
            if cached_filepath:
                write_file(cached_filepath, fasta)

        # Get sequence
        header = fasta.split("\n")[0].split()
        assert(len(header) == 2)
        assert(header[0] == ">%s" % UniParcID)
        assert(header[1].startswith("status="))
        sequence = "".join(map(string.strip, fasta.split("\n")[1:]))
        self.sequence = sequence

        # Get atomic mass (and sequence again)
        self.atomic_mass = None
        self.CRC64Digest = None
        recommended_names = set()
        for UniProtAC in self.UniProtACs:
            colortext.write("%s\n" % UniProtAC, "cyan")
            AC_entry = UniProtACEntry(UniProtAC, cache_dir = self.cache_dir)

            # Mass sanity check
            if self.atomic_mass != None:
                assert(self.atomic_mass == AC_entry.atomic_mass)
            self.atomic_mass = AC_entry.atomic_mass

            # Sequence sanity check
            assert(self.sequence == AC_entry.sequence)

            # CRC 64 sanity check
            if self.CRC64Digest != None:
                assert(self.CRC64Digest == AC_entry.CRC64Digest)
            self.CRC64Digest = AC_entry.CRC64Digest
            assert(CRC64.CRC64digest(self.sequence) == self.CRC64Digest)

            if AC_entry.recommended_name:
                recommended_names.add(AC_entry.recommended_name['Name'])
            #print(AC_entry.get_names())
        print('recommended_names', recommended_names)


    def to_dict(self):
        return {
            'UniParcID' : self.UniParcID,
            'UniProtAC' : self.UniProtAC,
            'UniProtKB' : self.UniProtKB,
            'sequence'  : self.sequence,
            'atomic_mass'  : self.atomic_mass,
            'CRC64Digest'  : self.CRC64Digest,
        }

    def __repr__(self):
        return simplejson.dumps(self.to_dict())
