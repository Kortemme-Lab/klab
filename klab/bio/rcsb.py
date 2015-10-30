#!/usr/bin/python
# encoding: utf-8
"""
rcsb.py
For functions relating to getting data from the RCSB.

Created by Shane O'Connor 2011/2012
"""

import os
from tools.comms.http import get_resource

from tools import colortext

def retrieve_file_from_RCSB(resource, silent = True):
    '''Retrieve a file from the RCSB.'''
    if not silent:
        colortext.printf("Retrieving %s from RCSB" % os.path.split(resource)[1], color = "aqua")
    return get_resource("www.rcsb.org", resource)

def retrieve_pdb(pdb_id, silent = True):
    return retrieve_file_from_RCSB("/pdb/files/%s.pdb" % pdb_id, silent)

def retrieve_fasta(pdb_id, silent = True):
    return retrieve_file_from_RCSB("/pdb/files/fasta.txt?structureIdList=%s" % pdb_id, silent)

def retrieve_xml(pdb_id, silent = True):
    return retrieve_file_from_RCSB("/pdb/files/%s.xml" % pdb_id, silent)

def retrieve_fasta_from_database(pdbID, database_ref = None, database_table = None, database_field = None, database_IDfield = None, silent = True):
    if database_ref and database_table and database_field and database_IDfield:
        results = database_ref.execute(("SELECT %s FROM %s WHERE %s=" % (database_field, database_table, database_IDfield)) + "%s", parameters = (pdbID,))
        if results:
            assert(len(results) == 1)
            return results[0][database_field]
    return retrieve_fasta(pdbID, silent)