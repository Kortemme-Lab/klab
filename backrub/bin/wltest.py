#!/usr/bin/python2.4

import os, sys

from weblogolib import *

seqs = read_seq_data(open(sys.argv[1],'r'))
logo_data = LogoData.from_seqs(seqs)
logo_options = LogoOptions()
logo_options.title = "Sequence profile for num_designs designs on num_structs Backrub backbones of ens_name" % vars()
logo_options.number_interval = 1
logo_options.color_scheme = std_color_schemes["chemistry"]
logo_options.yaxis_label = ''
logo_options.annotate = ['A','B','C','D','E','F','G','H','I','J','K','L','A','B','C','D','E','F','G','H','I']
logo_format = LogoFormat(logo_data, logo_options)
png_print_formatter(logo_data, logo_format, open(sys.argv[2], 'w'))



