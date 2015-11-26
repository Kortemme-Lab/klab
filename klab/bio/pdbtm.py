#!/usr/bin/python
# encoding: utf-8
"""
pdbtm.py
Basic parsing for the PDBTM:Protein Data Bank of Transmembrane Proteins. This is currently only used to extract a list of PDB identifiers.

Created by Shane O'Connor 2014

"""

# We use xml.etree.ElementTree at present which runs slowly compared to xml.sax but the code is quicker to read/write.
import io
from lxml import etree
from klab.parsers.xml import fast_iter

import re
class record_iterator(object):
    '''This class is deprecated by PDBTM.get_xml.'''
    def __init__(self, xml_contents):
        self.records = re.findall('(<pdbtm\s*.*?</pdbtm>)', xml_contents, re.DOTALL)

    def get(self, pdb_id):
        for r in self.records:
            id = re.match(r'<pdbtm.*?ID="(.*?)".*>', r, re.DOTALL)
            assert(id)
            id = id.group(1)
            if id.upper() == pdb_id.upper():
                return r


class EarlyOut(Exception): pass

class PDBTM(object):

    PDBTM_entry_tag_type = '{http://pdbtm.enzim.hu}pdbtm'
    PDBTM_membrane_tag_type = '{http://pdbtm.enzim.hu}MEMBRANE'
    PDBTM_rawres_tag_type = '{http://pdbtm.enzim.hu}RAWRES'
    PDBTM_tmtype_tag_type = '{http://pdbtm.enzim.hu}TMTYPE'
    non_transmembrane_tmtypes = set(['Soluble', 'No_Protein', 'Nucleotide', 'Virus', 'Pilus', 'Ca_Globular', 'Tm_Part'])
    transmembrane_tmtypes = set(['Tm_Alpha', 'Tm_Beta', 'Tm_Coil', 'Tm_Ca'])

    def __init__(self, xml_contents, restrict_to_transmembrane_proteins = True):
        self.xml_contents = xml_contents.strip()

        # At some point, this tag crept into the PDBTM XML which the parser below cannot handle
        self.xml_contents = self.xml_contents.replace('''<?xml version="1.0"?>''', '')

        self.restrict_to_transmembrane_proteins = restrict_to_transmembrane_proteins


    @staticmethod
    def _get_tm_type(elem):
        for child in elem:
            if child.tag == PDBTM.PDBTM_rawres_tag_type:
                for gchild in child:
                    if gchild.tag == PDBTM.PDBTM_tmtype_tag_type:
                        return gchild.text.strip()
        return 'N/A'


    def _get_pdb_id(self, elem, **kwargs):
        '''If self.restrict_to_transmembrane_proteins is False then this adds all ids to self.ids. Otherwise, only transmembrane protein ids are added.'''
        id = elem.attrib['ID']
        if self.restrict_to_transmembrane_proteins:
            tmp = elem.attrib['TMP']
            assert(tmp == 'no' or tmp == 'yes' or tmp == 'not')
            if tmp == 'yes':
                self.ids[id] = PDBTM._get_tm_type(elem)
        else:
            self.ids[id] = self.ids.get(id, 0) + 1


    def get_pdb_ids(self):
        '''Returns the sorted list of PDB IDs from the records.'''
        return sorted(self.get_pdb_id_map().keys())


    def get_pdb_id_map(self):
        ''' Returns a dict mapping PDB IDs to:
                i) their number of associated records, if self.restrict_to_transmembrane_proteins is False;
               ii) the type of transmembrane protein if self.restrict_to_transmembrane_proteins is True.
            At the time of writing this (2014-12-03), there were 106,094 PDB IDs and 106,090 unique IDs.
            These records had duplicate entries: '2amk', '2ar1', '3b4r', '4k5y'.'''
        self.ids = {}
        context = etree.iterparse(io.BytesIO(self.xml_contents), events=('end',), tag=self.PDBTM_entry_tag_type)
        fast_iter(context, self._get_pdb_id)
        return self.ids


    def _get_membrane_xml(self, elem, pdb_id):
        assert(elem.tag == self.PDBTM_entry_tag_type)
        id = elem.attrib['ID'] or ''
        if id.upper() == pdb_id:
            for child in elem:
                if child.tag == self.PDBTM_membrane_tag_type:
                    self.tmp_string = etree.tostring(child)
            raise EarlyOut()


    def get_membrane_xml(self, pdb_id):
        ''' Returns the <MEMBRANE> tag XML for pdb_id if the tag exists.'''
        self.tmp_string = None
        context = etree.iterparse(io.BytesIO(self.xml_contents), events=('end',), tag=self.PDBTM_entry_tag_type)
        try:
            fast_iter(context, self._get_membrane_xml, pdb_id = pdb_id.upper())
        except EarlyOut: pass
        return self.tmp_string


    def _get_xml(self, elem, pdb_id):
        assert(elem.tag == self.PDBTM_entry_tag_type)
        id = elem.attrib['ID'] or ''
        if id.upper() == pdb_id:
            self.tmp_string = etree.tostring(elem)
            raise EarlyOut()

    def get_xml(self, pdb_id):
        ''' Returns the XML for pdb_id if the tag exists.'''
        self.tmp_string = None
        context = etree.iterparse(io.BytesIO(self.xml_contents), events=('end',), tag=self.PDBTM_entry_tag_type)
        try:
            fast_iter(context, self._get_xml, pdb_id = pdb_id.upper())
        except EarlyOut: pass
        return self.tmp_string


