#!/usr/bin/python
# encoding: utf-8
"""
uniprot.py
For functions relating to getting data from UniProt.

Created by Shane O'Connor 2013
"""

import sys
import os
import string
import re
import urllib,urllib2
try:
    import json as simplejson
except:
    import simplejson
from xml.dom.minidom import parse, parseString

if __name__ == '__main__':
    sys.path.insert(0, "../..")
from klab.comms.http import get as http_get
from klab import colortext
from klab.hash import CRC64
from klab.fs.fsio import read_file, write_file
from klab.bio.uniprot_patches import * # UniParcMergedSubmittedNamesRemap, UniParcMergedRecommendedNamesRemap, clashing_subsections_for_removal, subsections_for_addition, AC_entries_where_we_ignore_the_subsections, overlapping_subsections_for_removal, PDBs_marked_as_XRay_with_no_resolution


class ProteinSubsectionOverlapException(colortext.Exception): pass
class UniParcEntryStandardizationException(colortext.Exception): pass


def get_obsolete_acc_to_uniparc(acc):
    ''' Tries to determine the UniParc ID for obsolete ACCs which are not returned using uniprot_map.

        :param acc: The UniProt accession number.
        :return: The corresponding UniParc ID.

        Warning: This is a fragile function as the underlying website generation or URL could change.
    '''
    contents = http_get('www.uniprot.org/uniparc/?query={0}'.format(acc))
    mtchs = re.findall(r'"UPI[A-Z0-9]+?"', contents, re.DOTALL)
    uniparc_id = set([m[1:-1] for m in mtchs])
    if len(uniparc_id) == 1:
        return uniparc_id.pop()
    elif len(uniparc_id) > 1:
        raise Exception('Multiple UPI identifiers found.')
    return None


def uniprot_map(from_scheme, to_scheme, list_of_from_ids, cache_dir = None, silent = True):
    '''Maps from one ID scheme to another using the UniProt service.
        list_of_ids should be a list of strings.
        This function was adapted from http://www.uniprot.org/faq/28#id_mapping_examples which also gives examples of
        valid values for from_scheme and to_scheme.
        Note that some conversions are not directly possible e.g. PDB_ID (PDB) to UPARC (UniParc). They need to go through
        an intermediary format like ACC (UniProtKB AC) or ID (UniProtKB ID).
        This function returns a dict mapping the IDs in from_scheme to a list of sorted IDs in to_scheme.
    '''
    try:
        assert(hasattr(list_of_from_ids, '__iter__'))
    except:
        raise Exception('The list_of_from_ids argument should be an iterable type (e.g. list).')
    full_mapping = {}
    cached_mapping_file = None
    if cache_dir:
        cached_mapping_file = os.path.join(cache_dir, '%s.%s' % (from_scheme, to_scheme))
        if os.path.exists(cached_mapping_file):
            full_mapping = simplejson.loads(read_file(cached_mapping_file))
    list_of_from_ids = set(list_of_from_ids)

    requested_mapping = {}
    remaining_ids = []
    for id in list_of_from_ids:
        if full_mapping.get(id):
            requested_mapping[id] = full_mapping[id]
        else:
            remaining_ids.append(id)
    assert(set(remaining_ids + requested_mapping.keys()) == set(list_of_from_ids))

    if remaining_ids:
        if not silent:
            print("Getting %s->%s mapping" % (from_scheme, to_scheme))
        url = 'http://www.uniprot.org/mapping/'
        params = {
            'from'      : from_scheme,
            'to'        : to_scheme,
            'format'    : 'tab',
            'query'     : ' '.join(sorted(list(list_of_from_ids))),
        }

        data = urllib.urlencode(params)
        request = urllib2.Request(url, data)
        contact = "" # Please set your email address here to help us debug in case of problems.
        request.add_header('User-Agent', 'Python %s' % contact)
        response = urllib2.urlopen(request)
        page = response.read(200000)
        lines = page.split("\n")

        assert(lines[-1] == '')
        assert(lines[0].split("\t") == ['From', 'To'])
        for line in lines[1:-1]:
            tokens = line.split("\t")
            assert(len(tokens) == 2)
            assert(tokens[0] in list_of_from_ids)
            full_mapping[tokens[0]] = full_mapping.get(tokens[0], [])
            full_mapping[tokens[0]].append(tokens[1])
            requested_mapping[tokens[0]] = requested_mapping.get(tokens[0], [])
            requested_mapping[tokens[0]].append(tokens[1])

    # Sort the IDs
    for k, v in requested_mapping.iteritems():
        #assert(len(v) == len(set(v)))
        requested_mapping[k] = sorted(set(v))
    for k, v in full_mapping.iteritems():
        #assert(len(v) == len(set(v)))
        full_mapping[k] = sorted(set(v))

    if remaining_ids and cached_mapping_file:
        write_file(cached_mapping_file, simplejson.dumps(full_mapping))
    return requested_mapping

def pdb_to_uniparc(pdb_ids, silent = True, cache_dir = None, manual_additions = {}):
    ''' Returns a mapping {PDB ID -> List(UniParcEntry)}
        The UniParcEntry objects have a to_dict() method which may be useful.
    '''

    # Map PDB IDs to UniProtKB AC
    if not silent:
        colortext.write("Retrieving PDB to UniProtKB AC mapping: ", 'cyan')
    pdb_ac_mapping = uniprot_map('PDB_ID', 'ACC', pdb_ids, cache_dir = cache_dir, silent = silent)

    for k, v in manual_additions.iteritems():
        if k in pdb_ids:
            if pdb_ac_mapping.get(k):
                pdb_ac_mapping[k].extend(v)
                pdb_ac_mapping[k] = list(set(pdb_ac_mapping[k]))
            else:
                pdb_ac_mapping[k] = v

    if not silent:
        colortext.write("done\n", 'green')

    # Get a list of AC_IDs
    if not silent:
        colortext.write("Retrieving UniProtKB AC to UniProtKB ID mapping: ", 'cyan')
    AC_IDs = set()
    for k, v in pdb_ac_mapping.iteritems():
        AC_IDs = AC_IDs.union(set(v))
    AC_IDs = list(AC_IDs)
    if not silent:
        colortext.write("done\n", 'green')

    # Map UniProtKB ACs to UniParc IDs
    if not silent:
        colortext.write("Retrieving UniProtKB AC to UniParc ID mapping: ", 'cyan')
    ac_uniparc_mapping = uniprot_map('ACC', 'UPARC', AC_IDs, cache_dir = cache_dir, silent = silent)
    for k, v in ac_uniparc_mapping.iteritems():
        assert(len(v) == 1)
        ac_uniparc_mapping[k] = v[0]
    if not silent:
        colortext.write("done\n", 'green')

    # Map UniProtKB ACs to UniProtKB IDs
    ac_id_mapping = uniprot_map('ACC', 'ID', AC_IDs, cache_dir = cache_dir, silent = silent)

    for k, v in ac_id_mapping.iteritems():
        assert(len(v) == 1)
        ac_id_mapping[k] = v[0]

    # Create mapping from PDB IDs to UniParcEntry objects
    m = {}
    if not silent:
        colortext.message("\nRetrieving FASTA sequences for the %d PDB IDs." % len(pdb_ids))
    for pdb_id, ACs in pdb_ac_mapping.iteritems():
        if not silent:
            colortext.write("%s: " % pdb_id, "orange")
        m[pdb_id] = []
        for AC in ACs:
            entry = UniParcEntry(ac_uniparc_mapping[AC], [AC], [ac_id_mapping[AC]], cache_dir = cache_dir)
            m[pdb_id].append(entry)
            if not silent:
                colortext.write(".", "green")
        if not silent:
            print("")
    return m

class ProteinSubsection(object):

    def __init__(self, att_type, description, begin_position, end_position):
        self.att_type = att_type
        self.description = description
        assert(type(begin_position) == type(1))
        assert(type(end_position) == type(1))
        self.begin_position = begin_position
        self.end_position = end_position
        #self.parent = None - Unused at present

    def to_db(self):
        return {
            'StartResidue'  :   self.begin_position,
            'EndResidue'    :   self.end_position,
            'Type'          :   self.att_type,
            'Description'   :   self.description,
        }

    def __repr__(self):
        s = []
        s.append('%s-%s: ' % (str(self.begin_position).rjust(5), str(self.end_position).ljust(5)))
        s.append(self.att_type)
        if self.description:
            s.append(' (%s)' % self.description)
        return "".join(s)

    def __lt__(self, other):
        return self.begin_position < other.begin_position

    def __le__(self, other):
        return self.begin_position <= other.begin_position

    def __eq__(self, other):
        return self.att_type == other.att_type and self.description == other.description and self.begin_position == other.begin_position and self.end_position == other.end_position

class ProteinSubsectionHolder(object):
    def __init__(self, _length):
        self.sections = []
        self._length = _length
        #self.add('SEQUENCE', 'WHOLE SEQUENCE', 1, _length)

    #def verify(self):
    #    pass

    def add(self, att_type, description, begin_position, end_position):
        # This is fairly brute force. Another implementation is to allow all pairs to be added then have a verify function.
        # The verify function would sort sections by (ascending beginning index, descending end index).
        # Iterating through the sections (variable s), we would see if a section is contained within a 'parent' (we set the whole sequence to be the root parent).
        #   if so then we tie a child/parent link and set the current section s to be the new parent
        #   if there is an overlap, we raise an exception
        #   if the sections are disparate, we go up the tree to find the first parent which contains s, tie the links, then make s the new parent
        # A successful verification should partition the sequence into subsequences inside subsequences.
        new_section = ProteinSubsection(att_type, description, begin_position, end_position)
        for s in self.sections:
            # Sort by beginning index.
            # Valid pairs are then: i) 2nd section is disparate; or ii) 2nd section in contained in the first.
            # We check for the second case below.
            s_pair = sorted([new_section, s], key=lambda x: (x.begin_position, -x.end_position))
            overlap = False
            assert(s_pair[0].begin_position <= s_pair[1].begin_position)
            if (s_pair[0].begin_position <= s_pair[1].begin_position <= s_pair[0].end_position) and (s_pair[1].end_position > s_pair[0].end_position):
                overlap = True
            elif (s_pair[0].begin_position <= s_pair[1].end_position <= s_pair[0].end_position) and (s_pair[1].begin_position < s_pair[0].begin_position):
                overlap = True
            if overlap:
                #colortext.error("\n1: Overlap in protein sections.\nExisting sections:\n%s\nNew section:\n%s" % (s_pair[0], s_pair[1]))
                raise ProteinSubsectionOverlapException("\n1: Overlap in protein sections.\nExisting sections:\n%s\nNew section:\n%s" % (s_pair[0], s_pair[1]))
        self.sections.append(new_section)
        self.sections = sorted(self.sections, key=lambda x:(x.begin_position, -x.end_position))

    def __add__(self, other):
        assert(self._length == other._length)
        holder = ProteinSubsectionHolder(self._length)
        for s in self.sections:
            holder.add(s.att_type, s.description, s.begin_position, s.end_position)
        for o in other.sections:
            already_exists = False
            for s in self.sections:
                if o.begin_position == s.begin_position and o.end_position == s.end_position:
                    assert(o.att_type == s.att_type)
                    if o.description and s.description:
                        if o.description != s.description:
                            # Ignore case differences for equality but favor the case where the first letter is capitalized
                            if o.description.upper() != s.description.upper():
                                #colortext.error("\nSubsection descriptions do not match for '%s', range %d-%d.\nFirst description: '%s'\nSecond description: '%s'\n" % (s.att_type, s.begin_position, s.end_position, o.description, s.description))
                                raise ProteinSubsectionOverlapException("\nSubsection descriptions do not match for '%s', range %d-%d.\nFirst description: '%s'\nSecond description: '%s'\n" % (s.att_type, s.begin_position, s.end_position, o.description, s.description))
                            elif o.description[0].upper() == o.description[0]:
                                s.description = o.description
                            else:
                                o.description = s.description
                    else:
                        o.description = o.description or s.description
                        s.description = o.description or s.description
                    already_exists = True
                #elif o.begin_position <= s.begin_position <= o.end_position:
                #    raise ProteinSubsectionOverlapException("\n2: Overlap in protein sections.\nFirst set of sections:\n%s\nSecond set of sections:\n%s" % (s, o))
                #elif o.end_position <= s.end_position <= o.end_position:
                #    raise ProteinSubsectionOverlapException("\n3: Overlap in protein sections.\nFirst set of sections:\n%s\nSecond set of sections:\n%s" % (s, o))
            if not(already_exists):
                holder.add(o.att_type, o.description, o.begin_position, o.end_position)
        return holder

    def __len__(self):
        return len(self.sections)

    def __repr__(self):
        return "\n".join([str(s) for s in self.sections])

class EmptyUniProtACXMLException(Exception): pass

class UniProtACEntry(object):

    organism_name_types = set(['common', 'full', 'scientific', 'synonym', 'abbreviation'])

    molecule_processing_subsections = set([
        "signal peptide",
        "chain",
        "transit peptide",
        "propeptide",
        "peptide",
        "initiator methionine",
    ])

    sampling_methods = {
        'EM'    : 'electron microscopy',
        'Fiber' : 'fiber diffraction',
        'Model' : 'model',
        'NMR'   : 'nuclear magnetic resonance',
        'X-ray' : 'X-ray crystallography',
        'Neutron'   : 'neutron diffraction',
        'Other'     : 'other'
    }

    def __init__(self, UniProtAC, XML = None, cache_dir = None, silent = True):
        if cache_dir and not(os.path.exists(cache_dir)):
            raise Exception("The cache directory %s does not exist." % cache_dir)

        self.UniProtAC = UniProtAC
        self.silent = silent

        # Get XML
        if XML == None:
            protein_xml = None
            cached_filepath = None
            if cache_dir:
                cached_filepath = os.path.join(cache_dir, '%s.xml' % UniProtAC)
            if cached_filepath and os.path.exists(cached_filepath):
                protein_xml = read_file(cached_filepath)
            else:
                if not silent:
                    colortext.write("Retrieving %s\n" % UniProtAC, "cyan")
                url = 'http://www.uniprot.org/uniprot/%s.xml' % UniProtAC
                protein_xml = http_get(url)
                if not(protein_xml.strip()):
                    raise EmptyUniProtACXMLException('The file %s is empty.' % UniProtAC)
                if cached_filepath:
                    write_file(cached_filepath, protein_xml)
            self.XML = protein_xml
        else:
            self.XML = XML

        self.recommended_name = None
        self.submitted_names = []
        self.alternative_names = []

        # Get DOM
        try:
            self._dom = parseString(protein_xml)
        except:
            if cached_filepath:
                raise Exception("The UniProtAC XML for '%s' was invalid. The cached file is located at %s. Check this file - if it is not valid XML then delete the file and rerun the script." % (UniProtAC, cached_filepath))
            else:
                raise Exception("The UniProtAC XML for '%s' was invalid." % UniProtAC)
        main_tags = self._dom.getElementsByTagName("uniprot")
        assert(len(main_tags) == 1)
        entry_tags = main_tags[0].getElementsByTagName("entry")
        assert(len(entry_tags) == 1)
        self.entry_tag = entry_tags[0]

        self._parse_evidence_tag()
        self._parse_sequence_tag()
        self._parse_protein_tag()
        self._parse_organism_tag()
        self._parse_subsections()
        self._parse_PDB_mapping()

    def _parse_PDB_mapping(self):
        entry_tag = self.entry_tag
        mapping = {}
        dbReference_tags = [child for child in entry_tag.childNodes if child.nodeType == child.ELEMENT_NODE and child.tagName == 'dbReference']

        for t in dbReference_tags:
            db_type = t.getAttribute('type')
            assert(db_type)
            if db_type == 'PDB':
                pdb_id = t.getAttribute('id')
                assert(len(pdb_id) == 4)
                #print(pdb_id)
                method = None
                resolution = None
                chains = []
                for p in t.getElementsByTagName('property'):
                    if p.getAttribute('type') == 'method':
                        method = p.getAttribute('value')
                    elif p.getAttribute('type') == 'resolution':
                        resolution = float(p.getAttribute('value'))
                    elif p.getAttribute('type') == 'chains':
                        chains_groups = [x.strip() for x in p.getAttribute('value').split(",") if x.strip()]
                        for cg in chains_groups:
                            cg_tokens = cg.split("=")
                            assert(len(cg_tokens) == 2)

                            chain_ids = cg_tokens[0].strip().split("/")
                            for chain_id in chain_ids:
                                assert(len(chain_id) == 1)
                            #print(chain_id)

                            range = cg_tokens[1].strip().split("-")
                            assert(len(range) == 2)
                            starting_index = None
                            ending_index = None
                            try:
                                starting_index = int(range[0])
                                ending_index = int(range[1])
                            except:
                                mmkey = "/".join(sorted(chain_ids))
                                if missing_mapping_for_AC_PDB_chains.get(self.UniProtAC, {}).get(pdb_id, {}).get(mmkey):
                                    starting_index, ending_index = missing_mapping_for_AC_PDB_chains.get(self.UniProtAC, {}).get(pdb_id, {}).get(mmkey)
                                    if not self.silent:
                                        colortext.error("Fixing starting_index, ending_index to %d, %d for PDB chains %s." % (starting_index, ending_index, str(chain_ids)))
                                else:
                                    if not set(chain_ids) in broken_mapping_for_AC_PDB_chains.get(self.UniProtAC, {}).get(pdb_id, []):
                                        raise colortext.Exception("The starting index and ending index for %s, chains %s in UniProtKB AC entry %s is broken or missing. Fix the mapping or mark it as missing in uniprot_patches.py" % (pdb_id, ",".join(chain_ids), self.UniProtAC))
                                    continue

                            for chain_id in chain_ids:
                                assert(len(chain_id) == 1)
                                if fixed_mapping_for_AC_PDB_chains.get(self.UniProtAC, {}).get(pdb_id, {}).get(chain_id):
                                    fixed_chain_id = fixed_mapping_for_AC_PDB_chains.get(self.UniProtAC, {}).get(pdb_id, {}).get(chain_id)
                                    if not self.silent:
                                        colortext.error("Fixing PDB chain from %s to %s." % (chain_id, fixed_chain_id))
                                    chain_id = fixed_chain_id
                                chains.append((chain_id, starting_index, ending_index))

                    else:
                        raise Exception("Unhandled dbReference property tag type.")

                if not method:
                    temp_method = missing_AC_PDB_methods.get(self.UniProtAC, {}).get(pdb_id, [])
                    if temp_method:
                        method = temp_method[0]
                        if not self.silent:
                            colortext.error("Fixing method to %s for PDB %s." % (method, pdb_id))

                if not chains:
                    assert(pdb_id in broken_mapping_for_AC_PDB_chains.get(self.UniProtAC, {}))
                    continue

                if not method and chains:
                    raise colortext.Exception("Missing method and chains for %s in UniProtKB AC entry %s. Fix the mapping or mark it as missing in uniprot_patches.py" % (pdb_id, self.UniProtAC))

                if not method in UniProtACEntry.sampling_methods.keys():
                    raise colortext.Exception("Unknown method '%s' found in UniProtKB AC entry %s." % (method, self.UniProtAC))
                if method in ['X-ray'] and resolution: # resolution can be null e.g. in P00698 with 2A6U (POWDER DIFFRACTION)
                    assert(pdb_id not in mapping)
                    if pdb_id not in PDBs_marked_as_XRay_with_no_resolution:
                        assert(resolution)
                        mapping[pdb_id] = {'method' : method, 'resolution' : resolution, 'chains' : {}}
                        import pprint
                        for chain in chains:
                            #assert(chain[0] not in mapping[pdb_id]['chains']) # todo: I disabled this when calling get_common_PDB_IDs as it hit the assertion while looking up 1REW with 4N1D. Is this assertion necessary?
                            mapping[pdb_id]['chains'][chain[0]] = (chain[1], chain[2])

        if False:
            for pdb_id, details in sorted(mapping.iteritems()):
                if not self.silent:
                    colortext.message("%s, %s, %sA" % (str(pdb_id), str(details['method']), str(details['resolution'])))
                for chain, indices in sorted(details['chains'].iteritems()):
                    if not self.silent:
                        colortext.warning(" Chain %s: %s-%s" % (chain, str(indices[0]).rjust(5), str(indices[1]).ljust(5)))


    def _parse_evidence_tag(self):
        entry_tag = self.entry_tag
        protein_Existence_tags = entry_tag.getElementsByTagName("proteinExistence")
        assert(len(protein_Existence_tags) == 1)
        self.existence_type = protein_Existence_tags[0].getAttribute('type')
        #print(self.existence_type)

    def _parse_subsections(self):
        molecule_processing_subsections = UniProtACEntry.molecule_processing_subsections
        assert(self.sequence_length)
        subsections = ProteinSubsectionHolder(self.sequence_length)
        entry_tag = self.entry_tag
        feature_tags = [child for child in entry_tag.childNodes if child.nodeType == child.ELEMENT_NODE and child.tagName == 'feature']

        for additional_subsection in subsections_for_addition.get(self.UniProtAC, []):
            if not self.silent:
                colortext.warning("Adding additional subsection %s." % str(additional_subsection))
            subsections.add(additional_subsection[0], additional_subsection[1], additional_subsection[2], additional_subsection[3])

        if self.UniProtAC not in AC_entries_where_we_ignore_the_subsections:
            for feature_tag in feature_tags:
                if feature_tag.hasAttribute('type'):
                    att_type = feature_tag.getAttribute('type')
                    if att_type in molecule_processing_subsections:
                        description = feature_tag.getAttribute('description')
                        locations = feature_tag.getElementsByTagName("location")
                        assert(len(locations) == 1)

                        subsection_for_addition = None
                        begin_position = None
                        end_position = None
                        position_tag = locations[0].getElementsByTagName("position")
                        if position_tag:
                            assert(len(position_tag) == 1)
                            position_tag = locations[0].getElementsByTagName("position")
                            if position_tag[0].hasAttribute('position'):
                                begin_position = int(position_tag[0].getAttribute('position'))
                                end_position = begin_position
                        else:
                            begin_pos = locations[0].getElementsByTagName("begin")
                            end_pos = locations[0].getElementsByTagName("end")
                            assert(len(begin_pos) == 1 and len(end_pos) == 1)

                            if begin_pos[0].hasAttribute('position'):
                                begin_position = int(begin_pos[0].getAttribute('position'))
                            if end_pos[0].hasAttribute('position'):
                                end_position = int(end_pos[0].getAttribute('position'))

                        if (begin_position, end_position) in differing_subsection_name_patch.get(self.UniProtAC, {}):
                            description_pair = differing_subsection_name_patch[self.UniProtAC][(begin_position, end_position)]
                            if description_pair[0] == description:
                                if not self.silent:
                                    colortext.warning("Changing subsection name from '%s' to '%s'." % description_pair)
                                description = description_pair[1]

                        if begin_position and end_position:
                            subsection_for_addition = (att_type, description, begin_position, end_position)
                            if subsection_for_addition not in clashing_subsections_for_removal.get(self.UniProtAC, []):
                                if subsection_for_addition not in overlapping_subsections_for_removal.get(self.UniProtAC, []): # This may be overkill
                                    #colortext.message("Adding subsection %s." % str(subsection_for_addition))
                                    subsections.add(subsection_for_addition[0], subsection_for_addition[1], subsection_for_addition[2], subsection_for_addition[3])
                                else:
                                    if not self.silent:
                                        colortext.warning("Skipping overlapping subsection %s." % str(subsection_for_addition))
                            else:
                                if not self.silent:
                                    colortext.warning("Skipping clashing subsection %s." % str(subsection_for_addition))

        self.subsections = subsections

    def _parse_sequence_tag(self):
        '''Parses the sequence and atomic mass.'''
        #main_tags = self._dom.getElementsByTagName("uniprot")
        #assert(len(main_tags) == 1)
        #entry_tags = main_tags[0].getElementsByTagName("entry")
        #assert(len(entry_tags) == 1)
        #entry_tags[0]

        entry_tag = self.entry_tag
        # only get sequence tags that are direct children of the entry tag (sequence tags can also be children of entry.comment.conflict)
        sequence_tags = [child for child in entry_tag.childNodes if child.nodeType == child.ELEMENT_NODE and child.tagName == 'sequence']
        assert(len(sequence_tags) == 1)
        sequence_tag = sequence_tags[0]

        # atomic mass, sequence, CRC64 digest
        self.atomic_mass = float(sequence_tag.getAttribute("mass"))
        self.sequence = "".join(sequence_tag.firstChild.nodeValue.strip().split("\n"))
        self.sequence_length = int(sequence_tag.getAttribute("length"))
        self.CRC64Digest = sequence_tag.getAttribute("checksum")

    def _parse_organism_tag(self):
        '''Parses the protein tag to get the names and EC numbers.'''
        organism_name_types = UniProtACEntry.organism_name_types
        self.organisms = []
        organism_tags = [child for child in self.entry_tag.childNodes if child.nodeType == child.ELEMENT_NODE and child.tagName == 'organism']
        assert(len(organism_tags) == 1)
        for organism_tag in organism_tags:
            names = dict.fromkeys(organism_name_types, None)
            for name_tag in [child for child in organism_tag.childNodes if child.nodeType == child.ELEMENT_NODE and child.tagName == 'name']:
                name_type = name_tag.getAttribute("type")
                assert(name_type in organism_name_types)
                names[name_type] = name_tag.firstChild.nodeValue.strip()
            assert(names.get('scientific'))
            self.organisms.append(names)
            
    def _parse_protein_tag(self):
        '''Parses the protein tag to get the names and EC numbers.'''

        protein_nodes = self._dom.getElementsByTagName('protein')
        assert(len(protein_nodes) == 1)
        self.protein_node = protein_nodes[0]

        self._get_recommended_name()
        self._get_submitted_names()
        self._get_alternative_names()

    def get_names(self):
        if self.recommended_name:
            return [self.recommended_name] + self.alternative_names + self.submitted_names
        else:
            return self.alternative_names + self.submitted_names

    @staticmethod
    def parse_names(tags):
        names = []
        for tag in tags:
            fullNames = tag.getElementsByTagName('fullName')
            assert(len(fullNames) == 1)
            fullName = fullNames[0].firstChild.nodeValue

            EC_numbers = []
            EC_number_tags = tag.getElementsByTagName('ecNumber')
            for EC_number_tag in EC_number_tags:
                EC_numbers.append(EC_number_tag.firstChild.nodeValue)

            short_names = []
            short_name_tags = tag.getElementsByTagName('shortName')
            for short_name_tag in short_name_tags:
                short_names.append(short_name_tag.firstChild.nodeValue)
            for n in names:
                assert(n['Name'] != fullName)
            names.append({'Name' : fullName, 'EC numbers' : EC_numbers, 'Short names' : short_names})
        return names

    def _get_recommended_name(self):
        # only get recommendedName tags that are direct children of the protein tag (recommendedName tags can also be children of protein.component tags)
        recommended_names = [child for child in self.protein_node.childNodes if child.nodeType == child.ELEMENT_NODE and child.tagName == 'recommendedName']
        if recommended_names:
            assert(len(recommended_names) == 1)
            recommended_names = UniProtACEntry.parse_names(recommended_names)
            assert(len(recommended_names) == 1)
            self.recommended_name = recommended_names[0]

    def _get_submitted_names(self):
        submitted_names = self.protein_node.getElementsByTagName('submittedName')
        if submitted_names:
            for submitted_name in submitted_names:
                # According to the schema (http://www.uniprot.org/docs/uniprot.xsd), submitted names have no short names
                assert(len(submitted_name.getElementsByTagName('shortName')) == 0)
            self.submitted_names = UniProtACEntry.parse_names(submitted_names)

    def _get_alternative_names(self):
        alternative_names = self.protein_node.getElementsByTagName('alternativeName')
        if alternative_names:
             self.alternative_names = UniProtACEntry.parse_names(alternative_names)


class UniParcEntry(object):

    def __init__(self, UniParcID, UniProtACs = None, UniProtIDs = None, cache_dir = None, silent = False):
        if cache_dir and not(os.path.exists(os.path.abspath(cache_dir))):
            raise Exception("The cache directory %s does not exist." % os.path.abspath(cache_dir))
        self.UniParcID = UniParcID
        self.cache_dir = cache_dir
        self.recommended_name = None
        self.silent = silent

        # Get AC mapping
        if not UniProtACs or UniParcID=='UPI0000047CA3': # todo: is this UPI0000047CA3 special handling necessary?
            mapping = uniprot_map('UPARC', 'ACC', [UniParcID], cache_dir = cache_dir, silent = silent)[UniParcID]
            self.UniProtACs = mapping
        else:
            self.UniProtACs = UniProtACs

        # Get ID mapping
        if not UniProtIDs:
            mapping = uniprot_map('UPARC', 'ID', [UniParcID], cache_dir = cache_dir, silent = silent)[UniParcID]
            self.UniProtIDs = mapping
        else:
            self.UniProtIDs = UniProtIDs

        # Get FASTA
        cached_filepath = None
        if cache_dir:
            cached_filepath = os.path.join(cache_dir, '%s.fasta' % UniParcID)
        if cached_filepath and os.path.exists(cached_filepath):
            fasta = read_file(cached_filepath)
        else:
            if not silent:
                print("Getting FASTA file")
            url = 'http://www.uniprot.org/uniparc/%s.fasta' % UniParcID
            fasta = http_get(url)
            if cached_filepath:
                write_file(cached_filepath, fasta)

        # Get sequence
        header = fasta.split("\n")[0].split()
        assert(len(header) == 2)
        assert(header[0] == ">%s" % UniParcID)
        assert(header[1].startswith("status="))
        sequence = "".join(map(string.strip, fasta.split("\n")[1:]))
        self.sequence = sequence

        # Get atomic mass (and sequence again)
        self.atomic_mass = None
        self.CRC64Digest = None
        recommended_names = []
        alternative_names = []
        submitted_names = []

        self.AC_entries = {}
        subsections = ProteinSubsectionHolder(len(sequence))

        for UniProtAC in self.UniProtACs:
            #colortext.write("%s\n" % UniProtAC, 'cyan')
            try:
                AC_entry = UniProtACEntry(UniProtAC, cache_dir = self.cache_dir, silent = silent)
            except EmptyUniProtACXMLException:
                continue
            self.AC_entries[UniProtAC] = AC_entry

            # Mass sanity check
            if self.atomic_mass != None:
                assert(self.atomic_mass == AC_entry.atomic_mass)
            self.atomic_mass = AC_entry.atomic_mass

            # Sequence sanity check
            assert(self.sequence == AC_entry.sequence)
            # CRC 64 sanity check
            if self.CRC64Digest != None:
                assert(self.CRC64Digest == AC_entry.CRC64Digest)
            self.CRC64Digest = AC_entry.CRC64Digest
            assert(CRC64.CRC64digest(self.sequence) == self.CRC64Digest)

            if AC_entry.recommended_name:
                found = False
                for n in recommended_names:
                    if n[0] == AC_entry.recommended_name:
                        n[1] += 1
                        found = True
                        break
                if not found:
                    recommended_names.append([AC_entry.recommended_name, 1])

            for alternative_name in AC_entry.alternative_names:
                found = False
                for n in alternative_names:
                    if n[0] == alternative_name:
                        n[1] += 1
                        found = True
                        break
                if not found:
                    alternative_names.append([alternative_name, 1])

            for submitted_name in AC_entry.submitted_names:
                found = False
                for n in submitted_names:
                    if n[0] == submitted_name:
                        n[1] += 1
                        found = True
                        break
                if not found:
                    submitted_names.append([submitted_name, 1])

            subsections += AC_entry.subsections
        self.subsections = subsections

        assert(len(set(UniParcMergedRecommendedNamesRemap.keys()).intersection(set(UniParcMergedSubmittedNamesRemap.keys()))) == 0)
        if UniParcID in UniParcMergedRecommendedNamesRemap:
            recommended_names = [[UniParcMergedRecommendedNamesRemap[UniParcID], 1]]
        elif UniParcID in UniParcMergedSubmittedNamesRemap:
            recommended_names = [[UniParcMergedSubmittedNamesRemap[UniParcID], 1]]

        if not silent:
            colortext.write('Subsections\n', 'orange')
        #print(subsections)

        if len(recommended_names) == 0 and len(alternative_names) == 0 and len(submitted_names) == 0:
            raise UniParcEntryStandardizationException("UniParcID %s has no recommended names." % UniParcID)
        elif len(recommended_names) == 0:
            s = ["UniParcID %s has no recommended names.\n" % UniParcID]
            if alternative_names:
                s.append("It has the following alternative names:")
                for tpl in sorted(alternative_names, key=lambda x:-x[1]):
                    s.append("\n  count=%s: %s" % (str(tpl[1]).ljust(5), tpl[0]['Name']))
                    if tpl[0]['Short names']:
                        s.append(" (short names: %s)" % ",".join(tpl[0]['Short names']))
                    if tpl[0]['EC numbers']:
                        s.append(" (EC numbers: %s)" % ",".join(tpl[0]['EC numbers']))
            if submitted_names:
                s.append("It has the following submitted names:")
                for tpl in sorted(submitted_names, key=lambda x:-x[1]):
                    s.append("\n  count=%s: %s" % (str(tpl[1]).ljust(5), tpl[0]['Name']))
                    if tpl[0]['Short names']:
                        s.append(" (short names: %s)" % ",".join(tpl[0]['Short names']))
                    if tpl[0]['EC numbers']:
                        s.append(" (EC numbers: %s)" % ",".join(tpl[0]['EC numbers']))
            #raise UniParcEntryStandardizationException("".join(s))
        elif len(recommended_names) > 1:
            s = ["UniParcID %s has multiple recommended names: " % UniParcID]
            for tpl in sorted(recommended_names, key=lambda x:-x[1]):
                s.append("\n  count=%s: %s" % (str(tpl[1]).ljust(5), tpl[0]['Name']))
                if tpl[0]['Short names']:
                    s.append(" (short names: %s)" % ",".join(tpl[0]['Short names']))
                if tpl[0]['EC numbers']:
                    s.append(" (EC numbers: %s)" % ",".join(tpl[0]['EC numbers']))
            raise UniParcEntryStandardizationException("".join(s))

        #assert(len(recommended_names) == 1) # todo: this is not always available
        #print(recommended_names)
        self.recommended_name = None
        if len(recommended_names) == 1:
            self.recommended_name = recommended_names[0][0]
        self.get_organisms()

    def _get_XML(self):
        uparc_xml = None
        cached_filepath = None
        if self.cache_dir:
            cached_filepath = os.path.join(self.cache_dir, '%s.xml' % self.UniParcID)
        if cached_filepath and os.path.exists(cached_filepath):
            uparc_xml = read_file(cached_filepath)
        else:
            if not self.silent:
                colortext.write("Retrieving %s\n" % self.UniParcID, "cyan")
            url = 'http://www.uniprot.org/uniparc/%s.xml' % self.UniParcID
            uparc_xml = http_get(url)
            if cached_filepath:
                write_file(cached_filepath, uparc_xml)
        self.XML = uparc_xml

        # Get DOM
        self._dom = parseString(uparc_xml)
        main_tags = self._dom.getElementsByTagName("uniparc")
        assert(len(main_tags) == 1)
        entry_tags = main_tags[0].getElementsByTagName("entry")
        assert(len(entry_tags) == 1)
        self.entry_tag = entry_tags[0]

    def _get_active_ACCs(self):
        entry_tag = self.entry_tag
        db_reference_tags = [child for child in entry_tag.childNodes if child.nodeType == child.ELEMENT_NODE and child.tagName == 'dbReference']
        ACCs = []
        for db_reference_tag in db_reference_tags:
            assert(db_reference_tag.hasAttribute('type') and db_reference_tag.hasAttribute('active') and db_reference_tag.hasAttribute('id'))
            att_type = db_reference_tag.getAttribute('type')
            is_active = db_reference_tag.getAttribute('active')
            dbref_id = db_reference_tag.getAttribute('id')
            assert(is_active == 'Y' or is_active == 'N')
            is_active = (is_active == 'Y')
            if att_type == 'UniProtKB/Swiss-Prot' or att_type == 'UniProtKB/TrEMBL':
                if is_active:
                    #colortext.message(att_type + dbref_id)
                    ACCs.append(dbref_id)
                else:
                    pass#colortext.warning(att_type + dbref_id)
        return ACCs

    def get_organisms(self):
        self.organisms = {}
        self._get_XML()
        ACCs = self._get_active_ACCs()
        #print(ACCs)
        name_count = {}
        for UniProtAC in ACCs:
            #print(UniProtAC)
            if UniProtAC in self.AC_entries:
                AC_entry = self.AC_entries[UniProtAC]
            else:
                if UniProtAC in ['N2XE95', 'N1E9H6', 'N2JUB3', 'N2Z3Z2']: # hack for bad XML documents at time of writing
                    continue
                if not self.silent:
                    colortext.warning("Retrieving %s" % UniProtAC)
                try:
                    AC_entry = UniProtACEntry(UniProtAC, cache_dir = self.cache_dir, silent = self.silent)
                except EmptyUniProtACXMLException:
                    continue

            for o in AC_entry.organisms:
                name_count[o['scientific']] = name_count.get(o['scientific'], 0)
                name_count[o['scientific']] += 1
            assert(len(AC_entry.organisms) == 1)
            self.organisms[UniProtAC] = AC_entry.organisms[0]

    def to_dict(self):
        return {
            'UniParcID' : self.UniParcID,
            'UniProtAC' : self.UniProtACs,
            'UniProtKB' : self.UniProtIDs,
            'sequence'  : self.sequence,
            'atomic_mass'  : self.atomic_mass,
            'CRC64Digest'  : self.CRC64Digest,
            'Subsections' : self.subsections,
            'Recommended Name' : self.recommended_name,
        }

    def __repr__(self):
        a = []
        for k, v in sorted(self.to_dict().iteritems()):
            if k == 'Subsections':
                a.append(colortext.make("Subsections\n", 'green'))
                a.append("%s\n" % str(v))
            else:
                a.append(colortext.make(k.ljust(20), 'green'))
                a.append(colortext.make("%s\n" % str(v), 'silver'))
        return "".join(a)
        #, '        return simplejson.dumps(self.to_dict())



def get_common_PDB_IDs(pdb_id, cache_dir = None, exception_on_failure = True):
    '''This function takes a PDB ID, maps it to UniProt ACCs, then returns the common set of PDB IDs related to those ACCs.
       The purpose is to find any PDB files related to pdb_id, particularly for complexes, such that the other PDB files
       contain identical sequences or mutant complexes.'''
    m = pdb_to_uniparc([pdb_id], cache_dir = cache_dir)
    UniProtACs = []
    if pdb_id in m:
        for entry in m[pdb_id]:
            if entry.UniProtACs:
                UniProtACs.extend(entry.UniProtACs)
            elif exception_on_failure:
                raise Exception('No UniProtAC for one entry.Lookup failed.')
    elif exception_on_failure:
        raise Exception('Lookup failed.')

    if not UniProtACs:
        if exception_on_failure:
            raise Exception('Lookup failed.')
        else:
            return None
    common_set = set(uniprot_map('ACC', 'PDB_ID', [UniProtACs[0]], cache_dir = cache_dir).get(UniProtACs[0], []))
    for acc in UniProtACs[1:]:
         common_set = common_set.intersection(set(uniprot_map('ACC', 'PDB_ID', [acc], cache_dir = cache_dir).get(acc, [])))
    return sorted(common_set)
