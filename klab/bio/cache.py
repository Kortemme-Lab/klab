#!/usr/bin/env python2
# encoding: utf-8
"""
cache.py
Simple functionality to help to avoid reading in file data multiple times. Motivated by a practical use of the relatrix code.

Created by Shane O'Connor 2016.
"""

import os
import datetime
import operator
import traceback
import json

from klab import colortext
from klab.bio.rcsb import download_pdb, retrieve_pdb, download_fasta, retrieve_fasta
from klab.bio.rcsb import download_xml as download_pdbml
from klab.bio.rcsb import retrieve_xml as retrieve_pdbml
from klab.bio.pdb import PDB
from klab.bio.sifts import SIFTS
from klab.bio.sifts import retrieve_xml as retrieve_sifts_xml
from klab.bio.sifts import download_xml as download_sifts_xml
from klab.bio.pdbml import PDBML
from klab.bio.fasta import FASTA
from klab.fs.fsio import read_file, write_file
from klab.hash.CRC64 import CRC64digest


class CacheNode(object):
    '''Simple class to store an object and the time of insertion.'''

    def __init__(self, payload):
        self.t = datetime.datetime.now()
        self.o = payload


    def get(self):
        '''Refresh the access time and return the object.'''
        self.t = datetime.datetime.now()
        return self.o

    def __repr__(self): return '{0}: {1}'.format(self.t, self.o.__repr__()[:50])
    def __cmp__(self, other): return (self.t).__cmp__(other.t)
    def __gt__(self, other): return (self.t).__gt__(other.t)
    def __ge__(self, other): return (self.t).__ge__(other.t)
    def __lt__(self, other): return (self.t).__lt__(other.t)
    def __le__(self, other): return (self.t).__le__(other.t)
    def __eq__(self, other): return (self.t).__eq__(other.t)
    def __ne__(self, other): return (self.t).__ne__(other.t)



class CacheNodeDict(dict):

    def __getitem__(self, k):
        return dict.__getitem__(self, k).get()



class BioCache(object):
    '''Class to store a cache of klab.bio objects. This can be used to avoid reading the same data in from disk over
       and over again.
    '''


    def __init__(self, cache_dir = None, max_capacity = None, silent = True):
        '''max_capacity is currently used to set the maximum capacity of all object lists i.e. you cannot currently set different
           max capacities for different lists.'''
        if cache_dir:
            assert(os.path.exists(cache_dir))
        if max_capacity != None:
            max_capacity = int(max_capacity)
            assert(max_capacity >= 1)
        self.cache_dir = cache_dir

        # PDB files
        self.pdb_contents = CacheNodeDict()
        self.pdb_objects = CacheNodeDict()

        # SIFTS XML files
        self.sifts_xml_contents = CacheNodeDict()
        self.sifts_objects = CacheNodeDict()

        # PDBML files
        self.pdbml_contents = CacheNodeDict()
        self.pdbml_objects = CacheNodeDict()

        # FASTA files
        self.fasta_contents = CacheNodeDict()
        self.fasta_objects = CacheNodeDict()

        self.max_capacity = max_capacity
        self.silent = silent


    def log(self, msg):
        if not self.silent:
            colortext.plightpurple(msg)


    def log_lookup(self, msg):
        self.log('CACHE LOOKUP: {0}'.format(msg))
        #self.log('CACHE LOOKUP: {0}.\n{1}'.format(msg, '\n'.join([l[:-1] for l in traceback.format_stack()])))


    def add_node(self, container, k, v):
        if self.max_capacity and (len(container) + 1) > self.max_capacity:
            # Truncate container contents
            keys_to_delete = [t[0] for t in sorted(container.items(), key=operator.itemgetter(1))[:-(self.max_capacity - 1)]] # sort by datetime of insertion and keep the last self.max_capacity minus one objects (to allow space for one more object)
            for dk in keys_to_delete:
                del container[dk]
        container[k] = CacheNode(v)


    ######################
    # PDB files
    ######################


    def add_pdb_contents(self, pdb_id, contents):
        self.add_node(self.pdb_contents, pdb_id.upper(), contents)


    def get_pdb_contents(self, pdb_id):
        self.log_lookup('pdb contents {0}'.format(pdb_id))
        pdb_id = pdb_id.upper()
        if not self.pdb_contents.get(pdb_id):
            if self.pdb_objects.get(pdb_id):
                self.add_pdb_contents(pdb_id, '\n'.join(self.pdb_objects[pdb_id].lines))
            elif self.cache_dir:
                self.add_pdb_contents(pdb_id, download_pdb(pdb_id, self.cache_dir, silent = True))
            else:
                self.add_pdb_contents(pdb_id, retrieve_pdb(pdb_id, silent = True))
        return self.pdb_contents[pdb_id]


    def add_pdb_object(self, pdb_id, pdb_object):
        self.add_node(self.pdb_objects, pdb_id.upper(), pdb_object)


    def get_pdb_object(self, pdb_id):
        self.log_lookup('pdb object {0}'.format(pdb_id))
        pdb_id = pdb_id.upper()
        if not self.pdb_objects.get(pdb_id):
            if not self.pdb_contents.get(pdb_id):
                if self.cache_dir:
                    self.add_pdb_contents(pdb_id, download_pdb(pdb_id, self.cache_dir, silent = True))
                else:
                    self.add_pdb_contents(pdb_id, retrieve_pdb(pdb_id, silent = True))
            self.add_pdb_object(pdb_id, PDB(self.pdb_contents[pdb_id]))
        return self.pdb_objects[pdb_id]


    ######################
    # SIFTS XML files
    ######################


    def add_sifts_xml_contents(self, pdb_id, sifts_xml_contents):
        self.add_node(self.sifts_xml_contents, pdb_id.upper(), sifts_xml_contents)


    def get_sifts_xml_contents(self, pdb_id):
        self.log_lookup('SIFTS xml {0}'.format(pdb_id))
        pdb_id = pdb_id.upper()
        if not self.sifts_xml_contents.get(pdb_id):
            if self.sifts_objects.get(pdb_id):
                self.add_sifts_xml_contents(pdb_id, self.sifts_objects[pdb_id].xml_contents)
            elif self.cache_dir:
                self.add_sifts_xml_contents(pdb_id, download_sifts_xml(pdb_id, self.cache_dir, silent = True))
            else:
                self.add_sifts_xml_contents(pdb_id, retrieve_sifts_xml(pdb_id, silent = True))
        return self.sifts_xml_contents[pdb_id]


    def add_sifts_object(self, pdb_id, sifts_object):
        self.add_node(self.sifts_objects, pdb_id.upper(), sifts_object)


    def get_sifts_object(self, pdb_id, acceptable_sequence_percentage_match = 90.0, restrict_match_percentage_errors_to_these_uniparc_ids = None):
        # todo: we need to store all/important parameters for object creation and key on those as well e.g. "give me the SIFTS object with , restrict_match_percentage_errors_to_these_uniparc_ids = <some_set>"
        #       otherwise, unexpected behavior may occur
        self.log_lookup('SIFTS object {0}'.format(pdb_id))
        pdb_id = pdb_id.upper()
        if not self.sifts_objects.get(pdb_id):
            if not self.sifts_xml_contents.get(pdb_id):
                if self.cache_dir:
                    self.add_sifts_xml_contents(pdb_id, download_sifts_xml(pdb_id, self.cache_dir, silent = True))
                else:
                    self.add_sifts_xml_contents(pdb_id, retrieve_sifts_xml(pdb_id, silent = True))
            self.add_sifts_object(pdb_id, SIFTS.retrieve(pdb_id, cache_dir = self.cache_dir, acceptable_sequence_percentage_match = acceptable_sequence_percentage_match, bio_cache = self, restrict_match_percentage_errors_to_these_uniparc_ids = restrict_match_percentage_errors_to_these_uniparc_ids))
        return self.sifts_objects[pdb_id]


    ######################
    # PDBML files
    ######################


    def add_pdbml_contents(self, pdb_id, pdbml_contents):
        self.add_node(self.pdbml_contents, pdb_id.upper(), pdbml_contents)


    def get_pdbml_contents(self, pdb_id):
        self.log_lookup('PDBML {0}'.format(pdb_id))
        pdb_id = pdb_id.upper()
        if not self.pdbml_contents.get(pdb_id):
            if self.pdbml_objects.get(pdb_id):
                self.add_pdbml_contents(pdb_id, self.pdbml_objects[pdb_id].xml_contents)
            elif self.cache_dir:
                self.add_pdbml_contents(pdb_id, download_pdbml(pdb_id, self.cache_dir, silent = True))
            else:
                self.add_pdbml_contents(pdb_id, retrieve_pdbml(pdb_id, silent = True))
        return self.pdbml_contents[pdb_id]


    def add_pdbml_object(self, pdb_id, pdbml_object):
        self.add_node(self.pdbml_objects, pdb_id.upper(), pdbml_object)


    def get_pdbml_object(self, pdb_id, acceptable_sequence_percentage_match = 90.0):
        self.log_lookup('PDBML object {0}'.format(pdb_id))
        pdb_id = pdb_id.upper()
        if not self.pdbml_objects.get(pdb_id):
            if not self.pdbml_contents.get(pdb_id):
                if self.cache_dir:
                    self.add_pdbml_contents(pdb_id, download_pdbml(pdb_id, self.cache_dir, silent = True))
                else:
                    self.add_pdbml_contents(pdb_id, retrieve_pdbml(pdb_id, silent = True))
            self.add_pdbml_object(pdb_id, PDBML.retrieve(pdb_id, cache_dir = self.cache_dir, bio_cache = self))
        return self.pdbml_objects[pdb_id]


    ######################
    # FASTA files
    ######################


    def add_fasta_contents(self, pdb_id, fasta_contents):
        self.add_node(self.fasta_contents, pdb_id.upper(), fasta_contents)


    def get_fasta_contents(self, pdb_id):
        self.log_lookup('FASTA {0}'.format(pdb_id))
        pdb_id = pdb_id.upper()
        if not self.fasta_contents.get(pdb_id):
            if self.fasta_objects.get(pdb_id):
                self.add_fasta_contents(pdb_id, self.fasta_objects[pdb_id].fasta_contents)
            elif self.cache_dir:
                self.add_fasta_contents(pdb_id, download_fasta(pdb_id, self.cache_dir, silent = True))
            else:
                self.add_fasta_contents(pdb_id, retrieve_fasta(pdb_id, silent = True))
        return self.fasta_contents[pdb_id]


    def add_fasta_object(self, pdb_id, fasta_object):
        self.add_node(self.fasta_objects, pdb_id.upper(), fasta_object)


    def get_fasta_object(self, pdb_id, acceptable_sequence_percentage_match = 90.0):
        self.log_lookup('FASTA object {0}'.format(pdb_id))
        pdb_id = pdb_id.upper()
        if not self.fasta_objects.get(pdb_id):
            if not self.fasta_contents.get(pdb_id):
                if self.cache_dir:
                    self.add_fasta_contents(pdb_id, download_fasta(pdb_id, self.cache_dir, silent = True))
                else:
                    self.add_fasta_contents(pdb_id, retrieve_fasta(pdb_id, silent = True))
            self.add_fasta_object(pdb_id, FASTA.retrieve(pdb_id, cache_dir = self.cache_dir, bio_cache = self))
        return self.fasta_objects[pdb_id]


    ######################
    # BLAST results
    ######################


    def _get_blast_pdb_filepath(self, pdb_id, chain_id, cut_off, matrix, sequence_identity_cut_off):
        assert(self.cache_dir)
        return os.path.join(self.cache_dir, '{0}_{1}_{2}_{3}_{4}.BLAST.json'.format(pdb_id.upper(), chain_id, cut_off, matrix, sequence_identity_cut_off))


    def load_pdb_chain_blast(self, pdb_id, chain_id, cut_off, matrix, sequence_identity_cut_off):
        if self.cache_dir:
            filepath = self._get_blast_pdb_filepath(pdb_id, chain_id, cut_off, matrix, sequence_identity_cut_off)
            if os.path.exists(filepath):
                return json.loads(read_file(filepath))
        return None


    def save_pdb_chain_blast(self, pdb_id, chain_id, cut_off, matrix, sequence_identity_cut_off, data):
        if self.cache_dir:
            filepath = self._get_blast_pdb_filepath(pdb_id, chain_id, cut_off, matrix, sequence_identity_cut_off)
            write_file(filepath, json.dumps(data))
            return True
        return False


    def _get_blast_sequence_filepath(self, sequence, cut_off, matrix, sequence_identity_cut_off):
        assert(self.cache_dir)
        id = '{0}_{1}_{2}_{3}'.format(CRC64digest(sequence), len(sequence), sequence[:5], sequence[-5:])
        return os.path.join(self.cache_dir, '{0}_{1}_{2}_{3}.BLAST.json'.format(id, cut_off, matrix, sequence_identity_cut_off))


    def load_sequence_blast(self, sequence, cut_off, matrix, sequence_identity_cut_off):
        if self.cache_dir:
            filepath = self._get_blast_sequence_filepath(sequence, cut_off, matrix, sequence_identity_cut_off)
            if os.path.exists(filepath):
                for sequence_hits in json.loads(read_file(filepath)):
                    if sequence_hits['sequence'] == sequence:
                        return sequence_hits
        return None


    def save_sequence_blast(self, sequence, cut_off, matrix, sequence_identity_cut_off, data):
        assert(data['sequence'] == sequence)
        sequence_data = [data] # put the new hit at the start of the file
        if self.cache_dir:
            filepath = self._get_blast_sequence_filepath(sequence, cut_off, matrix, sequence_identity_cut_off)
            if os.path.exists(filepath):
                for sequence_hits in json.loads(read_file(filepath)):
                    if sequence_hits['sequence'] != sequence:
                        sequence_data.append(sequence_hits)
            write_file(filepath, json.dumps(sequence_data))
            return True
        return False


    ######################
    # Static methods
    ######################


    @staticmethod
    def static_get_pdb_object(pdb_id, bio_cache = None, cache_dir = None):
        '''This method does not necessarily use a BioCache but it seems to fit here.'''
        pdb_id = pdb_id.upper()

        if bio_cache:
            return bio_cache.get_pdb_object(pdb_id)

        if cache_dir:
            # Check to see whether we have a cached copy of the PDB file
            filepath = os.path.join(cache_dir, '{0}.pdb'.format(pdb_id))
            if os.path.exists(filepath):
                return PDB.from_filepath(filepath)

        # Get any missing files from the RCSB and create cached copies if appropriate
        pdb_contents = retrieve_pdb(pdb_id)
        if cache_dir:
            write_file(os.path.join(cache_dir, "%s.pdb" % pdb_id), pdb_contents)
        return PDB(pdb_contents)