#!/usr/bin/env python2
# encoding: utf-8
"""
blast.py
Python interface to the RCSB REST API for BLASTing sequences. The interface uses the BioCache class to reduce repeatedly
hitting the RCSB servers.

Created by Shane O'Connor 2016.
"""

import datetime
import os
import urllib2
import string

from klab import colortext
from klab.bio.cache import BioCache


upper_case_letters = set(list(string.ascii_uppercase))


class BLAST(object):
    '''Using a class makes it easier to set the BLAST parameters once.'''

    date_format = '%Y-%m-%dT%H:%M:%S'


    def __init__(self, bio_cache = None, cache_dir = None, matrix = 'BLOSUM62', silent = False, cut_off = 0.001, sequence_identity_cut_off = 70, stale_period_in_hours = 7 * 24, min_sequence_length = 20, force_lookup = False):
        '''If data is staler than stale_period_in_hours then we query it anew from the source e.g. BLAST results.'''
        self.bio_cache = bio_cache
        self.cache_dir = cache_dir
        if not(bio_cache) and (cache_dir and os.path.exists(cache_dir)):
            self.bio_cache = BioCache(cache_dir = cache_dir , max_capacity = 1000, silent = True)
        self.silent = silent
        self.matrix = matrix
        self.cut_off = cut_off
        self.sequence_identity_cut_off = sequence_identity_cut_off
        self.stale_period_in_hours = stale_period_in_hours
        self.min_sequence_length = min_sequence_length
        self.force_lookup = force_lookup

    #########################
    # Utility functions
    #########################


    def log(self, msg, silent, pfunk = None):
        if silent == None:
            silent = self.silent
        if not silent:
            if not pfunk:
                print(msg)
            else:
                pfunk(msg)


    #########################
    # BLAST functions
    #########################


    def by_pdb(self, pdb_id, take_top_percentile = 30.0, cut_off = None, matrix = None, sequence_identity_cut_off = None, silent = None):
        '''Returns a list of all PDB files which contain protein sequences similar to the protein sequences of pdb_id.
           Only protein chains are considered in the matching so e.g. some results may have DNA or RNA chains or ligands
           while some may not.
        '''

        self.log('BLASTing {0}'.format(pdb_id), silent, colortext.pcyan)

        # Preamble
        matrix = matrix or self.matrix
        cut_off = cut_off or self.cut_off
        sequence_identity_cut_off = sequence_identity_cut_off or self.sequence_identity_cut_off

        # Parse PDB file
        p = self.bio_cache.get_pdb_object(pdb_id)

        chain_ids = sorted(p.seqres_sequences.keys())
        assert(chain_ids)

        # Run BLAST over all chains
        hits = set(self.blast_by_pdb_chain(pdb_id, chain_ids[0], cut_off = cut_off, matrix = matrix, sequence_identity_cut_off = sequence_identity_cut_off, take_top_percentile = take_top_percentile, silent = silent))
        for chain_id in chain_ids[1:]:
            chain_hits = self.blast_by_pdb_chain(pdb_id, chain_id, cut_off = cut_off, matrix = matrix, sequence_identity_cut_off = sequence_identity_cut_off, take_top_percentile = take_top_percentile)
            if chain_hits != None:
                # None suggests that the chain was not a protein chain whereas an empty list suggest a protein chain with no hits
                hits = hits.intersection(set(chain_hits))
        return sorted(hits)


    def blast_by_pdb_chain(self, pdb_id, chain_id, take_top_percentile = 30.0, cut_off = None, matrix = None, sequence_identity_cut_off = None, silent = None):

        # Checks
        pdb_id, chain_id = pdb_id.strip(), chain_id.strip()
        if len(pdb_id) != 4:
            raise Exception('A PDB ID of four characters was expected. "{0}" was passed.'.format(pdb_id))
        if 5 <= len(chain_id) <= 0:
            raise Exception('A chain ID of between 1-4 characters was expected. "{0}" was passed.'.format(chain_id))

        self.log('BLASTing {0}:{1}'.format(pdb_id, chain_id), silent)

        # Construct query
        query_data = dict(
            structureId = pdb_id,
            chainId = chain_id,
        )
        xml_query = self._construct_query(query_data, cut_off = cut_off, matrix = matrix, sequence_identity_cut_off = sequence_identity_cut_off)

        # Read cached results
        if self.bio_cache:
            data = self.bio_cache.load_pdb_chain_blast(pdb_id, chain_id, query_data['eCutOff'], query_data['matrix'], query_data['sequenceIdentityCutoff'])
            if data:
                assert('query_date' in data)
                query_date = datetime.datetime.strptime(data['query_date'], BLAST.date_format)
                age_in_hours = ((datetime.datetime.now() -  query_date).total_seconds()) / (3600.0)
                assert(age_in_hours > -24.01)
                if not self.force_lookup:
                    if age_in_hours < self.stale_period_in_hours:
                        return data['hits']

        # POST the request and parse the PDB hits
        result = self._post(xml_query)
        hits = [l.strip().split(':')[0] for l in result.split('\n') if l.strip()]
        if pdb_id not in hits:
            if not hits:
                try:
                    p = self.bio_cache.get_pdb_object(pdb_id)
                    chain_type = p.chain_types[chain_id]
                    sequence_length = len(p.seqres_sequences[chain_id])
                    if not(chain_type == 'Protein' or chain_type == 'Protein skeleton'):
                        colortext.warning('Chain {1} of {0} is a {2} chain.'.format(pdb_id, chain_id, chain_type))
                        hits = None # None suggests that the chain was not a protein chain whereas an empty list suggest a protein chain with no hits
                    elif sequence_length < self.min_sequence_length:
                        colortext.warning('Chain {1} of {0} only contains {2} residues. The minimum sequence length is set to {3} residues so we will ignore this chain in matching.'.format(pdb_id, chain_id, sequence_length, self.min_sequence_length))
                        hits = None # None suggests that the chain was not a protein chain whereas an empty list suggest a protein chain with no hits
                except:
                    raise colortext.Exception('Failed to determine the chain type for chain {1} of {0}.'.format(pdb_id, chain_id))
            else:
                raise Exception('A BLAST of {0} chain {1} failed to find any hits for {0}. Is the chain a polypeptide chain?'.format(pdb_id, chain_id))

        query_data['hits'] = hits

        # Cache the results
        if self.bio_cache:
            self.bio_cache.save_pdb_chain_blast(pdb_id, chain_id, query_data['eCutOff'], query_data['matrix'], query_data['sequenceIdentityCutoff'], query_data)

        return query_data['hits']


    def by_sequence(self, sequence, take_top_percentile = 30.0, cut_off = None, matrix = None, sequence_identity_cut_off = None, silent = None):

        # Checks
        if set(sequence).intersection(upper_case_letters) != set(sequence): # We allow all characters just in case these are valid. Alternatively, we could check against basics.py::residue_type_1to3_map.keys() - 'X'
            raise Exception('The sequence {0} contained unexpected characters: {1}.'.format(colortext.myellow(sequence), colortext.morange(','.join(sorted(set(sequence).difference(upper_case_letters))))))

        self.log('BLASTing sequence {0}'.format(sequence), silent)

        # Construct query
        query_data = dict(sequence = sequence)
        xml_query = self._construct_query(query_data, cut_off = cut_off, matrix = matrix, sequence_identity_cut_off = sequence_identity_cut_off)

        # Read cached results
        if self.bio_cache:
            data = self.bio_cache.load_sequence_blast(sequence, query_data['eCutOff'], query_data['matrix'], query_data['sequenceIdentityCutoff'])
            if data:
                assert('query_date' in data)
                query_date = datetime.datetime.strptime(data['query_date'], BLAST.date_format)
                age_in_hours = ((datetime.datetime.now() -  query_date).total_seconds()) / (3600.0)
                assert(age_in_hours > -24.01)
                if age_in_hours < self.stale_period_in_hours:
                    return data['hits']

        # POST the request and parse the PDB hits
        result = self._post(xml_query)
        hits = map(str, [l.strip().split(':')[0] for l in result.split('\n') if l.strip()])
        query_data['hits'] = hits

        # Cache the results
        if self.bio_cache:
            self.bio_cache.save_sequence_blast(sequence, query_data['eCutOff'], query_data['matrix'], query_data['sequenceIdentityCutoff'], query_data)

        return query_data['hits']


    #########################
    # Private functions
    #########################


    def _construct_query(self, query_data, cut_off = None, matrix = None, sequence_identity_cut_off = None):

        if not 'matrix' in query_data:
            query_data['matrix'] = matrix or self.matrix
        if not 'eCutOff' in query_data:
            query_data['eCutOff'] = cut_off or self.cut_off
        if not 'sequenceIdentityCutoff' in query_data:
            query_data['sequenceIdentityCutoff'] = sequence_identity_cut_off or self.sequence_identity_cut_off
        query_data['query_date'] = datetime.datetime.strftime(datetime.datetime.now(), BLAST.date_format)

        description = ''
        extra_lines = []
        if 'structureId' in query_data and 'chainId' in query_data:
            description = 'Sequence Search (Structure:Chain = {structureId}:{chainId}, Expectation Value = {eCutOff}, Search Tool = BLAST)'
            extra_lines += ['\t<structureId>{structureId}</structureId>'.format(**query_data), '\t<chainId>{chainId}</chainId>'.format(**query_data)]
        elif 'sequence' in query_data:
            description = 'Sequence Search (Sequence = {sequence}, Expectation Value = {eCutOff}, Search Tool = BLAST)'
            extra_lines += ['\t<sequence>{sequence}</sequence>'.format(**query_data)]

        xml_query = '\n'.join([
            '<orgPdbQuery>',
            '\t<queryType>org.pdb.query.simple.SequenceQuery</queryType>',
            '\t<description>' + description + '</description>',
        ] + extra_lines + [
            '\t<eCutOff>{eCutOff}</eCutOff>',
            '\t<searchTool>blast</searchTool>',
            '\t<sequenceIdentityCutoff>{sequenceIdentityCutoff}</sequenceIdentityCutoff>',
            '</orgPdbQuery>']).format(**query_data)
        return xml_query


    def _post(self, xml_query):
        '''POST the request.'''
        req = urllib2.Request(url = 'http://www.rcsb.org/pdb/rest/search', data=xml_query)
        f = urllib2.urlopen(req)
        return f.read().strip()



