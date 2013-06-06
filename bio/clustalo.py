#!/usr/bin/python
# encoding: utf-8
"""
clustalo.py
Wrapper functions for Clustal Omega.

Created by Shane O'Connor 2013
"""

import os
import shlex

from tools.fs.io import open_temp_file
from tools.process import Popen as _Popen
from tools import colortext

def align_two_FASTA_records(record1, record2):
    tempfiles = []

    fasta_handle, fasta_filename = open_temp_file('/tmp')
    tempfiles.append(fasta_filename)
    clustal_output_handle, clustal_filename = open_temp_file('/tmp')
    tempfiles.append(clustal_filename)
    stats_output_handle, stats_filename = open_temp_file('/tmp')
    tempfiles.append(stats_filename)
    print(fasta_filename, clustal_filename)

    # Create FASTA file
    fasta_handle.write("%s\n%s" % (record1, record2))
    fasta_handle.close()

    try:
        colortext.message("Calling clustalo to align sequences:")
        print(shlex.split('clustalo --infile %(fasta_filename)s --verbose --outfmt clustal --outfile %(clustal_filename)s' % vars()))
        p = _Popen('.', shlex.split('clustalo --infile %(fasta_filename)s --verbose --outfmt clustal --outfile %(clustal_filename)s --force' % vars()))
        if p.errorcode:
            raise Exception(p.stderr)
        else:
            print(p.stdout)

        colortext.message("Calling clustalw to generate Percent Identity Matrix:")
        p = _Popen('.', shlex.split('clustalw -INFILE=%(clustal_filename)s -PIM -TYPE=PROTEIN -STATS=%(stats_filename)s -OUTFILE=/dev/null' % vars()))
        if p.errorcode:
            raise Exception(p.stderr)
        else:
            tempfiles.append("%s.dnd" % clustal_filename)
            print(p.stdout)
    except:
        for t in tempfiles:
            os.remove(t)
        raise

    for t in tempfiles:
       os.remove(t)
    print(tempfiles)

    '''
    rm stats.txt
    rm clustalo.dnd
    '''


def align_two_simple_sequences(sequence1, sequence2, sequence1name = 'sequence1', sequence2name = 'sequence1'):
    pass
    FASTA1 = ">%s\n%s" % (sequence1name, "\n".join([sequence1[i:i+80] for i in range(0, len(sequence1), 80)]))
    FASTA2 = ">%s\n%s" % (sequence2name, "\n".join([sequence2[i:i+80] for i in range(0, len(sequence2), 80)]))
    print(FASTA1)
    print(FASTA2)
