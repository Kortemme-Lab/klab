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
import urllib
import gzip
import shlex

from klab.comms.http import Connection
from klab.fs.fsio import read_file, write_file
from klab import colortext
from klab.process import Popen


rcsb_connection = None
rcsb_files_connection = None


def get_rcsb_connection():
    global rcsb_connection
    if not rcsb_connection:
        rcsb_connection = Connection('www.rcsb.org', timeout = 10)
    return rcsb_connection


def get_rcsb_files_connection():
    global rcsb_files_connection
    if not rcsb_files_connection:
        rcsb_files_connection = Connection('files.rcsb.org', timeout = 10)
    return rcsb_files_connection


def retrieve_file_from_RCSB(http_connection, resource, silent = True):
    '''Retrieve a file from the RCSB.'''
    if not silent:
        colortext.printf("Retrieving %s from RCSB" % os.path.split(resource)[1], color = "aqua")
    return http_connection.get(resource)


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
    return retrieve_file_from_RCSB(get_rcsb_files_connection(), "/download/%s.pdb" % pdb_id, silent = silent)


def retrieve_fasta(pdb_id, silent = True):
    return retrieve_file_from_RCSB(get_rcsb_connection(), "/pdb/files/fasta.txt?structureIdList=%s" % pdb_id, silent = silent)


def download_fasta(pdb_id, dest_dir, silent = True, filename = None):
    assert(os.path.exists(dest_dir))
    lower_case_filename = os.path.join(dest_dir, '{0}.fasta'.format(pdb_id.lower()))
    upper_case_filename = os.path.join(dest_dir, '{0}.fasta'.format(pdb_id.upper()))
    if filename:
        requested_filename = os.path.join(dest_dir, filename)
        if os.path.exists(requested_filename):
            return read_file(requested_filename)
    if os.path.exists(lower_case_filename):
        return read_file(lower_case_filename)
    elif os.path.exists(upper_case_filename):
        return read_file(upper_case_filename)
    else:
        contents = retrieve_fasta(pdb_id, silent = silent)
        write_file(os.path.join(dest_dir, filename or '{0}.fasta'.format(pdb_id)), contents)
        return contents


def retrieve_xml(pdb_id, silent = True):
    '''The RCSB website now compresses XML files.'''
    xml_gz = retrieve_file_from_RCSB(get_rcsb_files_connection(), "/download/%s.xml.gz" % pdb_id, silent = silent)
    cf = StringIO.StringIO()
    cf.write(xml_gz)
    cf.seek(0)
    df = gzip.GzipFile(fileobj = cf, mode='rb')
    contents = df.read()
    df.close()
    return contents


def download_xml(pdb_id, dest_dir, silent = True, filename = None):
    assert(os.path.exists(dest_dir))
    lower_case_filename = os.path.join(dest_dir, '{0}.xml'.format(pdb_id.lower()))
    upper_case_filename = os.path.join(dest_dir, '{0}.xml'.format(pdb_id.upper()))
    if filename:
        requested_filename = os.path.join(dest_dir, filename)
        if os.path.exists(requested_filename):
            return read_file(requested_filename)
    if os.path.exists(lower_case_filename):
        return read_file(lower_case_filename)
    elif os.path.exists(upper_case_filename):
        return read_file(upper_case_filename)
    else:
        contents = retrieve_xml(pdb_id, silent = silent)
        write_file(os.path.join(dest_dir, filename or '{0}.xml'.format(pdb_id)), contents)
        return contents


def retrieve_ligand_cif(ligand_id, silent = True):
    return retrieve_file_from_RCSB(get_rcsb_connection(), "/pdb/files/ligand/%s.cif" % ligand_id, silent = silent)


def retrieve_pdb_ligand_info(pdb_id, silent = True):
    return retrieve_file_from_RCSB(get_rcsb_connection(), "http://www.rcsb.org/pdb/rest/ligandInfo?structureId={0}".format(pdb_id), silent = silent)


def retrieve_ligand_diagram(pdb_ligand_code):
    from PIL import Image
    file = BytesIO(urllib.urlopen('http://www.rcsb.org/pdb/images/{0}_600.gif'.format(pdb_ligand_code)).read())
    img = Image.open(file)
    width, height = img.size
    if width < 100: # not a foolproof method - they may change the failure picture in future
        file = BytesIO(urllib.urlopen('http://www.rcsb.org/pdb/images/{0}_270.gif'.format(pdb_ligand_code)).read())
        img = Image.open(file)
        width, height = img.size
        if width < 100:
            colortext.warning('Could not find a diagram for ligand {0}. It is possible that the URLs have changed.'.format(pdb_ligand_code))
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
