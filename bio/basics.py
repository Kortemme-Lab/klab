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

import types

from Bio.SubsMat.MatrixInfo import blosum62 as _blosum62, pam250 as _pam250# The amino acid codes BXZ in these blosum62 and pam250 matrices appear to be amino acid ambiguity codes
import tools.colortext as colortext

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
    "TYR": "Y",
    "UNK": 'X',
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
    'ASX' : 'N', # ??? N in UniProt entry P0A786 for 2ATC, chain A
    'GLX' : 'Q', # ??? Q in UniProt entry P01075 for 4CPA, chain I
}

###
# DNA
# I am unsure whether this is all correct. The code I inherited seems to leave out DI and DU for DNA and T and I for RNA which seems wrong.
###

dna_nucleotides = set(['DA', 'DC', 'DG', 'DT', 'DU', 'DI']) # deoxyribonucleic acids
rna_nucleotides = set(['A', 'C', 'G', 'U', 'I']) # ribonucleic acids

dna_nucleotides_3to1_map = {
    # Used to map Rosetta features database mappings to single letter sequences
    'ADE' : 'A', 'CYT' : 'C', 'GUA' : 'G', 'THY' : 'T', #'DU' : 'U', 'DI' : 'I',
}

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
# Substitution matrices
# Create full matrices to make the lookup logic simpler
# e.g. "pam250.get(x, y) or pam250.get(y, x)" fails due to Python's semantics when the first term is 0 and the second is None - in this case None is returned whereas 0 is what is probably wanted.
# "pam250.get(x, y) or pam250.get(y, x) or 0" is just plain ugly
###

pam250 = {}
for k, v in _pam250.iteritems():
    if k[0] != k[1]:
        assert((k[1], k[0])) not in _pam250
        pam250[(k[1], k[0])] = v
    pam250[(k[0], k[1])] = v

blosum62 = {}
for k, v in _blosum62.iteritems():
    if k[0] != k[1]:
        assert((k[1], k[0])) not in _blosum62
        blosum62[(k[1], k[0])] = v
    blosum62[(k[0], k[1])] = v

###
# Sequences
#

class Sequence(object):
    ''' A class to hold a list of Residues in the same chain.
        This class maintains two elements:
            1) order        List(ID)            : a list of residue IDs in the order of addition;
            2) sequence     Dict(ID->Residue)   : a map from residue IDs to a Residue object (chain, residue ID, residue type, sequence_type).
    '''
    def __init__(self, sequence_type = None):

        self.order = []
        self.sequence = {}
        self.sequence_type = sequence_type

        if sequence_type:
            assert(sequence_type == 'Protein' or sequence_type == 'DNA' or sequence_type == 'RNA' or sequence_type == 'Protein skeleton')

    def __iter__(self):
        self._iter_index = 0
        return self

    def __getitem__(self, item):
        return self.sequence[item]

    def ids(self):
        return self.sequence.keys()

    def next(self): # todo: This is __next__ in Python 3.x
        try:
            id = self.order[self._iter_index]
            self._iter_index += 1
            return id, self.sequence[id]
        except:
            raise StopIteration

    def add(self, r):
        '''Takes an id and a Residue r and adds them to the Sequence.'''
        id = r.get_residue_id()
        if self.order:
            last_id = self.order[-1]
            assert(r.Chain == self.sequence[last_id].Chain)
            assert(r.residue_type == self.sequence[last_id].residue_type)
        self.order.append(id)
        self.sequence[id] = r

    def set_type(self, sequence_type):
        '''Set the type of a Sequence if it has not been set.'''
        if not(self.sequence_type):
            for id, r in self.sequence.iteritems():
                assert(r.residue_type == None)
                r.residue_type = sequence_type
            self.sequence_type = sequence_type

    def __repr__(self):
        sequence = self.sequence
        return "".join([sequence[id].ResidueAA for id in self.order])

    @staticmethod
    def from_sequence(chain, list_of_residues, sequence_type = None):
        '''Takes in a chain identifier and protein sequence and returns a Sequence object of Residues, indexed from 1.'''
        s = Sequence(sequence_type)
        count = 1
        for ResidueAA in list_of_residues:
            s.add(Residue(chain, count, ResidueAA, sequence_type))
            count += 1
        return s

class InconsistentMappingException(Exception): pass

class SequenceMap():
    ''' A class to map the IDs of one Sequence to another.'''

    def __init__(self):
        self.map = {}
        self.substitution_scores = {}

    @staticmethod
    def from_dict(d):
        for k, v in d.iteritems():
            assert(type(k) == types.IntType or type(k) == types.StringType or type(k) == types.UnicodeType)
            assert(type(v) == types.IntType or type(v) == types.StringType or type(v) == types.UnicodeType)
        s = SequenceMap()
        s.map = d
        s.substitution_scores = dict.fromkeys(d.keys(), None)
        return s

    def add(self, key, value, substitution_score):
        self[key] = value
        self.substitution_scores[key] = substitution_score

    def remove(self, key):
        if self.map.get(key):
            del self.map[key]
        if self.substitution_scores.get(key):
            del self.substitution_scores[key]

    def matches(self, other):
        overlap = set(self.keys()).intersection(set(other.keys()))
        for k in overlap:
            if self[k] != other[k]:
                return False
        return True

    def substitution_scores_match(self, other):
        '''Check to make sure that the substitution scores agree. If one map has a null score and the other has a non-null score, we trust the other's score and vice versa.'''
        overlap = set(self.substitution_scores.keys()).intersection(set(other.substitution_scores.keys()))
        for k in overlap:
            if not(self.substitution_scores[k] == None or other.substitution_scores[k] == None):
                if self.substitution_scores[k] != other.substitution_scores[k]:
                    return False
        return True

    def keys(self):
        return self.map.keys()

    def values(self):
        return self.map.values()

    def __getitem__(self, item):
        return self.map.get(item)

    def __setitem__(self, key, value):
        assert(type(key) == types.IntType or type(key) == types.StringType or type(key) == types.UnicodeType)
        assert(type(value) == types.IntType or type(value) == types.StringType or type(value) == types.UnicodeType)
        self.map[key] = value
        self.substitution_scores[key] = None

    def next(self): # todo: This is __next__ in Python 3.x
        try:
            id = self._iter_keys.pop()
            return id, self.map[id], self.substitution_scores[id]
        except:
            raise StopIteration

    def __iter__(self):
        self._iter_keys = set(self.map.keys())
        return self

    def __eq__(self, other):
        if self.keys() == other.keys():
            for k in self.keys():
                if self[k] != other[k]:
                    return False
            return True
        else:
            return False

    def __le__(self, other):
        if set(self.keys()).issubset == set(other.keys()):
            for k in self.keys():
                if self[k] != other[k]:
                    return False
            return True
        else:
            return False

    def glue(self, other):
        return self + other

    def __add__(self, other):
        '''Glue two maps together. The operation is defined on maps which agree on the intersection of their domain as:
             (f + g)(x) = f(x) if x not in dom(f)
             (f + g)(x) = g(x) if x not in dom(g)
             (f + g)(x) = f(x) = g(x) if x in dom(f) n dom(g)
        '''

        if not self.matches(other):
            overlap = set(self.keys()).intersection(set(other.keys()))
            mismatches = [k for k in overlap if self[k] != other[k]]
            raise InconsistentMappingException('The two maps disagree on the common domain elements %s.' % str(mismatches))
        elif not self.substitution_scores_match(other):
            overlap = set(self.substitution_scores.keys()).intersection(set(other.substitution_scores.keys()))
            mismatches = [k for k in overlap if self.substitution_scores[k] != other.substitution_scores[k]]
            raise InconsistentMappingException('The two maps scores disagree on the common domain elements %s.' % str(mismatches))
        elif not self.__class__ == other.__class__:
            raise InconsistentMappingException('''The two maps have different classes: '%s' and '%s'.''' % ( self.__class__, other.__class__))
        else:
            d, s = {}, {}
            other_domain = set(other.keys()).difference(set(self.keys()))
            for k in self.keys():
                d[k] = self.map[k]
                s[k] = self.substitution_scores[k]
            for k in other_domain:
                assert(self.map.get(k) == None)
                assert(self.substitution_scores.get(k) == None)
                d[k] = other.map[k]
                s[k] = other.substitution_scores[k]
            o = self.__class__.from_dict(d)
            o.substitution_scores = s
            return o

    def __repr__(self):
        s = []
        substitution_scores = self.substitution_scores
        for k, v in sorted(self.map.iteritems()):
            if type(k) == types.StringType or type(k) == types.UnicodeType:
                key = "'%s'" % k
            else:
                key = str(k)
            if type(v) == types.StringType or type(v) == types.UnicodeType:
                val = "'%s'" % v
            else:
                val = str(v)
            if substitution_scores.get(k):
                s.append('%s->%s (%s)' % (str(key), str(val), str(substitution_scores[k])))
            else:
                s.append('%s->%s' % (str(key), str(val)))
        return ", ".join(s)

class PDBUniParcSequenceMap(SequenceMap):
    ''' A class to map the IDs of a PDB chain's Sequence (ATOM/SEQRES/FASTA) to a UniParc residue pairs (UniParcID, sequence index).
        Mapping to tuples is necessary for some cases e.g. for chimeras like 1M7T.
    '''

    def __setitem__(self, key, value):
        assert(len(value) == 2)
        assert(type(key) == types.IntType or type(key) == types.StringType or type(key) == types.UnicodeType)
        assert((type(value[0]) == types.StringType or type(value[0]) == types.UnicodeType) and (type(value[1]) == types.IntType))

        self.map[key] = value
        self.substitution_scores[key] = None

    @staticmethod
    def from_dict(d):
        for k, v in d.iteritems():
            assert(len(v) == 2)
            assert(type(k) == types.IntType or type(k) == types.StringType or type(k) == types.UnicodeType)
            assert((type(v[0]) == types.StringType or type(v[0]) == types.UnicodeType) and (type(v[1]) == types.IntType))

        s = PDBUniParcSequenceMap()
        s.map = d
        s.substitution_scores = dict.fromkeys(d.keys(), None)
        return s

class UniParcPDBSequenceMap(SequenceMap):
    ''' A class to map the IDs of UniParc residue pairs (UniParcID, sequence index) to a PDB chain's Sequence (ATOM/SEQRES/FASTA).
        Mapping from tuples is necessary for some cases e.g. for chimeras like 1M7T.
    '''

    def __setitem__(self, key, value):
        assert(len(key) == 2)
        assert(type(value) == types.IntType or type(value) == types.StringType or type(value) == types.UnicodeType)
        assert((type(key[0]) == types.StringType or type(key[0]) == types.UnicodeType) and (type(key[1]) == types.IntType))

        self.map[key] = value
        self.substitution_scores[key] = None

    @staticmethod
    def from_dict(d):
        for k, v in d.iteritems():
            assert(len(k) == 2)
            assert(type(v) == types.IntType or type(v) == types.StringType or type(v) == types.UnicodeType)
            assert((type(k[0]) == types.StringType or type(k[0]) == types.UnicodeType) and (type(k[1]) == types.IntType))

        s = PDBUniParcSequenceMap()
        s.map = d
        s.substitution_scores = dict.fromkeys(d.keys(), None)
        return s

def sequence_formatter(sequences):
    assert(sequences and (len(set(map(len, sequences))) == 1))
    first_sequence = sequences[0]
    header = ("%s%s" % ("1234567890" * (len(first_sequence)/10), "1234567890"[:len(first_sequence) - (len(first_sequence)/10 * 10)])).replace('0', colortext.make('0', 'orange'))
    s = ['|%s|' % header]
    for sequence in sequences:
        s.append('|%s|' % sequence)
    return "\n".join(s)

###
# Substitutions
#

class SubstitutionScore(object):
    ''' Container class to score substitution matrix scores for a residue match.
        The clustal score is based on the Clustal Omega alignment output (clustal format). A score of 1 (asterix) means
        identical residue types, 0 (colon) indicates "conservation between groups of strongly similar properties -
        scoring > 0.5 in the Gonnet PAM 250 matrix." A score of -1 (period) indicates "conservation between groups of
        weakly similar properties - scoring =< 0.5 in the Gonnet PAM 250 matrix." '''

    clustal_symbols = {1 : '*', 0 : ':', -1 : '.'}

    def __init__(self, clustal, from_residue, to_residue):
        assert(-1 <= clustal <= 1)
        self.clustal = clustal
        self.blosum62 = blosum62[(from_residue, to_residue)]
        self.pam250 = pam250[(from_residue, to_residue)]

    def __repr__(self):
        return "(%s, b%d, p%d)" % (SubstitutionScore.clustal_symbols[self.clustal], self.blosum62, self.pam250)
###
# Residues
#

class Residue(object):
    # For residues ResidueID
    def __init__(self, Chain, ResidueID, ResidueAA, residue_type = None):
        if residue_type:
            if residue_type == 'Protein' or residue_type == 'Protein skeleton':
                assert((ResidueAA in residue_types_1) or (ResidueAA in protonated_residues_types_1) or (ResidueAA == 'X') or (ResidueAA == 'B'))
            else:
                assert(ResidueAA in nucleotide_types_1)
        self.Chain = Chain
        self.ResidueID = ResidueID
        self.ResidueAA = ResidueAA
        self.residue_type = residue_type

    def __repr__(self):
        return "%s:%s %s" % (self.Chain, str(self.ResidueID).strip(), self.ResidueAA)

    def __eq__(self, other):
        '''Basic form of equality, just checking the amino acid types. This lets us check equality over different chains with different residue IDs.'''
        return (self.ResidueAA == other.ResidueAA) and (self.residue_type == other.residue_type)

    def get_residue_id(self):
        return self.ResidueID

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

    def get_residue_id(self):
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
