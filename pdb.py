#!/usr/bin/python2.4


import re
import sys
import os
import types
import string
import UserDict
import spatialhash
import chainsequence
import math

#todo: replace with ROSETTAWEB_SK_AA
aa1 = {"ALA": "A", "CYS": "C", "ASP": "D", "GLU": "E", "PHE": "F", "GLY": "G",
       "HIS": "H", "ILE": "I", "LYS": "K", "LEU": "L", "MET": "M", "ASN": "N",
       "PRO": "P", "GLN": "Q", "ARG": "R", "SER": "S", "THR": "T", "VAL": "V",
       "TRP": "W", "TYR": "Y"}

amino_acid_codes = aa1.values()
relaxed_amino_acid_codes = amino_acid_codes + ['X']

non_canonical_aa1 = {
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

known_chimeras = set([
    ('1M7T', 'A'), # chimera of UniProtKB ACs P0AA25 (previously P00274) and P10599
    ])

maps_to_multiple_uniprot_ACs = set([('1Z1I', 'A'), ])

residues = ["ALA", "CYS", "ASP", "ASH", "GLU", "GLH", "PHE", "GLY", "HIS", 
            "HIE", "HIP", "ILE", "LYS", "LYN", "LEU", "MET", "ASN", "PRO", 
            "GLN", "ARG", "ARN", "SER", "THR", "VAL", "TRP", "TYR"]

cases_with_ACE_residues_we_can_ignore = set(['3UB5', '1TIN', '2ZTA', '5CPV', '1ATN', '1LFO', '1OVA', '3PGK', '2FAL', '2SOD', '1SPD'])

# todo: replace residues with this and move to rwebhelper.py
allowedResidues = {}
for r in residues:
    allowedResidues[r] = True

nucleotides_dna = ["DT","DA","DC","DG"]
nucleotides_dna_to_shorthand = {
    'DA' : 'A', 'DC' : 'C', 'DG' : 'G', 'DT' : 'T'
}
non_canonical_dna = {
    '5IU' : 'U', # 5-Iodo-2'-Deoxyuridine-5'-Monophosphate
}
nucleotides_rna = ["U","C","G","A"]
set_of_nucleotides_dna = set(nucleotides_dna)

records = ["HEADER","OBSLTE","TITLE","SPLIT","CAVEAT","COMPND","SOURCE","KEYWDS",
           "EXPDTA","NUMMDL","MDLTYP","AUTHOR","REVDAT","SPRSDE","JRNL","REMARK",
           "DBREF","DBREF1","DBREF2","DBREF1/DBREF2","SEQADV","SEQRES","MODRES",
           "HET","HETNAM","HETSYN","FORMUL","HELIX","SHEET","SSBOND","LINK","CISPEP",
           "SITE","CRYST1","ORIGX1","ORIGX2","ORIGX3","SCALE1","SCALE2","SCALE3",
           "MTRIX1","MTRIX2","MTRIX3","MODEL","ATOM","ANISOU","TER","HETATM",
           "ENDMDL","CONECT","MASTER","END"]

def ChainResidueID2String(chain, residueID):
    '''Takes a chain ID e.g. 'A' and a residueID e.g. '123' or '123A' and returns the 6-character identifier
       spaced as in the PDB format.'''
    return "%s%s" % (chain, ResidueID2String(residueID))

def ResidueID2String(residueID):
    '''Takes a chain ID e.g. 'A' and a residueID e.g. '123' or '123A' and returns the 6-character identifier
       spaced as in the PDB format.'''
    if residueID.isdigit():
        return "%s " % (residueID.rjust(4))
    else:
        return "%s" % (residueID.rjust(5))

def checkPDBAgainstMutations(pdbID, pdb, mutations):
    resID2AA = pdb.ProperResidueIDToAAMap()
    badmutations = []
    for m in mutations:
        wildtype = resID2AA.get(ChainResidueID2String(m[0], m[1]), "")
        if m[2] != wildtype:
            badmutations.append("%s%s:%s->%s" % (m[0], m[1], m[2], m[3]))
    if badmutations:
        raise Exception("The mutation(s) %s could not be matched against the PDB %s." % (string.join(badmutations, ", "), pdbID))

def computeMeanAndStandardDeviation(values):
    sum = 0
    n = len(values)

    for v in values:
        sum += v

    mean = sum / n
    sumsqdiff = 0

    for v in values:
        t = (v - mean)
        sumsqdiff += t * t

    variance = sumsqdiff / n
    stddev = math.sqrt(variance)

    return mean, stddev, variance

class Residue(object):
    def __init__(self, Chain, ResidueID, ResidueAA):
        assert(len(Chain) == 1)
        assert(len(ResidueID) == 5)
        assert(ResidueAA in aa1.values())

        self.Chain = Chain
        self.ResidueID = ResidueID
        self.ResidueAA = ResidueAA

class JRNL(object):

    def __init__(self, lines):
        if not lines:
            raise Exception("Could not parse JRNL: No lines to parse.")
        self.d = {}
        self.d["lines"] = lines
        self.parse_REF()
        self.parse_REFN()
        self.parse_DOI()

    def getInfo(self):
        return self.d

    def parse_REF(self):
        lines = [line for line in self.d["lines"] if line.startswith("JRNL        REF ")]
        mainline = lines[0]
        if not mainline[19:34].startswith("TO BE PUBLISHED"):
            numContinuationLines = mainline[16:18].strip()
            if numContinuationLines:
                numContinuationLines = int(numContinuationLines)
                if not numContinuationLines + 1 == len(lines):
                    raise Exception("There are %d REF lines but the continuation field (%d) suggests there should be %d." % (len(lines), numContinuationLines, numContinuationLines + 1))
            else:
                numContinuationLines = 0

            pubName = [mainline[19:47].rstrip()]
            volumeV = mainline[49:51].strip()
            volume = mainline[51:55].strip()
            if volumeV:
                assert(volume)
            page = mainline[56:61].strip()
            year = mainline[62:66]

            # Count the number of periods, discounting certain abbreviations
            plines = []
            for line in lines:
                pline = line.replace("SUPPL.", "")
                pline = pline.replace("V.", "")
                pline = pline.replace("NO.", "")
                pline = pline.replace("PT.", "")
                plines.append(pline)
            numperiods = len([1 for c in string.join(plines,"") if c == "."])

            # Reconstruct the publication name
            for n in range(1, numContinuationLines + 1):
                line = lines[n]
                pubNameField = line[19:47]
                lastFieldCharacter = pubNameField[-1]
                lastLineCharacter = line.strip()[-1]
                txt = pubNameField.rstrip()
                pubName.append(txt)
                if lastFieldCharacter == "-" or lastFieldCharacter == "." or lastLineCharacter == "-" or (lastLineCharacter == "." and numperiods == 1):
                    pubName.append(" ")
            pubName = string.join(pubName, "")
            self.d["REF"] = {
                "pubName"	: pubName,
                "volume"	: volume or None,
                "page"		: page or None,
                "year"		: year or None,
            }
            self.d["published"] = True
        else:
            self.d["REF"] = {}
            self.d["published"] = False

    def parse_REFN(self):
        PRELUDE = "JRNL        REFN"
        if not self.d.get("published"):
            self.parse_REF()
        isPublished = self.d["published"]

        lines = [line for line in self.d["lines"] if line.startswith(PRELUDE)]
        if not len(lines) == 1:
            raise Exception("Exactly one JRNL REF line expected in the PDB title.")
        line = lines[0]
        if isPublished:
            type = line[35:39]
            ID = line[40:65].strip()
            if type != "ISSN" and type != "ESSN":
                raise Exception("Invalid type for REFN field (%s)" % type)
            self.d["REFN"] = {"type" : type, "ID" : ID}
        else:
            assert(line.strip() == PRELUDE)

    def parse_DOI(self):
        lines = [line for line in self.d["lines"] if line.startswith("JRNL        DOI ")]
        if lines:
            line = string.join([line[19:79].strip() for line in lines], "")
            if line.lower().startswith("doi:"):
                self.d["DOI"] = ["%s" % line[4:]]
            else:
                self.d["DOI"] = line
        else:
            self.d["DOI"] = None

class NonCanonicalResidueException(Exception):
    pass

COMPND_field_map = {
    'MOL_ID' : 'MoleculeID',
    'MOLECULE' : 'Name',
    'CHAIN' : 'Chains',
    'FRAGMENT' : 'Fragment',
    'SYNONYM' : 'Synonym',
    'EC' : 'EC',
    'ENGINEERED' : 'Engineered',
    'MUTATION' : 'Mutation',
    'OTHER_DETAILS' : 'OtherDetails',
}

SOURCE_field_map = {
    'MOL_ID' : 'MoleculeID',
    'SYNTHETIC' : 'Synthetic',
    'ORGANISM_SCIENTIFIC' : 'OrganismScientificName',
    'ORGANISM_COMMON' : 'OrganismCommonName',
    'ORGANISM_TAXID' : 'OrganismNCBITaxonomyID',
}

#From the PDB format documentation at http://www.wwpdb.org/documentation/format33/sect1.html

allowed_record_types = set([
# One time, single line:
'CRYST1', #     Unit cell parameters, space group, and Z.
'END   ', #     Last record in the file.
'HEADER', #     First line of the entry, contains PDB ID code, classification, and date of deposition.
'NUMMDL', #     Number of models.
'MASTER', #     Control record for bookkeeping.
'ORIGXn', #     Transformation from orthogonal  coordinates to the submitted coordinates (n = 1, 2, or 3).
'SCALEn', #     Transformation from orthogonal coordinates to fractional crystallographic coordinates  (n = 1, 2, or 3).
# One time, multiple lines:
'AUTHOR', #     List of contributors.
'CAVEAT', #     Severe error indicator.
'COMPND', #     Description of macromolecular contents of the entry.
'EXPDTA', #     Experimental technique used for the structure determination.
'MDLTYP', #     Contains additional annotation  pertinent to the coordinates presented  in the entry.
'KEYWDS', #     List of keywords describing the macromolecule.
'OBSLTE', #     Statement that the entry has been removed from distribution and list of the ID code(s) which replaced it.
'SOURCE', #     Biological source of macromolecules in the entry.
'SPLIT ', #     List of PDB entries that compose a larger  macromolecular complexes.
'SPRSDE', #     List of entries obsoleted from public release and replaced by current entry.
'TITLE ', #     Description of the experiment represented in the entry.
# Multiple times, one line:
'ANISOU', #     Anisotropic temperature factors.
'ATOM  ', #     Atomic coordinate records for  standard groups.
'CISPEP', #     Identification of peptide residues in cis conformation.
'CONECT', #     Connectivity records.
'DBREF ', #     Reference  to the entry in the sequence database(s).
'HELIX ', #     Identification of helical substructures.
'HET   ', #     Identification of non-standard groups heterogens).
'HETATM', #     Atomic coordinate records for heterogens.
'LINK  ', #     Identification of inter-residue bonds.
'MODRES', #     Identification of modifications to standard residues.
'MTRIXn', #     Transformations expressing non-crystallographic symmetry (n = 1, 2, or 3). There may be multiple sets of these records.
'REVDAT', #     Revision date and related information.
'SEQADV', #     Identification of conflicts between PDB and the named sequence database.
'SHEET ', #     Identification of sheet substructures.
'SSBOND', #     Identification of disulfide bonds.
# Multiple times, multiple lines:
'FORMUL', #     Chemical formula of non-standard groups.
'HETNAM', #     Compound name of the heterogens.
'HETSYN', #     Synonymous compound names for heterogens.
'SEQRES', #     Primary sequence of backbone residues.
'SITE  ', #     Identification of groups comprising important entity sites.
# Grouping:
'ENDMDL', #     End-of-model record for multiple structures in a single coordinate entry.
'MODEL ', #     Specification of model number for multiple structures in a single coordinate entry.
'TER   ', #     Chain terminator.
# Other:
'JRNL  ', #     Literature citation that defines the coordinate set.
'REMARK', #     General remarks; they can be structured or free form.
])

class PDBParsingException(Exception): pass

class PDB:
    """A class to store and manipulate PDB data"""

    ## Constructor:
  # takes either a pdb file, a list of strings = lines of a pdb file, or another object
  # 
  # 
    def __init__(self, pdb = None, pdb_id = None):

        self.parsed_lines = {}
        self.structure_lines = [] # For ATOM and HETATM records
        self.ddGresmap = None
        self.ddGiresmap = None
        self.lines = []
        self.journal = None
        self.pdb_id = pdb_id
        if type(pdb) == types.StringType:
            self.read(pdb)
        elif type(pdb) == types.ListType:
            self.lines.extend(pdb)
        elif type(pdb) == type(self):
            self.lines.extend(pdb.lines)
        self.split_lines()

    def split_lines(self):
        parsed_lines = {}
        for rt in allowed_record_types:
            parsed_lines[rt] = []
        parsed_lines[0] = []

        for line in self.lines:
            linetype = line[0:6]
            if linetype in allowed_record_types:
                parsed_lines[linetype].append(line)
                if linetype == 'ATOM' or linetype == 'HETATM':
                    self.structure_lines.append(line)
            else:
                parsed_lines[0].append(line)

        self.parsed_lines = parsed_lines

    def get_resolution(self):
        resolution = None
        for line in self.parsed_lines["REMARK"]:
            if line[9] == "2" and line[11:22] == "RESOLUTION.":
                #if id == :
                #	line = "REMARK   2 RESOLUTION. 3.00 ANGSTROMS.

                                # This code SHOULD work but there are badly formatted PDBs in the RCSB database.
                # e.g. "1GTX"
                #if line[31:41] == "ANGSTROMS.":
                #	try:
                #		resolution = float(line[23:30])
                #	except:
                #		raise Exception("Error parsing PDB file to determine resolution. The resolution line\n  '%s'\ndoes not match the PDB standard. Expected data for diffraction experiments." % line )
                #if line[23:38] == "NOT APPLICABLE.":
                #	resolution = "N/A"
                #else:
                #	raise Exception("Error parsing PDB file to determine resolution. The resolution line\n  '%s'\ndoes not match the PDB standard." % line )
                #
                # Instead, we use the code below:
                if resolution:
                    raise Exception("Found multiple RESOLUTION lines.")
                strippedline = line[22:].strip()
                Aindex = strippedline.find("ANGSTROMS.")
                if strippedline == "NOT APPLICABLE.":
                    resolution = "N/A"
                elif Aindex != -1 and strippedline.endswith("ANGSTROMS."):
                    if strippedline[:Aindex].strip() == "NULL":
                        resolution = "N/A" # Yes, yes, yes, I know. Look at 1WSY.pdb.
                    else:
                        try:
                            resolution = float(strippedline[:Aindex].strip())
                        except:
                            raise PDBParsingException("Error parsing PDB file to determine resolution. The resolution line\n  '%s'\ndoes not match the PDB standard. Expected data for diffraction experiments." % line )
                else:
                    raise PDBParsingException("Error parsing PDB file to determine resolution. The resolution line\n  '%s'\ndoes not match the PDB standard." % line )
        if not resolution:
            raise PDBParsingException("Could not determine resolution.")
        return resolution

    def get_techniques(self):
        techniques = None
        for line in self.parsed_lines["EXPDTA"]:
            techniques = line[10:71].split(";")
            for k in range(len(techniques)):
                techniques[k] = techniques[k].strip()
            techniques = ";".join(techniques)
        if not techniques:
            raise PDBParsingException("Could not determine techniques used.")
        return techniques

    def get_ATOM_and_HETATM_chains(self):
        '''Returns the chains of the PDB in the order in which they appear in the file.'''
        chains = []
        for line in self.structure_lines:
            chainID = line[21]
            if chainID not in chains:
                chains.append(chainID)
        return chains

    def get_DB_references(self):
        ''' "The DBREF record provides cross-reference links between PDB sequences (what appears in SEQRES record) and
                a corresponding database sequence." - http://www.wwpdb.org/documentation/format33/sect3.html#DBREF

        '''

        _database_names = {
            'GB'    :  'GenBank',
            'PDB'   :  'Protein Data Bank',
            'UNP'   :  'UNIPROT',
            'NORINE':  'Norine',
            'TREMBL': 'UNIPROT',
        }

        DBREF_lines = [l for l in self.lines if l.startswith('DBREF')]
        DBref = {}
        for l in DBREF_lines:
            pdb_id = l[7:11]
            chain_id = l[12]
            seqBegin = int(l[14:18])
            insertBegin = l[18]
            seqEnd = int(l[20:24])
            insertEnd = l[24]
            database = _database_names[l[26:32].strip()]
            dbAccession = l[33:41].strip()
            dbIdCode = l[42:54].strip()
            dbseqBegin = int(l[55:60])
            idbnsBeg = l[60]
            dbseqEnd = int(l[62:67])
            dbinsEnd = l[67]

            DBref[pdb_id] = DBref.get(pdb_id, {})
            DBref[pdb_id][database] = DBref[pdb_id].get(database, {})
            print((pdb_id, chain_id), known_chimeras)
            if DBref[pdb_id][database].get(chain_id):
                if not(DBref[pdb_id][database][chain_id]['dbAccession'] == dbAccession and DBref[pdb_id][database][chain_id]['dbIdCode'] == dbIdCode):
                    raise PDBParsingException('This code needs to be generalized. dbIdCode should really be a list to handle chimera cases.')
            else:
                DBref[pdb_id][database][chain_id] = {'dbAccession'   :   dbAccession, 'dbIdCode'      :   dbIdCode, 'PDBtoDB_mapping' : []}

            DBref[pdb_id][database][chain_id]['PDBtoDB_mapping'].append(
                {'PDBRange'      :   ("%d%s" % (seqBegin,  insertBegin), "%d%s" % (seqEnd,  insertEnd)),
                'dbRange'       :   ("%d%s" % (dbseqBegin, idbnsBeg), "%d%s" % (dbseqEnd, dbinsEnd)),
                }
            )
        return DBref

    def getSEQRESSequences(self):
        # Extract the SEQRES lines
        SEQRES_lines = []
        found_SEQRES_lines = False
        pdb_id = self.pdb_id
        for line in self.lines:
            if line.startswith("HEADER"):
                if not pdb_id:
                    pdb_id = line[62:66]
            if not line.startswith("SEQRES"):
                if not found_SEQRES_lines:
                    continue
                else:
                    break
            else:
                found_SEQRES_lines = True
                SEQRES_lines.append(line)
        for x in range(0, len(SEQRES_lines)):
            assert(SEQRES_lines[x][7:10].strip().isdigit())

        if not SEQRES_lines:
            raise Exception("Do not raise this exception")
            return None

        # If the COMPND lines exist, concatenate them together into one string
        sequences = {}
        chains_in_order = []
        SEQRES_lines = [line[11:].strip() for line in SEQRES_lines]

        # Collect all residues for all chains
        chain_tokens = {}
        for line in SEQRES_lines:
            chainID = line[0]
            if chainID not in chains_in_order:
                chains_in_order.append(chainID)
            chain_tokens[chainID] = chain_tokens.get(chainID, [])
            residues = line[6:].strip().split()
            chain_tokens[chainID].extend(residues)

        self.chain_types = {}
        for chain_id, tokens in chain_tokens.iteritems():
            # Determine whether chains are DNA or proteins
            chain_type = None
            set_of_tokens = set(tokens)
            if (set(tokens).union(set_of_nucleotides_dna) == set_of_nucleotides_dna) or (len(set_of_tokens) <= 5 and len(set_of_tokens.union(set_of_nucleotides_dna)) == len(set_of_tokens) + 1): # allow one unknown DNA residue
                chain_type = 'DNA'
            else:
                chain_type = 'Protein'
            self.chain_types[chain_id] = chain_type

            sequence = []
            if chain_type == 'DNA':
                for r in tokens:
                    if nucleotides_dna_to_shorthand.get(r):
                        sequence.append(nucleotides_dna_to_shorthand[r])
                    else:
                        if non_canonical_dna.get(r):
                            sequence.append(non_canonical_dna[r])
                        else:
                            raise Exception("Unknown DNA residue %s." % r)
            else:
                for r in tokens:
                    if aa1.get(r):
                        sequence.append(aa1[r])
                    else:
                        if non_canonical_aa1.get(r):
                            #print('Mapping non-canonical residue %s to %s.' % (r, non_canonical_aa1[r]))
                            #print(SEQRES_lines)
                            #print(line)
                            sequence.append(non_canonical_aa1[r])
                        elif r == 'UNK':
                            continue
                        # Skip these residues
                        elif r == 'ACE' and pdb_id in cases_with_ACE_residues_we_can_ignore:
                            continue
                        # End of skipped residues
                        else:
                            #print(SEQRES_lines)
                            #print(line)
                            raise Exception("Unknown protein residue %s." % r)
            sequences[chain_id] = "".join(sequence)

        return sequences, chains_in_order



    def getMoleculeInfo(self):
        # Extract the COMPND lines
        COMPND_lines = []
        found_COMPND_lines = False
        for line in self.lines:
            if not line.startswith("COMPND"):
                if not found_COMPND_lines:
                    continue
                else:
                    break
            else:
                found_COMPND_lines = True
                COMPND_lines.append(line)
        for x in range(1, len(COMPND_lines)):
            assert(int(COMPND_lines[x][7:10]) == x+1)

        if not COMPND_lines:
            raise Exception("Do not raise this exception")
            return None

        # If the COMPND lines exist, concatenate them together into one string
        COMPND_lines = " ".join([line[10:].strip() for line in COMPND_lines])
        COMPND_lines.replace("  ", " ")

        # Split the COMPND lines into seperate molecule entries
        molecules = {}
        MOL_DATA = ["MOL_ID:%s".strip() % s for s in COMPND_lines.split('MOL_ID:') if s]

        # Parse the molecule entries
        for MD in MOL_DATA:
            # Hack for 2OMT
            MD = MD.replace('EPITHELIAL-CADHERIN; E-CAD/CTF1', 'EPITHELIAL-CADHERIN: E-CAD/CTF1')
            # Hack for 1M2T
            MD = MD.replace('SYNONYM: BETA-GALACTOSIDE SPECIFIC LECTIN I A CHAIN; MLA; ML-I A;', 'SYNONYM: BETA-GALACTOSIDE SPECIFIC LECTIN I A CHAIN, MLA, ML-I A,')
            # Hack for 1IBR
            MD = MD.replace('SYNONYM: RAN; TC4; RAN GTPASE; ANDROGEN RECEPTOR- ASSOCIATED PROTEIN 24;', 'SYNONYM: RAN TC4, RAN GTPASE, ANDROGEN RECEPTOR-ASSOCIATED PROTEIN 24;')
            # Hack for 1IBR
            MD = MD.replace('SYNONYM: KARYOPHERIN BETA-1 SUBUNIT; P95; NUCLEAR FACTOR P97; IMPORTIN 90', 'SYNONYM: KARYOPHERIN BETA-1 SUBUNIT, P95, NUCLEAR FACTOR P97, IMPORTIN 90')
            # Hack for 1NKH
            MD = MD.replace('SYNONYM: B4GAL-T1; BETA4GAL-T1; BETA-1,4-GALTASE 1; BETA-1, 4-GALACTOSYLTRANSFERASE 1;  UDP-GALACTOSE:BETA-N- ACETYLGLUCOSAMINE BETA-1,4-GALACTOSYLTRANSFERASE 1; EC: 2.4.1.22, 2.4.1.90, 2.4.1.38; ENGINEERED: YES; OTHER_DETAILS: CHAINS A AND B FORM FIRST, C AND D SECOND LACTOSE SYNTHASE COMPLEX',
                            'SYNONYM: B4GAL-T1, BETA4GAL-T1, BETA-1,4-GALTASE 1, BETA-1, 4-GALACTOSYLTRANSFERASE 1,  UDP-GALACTOSE:BETA-N- ACETYLGLUCOSAMINE BETA-1,4-GALACTOSYLTRANSFERASE 1, EC: 2.4.1.22, 2.4.1.90, 2.4.1.38, ENGINEERED: YES, OTHER_DETAILS: CHAINS A AND B FORM FIRST, C AND D SECOND LACTOSE SYNTHASE COMPLEX')
            # Hacks for 2PMI
            MD = MD.replace('SYNONYM: SERINE/THREONINE-PROTEIN KINASE PHO85; NEGATIVE REGULATOR OF THE PHO SYSTEM;',
                            'SYNONYM: SERINE/THREONINE-PROTEIN KINASE PHO85, NEGATIVE REGULATOR OF THE PHO SYSTEM;')
            MD = MD.replace('SYNONYM: PHOSPHATE SYSTEM CYCLIN PHO80; AMINOGLYCOSIDE ANTIBIOTIC SENSITIVITY PROTEIN 3;',
                            'SYNONYM: PHOSPHATE SYSTEM CYCLIN PHO80, AMINOGLYCOSIDE ANTIBIOTIC SENSITIVITY PROTEIN 3;')

            MOL_fields = [s.strip() for s in MD.split(';') if s.strip()]
            molecule = {}
            for field in MOL_fields:
                print(field)
                field = field.split(":")
                field_name = COMPND_field_map[field[0].strip()]
                field_data = field[1].strip()
                molecule[field_name] = field_data

            # Normalize and type the fields 

            # Required (by us) fields
            molecule['MoleculeID'] = int(molecule['MoleculeID'])
            molecule['Chains'] = map(string.strip, molecule['Chains'].split(','))
            for c in molecule['Chains']:
                assert(len(c) == 1)

            # Optional fields
            if not molecule.get('Engineered'):
                molecule['Engineered'] = None
            elif molecule.get('Engineered') == 'YES':
                molecule['Engineered'] = True
            elif molecule.get('Engineered') == 'NO':
                molecule['Engineered'] = False
            else:
                raise Exception("Error parsing ENGINEERED field of COMPND lines: '%s'." % molecule)

            if molecule.get('Mutation'):
                if molecule['Mutation'] != 'YES':
                    raise Exception("Error parsing MUTATION field of COMPND lines. Expected 'YES', got '%s'." % molecule['Mutation'])
                else:
                    molecule['Mutation'] = True
            else:
                molecule['Mutation'] = None

            # Add missing fields
            for k in COMPND_field_map.values():
                if k not in molecule.keys():
                    molecule[k] = None

            molecules[molecule['MoleculeID']] = molecule

        # Extract the SOURCE lines
        SOURCE_lines = []
        found_SOURCE_lines = False
        for line in self.lines:
            if not line.startswith("SOURCE"):
                if not found_SOURCE_lines:
                    continue
                else:
                    break
            else:
                found_SOURCE_lines = True
                SOURCE_lines.append(line)
        for x in range(1, len(SOURCE_lines)):
            assert(int(SOURCE_lines[x][7:10]) == x+1)

        if not SOURCE_lines:
            raise Exception("Do not raise this exception")
            return None

        # If the SOURCE lines exist, concatenate them together into one string
        SOURCE_lines = " ".join([line[10:].strip() for line in SOURCE_lines])
        SOURCE_lines.replace("  ", " ")

        # Split the SOURCE lines into seperate molecule entries
        MOL_DATA = ["MOL_ID:%s".strip() % s for s in SOURCE_lines.split('MOL_ID:') if s]
        # Parse the molecule entries
        for MD in MOL_DATA:
            MOL_fields = [s.strip() for s in MD.split(';') if s.strip()]
            new_molecule = {}
            for field in MOL_fields:
                print(field)
                field = field.split(":")
                if SOURCE_field_map.get(field[0].strip()):
                    field_name = SOURCE_field_map[field[0].strip()]
                    field_data = field[1].strip()
                    new_molecule[field_name] = field_data

            MoleculeID = int(new_molecule['MoleculeID'])
            print(molecules.keys())
            assert(MoleculeID in molecules)
            molecule = molecules[MoleculeID]

            for field_name, field_data in new_molecule.iteritems():
                if field_name != 'MoleculeID':
                    molecule[field_name] = field_data 

            # Normalize and type the fields

            if not molecule.get('Synthetic'):
                molecule['Synthetic'] = None
            elif molecule.get('Synthetic') == 'YES':
                molecule['Synthetic'] = True
            elif molecule.get('Synthetic') == 'NO':
                molecule['Synthetic'] = False
            else:
                raise Exception("Error parsing SYNTHETIC field of SOURCE lines: '%s'." % molecule)

            # Add missing fields
            for k in SOURCE_field_map.values():
                if k not in molecule.keys():
                    molecule[k] = None

        return [v for k, v in sorted(molecules.iteritems())]

    def GetATOMSequences(self, ConvertMSEToAtom = False, RemoveIncompleteFinalResidues = False, RemoveIncompleteResidues = False):
        sequences, residue_map = self.GetRosettaResidueMap(ConvertMSEToAtom = ConvertMSEToAtom, RemoveIncompleteFinalResidues = RemoveIncompleteFinalResidues, RemoveIncompleteResidues = RemoveIncompleteResidues)
        return sequences

    def GetRosettaResidueMap(self, ConvertMSEToAtom = False, RemoveIncompleteFinalResidues = False, RemoveIncompleteResidues = False):
        '''Note: This function ignores any DNA.'''
        chain = None
        sequences = {}
        residue_map = {}
        resid_set = set()
        resid_list = []

        DNA_residues = set([' DA', ' DC', ' DG', ' DT'])
        chains = []
        self.RAW_ATOM_SEQUENCE = []
        essential_atoms_1 = set(['CA', 'C', 'N'])#, 'O'])
        essential_atoms_2 = set(['CA', 'C', 'N'])#, 'OG'])
        current_atoms = set()
        atoms_read = {}
        oldchainID = None
        removed_residue = {}
        for line in self.lines:
            if line[0:4] == 'ATOM' or (ConvertMSEToAtom and (line[0:6] == 'HETATM') and (line[17:20] == 'MSE')):
                chainID = line[21]
                if chainID not in chains:
                    chains.append(chainID)
                residue_longname = line[17:20]
                if residue_longname in DNA_residues: 
                    # Skip DNA
                    continue
                if residue_longname == 'UNK':
                    # Skip unknown residues
                    continue
                if residue_longname not in residues and not(ConvertMSEToAtom and residue_longname == 'MSE'):
                    raise NonCanonicalResidueException("Residue %s encountered: %s" % (line[17:20], line))
                else:
                    resid = line[21:27]
                    #print(chainID, residue_longname, resid)
                    #print(line)
                    #print(resid_list)
                    if resid not in resid_set:
                        removed_residue[chainID] = False
                        add_residue = True
                        if current_atoms:
                            if RemoveIncompleteResidues and essential_atoms_1.intersection(current_atoms) != essential_atoms_1 and essential_atoms_2.intersection(current_atoms) != essential_atoms_2:
                                oldChain = resid_list[-1][0]
                                oldResidueID = resid_list[-1][1:]
                                print("The last residue '%s', %s, in chain %s is missing these atoms: %s." % (resid_list[-1], residue_longname, oldChain, essential_atoms_1.difference(current_atoms) or essential_atoms_2.difference(current_atoms)))
                                resid_set.remove(resid_list[-1])
                                #print("".join(resid_list))
                                resid_list = resid_list[:-1]
                                if oldchainID:
                                    removed_residue[oldchainID] = True
                                #print("".join(resid_list))
                                #print(sequences[oldChain])
                                if sequences.get(oldChain):
                                    sequences[oldChain] = sequences[oldChain][:-1]

                                if residue_map.get(oldChain):
                                    residue_map[oldChain] = residue_map[oldChain][:-1]

                                #print(sequences[oldChain]
                        else:
                            assert(not(resid_set))
                        current_atoms = set()
                        atoms_read[chainID] = set()
                        atoms_read[chainID].add(line[12:15].strip())
                        resid_set.add(resid)
                        resid_list.append(resid)
                        chainID = line[21]

                        sequences[chainID] = sequences.get(chainID, [])
                        if residue_longname in non_canonical_aa1:
                            sequences[chainID].append(non_canonical_aa1[residue_longname])
                        else:
                            sequences[chainID].append(aa1[residue_longname])

                        residue_map[chainID] = residue_map.get(chainID, [])
                        if residue_longname in non_canonical_aa1:
                            residue_map[chainID].append((resid, non_canonical_aa1[residue_longname]))
                        else:
                            residue_map[chainID].append((resid, aa1[residue_longname]))

                        oldchainID = chainID
                    else:
                        #atoms_read[chainID] = atoms_read.get(chainID, set())
                        atoms_read[chainID].add(line[12:15].strip())
                    current_atoms.add(line[12:15].strip())
        if RemoveIncompleteFinalResidues:
            # These are (probably) necessary for Rosetta to keep the residue. Rosetta does throw away residues where only the N atom is present if that residue is at the end of a chain.
            for chainID, sequence_list in sequences.iteritems():
                if not(removed_residue[chainID]):
                    if essential_atoms_1.intersection(atoms_read[chainID]) != essential_atoms_1 and essential_atoms_2.intersection(atoms_read[chainID]) != essential_atoms_2:
                        print("The last residue %s of chain %s is missing these atoms: %s." % (sequence_list[-1], chainID, essential_atoms_1.difference(atoms_read[chainID]) or essential_atoms_2.difference(atoms_read[chainID])))
                        oldResidueID = sequence_list[-1][1:]
                        residue_map[chainID] = residue_map[chainID][0:-1] 
                        sequences[chainID] = sequence_list[0:-1]


        for chainID, sequence_list in sequences.iteritems():
            sequences[chainID] = "".join(sequence_list)
            assert(sequences[chainID] == "".join([res_details[1] for res_details in residue_map[chainID]]))
        for chainID in chains:
            for a_acid in sequences.get(chainID, ""):
                self.RAW_ATOM_SEQUENCE.append((chainID, a_acid))

        residue_objects = {}
        for chainID in residue_map.keys():
            residue_objects[chainID] = []
        for chainID, residue_list in residue_map.iteritems():
            for res_pair in residue_list:
                resid = res_pair[0]
                resaa = res_pair[1]
                assert(resid[0] == chainID)
                residue_objects[chainID].append((resid[1:].strip(), resaa))

        return sequences, residue_objects

    def getJournal(self):
        if not self.journal:
            self.parseJRNL()
        return self.journal.getInfo()

    def parseJRNL(self):
        journal = []
        startedToRead = False 
        for line in self.lines:
            if line.startswith("JRNL  "):
                journal.append(line)
                startedToRead = True
            else:
                if startedToRead:
                    break	# early out
        self.journal = JRNL(journal)

    def read(self, pdbpath):

        pdbhandle = open(pdbpath)
        self.lines = pdbhandle.readlines()
        pdbhandle.close()

    def write(self, pdbpath, separator = '\n'):
        pdbhandle = open(pdbpath, "w")
        text = string.join(self.lines, separator)
        pdbhandle.write(text)
        pdbhandle.close()

    def remove_nonbackbone_atoms(self, resid_list):

        backbone_atoms = set(["N", "CA", "C", "O", "OXT"])

        resid_set = set(resid_list)

        self.lines = [line for line in self.lines if line[0:4] != "ATOM" or
                                                     line[21:26] not in resid_set or
                                                     line[12:16].strip() in backbone_atoms]

    @staticmethod
    def getOccupancy(line):
        ''' Handles the cases of missing occupancy by omission '''
        occstring = line[54:60]
        if not(occstring):
            return 0
        else:
            try:
                return float(occstring)
            except ValueError, TypeError:
                return 0                          

    def removeUnoccupied(self):
        self.lines = [line for line in self.lines if not (line.startswith("ATOM") and PDB.getOccupancy(line) == 0)]

    def fillUnoccupied(self):
        for i in xrange(len(self.lines)):
            line = self.lines[i]
            if line.startswith("ATOM") and PDB.getOccupancy(line) == 0:
                self.lines[i] = line[:54] + "  1.00" + line[60:]

    # Unused function
    def fix_backbone_occupancy(self):

        backbone_atoms = set(["N", "CA", "C", "O"])

        for i in xrange(len(self.lines)):
            line = self.lines[i]
            if line.startswith("ATOM") and line[12:16].strip() in backbone_atoms and PDB.getOccupancy(line) == 0:
                self.lines[i] = line[:54] + "  1.00" + line[60:]

    def fix_chain_id(self):
        """fill in missing chain identifier""" 

        for i in xrange(len(self.lines)):
            line = self.lines[i]
            if line.startswith("ATOM") and line[21] == ' ':
                self.lines[i] = line[:21] + 'A' + line[22:]


    def remove_hetatm(self):

        self.lines = [line for line in self.lines if not line.startswith("HETATM")]

    def get_ddGResmap(self):
        return self.ddGresmap

    def get_ddGInverseResmap(self):
        return self.ddGiresmap 

    def getAminoAcid(self, line):
        return line[17:20]

    def getAtomLine(self, chain, resid):
        '''This function assumes that all lines are ATOM or HETATM lines.
           resid should have the proper PDB format i.e. an integer left-padded
           to length 4 followed by the insertion code which may be a blank space.'''
        for line in self.lines:
            fieldtype = line[0:6].strip()
            assert(fieldtype == "ATOM" or fieldtype == "HETATM")
            if line[21:22] == chain and resid == line[22:27]:
                return line
        raise Exception("Could not find the ATOM/HETATM line corresponding to chain '%(chain)s' and residue '%(resid)s'." % vars())	

    def getAtomLinesForResidueInRosettaStructure(self, resid):
        '''We assume a Rosetta-generated structure where residues are uniquely identified by number.'''
        lines = [line for line in self.lines if line[0:4] == "ATOM" and resid == int(line[22:27])]
        if not lines:  
            #print('Failed searching for residue %d.' % resid)
            #print("".join([line for line in self.lines if line[0:4] == "ATOM"]))
            raise Exception("Could not find the ATOM/HETATM line corresponding to residue '%(resid)s'." % vars())
        return lines

    def remapMutations(self, mutations, pdbID = '?'):
        '''Takes in a list of (Chain, ResidueID, WildtypeAA, MutantAA) mutation tuples and returns the remapped
           mutations based on the ddGResmap (which must be previously instantiated).
           This function checks that the mutated positions exist and that the wild-type matches the PDB.
        '''
        remappedMutations = []
        ddGResmap = self.get_ddGResmap()
        for m in mutations:
            ns = (ChainResidueID2String(m[0], str(ddGResmap['ATOM-%s' % ChainResidueID2String(m[0], m[1])])))
            remappedMutations.append((ns[0], ns[1:].strip(), m[2], m[3])) 
        checkPDBAgainstMutations(pdbID, self, remappedMutations)
        return remappedMutations

    def stripForDDG(self, chains = True, keepHETATM = False, numberOfModels = None):
        '''Strips a PDB to ATOM lines. If keepHETATM is True then also retain HETATM lines.
           By default all PDB chains are kept. The chains parameter should be True or a list.
           In the latter case, only those chains in the list are kept.
           Unoccupied ATOM lines are discarded.
           This function also builds maps from PDB numbering to Rosetta numbering and vice versa.
           '''
        from Bio.PDB import PDBParser
        resmap = {}
        iresmap = {}
        newlines = []
        residx = 0
        oldres = None
        model_number = 1
        for line in self.lines:
            fieldtype = line[0:6].strip()
            if fieldtype == "ENDMDL":
                model_number += 1
                if numberOfModels and (model_number > numberOfModels):
                    break
                if not numberOfModels:
                    raise Exception("The logic here does not handle multiple models yet.")
            if (fieldtype == "ATOM" or (fieldtype == "HETATM" and keepHETATM)) and (float(line[54:60]) != 0):
                chain = line[21:22]
                if (chains == True) or (chain in chains): 
                    resid = line[21:27] # Chain, residue sequence number, insertion code
                    iCode = line[26:27]
                    if resid != oldres:
                        residx += 1
                        newnumbering = "%s%4.i " % (chain, residx)
                        assert(len(newnumbering) == 6)
                        id = fieldtype + "-" + resid
                        resmap[id] = residx 
                        iresmap[residx] = id 
                        oldres = resid
                    oldlength = len(line)
                    # Add the original line back including the chain [21] and inserting a blank for the insertion code
                    line = "%s%4.i %s" % (line[0:22], resmap[fieldtype + "-" + resid], line[27:])
                    assert(len(line) == oldlength)
                    newlines.append(line)
        self.lines = newlines
        self.ddGresmap = resmap
        self.ddGiresmap = iresmap

        # Sanity check against a known library
        tmpfile = "/tmp/ddgtemp.pdb"
        self.lines = self.lines or ["\n"] 	# necessary to avoid a crash in the Bio Python module 
        F = open(tmpfile,'w')
        F.write(string.join(self.lines, "\n"))
        F.close()
        parser=PDBParser()
        structure=parser.get_structure('tmp', tmpfile)
        os.remove(tmpfile)
        count = 0
        for residue in structure.get_residues():
            count += 1
        assert(count == residx)
        assert(len(resmap) == len(iresmap))

    def mapRosettaToPDB(self, resnumber):
        res = self.ddGiresmap.get(resnumber)
        if res:
            res = res.split("-")
            return res[1], res[0]
        return None

    def mapPDBToRosetta(self, chain, resnum, iCode = " ", ATOM = True):
        if ATOM:
            key = "ATOM-%s%4.i%s" % (chain, resnum, iCode) 
        else:
            key = "HETATM-%s%4.i%s" % (chain, resnum, iCode)
        res = self.ddGresmap.get(key)
        if res:
            return res
        return None


    def aa_resids(self, only_res=None):

        if only_res:
          atomlines = [line for line in self.lines if line[0:4] == "ATOM" and line[17:20] in residues and line[26] == ' ']
        else:  
          atomlines = [line for line in self.lines if line[0:4] == "ATOM" and (line[17:20] in residues or line[18:20] in nucleotides_dna or line[19:20] in nucleotides_rna ) and line[26] == ' ']

        resid_set = set()
        resid_list = []

        # todo: Seems a little expensive to create a set, check 'not in', and do fn calls to add to the set. Use a dict instead? 
        for line in atomlines:
            resid = line[21:26]
            if resid not in resid_set:
                resid_set.add(resid)
                resid_list.append(resid)

        return resid_list # format: "A 123" or: '%s%4.i' % (chain,resid)

    def ComputeBFactors(self):
        '''This reads in all ATOM lines and compute the mean and standard deviation of each
           residue's bfactors. It returns a table of the mean and standard deviation per
           residue as well as the mean and standard deviation over all residues with each
           residue having equal weighting.

           Whether the atom is occupied or not is not taken into account.'''

        # Read in the list of bfactors for each ATOM line.
        bfactors = {}
        old_residueID = None
        for line in self.lines:
            if line[0:4] == "ATOM":
                residueID = line[21:27]
                if residueID != old_residueID:
                    bfactors[residueID] = []
                    old_residueID = residueID
                bfactors[residueID].append(float(line[60:66]))

        # Compute the mean and standard deviation for the list of bfactors of each residue
        BFPerResidue = {}
        MeanPerResidue = []
        for residueID, bfactorlist in bfactors.iteritems():
            mean, stddev, variance = computeMeanAndStandardDeviation(bfactorlist)
            BFPerResidue[residueID] = (mean, stddev)
            MeanPerResidue.append(mean)
        TotalAverage, TotalStandardDeviation, variance = computeMeanAndStandardDeviation(MeanPerResidue)

        return {"_description" : "First tuple element is average, second is standard deviation",
                "Total"        : (TotalAverage, TotalStandardDeviation),
                "PerResidue"    : BFPerResidue}

    def CheckForPresenceOf(self, reslist):
        '''This checks whether residues in reslist exist in the ATOM lines. 
           It returns a list of the residues in reslist which did exist.'''
        if type(reslist) == type(""):
            reslist = [reslist]

        foundRes = {}
        for line in self.lines:
            resname = line[17:20]
            if line[0:4] == "ATOM":
                if resname in reslist:
                    foundRes[resname] = True

        return foundRes.keys()

    def ProperResidueIDToAAMap(self):
        '''This fixes the odd behaviour of aa_resid2type by including the insertion code.
           Returns a dictionary mapping residue IDs (Chain, residue number, insertion code) to the
           corresponding one-letter amino acid.'''

        resid2type = {}
        for line in self.lines:
            resname = line[17:20]
            if line[0:4] == "ATOM" and resname in residues and line[13:16] == 'CA ':
                resid2type[line[21:27]] = aa1[resname]
        return resid2type 


    def aa_resid2type(self):
        '''this creates a dictionary where the resid "A 123" is mapped to the one-letter aa type'''

        resid2type = {}

        for line in self.lines:
            resname = line[17:20]
            if line[0:4] == "ATOM" and resname in residues and line[26] == ' ' and line[13:16] == 'CA ':
                resid2type[line[21:26]] = aa1[resname]

        return resid2type # format: "A 123" or: '%s%4.i' % (chain,resid)    

    def pruneChains(self, chainsChosen):
        # If chainsChosen is non-empty then removes any ATOM lines of chains not in chainsChosen
        if chainsChosen and (sorted(chainsChosen) != sorted(self.chain_ids())):
            templines = []
            for line in self.lines:
                shortRecordName = line[0:4]
                if shortRecordName == "ATOM" and line[17:20] in residues and line[26] == ' ':
                    chain = line[21:22]
                    if chain in chainsChosen:
                        # Only keep ATOM lines for chosen chains
                        templines.append(line)
                elif shortRecordName == "TER ":
                    chain = line[21:22]
                    if chain in chainsChosen:
                        # Only keep TER lines for chosen chains
                        templines.append(line)
                else:
                    # Keep all non-ATOM lines
                    templines.append(line)
            self.lines = templines

    def chain_ids(self):
        chain_ids = set()
        chainlist = []
        for line in self.lines:
            if line[0:4] == "ATOM" and line[17:20] in residues and line[26] == ' ':
                chain = line[21:22]
                if chain not in chain_ids:
                    chain_ids.add(chain)
                    chainlist.append(chain)

        return chainlist

    def number_of_models(self):
        return len( [line for line in self.lines if line[0:4] == 'MODEL'] )


    def fix_residue_numbering(self):
        """this function renumbers the res ids in order to avoid strange behaviour of Rosetta"""

        resid_list = self.aa_resids()
        resid_set  = set(resid_list)
        resid_lst1 = list(resid_set)
        resid_lst1.sort()
        map_res_id = {}

        x = 1
        old_chain = resid_lst1[0][0]
        for resid in resid_lst1:
            map_res_id[resid] = resid[0] + '%4.i' % x
            if resid[0] == old_chain:
                x+=1
            else:
                x = 1
                old_chain = resid[0]

        atomlines = []
        for line in self.lines:
            if line[0:4] == "ATOM" and line[21:26] in resid_set and line[26] == ' ':
                lst = [char for char in line]
                #lst.remove('\n')
                lst[21:26] = map_res_id[line[21:26]]
                atomlines.append( string.join(lst,'') )
                #print string.join(lst,'')
            else:
                atomlines.append(line)

        self.lines = atomlines
        return map_res_id


    def get_residue_mapping(self):
        """this function maps the chain and res ids "A 234" to values from [1-N]"""

        resid_list = self.aa_resids()
        # resid_set  = set(resid_list)
        # resid_lst1 = list(resid_set)
        # resid_lst1.sort()
        map_res_id = {}

        x = 1
        for resid in resid_list:
            # map_res_id[ int(resid[1:].strip()) ] = x
            map_res_id[ resid ] = x
            x+=1
        return map_res_id

    def GetAllATOMLines(self):
        return [line for line in self.lines if line[0:4] == "ATOM"]

    def atomlines(self, resid_list = None):

        if resid_list == None:
            resid_list = self.aa_resids()

        resid_set = set(resid_list)

        return [line for line in self.lines if line[0:4] == "ATOM" and line[21:26] in resid_set and line[26] == ' ' ]


    def neighbors(self, distance, residue, atom = None, resid_list = None): #atom = " CA "

        if atom == None:     # consider all atoms
            lines = [line for line in self.atomlines(resid_list)]
        else:                # consider only given atoms
            lines = [line for line in self.atomlines(resid_list) if line[12:16] == atom]

        shash = spatialhash.SpatialHash(distance)

        #resid_pos = []

        for line in lines:
            pos = (float(line[30:38]), float(line[38:46]), float(line[46:54]))
            shash.insert(pos, line[21:26])

        neighbor_list = []        # (key, value) = (resid, 

        for line in lines:
            #print line
            resid = line[21:26]
            #print resid[1:-1], str(residue).rjust(4), resid[1:-1] == str(residue).rjust(4)
            if resid[1:] == str(residue).rjust(4):
                pos = (float(line[30:38]), float(line[38:46]), float(line[46:54]))
                for data in shash.nearby(pos, distance):
                    if data[1] not in neighbor_list:
                        #print data
                        neighbor_list.append(data[1])
                neighbor_list.sort()
        return neighbor_list


    #todo 29: Optimise all callers of this function by using fastneighbors2 instead
    def neighbors2(self, distance, chain_residue, atom = None, resid_list = None):  

        #atom = " CA "
        '''this one is more precise since it uses the chain identifier also'''

        if atom == None:     # consider all atoms
            lines = [line for line in self.atomlines(resid_list) if line[17:20] in residues]
        else:                # consider only given atoms
            lines = [line for line in self.atomlines(resid_list) if line[17:20] in residues and line[12:16] == atom]

        shash = spatialhash.SpatialHash(distance)

        for line in lines:
            pos = (float(line[30:38]), float(line[38:46]), float(line[46:54]))
            shash.insert(pos, line[21:26])

        neighbor_list = []
        for line in lines:
            resid = line[21:26]
            if resid == chain_residue:
                pos = (float(line[30:38]), float(line[38:46]), float(line[46:54]))

                for data in shash.nearby(pos, distance):
                    if data[1] not in neighbor_list:
                        neighbor_list.append(data[1])
                neighbor_list.sort()
        return neighbor_list

    def fastneighbors2(self, distance, chain_residues, atom = None, resid_list = None):  

        # Create the spatial hash and construct a list of positions matching chain_residue

        #chainResPositions holds all positions related to a chain residue (A1234) defined on ATOM lines
        chainResPositions = {}
        for res in chain_residues:
            chainResPositions[res] = []

        shash = spatialhash.SpatialHash3D(distance)

        # This could be made fast by inlining atomlines and avoiding creating line[21:26] twice and by reusing resids rather than recomputing them
        # However, the speedup may not be too great and would need profiling
        for line in self.atomlines(resid_list):
            if line[17:20] in residues:
                if atom == None or line[12:16] == atom:                    
                    resid = line[21:26]
                    pos = (float(line[30:38]), float(line[38:46]), float(line[46:54]))
                    shash.insert(pos, resid)
                    if resid in chain_residues:
                        chainResPositions[resid].append(pos)

        neighbors = {}
        # for all residues ids (A1234) in chain residues and all their positions,
        #   get a list of all ((x,y,z),resid) tuples within a radius of distance and add them uniquely to neighbor_list
        #   sort the list and store in neighbors
        for resid in chain_residues:
            neighbor_list = {}
            for pos in chainResPositions[resid]:               
                for data in shash.nearby(pos):
                    neighbor_list[data[1]] = True
            neighbors[resid] = neighbor_list.keys()

        return neighbors

    def neighbors3(self, distance, chain_residue, atom = None, resid_list = None):
      '''this is used by the sequence tolerance scripts to find the sc-sc interactions only'''

      backbone_atoms = [' N  ',' CA ',' C  ',' O  ']

      lines = [line for line in self.atomlines(resid_list) if line[12:16] not in backbone_atoms] # this excludes backbone atoms
      lines = [line for line in lines if line[13] != 'H'] # exclude hydrogens too!

      shash = spatialhash.SpatialHash(distance)

      #resid_pos = []

      for line in lines:
          pos = (float(line[30:38]), float(line[38:46]), float(line[46:54]))
          shash.insert(pos, line[21:26])

      neighbor_list = []        # 
      for line in lines:
          resid = line[21:26]
          if resid == chain_residue:
              pos = (float(line[30:38]), float(line[38:46]), float(line[46:54]))
              for data in shash.nearby(pos, distance):
                  if data[1] not in neighbor_list:
                      neighbor_list.append(data[1])
              neighbor_list.sort()
      return neighbor_list


    def get_stats(self):
      counts = {}
      counts["models"]   = self.number_of_models()
      counts["residues"] = len(self.aa_resids())
      counts["chains"]   = len(self.chain_ids())
      counts["atoms"]    = len(self.atomlines())
      counts["cys"]      = len([line for line in self.lines if line[0:4] == "ATOM" and line[13:16] == 'CA ' and line[17:20] == "CYS" and line[26] == ' '])

      return counts

    # This function can be expanded to allow us to use non-standard PDB files such as the ones given
    # as examples in the RosettaCon 2010 sequence tolerance protocol based on Smith, Kortemme 2010. 
    def check_custom_format(self, line, lineidx):
        if line[0:9] == "FOLD_TREE":
            return True
        return False          

    def check_format(self, usingClassic, ableToUseMini):
        warnings = []
        errors = []
        lineidx = 1
        # remove leading and trailing empty lines
        for line in self.lines:
            if len(line.strip()) == 0:
                self.lines.remove(line)
                lineidx = lineidx + 1
            else:
                break

        for line in reversed(self.lines):
            if len(line.strip()) == 0:
                self.lines.remove(line)
            else:
                break

        currentChain = None
        oldChain = None
        TERidx = 0
        ATOMidx = 0

        # Unused but handy to have for debugging
        residueNumber = 0

        # Variables for checking missing backbone residues
        missingBackboneResidues = False
        lastReadResidue = None
        currentResidue = None
        bbatoms = ["N", "O", "C", "CA"]#, "CB"]

        # For readability
        NOT_OCCUPIED = -1.0
        NINDEX = 0
        OINDEX = 1
        CINDEX = 2
        CAINDEX = 3
        #CBINDEX = 4
        missingSomeBBAtoms = False
        someBBAtomsAreUnoccupied = False
        backboneAtoms = {}
        backboneAtoms[" "] = [0.0, 0.0, 0.0, 0.0]#, 0.0]
        commonConformationIsPresent = False
        oldres = ""

        # Check for bad resfile input to classic
        resfileEntries = {}
        classicErrors = []

        # We add these dummy lines to avoid messy edge-case logic in the loop below.
        self.lines.append("ATOM   9999  N   VAL ^ 999       0.000   0.000   0.000  1.00 00.00           N")
        self.lines.append("ATOM   9999  CA  VAL ^ 999       0.000   0.000   0.000  1.00 00.00           C")
        self.lines.append("ATOM   9999  C   VAL ^ 999       0.000   0.000   0.000  1.00 00.00           C")
        self.lines.append("ATOM   9999  O   VAL ^ 999       0.000   0.000   0.000  1.00 00.00           O")
        #self.lines.append("ATOM   9999  CB  VAL ^ 999       0.000   0.000   0.000  1.00 00.00           C")

        for line in self.lines:

            if line[0:4] == "ATOM":
                # http://www.wwpdb.org/documentation/format32/sect9.html#ATOM
                alternateConformation = line[16]
                residue = line[17:20]
                currentChain = line[21]

                if currentChain == " ":
                    errors.append("Missing chain identifier (e.g. 'A', 'B') on line %d." % lineidx)

                currentResidue = line[21:27]
                classicCurrentResidue = line[21:26] # classic did not handle the insertion code in resfiles until revision 29386

                occupancy = PDB.getOccupancy(line)

                if usingClassic and (not allowedResidues.get(residue)):
                    # Check for residues outside the list classic can handle
                    classicErrors.append("Residue %s on line %d is not recognized by classic." % (residue, lineidx))
                elif (oldChain != None) and (currentChain == oldChain):
                    # Check for bad TER fields
                    oldChain = None    
                    errors.append("A TER field on line %d interrupts two ATOMS on lines %d and %d with the same chain %s." % (TERidx, ATOMidx, lineidx, currentChain))
                ATOMidx = lineidx

                if not lastReadResidue:
                    if currentResidue == '^ 999 ':
                        # We reached the end of the file
                        break
                    lastReadResidue = (residue, lineidx, currentResidue)

                if lastReadResidue[2] == currentResidue:
                    if alternateConformation == ' ':
                        commonConformationIsPresent = True
                if lastReadResidue[2] != currentResidue:
                    residueNumber += 1

                    # Check for malformed resfiles for classic
                    if usingClassic:
                        if not resfileEntries.get(classicCurrentResidue):
                            resfileEntries[classicCurrentResidue] = (currentResidue, lineidx)
                        else:
                            oldRes = resfileEntries[classicCurrentResidue][0]
                            oldLine = resfileEntries[classicCurrentResidue][1]
                            if currentResidue == resfileEntries[classicCurrentResidue][0]:
                                classicErrors.append("Residue %(currentResidue)s on line %(lineidx)d was already defined on line %(oldLine)d." % vars())
                            else:
                                classicErrors.append("Residue %(currentResidue)s on line %(lineidx)d has the same sequence number (ignoring iCode) as residue %(oldRes)s on line %(oldLine)d." % vars())

                    # Check for missing backbone residues
                    # Add the backbone atoms common to all alternative conformations to the common conformation
                    # todo: I've changed this to always take the union in all versions rather than just in Rosetta 3. This was to fix a false positive with 3OGB.pdb on residues A13 and A55 which run fine under point mutation.
                    #       This may now be too permissive. 
                    if True or not usingClassic:
                        commonToAllAlternatives = [0, 0, 0, 0]#, 0]
                        for conformation, bba in backboneAtoms.items():
                            for atomocc in range(CAINDEX + 1):
                                if conformation != " " and backboneAtoms[conformation][atomocc]:
                                    commonToAllAlternatives[atomocc] += backboneAtoms[conformation][atomocc]
                        for atomocc in range(CAINDEX + 1):
                            backboneAtoms[" "][atomocc] = backboneAtoms[" "][atomocc] or 0
                            backboneAtoms[" "][atomocc] += commonToAllAlternatives[atomocc]

                    # Check whether the common conformation has all atoms
                    commonConformationHasAllBBAtoms = True
                    for atomocc in range(CAINDEX + 1):
                        commonConformationHasAllBBAtoms = backboneAtoms[" "][atomocc] and commonConformationHasAllBBAtoms                            

                    ps = ""
                    for conformation, bba in backboneAtoms.items():

                        # Add the backbone atoms of the common conformation to all alternatives
                        if not usingClassic:
                            for atomocc in range(CAINDEX + 1):
                                if backboneAtoms[" "][atomocc]:
                                    backboneAtoms[conformation][atomocc] = backboneAtoms[conformation][atomocc] or 0
                                    backboneAtoms[conformation][atomocc] += backboneAtoms[" "][atomocc]

                        missingBBAtoms = False
                        for atomocc in range(CAINDEX + 1):
                            if not backboneAtoms[conformation][atomocc]:
                                missingBBAtoms = True
                                break

                        if not commonConformationHasAllBBAtoms and missingBBAtoms:
                            missing = []
                            unoccupied = []
                            for m in range(CAINDEX + 1):
                                if backboneAtoms[conformation][m] == 0:
                                    unoccupied.append(bbatoms[m])
                                    someBBAtomsAreUnoccupied = True
                                elif not(backboneAtoms[conformation][m]):
                                    missing.append(bbatoms[m])
                                    missingSomeBBAtoms = True
                            s1 = ""
                            s2 = ""
                            if len(missing) > 1:
                                s1 = "s"
                            if len(unoccupied) > 1:
                                s2 = "s"
                            missing = string.join(missing, ",")
                            unoccupied = string.join(unoccupied, ",")

                            failedClassic = False
                            haveAllAtoms = True
                            for atomocc in range(CAINDEX + 1):
                                if backboneAtoms[conformation][atomocc] <= 0 or backboneAtoms[" "][atomocc] <= 0:
                                    haveAllAtoms = False
                                    break
                            if haveAllAtoms:
                                failedClassic = True
                                ps = " The common conformation correctly has these atoms."

                            if conformation != " " or commonConformationIsPresent:
                                # We assume above that the common conformation exists. However, it is valid for it not to exist at all.
                                if conformation == " ":
                                    conformation = "common"

                                if missing:
                                    errstring = "The %s residue %s on line %d is missing the backbone atom%s %s in the %s conformation.%s" % (lastReadResidue[0], lastReadResidue[2], lastReadResidue[1], s1, missing, conformation, ps)
                                    if ps:
                                        classicErrors.append(errstring)
                                    else:
                                        errors.append(errstring)
                                if unoccupied:
                                    errstring = "The %s residue %s on line %d has the backbone atom%s %s set as unoccupied in the %s conformation.%s" % (lastReadResidue[0], lastReadResidue[2], lastReadResidue[1], s2, unoccupied, conformation, ps)
                                    if ps:
                                        classicErrors.append(errstring)
                                    else:
                                        errors.append(errstring)
                    backboneAtoms = {}
                    backboneAtoms[" "] = [None, None, None, None, None]
                    commonConformationIsPresent = False
                    lastReadResidue = (residue, lineidx, currentResidue)
                oldres = residue
                atom = line[12:16]
                backboneAtoms[alternateConformation] = backboneAtoms.get(alternateConformation) or [None, None, None, None, None]
                if occupancy >= 0:
                    if atom == ' N  ':
                        backboneAtoms[alternateConformation][NINDEX] = occupancy
                    elif atom == ' O  ' or atom == ' OT1' or atom == ' OT2':
                        backboneAtoms[alternateConformation][OINDEX] = occupancy
                    elif atom == ' C  ':
                        backboneAtoms[alternateConformation][CINDEX] = occupancy
                    elif atom == ' CA ':
                        backboneAtoms[alternateConformation][CAINDEX] = occupancy
                    #if atom == ' CB ' or residue == 'GLY':
                    #    backboneAtoms[alternateConformation][CBINDEX] = occupancy

            elif line[0:3] == "TER":
                oldChain = currentChain
                TERidx = lineidx            

            # print len(line),'\t', line[0:6]
            # remove all white spaces, and check if the line is empty or too long:

            if len(line.strip()) == 0:
                errors.append("Empty line found on line %d." % lineidx)
            elif len(line.rstrip()) > 81:
                errors.append("Line %d is too long." % lineidx)
            # check if the file contains tabs
            elif '\t' in line:
                errors.append("The file contains tabs on line %d." % lineidx)
            # check whether the records in the file are conform with the PDB format
            elif not line[0:6].rstrip() in records:
                if not self.check_custom_format(line, lineidx):
                    errors.append("Unknown record (%s) on line %d." % (line[0:6], lineidx))
                else:
                    warnings.append("The PDB file contains the following non-standard line which is allowed by the server:\n  line %d: %s" % (lineidx, line))
            lineidx = lineidx + 1

        # Remove the extra ATOM lines added above
        self.lines = self.lines[0:len(self.lines) - (CAINDEX + 1)]

        if not lastReadResidue:
            errors.append("No valid ATOM lines were found.")                

        if not missingSomeBBAtoms and someBBAtomsAreUnoccupied:
            errors.insert(0, "The PDB has some backbone atoms set as unoccupied. You can set these as occupied using the checkbox on the submission page.<br>")                

        if classicErrors:
            if ableToUseMini:
                errors.insert(0, "The PDB is incompatible with the classic version of Rosetta. Try using the mini version of Rosetta or else altering the PDB.<br>")
            else:
                errors.insert(0, "The PDB is incompatible with the classic version of Rosetta. No mini version is available for this protocol so the PDB will need to be altered.<br>")                
            errors.append("<br>The classic-specific errors are as follows:<ul style='text-align:left'>")
            errors.append("<li>%s" % string.join(classicErrors, "<li>"))
            errors.append("</ul>")

        if errors:
            if usingClassic:
                errors.insert(0, "Version: Rosetta++")
            else: 
                errors.insert(0, "Version: Rosetta 3") 

            return errors, None

        return True, warnings


if __name__ == "__main__":

    pdbobj = PDB(sys.argv[1])

    # print pdbobj.check_format()

    # print pdbobj.get_stats()
    d = float(sys.argv[2])

    all = []
    all.extend(pdbobj.neighbors3(d, 'A  26'))
    all.extend(pdbobj.neighbors3(d, 'A  44'))
    all.extend(pdbobj.neighbors3(d, 'A  48'))
    all.extend(pdbobj.neighbors3(d, 'A  64'))
    all.extend(pdbobj.neighbors3(d, 'A 157'))
    all.extend(pdbobj.neighbors3(d, 'A 163'))

    all.sort()
    new = []
    for x in all:
      if x not in new:
        new.append(x)
        print x


    print pdbobj.neighbors2(d, 'A  26')
    print pdbobj.neighbors2(d, 'A  44')
    print pdbobj.neighbors2(d, 'A  48')
    print pdbobj.neighbors2(d, 'A  64')
    print pdbobj.neighbors2(d, 'A 157')
    print pdbobj.neighbors2(d, 'A 163')
    # print pdbobj.aa_resid2type()

    # pdbobj.remove_hetatm()
    # #pdbobj.fix_chain_id()
    # 
    # pdbobj.fix_residue_numbering()
    # 
    # for line in pdbobj.atomlines():
    #     print line,
    # 
    # print pdbobj.chain_ids()

    #pdbobj.fix_chain_id()

    #import rosettaplusplus

    #rosetta = rosettaplusplus.RosettaPlusPlus(tempdir = "temp", auto_cleanup = False)

    #mutations = {}

    #for resid in pdbobj.aa_resids():
    #    mutations[resid] = "ALA"
    #    print resid

    #import chainsequence
    #seqs = chainsequence.ChainSequences()
    #chain_resnums = seqs.parse_atoms(pdbobj)
    #print chain_resnums

    #pdb_cb = rosetta.mutate(pdbobj, mutations)
    #for x in pdbobj.atomlines():
        #print x[21:26], x[26]

    #neighbors = pdbobj.neighbors(6.0, 225) #" CA ")

    #print neighbors
    #for key, value in neighbors.iteritems():
        #print key + ":", value
