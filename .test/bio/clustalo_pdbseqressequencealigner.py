"""
Script to test out new functionality of PDBSeqresSequenceAligner in the klab clustal module.

The aim of the new functionality is to take two related PDB structures A and B and a list of chains of interest in A and
to return a residue map between the best-matching chains of A and B.

Created by Shane O'Connor 2016
"""

import sys
import pprint

from klab import colortext
from klab.bio.basics import ChainMutation
from klab.bio.clustalo import PDBSeqresSequenceAligner

test_cases = [
    dict(
        wt = '1TM1',
        mut = '1TO1',
        #mut = '1T01', # todo: try this ID - it is the wrong one but may expose some exceptions we want to catch
        wt_chains = ['E', 'I'],
        mutations = ChainMutation('G', ' 489 ', 'A', Chain = 'D'),
    ),
    dict(
        wt='1AK4',
        mut='1M9X',
        wt_chains=['A', 'D'],
        mutations=ChainMutation('G', ' 489 ', 'A', Chain='D'),
    ),
    dict(
        wt='2AJF',
        mut='3D0G',
        wt_chains=['A', 'B', 'E', 'F'],
        mutations=ChainMutation('G', ' 489 ', 'A', Chain='D'),
    ),
]

for case in test_cases:
    pssa = PDBSeqresSequenceAligner(case['wt'], case['mut'])
    for wt_chain_id in case['wt_chains']:
        mut_chain_ids = pssa.get_matching_chains(wt_chain_id)
        for mut_chain_id in mut_chain_ids:
            print('ATOM residue mapping for {0} {1} -> {2} {3}'.format(case['wt'], wt_chain_id, case['mut'], mut_chain_id))
            print(sorted((pssa.get_atom_residue_mapping(wt_chain_id, mut_chain_id) or {}).iteritems()))
            print('Matching chains for chain {0}'.format(wt_chain_id))
            print(pssa.get_matching_chains(wt_chain_id))

    print('{0} {1} residue "{2}" maps to {3}'.format(case['wt'], 'I', case['mut'], pssa.map_atom_residue('I', 'I', '  20 ')))
