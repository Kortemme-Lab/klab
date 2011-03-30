#!/usr/bin/env python
# encoding: utf-8


import os
import sys
import string
from weblogolib import *

resids = [2,3,4,5,7,12]

# create weblogo from the created fasta file
seqs = read_seq_data(open("specificity_sequences.fasta"))
logo_data = LogoData.from_seqs(seqs)
logo_options = LogoOptions()
logo_options.logo_title = "Sequence profile"
logo_options.number_interval = 1
logo_options.xaxis_label = 'Mutated residues'
# logo_options.[ 'B' + str(resid) for resid in resids]
# logo_options.yaxis_label = 'Frequency'
logo_format = LogoFormat(logo_data, logo_options)
png_print_formatter(logo_data, logo_format, open("test_specificity_motif.png", 'w'))