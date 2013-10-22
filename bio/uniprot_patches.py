#!/usr/bin/python
# encoding: utf-8
"""
uniprot_patches.py
Patches for UniProt entries to ensure that recommended names and subsection namings are unique.


Created by Shane O'Connor 2013
"""

use_patches = True

# These entries had multiple recommended names - the entries below represent the majority name or merged names
if use_patches:
    UniParcMergedRecommendedNamesRemap = {
        'UPI00000002EF' : {'Name' : 'Major prion protein', 'EC numbers' : [], 'Short names' : ['PrP']},
        'UPI0000000440' : {'Name' : 'Shiga-like toxin 1 subunit B', 'EC numbers' : [], 'Short names' : ['SLT-1 B subunit', 'SLT-1b']},
        'UPI0000000586' : {'Name' : 'Histone H3', 'EC numbers' : [], 'Short names' : []},
        'UPI0000000DA9' : {'Name' : 'Shiga toxin subunit A', 'EC numbers' : ['3.2.2.22'], 'Short names' : []},
        'UPI0000000ED4' : {'Name' : '60 kDa chaperonin', 'EC numbers' : [], 'Short names' : []},
        'UPI00000010A1' : {'Name' : 'Calmodulin', 'EC numbers' : [], 'Short names' : ['CaM']},
        'UPI00000017E7' : {'Name' : 'Protein enhancer of sevenless 2B', 'EC numbers' : [], 'Short names' : ['Protein E(sev)2B']},
        'UPI0000001C4C' : {'Name' : 'Annexin', 'EC numbers' : [], 'Short names' : []},
        'UPI000000E853' : {'Name' : 'Elongation factor Tu', 'EC numbers' : [], 'Short names' : ['EF-Tu']},
        'UPI0000024FDD' : {'Name' : 'Major prion protein', 'EC numbers' : [], 'Short names' : ['PrP']},
        'UPI000003112A' : {'Name' : 'Thioredoxin', 'EC numbers' : [], 'Short names' : []},
        'UPI0000033C27' : {'Name' : 'Major prion protein', 'EC numbers' : [], 'Short names' : ['PrP']},
        'UPI000003FF29' : {'Name' : 'Cold shock protein CspA', 'EC numbers' : [], 'Short names' : ['CSP-A']},
        'UPI0000052EE3' : {'Name' : 'Triosephosphate isomerase', 'EC numbers' : ['5.3.1.1'], 'Short names' : ['TIM']},
        'UPI0000060D14' : {'Name' : 'Probable manganese-dependent inorganic pyrophosphatase', 'EC numbers' : ['3.6.1.1'], 'Short names' : []},
        'UPI00000FB627' : {'Name' : 'Histone H2A', 'EC numbers' : [], 'Short names' : []},
        'UPI000011065C' : {'Name' : 'Thioredoxin', 'EC numbers' : [], 'Short names' : []},
        'UPI00001108BE' : {'Name' : 'Rubredoxin', 'EC numbers' : [], 'Short names' : ['Rd']},
        'UPI00001109D0' : {'Name' : 'Rubredoxin', 'EC numbers' : [], 'Short names' : ['Rd']},
        'UPI0000111347' : {'Name' : 'Aspartate carbamoyltransferase', 'EC numbers' : ['2.1.3.2'], 'Short names' : []},
        'UPI0000111CC2' : {'Name' : 'Lambda prophage-derived head-to-tail joining protein W', 'EC numbers' : [], 'Short names' : ['gpW']},
        'UPI0000111D34' : {'Name' : 'Superoxide dismutase', 'EC numbers' : ['1.15.1.1'], 'Short names' : []},
        'UPI000011287C' : {'Name' : 'Peptidyl-prolyl cis-trans isomerase', 'EC numbers' : ['5.2.1.8'], 'Short names' : []},
        'UPI0000112C08' : {'Name' : 'Ribonuclease HI', 'EC numbers' : ['3.1.26.4'], 'Short names' : ['RNase HI']},
        'UPI000012813D' : {'Name' : 'Cytochrome c oxidase subunit 6A, mitochondrial', 'EC numbers' : [], 'Short names' : []},
        'UPI00001292ED' : {'Name' : 'Glutamate dehydrogenase', 'EC numbers' : ['1.4.1.3'], 'Short names' : ['GDH']},
        'UPI000012EBF8' : {'Name' : 'Silenced mating-type protein ALPHA2', 'EC numbers' : [], 'Short names' : ['MATalpha2 protein']},
        'UPI00001354F1' : {'Name' : 'Adenosylhomocysteinase', 'EC numbers' : ['3.3.1.1'], 'Short names' : ['AdoHcyase']},
        'UPI0000136BC5' : {'Name' : 'Tetracycline repressor protein class D', 'EC numbers' : [], 'Short names' : []},
        'UPI00001437D3' : {'Name' : 'Peptidyl-prolyl cis-trans isomerase FKBP1A', 'EC numbers' : ['5.2.1.8'], 'Short names' : ['PPIase FKBP1A']},
        'UPI0000166112' : {'Name' : 'Glutamate dehydrogenase', 'EC numbers' : ['1.4.1.3'], 'Short names' : ['GDH']},
        'UPI0000168235' : {'Name' : 'Ornithine carbamoyltransferase', 'EC numbers' : ['2.1.3.3'], 'Short names' : ['OTCase']},
        'UPI000016DD37' : {'Name' : 'Thioredoxin H-type', 'EC numbers' : [], 'Short names' : ['Trx-H']},
        'UPI000017133B' : {'Name' : 'Histone H2B', 'EC numbers' : [], 'Short names' : []},
        'UPI00004F0556' : {'Name' : 'Acylphosphatase-1', 'EC numbers' : ['3.6.1.7'], 'Short names' : []},
        'UPI000002D10B' : {'Name' : 'Thiol:disulfide interchange protein', 'EC numbers' : [], 'Short names' : []},
        'UPI0000054B9A' : {'Name' : 'DSBA-like thioredoxin domain protein', 'EC numbers' : [], 'Short names' : []},
        'UPI0000021092' : {'Name' : '', 'EC numbers' : [], 'Short names' : []},
        'UPI00000B96E8' : {'Name' : 'Chitinase', 'EC numbers' : [], 'Short names' : []},
        'UPI00000C5AE8' : {'Name' : '', 'EC numbers' : [], 'Short names' : []},
    }

    # These entries had no recommended names - the names here are merges of submitted names
    UniParcMergedSubmittedNamesRemap = {
        'UPI000004A5EE' : {'Name' : 'Glycoside hydrolase family 12 / Endo-beta-1,4-glucanase', 'EC numbers' : ['3.2.1.4'], 'Short names' : []},
        'UPI000004A5EF' : {'Name' : 'Endoglucanase', 'EC numbers' : [], 'Short names' : []},
        'UPI000004A5F4' : {'Name' : 'Endoglucanase', 'EC numbers' : [], 'Short names' : []},
        'UPI0000056C0A' : {'Name' : 'Carboxylesterase', 'EC numbers' : [], 'Short names' : []},
        'UPI00000619ED' : {'Name' : 'Xylanase', 'EC numbers' : [], 'Short names' : []},
        'UPI0000066862' : {'Name' : '389aa long hypothetical aspartate aminotransferase', 'EC numbers' : [], 'Short names' : []},
        'UPI00000A85FC' : {'Name' : 'I lectin', 'EC numbers' : [], 'Short names' : []},
        'UPI00000AA891' : {'Name' : 'II lectin', 'EC numbers' : [], 'Short names' : []},
        'UPI00000AFF7F' : {'Name' : 'Beta-lactamase inhibitory protein II', 'EC numbers' : [], 'Short names' : []},
        'UPI00000B3DA5' : {'Name' : 'Class C beta-lactamase', 'EC numbers' : ['3.5.2.6'], 'Short names' : []},
        'UPI00000B533A' : {'Name' : 'Putative uncharacterized protein', 'EC numbers' : [], 'Short names' : []},
        'UPI00000B54B0' : {'Name' : 'Chitinase', 'EC numbers' : ['3.2.1.14'], 'Short names' : []},
        'UPI000017CAE4' : {'Name' : 'Mannose-specific lectin KM+', 'EC numbers' : [], 'Short names' : []},
        'UPI00001E0563' : {'Name' : 'Hydrolase', 'EC numbers' : [], 'Short names' : []},
        'UPI0000212E45' : {'Name' : 'Defensin-like protein / Plant defensin', 'EC numbers' : [], 'Short names' : []},
        'UPI0000E79739' : {'Name' : 'Putative uncharacterized protein', 'EC numbers' : [], 'Short names' : []},
    }

    #k['Validity'] = 'Standard'
    for k, v in UniParcMergedRecommendedNamesRemap.iteritems():
        v['Validity'] = 'Majority'

    for k, v in UniParcMergedSubmittedNamesRemap.iteritems():
        v['Validity'] = 'In flux'

    # These subsections clash with those of UniProt AC entries relating to the same protein
    clashing_subsections_for_removal = {
        # UPI000000D50D - The majority of cases disagreed
        'C6EK70' : [ # Inferred from homology whereas P37001 has Evidence at protein level
            (u'signal peptide', '', 1, 26),
            (u'chain', '', 27, 186),
        ],
        'C9R198' : [ # Inferred from homology whereas P37001 has Evidence at protein level
            (u'signal peptide', '', 1, 26),
            (u'chain', '', 27, 186),
        ],
        # UPI000002D10B - I took the minority case (2 vs 4) but those two cases P0AEG4 and P0AEG5 had Evidence at protein level
        'B1IW52' : [
            (u'signal peptide', '', 1, 20),
            (u'chain', '', 21, 208),
        ],
        'C9QW99' : [
            (u'signal peptide', '', 1, 20),
            (u'chain', '', 21, 208),
        ],
        'E0J4U9' : [
            (u'signal peptide', '', 1, 20),
            (u'chain', '', 21, 208),
        ],
        'E8Y7Z9' : [
            (u'signal peptide', '', 1, 20),
            (u'chain', '', 21, 208),
        ],
        # UPI000002D34D - this was a choice between two partitionings (G0Q513 and P00777) at the time of writing so.
        # However, P00777 has Evidence at protein level whereas G0Q513 is Predicted.
        'G0Q513' : [
            (u'signal peptide', '', 1, 39),
            (u'chain', '', 40, 299),
        ],
        # UPI000003EAF7 - again, this was a choice between two partitionings (6 entries like C6EG66 and 4 entries like C7BU11,
        #  all Inferred from homology) at the time of writing so the choice is somewhat arbitrary (I took the majority)
        'C7BU11' : [
            (u'signal peptide', '', 1, 23),
            (u'chain', '', 24, 79),
        ],
        'D2THA1' : [
            (u'signal peptide', '', 1, 23),
            (u'chain', '', 24, 79),
        ],
        'J3Z435' : [
            (u'signal peptide', '', 1, 23),
            (u'chain', '', 24, 79),
        ],
        'L0M8Y4' : [
            (u'signal peptide', '', 1, 23),
            (u'chain', '', 24, 79),
        ],
        # UPI000003EB7E - again, this choice is somewhat arbitary. P02925 has Evidence at protein level whereas C9QX85 is Predicted.
        'C9QX85' : [
            (u'signal peptide', '', 1, 26),
            (u'chain', '', 27, 296),
        ],
        # UPI00000421AF - This entry overlapped with itself. This removal and the addition in subsections_for_addition may be wrong.
        'Q59962' : [
            (u'signal peptide', '', 1, 39),
            (u'chain', '', 40, 228),
        ],
        # UPI0000054B9A. Choice between Q9EYL5 and D1GSI9. Q9EYL5 has 'Evidence at protein level' for its protein existence, D1GSI9 has a 'Predicted' protein existence.
        'D1GSI9' : [
            (u'signal peptide', '', 1, 25),
            (u'chain', '', 26, 199),
        ],
        # UPI000005D4DB. Choice between P00149/Q8RME7 and B3QFJ7. P00149 has 'Evidence at protein level' for its protein existence, B3QFJ7 has a 'Predicted' protein existence.
        'B3QFJ7' : [
            (u'signal peptide', '', 1, 22),
            (u'chain', '', 23, 146),
        ],
        # UPI0000110615. Choice between P08306 and A1BA41. P08306 has 'Evidence at protein level' for its protein existence, A1BA41 is 'Inferred from homology'.
        'A1BA41' : [
            (u'signal peptide', '', 1, 30),
            (u'chain', '', 31, 298),
        ],
        # UPI00001259D7. Choice between C9QU48/E8Y3Y8 and P00811. P00811 has 'Evidence at protein level' for its protein existence, C9QU48/E8Y3Y8 are 'Predicted'.
        'C9QU48' : [
            (u'signal peptide', '', 1, 20),
            (u'chain', '', 21, 377),
        ],
        'E8Y3Y8' : [
            (u'signal peptide', '', 1, 20),
            (u'chain', '', 21, 377),
        ],
        # UPI0000125D6C. Choice between B1J0J0/C6EBF9/C9QT38/E0J559/E8Y4D5 and P02924. P02924 has 'Evidence at protein level' for its protein existence, the others are 'Inferred from homology'.
        'B1J0J0' : [
            (u'signal peptide', '', 1, 24),
            (u'chain', '', 25, 329),
        ],
        'C6EBF9' : [
            (u'signal peptide', '', 1, 24),
            (u'chain', '', 25, 329),
        ],
        'C9QT38' : [
            (u'signal peptide', '', 1, 24),
            (u'chain', '', 25, 329),
        ],
        'E0J559' : [
            (u'signal peptide', '', 1, 24),
            (u'chain', '', 25, 329),
        ],
        'E8Y4D5' : [
            (u'signal peptide', '', 1, 24),
            (u'chain', '', 25, 329),
        ],
        # UPI00001260FB. Choice between C6EIF4/C9QZG2 and P00805. P00805 has 'Evidence at protein level' for its protein existence, the others are 'Predicted'.
        'C6EIF4' : [
            (u'signal peptide', '', 1, 23),
            (u'chain', '', 24, 348),
        ],
        'C9QZG2' : [
            (u'signal peptide', '', 1, 23),
            (u'chain', '', 24, 348),
        ],
        # UPI0000126C7E. Choice between C6ECB3/E0J2H8/E8Y337 and P0ABE7. P0ABE7 has 'Evidence at protein level' for its protein existence, the others are 'Predicted'.
        'C6ECB3' : [
            (u'signal peptide', '', 1, 23),
            (u'chain', '', 24, 128),
        ],
        'E0J2H8' : [
            (u'signal peptide', '', 1, 23),
            (u'chain', '', 24, 128),
        ],
        'E8Y337' : [
            (u'signal peptide', '', 1, 23),
            (u'chain', '', 24, 128),
        ],
        # UPI0000128133. Choice between P82543 ('Evidence at protein level') and 6DH43 ('Predicted') and H9ZR67 ('Predicted').
        # The Predicted partitionings split the sequence into signal peptide and chain whereas P82543 only has a chain with 34 residues.
        # Since this is a short sequence and the PDB files cover most of it, I took the P82543 entry.
        'F6DH43' : [
            (u'signal peptide', '', 1, 29),
            (u'chain', '', 30, 34),
        ],
        'H9ZR67' : [
            (u'signal peptide', '', 1, 28),
            (u'chain', '', 29, 34),
        ],
        # UPI0000128B4D. Choice between A1V9X3/E3IQX1 and P00131. P00131 has 'Evidence at protein level' for its protein existence, the others are 'Predicted'.
        'A1V9X3' : [
            (u'signal peptide', '', 1, 23),
            (u'chain', '', 24, 129),
        ],
        'E3IQX1' : [
            (u'signal peptide', '', 1, 23),
            (u'chain', '', 24, 129),
        ],
        # UPI000012A647. Choice between C9R1D8 and P05825. P05825 has 'Evidence at protein level' for its protein existence, C9R1D8 is 'Inferred from homology'.
        'C9R1D8' : [
            (u'signal peptide', '', 1, 23),
            (u'chain', '', 24, 746),
        ],
        # UPI000012BDB6. Choice between P26222 and Q47R05. P26222 has 'Evidence at protein level' for its protein existence, Q47R05 is 'Predicted'.
        'Q47R05' : [
            (u'signal peptide', '', 1, 32),
            (u'chain', '', 33, 441),
        ],
        # UPI000012EB43. Choice between P0AEX9/P0AEY0 and C6EDY9/C9QV44/E0J0G2/E8Y5J0. P0AEX9/P0AEY0 have 'Evidence at protein level'
        # for their protein existence, the others are 'Predicted'.
        'C6EDY9' : [
            (u'signal peptide', '', 1, 27),
            (u'chain', '', 28, 396),
        ],
        'C9QV44' : [
            (u'signal peptide', '', 1, 27),
            (u'chain', '', 28, 396),
        ],
        'E0J0G2' : [
            (u'signal peptide', '', 1, 27),
            (u'chain', '', 28, 396),
        ],
        'E8Y5J0' : [
            (u'signal peptide', '', 1, 27),
            (u'chain', '', 28, 396),
        ],
        # UPI0000130CF0. Choice between P0A910/P0A911/Q6W821 and C6EI25/C9QZB9/E0IZ85/E8Y2U5. P0A910 has 'Evidence at protein level',
        # the rest are 'Inferred from homology'.
        'C6EI25' : [
            (u'signal peptide', '', 1, 22),
            (u'chain', '', 23, 346),
        ],
        'C9QZB9' : [
            (u'signal peptide', '', 1, 22),
            (u'chain', '', 23, 346),
        ],
        'E0IZ85' : [
            (u'signal peptide', '', 1, 22),
            (u'chain', '', 23, 346),
        ],
        'E8Y2U5' : [
            (u'signal peptide', '', 1, 22),
            (u'chain', '', 23, 346),
        ],
        # UPI0000132009. Choice between P00634 and C9QQP9. P00634 has 'Evidence at protein level' for its protein existence, C9QQP9 is 'Inferred from homology'.
        'C9QQP9' : [
            (u'signal peptide', '', 1, 22),
            (u'chain', '', 23, 471),
        ],
    }

    # These are sections I removed above which I'm truncating here. This may be wrong!
    subsections_for_addition = {
        'Q59962' : [
            (u'signal peptide', '', 1, 38),
        ],
    }

    AC_entries_where_we_ignore_the_subsections = set([
        # UPI000018DB89. Complicated. A7J8L3, P0C6U8, and D3KDM4 agree and A7J8L3 and P0C6U8 have 'Evidence at protein level' but the subsection names differ. I chose P0C6U8 out of these.
        'A7J8L3', 'D3KDM4', # agrees with P0C6U8 but with different names
        'Q6RCX7', 'Q6RCY8', 'Q6RCZ9', 'Q6RD10', 'Q6RD43', 'Q6RD65', # agree with each other but disagree with P0C6U8
        'Q6VA79', 'Q6VA90', 'Q6VAA1', # agree with each other but disagree with P0C6U8
        # UPI000019098F. Complicated. A7J8L2, D3KDM3, and P0C6X7 nearly agree. P0C6X7 has 'Evidence at protein level' but the subsection names differ on matching segments. I chose P0C6X7 out of these.
        'A7J8L2', 'D3KDM3', # nearly agree with each other and P0C6X7
        'Q6RCY9', 'Q6RD00', 'Q6RD11', 'Q6RD44', 'Q6RD66', # agree with each other but disagree with P0C6X7
        'Q6VA91', 'Q6VAA2', # agree with each other but disagree with P0C6X7
        # UPI0000000ED4.
        'A1AJ51', 'A7ZV12', 'A8A7N9', 'B1ITQ5', 'B1LQG4', 'B1XDP7', 'B2TY18', # Do not specify the name of position 1 (initiator methionine) whereas entries like P10149 do
        'B5Z2F2', 'B6I615', 'B7LC02', 'B7M8Q4', 'B7MKU8', 'B7MSV9', 'B7NG81',
        'B7NTK2', 'B7UPW3', 'C5A1D5', 'Q0SXD6', 'Q31T78', 'Q328C4', 'Q3YUJ7',
        'Q1R3B6', # This has Evidence at protein level but also omits the name of position 1
        # UPI000000E853
        'A1AGM6', 'A7ZSL4', 'A8A5E6', 'B1IPW0', # Do not specify the name of position 1 (initiator methionine) whereas entries like P0CE47 do
        'Q0TCC0', 'Q1R5Y2', 'Q31VV0', 'Q32B27', 'Q3YWT3'
    ])

    # These subsections overlap with those of UniProt AC entries relating to the same protein. We may want to keep this information instead of discarding it.
    overlapping_subsections_for_removal = {
        # UPI000000D8B8
        'P00747' : [
            (u'chain', u'Angiostatin', 79, 466), # overlaps with its own AC entry which is presumably on purpose
        ],
    }

    PDBs_marked_as_XRay_with_no_resolution = set([
        '2A6U', # Solved with POWDER DIFFRACTION
    ])

    # These entries seem wrong in UniProt
    fixed_mapping_for_AC_PDB_chains = {
        'P18525' : {'1AR1' : {'D' : 'C'}},
        'P01636' : {'1AR1' : {'C' : 'D'}},
    }

    # These entries have an unknown position mapping in UniProt
    broken_mapping_for_AC_PDB_chains = {
        'P18525' : {'1AR1' : [set(['D'])]},
        'P01636' : {'1AR1' : [set(['C'])]},
        'P61823' : {'1UN5' : [set(['A'])]},
        'P00559' : {'2PGK' : [set(['A'])]},
        'P29395' : {'1IP8' : [set(['G'])]},
    }

    # These entries have missing position mapping in UniProt but are easily fixed
    missing_mapping_for_AC_PDB_chains = {
        'Q5SLP8' : {'2OW8' : {'g' : (1, 101)}},
    }

    # These entries have missing methods mapping in UniProt
    missing_AC_PDB_methods = {
        'P24297' : {'3KYX' : ['X-ray', 'Neutron']},
        'P00918' : {'3TMJ' : ['X-ray', 'Neutron']},
        'P00974' : {'3OTJ' : ['X-ray', 'Neutron']},
        'P08839' : {
            '2KX9' : ['NMR', 'Solution scattering'],
            '2L5H' : ['NMR', 'Solution scattering'],
            '2XDF' : ['NMR', 'Solution scattering'],
        },
        'P07320' : {'2KLJ' : ['NMR', 'Solution scattering']},
        'P00760' : {'3OTJ' : ['X-ray', 'Neutron']},
    }
    differing_subsection_name_patch = {
        # UPI00000000C3 - P01899 has Evidence at protein level, Q792Z7 has Evidence at transcript level
        'Q792Z7' : {(25, 362) : ('D(b) glycoprotein', 'H-2 class I histocompatibility antigen, D-B alpha chain')},
        # UPI00000000E4 - A7Z0C2, P62593, P62594 use the second name. P62593 has Evidence at protein level, Q6A253 is Predicted
        'Q6A253' : {(24, 286) : ('beta-lactamase', 'Beta-lactamase TEM')},
        # UPI0000000440 - P69178, P69179, and Q7BQ98 have Evidence at protein level. P69178, P69179 agree so I took their description
        'Q1ELX8' : {(21, 89) : ('shiga toxin I subunit B', 'Shiga-like toxin 1 subunit B')},
        'Q32GM0' : {(21, 89) : ('Shiga toxin subunit B', 'Shiga-like toxin 1 subunit B')},
        'Q6LDT3' : {(21, 89) : ('Shiga toxin-like subunit B', 'Shiga-like toxin 1 subunit B')},
        'Q779K3' : {(21, 89) : ('Shiga toxin subunit B', 'Shiga-like toxin 1 subunit B')},
        'Q7BQ98' : {(21, 89) : ('Shiga toxin subunit B', 'Shiga-like toxin 1 subunit B')},
        'Q8X4M7' : {(21, 89) : ('Shiga-like toxin type-I beta subunit', 'Shiga-like toxin 1 subunit B')},
        # UPI0000000586 - more entries with Evidence at protein level used Histone H3.2 rather than Histone H3
        'P02299' : {(2, 136) : ('Histone H3', 'Histone H3.2')},
        'P84235' : {(2, 136) : ('Histone H3', 'Histone H3.2')},
        'P84236' : {(2, 136) : ('Histone H3', 'Histone H3.2')},
        'P84237' : {(2, 136) : ('Histone H3', 'Histone H3.2')},
        'P84238' : {(2, 136) : ('Histone H3', 'Histone H3.2')},
        'P84239' : {(2, 136) : ('Histone H3', 'Histone H3.2')},
        # UPI0000000DA9 - This may not be the best name but the Evidence at protein level entry uses it
        'P10149' : {(23, 315) : ('Shiga-like toxin 1 subunit A', 'Shiga toxin subunit A')},
        # UPI00000010A1 - I took the majority case here.
        'P62147' : {(2, 149) : ('Calmodulin-1', 'Calmodulin')},
        'P62148' : {(2, 149) : ('Calmodulin-1', 'Calmodulin')},
        'P62153' : {(2, 149) : ('Calmodulin-A', 'Calmodulin')},
        # UPI00000017E7 - Taking the Evidence at protein level entry Q08012
        'Q6YKA8' : {(1, 211) : ('Protein E(sev)2B', 'Protein enhancer of sevenless 2B')},
        # UPI000000E853 -
        'Q83JC4' : {(2, 394) : ('Elongation factor Tu', 'Elongation factor Tu 1')},
        # UPI0000111CC2 -
        'P68659' : {(1, 68) : ('Lambda prophage-derived head-to-tail joining protein W', 'Head-to-tail joining protein W')},
        # UPI0000112C08 -
        'A7ZHV1' : {(1, 155) : ('Ribonuclease H', 'Ribonuclease HI')},
        'B1IPU4' : {(1, 155) : ('Ribonuclease H', 'Ribonuclease HI')},
        'B1LHM3' : {(1, 155) : ('Ribonuclease H', 'Ribonuclease HI')},
        'B1XD78' : {(1, 155) : ('Ribonuclease H', 'Ribonuclease HI')},
        'B2U352' : {(1, 155) : ('Ribonuclease H', 'Ribonuclease HI')},
        'B5Z0I8' : {(1, 155) : ('Ribonuclease H', 'Ribonuclease HI')},
        'B6HZS7' : {(1, 155) : ('Ribonuclease H', 'Ribonuclease HI')},
        'B7LW89' : {(1, 155) : ('Ribonuclease H', 'Ribonuclease HI')},
        'B7M213' : {(1, 155) : ('Ribonuclease H', 'Ribonuclease HI')},
        'B7MBJ0' : {(1, 155) : ('Ribonuclease H', 'Ribonuclease HI')},
        'B7MQ23' : {(1, 155) : ('Ribonuclease H', 'Ribonuclease HI')},
        'B7N876' : {(1, 155) : ('Ribonuclease H', 'Ribonuclease HI')},
        'B7NKW4' : {(1, 155) : ('Ribonuclease H', 'Ribonuclease HI')},
        'C4ZRV1' : {(1, 155) : ('Ribonuclease H', 'Ribonuclease HI')},
        'Q325T2' : {(1, 155) : ('Ribonuclease H', 'Ribonuclease HI')},
        'Q32JP9' : {(1, 155) : ('Ribonuclease H', 'Ribonuclease HI')},
        'Q3Z5E9' : {(1, 155) : ('Ribonuclease H', 'Ribonuclease HI')},
        # UPI000012EBF8 - I took the entry P0CY08 with Evidence at protein level
        'P0CY09' : {(1, 210) : ('Silenced mating-type protein ALPHA2', 'Mating-type protein ALPHA2')},
    }

else:
    UniParcMergedSubmittedNamesRemap = {}
    UniParcMergedRecommendedNamesRemap = {}
    clashing_subsections_for_removal = {}
    subsections_for_addition = {}
    AC_entries_where_we_ignore_the_subsections = set([])
    overlapping_subsections_for_removal = {}
    PDBs_marked_as_XRay_with_no_resolution = set([])
    fixed_mapping_for_AC_PDB_chains = {}
    broken_mapping_for_AC_PDB_chains = {}
    missing_mapping_for_AC_PDB_chains = {}
    missing_AC_PDB_methods = {}
    differing_subsection_name_patch = {}