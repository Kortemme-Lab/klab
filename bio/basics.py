#!/usr/bin/python
# encoding: utf-8
"""
basics.py
Basic objects for bioinformatics.

Created by Shane O'Connor 2013
"""

# todo: To update code which uses these objects formally in pdb.py:
#   replace aa1 with residue_type_3to1_map
#   replace relaxed_amino_acid_codes (a list) with relaxed_residue_types_1 (a set)
#   replace amino_acid_codes (a list) with residue_types_1 (a set)
#   replace non_canonical_aa1 with non_canonical_amino_acids
#   replace residues with allowed_PDB_residues_types
#   replace nucleotides_dna_to_shorthand with dna_nucleotides_2to1_map
#   replace nucleotides_dna and nucleotides_rna with dna_nucleotides and rna_nucleotides respectively
#   The Residue class is now located here and renamed to PDBResidue (since we assert that the chain is 1 character long).
#   The Mutation class is now located here. ChainMutation was called something else.


###
# Residue maps and sets.
###

residue_type_3to1_map = {
    "ALA": "A",
    "CYS": "C",
    "ASP": "D",
    "GLU": "E",
    "PHE": "F",
    "GLY": "G",
    "HIS": "H",
    "ILE": "I",
    "LYS": "K",
    "LEU": "L",
    "MET": "M",
    "ASN": "N",
    "PRO": "P",
    "GLN": "Q",
    "ARG": "R",
    "SER": "S",
    "THR": "T",
    "VAL": "V",
    "TRP": "W",
    "TYR": "Y"
}

residue_types_3 = set(residue_type_3to1_map.keys())
residue_types_1 = set(residue_type_3to1_map.values()) # formally a list called amino_acid_codes
relaxed_residue_types_1 = residue_types_1.union(set(['X']))

protonated_residues_types_3 = set(['ARN', 'ASH', 'GLH', 'LYN', 'HIE', 'HIP'])

non_canonical_amino_acids = {
    'ABA' : 'A', # Alpha-aminobutyric acid
    'CCS' : 'C', # Carboxymethylated cysteine
    'CME' : 'C', # S,S-(2-Hydroxyethyl)Thiocysteine (DB04530)
    'CSD' : 'C', # 3-sulfinoalanine
    'CSO' : 'C', # s-hydroxycysteine
    'CSS' : 'C', # S-Mercaptocysteine (DB02761)
    'CSU' : 'C', # ? some type of cysteine or a typo
    'CSW' : 'C', # Cysteine-S-dioxide
    'CSX' : 'C', # Modified cysteine residue
    'SCH' : 'C', # S-Methyl-Thio-Cysteine
    'SMC' : 'C', # S-methylcysteine
    'PCA' : 'E', # Pyroglutamic acid
    'GLZ' : 'G', # Amino-acetaldehyde
    'HIC' : 'H', # 4-Methyl-Histidine
    'M3L' : 'K', # N-Trimethyllysine
    'MLY' : 'K', # dimethyl lysine
    'FME' : 'M', # N-Formylmethionine
    'MSE' : 'M', # selenomethionine
    'MEN' : 'N', # N-methyl asparagine
    'SEP' : 'S', # Phosphoserine
    'SVA' : 'S', # Serine vanadate
    'TPO' : 'T', # phosphothreonine
    'TRN' : 'W', # Nz2-Tryptophan
    'NEH' : 'X', # Ethanamine
    'MPT' : 'X', # Beta-Mercaptopropionic acid
    'NH2' : 'X', # Amino group
    'PTR' : 'Y', # phospotyrosine
    'BHD' : 'D', # (3S)-3-HYDROXY-L-ASPARTIC ACID
    #
    'ASX' : 'B', # ??? N in UniProt entry P0A786 for 2ATC, chain A
    'GLX' : 'Q', # ??? Q in UniProt entry P01075 for 4CPA, chain I
}

###
# DNA
# I am unsure whether this is all correct. The code I inherited seems to leave out DI and DU for DNA and T and I for RNA which seems wrong.
###

dna_nucleotides = set(['DA', 'DC', 'DG', 'DT', 'DU', 'DI']) # deoxyribonucleic acids
rna_nucleotides = set(['A', 'C', 'G', 'U', 'I']) # ribonucleic acids

dna_nucleotides_2to1_map = {
    # Used to map PDB SEQRES DNA sequences to single letter sequences
    'DA' : 'A', 'DC' : 'C', 'DG' : 'G', 'DT' : 'T', 'DU' : 'U', 'DI' : 'I',
}

non_canonical_dna = {
    '5IU' : 'U', # 5-Iodo-2'-Deoxyuridine-5'-Monophosphate
}

non_canonical_rna = {
    'U33' : 'U', # 5-bromo-2'-deoxy-uridine
}

all_recognized_dna = dna_nucleotides.union(set(non_canonical_dna.keys()))
all_recognized_rna = rna_nucleotides.union(set(non_canonical_rna.keys()))


###
# Mutations
#

class PDBResidue(object):
    def __init__(self, Chain, ResidueID, ResidueAA):
        assert(len(Chain) == 1)
        assert(len(ResidueID) == 5)
        assert(ResidueAA in residue_types_1)

        self.Chain = Chain
        self.ResidueID = ResidueID
        self.ResidueAA = ResidueAA

###
# Mutations
#   These classes can represent mutations to PDB chains where Chain is one character and ResidueID is a string.
#   However. since we do not do type-checking and convert ResidueIDs to strings, the same classes can represent mutations
#   to UniParc sequences where Chain is the UniParc ID and ResidueID is an integer.
###

class SimpleMutation(object):
    '''A class to describe mutations to (PDB) structures.'''

    def __init__(self, WildTypeAA, ResidueID, MutantAA, Chain = None):
        self.WildTypeAA = WildTypeAA
        self.ResidueID = ResidueID
        self.MutantAA = MutantAA
        self.Chain = Chain

    def __repr__(self):
        suffix = ''
        if self.Chain:
            return "%s:%s %s->%s%s" % (self.Chain, self.WildTypeAA, str(self.ResidueID), self.MutantAA, suffix)
        else:
            return "?:%s %s->%s%s" % (self.WildTypeAA, str(self.ResidueID), self.MutantAA, suffix)

    def __eq__(self, other):
        '''Only checks amino acid types and residue ID.'''
        if self.WildTypeAA != other.WildTypeAA:
            return False
        if self.ResidueID != other.ResidueID:
            return False
        if self.MutantAA != other.MutantAA:
            return False
        return True

    def __cmp__(self, other):
        '''Only checks amino acid types and residue ID.'''
        if self.Chain != other.Chain:
            if ord(self.Chain) < ord(other.Chain):
                return -1
            else:
                return 1
        selfResidueID = self.ResidueID
        otherResidueID = other.ResidueID
        if selfResidueID != otherResidueID:
            if not selfResidueID.isdigit():
                spair = (int(selfResidueID[:-1]), ord(selfResidueID[-1]))
            else:
                spair = (int(selfResidueID), 0)
            if not otherResidueID.isdigit():
                opair = (int(otherResidueID[:-1]), ord(otherResidueID[-1]))
            else:
                opair = (int(otherResidueID), 0)
            if spair < opair:
                return -1
            else:
                return 1
        return 0

class Mutation(SimpleMutation):
    '''A class to describe mutations to structures.
       For legacy support, we store SecondaryStructurePosition and AccessibleSurfaceArea. This should be rethought.
       We probably want to store SS and ASA for wildtype *and* mutant. This is ambiguous at present.
       '''

    def __init__(self, WildTypeAA, ResidueID, MutantAA, Chain = None, SecondaryStructurePosition = None, AccessibleSurfaceArea = None):
        super(Mutation, self).__init__(WildTypeAA, ResidueID, MutantAA, Chain = Chain)
        self.SecondaryStructurePosition = SecondaryStructurePosition
        self.AccessibleSurfaceArea = AccessibleSurfaceArea

    def __repr__(self):
        suffix = ''
        if self.SecondaryStructurePosition:
            suffix = ' (%s)' % self.SecondaryStructurePosition
        if self.AccessibleSurfaceArea:
            suffix += ' ASA=%s' % self.AccessibleSurfaceArea
        if self.Chain:
            return "%s:%s %s->%s%s" % (self.Chain, self.WildTypeAA, str(self.ResidueID), self.MutantAA, suffix)
        else:
            return "?:%s %s->%s%s" % (self.WildTypeAA, str(self.ResidueID), self.MutantAA, suffix)

class ChainMutation(Mutation):
    '''Refines Mutation by adding the chain as a parameter of the equality function.'''

    def __eq__(self, other):
        if self.WildTypeAA != other.WildTypeAA:
            return False
        if self.ResidueID != other.ResidueID:
            return False
        if self.MutantAA != other.MutantAA:
            return False
        if self.Chain != other.Chain:
            return False
        return True
