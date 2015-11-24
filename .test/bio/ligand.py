import sys
import os

sys.path.insert(0, os.path.join('..', '..'))

from klab.bio.ligand import Ligand
from klab import colortext

l = Ligand.retrieve_data_from_rcsb('NAG', pdb_id = '1WCO', silent = True, cached_dir = '/tmp')
colortext.warning(l)
l = Ligand.retrieve_data_from_rcsb('GDP', silent = True, cached_dir = '/tmp')
colortext.pcyan(l)

 #pdb_id = '1WCO',