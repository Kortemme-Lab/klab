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

from klab import colortext
from klab.bio.rcsb import download_pdb, retrieve_pdb
from klab.bio.pdb import PDB

class CacheNode(object):
    '''Simple class to store an object and the time of insertion.'''

    def __init__(self, payload):
        self.t = datetime.datetime.now()
        self.o = payload


    def get(self): return self.o
    def __repr__(self): return '{0}: {1}'.format(self.t, self.o.__repr__()[:50])
    def __cmp__(self, other): return (self.t).__cmp__(other.t)
    def __gt__(self, other): return (self.t).__gt__(other.t)
    def __ge__(self, other): return (self.t).__ge__(other.t)
    def __lt__(self, other): return (self.t).__lt__(other.t)
    def __le__(self, other): return (self.t).__le__(other.t)
    def __eq__(self, other): return (self.t).__eq__(other.t)
    def __ne__(self, other): return (self.t).__ne__(other.t)


class PDBCache(object):
    '''Class to store a cache of PDB-related objects. This can be used to avoid reading the same data in from disk over
       and over again.
    '''


    def __init__(self, cache_dir = None, max_capacity = None):
        if cache_dir:
            assert(os.path.exists(cache_dir))
        if max_capacity != None:
            max_capacity = int(max_capacity)
            assert(max_capacity >= 1)
        self.cache_dir = cache_dir
        self.pdb_contents = {}
        self.pdb_objects = {}
        self.max_capacity = max_capacity


    def add_node(self, container, k, v):
        if self.max_capacity and (len(container) + 1) > self.max_capacity:
            # Truncate container contents
            keys_to_delete = [t[0] for t in sorted(container.items(), key=operator.itemgetter(1))[:-(self.max_capacity - 1)]] # sort by datetime of insertion and keep the last self.max_capacity minus one objects (to allow space for one more object)
            for dk in keys_to_delete:
                del container[dk]
        container[k] = CacheNode(v)


    def add_pdb_contents(self, pdb_id, contents):
        self.add_node(self.pdb_contents, pdb_id, contents)


    def get_pdb_contents(self, pdb_id):
        pdb_id = pdb_id.upper()
        if not self.pdb_contents.get(pdb_id):
            if self.pdb_objects.get(pdb_id):
                self.add_pdb_contents(pdb_id, '\n'.join(self.pdb_objects[pdb_id].lines))
            elif self.cache_dir:
                self.add_pdb_contents(pdb_id, download_pdb(pdb_id, self.cache_dir, silent = True))
            else:
                self.add_pdb_contents(pdb_id, retrieve_pdb(pdb_id, silent = True))
        return self.pdb_contents[pdb_id].get()


    def add_pdb_object(self, pdb_id, pdb_object):
        self.add_node(self.pdb_objects, pdb_id, pdb_object)


    def get_pdb_objects(self, pdb_id):
        pdb_id = pdb_id.upper()
        if not self.pdb_objects.get(pdb_id):
            if not self.pdb_contents.get(pdb_id):
                if self.cache_dir:
                    self.add_pdb_contents(pdb_id, download_pdb(pdb_id, self.cache_dir, silent = True))
                else:
                    self.add_pdb_contents(pdb_id, retrieve_pdb(pdb_id, silent = True))
            self.add_pdb_object(pdb_id, PDB(self.pdb_contents[pdb_id]))
        return self.pdb_objects[pdb_id].get()


