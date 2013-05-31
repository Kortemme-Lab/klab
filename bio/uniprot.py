#!/usr/bin/python
# encoding: utf-8
"""
uniprot.py
For functions relating to getting data from UniProt.

Created by Shane O'Connor 2013
"""

import string
import urllib,urllib2
import simplejson

if __name__ == '__main__':
    import sys
    sys.path.insert(0, "../..")
from tools.comms.http import get as http_get
from tools import colortext

def uniprot_map(from_scheme, to_scheme, list_of_from_ids):
    '''Maps from one ID scheme to another using the UniProt service.
        list_of_ids should be a list of strings.
        This function was adapted from http://www.uniprot.org/faq/28#id_mapping_examples which also gives examples of
        valid values for from_scheme and to_scheme.
        Note that some conversions are not directly possible e.g. PDB_ID (PDB) to UPARC (UniParc). They need to go through
        an intermediary format like ACC (UniProtKB AC) or ID (UniProtKB ID).
        This function returns a dict mapping the IDs in from_scheme to a list of sorted IDs in to_scheme.
    '''
    mapping = {}
    list_of_from_ids = set(list_of_from_ids)

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
        mapping[tokens[0]] = mapping.get(tokens[0], [])
        mapping[tokens[0]].append(tokens[1])

    # Sort the IDs
    for k, v in mapping.iteritems():
        assert(len(v) == len(set(v)))
        mapping[k] = sorted(v)

    return mapping

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
            entry = UniParcEntry(ac_uniparc_mapping[AC], AC, ac_id_mapping[AC])
            m[pdb_id].append(entry.to_dict())
            if not silent:
                colortext.write(".", "green")
        if not silent:
            print("")

    return m

class UniParcEntry(object):

    def __init__(self, UniParcID, UniProtAC, UniProtKB):
        self.UniParcID = UniParcID
        self.UniProtAC = UniProtAC
        self.UniProtKB = UniProtKB

        url = 'http://www.uniprot.org/uniparc/%s.fasta' % UniParcID
        fasta = http_get(url)
        header = fasta.split("\n")[0].split()
        assert(len(header) == 2)
        assert(header[0] == ">%s" % UniParcID)
        assert(header[1].startswith("status="))
        sequence = "".join(map(string.strip, fasta.split("\n")[1:]))
        self.sequence = sequence

    def to_dict(self):
        return {
            'UniParcID' : self.UniParcID,
            'UniProtAC' : self.UniProtAC,
            'UniProtKB' : self.UniProtKB,
            'sequence'  : self.sequence,
        }

    def __repr__(self):
        return simplejson.dumps(self.to_dict())
