#!/usr/bin/python2.4
# encoding: utf-8
"""
pfam.py
Functions for interacting with Pfam entries.

Created by Shane O'Connor 2015.
"""

import sys, os
import pprint

if __name__ == "__main__":
    sys.path.insert(0, "../../")
from klab.db.mysql import DatabaseInterface
from klab import colortext
from klab.fs.fsio import read_file


pdb_to_pfam_mapping_file = '/kortemmelab/shared/mirror/SIFTS/pdb_chain_pfam.tsv.gz'


class Pfam(object):

    def __init__(self):
        pdb_chain_to_pfam_mapping = {}
        pfam_to_pdb_chain_mapping = {}
        lines = read_file(pdb_to_pfam_mapping_file).split('\n')

        for c in range(len(lines)):
            if not lines[c].startswith('#'):
                break
        assert(lines[c].split() == ['PDB', 'CHAIN', 'SP_PRIMARY', 'PFAM_ID'])
        for l in lines[c:]:
            if l.strip():
                tokens = l.split()

                pdb_id = tokens[0].lower()
                chain_id = tokens[1]
                pfam_acc = tokens[3]
                pdb_key = (pdb_id, chain_id)
                pdb_chain_to_pfam_mapping[pdb_id] = pdb_chain_to_pfam_mapping.get(pdb_id, {})
                pdb_chain_to_pfam_mapping[pdb_id][chain_id] = pdb_chain_to_pfam_mapping[pdb_id].get(chain_id, set())
                pdb_chain_to_pfam_mapping[pdb_id][chain_id].add(pfam_acc)

                pfam_to_pdb_chain_mapping[pfam_acc] = pfam_to_pdb_chain_mapping.get(pfam_acc, set())
                pfam_to_pdb_chain_mapping[pfam_acc].add(pdb_key)

        self.pdb_chain_to_pfam_mapping = pdb_chain_to_pfam_mapping
        self.pfam_to_pdb_chain_mapping = pfam_to_pdb_chain_mapping


    def get_pfam_accession_numbers_from_pdb_id(self, pdb_id):
        '''Note: an alternative is to use the RCSB API e.g. http://www.rcsb.org/pdb/rest/hmmer?structureId=1cdg.'''
        pdb_id = pdb_id.lower()
        if self.pdb_chain_to_pfam_mapping.get(pdb_id):
            return self.pdb_chain_to_pfam_mapping[pdb_id].copy()

    def get_pfam_accession_numbers_from_pdb_chain(self, pdb_id, chain):
        '''Note: an alternative is to use the RCSB API e.g. http://www.rcsb.org/pdb/rest/hmmer?structureId=1cdg.'''
        return self.pdb_chain_to_pfam_mapping.get(pdb_id.lower(), {}).get(chain)

    def get_pdb_chains_from_pfam_accession_number(self, pfam_acc):
        return self.pfam_to_pdb_chain_mapping.get(pfam_acc)


if __name__ == '__main__':
    pfam_api = Pfam()
    colortext.warning(pfam_api.get_pfam_accession_numbers_from_pdb_chain('1TVA', 'A'))
    colortext.warning(pfam_api.get_pfam_accession_numbers_from_pdb_chain('1CDG', 'A'))
    colortext.warning(pfam_api.get_pfam_accession_numbers_from_pdb_id('1A2c'))

    colortext.message(pfam_api.get_pdb_chains_from_pfam_accession_number('PF14716'))
