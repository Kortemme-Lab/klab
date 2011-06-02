#!/usr/bin/python2.4
# encoding: utf-8
"""
weblogotest.py

Created by Shane O'Connor 2011.
Copyright (c) 2011 __UCSF__. All rights reserved.

This file is useful for testing any reformatting to the generated fasta files.
"""


import sys
import string
import traceback
from weblogolib import *

for i in range(1, 10):
    s = []
    for j in range(1, 101):
        s.append(">%d" % j)
        s.append("L" * i)
    
    fastafile = "tolerance_sequences%d.fasta" % i
    motiffile = "tolerance_motif%d.png" % i
    fh = open(fastafile, 'w')
    fh.write(string.join(s, "\n"))
    fh.close()

    try:
        # create weblogo from the created fasta file
        seqs = read_seq_data(open(fastafile))
        logo_data = LogoData.from_seqs(seqs)
        logo_data.alphabet = std_alphabets['protein'] # this seems to affect the coloring, but not the actual motif
        logo_options = LogoOptions()
        logo_options.title = "Sequence profile"
        logo_options.number_interval = 1
        logo_options.color_scheme = std_color_schemes["chemistry"]
        ann = ["A%d" % (103 + k) for k in range(i)]
        logo_options.annotate = ann
        
        # Change the logo size of the X-axis for readability
        logo_options.number_fontsize = 3.5
        
        # Change the logo size of the Weblogo 'fineprint' - the default Weblogo text
        logo_options.small_fontsize = 4
        
        # Move the Weblogo fineprint to the left hand side for readability
        fineprinttabs = "\t" * (int(2.7 * float(len(ann))))
        logo_options.fineprint = "%s\t%s" % (logo_options.fineprint, fineprinttabs)
        
        logo_format = LogoFormat(logo_data, logo_options)
        png_print_formatter(logo_data, logo_format, open(motiffile, 'w'))
    except Exception, e:
        print("An error occurred creating the motifs.\n%s\n%s" % (str(e), traceback.format_exc()))
        success = False
