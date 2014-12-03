#!/usr/bin/python
# encoding: utf-8
"""
pdbtm.py
Basic parsing for the PDBTM:Protein Data Bank of Transmembrane Proteins. This is currently only used to extract a list of PDB identifiers.

Created by Shane O'Connor 2014

"""

# We use xml.etree.ElementTree at present which runs slowly compared to xml.sax but the code is quicker to read/write.
import xml.etree.ElementTree as ET
import re
import time

class PDBTM_slow(object):

    def __init__(self, xml_contents):
        t1 = time.time()
        self.root = ET.fromstring(xml_contents)
        print('Parsing took %0.2fs' % (time.time() - t1))


    def get_pdb_ids(self):
        '''Returns the sorted list of PDB IDs from the records.'''
        return sorted(self.get_pdb_id_counts().keys())


    def get_pdb_id_counts(self):
        ''' Returns a dict mapping PDB IDs to their number of associated records.
            At the time of writing this (2014-12-03), there were 106,094 PDB IDs and 106,090 unique IDs.
            These records had duplicate entries: '2amk', '2ar1', '3b4r', '4k5y'.'''

        ids = {}
        for child in self.root:
            if child.tag == '{http://pdbtm.enzim.hu}pdbtm':
                id = child.attrib['ID']
                ids[id] = ids.get(id, 0) + 1
        return ids


class PDBTM_faster(object):

    def __init__(self, xml_contents):
        t1 = time.time()
        self.records = re.findall('(<pdbtm\s*.*?</pdbtm>)', xml_contents, re.DOTALL)
        self.root = ET.fromstring(xml_contents)
        print('Parsing took %0.2fs' % (time.time() - t1))


    def get_pdb_ids(self):
        '''Returns the sorted list of PDB IDs from the records.'''
        return sorted(self.get_pdb_id_counts().keys())


    def get_pdb_id_counts(self):
        ''' Returns a dict mapping PDB IDs to their number of associated records.
            At the time of writing this (2014-12-03), there were 106,094 PDB IDs and 106,090 unique IDs.
            These records had duplicate entries: '2amk', '2ar1', '3b4r', '4k5y'.'''

        ids = {}
        for r in self.records:
            root = ET.fromstring(r)
            id = root.attrib['ID']
            ids[id] = ids.get(id, 0) + 1

        return ids
