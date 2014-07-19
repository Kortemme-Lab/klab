#!/usr/bin/python
# encoding: utf-8
"""
clustalo.py
Wrapper functions for Clustal Omega.

Created by Shane O'Connor 2013.
Note: The defaults I use here (ClustalW and a gap opening penalty of 0.2 rather than the default value of 10.0) seem to
work well for aligning sequences with gaps and mutations e.g. wildtype and design sequences. You may want to adjust these
values to fit your application.
"""

import os
import shlex
import re
import commands
import platform

from tools.fs.fsio import open_temp_file, read_file
from tools.process import Popen as _Popen
from tools import colortext
from uniprot import pdb_to_uniparc, uniprot_map, UniProtACEntry, UniParcEntry
from fasta import FASTA
from pdb import PDB
from basics import SubstitutionScore, Sequence, SequenceMap, PDBUniParcSequenceMap

### Check for the necessary Clustal Omega and ClustalW software

missing_clustalo_message = '''

This module requires Clustal Omega to be installed. This software appears to be missing on your machine. On Ubuntu, you
can install the software as follows:
  sudo apt-get install clustalo
  sudo apt-get install clustalw

Otherwise, you can download the source code here: http://www.clustal.org/omega/. These instructions work as of 2013/09/13 but a newer version may be available.

  wget http://www.clustal.org/omega/clustal-omega-1.2.0.tar.gz
  wget http://www.clustal.org/download/current/clustalw-2.1-linux-x86_64-libcppstatic.tar.gz

  tar -zxvf clustal-omega-1.2.0.tar.gz
  tar -zxvf clustalw-2.1-linux-x86_64-libcppstatic.tar.gz

  cd clustal-omega-1.2.0/
  ./configure
  make
  sudo make install
  cd ..

  cd clustalw-2.1-linux-x86_64-libcppstatic.tar.gz
  ./configure
  make
  sudo make install

Note that you may need to build argtable2 (http://argtable.sourceforge.net) or install it with the libargtable2-0 package to get Clustal Omega to compile.
'''

if os.name == 'posix' or 'Linux' in platform.uname():
    if commands.getstatusoutput('which clustalo')[0] != 0 or commands.getstatusoutput('which clustalw')[0] != 0:
        raise colortext.Exception(missing_clustalo_message)
else:
    raise Exception("Please extend this check to work on your architecture. At present, it only works on Linux.")




### Module begins

alignment_results_regex = re.compile('.*?Aligning[.]{3}(.*?)Guide tree file created', re.DOTALL)
alignment_line_regex = re.compile('Sequences [(](\d+):(\d+)[)] Aligned. Score:\s*(\d+)')

class NoPDBUniParcMappingExists(Exception): pass
class MalformedSequenceException(Exception): pass

class SequenceAligner(object):
    ''' This class is used to align sequences. To use it, first add sequences using the add_sequence function. Next, call the align function to perform
        the alignment. Alignment results are stored in the following object variables:
            matrix : the 1-indexed matrix returned from clustalw
            named_matrix : [finish this help section...]

        e.g.
            sa = SequenceAligner()
            sa.add_sequence('1A2P_A', 'AQVINTFDGVADYLQTYHKLPDNYITKSEAQALGWVASKGNLADVAPGKSIGGDIFSNREGKLPGKSGRTWREADINYTSGFRNSDRILYSSDWLIYKTTDHYQTFTKIR')
            sa.add_sequence('1B20_A', 'AQVINTFDGVADYLQTYHKLPDNYITKSEAQALGWVASKGNLADVAPGKSIGGDIFSNREGKLPGKSGSTWREADINYTSGFRNSDRILYSSDWLIYKTTDHYQTFTKIR')
            sa.add_sequence('2KF4_A', 'AQVINTFDGVADYLQTYHKLPDNYITKSEAQALGWVASKGNLADVAPGKSIGGDIFSNREGKLPGKSGRTWREADINYTSGFRNSDRILYSSDWLIYKTTDAYQTFTKIR')
            best_matches = sa.align() # {'2KF4_A': {'2KF4_A': 100.0, '1A2P_A': 99.0, '1B20_A': 98.0}, '1A2P_A': {'2KF4_A': 99.0, '1A2P_A': 100.0, '1B20_A': 99.0}, '1B20_A': {'2KF4_A': 98.0, '1A2P_A': 99.0, '1B20_A': 100.0}}
            best_matches_by_id = sa.get_best_matches_by_id('2KF4_A') # {'1A2P_A': 99.0, '1B20_A': 98.0}

        get_residue_mapping returns the mapping between the sequences. Note that this mapping is only based on the sequence strings
        and not e.g. on the residue IDs in the PDB. Since the sequences are 1-indexed, the mapping is also 1-indexed. In the example
        above, for 1A2P to 1B20, the residue mapping would be 1->1 for residue A, 2->2 for residue Q, 3->3 for residue V etc.
    '''

    ### Constructor ###

    def __init__(self, alignment_tool = 'clustalw', gap_opening_penalty = 0.2):
        '''The constructor accepts an alignment tool used to create the alignment and a gap opening penalty. Note that
           the gap opening penalty is currently only used by ClustalW.'''
        assert(alignment_tool == 'clustalw' or alignment_tool == 'clustalo')
        gap_opening_penalty = float(gap_opening_penalty)

        self.records = []
        self.sequence_ids = {} # A 1-indexed list of the sequences in the order that they were added (1-indexing to match Clustal numbering)
        self.matrix = None
        self.named_matrix = None
        self.alignment_output = None
        self.alignment_tool = alignment_tool
        self.gap_opening_penalty = gap_opening_penalty

    ### Class methods
    @staticmethod
    def from_list_of_FASTA_content(FASTA_content_list):
        f = FASTA(FASTA_content_list[0])
        for x in FASTA_content_list[1:]:
            f += FASTA(x)
        return SequenceAligner.from_FASTA(f)

    @staticmethod
    def from_FASTA(f):
        sa = SequenceAligner()
        for sequence in f.sequences:
            sa.add_sequence('%s_%s' % (sequence[0], sequence[1]), sequence[2])
        best_matches = sa.align()
        return sa

    ### API methods ###
    def __repr__(self):
        s = []
        best_matches = self.align()
        for k, v in sorted(best_matches.iteritems()):
            s.append("%s: %s" % (k, ["%s, %s" % (x, y) for x, y in sorted(v.iteritems(), key=lambda x:-x[1]) if x !=k ]))
        return "\n".join(s)

    def add_sequence(self, sequence_id, sequence):

        # This is a sanity check. ClustalO allows ':' in the chain ID but ClustalW replaces ':' with '_' which breaks our parsing
        # All callers to add_sequence now need to replace ':' with '_' so that we can use ClustalW
        assert(sequence_id.find(':') == -1)

        if sequence_id in self.sequence_ids.values():
            raise Exception("Sequence IDs must be unique")
        if list(set(sequence)) == ['X']:
            raise MalformedSequenceException('The sequence contains only X characters. This will crash Clustal Omega.')
        self.records.append(">%s\n%s" % (sequence_id, "\n".join([sequence[i:i+80] for i in range(0, len(sequence), 80)])))
        self.sequence_ids[len(self.sequence_ids) + 1] = sequence_id

    def align(self):

        records = self.records
        percentage_identity_output = None

        fasta_handle, fasta_filename = open_temp_file('/tmp')
        clustal_output_handle, clustal_filename = open_temp_file('/tmp')
        stats_output_handle, stats_filename = open_temp_file('/tmp')
        tempfiles = [fasta_filename, clustal_filename, stats_filename]

        # Create FASTA file
        fasta_handle.write("\n".join(records))
        fasta_handle.close()

        try:
            # Note: By default, ClustalW can rearrange the sequence order in the alignment i.e. the order in which we add
            # the sequences is not necessarily the order in which they appear in the output. For simplicity, the parsing
            # logic assumes (and asserts) that order is maintained so we add the -OUTORDER=INPUT command to ClustalW to
            # ensure this.
            if self.alignment_tool == 'clustalo':
                p = _Popen('.', shlex.split('clustalo --infile %(fasta_filename)s --verbose --outfmt clustal --outfile %(clustal_filename)s --force' % vars()))
                if p.errorcode:
                    raise Exception('An error occurred while calling clustalo to align sequences:\n%s' % p.stderr)
                self.alignment_output = read_file(clustal_filename)
                p = _Popen('.', shlex.split('clustalw -INFILE=%(clustal_filename)s -PIM -TYPE=PROTEIN -STATS=%(stats_filename)s -OUTFILE=/dev/null -OUTORDER=INPUT' % vars()))
                if p.errorcode:
                    raise Exception('An error occurred while calling clustalw to generate the Percent Identity Matrix:\n%s' % p.stderr)
                percentage_identity_output = p.stdout
            elif self.alignment_tool == 'clustalw':
                gap_opening_penalty = self.gap_opening_penalty
                p = _Popen('.', shlex.split('clustalw -INFILE=%(fasta_filename)s -PIM -TYPE=PROTEIN -STATS=%(stats_filename)s -GAPOPEN=%(gap_opening_penalty)0.2f -OUTFILE=%(clustal_filename)s -OUTORDER=INPUT' % vars()))
                if p.errorcode:
                    raise Exception('An error occurred while calling clustalw to generate the Percent Identity Matrix:\n%s' % p.stderr)
                self.alignment_output = read_file(clustal_filename)
                percentage_identity_output = p.stdout
            else:
                raise Exception("An unexpected alignment tool ('%s') was specified" % alignment_tool)

        except Exception, e:
            for t in tempfiles:
                os.remove(t)
            raise

        for t in tempfiles:
            try:
                os.remove(t)
            except: pass

        return self._parse_percentage_identity_output(percentage_identity_output)

    def get_best_matches_by_id(self, id, cut_off = 98.0):
        best_matches = {}
        named_matrix = self.named_matrix
        for k, v in named_matrix[id].iteritems():
            if k != id and v >= cut_off:
                best_matches[k] = v
        return best_matches

    def get_residue_mapping(self):
        '''Returns a mapping between the sequences ONLY IF there are exactly two. This restriction makes the code much simpler.'''
        if len(self.sequence_ids) == 2:
            if not self.alignment_output:
                self.align()
            assert(self.alignment_output)
            return self._create_residue_map(self._get_alignment_lines(), self.sequence_ids[1], self.sequence_ids[2])
        else:
            return None

    ### Private methods ###

    def _create_residue_map(self, alignment_lines, from_sequence_id, to_sequence_id):
        from_sequence = alignment_lines[from_sequence_id]
        to_sequence = alignment_lines[to_sequence_id]
        match_sequence = alignment_lines[-1]

        mapping = {}
        match_mapping = {}
        assert(len(from_sequence) == len(to_sequence) and len(to_sequence) == len(match_sequence))
        from_residue_id = 0
        to_residue_id = 0
        for x in range(len(from_sequence)):
            c = 0
            from_residue = from_sequence[x]
            to_residue = to_sequence[x]
            match_type = match_sequence[x]
            if from_residue != '-':
                from_residue_id += 1
                assert('A' <= from_residue <= 'Z')
                c += 1
            if to_residue != '-':
                to_residue_id += 1
                assert('A' <= to_residue <= 'Z')
                c += 1
            if c == 2:
                if from_residue == to_residue:
                    assert(match_type == '*')

                # We do not want to include matches which are distant from other matches
                has_surrounding_matches = ((x > 0) and (match_sequence[x - 1] != ' ')) or (((x + 1) < len(match_sequence)) and (match_sequence[x + 1] != ' '))
                if match_type == '*':
                    mapping[from_residue_id] = to_residue_id
                    match_mapping[from_residue_id] = SubstitutionScore(1, from_residue, to_residue)
                elif match_type == ':':
                    if has_surrounding_matches:
                        mapping[from_residue_id] = to_residue_id
                        match_mapping[from_residue_id] = SubstitutionScore(0, from_residue, to_residue)
                elif match_type == '.':
                    if has_surrounding_matches:
                        mapping[from_residue_id] = to_residue_id
                        match_mapping[from_residue_id] = SubstitutionScore(-1, from_residue, to_residue)
                elif match_type == ' ':
                    # Allow unmatched residues if they have surrounding matches
                    if has_surrounding_matches:
                        mapping[from_residue_id] = to_residue_id
                        match_mapping[from_residue_id] = SubstitutionScore(-2, from_residue, to_residue)
                else:
                    assert(False)

        ### Prune the mapping
        # We probably do not want to consider all partial matches that Clustal reports as some may be coincidental
        # e.g. part of a HIS-tag partially matching a tyrosine so we will prune the mapping.

        # Remove any matches where there are no matches which are either direct neighbors or the neighbor of a direct
        # neighbor e.g. the colon in this match "  ***..***  :  .*****" is on its own
        while True:
            remove_count = 0
            all_keys = sorted(mapping.keys())
            for k in all_keys:
                current_keys = mapping.keys()
                if (k - 2 not in current_keys) and (k - 1 not in current_keys) and (k + 1 not in current_keys) and (k - 2 not in current_keys):
                    del mapping[k]
                    del match_mapping[k]
                    remove_count += 1
            if remove_count == 0:
                break

        # Remove all leading partial matches except the last one
        keys_so_far = set()
        for k in sorted(mapping.keys()):
            if match_mapping[k].clustal == 1:
                break
            else:
                keys_so_far.add(k)
        for k in sorted(keys_so_far)[:-1]:
            del mapping[k]
            del match_mapping[k]

        # Remove all trailing partial matches except the first one
        keys_so_far = set()
        for k in sorted(mapping.keys(), reverse = True):
            if match_mapping[k].clustal == 1:
                break
            else:
                keys_so_far.add(k)
        for k in sorted(keys_so_far)[1:]:
            del mapping[k]
            del match_mapping[k]

        return mapping, match_mapping

    def _get_alignment_lines(self):
        ''' This function parses the Clustal Omega alignment output and returns the aligned sequences in a dict: sequence_id -> sequence_string.
            The special key -1 is reserved for the match line (e.g. ' .:******* *').'''

        # Strip the boilerplate lines
        lines = self.alignment_output.split("\n")
        assert(lines[0].startswith('CLUSTAL'))
        lines = '\n'.join(lines[1:]).lstrip().split('\n')

        # The sequence IDs should be unique. Reassert this here
        assert(len(self.sequence_ids.values()) == len(set(self.sequence_ids.values())))

        # Create the list of sequence IDs
        id_list = [v for k, v in sorted(self.sequence_ids.iteritems())]

        # Determine the indentation level
        first_id = id_list[0]
        header_regex = re.compile("(.*?\s+)(.*)")
        alignment_regex = re.compile("^([A-Z\-]+)\s*$")
        mtchs = header_regex.match(lines[0])
        assert(mtchs.group(1).strip() == first_id)
        indentation = len(mtchs.group(1))
        sequence = mtchs.group(2)
        assert(sequence)
        assert(alignment_regex.match(sequence))

        # Create empty lists for the sequences
        sequences = {}
        for id in id_list:
            sequences[id] = []
        sequences[-1] = []

        # Get the lists of sequences
        num_ids = len(id_list)
        for x in range(0, len(lines), num_ids + 2):
            for y in range(num_ids):
                id = id_list[y]
                assert(lines[x + y][:indentation].strip() == id)
                assert(lines[x + y][indentation - 1] == ' ')
                sequence = lines[x + y][indentation:].strip()
                assert(alignment_regex.match(sequence))
                sequences[id].append(sequence)

            # Get the length of the sequence lines
            length_of_sequences = list(set(map(len, [v[-1] for k, v in sequences.iteritems() if k != -1])))
            assert(len(length_of_sequences) == 1)
            length_of_sequences = length_of_sequences[0]

            # Parse the Clustal match line
            assert(lines[x + num_ids][:indentation].strip() == '')
            match_sequence = lines[x + num_ids][indentation:indentation + length_of_sequences]
            assert(match_sequence.strip() == lines[x + num_ids].strip())
            assert(lines[x + y][indentation - 1] == ' ')
            sequences[-1].append(match_sequence)

            # Check for the empty line
            assert(lines[x + num_ids + 1].strip() == '')

        # Create the sequences, making sure that all sequences are the same length
        lengths = set()
        for k, v in sequences.iteritems():
            sequences[k] = "".join(v)
            lengths.add(len(sequences[k]))
        assert(len(lengths) == 1)

        return sequences

    def _parse_percentage_identity_output(self, percentage_identity_output):

        # Initalize matrix
        matrix = dict.fromkeys(self.sequence_ids.keys(), None)
        for x in range(len(self.sequence_ids)):
            matrix[x + 1] = {}
            for y in range(len(self.sequence_ids)):
                matrix[x + 1][y + 1] = None
            matrix[x + 1][x + 1] = 100.0

        matches = alignment_results_regex.match(percentage_identity_output)
        if matches:
            assert(len(matches.groups(0)) == 1)
            for l in matches.group(1).strip().split('\n'):
                line_matches = alignment_line_regex.match(l)
                if line_matches:
                    from_index = int(line_matches.group(1))
                    to_index = int(line_matches.group(2))
                    score = float(line_matches.group(3))
                    assert(matrix[from_index][to_index] == None)
                    assert(matrix[to_index][from_index] == None)
                    matrix[from_index][to_index] = score
                    matrix[to_index][from_index] = score

                else:
                    raise colortext.Exception("Error parsing alignment line for alignment scores. The line was:\n%s" % l)
        else:
            raise colortext.Exception("Error parsing alignment output for alignment scores. The output was:\n%s" % percentage_identity_output)

        self.matrix = matrix
        return self._create_named_matrix()

    def _create_named_matrix(self):
        matrix = self.matrix
        named_matrix = {}
        for x, line in matrix.iteritems():
            named_matrix[self.sequence_ids[x]] = {}
            for y, value in line.iteritems():
                named_matrix[self.sequence_ids[x]][self.sequence_ids[y]] = value
        self.named_matrix = named_matrix
        return named_matrix


class MultipleAlignmentException(Exception):
    '''This exception gets thrown when there are more alignments found than expected.'''
    def __init__(self, chain_id, max_expected_matches_per_chain, num_actual_matches, match_list):
        super(MultipleAlignmentException, self).__init__("Each chain was expected to match at most %d other sequences but chain %s matched %d chains: %s." % (max_expected_matches_per_chain, chain_id, num_actual_matches, ", ".join(match_list)))

class PDBUniParcSequenceAligner(object):

    ### Constructor methods ###

    def __init__(self, pdb_id, cache_dir = None, cut_off = 98.0, sequence_types = {}, replacement_pdb_id = None, added_uniprot_ACs = []):
        ''' The sequences are matched up to a percentage identity specified by cut_off (0.0 - 100.0).
            sequence_types e.g. {'A' : 'Protein', 'B' : 'RNA',...} should be passed in if the PDB file contains DNA or RNA chains. Otherwise, the aligner will attempt to match their sequences.

            replacement_pdb_id is used to get a mapping from deprecated PDB IDs to uniparc sequences. It should be the new PDB ID corresponding to the obsolete pdb_id.
            The PDB and PDBML classes parse the deprecation information from the PDB file or XML respectively and store the new PDB ID in their replacement_pdb_id variable.

        '''
        # todo: We could speed up the matching by only matching unique sequences rather than matching all sequences

        # Remove any deprecated UniProt AC records that may be stored in PDB files. This depends on the cache directory being up to date.
        added_uniprot_ACs = list(set(added_uniprot_ACs))
        for AC in added_uniprot_ACs:
            try:
                UniProtACEntry(AC, cache_dir = cache_dir)
            except:
                added_uniprot_ACs.remove(AC)

        self.pdb_id = pdb_id
        self.replacement_pdb_id = replacement_pdb_id
        self.cut_off = cut_off
        self.added_uniprot_ACs = added_uniprot_ACs
        self.sequence_types = sequence_types
        assert(0.0 <= cut_off <= 100.0)

        # Retrieve the FASTA record
        f = FASTA.retrieve(pdb_id, cache_dir = cache_dir)
        self.identical_sequences = {}
        if f.identical_sequences.get(pdb_id):
            self.identical_sequences = f.identical_sequences[pdb_id]
        f = f[pdb_id]
        self.chains = sorted(f.keys())
        self.fasta = f
        self.clustal_matches = dict.fromkeys(self.chains, None)
        self.substring_matches = dict.fromkeys(self.chains, None)
        self.alignment = {}
        self.seqres_to_uniparc_sequence_maps = {}
        self.uniparc_sequences = {}
        self.uniparc_objects = {}
        self.equivalence_fiber = {}
        self.representative_chains = []

        # Retrieve the list of associated UniParc entries
        self._get_uniparc_sequences_through_uniprot(cache_dir)

        # Reduce the set of chains to a set of chains where there is exactly one chain from the equivalence class where equivalence is defined as sequence equality
        # This is used later to reduce the amount of matching we need to do by not matching the same sequences again
        self._determine_representative_chains()

        # All of the above only needs to be run once
        # The alignment can be run multiple times with different cut-offs
        # Run an initial alignment with clustal using the supplied cut-off
        self._align_with_clustal()
        self._align_with_substrings()
        self._check_alignments()
        self._get_residue_mapping()

    ### Object methods ###

    def __getitem__(self, chain):
        return self.alignment.get(chain)

    def __repr__(self):
        s = []
        for c in sorted(self.chains):
            if self.clustal_matches.get(c):
                match_string = ['%s (%.2f%%)' % (k, v) for k, v in sorted(self.clustal_matches[c].iteritems(), key = lambda x: x[1])] # this list should have be at most one element unless the matching did not go as expected
                s.append("%s -> %s" % (c, ", ".join(match_string)))
            elif self.alignment.get(c):
                s.append("%s -> %s" % (c, self.alignment[c]))
            else:
                s.append("%s -> ?" % c)
        return "\n".join(s)

    ### API methods ###

    def realign(self, cut_off, chains_to_skip = set()):
        ''' Alter the cut-off and run alignment again. This is much quicker than creating a new PDBUniParcSequenceAligner
            object as the UniParcEntry creation etc. in the constructor does not need to be repeated.

            The chains_to_skip argument (a Set) allows us to skip chains that were already matched which speeds up the alignment even more.
        '''
        if cut_off != self.cut_off:
            self.cut_off = cut_off

            # Wipe any existing information for chains not in chains_to_skip
            for c in self.chains:
                if c not in chains_to_skip:
                    self.clustal_matches[c] = None
                    self.substring_matches[c] = None
                    if self.alignment.get(c):
                        del self.alignment[c]
                    if self.seqres_to_uniparc_sequence_maps.get(c):
                        del self.seqres_to_uniparc_sequence_maps[c]

            # Run alignment for the remaining chains
            self._align_with_clustal(chains_to_skip = chains_to_skip)
            self._align_with_substrings(chains_to_skip = chains_to_skip)
            self._check_alignments(chains_to_skip = chains_to_skip)
            self._get_residue_mapping(chains_to_skip = chains_to_skip)

    def get_alignment_percentage_identity(self, chain):
        vals = self.clustal_matches[chain].values()
        if len(vals) == 1:
            return vals[0]
        return None

    def get_uniparc_object(self, chain):
        if self.alignment.get(chain):
            return self.uniparc_objects.get(self.alignment[chain])
        return None

    ### Private methods ###

    def _determine_representative_chains(self):
        ''' Quotient the chains to get equivalence classes of chains. These will be used for the actual mapping.'''
        # todo: This logic should be moved into the FASTA class or a more general module (maybe a fast exists which uses a C/C++ library?) but at present it is easier to write here since we do not need to worry about other PDB IDs.

        equivalence_fiber = {}
        matched_chains = set()
        for chain_id, equivalent_chains in self.identical_sequences.iteritems():
            matched_chains.add(chain_id)
            equivalent_chain_ids = set()
            for equivalent_chain in equivalent_chains:
                assert(len(equivalent_chain) == 6)
                assert(equivalent_chain[:5] == '%s_' % self.pdb_id)
                equivalent_chain_ids.add(equivalent_chain[5])
            found = False
            for equivalent_chain_id in equivalent_chain_ids:
                if equivalence_fiber.get(equivalent_chain_id):
                    found = True
                    assert(equivalence_fiber[equivalent_chain_id] == equivalent_chain_ids.union(set([chain_id])))
                    break
            if not found:
                equivalence_fiber[chain_id] = set(equivalent_chain_ids)
                equivalence_fiber[chain_id].add(chain_id)

        for c in self.chains:
            if c not in matched_chains:
                equivalence_fiber[c] = set([c])

        self.equivalence_fiber = equivalence_fiber
        self.representative_chains = equivalence_fiber.keys()
        # we could remove each chain from its image in the fiber which would be marginally more efficient in the logic below but that destroys the reflexivity in the equivalence class. Mathematics would cry a little.

    def _get_uniparc_sequences_through_uniprot(self, cache_dir):
        # Retrieve the related UniParc sequences
        pdb_id = self.pdb_id
        replacement_pdb_id = self.replacement_pdb_id

        # This is the usual path. We get a PDB->UniProt/UniParc mapping using the UniProt web API. This usually works
        # if there are matches.
        # todo: We *either* use the UniProt web API *or (exclusively)* use the DBREF entries. In cases where the UniProt API has mappings for, say chain A in a PDB file but not chain B but the DBREF maps B, we will not have a mapping for B. In this case, a hybrid method would be best.
        uniparc_sequences = {}
        uniparc_objects = {}
        mapping_pdb_id = pdb_id
        pdb_uniparc_mapping = pdb_to_uniparc([pdb_id], cache_dir = cache_dir, manual_additions = {self.pdb_id : self.added_uniprot_ACs}) # we could pass both pdb_id and replacement_pdb_id here but I prefer the current (longer) logic at present

        if not pdb_uniparc_mapping.get(pdb_id):
            if replacement_pdb_id:
                mapping_pdb_id = replacement_pdb_id
                pdb_uniparc_mapping = pdb_to_uniparc([replacement_pdb_id], cache_dir = cache_dir)

        dbref_exists = False
        if not pdb_uniparc_mapping:
            # We could not get a UniProt mapping using the UniProt web API. Instead, try using the PDB DBREF fields.
            # This fixes some cases e.g. 3ZKB (at the time of writing) where the UniProt database is not up-to-date.
            uniprot_ACs = set()

            p = PDB.retrieve(pdb_id, cache_dir = cache_dir)
            uniprot_mapping = p.get_DB_references().get(pdb_id).get('UNIPROT')
            if uniprot_mapping:
                dbref_exists = True
                for chain_id, details in uniprot_mapping.iteritems():
                    uniprot_ACs.add(details['dbAccession'])

            if not(uniprot_ACs) and replacement_pdb_id:
                p = PDB.retrieve(replacement_pdb_id, cache_dir = cache_dir)
                uniprot_mapping = p.get_DB_references().get(replacement_pdb_id).get('UNIPROT')
                if uniprot_mapping:
                    for chain_id, details in uniprot_mapping.iteritems():
                        uniprot_ACs.add(details['dbAccession'])
                mapping_pdb_id = replacement_pdb_id
            else:
                mapping_pdb_id = pdb_id

            pdb_uniparc_mapping = self._get_uniparc_sequences_through_uniprot_ACs(mapping_pdb_id, list(uniprot_ACs), cache_dir)

        # If there is no mapping whatsoever found from PDB chains to UniParc sequences then we cannot continue. Again, the hybrid method mentioned in the to-do above would solve some of these cases.
        if not pdb_uniparc_mapping:
            extra_str = ''
            if not(dbref_exists):
                extra_str = ' No DBREF records were found in the PDB file.'
            if replacement_pdb_id:
                raise NoPDBUniParcMappingExists('No PDB->UniParc mapping was found for %s (obsolete) or its replacement %s.%s' % (pdb_id, replacement_pdb_id, extra_str))
            else:
                raise NoPDBUniParcMappingExists('No PDB->UniParc mapping was found for %s.%s' % (pdb_id, extra_str))

        for upe in pdb_uniparc_mapping[mapping_pdb_id]:
            uniparc_sequences[upe.UniParcID] = Sequence.from_sequence(upe.UniParcID, upe.sequence)
            uniparc_objects[upe.UniParcID] = upe
        self.uniparc_sequences = uniparc_sequences
        self.uniparc_objects = uniparc_objects

    def _get_uniparc_sequences_through_uniprot_ACs(self, mapping_pdb_id, uniprot_ACs, cache_dir):
        '''Get the UniParc sequences associated with the UniProt accession number.'''

        # Map the UniProt ACs to the UniParc IDs
        m = uniprot_map('ACC', 'UPARC', uniprot_ACs, cache_dir = cache_dir)
        UniParcIDs = []
        for _, v in m.iteritems():
            UniParcIDs.extend(v)

        # Create a mapping from the mapping_pdb_id to the UniParcEntry objects. This must match the return type from pdb_to_uniparc.
        mapping = {mapping_pdb_id : []}
        for UniParcID in UniParcIDs:
            entry = UniParcEntry(UniParcID, cache_dir = cache_dir)
            mapping[mapping_pdb_id].append(entry)

        return mapping

    def _align_with_clustal(self, chains_to_skip = set()):
        if not(self.uniparc_sequences):
            raise NoPDBUniParcMappingExists("No matches were found to any UniParc sequences.")

        for c in self.representative_chains:
            # Skip specified chains
            if c not in chains_to_skip:
                # Only align protein chains
                chain_type = self.sequence_types.get(c, 'Protein')
                if chain_type == 'Protein' or chain_type == 'Protein skeleton':

                    pdb_chain_id = '%s_%s' % (self.pdb_id, c)

                    sa = SequenceAligner()
                    try:
                        sa.add_sequence(pdb_chain_id, self.fasta[c])
                    except MalformedSequenceException:
                        self.clustal_matches[c] = {}
                        continue

                    for uniparc_id, uniparc_sequence in sorted(self.uniparc_sequences.iteritems()):
                        sa.add_sequence(uniparc_id, str(uniparc_sequence))
                    best_matches = sa.align()
                    self.clustal_matches[c] = sa.get_best_matches_by_id(pdb_chain_id, cut_off = self.cut_off)
                else:
                    # Do not try to match DNA or RNA
                    self.clustal_matches[c] = {}

        # Use the representatives' alignments for their respective equivalent classes
        for c_1, related_chains in self.equivalence_fiber.iteritems():
            for c_2 in related_chains:
                self.clustal_matches[c_2] = self.clustal_matches[c_1]

    def _align_with_substrings(self, chains_to_skip = set()):
        '''Simple substring-based matching'''
        for c in self.representative_chains:
            # Skip specified chains
            if c not in chains_to_skip:
                fasta_sequence = self.fasta[c]

                substring_matches = {}

                for uniparc_id, uniparc_sequence in sorted(self.uniparc_sequences.iteritems()):
                    uniparc_sequence = str(uniparc_sequence)
                    idx = uniparc_sequence.find(fasta_sequence)
                    if idx != -1:
                        substring_matches[uniparc_id] = 0
                    elif len(fasta_sequence) > 30:
                        idx = uniparc_sequence.find(fasta_sequence[5:-5])
                        if idx != -1:
                            substring_matches[uniparc_id] = 5
                        else:
                            idx = uniparc_sequence.find(fasta_sequence[7:-7])
                            if idx != -1:
                                substring_matches[uniparc_id] = 7
                    elif len(fasta_sequence) > 15:
                        idx = uniparc_sequence.find(fasta_sequence[3:-3])
                        if idx != -1:
                            substring_matches[uniparc_id] = 3

                self.substring_matches[c] = substring_matches

        # Use the representatives' alignments for their respective equivalent classes
        for c_1, related_chains in self.equivalence_fiber.iteritems():
            for c_2 in related_chains:
                self.substring_matches[c_2] = self.substring_matches[c_1]

    def _check_alignments(self, chains_to_skip = set()):
        max_expected_matches_per_chain = 1
        for c in self.representative_chains:
            # Skip specified chains
            if c not in chains_to_skip:
                if not(len(self.clustal_matches[c]) <= max_expected_matches_per_chain):
                    raise MultipleAlignmentException(c, max_expected_matches_per_chain, len(self.clustal_matches[c]), self.clustal_matches[c])
                assert(len(self.substring_matches[c]) == 1 or len(self.substring_matches[c]) <= len(self.clustal_matches[c]))
                if self.clustal_matches[c]:
                    if not (len(self.clustal_matches[c].keys()) == max_expected_matches_per_chain):
                        raise MultipleAlignmentException(c, max_expected_matches_per_chain, len(self.clustal_matches[c].keys()))
                    if self.substring_matches[c]:
                        if self.substring_matches[c].keys() != self.clustal_matches[c].keys():
                            print("ERROR: An inconsistent alignment was found between Clustal Omega and a substring search.")
                        else:
                            self.alignment[c] = self.clustal_matches[c].keys()[0]
                    else:
                        self.alignment[c] = self.clustal_matches[c].keys()[0]

        # Use the representatives' alignments for their respective equivalent classes. This saves memory as the same SequenceMap is used.
        for c_1, related_chains in self.equivalence_fiber.iteritems():
            for c_2 in related_chains:
                if self.alignment.get(c_1):
                    self.alignment[c_2] = self.alignment[c_1]

    def _get_residue_mapping(self, chains_to_skip = set()):
        '''Creates a mapping between the residues of the chains and the associated UniParc entries.'''
        for c in self.representative_chains:
            # Skip specified chains
            if c not in chains_to_skip:
                if self.alignment.get(c):
                    uniparc_entry = self.get_uniparc_object(c)
                    sa = SequenceAligner()
                    sa.add_sequence(c, self.fasta[c])
                    sa.add_sequence(uniparc_entry.UniParcID, uniparc_entry.sequence)
                    sa.align()
                    residue_mapping, residue_match_mapping = sa.get_residue_mapping()

                    # Create a SequenceMap
                    s = PDBUniParcSequenceMap()
                    assert(sorted(residue_mapping.keys()) == sorted(residue_match_mapping.keys()))
                    for k, v in residue_mapping.iteritems():
                        s.add(k, (uniparc_entry.UniParcID, v), residue_match_mapping[k])
                    self.seqres_to_uniparc_sequence_maps[c] = s

                else:
                    self.seqres_to_uniparc_sequence_maps[c] = PDBUniParcSequenceMap()

        # Use the representatives' alignments for their respective equivalent classes. This saves memory as the same SequenceMap is used.
        for c_1, related_chains in self.equivalence_fiber.iteritems():
            for c_2 in related_chains:
                if self.seqres_to_uniparc_sequence_maps.get(c_1):
                    self.seqres_to_uniparc_sequence_maps[c_2] = self.seqres_to_uniparc_sequence_maps[c_1]
