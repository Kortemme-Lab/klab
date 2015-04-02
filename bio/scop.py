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
from tools.bio.pfam import Pfam


installed_database = 'SCOPe205' # rename this to the new database name on updates
installed_database_version = '2.05' # rename this to the new database version on updates


class SCOPeTableCollection(object):

    def __init__(self, SCOPe_database):
        self.SCOPe_database = SCOPe_database
        self.pdb_table = []
        self.pfam_table = []

    def __add__(self, other):
        new_t = SCOPeTableCollection(self.SCOPe_database)
        new_t.pdb_table = self.pdb_table + other.pdb_table
        new_t.pfam_table = self.pfam_table + other.pfam_table
        return new_t

    def add_pdb_line(self, details):
        if details:
            self.pdb_table.append([str(details[f] or '') for f in self.SCOPe_database.pdb_csv_fields])

    def add_pfam_line(self, details):
        if details:
            self.pfam_table.append([str(details[f] or '') for f in self.SCOPe_database.pfam_csv_fields])

    def get_csv_tables(self, field_separator = '\t', line_separator = '\n'):
        d = dict.fromkeys(['PDB', 'Pfam'], None)
        if self.pfam_table:
            d['Pfam'] = line_separator.join([field_separator.join(l) for l in [self.SCOPe_database.pfam_csv_headers] + self.pfam_table])
        if self.pdb_table:
            d['PDB'] = line_separator.join([field_separator.join(l) for l in [self.SCOPe_database.pdb_csv_headers] + self.pdb_table])
        return d

    def get_tables(self):
        d = dict.fromkeys(['PDB', 'Pfam'], None)
        if self.pfam_table:
            d['Pfam'] = [self.SCOPe_database.pfam_csv_headers] + self.pfam_table
        if self.pdb_table:
            d['PDB'] = [self.SCOPe_database.pdb_csv_headers] + self.pdb_table
        return d



class SCOPeDatabase(DatabaseInterface):

    def __init__(self, passwd = None, username = 'anonymous', use_utf=False, fallback_on_failures = True):
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

        self.fallback_on_failures = fallback_on_failures
        self.levels = self.get_SCOPe_levels()
        level_names = [v for k, v in sorted(self.levels.iteritems()) if k != 1] # skip the root level
        search_fields = ['SCOP_sources', 'SCOP_search_fields', 'SCOP_trust_level']
        search_headers = ['SCOP sources', 'Search fields', 'Trustiness']
        self.pfam_api = None

        # Set up CSV fields
        self.pdb_csv_fields = [
            'pdb_id', 'chain', 'is_polypeptide', 'chain_description', 'resolution',
            'sunid', 'sccs', 'sid']
        self.pdb_csv_headers = [
            'PDB id', 'Chain', 'Is polypeptide', 'Description', 'Resolution',
            'sunid', 'sccs', 'sid']
        self.pdb_csv_fields += level_names + search_fields
        self.pdb_csv_headers += level_names + search_headers

        self.pfam_csv_fields = [
            'pfam_accession', 'pfam_name', 'pfam_description', 'pfam_type_description', 'pfam_length',
            'sunid', 'sccs', 'sid', 'SCOP_sources', 'SCOP_search_fields']
        self.pfam_csv_headers = [
            'Pfam accession', 'Name', 'Description', 'Type', 'Length',
            'sunid', 'sccs', 'sid', 'SCOP sources', 'Search fields']
        self.pfam_csv_fields += level_names[:4] + search_fields
        self.pfam_csv_headers += level_names[:4] + search_headers

        assert(len(self.pdb_csv_fields) == len(self.pdb_csv_headers))
        assert(len(self.pfam_csv_fields) == len(self.pfam_csv_headers))


    def get_SCOPe_levels(self):
        d = {}
        results = self.execute_select('SELECT * FROM scop_level ORDER BY id')
        for r in results:
            d[r['id']] = r['description']
        return d


    def get_pfam_api(self):
        if not(self.pfam_api):
            self.pfam_api = Pfam()
        return self.pfam_api


    def get_basic_pdb_chain_information(self, pdb_id, chain_id):
        is_polypeptide, chain_description, resolution = None, None, None
        results = self.execute_select('''
            SELECT DISTINCT pdb_entry.code, pdb_chain.chain, pdb_chain.is_polypeptide, pdb_entry.description AS ChainDescription, pdb_release.resolution
            FROM pdb_chain
            INNER JOIN pdb_release ON pdb_release_id = pdb_release.id
            INNER JOIN pdb_entry ON pdb_entry_id = pdb_entry.id
            WHERE pdb_entry.code=%s AND pdb_chain.chain=%s
            ORDER BY pdb_release.revision_date DESC''', parameters = (pdb_id, chain_id))
        if results:
            is_polypeptide = results[0]['is_polypeptide']
            chain_description = results[0]['ChainDescription']
            resolution = results[0]['resolution']
        return dict(
            pdb_id = pdb_id,
            chain = chain_id,
            is_polypeptide = is_polypeptide,
            chain_description = chain_description,
            resolution = resolution)


    def get_chain_details_by_related_pdb_chains(self, pdb_id, chain_id, pfam_accs):
        ''' Returns a dict of SCOP details using info
            This returns Pfam-level information for a PDB chain i.e. no details on the protein, species, or domain will be returned.
            If there are SCOPe entries for the associated Pfam accession numbers which agree then this function returns
            pretty complete information.
        '''

        return None
        d = self.get_basic_pdb_chain_information(pdb_id, chain_id)
        #sunid = sunid
        #sccs = sccs
        #sid = sid
        #scop_release_id = scop_release_id
        SCOP_sources = 'Pfam + SCOP'
        SCOP_search_fields = 'Pfam + link_pfam.pfam_accession'
        d[chain_id].update(dict(
            sunid = sunid,
            sccs = sccs,
            sid = sid,
            scop_release_id = scop_release_id,
            SCOP_sources = 'Pfam + SCOP',
            SCOP_search_fields = 'Pfam + link_pdb.pdb_chain_id',
            SCOP_trust_level = 3
        ))

        return d


    def get_chain_details_by_pfam(self, pdb_id, chain = None):
        ''' Returns a dict pdb_id -> chain(s) -> chain and SCOP details.
            This returns Pfam-level information for a PDB chain i.e. no details on the protein, species, or domain will be returned.
            If there are SCOPe entries for the associated Pfam accession numbers which agree then this function returns
            pretty complete information.
        '''
        pfam_api = self.get_pfam_api()
        if chain:
            pfam_accs = pfam_api.get_pfam_accession_numbers_from_pdb_chain(pdb_id, chain)
            if pfam_accs:
                pfam_accs = {chain : pfam_accs}
        else:
            pfam_accs = pfam_api.get_pfam_accession_numbers_from_pdb_id(pdb_id)

        if not pfam_accs:
            # There were no associated Pfam accession numbers so we return
            return None

        d = {}
        for chain_id, pfam_acc_set in pfam_accs.iteritems():
            family_details = []
            for pfam_accession in pfam_acc_set:
                family_details.append(self.get_pfam_details(pfam_accession))

            family_details = [f for f in family_details if f]
            if not family_details:
                if self.fallback_on_failures:
                    # Fallback - There were no associated SCOPe entries with the associated Pfam accession numbers so we will
                    #            search all PDB chains associated with those Pfam accession numbers instead
                    d[chain_id] = self.get_chain_details_by_related_pdb_chains(pdb_id, chain_id, pfam_accs)
                else:
                    d[chain_id] = None
                continue

            # Get the common SCOPe fields. For the sccs class, we take the longest common prefix
            sunid = set([f['sunid'] for f in family_details if f['sunid']]) or None
            sccs = set([f['sccs'] for f in family_details if f['sccs']]) or None
            sid = set([f['sid'] for f in family_details if f['sid']]) or None
            scop_release_id = set([f['scop_release_id'] for f in family_details if f['scop_release_id']]) or None
            if sunid:
                if len(sunid) > 1:
                    sunid = None
                else:
                    sunid = sunid.pop()
            if sccs:
                # take the longest common prefix
                sccs = os.path.commonprefix(sccs) or None
            if sid:
                if len(sid) > 1:
                    sid = None
                else:
                    sid = sid.pop()
            if scop_release_id:
                if len(scop_release_id) > 1:
                    scop_release_id = None
                else:
                    scop_release_id = scop_release_id.pop()

            d[chain_id] = self.get_basic_pdb_chain_information(pdb_id, chain_id)
            d[chain_id].update(dict(
                sunid = sunid,
                sccs = sccs,
                sid = sid,
                scop_release_id = scop_release_id,
                SCOP_sources = 'Pfam + SCOP',
                SCOP_search_fields = 'Pfam + link_pfam.pfam_accession',
                SCOP_trust_level = 2
            ))

            for k, v in sorted(self.levels.iteritems()):
                d[chain_id][v] = None

            # Return the lowest common classification over all related Pfam families
            level = 1
            while level < 9:
                classification_level = self.levels[level]
                family_values = set([f[classification_level] for f in family_details]) # allow null fields - if we get a filled in field for one Pfam accession number and a null field for another then we should discount this field entirely and break out
                if len(family_values) == 1:
                    family_value = family_values.pop()
                    if family_value == None:
                        break
                    else:
                        d[chain_id][classification_level] = family_value
                else:
                    break
                level += 1

        return d


    def get_chain_details(self, pdb_id, chain = None):
        ''' Returns a dict pdb_id -> chain(s) -> chain and SCOP details.
            This is the main function for getting details for a PDB chain. If there is an associated SCOPe entry for this
            chain then this function returns the most information.
        '''

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
            if self.fallback_on_failures:
                # Fallback - use any Pfam accession numbers associated with the chain to get partial information
                #            Note: this fallback has another fallback in case none of the Pfam entries exist in SCOPe
                return self.get_chain_details_by_pfam(pdb_id, chain)
            else:
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
                scop_release_id = details['release_id'],
                SCOP_sources = 'SCOP',
                SCOP_search_fields = 'link_pdb.pdb_chain_id',
                SCOP_trust_level = 1
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
        t = SCOPeTableCollection(self)
        d = self.get_pdb_list_details(list(set(pdb_ids)))
        failed_pdb_ids = []
        if d:
            for pdb_id, pdb_details in sorted(d.iteritems()):
                if pdb_details:
                    for chain_id, chain_details in sorted(pdb_details.iteritems()):
                        t.add_pdb_line(chain_details)
                else:
                    failed_pdb_ids.append(pdb_ids)
        return t


    def get_pdb_list_details_as_csv(self, pdb_ids, field_separator = '\t', line_separator = '\n'):
        return self.get_details_as_csv(self.get_pdb_list_details_as_table(pdb_ids), field_separator = field_separator, line_separator = line_separator)


    def get_details_as_csv(self, tbl, field_separator = '\t', line_separator = '\n'):
        return tbl.get_csv_tables(field_separator, line_separator)


    def get_pfam_details(self, pfam_accession):
        '''Returns a dict pdb_id -> chain(s) -> chain and SCOP details.'''

        results = self.execute_select('''
            SELECT DISTINCT scop_node.*, scop_node.release_id AS scop_node_release_id,
            pfam.release_id AS pfam_release_id, pfam.name AS pfam_name, pfam.accession, pfam.description AS pfam_description, pfam.length AS pfam_length,
            pfam_type.description AS pfam_type_description
            FROM `link_pfam`
            INNER JOIN scop_node on node_id=scop_node.id
            INNER JOIN pfam ON link_pfam.pfam_accession = pfam.accession
            INNER JOIN pfam_type ON pfam.pfam_type_id = pfam_type.id
            WHERE pfam.accession=%s ORDER BY scop_node.release_id DESC''', parameters = (pfam_accession,))

        if not results:
            return None

        # Only consider the most recent Pfam releases and most recent SCOP records, giving priority to SCOP revisions over Pfam revisions
        most_recent_record = None
        for r in results:
            accession = r['accession']
            if (not most_recent_record) or (r['scop_node_release_id'] > most_recent_record['scop_node_release_id']):
                most_recent_record = r
            elif r['pfam_release_id'] > most_recent_record['pfam_release_id']:
                most_recent_record = r

        d = dict(
            pfam_accession = most_recent_record['accession'],
            pfam_name = most_recent_record['pfam_name'],
            pfam_description = most_recent_record['pfam_description'],
            pfam_type_description = most_recent_record['pfam_type_description'],
            pfam_length = most_recent_record['pfam_length'],
            pfam_release_id = most_recent_record['pfam_release_id'],
            sunid = most_recent_record['sunid'],
            sccs = most_recent_record['sccs'],
            sid = most_recent_record['sid'],
            scop_release_id = most_recent_record['scop_node_release_id'],
            SCOP_sources = 'SCOP',
            SCOP_search_fields = 'link_pfam.pfam_accession',
            SCOP_trust_level = 1
        )

        for k, v in sorted(self.levels.iteritems()):
            d[v] = None

        level, parent_node_id = most_recent_record['level_id'], most_recent_record['parent_node_id']

        # Store the top-level description
        d[self.levels[level]] = most_recent_record['description']

        # Wind up the level hierarchy and retrieve the descriptions
        c = 0
        while level > 0 :
            parent_details = self.execute_select('SELECT * FROM scop_node WHERE id=%s', parameters = (parent_node_id,))
            assert(len(parent_details) <= 1)
            if parent_details:
                parent_details = parent_details[0]
                level, parent_node_id = parent_details['level_id'], parent_details['parent_node_id']
                d[self.levels[level]] = parent_details['description']
            else:
                break
            # This should never trigger but just in case...
            c += 1
            if c > 20:
                raise Exception('There is a logical error in the script or database which may result in an infinite lookup loop.')

        assert(d['Protein'] == d['Species'] == d['PDB Entry Domain'] == None)
        return d


    def get_pfam_list_details(self, pfam_accs):
        d = {}
        for pfam_accession in pfam_accs:
            results = self.get_pfam_details(pfam_accession)
            d[pfam_accession] = results
        return d


    def get_pfam_list_details_as_table(self, pfam_accs):
        t = SCOPeTableCollection(self)
        d = self.get_pfam_list_details(pfam_accs)
        if d:
            for pfam_accession, pfam_details in sorted(d.iteritems()):
                if pfam_details:
                    t.add_pfam_line(pfam_details)
        return t


    def get_pfam_list_details_as_csv(self, pfam_accs, field_separator = '\t', line_separator = '\n'):
        #, field_separator = '\t', line_separator = '\n'):
        return self.get_details_as_csv(self.get_pfam_list_details_as_table(pfam_accs), field_separator = field_separator, line_separator = line_separator)


if __name__ == '__main__':
    scopdb = SCOPeDatabase()

    if True:
        colortext.message('\nGetting chain details for 2zxj, chain A')
        colortext.warning(pprint.pformat(scopdb.get_chain_details('2zxj', 'A')))

        colortext.message('\nGetting PDB details for 2zxj')
        colortext.warning(pprint.pformat(scopdb.get_chain_details('2zXJ'))) # the lookup is not case-sensitive w.r.t. PDB ID

        colortext.message('\nGetting dicts for 1ki1 and 1a2c')
        colortext.warning(pprint.pformat(scopdb.get_pdb_list_details(['1ki1', '1a2c'])))

        colortext.message('\nGetting details as CSV for 1ki1 and 1a2c')
        colortext.warning(scopdb.get_pdb_list_details_as_csv(['1ki1', '1a2c']))

        colortext.message('\nGetting PFAM details for PF01035,  PF01833')
        colortext.warning(pprint.pformat(scopdb.get_pfam_details('PF01035')))

        colortext.message('\nGetting details as CSV for 1ki1 and 1a2c')
        colortext.warning(scopdb.get_pdb_list_details_as_csv(['1ki1', '1a2c']))

        colortext.message('\nGetting details as CSV for 1ki1 and 1a2c')
        colortext.warning(scopdb.get_pfam_list_details_as_csv(['PF01035', 'PF01833'])['Pfam'])

        # get_chain_details_by_pfam cases
        # This case tests what happens when there is no PDB chain entry in SCOPe - we should find the Pfam entry instead and look that up
        colortext.message('\nGetting chain details for 3GVA')
        colortext.warning(pprint.pformat(scopdb.get_chain_details('3GVA')))

        colortext.message('\nGetting chain details for 3GVA, chain A')
        colortext.warning(pprint.pformat(scopdb.get_chain_details('3GVA', 'A')))
        assert(scopdb.get_chain_details('3GVA', 'A')['A']['SCOP_trust_level'] == 2)

    # get_chain_details_by_related_pdb_chains cases
    # This case tests what happens when there is no PDB chain entry in SCOPe and the associated Pfam entries also have no
    # SCOPe entries but their associated PDB chains do
    # 2EVB, 2PND, 2QLC, 3FYM
    colortext.message('\nGetting chain details for 2EVB')
    colortext.warning(pprint.pformat(scopdb.get_chain_details('2EVB')))
    #assert(scopdb.get_chain_details('2EVB', 'A')['A']['SCOP_trust_level'] == 3)


    print('\n')