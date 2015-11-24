import sys
import os

sys.path.insert(0, os.path.join('..', '..'))

from klab.bio.ligand import Ligand, PDBLigand
from klab import colortext

l = Ligand.retrieve_data_from_rcsb('NAG', pdb_id = '1WCO', silent = True, cached_dir = '/tmp')
colortext.warning(l)
l = Ligand.retrieve_data_from_rcsb('GDP', silent = True, cached_dir = '/tmp')
colortext.pcyan(l)
l = PDBLigand.retrieve_data_from_rcsb('GOL', '1BXO', 'A', '  12B', pdb_ligand_code='TST', silent = True, cached_dir = '/tmp')
colortext.ppurple(l)
