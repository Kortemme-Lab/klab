#!/usr/bin/python
# encoding: utf-8
"""
blast.py test code.

Created by Shane O'Connor 2016
"""

import traceback

from klab import colortext
from klab.bio.blast import BLAST

def test_pdb_files(b, pdb_ids):

    failed_cases = []
    c = 0
    for pdb_id in pdb_ids:
        try:
            c += 1
            colortext.message('\n{0}/{1}: {2}'.format(c, len(pdb_ids), pdb_id))
            hits = b.by_pdb(pdb_id)
            if hits:
                colortext.warning('{0} hits: {1}'.format(len(hits), ','.join(hits)))
            else:
                colortext.warning('No hits')
        except Exception, e:
            colortext.error('FAILED')
            failed_cases.append((pdb_id, str(e), traceback.format_exc()))

    if failed_cases:
        colortext.warning('*** These cases failed ***')
        for p in failed_cases:
            print('')
            colortext.pcyan(p[0])
            colortext.error(p[1])
            print(p[2])
        print('')


def test_sequences(b, sequences):
    failed_cases = []
    c = 0
    for sequence in sequences:
        try:
            c += 1
            colortext.message('\n{0}/{1}: {2}'.format(c, len(sequences), sequence))
            hits = b.by_sequence(sequence)
            if hits:
                colortext.warning('{0} hits: {1}'.format(len(hits), ','.join(hits)))
            else:
                colortext.warning('No hits')
        except Exception, e:
            colortext.error('FAILED')
            failed_cases.append((sequence, str(e), traceback.format_exc()))

    if failed_cases:
        colortext.warning('*** These cases failed ***')
        for p in failed_cases:
            print('')
            colortext.pcyan(p[0])
            colortext.error(p[1])
            print(p[2])
        print('')


if __name__ == '__main__':
    zemu_cases = ['1A22', '1A4Y', '1ACB', '1AHW', '1AK4', '1BRS', '1CBW', '1CHO', '1CSE', '1DAN', '1DFJ', '1DQJ', '1DVF', '1E96', '1EAW', '1EFN', '1EMV', '1F47', '1F5R', '1FC2', '1FCC', '1FFW', '1FY8', '1GC1', '1GCQ', '1GL0', '1GL1', '1GRN', '1H9D', '1HE8', '1IAR', '1JCK', '1JRH', '1JTG', '1KAC', '1KTZ', '1LFD', '1MAH', '1MLC', '1MQ8', '1N8O', '1NCA', '1NMB', '1PPF', '1R0R', '1REW', '1S1Q', '1SBB', '1SBN', '1SIB', '1SMF', '1TM1', '1UUZ', '1VFB', '1XD3', '2A9K', '2ABZ', '2AJF', '2B0Z', '2B10', '2B11', '2B12', '2B42', '2BTF', '2C0L', '2FTL', '2G2U', '2GOX', '2HLE', '2HRK', '2I26', '2I9B', '2J0T', '2J12', '2J1K', '2JEL', '2NOJ', '2O3B', '2OOB', '2PCB', '2PCC', '2QJ9', '2QJA', '2QJB', '2SIC', '2VIR', '2VLJ', '2VLR', '2WPT', '3BK3', '3BN9', '3BP8', '3HFM', '3NPS', '3SGB', '3TGK', '4CPA']
    sequences = [
        'CVSNKYFSNIHWCNCPKKFGGQHCEIDKSKTCYEGNGHFYRGKASTDTMGRPCLPWNSATVLQQTYHAHRSD',
        'MQIFVKTLTGKTITLEVEPSDTIENVKAKIQDKEGIPPDQQRLIFAGKQLEDGRTLSDYNIQKESTLHLVLRLRGG',
    ]
    raster_blaster = BLAST(bio_cache = None, cache_dir = '/kortemmelab/shared/DDG/structures', matrix = 'BLOSUM62', silent = False, cut_off = 0.001, sequence_identity_cut_off = 70)

    test_pdb_files(raster_blaster, zemu_cases)
    test_sequences(raster_blaster, sequences)
