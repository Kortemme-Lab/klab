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

protonated_residue_type_3to1_map = {
    'ARN': 'R', # neutral arginine
    'ASH': 'D', # protonated aspartic acid
    'GLH': 'E', # protonated glutamic acid
    'LYN': 'K', # neutral lysine
    'HIE': 'H', # epsilon-protonated histidine
    'HIP': 'H', # epsilon- and delta-protonated histidine
    'HIS': 'H', # delta-protonated histidine
    'CYM': 'C', # deprotonated or bonded to metal atom
    'CYT': 'C', # deprotonated negative cysteine
    'CYX': 'C', # involved in disulphide bridge and other bonds / neutral cysteine
}
protonated_residues_types_3 = set(protonated_residue_type_3to1_map.keys())
protonated_residues_types_1 = set(protonated_residue_type_3to1_map.values())

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

nucleotide_types_1 = set(dna_nucleotides_2to1_map.values()) # for use in SEQRES sequences

###
# Mutations
#

class Sequence(object):
    '''A class to hold a list of Residues in the same chain. The order of the sequence is the order of addition.'''
    def __init__(self, sequence_type = None):
        self.sequence = []
        if sequence_type:
            assert(sequence_type == 'Protein' or sequence_type == 'DNA' or sequence_type == 'RNA')
        self.sequence_type = sequence_type

    def add(self, r):
        if self.sequence:
            assert(r.Chain == self.sequence[-1].Chain)
            assert(r.residue_type == self.sequence[-1].residue_type)
        self.sequence.append(r)

    def set_type(self, sequence_type):
        '''Set the type of a Sequence if it has not been set.'''
        if not(self.sequence_type):
            for r in self.sequence:
                r.sequence_type = sequence_type
            self.sequence_type = sequence_type

    def __repr__(self):
        return "".join([r.ResidueAA for r in self.sequence])

    @staticmethod
    def from_sequence(chain, list_of_residues, sequence_type = None):
        '''Takes in a chain identifier and protein sequence and returns a Sequence object of Residues, indexed from 1.'''
        s = Sequence(sequence_type)
        count = 1
        for ResidueAA in list_of_residues:
            if sequence_type:
                s.add(Residue(chain, count, ResidueAA, sequence_type))
            else:
                s.add(Residue(chain, count, ResidueAA, sequence_type))
            count += 1
        return s


class Residue(object):
    def __init__(self, Chain, ResidueID, ResidueAA, residue_type = None):
        if residue_type:
            if residue_type == 'Protein':
                assert((ResidueAA in residue_types_1) or (ResidueAA in protonated_residues_types_1))
            else:
                assert(ResidueAA in nucleotide_types_1)
        self.Chain = Chain
        self.ResidueID = ResidueID
        self.ResidueAA = ResidueAA
        self.residue_type = residue_type

    def __repr__(self):
        return "%s:%s %s" % (self.Chain, self.ResidueID.strip(), self.ResidueAA)

    def __eq__(self, other):
        '''Basic form of equality, just checking the amino acid types. This lets us check equality over different chains with different residue IDs.'''
        return (self.ResidueAA == other.ResidueAA) and (self.residue_type == other.residue_type)

class PDBResidue(Residue):
    def __init__(self, Chain, ResidueID, ResidueAA, residue_type, Residue3AA = None):
        '''Residue3AA has to be used when matching non-canonical residues/HETATMs to the SEQRES record e.g. 34H in 1A2C.'''
        assert(len(Chain) == 1)
        assert(len(ResidueID) == 5)
        super(PDBResidue, self).__init__(Chain, ResidueID, ResidueAA, residue_type)
        self.Residue3AA = Residue3AA

    def add_position(self, x, y, z):
        self.x, self.y, self.z = x, y, z

    def __repr__(self):
        return "%s%s" % (self.Chain, self.ResidueID)

class IdentifyingPDBResidue(PDBResidue):
    '''A sortable subclass.'''

    def __eq__(self, other):
        return (self.Chain == other.Chain) and (self.ResidueID == other.ResidueID) and (self.ResidueAA == other.ResidueAA) and (self.residue_type == other.residue_type)

    def __cmp__(self, other):
        '''Only checks chains and residue IDs.'''
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
