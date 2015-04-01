#!/usr/bin/python2.4
# encoding: utf-8
"""
scop.py
Functions for interacting with the SCOPe database.

Created by Shane O'Connor 2015.
"""

import sys, os
import pprint

if __name__ == "__main__":
    sys.path.insert(0, "../../")
from tools.db.mysql import DatabaseInterface
from tools import colortext


installed_database = 'SCOPe205' # rename this to the new database name on updates
installed_database_version = '2.05' # rename this to the new database version on updates

class SCOPeDatabase(DatabaseInterface):


    def __init__(self, passwd = None, username = 'anonymous', use_utf=False):
        super(SCOPeDatabase, self).__init__({},
            isInnoDB = True,
            numTries = 32,
            host = "guybrush.ucsf.edu",
            db = installed_database,
            user = username,
            passwd = None,
            port = 3306,
            unix_socket = "/var/lib/mysql/mysql.sock",
            use_utf = use_utf)

        self.levels = self.get_SCOPe_levels()

        # Set up CSV fields
        self.csv_fields = [
            'pdb_id', 'chain', 'is_polypeptide', 'chain_description', 'resolution',
            'sunid', 'sccs', 'sid']
        self.csv_headers = [
            'PDB id', 'Chain', 'Is polypeptide', 'Description', 'Resolution',
            'sunid', 'sccs', 'sid']
        level_names = [v for k, v in sorted(self.levels.iteritems()) if k != 1] # skip the root level
        self.csv_fields.extend(level_names)
        self.csv_headers.extend(level_names)
        assert(len(self.csv_fields) == len(self.csv_headers))


    def get_SCOPe_levels(self):
        d = {}
        results = self.execute_select('SELECT * FROM scop_level ORDER BY id')
        for r in results:
            d[r['id']] = r['description']
        return d


    def get_chain_details(self, pdb_id, chain = None):
        '''Returns a dict pdb_id -> chain(s) -> chain and SCOP details.'''

        query = '''
            SELECT DISTINCT scop_node.*, pdb_entry.code, pdb_chain.chain, pdb_chain.is_polypeptide, pdb_entry.description AS ChainDescription, pdb_release.resolution
            FROM `link_pdb`
            INNER JOIN scop_node on node_id=scop_node.id
            INNER JOIN pdb_chain ON pdb_chain_id = pdb_chain.id
            INNER JOIN pdb_release ON pdb_release_id = pdb_release.id
            INNER JOIN pdb_entry ON pdb_entry_id = pdb_entry.id
            WHERE pdb_entry.code=%s'''
        if chain:
            query += ' AND pdb_chain.chain=%s'
            parameters=(pdb_id, chain)
        else:
            parameters = (pdb_id, )
        query += ' ORDER BY release_id DESC'

        leaf_nodes = {}
        results = self.execute_select(query, parameters = parameters)
        if not results:
            return None

        # Only consider the most recent records
        for r in results:
            chain_id = r['chain']
            if (not leaf_nodes.get(chain_id)) or (r['release_id'] > leaf_nodes[chain_id]['release_id']):
                leaf_nodes[chain_id] = r

        # Older revisions of SCOP have blank chain IDs for some records while newer revisions have the chain ID
        # The best solution to avoid redundant results seems to be to remove all blank chain records if at least one
        # more recent named chain exists. There could be some nasty cases - we only keep the most recent unnamed chain
        # but this may correspond to many chains if the PDB has multiple chains since we only look at the chain ID.
        # I think that it should be *unlikely* that we will have much if any bad behavior though.
        if leaf_nodes.get(' '):
            release_id_of_blank_record = leaf_nodes[' ']['release_id']
            for k, v in leaf_nodes.iteritems():
                if k != ' ':
                    assert(k.isalpha() and len(k) == 1)
                    if v['release_id'] > release_id_of_blank_record:
                        del leaf_nodes[' '] # we are modifying a structure while iterating over it but we break immediately afterwards
                        break

        d = {}
        for chain_id, details in leaf_nodes.iteritems():

            # Get the details for all chains
            d[chain_id] = dict(
                pdb_id = details['code'],
                chain = details['chain'],
                is_polypeptide = details['is_polypeptide'],
                chain_description = details['ChainDescription'],
                resolution = details['resolution'],
                sunid = details['sunid'],
                sccs = details['sccs'],
                sid = details['sid'],
                scop_release_id = details['release_id']
            )

            for k, v in sorted(self.levels.iteritems()):
                d[chain_id][v] = None

            level, parent_node_id = details['level_id'], details['parent_node_id']

            # Store the top-level description
            d[chain_id][self.levels[level]] = details['description']

            # Wind up the level hierarchy and retrieve the descriptions
            c = 0
            while level > 0 :
                parent_details = self.execute_select('SELECT * FROM scop_node WHERE id=%s', parameters = (parent_node_id,))
                assert(len(parent_details) <= 1)
                if parent_details:
                    parent_details = parent_details[0]
                    level, parent_node_id = parent_details['level_id'], parent_details['parent_node_id']
                    d[chain_id][self.levels[level]] = parent_details['description']
                else:
                    break
                # This should never trigger but just in case...
                c += 1
                if c > 20:
                    raise Exception('There is a logical error in the script or database which may result in an infinite lookup loop.')
        return d


    def get_pdb_list_details(self, pdb_ids):
        d = {}
        for pdb_id in pdb_ids:
            results = self.get_chain_details(pdb_id)
            d[pdb_id] = results
        return d


    def get_pdb_list_details_as_table(self, pdb_ids):
        s = []
        d = self.get_pdb_list_details(pdb_ids)
        if d:
            s.append(self.csv_headers)
            for pdb_id, pdb_details in sorted(d.iteritems()):
                if pdb_details:
                    for chain_id, chain_details in sorted(pdb_details.iteritems()):
                        s.append([str(chain_details[f]) for f in self.csv_fields])
        return s


    def get_pdb_list_details_as_csv(self, pdb_ids, field_separator = ',', line_separator = '\n'):
        lst = self.get_pdb_list_details_as_table(pdb_ids)
        return line_separator.join([field_separator.join(l) for l in lst])


    def get_pfam_details(self, pfam_id):
        '''Returns a dict pdb_id -> chain(s) -> chain and SCOP details.'''

        query = '''
            SELECT DISTINCT scop_node.*, pdb_entry.code, pdb_chain.chain, pdb_chain.is_polypeptide, pdb_entry.description AS ChainDescription, pdb_release.resolution
            FROM `link_pdb`
            INNER JOIN scop_node on node_id=scop_node.id
            INNER JOIN pdb_chain ON pdb_chain_id = pdb_chain.id
            INNER JOIN pdb_release ON pdb_release_id = pdb_release.id
            INNER JOIN pdb_entry ON pdb_entry_id = pdb_entry.id
            WHERE pdb_entry.code=%s'''
        if chain:
            query += ' AND pdb_chain.chain=%s'
            parameters=(pdb_id, chain)
        else:
            parameters = (pdb_id, )
        query += ' ORDER BY release_id DESC'

        leaf_nodes = {}
        results = self.execute_select(query, parameters = parameters)
        if not results:
            return None

        # Only consider the most recent records
        for r in results:
            chain_id = r['chain']
            if (not leaf_nodes.get(chain_id)) or (r['release_id'] > leaf_nodes[chain_id]['release_id']):
                leaf_nodes[chain_id] = r

        d = {}
        for chain_id, details in leaf_nodes.iteritems():

            # Get the details for all chains
            d[chain_id] = dict(
                pdb_id = details['code'],
                chain = details['chain'],
                is_polypeptide = details['is_polypeptide'],
                chain_description = details['ChainDescription'],
                resolution = details['resolution'],
                sunid = details['sunid'],
                sccs = details['sccs'],
                sid = details['sid'],
                scop_release_id = details['release_id']
            )

            for k, v in sorted(self.levels.iteritems()):
                d[chain_id][v] = None

            level, parent_node_id = details['level_id'], details['parent_node_id']

            # Store the top-level description
            d[chain_id][self.levels[level]] = details['description']

            # Wind up the level hierarchy and retrieve the descriptions
            c = 0
            while level > 0 :
                parent_details = self.execute_select('SELECT * FROM scop_node WHERE id=%s', parameters = (parent_node_id,))
                assert(len(parent_details) <= 1)
                if parent_details:
                    parent_details = parent_details[0]
                    level, parent_node_id = parent_details['level_id'], parent_details['parent_node_id']
                    d[chain_id][self.levels[level]] = parent_details['description']
                else:
                    break
                # This should never trigger but just in case...
                c += 1
                if c > 20:
                    raise Exception('There is a logical error in the script or database which may result in an infinite lookup loop.')
        return d

if __name__ == '__main__':
    scopdb = SCOPeDatabase()

    if False:
        colortext.message('\nGetting chain details for 2zxj, chain A')
        colortext.warning(pprint.pformat(scopdb.get_chain_details('2zxj', 'A')))

        colortext.message('\nGetting PDB details for 2zxj')
        colortext.warning(pprint.pformat(scopdb.get_chain_details('2zXJ'))) # the lookup is not case-sensitive w.r.t. PDB ID

        colortext.message('\nGetting dicts for 1ki1 and 1a2c')
        colortext.warning(pprint.pformat(scopdb.get_pdb_list_details(['1ki1', '1a2c'])))

        colortext.message('\nGetting details as CSV for 1ki1 and 1a2c')
        colortext.warning(scopdb.get_pdb_list_details_as_csv(['1ki1', '1a2c']))

        colortext.message('\nGetting PFAM details for PF00013,  PF00708')
        colortext.warning(scopdb.get_pfam_details('PF00013'))

    colortext.message('\nGetting dicts for 107L and 160L')
    colortext.warning(pprint.pformat(scopdb.get_pdb_list_details(['107L', '160L'])))

    #get_pfam_details
    print('\n')