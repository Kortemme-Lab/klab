#!/usr/bin/python
# encoding: utf-8
"""
sifts.py test code.

Created by Shane O'Connor 2016
"""

import sys
import os
import time
import pprint

sys.path.insert(0, os.path.join('..', '..'))

from klab import colortext
from klab.bio.sifts import SIFTS

#for pdb_id in ['1AQT', '1lmb', '1utx', '2gzu', '2pnr', '1y8p', '2q8i', '1y8n', '1y8o', '1oax', '3dvn', '1mnu', '1mcl', '2p4a', '1s78', '1i8k']:
for pdb_id in ['2pnr']:
    print('\n')
    colortext.message(pdb_id)
    s = SIFTS.retrieve(pdb_id, cache_dir = '/kortemmelab/data/oconchus/SIFTS', acceptable_sequence_percentage_match = 70.0)
    colortext.warning(pprint.pformat(s.region_mapping))
    colortext.warning(pprint.pformat(s.region_map_coordinate_systems))
    colortext.warning(pprint.pformat(s.pfam_scop_mapping))
    colortext.warning(pprint.pformat(s.scop_pfam_mapping))
    print('\n')

print('\n\n')
