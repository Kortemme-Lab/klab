#!/usr/bin/python2.4
# encoding: utf-8
"""
scop.py
Functions for interacting with the SCOPe database.

Created by Shane O'Connor 2015.
"""

import sys, os
import pprint
import traceback

if __name__ == "__main__":
    sys.path.insert(0, "../../")
from klab.db.mysql import DatabaseInterface
from klab import colortext
from klab.fs.fsio import read_file, write_file
from klab.bio.pfam import Pfam
from klab.bio.sifts import SIFTS
from klab.bio.pdb import PDB

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

    def __init__(self, passwd = None, username = 'anonymous', use_utf=False, fallback_on_failures = True, cache_dir = '/kortemmelab/data/oconchus/SIFTS'):
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

        self.cache_dir = cache_dir
        self.fallback_on_failures = fallback_on_failures
        self.levels = self.get_SCOPe_levels()
        del self.levels[1] # remove the root level

        level_names = [v for k, v in sorted(self.levels.iteritems()) if k != 1] # skip the root level
        search_fields = ['SCOPe_sources', 'SCOPe_search_fields', 'SCOPe_trust_level']
        search_headers = ['SCOPe sources', 'Search fields', 'Trustiness']
        self.pfam_api = None
        self.SIFTS = {}

        # Set up CSV fields
        self.pdb_csv_fields = [
            'pdb_id', 'chain', 'is_polypeptide', 'chain_description', 'resolution', 'pdbe_residue_range',
            'sunid', 'sccs', 'sid']
        self.pdb_csv_headers = [
            'PDB id', 'Chain', 'Is polypeptide', 'Description', 'Resolution', 'PDBe residues',
            'sunid', 'sccs', 'sid']
        self.pdb_csv_fields += level_names + search_fields
        self.pdb_csv_headers += level_names + search_headers

        self.pfam_csv_fields = [
            'pfam_accession', 'pfam_name', 'pfam_description', 'pfam_type_description', 'pfam_length',
            'sunid', 'sccs', 'sid', 'SCOPe_sources', 'SCOPe_search_fields']
        self.pfam_csv_headers = [
            'Pfam accession', 'Name', 'Description', 'Type', 'Length',
            'sunid', 'sccs', 'sid', 'SCOPe sources', 'Search fields']
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


    def get_sifts(self, pdb_id, fail_on_error = False, require_uniprot_residue_mapping = False):
        try:
            pdb_id = pdb_id.lower()
            if self.SIFTS.get(pdb_id):
                return self.SIFTS[pdb_id]
            self.SIFTS[pdb_id] = SIFTS.retrieve(pdb_id, cache_dir = self.cache_dir, acceptable_sequence_percentage_match = 70.0, require_uniprot_residue_mapping = require_uniprot_residue_mapping)
            return self.SIFTS[pdb_id]
        except Exception, e:
            colortext.error('An exception happened retrieving the SIFTS file for %s: "%s". Ignoring this exception and continuing on...' % (pdb_id, str(e)))
            colortext.error(traceback.format_exc())
            if fail_on_error:
                raise
            return None


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


    def get_common_fields(self, family_details):
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
            if sccs and sccs.endswith('.'):
                sccs = sccs[:-1]
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
        return dict(
            sunid = sunid,
            sccs = sccs,
            sid = sid,
            scop_release_id = scop_release_id,
        )


    def get_common_hierarchy(self, family_details):
        d = {}
        level = 2
        while level < 9:
            classification_level = self.levels[level]
            family_values = set([f[classification_level] for f in family_details]) # allow null fields - if we get a filled in field for one Pfam accession number and a null field for another then we should discount this field entirely and break out
            if len(family_values) == 1:
                family_value = family_values.pop()
                if family_value == None:
                    break
                else:
                    d[classification_level] = family_value
            else:
                break
            level += 1
        return d


    def get_chain_details_by_related_pdb_chains(self, pdb_id, chain_id, pfam_accs):
        ''' Returns a dict of SCOPe details using info
            This returns Pfam-level information for a PDB chain i.e. no details on the protein, species, or domain will be returned.
            If there are SCOPe entries for the associated Pfam accession numbers which agree then this function returns
            pretty complete information.
        '''

        if not pfam_accs:
            return None

        associated_pdb_chains = set()
        pfam_api = self.get_pfam_api()
        for pfam_acc in pfam_accs:
            associated_pdb_chains = associated_pdb_chains.union(pfam_api.get_pdb_chains_from_pfam_accession_number(pfam_acc))

        hits = []
        #class_count = {}

        pfam_scop_mapping = {}
        for pdb_chain_pair in associated_pdb_chains:
            ass_pdb_id, ass_chain_id = pdb_chain_pair[0], pdb_chain_pair[1]
            hit = self.get_chain_details(ass_pdb_id, chain = ass_chain_id, internal_function_call = True, pfam_scop_mapping = pfam_scop_mapping)
            if hit and hit.get('chains'):
                assert(len(hit['chains']) == 1)
                hits.append(hit['chains'][ass_chain_id])
                #for k, v in hit.iteritems():
                    #class_count[v['sccs']] = class_count.get(v['sccs'], 0)
                    #class_count[v['sccs']] += 1
                    #print(' %s, %s: %s' % (v['pdb_id'], k, v['sccs']))
        #pprint.pprint(class_count)
        allowed_scop_domains = map(int, map(set.intersection, pfam_scop_mapping.values())[0])
        allowed_scop_domains = list(set((allowed_scop_domains or []) + (self.get_sunid_for_pfam_accs(pfam_accs) or [])))


        filtered_hits = []
        print(pfam_accs)
        print(allowed_scop_domains)
        print('%d hits' % len(hits))
        for hit in hits:
            domains_to_ignore = []
            for k, v in hit['domains'].iteritems():
                if v['sunid'] in allowed_scop_domains:
                    filtered_hits.append(v)
        print('%d filtered_hits' % len(filtered_hits))

        if not filtered_hits:
            return None

        d = self.get_basic_pdb_chain_information(pdb_id, chain_id)
        d.update(self.get_common_fields(filtered_hits))
        d.update(dict(
            SCOPe_sources = 'Pfam + SCOPe',
            SCOPe_search_fields = 'Pfam + link_pdb.pdb_chain_id',
            SCOPe_trust_level = 3
        ))
        # Add the lowest common classification over all related Pfam families
        for k, v in sorted(self.levels.iteritems()):
            d[v] = None
        d.update(dict(self.get_common_hierarchy(filtered_hits)))
        return d


    def get_chain_details_by_pfam(self, pdb_id, chain = None):
        ''' Returns a dict pdb_id -> chain(s) -> chain and SCOPe details.
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
                    d[chain_id] = self.get_chain_details_by_related_pdb_chains(pdb_id, chain_id, pfam_accs.get(chain_id))
                else:
                    d[chain_id] = None
                continue

            # Get the common SCOPe fields. For the sccs class, we take the longest common prefix


            d[chain_id] = self.get_basic_pdb_chain_information(pdb_id, chain_id)
            d[chain_id].update(self.get_common_fields(family_details))
            d[chain_id].update(dict(
                SCOPe_sources = 'Pfam + SCOPe',
                SCOPe_search_fields = 'Pfam + link_pfam.pfam_accession',
                SCOPe_trust_level = 2
            ))
            # Add the lowest common classification over all related Pfam families
            for k, v in sorted(self.levels.iteritems()):
                d[chain_id][v] = None
            d[chain_id].update(dict(self.get_common_hierarchy(family_details)))
        return d


    def get_list_of_pdb_chains(self, pdb_id):
        results = self.execute_select('''
            SELECT DISTINCT pdb_chain.chain, pdb_release.id as release_id
            FROM pdb_chain
            INNER JOIN pdb_release ON pdb_release_id = pdb_release.id
            INNER JOIN pdb_entry ON pdb_entry_id = pdb_entry.id
            WHERE pdb_entry.code=%s''', parameters = (pdb_id,))
        if results:
            max_release_id = max([r['release_id'] for r in results])
            return set([r['chain'] for r in results if r['release_id'] == max_release_id])
        return None



    def get_chain_details(self, pdb_id, chain = None, internal_function_call = False, pfam_scop_mapping = {}):
        ''' Returns a dict pdb_id -> chain(s) -> chain and SCOPe details.
            This is the main function for getting details for a PDB chain. If there is an associated SCOPe entry for this
            chain then this function returns the most information.
            internal_function_call is used to prevent potential infinite loops
        '''

        query = '''
            SELECT DISTINCT scop_node.id AS scop_node_id, scop_node.*, pdb_entry.code, pdb_chain_id, pdb_chain.chain, pdb_chain.is_polypeptide, pdb_entry.description AS ChainDescription, pdb_release.resolution
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

        results = self.execute_select(query, parameters = parameters)
        if not results:
            if self.fallback_on_failures and not internal_function_call:
                # Fallback - use any Pfam accession numbers associated with the chain to get partial information
                #            Note: this fallback has another fallback in case none of the Pfam entries exist in SCOPe
                searched_deeper = True
                return self.get_chain_details_by_pfam(pdb_id, chain)
            else:
                return None

        # I am making the assumption here that sids are consistent through releases i.e. that if d1aqt_1 is used in release
        # 3 then it will be used for any other releases where the domain is named
        sid_map = {}
        for r in results:
            sid = r['sid']
            c_id = r['chain']
            if not(sid_map.get(sid)) or sid_map[sid] == ' ':
                sid_map[sid] = c_id
        chain_to_sid_map = {}
        for k, v in sid_map.iteritems():
            chain_to_sid_map[v] = chain_to_sid_map.get(v, set())
            chain_to_sid_map[v].add(k)

        leaf_node_chains = set()
        searched_deeper = False
        if pdb_id and chain:
            leaf_node_chains.add(chain)
        else:
            pdb_chain_ids = self.get_list_of_pdb_chains(pdb_id)
            if pdb_chain_ids:
                leaf_node_chains = pdb_chain_ids
            else:
                return None

        leaf_nodes = {}
        for c in leaf_node_chains:
            if c in chain_to_sid_map:
                for sid in chain_to_sid_map[c]:
                    leaf_nodes[(c, sid)] = None


        # Only consider the most recent records
        for r in results:
            chain_id = r['chain']
            sid = r['sid']
            k = (chain_id, sid)
            if (not leaf_nodes.get(k)) or (r['release_id'] > leaf_nodes[k]['release_id']):
                leaf_nodes[k] = r

        # Older revisions of SCOPe have blank chain IDs for some records while newer revisions have the chain ID
        # The best solution to avoid redundant results seems to be to remove all blank chain records if at least one
        # more recent named chain exists. There could be some nasty cases - we only keep the most recent unnamed chain
        # but this may correspond to many chains if the PDB has multiple chains since we only look at the chain ID.
        # I think that it should be *unlikely* that we will have much if any bad behavior though.
        for k1, v2 in leaf_nodes.iteritems():
            if k1[0] == ' ':
                release_id_of_blank_record = leaf_nodes[k1]['release_id']
                for k2, v2 in leaf_nodes.iteritems():
                    if k2[0] != ' ':
                        assert(k2[0].isalpha() and len(k2[0]) == 1)
                        if v2['release_id'] > release_id_of_blank_record:
                            del leaf_nodes[k1] # we are modifying a structure while iterating over it but we break immediately afterwards
                            break

        d = {}
        for chain_sid_pair, details in leaf_nodes.iteritems():
            chain_id = chain_sid_pair[0]
            sid = chain_sid_pair[1]
            if sid.strip() == '':
                colortext.warning('FOUND AN EMPTY SID FIELD')
            assert(sid == details['sid'])

            # Get the details for all chains
            if details:

                if d.get('resolution'):
                    assert(d['resolution'] == details['resolution'])
                else:
                    d['resolution'] = details['resolution']

                d['chains'] = d.get('chains', {})
                if d['chains'].get(chain_id):
                    assert(d['chains'][chain_id]['is_polypeptide'] == details['is_polypeptide'])
                    assert(d['chains'][chain_id]['chain_description'] == details['ChainDescription'])
                else:
                    d['chains'][chain_id] = {}
                    d['chains'][chain_id]['is_polypeptide'] = details['is_polypeptide']
                    d['chains'][chain_id]['chain_description'] = details['ChainDescription']

                d['chains'][chain_id]['domains'] = d['chains'][chain_id].get('domains', {})
                domain_information = dict(
                    #pdb_id = details['code'],
                    #chain = details['chain'],
                    #is_polypeptide = details['is_polypeptide'],
                    #chain_description = details['ChainDescription'],
                    sunid = details['sunid'],
                    sccs = details['sccs'],
                    sid = details['sid'],
                    scop_release_id = details['release_id'],
                    SCOPe_sources = 'SCOPe',
                    SCOPe_search_fields = 'link_pdb.pdb_chain_id',
                    SCOPe_trust_level = 1
                )

                for k, v in sorted(self.levels.iteritems()):
                    domain_information[v] = None

                pfam = None
                level, parent_node_id = details['level_id'], details['parent_node_id']
                pfam = pfam or self.get_pfam_for_node(details['scop_node_id'])

                # Store the top-level description
                domain_information[self.levels[level]] = details['description']

                # Wind up the level hierarchy and retrieve the descriptions
                c = 0
                while level > 2:
                    parent_details = self.execute_select('SELECT * FROM scop_node WHERE id=%s', parameters = (parent_node_id,))
                    assert(len(parent_details) <= 1)
                    if parent_details:
                        parent_details = parent_details[0]
                        level, parent_node_id = parent_details['level_id'], parent_details['parent_node_id']
                        pfam = pfam or self.get_pfam_for_node(parent_details['id'])
                        domain_information[self.levels[level]] = parent_details['description']
                    else:
                        break
                    # This should never trigger but just in case...
                    c += 1
                    if c > 20:
                        raise Exception('There is a logical error in the script or database which may result in an infinite lookup loop.')
                domain_information['Pfam'] = pfam

                # Fill in the residue range data
                domain_information['pdbe_residue_range'] = None
                sifts_object = self.get_sifts(pdb_id)
                if sifts_object:
                    colortext.message(pdb_id)
                    region_mapping = sifts_object.region_mapping
                    ps_map = sifts_object.pfam_scop_mapping or {}
                    for k, v in ps_map.iteritems():
                        pfam_scop_mapping[k] = pfam_scop_mapping.get(k, set())
                        pfam_scop_mapping[k] = pfam_scop_mapping[k].union(v.get_matches('SCOP'))

                    residue_ranges = region_mapping.get(chain_id, {}).get('SCOP', {}).get(str(details['sunid']))
                    if residue_ranges:
                        residue_ranges = ', '.join(['%d-%d' % (t[0], t[1]) for t in residue_ranges])
                    domain_information['pdbe_residue_range'] = residue_ranges

                d['chains'][chain_id]['domains'][sid] = domain_information

            else:
                if self.fallback_on_failures and not(internal_function_call) and not(searched_deeper):
                    fallback_results = self.get_chain_details_by_pfam(pdb_id, chain_id)
                    if fallback_results and fallback_results.get(chain_id):
                        domain_information = fallback_results[chain_id]
        return d


    def get_pfam_for_node(self, scop_node_id):
        results = self.execute_select('SELECT pfam_accession FROM link_pfam WHERE node_id=%s', parameters = (scop_node_id,))
        if results:
            return results[0]['pfam_accession']
        return None


    def get_sunid_for_pfam_accs(self, pfam_accs):
        sunids = set()
        for pfam_acc in pfam_accs:
            results = self.execute_select('SELECT scop_node.sunid FROM link_pfam INNER JOIN scop_node ON node_id=scop_node.id WHERE pfam_accession=%s', parameters = (pfam_acc,))
            if results:
                sunids.add(results[0]['sunid'])
        return list(sunids) or None


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
        '''Returns a dict pdb_id -> chain(s) -> chain and SCOPe details.'''

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

        # Only consider the most recent Pfam releases and most recent SCOPe records, giving priority to SCOPe revisions over Pfam revisions
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
            SCOPe_sources = 'SCOPe',
            SCOPe_search_fields = 'link_pfam.pfam_accession',
            SCOPe_trust_level = 1
        )

        for k, v in sorted(self.levels.iteritems()):
            d[v] = None

        level, parent_node_id = most_recent_record['level_id'], most_recent_record['parent_node_id']

        # Store the top-level description
        d[self.levels[level]] = most_recent_record['description']

        # Wind up the level hierarchy and retrieve the descriptions
        c = 0
        while level > 2 :
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


    def determine_SCOPe_class_of_pdb_residue(self, pdb_id, pdb_chain_id, pdb_residue_id):
        sifts_object = self.get_sifts(pdb_id, fail_on_error = True, require_uniprot_residue_mapping = False)
        scop_class = None
        if sifts_object:
            PDBeResidueID = sifts_object.atom_to_seqres_sequence_maps.get(pdb_chain_id, {}).get(PDB.ChainResidueID2String(pdb_chain_id, pdb_residue_id))
            if PDBeResidueID:
                scop_hits = set()
                scop_regions = sifts_object.region_mapping.get(pdb_chain_id, {}).get('SCOP')
                if scop_regions:
                    for sunid, ranges in scop_regions.iteritems():
                        for r in ranges:
                            assert(r[0] <= r[1])
                            if r[0] <= PDBeResidueID <= r[1]:
                                scop_hits.add(sunid)
                    if scop_hits:
                        assert(len(scop_hits) == 1)
                        scop_class = self.execute_select('SELECT sccs FROM scop_node WHERE sunid=%s', parameters = (scop_hits.pop(),))
                        if scop_class:
                            scop_class = scop_class[0]['sccs']

        return scop_class


    def determine_Pfam_class_of_pdb_residue(self, pdb_id, pdb_chain_id, pdb_residue_id):
        sifts_object = self.get_sifts(pdb_id, fail_on_error = True, require_uniprot_residue_mapping = False)
        pfam_accs = []
        if sifts_object:
            PDBeResidueID = sifts_object.atom_to_seqres_sequence_maps.get(pdb_chain_id, {}).get(PDB.ChainResidueID2String(pdb_chain_id, pdb_residue_id))
            if PDBeResidueID:
                pfam_hits = set()
                pfam_regions = sifts_object.region_mapping.get(pdb_chain_id, {}).get('Pfam')
                if pfam_regions:
                    for pfam_acc, ranges in pfam_regions.iteritems():
                        for r in ranges:
                            assert(r[0] <= r[1])
                            if r[0] <= PDBeResidueID <= r[1]:
                                pfam_hits.add(pfam_acc)
                    if pfam_hits:
                        pfam_accs = sorted(pfam_hits)

        return pfam_accs




def __pick_cases_for_manual_inspection():
    import json
    import random

    scopdb = SCOPeDatabase()
    datasets = [
      '/kortemmelab/shared/benchmarks/ddg/input/json/potapov.json',
      '/kortemmelab/shared/benchmarks/ddg/input/json/kellogg.json',
      '/kortemmelab/shared/benchmarks/ddg/input/json/alascan-gpk.json',
      '/kortemmelab/shared/benchmarks/ddg/input/json/curatedprotherm.json',
      '/kortemmelab/shared/benchmarks/ddg/input/json/guerois.json'
    ]
    for dataset in datasets:
        data = json.loads(read_file(dataset))['data']
        c = 1

        random.seed(1357986420)
        random_checks = [random.randint(0, len(data) - 1) for i in range(5)]
        for n in random_checks:
            d = data[n]
            for m in d['Mutations']:
                if dataset == '/kortemmelab/shared/benchmarks/ddg/input/json/curatedprotherm.json':
                    if c in [2338, 2339, 2385, 2435, 2436, 2795, 2796, 2812, 2813, 2814]:
                        continue
                    if d['PDBFileID'] == '2IMM':
                        continue
                s = 'Mutation #%d: %s, chain %s, residue %s - ' % (c, d['PDBFileID'], m['Chain'], m['ResidueID'])
                try:
                    sys.stdout.flush()
                    sccs = scopdb.determine_SCOPe_class_of_pdb_residue(d['PDBFileID'], m['Chain'], m['ResidueID'])
                    pfam_accs = scopdb.determine_Pfam_class_of_pdb_residue(d['PDBFileID'], m['Chain'], m['ResidueID'])
                    if sccs:
                        s += colortext.make(' - %s' % sccs, 'cyan')
                    else:
                        s += colortext.make(' - %s' % sccs, 'yellow')

                    if pfam_accs:
                        s += colortext.make(', %s' % ', '.join(pfam_accs), 'green')
                    print(s)
                except Exception, e:
                    print(s)
                    colortext.error(str(e))
                    colortext.error(traceback.format_exc())
            c += 1


def __generate_benchmark_data():
    import json

    headers = 'Pfam ID,Pfam Name,Total # of sequences,PDB ID,Amino acid length,SCOP class'.split(',')
    lines = [l for l in read_file('/kortemmelab/shared/benchmarks/covariation/input/domains.csv').split('\n') if l.strip() and not(l.startswith('#'))]
    dataset_json = {
        "information": "\nThis dataset was taken from Table 1 in the Ollikainen and Kortemme paper [1], doi: 10.1371/journal.pcbi.1003313.",
        "references": {
            "1": "PMID:24244128"
        },
        "version": "This dataset was last updated on 2015-04-07.",
        "domains": []
    }
    for l in lines:
        tokens = l.split(',')
        assert(len(tokens) == len(headers))
        d = {}
        for x in range(len(headers)):
            d[headers[x]] = tokens[x]
        dataset_json["domains"].append(d)

    print(json.dumps(dataset_json, indent=4, sort_keys=True))


    data = write_file('/kortemmelab/shared/benchmarks/covariation/input/domains.json', json.dumps(dataset_json, indent=4, sort_keys=True))

    sys.exit(0)

    scopdb = SCOPeDatabase()
    datasets = [
      '/kortemmelab/shared/benchmarks/ddg/input/json/potapov.json',
      '/kortemmelab/shared/benchmarks/ddg/input/json/kellogg.json',
      '/kortemmelab/shared/benchmarks/ddg/input/json/alascan-gpk.json',
      '/kortemmelab/shared/benchmarks/ddg/input/json/curatedprotherm.json',
      '/kortemmelab/shared/benchmarks/ddg/input/json/guerois.json'
    ]
    for dataset in datasets:
        dataset_json = json.loads(read_file(dataset))
        data = dataset_json['data']
        c = 1
        skipped = 0

        scss_breakdown = dict(
            a = ['All alpha proteins', 0],
            b = ['All beta proteins', 0],
            c = ['Alpha and beta proteins (a/b)', 0],
            d = ['Alpha and beta proteins (a+b)', 0],
            e = ['Multi-domain proteins (alpha and beta)', 0],
            f = ['Membrane and cell surface proteins and peptides', 0],
            g = ['Small proteins', 0],
            h = ['Coiled-coil proteins', 0],
            i = ['Low resolution protein structures', 0],
            j = ['Peptides', 0],
            k = ['Designed proteins', 0]
        )
        for d in data:
            for m in d['Mutations']:
                s = 'Mutation #%d: %s, chain %s, residue %s - ' % (c, d['PDBFileID'], m['Chain'], m['ResidueID'])
                try:
                    sys.stdout.flush()
                    sccs = scopdb.determine_SCOPe_class_of_pdb_residue(d['PDBFileID'], m['Chain'], m['ResidueID'])
                    pfam_accs = scopdb.determine_Pfam_class_of_pdb_residue(d['PDBFileID'], m['Chain'], m['ResidueID'])
                    if sccs:
                        s += colortext.make(' - %s' % sccs, 'cyan')
                        top_class = sccs.split('.')[0]
                        scss_breakdown[top_class][1] += 1
                    else:
                        s += colortext.make(' - %s' % sccs, 'yellow')
                    if pfam_accs:
                        s += colortext.make(', %s' % ', '.join(pfam_accs), 'green')
                    m[u'SCOP class'] = sccs
                    if pfam_accs:
                        m[u'Pfam domains'] = ', '.join(pfam_accs)
                    else:
                        m[u'Pfam domains'] = None
                    print(s)
                except Exception, e:
                    print(s)
                    colortext.error(str(e))
                    colortext.error(traceback.format_exc())
                    raise
            c += 1
        print(len(data))
        keys_to_delete = [k for k in scss_breakdown.keys() if scss_breakdown[k][1] == 0]
        total_count = sum([scss_breakdown[k][1] for k in scss_breakdown.keys()])
        print(total_count)
        for k in keys_to_delete:
            del scss_breakdown[k]
        colortext.warning(pprint.pformat(scss_breakdown))
        print('skipped', skipped)

        data = write_file(dataset + '.new', json.dumps(dataset_json, indent=4, sort_keys=True))



def __test():

    scopdb = SCOPeDatabase()
    if False:

        # Outstanding issue 1
        # PDB chains with multiple domains: only one domain returned.
        # 1AQT chain A has a b.93.1.1 domain (residues 2-86) and a a.2.10.1 domain (residues 87-136). I only return the a.2.10.1 at present.
        #colortext.message('\nGetting PDB details for 1AQT, chain A')
        #colortext.warning(pprint.pformat(scopdb.get_chain_details('1AQT', 'A')))

        # Outstanding issue 2
        # For 3FYM, the mapping between PDB chains and Pfam accession numbers I am using (SIFTS) only has the mapping:
        # 3fym A -> PF13413 whereas the RCSB PDB website reports two other domains, PF12844 (a.35.1.3) and
        # PF01381 (a.35.1 or a.4.14.1). I need to use more information than just relying on SIFTS to be complete.
        # This should be fixed after issue 1 since we should return results for both PF12844 and PF01381.
        #colortext.message('\nGetting PDB details for PF13413')
        #colortext.warning(pprint.pformat(scopdb.get_chain_details_by_related_pdb_chains('3FYM', 'A', set(['PF13413']))))
        #colortext.message('\nGetting PDB details for PF12844')
        #colortext.warning(pprint.pformat(scopdb.get_chain_details_by_related_pdb_chains('3FYM', 'A', set(['PF12844']))))
        colortext.message('\nGetting PDB details for PF01381')
        colortext.warning(pprint.pformat(scopdb.get_chain_details_by_related_pdb_chains('3FYM', 'A', set(['PF01381']))))

        # todo: have a look at this case (scopdb.get_chain_details_by_related_pdb_chains('3FYM', 'A', set(['PF01381']))) to make sure that the results make sense
        # The accession numbers set(['PF01381'])
        # maps to sunids
        # [127500, 127502, 127504, 127506, 127508, 127510, 127512, 127514, 127516, 127518, 127520, 127408, 127522, 127524, 127526, 127528, 127530, 125874, 127536, 127538, 127540, 127542, 17035, 17023, 17024, 17025, 17026, 17027, 17028, 17029, 17030, 17031, 17032, 17033, 17034, 149783, 17036, 17037, 17038, 17039, 17040, 17041, 17042, 147604, 147605, 17064, 97513, 97514, 140526L, 118551, 118552, 128835, 128837, 128839, 128841, 128843, 128845, 121704, 122729, 122730, 116592, 108929, 108931, 108933, 108935, 135560, 108937, 135562, 108939, 108941, 135566, 108943, 105888, 125872, 127410, 125876, 125878, 125880, 125882, 125884, 125886, 125888, 125890, 125892, 125894, 125896, 125898, 127435, 127437, 127439, 127441, 127443, 127445, 127447, 127449, 127451, 127453, 127455, 127457, 151525, 151526]
        # These are of types a.35.1 or a.4.14 so we return a. Does this make sense?


        colortext.message('\nGetting chain details for 2zxj, chain A')
        colortext.warning(pprint.pformat(scopdb.get_chain_details('2zxj', 'A')))

        colortext.message('\nGetting PDB details for 2zxj')
        colortext.warning(pprint.pformat(scopdb.get_chain_details('2zXJ'))) # the lookup is not case-sensitive w.r.t. PDB ID

        colortext.message('\nGetting dicts for 1ki1 and 1a2p')
        colortext.warning(pprint.pformat(scopdb.get_pdb_list_details(['1ki1', '1a2p'])))

    if False:
        colortext.message('\nGetting details as CSV for 1ki1 and 1a2p')
        colortext.warning(scopdb.get_pdb_list_details_as_csv(['1ki1', '1a2p']))

    colortext.message('\nGetting PFAM details for PF01035,  PF01833')
    colortext.warning(pprint.pformat(scopdb.get_pfam_details('PF01035')))

    if False:
        colortext.message('\nGetting details as CSV for 1ki1 and 1a2p')
        colortext.warning(scopdb.get_pdb_list_details_as_csv(['1ki1', '1a2p']))

        colortext.message('\nGetting details as CSV for 1ki1 and 1a2p')
        colortext.warning(scopdb.get_pfam_list_details_as_csv(['PF01035', 'PF01833'])['Pfam'])

    # get_chain_details_by_pfam cases
    # This case tests what happens when there is no PDB chain entry in SCOPe - we should find the Pfam entry instead and look that up
    colortext.message('\nGetting chain details for 3GVA')
    colortext.warning(pprint.pformat(scopdb.get_chain_details('3GVA')))

    colortext.message('\nGetting chain details for 3GVA, chain A')
    colortext.warning(pprint.pformat(scopdb.get_chain_details('3GVA', 'A')))
    assert(scopdb.get_chain_details('3GVA', 'A')['A']['SCOPe_trust_level'] == 2)

    # get_chain_details_by_related_pdb_chains cases
    # This case tests what happens when there is no PDB chain entry in SCOPe and the associated Pfam entries also have no
    # SCOPe entries but their associated PDB chains do. In these cases, there is not enough common information e.g. 2EVB
    # resolves to b.84.1.1, b.84.1.0, and a.9.1.0 which have no common root whereas 2PND resolves to b.1.1.2, b.1.1.1,
    # b.1.1.0, and i.6.1.1.
    colortext.message('\nGetting chain details for 2EVB, 2PND, 2QLC, 3FYM')
    colortext.warning(pprint.pformat(scopdb.get_pdb_list_details(['2EVB', '2PND', '2QLC', '3FYM'])))
    assert(scopdb.get_chain_details('2EVB', 'A')['A']['SCOPe_trust_level'] == 3)
    assert(scopdb.get_chain_details('2PND', 'A')['A']['SCOPe_trust_level'] == 3)

    # However, 1a2c tests get_chain_details_by_related_pdb_chains since chain I needs to drop down to this level in order
    # to get results
    colortext.message('\nGetting chain details for 1a2c')
    colortext.warning(pprint.pformat(scopdb.get_chain_details('1a2c')))
    assert(scopdb.get_chain_details('1a2c', 'H')['H']['SCOPe_trust_level'] == 1)
    assert(scopdb.get_chain_details('1a2c', 'I')['I']['SCOPe_trust_level'] == 3)

    print('\n')




if __name__ == '__main__':
    #__test()
    __generate_benchmark_data()