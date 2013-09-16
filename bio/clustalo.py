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

from tools.fs.io import open_temp_file
from tools.process import Popen as _Popen
from tools import colortext

from uniprot import pdb_to_uniparc
from fasta import FASTA

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
        self.sequence_ids = {}
        self.matrix = None
        self.named_matrix = None

    ### API methods ###

    def add_sequence(self, sequence_id, sequence):
        if sequence_id in self.sequence_ids.values():
            raise Exception("Sequence IDs must be unique")
        self.records.append(">%s\n%s" % (sequence_id, "\n".join([sequence[i:i+80] for i in range(0, len(sequence), 80)])))
        self.sequence_ids[len(self.sequence_ids) + 1] = sequence_id

    def align(self):

        records = self.records

        alignment_output = None

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

            p = _Popen('.', shlex.split('clustalw -INFILE=%(clustal_filename)s -PIM -TYPE=PROTEIN -STATS=%(stats_filename)s -OUTFILE=/dev/null' % vars()))
            if p.errorcode:
                raise Exception('An error occurred while calling clustalw to generate the Percent Identity Matrix:\n%s' % p.stderr)
            else:
                tempfiles.append("%s.dnd" % clustal_filename)
                alignment_output = p.stdout
        except:
            for t in tempfiles:
                os.remove(t)
            raise

        for t in tempfiles:
            try:
                os.remove(t)
            except: pass

        return self._parse_alignment_output(alignment_output)

    def get_best_matches_by_id(self, id, cut_off = 98.0):
        best_matches = {}
        named_matrix = self.named_matrix
        for k, v in named_matrix[id].iteritems():
            if k != id and v >= cut_off:
                best_matches[k] = v
        return best_matches

    ### Private methods ###

    def _parse_alignment_output(self, alignment_output):

        # Initalize matrix
        matrix = dict.fromkeys(self.sequence_ids.keys(), None)
        for x in range(len(self.sequence_ids)):
            matrix[x + 1] = {}
            for y in range(len(self.sequence_ids)):
                matrix[x + 1][y + 1] = None
            matrix[x + 1][x + 1] = 100.0

        matches = alignment_results_regex.match(alignment_output)
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
            raise colortext.Exception("Error parsing alignment output for alignment scores. The output was:\n%s" % alignment_output)

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

    def __init__(self, pdb_id, cache_dir = None, cut_off = 98.0):
        ''' The sequences are matched up to a percentage identity specified by cut_off (0.0 - 100.0).
        '''
        self.pdb_id = pdb_id
        self.cut_off = cut_off
        assert(0.0 <= cut_off <= 100.0)

        # Retrieve the FASTA record
        f = FASTA.retrieve(pdb_id, cache_dir = cache_dir)[pdb_id]
        self.chains = sorted(f.keys())
        self.fasta = f
        self.clustal_matches = dict.fromkeys(self.chains, None)
        self.substring_matches = dict.fromkeys(self.chains, None)

        # Retrieve the related UniParc sequences
        uniparc_sequences = {}
        uniparc_objects = {}
        pdb_uniparc_mapping = pdb_to_uniparc([pdb_id], cache_dir = cache_dir)
        for upe in pdb_uniparc_mapping[pdb_id]:
            uniparc_sequences[upe.UniParcID] = upe.sequence
            uniparc_objects[upe.UniParcID] = upe
        self.uniparc_sequences = uniparc_sequences
        self.uniparc_objects = uniparc_objects

        # Run the alignment with clustal
        self._align_with_clustal()
        self._align_with_substrings()
        self._check_alignments()

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

    def _align_with_clustal(self):

        for c in self.chains:
            #clustal_indices = {1 : c}
            pdb_chain_id = '%s:%s' % (self.pdb_id, c)

            sa = SequenceAligner()
            sa.add_sequence(pdb_chain_id, self.fasta[c])
            #count = 2
            for uniparc_id, uniparc_sequence in sorted(self.uniparc_sequences.iteritems()):
                #clustal_indices[count] = uniparc_id
                sa.add_sequence(uniparc_id, uniparc_sequence)
                #count += 1
            best_matches = sa.align()
            self.clustal_matches[c] = sa.get_best_matches_by_id(pdb_chain_id, cut_off = self.cut_off)

    def _align_with_substrings(self):
        '''Simple substring-based matching'''

        for c in self.chains:
            fasta_sequence = self.fasta[c]

            substring_matches = {}

            for uniparc_id, uniparc_sequence in sorted(self.uniparc_sequences.iteritems()):
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
            assert(len(self.substring_matches[c]) <= len(self.clustal_matches[c]))
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

