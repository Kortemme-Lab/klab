#!/usr/bin/python
# encoding: utf-8
"""
ligand.py test code.

Created by Shane O'Connor 2016
"""

import sys
import os

sys.path.insert(0, os.path.join('..', '..'))

from klab.bio.ligand import Ligand, PDBLigand
from klab import colortext

l = Ligand.retrieve_data_from_rcsb('NAG', pdb_id = '1WCO', silent = True, cached_dir = '/tmp')
colortext.warning(l)
l = Ligand.retrieve_data_from_rcsb('GDP', silent = True, cached_dir = '/tmp')
colortext.pcyan(l)

l = PDBLigand.instantiate_from_ligand(l, 'A', ' 124B')
colortext.porange(l)

l = PDBLigand.retrieve_data_from_rcsb('GOL', '1BXO', 'A', '  12B', pdb_ligand_code='TST', silent = True, cached_dir = '/tmp')
colortext.ppurple(l)
