#!/usr/bin/python
# encoding: utf-8
"""
clustalo.py
Wrapper functions for Clustal Omega.

Created by Shane O'Connor 2013
"""

import os
import shlex
import re
import commands
import platform

from tools.fs.io import open_temp_file, read_file
from tools.process import Popen as _Popen
from tools import colortext
from uniprot import pdb_to_uniparc
from fasta import FASTA
from basics import SubstitutionScore, Sequence, SequenceMap

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


class SequenceAligner(object):
    ''' This class is used to align sequences. To use it, first add sequences using the add_sequence function. Next, call the align function to perform
        the alignment. Alignment results are stored in the following object variables:
            matrix : the 1-indexed matrix returned from clustalw
            named_matrix : [finish this on Monday...]

        e.g.
            sa = SequenceAligner()
            sa.add_sequence('1A2P:A', 'AQVINTFDGVADYLQTYHKLPDNYITKSEAQALGWVASKGNLADVAPGKSIGGDIFSNREGKLPGKSGRTWREADINYTSGFRNSDRILYSSDWLIYKTTDHYQTFTKIR')
            sa.add_sequence('1B20:A', 'AQVINTFDGVADYLQTYHKLPDNYITKSEAQALGWVASKGNLADVAPGKSIGGDIFSNREGKLPGKSGSTWREADINYTSGFRNSDRILYSSDWLIYKTTDHYQTFTKIR')
            sa.add_sequence('2KF4:A', 'AQVINTFDGVADYLQTYHKLPDNYITKSEAQALGWVASKGNLADVAPGKSIGGDIFSNREGKLPGKSGRTWREADINYTSGFRNSDRILYSSDWLIYKTTDAYQTFTKIR')
            best_matches = sa.align() # {'2KF4:A': {'2KF4:A': 100.0, '1A2P:A': 99.0, '1B20:A': 98.0}, '1A2P:A': {'2KF4:A': 99.0, '1A2P:A': 100.0, '1B20:A': 99.0}, '1B20:A': {'2KF4:A': 98.0, '1A2P:A': 99.0, '1B20:A': 100.0}}
            best_matches_by_id = sa.get_best_matches_by_id('2KF4:A') # {'1A2P:A': 99.0, '1B20:A': 98.0}

    '''

    ### Constructor ###

    def __init__(self):
        self.records = []
        self.sequence_ids = {} # A 1-indexed list of the sequences in the order that they were added (1-indexing to match Clustal numbering)
        self.matrix = None
        self.named_matrix = None
        self.alignment_output = None

    ### API methods ###

    def add_sequence(self, sequence_id, sequence):
        if sequence_id in self.sequence_ids.values():
            raise Exception("Sequence IDs must be unique")
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
            p = _Popen('.', shlex.split('clustalo --infile %(fasta_filename)s --verbose --outfmt clustal --outfile %(clustal_filename)s --force' % vars()))
            if p.errorcode:
                raise Exception('An error occurred while calling clustalo to align sequences:\n%s' % p.stderr)
            self.alignment_output = read_file(clustal_filename)

            p = _Popen('.', shlex.split('clustalw -INFILE=%(clustal_filename)s -PIM -TYPE=PROTEIN -STATS=%(stats_filename)s -OUTFILE=/dev/null' % vars()))
            if p.errorcode:
                raise Exception('An error occurred while calling clustalw to generate the Percent Identity Matrix:\n%s' % p.stderr)
            else:
                tempfiles.append("%s.dnd" % clustal_filename)
                percentage_identity_output = p.stdout
        except:
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
                else:
                    assert(match_type == ' ')

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

        if len(self.sequence_ids) != 2:
            # No need to write the general version at this date
            return None

        # Strip the boilerplate lines
        lines = self.alignment_output.split("\n")
        assert(lines[0].startswith('CLUSTAL'))
        lines = '\n'.join(lines[1:]).lstrip().split('\n')

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

        # Create the sequences
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

    def __init__(self, pdb_id, cache_dir = None, cut_off = 98.0, sequence_types = {}):
        ''' The sequences are matched up to a percentage identity specified by cut_off (0.0 - 100.0).
            sequence_types e.g. {'A' : 'Protein', 'B' : 'RNA',...} should be passed in if the PDB file contains DNA or RNA chains. Otherwise, the aligner will attempt to match their sequences.
        '''
        self.pdb_id = pdb_id
        self.cut_off = cut_off
        self.sequence_types = sequence_types
        assert(0.0 <= cut_off <= 100.0)

        # Retrieve the FASTA record
        f = FASTA.retrieve(pdb_id, cache_dir = cache_dir)[pdb_id]
        self.chains = sorted(f.keys())
        self.fasta = f
        self.clustal_matches = dict.fromkeys(self.chains, None)
        self.substring_matches = dict.fromkeys(self.chains, None)
        self.seqres_to_uniparc_sequence_maps = {}

        # Retrieve the related UniParc sequences
        uniparc_sequences = {}
        uniparc_objects = {}
        pdb_uniparc_mapping = pdb_to_uniparc([pdb_id], cache_dir = cache_dir)
        for upe in pdb_uniparc_mapping[pdb_id]:
            uniparc_sequences[upe.UniParcID] = Sequence.from_sequence(upe.UniParcID, upe.sequence)
            uniparc_objects[upe.UniParcID] = upe
        self.uniparc_sequences = uniparc_sequences
        self.uniparc_objects = uniparc_objects

        # Run the alignment with clustal
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
            if self.clustal_matches[c]:
                match_string = ['%s (%.2f%%)' % (k, v) for k, v in sorted(self.clustal_matches[c].iteritems(), key = lambda x: x[1])] # this list should have be at most one element unless the matching did not go as expected
                s.append("%c -> %s" % (c, ", ".join(match_string)))
            elif self.alignment[c]:
                s.append("%c -> %s" % (c, self.alignment[c]))
            else:
                s.append("%c -> ?")
        return "\n".join(s)

    ### API methods ###

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

    def _get_residue_mapping(self):
        '''Creates a mapping between the residues of the chains and the associated UniParc entries.'''
        self.seqres_to_uniparc_sequence_maps = {}
        alignment = self.alignment
        for c in self.chains:
            if alignment.get(c):
                uniparc_entry = self.get_uniparc_object(c)
                sa = SequenceAligner()
                sa.add_sequence(c, self.fasta[c])
                sa.add_sequence(uniparc_entry.UniParcID, uniparc_entry.sequence)
                sa.align()
                residue_mapping, residue_match_mapping = sa.get_residue_mapping()

                # Create a SequenceMap
                s = SequenceMap()
                assert(sorted(residue_mapping.keys()) == sorted(residue_match_mapping.keys()))
                for k, v in residue_mapping.iteritems():
                    s.add(k, v, residue_match_mapping[k])
                self.seqres_to_uniparc_sequence_maps[c] = s

            else:
                self.seqres_to_uniparc_sequence_maps[c] = {}

    def _align_with_clustal(self):

        for c in self.chains:
            if self.sequence_types.get(c, 'Protein') == 'Protein':
                #clustal_indices = {1 : c}
                pdb_chain_id = '%s:%s' % (self.pdb_id, c)

                sa = SequenceAligner()
                sa.add_sequence(pdb_chain_id, self.fasta[c])
                #count = 2
                for uniparc_id, uniparc_sequence in sorted(self.uniparc_sequences.iteritems()):
                    #clustal_indices[count] = uniparc_id
                    sa.add_sequence(uniparc_id, str(uniparc_sequence))
                    #count += 1
                best_matches = sa.align()
                self.clustal_matches[c] = sa.get_best_matches_by_id(pdb_chain_id, cut_off = self.cut_off)
            else:
                # Do not try to match DNA or RNA
                self.clustal_matches[c] = {}

    def _align_with_substrings(self):
        '''Simple substring-based matching'''

        for c in self.chains:
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

    def _check_alignments(self):
        alignment = {}
        max_expected_matches_per_chain = 1
        for c in self.chains:
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
                        alignment[c] = self.clustal_matches[c].keys()[0]
                else:
                    alignment[c] = self.clustal_matches[c].keys()[0]
        self.alignment = alignment

