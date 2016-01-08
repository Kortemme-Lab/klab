#!/usr/bin/python
# encoding: utf-8
"""
rcsb.py
For functions relating to getting data from the RCSB.

Created by Shane O'Connor 2011/2012
"""

import os
import StringIO
from io import BytesIO
from PIL import Image
import urllib
import shlex

from klab.comms.http import Connection
from klab.fs.fsio import read_file, write_file
from klab import colortext
from klab.process import Popen


rcsb_connection = None


def get_rcsb_connection():
    global rcsb_connection
    if not rcsb_connection:
        rcsb_connection = Connection('www.rcsb.org')
    return rcsb_connection


def retrieve_file_from_RCSB(resource, silent = True):
    '''Retrieve a file from the RCSB.'''
    get_rcsb_connection()
    if not silent:
        colortext.printf("Retrieving %s from RCSB" % os.path.split(resource)[1], color = "aqua")
    return rcsb_connection.get(resource)


def download_pdb(pdb_id, dest_dir, silent = True, filename = None):
    assert(os.path.exists(dest_dir))
    lower_case_filename = os.path.join(dest_dir, '{0}.pdb'.format(pdb_id.lower()))
    upper_case_filename = os.path.join(dest_dir, '{0}.pdb'.format(pdb_id.upper()))
    if filename:
        requested_filename = os.path.join(dest_dir, filename)
        if os.path.exists(requested_filename):
            return read_file(requested_filename)
    if os.path.exists(lower_case_filename):
        return read_file(lower_case_filename)
    elif os.path.exists(upper_case_filename):
        return read_file(upper_case_filename)
    else:
        contents = retrieve_pdb(pdb_id, silent = silent)
        write_file(os.path.join(dest_dir, filename or '{0}.pdb'.format(pdb_id)), contents)
        return contents


def retrieve_pdb(pdb_id, silent = True):
    return retrieve_file_from_RCSB("/pdb/files/%s.pdb" % pdb_id, silent = silent)


def retrieve_fasta(pdb_id, silent = True):
    return retrieve_file_from_RCSB("/pdb/files/fasta.txt?structureIdList=%s" % pdb_id, silent = silent)


def retrieve_xml(pdb_id, silent = True):
    return retrieve_file_from_RCSB("/pdb/files/%s.xml" % pdb_id, silent = silent)


def retrieve_ligand_cif(ligand_id, silent = True):
    return retrieve_file_from_RCSB("/pdb/files/ligand/%s.cif" % ligand_id, silent = silent)


def retrieve_pdb_ligand_info(pdb_id, silent = True):
    return retrieve_file_from_RCSB("http://www.rcsb.org/pdb/rest/ligandInfo?structureId={0}".format(pdb_id), silent = silent)


def retrieve_pdb_ligand_info2(pdb_id, silent = True):
    # todo: This is a nasty, platform-specific hack. Look into why retrieve_file_from_RCSB and urllib2 are not passing through the REST interface
    # update: this seemed to be because my old code opened a new HTTPConnection each time. I now use the new http.Connection class.
    tmp_filename = '/tmp/{0}.ligandinfo'.format(pdb_id.lower())
    p = Popen('/tmp', shlex.split('wget http://www.rcsb.org/pdb/rest/ligandInfo?structureId={0} -O {1}'.format(pdb_id, tmp_filename)))
    assert(p.errorcode == 0)
    contents = read_file(tmp_filename)
    os.remove(tmp_filename)
    return contents


def retrieve_ligand_diagram(pdb_ligand_code):
    file = BytesIO(urllib.urlopen('http://www.rcsb.org/pdb/images/{0}_600.gif'.format(pdb_ligand_code)).read())
    img = Image.open(file)
    width, height = img.size
    if width < 100: # not a foolproof method - they may change the failure picture in future
        file = BytesIO(urllib.urlopen('http://www.rcsb.org/pdb/images/{0}_270.gif'.format(pdb_ligand_code)).read())
        img = Image.open(file)
        width, height = img.size
        if width < 100:
            return None
    file.seek(0)
    return file.read()



def retrieve_fasta_from_database(pdbID, database_ref = None, database_table = None, database_field = None, database_IDfield = None, silent = True):
    if database_ref and database_table and database_field and database_IDfield:
        results = database_ref.execute(("SELECT %s FROM %s WHERE %s=" % (database_field, database_table, database_IDfield)) + "%s", parameters = (pdbID,))
        if results:
            assert(len(results) == 1)
            return results[0][database_field]
    return retrieve_fasta(pdbID, silent = silent)