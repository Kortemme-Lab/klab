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
import pprint
import traceback

from klab.fs.fsio import open_temp_file, read_file
from klab.process import Popen as _Popen
from klab import colortext
from uniprot import pdb_to_uniparc, uniprot_map, UniProtACEntry, UniParcEntry
from fasta import FASTA
from pdb import PDB
from basics import SubstitutionScore, Sequence, SequenceMap, PDBUniParcSequenceMap, ChainMutation, PDBMutationPair

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

class MultipleAlignmentException(Exception):
    '''This exception gets thrown when there are more alignments found than expected.'''
    def __init__(self, chain_id, max_expected_matches_per_chain, num_actual_matches, match_list, msg = ''):
        if msg: msg = '\n' + msg
        super(MultipleAlignmentException, self).__init__("Each chain was expected to match at most %d other sequences but chain %s matched %d chains: %s.%s" % (max_expected_matches_per_chain, chain_id, num_actual_matches, ", ".join(match_list), msg))


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

    def add_sequence(self, sequence_id, sequence, ignore_bad_chains = False):
        '''If ignore_bad_chains is True then any chains containing all Xs as the sequence will be silently skipped.
           The default behavior is to raise a MalformedSequenceException in this case.'''

        # This is a sanity check. ClustalO allows ':' in the chain ID but ClustalW replaces ':' with '_' which breaks our parsing
        # All callers to add_sequence now need to replace ':' with '_' so that we can use ClustalW
        assert(sequence_id.find(':') == -1)

        if sequence_id in self.sequence_ids.values():
            raise Exception("Sequence IDs must be unique")
        if list(set(sequence)) == ['X']:
            if ignore_bad_chains:
                return
            else:
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
            #colortext.pcyan(self.alignment_output)
        except Exception, e:
            colortext.error(str(e))
            colortext.error(traceback.format_exc())
            for t in tempfiles:
                os.remove(t)
            raise

        for t in tempfiles:
            try:
                os.remove(t)
            except: pass

        return self._parse_percentage_identity_output(percentage_identity_output)


    def get_best_matches_by_id(self, id, cut_off = 98.0):
        if not self.alignment_output:
            self.align()
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
                    # "a single, fully conserved residue" - http://www.ebi.ac.uk/Tools/msa/clustalw2/help/faq.html
                    mapping[from_residue_id] = to_residue_id
                    match_mapping[from_residue_id] = SubstitutionScore(1, from_residue, to_residue)
                elif match_type == ':':
                    # "conservation between groups of strongly similar properties - scoring > 0.5 in the Gonnet PAM 250 matrix" - ibid.
                    if has_surrounding_matches:
                        mapping[from_residue_id] = to_residue_id
                        match_mapping[from_residue_id] = SubstitutionScore(0, from_residue, to_residue)
                elif match_type == '.':
                    # "conservation between groups of weakly similar properties - scoring =< 0.5 in the Gonnet PAM 250 matrix" - ibid.
                    if has_surrounding_matches:
                        mapping[from_residue_id] = to_residue_id
                        match_mapping[from_residue_id] = SubstitutionScore(-1, from_residue, to_residue)
                elif match_type == ' ':
                    # not conserved
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


class PDBUniParcSequenceAligner(object):

    ### Constructor methods ###

    def __init__(self, pdb_id, cache_dir = None, cut_off = 98.0, sequence_types = {}, replacement_pdb_id = None, added_uniprot_ACs = [], restrict_to_uniparc_values = []):
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
        self.restrict_to_uniparc_values = map(str, restrict_to_uniparc_values) # can be used to remove ambiguity - see comments in relatrix.py about this
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
                assert((equivalent_chain[:5] == '%s_' % self.pdb_id) or (equivalent_chain[:5] == '%s:' % self.pdb_id)) # ClustalW changes e.g. 1KI1:A to 1KI1_A in its output
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

        #pprint.pprint(self.representative_chains)
        #pprint.pprint(self.equivalence_fiber)

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
            #print(upe.UniParcID, upe.sequence)
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
                #print('chain_type', chain_type, c)
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
                    #colortext.pcyan(sa.alignment_output)
                    self.clustal_matches[c] = sa.get_best_matches_by_id(pdb_chain_id, cut_off = self.cut_off)
                    #colortext.plightpurple(self.cut_off)
                    #pprint.pprint(sa.get_best_matches_by_id(pdb_chain_id, cut_off = self.cut_off))
                    #colortext.plightpurple(60.0)
                    #pprint.pprint(sa.get_best_matches_by_id(pdb_chain_id, cut_off = 60.0))
                else:
                    # Do not try to match DNA or RNA
                    self.clustal_matches[c] = {}

        # Restrict the matches to a given set of UniParc IDs. This can be used to remove ambiguity when the correct mapping has been determined e.g. from the SIFTS database.
        if self.restrict_to_uniparc_values:
            for c in self.representative_chains:
                if set(map(str, self.clustal_matches[c].keys())).intersection(set(self.restrict_to_uniparc_values)) > 0:
                    # Only restrict in cases where there is at least one match in self.restrict_to_uniparc_values
                    # Otherwise, chains which are not considered in self.restrict_to_uniparc_values may throw away valid matches
                    # e.g. when looking for structures related to 1KTZ (A -> P10600 -> UPI000000D8EC, B -> P37173 -> UPI000011DD7E),
                    #      we find the close match 2PJY. However, 2PJY has 3 chains: A -> P10600, B -> P37173, and C -> P36897 -> UPI000011D62A
                    restricted_matches = dict((str(k), self.clustal_matches[c][k]) for k in self.clustal_matches[c].keys() if str(k) in self.restrict_to_uniparc_values)
                    if len(restricted_matches) != len(self.clustal_matches[c]):
                        removed_matches = sorted(set(self.clustal_matches[c].keys()).difference(set(restricted_matches)))
                        #todo: add silent option to class else colortext.pcyan('Ignoring {0} as those chains were not included in the list self.restrict_to_uniparc_values ({1}).'.format(', '.join(removed_matches), ', '.join(self.restrict_to_uniparc_values)))
                    self.clustal_matches[c] = restricted_matches

        # Use the representatives' alignments for their respective equivalent classes
        for c_1, related_chains in self.equivalence_fiber.iteritems():
            for c_2 in related_chains:
                self.clustal_matches[c_2] = self.clustal_matches[c_1]


    def _align_with_substrings(self, chains_to_skip = set()):
        '''Simple substring-based matching'''
        for c in self.representative_chains:
            # Skip specified chains
            if c not in chains_to_skip:
                #colortext.pcyan(c)
                #colortext.warning(self.fasta[c])
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

        # Restrict the matches to a given set of UniParc IDs. This can be used to remove ambiguity when the correct mapping has been determined e.g. from the SIFTS database.
        colortext.pcyan('*' * 100)
        pprint.pprint(self.substring_matches)
        if self.restrict_to_uniparc_values:
            for c in self.representative_chains:
                #print('HERE!')
                #print(c)
                if set(map(str, self.substring_matches[c].keys())).intersection(set(self.restrict_to_uniparc_values)) > 0:
                    # Only restrict in cases where there is at least one match in self.restrict_to_uniparc_values
                    # Otherwise, chains which are not considered in self.restrict_to_uniparc_values may throw away valid matches
                    # e.g. when looking for structures related to 1KTZ (A -> P10600 -> UPI000000D8EC, B -> P37173 -> UPI000011DD7E),
                    #      we find the close match 2PJY. However, 2PJY has 3 chains: A -> P10600, B -> P37173, and C -> P36897 -> UPI000011D62A
                    restricted_matches = dict((str(k), self.substring_matches[c][k]) for k in self.substring_matches[c].keys() if str(k) in self.restrict_to_uniparc_values)
                    if len(restricted_matches) != len(self.substring_matches[c]):
                        removed_matches = sorted(set(self.substring_matches[c].keys()).difference(set(restricted_matches)))
                        # todo: see above re:quiet colortext.pcyan('Ignoring {0} as those chains were not included in the list self.restrict_to_uniparc_values ({1}).'.format(', '.join(removed_matches), ', '.join(self.restrict_to_uniparc_values)))
                    self.substring_matches[c] = restricted_matches
        #pprint.pprint(self.substring_matches)
        #colortext.pcyan('*' * 100)

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

                #colortext.message('Chain {0}'.format(c))
                #pprint.pprint(self.substring_matches)
                #pprint.pprint(self.clustal_matches)
                #pprint.pprint(self.substring_matches[c])
                #pprint.pprint(self.clustal_matches[c])

                if not (len(self.substring_matches[c]) == 1 or len(self.substring_matches[c]) <= len(self.clustal_matches[c])):
                    #pprint.pprint(self.clustal_matches[c])
                    #pprint.pprint(self.substring_matches[c])

                    match_list = sorted(set((self.clustal_matches[c].keys() or []) + (self.substring_matches[c].keys()  or [])))
                    raise MultipleAlignmentException(c, max_expected_matches_per_chain, max(len(self.substring_matches[c]), len(self.clustal_matches[c])), match_list, msg = 'More matches were found using the naive substring matching than the Clustal matching. Try lowering the cut-off (currently set to {0}).'.format(self.cut_off))

                if self.clustal_matches[c]:
                    if not (len(self.clustal_matches[c].keys()) == max_expected_matches_per_chain):
                        match_list = sorted(set((self.clustal_matches[c].keys() or []) + (self.substring_matches[c].keys()  or [])))
                        raise MultipleAlignmentException(c, max_expected_matches_per_chain, len(self.clustal_matches[c].keys()), match_list)
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



class PDBChainSequenceAligner(object):
    '''This is a useful utility class which allows you to quickly figure out when sequences are identical on their overlap or what the mutations are.
       I used this in the DDG project to investigate PDB files to determine overlap between the binding affinity datasets.

       Example usage:

            pcsa = PDBChainSequenceAligner(initial_chains = [('2GOO', 'A'), ('2GOO', 'D'), ('2H62', 'A'), ('2H62', 'B')], cache_dir = '/tmp')
            output, best_matches = pcsa.align()
            colortext.warning(pprint.pformat(best_matches))
    '''


    def __init__(self, initial_chains = [], cache_dir = None):
        '''initial_chains should be a list of (pdb_id, chain_id) tuples/lists.'''
        self.cache_dir = cache_dir
        self.pdb_chains = []
        for ic in initial_chains:
            self.add(ic[0], ic[1])


    def add(self, pdb_id, chain_id, sequence = None):
        assert(len(chain_id) == 1)
        if len(pdb_id) == 4 and not sequence:
            # RCSB files
            f = FASTA.retrieve(pdb_id, cache_dir = self.cache_dir)
            #print(f[pdb_id][chain_id])
            sequence = f[pdb_id][chain_id]
        self.pdb_chains.append(dict(
            pdb_id = pdb_id,
            chain_id = chain_id,
            sequence = sequence,
        ))


    def align(self, alignment_tool = 'clustalw', gap_opening_penalty = 0.2, ignore_bad_chains = False):
        '''If ignore_bad_chains is True then any chains containing all Xs as the sequence will be silently skipped.
           The default behavior is to raise a MalformedSequenceException in this case.'''
        if len(self.pdb_chains) > 1:
            sa = SequenceAligner(alignment_tool = alignment_tool, gap_opening_penalty = gap_opening_penalty)
            for pdb_chain in self.pdb_chains:
                sa.add_sequence('%s_%s' % (pdb_chain['pdb_id'], pdb_chain['chain_id']), pdb_chain['sequence'], ignore_bad_chains = ignore_bad_chains)
            best_matches = sa.align()
            return sa.alignment_output, best_matches
        else:
            raise Exception('Cannot align sequences - less than two chains were specified.')


class PDBSeqresSequenceAligner(object):
    '''This is a useful utility class to compare unique chains in RCSB PDB files and print the sequence alignments.

       Example usage:

           pssa = PDBSeqresSequenceAligner('2AJF', '3D0G')
           representative_alignment_output, chain_mapping, summary = pssa.get_representative_alignment()
           print(representative_alignment_output)
           colortext.warning(pprint.pformat(chain_mapping))
    '''

    def __init__(self, pdb_id_1, pdb_id_2, pdb_1 = None, pdb_2 = None, bio_cache = None, cache_dir = None, cut_off = 70.0, alignment_tool = 'clustalw', gap_opening_penalty = 0.2, ignore_bad_chains = False):

        self.pdb_id_1 = pdb_id_1
        self.pdb_id_2 = pdb_id_2
        self.bio_cache = bio_cache
        self.cache_dir = cache_dir
        if (not self.cache_dir) and self.bio_cache:
            self.cache_dir = self.bio_cache.cache_dir

        if self.bio_cache:
            self.pdb_1 = self.bio_cache.get_pdb_object(pdb_id_1)
            self.pdb_2 = self.bio_cache.get_pdb_object(pdb_id_2)
        else:
            self.pdb_1 = PDB.retrieve(pdb_id_1, cache_dir = self.cache_dir)
            self.pdb_2 = PDB.retrieve(pdb_id_2, cache_dir = self.cache_dir)

        self.best_matches = None
        self.complete_alignment_output = None
        self.representative_alignment_output = None
        self.summary = None
        self.alignment_tool = alignment_tool
        self.gap_opening_penalty = gap_opening_penalty
        self.ignore_bad_chains = ignore_bad_chains
        self.cut_off = cut_off

        self.alignments = {}  # Chain in pdb_1 -> Chain in pdb_2 -> alignment object
        self.seqres_sequence_maps = {}  # Chain in pdb_1 -> Chain in pdb_2 -> residue map (from sequence index to sequence index)
        self.atom_sequence_maps = {}

        self.seqres_to_atom_maps_1, self.atom_to_seqres_maps_1 = self.pdb_1.construct_seqres_to_atom_residue_map()
        self.seqres_to_atom_maps_2, self.atom_to_seqres_maps_2 = self.pdb_2.construct_seqres_to_atom_residue_map()


    def align(self):
        alignment_tool, gap_opening_penalty, ignore_bad_chains = self.alignment_tool, self.gap_opening_penalty, self.ignore_bad_chains
        if not(self.best_matches) or not(self.complete_alignment_output):
            sa = SequenceAligner(alignment_tool = alignment_tool, gap_opening_penalty = gap_opening_penalty)
            for chain_id, seq in sorted(self.pdb_1.seqres_sequences.iteritems()):
                sa.add_sequence('{0}_{1}'.format(self.pdb_id_1, chain_id), str(seq), ignore_bad_chains = ignore_bad_chains)
            for chain_id, seq in sorted(self.pdb_2.seqres_sequences.iteritems()):
                sa.add_sequence('{0}_{1}'.format(self.pdb_id_2, chain_id), str(seq), ignore_bad_chains = ignore_bad_chains)
            self.best_matches = sa.align()
            self.complete_alignment_output = sa.alignment_output


    def get_representative_alignment(self):

        # Perform a global alignment of all chains
        self.align()

        # Based on the alignment, determine which chains map best to each other
        pdb_1_self_mapping = {}
        pdb_2_self_mapping = {}
        chain_mapping = {}
        covered_pdb_1_chains = set()
        covered_pdb_2_chains = set()
        for chain_id in sorted(self.pdb_1.seqres_sequences.keys()):
            if chain_id in covered_pdb_1_chains:
                continue
            covered_pdb_1_chains.add(chain_id)

            for pdb_chain, match in sorted(self.best_matches['{0}_{1}'.format(self.pdb_id_1, chain_id)].items(), key = lambda x: x[1], reverse = True):
                other_pdb_chain_letter = pdb_chain.split('_')[1]
                if pdb_chain.startswith(self.pdb_id_1):
                    if match == 100.0:
                        covered_pdb_1_chains.add(other_pdb_chain_letter)
                        pdb_1_self_mapping[chain_id] = pdb_1_self_mapping.get(chain_id, [])
                        pdb_1_self_mapping[chain_id].append(other_pdb_chain_letter)
                else:
                    assert(pdb_chain.startswith(self.pdb_id_2))
                    if not(chain_mapping.get(chain_id)):
                        chain_mapping[chain_id] = (other_pdb_chain_letter, match)

        for chain_id in sorted(self.pdb_2.seqres_sequences.keys()):
            if chain_id in covered_pdb_2_chains:
                continue
            covered_pdb_2_chains.add(chain_id)

            for pdb_chain, match in sorted(self.best_matches['{0}_{1}'.format(self.pdb_id_2, chain_id)].items(), key = lambda x: x[1], reverse = True):
                other_pdb_chain_letter = pdb_chain.split('_')[1]
                if pdb_chain.startswith(self.pdb_id_2):
                    if match == 100.0:
                        covered_pdb_2_chains.add(other_pdb_chain_letter)
                        pdb_2_self_mapping[chain_id] = pdb_2_self_mapping.get(chain_id, [])
                        pdb_2_self_mapping[chain_id].append(other_pdb_chain_letter)

        # chain_mapping is a mapping of pdb_1 chains to a representative of the best match in pdb_2
        # we now create individual alignments for each case in the mapping

        #self.alignments
        self.representative_alignment_output = ''
        for chain_1, chain_2_pair in chain_mapping.iteritems():
            chain_2 = chain_2_pair[0]
            sa = self._align_chains(chain_1, chain_2)
            self.representative_alignment_output += sa.alignment_output + '\n'
        #get_residue_mapping

        self.summary = ''
        for chain_id, related_chains in pdb_1_self_mapping.iteritems():
            self.summary += 'Chain {0} of {1} represents chains {2} of {1}.\n'.format(chain_id, self.pdb_id_1, ', '.join(sorted(related_chains)))
        for chain_id, related_chains in pdb_2_self_mapping.iteritems():
            self.summary += 'Chain {0} of {1} represents chains {2} of {1}.\n'.format(chain_id, self.pdb_id_2, ', '.join(sorted(related_chains)))
        for chain_id, mtch in sorted(chain_mapping.iteritems()):
            self.summary += 'Chain {0} of {1} matches chain {2} of {3} (and its represented chains) at {4}%.\n'.format(chain_id, self.pdb_id_1, mtch[0], self.pdb_id_2, mtch[1])

        return self.representative_alignment_output, chain_mapping, self.summary


    def _align_chains(self, chain_1, chain_2):
        alignment_tool, gap_opening_penalty, ignore_bad_chains = self.alignment_tool, self.gap_opening_penalty, self.ignore_bad_chains
        if (chain_1, chain_2) in self.alignments:
            return self.alignments[(chain_1, chain_2)]
        else:
            sa = SequenceAligner(alignment_tool=alignment_tool, gap_opening_penalty=gap_opening_penalty)
            sa.add_sequence('{0}_{1}'.format(self.pdb_id_1, chain_1), str(self.pdb_1.seqres_sequences[chain_1]), ignore_bad_chains=ignore_bad_chains)
            sa.add_sequence('{0}_{1}'.format(self.pdb_id_2, chain_2), str(self.pdb_2.seqres_sequences[chain_2]), ignore_bad_chains=ignore_bad_chains)
            sa.align()
            self.alignments[(chain_1, chain_2)] = sa
            return sa


    def build_residue_mappings(self, from_chain = None, to_chain = None):

        alignment_tool, gap_opening_penalty, ignore_bad_chains = self.alignment_tool, self.gap_opening_penalty, self.ignore_bad_chains

        # ...
        if not self.alignments:
            self.get_representative_alignment()
        assert(self.alignments)

        #matched_chains = self.alignments = {} # Chain in pdb_1 -> Chain in pdb_2 -> alignment object

        # Perform individual alignments for all best-matched chains
        for chain_1 in sorted(self.pdb_1.seqres_sequences.keys()):
            if from_chain != None and from_chain != chain_1:
                continue

            #self.alignments[chain_1] = self.alignments.get(chain_1, {})
            self.seqres_sequence_maps[chain_1] = self.seqres_sequence_maps.get(chain_1, {})
            self.atom_sequence_maps[chain_1] = self.atom_sequence_maps.get(chain_1, {})

            best_match_percentage = None
            for pdb_chain, match in sorted(self.best_matches['{0}_{1}'.format(self.pdb_id_1, chain_1)].items(), key=lambda x: x[1], reverse=True):
                if pdb_chain.startswith(self.pdb_id_1):
                    continue
                chain_2 = pdb_chain.split('_')[1]
                if best_match_percentage == None or best_match_percentage == match:
                    best_match_percentage = match
                    if match < self.cut_off:
                        # Do not bother aligning sequences below the sequence identity cut-off
                        continue
                    elif from_chain != None and from_chain != chain_1:
                        continue
                    elif to_chain != None and to_chain != chain_2:
                        continue
                    else:
                        sa = self._align_chains(chain_1, chain_2)
                        self.seqres_sequence_maps[chain_1][chain_2] = sa.get_residue_mapping()

                    # self.seqres_sequence_maps contains the mappings between SEQRES sequences
        #
        for chain_1, matched_chains in self.seqres_sequence_maps.iteritems():
            self.atom_sequence_maps[chain_1] = self.atom_sequence_maps.get(chain_1, {})
            for chain_2, residue_mappings in matched_chains.iteritems():

                if not self.atom_sequence_maps[chain_1].get(chain_2):
                    self.atom_sequence_maps[chain_1][chain_2] = {}

                    # mapping is a SEQRES -> SEQRES mapping
                    mapping, match_mapping = residue_mappings

                    if chain_1 in self.seqres_to_atom_maps_1 and chain_2 in self.seqres_to_atom_maps_2:
                        for seqres_res_1, atom_res_1 in sorted(self.seqres_to_atom_maps_1[chain_1].iteritems()):
                            if seqres_res_1 in mapping:
                                seqres_res_2 = mapping[seqres_res_1]
                                if seqres_res_2 in self.seqres_to_atom_maps_2[chain_2]:
                                    atom_res_2 = self.seqres_to_atom_maps_2[chain_2][seqres_res_2]
                                    self.atom_sequence_maps[chain_1][chain_2][atom_res_1] = atom_res_2


    def get_atom_residue_mapping(self, from_chain, to_chain = None):
        self.build_residue_mappings(from_chain, to_chain)
        return self.atom_sequence_maps.get(from_chain, {}).get(to_chain, None)


    def get_matching_chains(self, from_chain):
        self.build_residue_mappings()
        return sorted([p[1] for p in self.alignments.keys() if p[0] == from_chain])


    def map_atom_residue(self, from_chain, to_chain, atom_res_1):
        # atom_res_1 should not include the chain ID
        self.build_residue_mappings(from_chain, to_chain)
        return self.atom_sequence_maps.get(from_chain, {}).get(to_chain, {}).get('{0}{1}'.format(from_chain, atom_res_1), None)


class SIFTSChainMutatorSequenceAligner(object):
    '''This is a useful utility class to generate a list of mutations between PDB files covered by SIFTS. It is used in the
       SpiderWebs project.

       Example usage:

           import pprint
           from klab.bio.clustalo import SIFTSChainMutatorSequenceAligner
           scmsa = SIFTSChainMutatorSequenceAligner(bio_cache = bio_cache)
           mutations = scmsa.get_mutations('2AJF', 'A', '3D0G', 'A')
           if mutations:
               print('{0} mismatches:\n{1}'.format(len(mutations), pprint.pformat(mutations)))

    '''

    def __init__(self, bio_cache = None, cache_dir = None, acceptable_sifts_sequence_percentage_match = 60.0, acceptable_sequence_similarity = 85.0):

        self.pdbs = {}
        self.alignments = {}
        self.chain_map = {}             # maps PDB ID 1 -> chain ID in PDB ID 1 -> PDB ID 2 -> Set[chain IDs in PDB ID 2]
        self.bio_cache = bio_cache
        self.cache_dir = cache_dir
        self.acceptable_sequence_similarity = acceptable_sequence_similarity
        self.seqres_sequence_maps = {}  # maps Tuple(PDB ID 1, chain ID in PDB ID 1) -> Tuple(PDB ID 2, chain ID in PDB ID 2) -> SequenceMap object based on an alignment from the first chain to the second
        self.acceptable_sifts_sequence_percentage_match = acceptable_sifts_sequence_percentage_match
        if (not self.cache_dir) and self.bio_cache:
            self.cache_dir = self.bio_cache.cache_dir


    def add_pdb(self, pdb_id):
        from klab.bio.sifts import SIFTS

        pdb_id = pdb_id.upper()
        if not self.pdbs.get(pdb_id):

            # Create the SIFTS objects
            try:
                if self.bio_cache:
                    sifts_object = self.bio_cache.get_sifts_object(pdb_id, acceptable_sequence_percentage_match = self.acceptable_sifts_sequence_percentage_match)
                else:
                    sifts_object = SIFTS.retrieve(pdb_id, cache_dir = self.cache_dir, acceptable_sequence_percentage_match = self.acceptable_sifts_sequence_percentage_match)
                sifts_object._create_inverse_maps()
            except:
                colortext.error('An exception occurred creating the SIFTS object for {0}.'.format(pdb_id))
                raise

            try:
                if self.bio_cache:
                    pdb_object = self.bio_cache.get_pdb_object(pdb_id)
                else:
                    pdb_object = PDB(sifts_object.pdb_contents)
            except:
                colortext.error('An exception occurred creating the PDB object for {0}.'.format(pdb_id))
                raise

            self.pdbs[pdb_id.upper()] = dict(
                id = pdb_id,
                sifts = sifts_object,
                pdb = pdb_object,
            )
        return self.pdbs[pdb_id]


    def get_alignment(self, pdb_id_1, pdb_id_2, alignment_tool = 'clustalw', gap_opening_penalty = 0.2):

        # Set up the objects
        p1 = self.add_pdb(pdb_id_1)
        p2 = self.add_pdb(pdb_id_2)
        pdb_1 = p1['pdb']
        pdb_2 = p2['pdb']

        # Run a sequence alignment on the sequences
        if not self.alignments.get(pdb_id_1, {}).get(pdb_id_2):
            self.alignments[pdb_id_1] = self.alignments.get(pdb_id_1, {})
            sa = SequenceAligner(alignment_tool = alignment_tool, gap_opening_penalty = gap_opening_penalty)
            for chain_id, seq in sorted(pdb_1.seqres_sequences.iteritems()):
                sa.add_sequence('{0}_{1}'.format(pdb_id_1, chain_id), str(seq), ignore_bad_chains = True)
            for chain_id, seq in sorted(pdb_2.seqres_sequences.iteritems()):
                sa.add_sequence('{0}_{1}'.format(pdb_id_2, chain_id), str(seq), ignore_bad_chains = True)
            self.alignments[pdb_id_1][pdb_id_2] = dict(
                alignment = sa,
                best_matches = sa.align()
            )
        return self.alignments[pdb_id_1][pdb_id_2]


    def get_mutations(self, pdb_id_1, pdb_id_2, alignment_tool = 'clustalw', gap_opening_penalty = 0.2):
        '''Returns a mapping chain_of_pdb_1 -> List[PDBMutationPair] representing the mutations needed to transform each chain of pdb_1 into the respective chains of pdb_2.
           This function also sets self.seqres_sequence_maps, a mapping Tuple(pdb_id_1, chain ID in pdb_id_1) -> Tuple(pdb_id_2, chain ID in pdb_id_2) -> a SequenceMap representing the mapping of residues between the chains based on the alignment.

           Warning: This function does not consider what happens if a chain in pdb_id_1 matches two chains in pdb_id_2
                    which have differing sequences. In this case, an self-inconsistent set of mutations is returned.
                    One solution would be to extend the mapping to:

                        chain_m_of_pdb_1 -> common_mutations -> List[PDBMutationPair]
                                         -> chain_x_of_pdb_2 -> List[PDBMutationPair]
                                         -> chain_y_of_pdb_2 -> List[PDBMutationPair]
                                         ...

                    where common_mutations contains the set of mutations common to the mapping m->x and m->y etc. whereas the
                    other two mappings contain the set of mutations from m->x or m->y etc. respectively which do not occur in
                    common_mutations. In general, both chain_x_of_pdb_2 and chain_y_of_pdb_2 will be empty excepting the
                    considered case where x and y differ in sequence.
        '''

        # Set up the objects
        p1 = self.add_pdb(pdb_id_1)
        p2 = self.add_pdb(pdb_id_2)
        self.chain_map[pdb_id_1] = self.chain_map.get(pdb_id_1, {})

        # Determine which chains map to which
        alignment = self.get_alignment(pdb_id_1, pdb_id_2, alignment_tool = alignment_tool, gap_opening_penalty = gap_opening_penalty)
        best_matches = alignment['best_matches']

        # Create the list of mutations
        mutations = {}
        for from_chain, mtches in sorted(best_matches.iteritems()):

            from_pdb_id, from_chain_id = from_chain.split('_')

            # Only consider matches from pdb_id_1 to pdb_id_2
            if from_pdb_id == pdb_id_1:

                self.seqres_sequence_maps[(from_pdb_id, from_chain_id)] = {}

                self.chain_map[from_pdb_id][from_chain_id] = self.chain_map[from_pdb_id].get(from_chain_id, {})

                # Do not consider matches from pdb_id_1 to itself or matches with poor sequence similarity
                restricted_mtchs = {}
                for to_chain, similarity in sorted(mtches.iteritems()):
                    if to_chain.split('_')[0] == pdb_id_2 and similarity >= self.acceptable_sequence_similarity:
                        restricted_mtchs[to_chain] = similarity

                # Take the best matching chains and create a list of mutations needed to transform from_chain to those chains
                # Warning: This does NOT take into account whether the sequences of the best matches differ.
                if restricted_mtchs:
                    top_similarity = max(restricted_mtchs.values())

                    #todo: if the sequences of the best matches differ, raise an Exception. Use 2ZNW and 1DQJ as an example (2ZNW chain A matches with 48% to both 1DQJ chain A and chain B)
                    #top_matches = [to_chain for to_chain, similarity in sorted(restricted_mtchs.iteritems()) if similarity == top_similarity]
                    #pprint.pprint(restricted_mtchs)
                    #print(from_pdb_id, from_chain, 'top_matches', top_matches)
                    #sys.exit(0)


                    for to_chain, similarity in sorted(restricted_mtchs.iteritems()):
                        to_pdb_id, to_chain_id = to_chain.split('_')
                        if similarity == top_similarity:
                            #print(from_pdb_id, from_chain_id)
                            #print(restricted_mtchs)
                            #print(to_pdb_id, to_chain, similarity)
                            self.chain_map[from_pdb_id][from_chain_id][to_pdb_id] = self.chain_map[from_pdb_id][from_chain_id].get(to_pdb_id, set())
                            self.chain_map[from_pdb_id][from_chain_id][to_pdb_id].add(to_chain)
                            mutations[from_chain_id] = mutations.get(from_chain_id, [])
                            chain_mutations = self.get_chain_mutations(from_pdb_id, from_chain_id, to_pdb_id, to_chain_id)
                            mutations[from_chain_id].extend(chain_mutations)

        # mutations can contain duplicates so we remove those
        for chain_id, mlist in mutations.iteritems():
            mutations[chain_id] = sorted(set(mlist))
        return mutations


    def get_corresponding_chains(self, from_pdb_id, from_chain_id, to_pdb_id):
        '''Should be called after get_mutations.'''
        chains = self.chain_map.get(from_pdb_id, {}).get(from_chain_id, {}).get(to_pdb_id, [])
        return sorted(chains)


    def get_chain_mutations(self, pdb_id_1, chain_1, pdb_id_2, chain_2):
        '''Returns a list of tuples each containing a SEQRES Mutation object and an ATOM Mutation object representing the
           mutations from pdb_id_1, chain_1 to pdb_id_2, chain_2.

           SequenceMaps are constructed in this function between the chains based on the alignment.

           PDBMutationPair are returned as they are hashable and amenable to Set construction to eliminate duplicates.
           '''

        # Set up the objects
        p1 = self.add_pdb(pdb_id_1)
        p2 = self.add_pdb(pdb_id_2)
        sifts_1, pdb_1 = p1['sifts'], p1['pdb']
        sifts_2, pdb_2 = p2['sifts'], p2['pdb']

        # Set up the sequences
        #pprint.pprint(sifts_1.seqres_to_atom_sequence_maps)
        seqres_to_atom_sequence_maps_1 = sifts_1.seqres_to_atom_sequence_maps.get(chain_1, {}) # this is not guaranteed to exist e.g. 2ZNW chain A
        seqres_1, atom_1 = pdb_1.seqres_sequences.get(chain_1), pdb_1.atom_sequences.get(chain_1)
        seqres_2, atom_2 = pdb_2.seqres_sequences.get(chain_2), pdb_2.atom_sequences.get(chain_2)
        if not seqres_1: raise Exception('No SEQRES sequence for chain {0} of {1}.'.format(chain_1, pdb_1))
        if not atom_1: raise Exception('No ATOM sequence for chain {0} of {1}.'.format(chain_1, pdb_1))
        if not seqres_2: raise Exception('No SEQRES sequence for chain {0} of {1}.'.format(chain_2, pdb_2))
        if not atom_2: raise Exception('No ATOM sequence for chain {0} of {1}.'.format(chain_2, pdb_2))
        seqres_str_1 = str(seqres_1)
        seqres_str_2 = str(seqres_2)

        # Align the SEQRES sequences
        sa = SequenceAligner()
        sa.add_sequence('{0}_{1}'.format(pdb_id_1, chain_1), seqres_str_1)
        sa.add_sequence('{0}_{1}'.format(pdb_id_2, chain_2), seqres_str_2)
        sa.align()
        seqres_residue_mapping, seqres_match_mapping = sa.get_residue_mapping()
        #colortext.pcyan(sa.alignment_output)

        # Create a SequenceMap
        seqres_sequence_map = SequenceMap()
        assert(sorted(seqres_residue_mapping.keys()) == sorted(seqres_match_mapping.keys()))
        for k, v in seqres_residue_mapping.iteritems():
            seqres_sequence_map.add(k, v, seqres_match_mapping[k])
        self.seqres_sequence_maps[(pdb_id_1, chain_1)][(pdb_id_2, chain_2)] = seqres_sequence_map

        # Determine the mutations between the SEQRES sequences and use these to generate a list of ATOM mutations
        mutations = []
        clustal_symbols = SubstitutionScore.clustal_symbols

        #print(pdb_id_1, chain_1, pdb_id_2, chain_2)
        #print(seqres_to_atom_sequence_maps_1)

        for seqres_res_id, v in seqres_match_mapping.iteritems():
            # Look at all positions which differ. seqres_res_id is 1-indexed, following the SEQRES and UniProt convention. However, so our our Sequence objects.
            if clustal_symbols[v.clustal] != '*':

                # Get the wildtype Residue objects
                seqres_wt_residue = seqres_1[seqres_res_id]
                #print(seqres_wt_residue)
                seqres_mutant_residue = seqres_2[seqres_residue_mapping[seqres_res_id]] # todo: this will probably fail for some cases where there is no corresponding mapping

                # If there is an associated ATOM record for the wildtype residue, get its residue ID
                atom_res_id = None
                atom_chain_res_id = seqres_to_atom_sequence_maps_1.get(seqres_res_id)
                try:
                    if atom_chain_res_id:
                        assert(atom_chain_res_id[0] == chain_1)
                        atom_residue = atom_1[atom_chain_res_id]
                        atom_res_id = atom_chain_res_id[1:]
                        assert(atom_residue.ResidueAA == seqres_wt_residue.ResidueAA)
                        assert(atom_residue.ResidueID == atom_res_id)
                except:
                    atom_res_id = None
                    if seqres_wt_residue.ResidueAA != 'X':
                        # we do not seem to keep ATOM records for unknown/non-canonicals: see 2BTF chain A -> 2PBD chain A
                        raise

                # Create two mutations - one for the SEQRES residue and one for the corresponding (if any) ATOM residue
                # We create both so that the user is informed whether there is a mutation between the structures which is
                # not captured by the coordinates.
                # If there are no ATOM coordinates, there is no point creating an ATOM mutation object so we instead use
                # the None type. This also fits with the approach in the SpiderWeb framework.
                seqres_mutation = ChainMutation(seqres_wt_residue.ResidueAA, seqres_res_id,seqres_mutant_residue.ResidueAA, Chain = chain_1)
                atom_mutation = None
                if atom_res_id:
                    atom_mutation = ChainMutation(seqres_wt_residue.ResidueAA, atom_res_id, seqres_mutant_residue.ResidueAA, Chain = chain_1)

                mutations.append(PDBMutationPair(seqres_mutation, atom_mutation))

        return mutations
