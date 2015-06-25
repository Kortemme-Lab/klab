#!/usr/bin/python2.4


import re
import sys
import os
import types
import string
import types

from .basics import Residue, PDBResidue, Sequence, SequenceMap, residue_type_3to1_map, protonated_residue_type_3to1_map, non_canonical_amino_acids, protonated_residues_types_3, residue_types_3, Mutation, ChainMutation
from .basics import dna_nucleotides, rna_nucleotides, dna_nucleotides_3to1_map, dna_nucleotides_2to1_map, non_canonical_dna, non_canonical_rna, all_recognized_dna, all_recognized_rna
from .. import colortext
from ..fs.fsio import read_file, write_file
from ..pymath.stats import get_mean_and_standard_deviation
from ..pymath.cartesian import spatialhash
from ..rosetta.map_pdb_residues import get_pdb_contents_to_pose_residue_map
from . import rcsb
from ..general.strutil import remove_trailing_line_whitespace as normalize_pdb_file

# todo: related packages will need to be fixed since my refactoring
# The PDB constructor has now changed
#   it now only accepts the content of a PDB file
#   calling functions should use one of:
#       clone (copy lines from an existing object)
#       from_filepath (read a file from the disk and create a PDB object)
#       from_lines (use the list of PDB file lines to create a PDB object)
#       retrieve (new: read a PDB file from the RCSB or a cached copy and create a PDB object)
#
# - replace aa1 with basics.residue_type_3to1_map
# - replace relaxed_amino_acid_codes (a list) with basics.relaxed_residue_types_1 (a set)
# - replace amino_acid_codes (a list) with basics.residue_types_1 (a set)
# - replace non_canonical_aa1 with basics.non_canonical_amino_acids
# - replace residues with pdb.allowed_PDB_residues_types
# - replace nucleotides_dna_to_shorthand with basics.dna_nucleotides_2to1_map
# - replace nucleotides_dna and nucleotides_rna with basics.dna_nucleotides and rna_nucleotides respectively
# - The Residue class is now located in basics.py and renamed to PDBResidue (since we assert that the chain is 1 character long).
# - The Mutation class is now located in basics.py. ChainMutation was called something else.
# - computeMeanAndStandardDeviation was renamed to pymath.stats.get_mean_and_standard_deviation
# - computeMeanAndStandardDeviation was renamed to get_mean_and_standard_deviation
# - checkPDBAgainstMutations and checkPDBAgainstMutationsTuple have now been made into object functions
# - getSEQRESSequences is now _get_SEQRES_sequences and handles RNA properly. IT DOES NOT RETURN anything and is not a private function.
# - getMoleculeInfo is now get_molecules_and_source
# - ProperResidueIDToAAMap is now get_residue_id_to_type_map. The buggy aa_resid2type function has been deleted.
# - getJournal is now get_journal.  parseJRNL has been removed.
# - Calls to get_ATOM_and_HETATM_chains should be removed
# - the read function has been removed

### Residue types

allowed_PDB_residues_types = protonated_residues_types_3.union(residue_types_3)
allowed_PDB_residues_and_nucleotides = allowed_PDB_residues_types.union(dna_nucleotides).union(rna_nucleotides)

### Rosetta hacks

# Rosetta fails on some edge cases with certain residues. Since we rely on a lot of logic associated with this module (mappings between residues), it seems best to fix those here.
ROSETTA_HACKS_residues_to_remove = {
    '1A2P' : set(['B   3 ']), # terminal residue B 3 gets removed which triggers an exception "( anchor_rsd.is_polymer() && !anchor_rsd.is_upper_terminus() ) && ( new_rsd.is_polymer() && !new_rsd.is_lower_terminus() ), Exit from: src/core/conformation/Conformation.cc line: 449". This seems like a Rosetta deficiency.
    '1BAO' : set(['B   3 ']), # similar
    '1BNI' : set(['C   3 ']), # similar
    '1BRH' : set(['A   3 ', 'B   3 ', 'C   3 ']), # similar
    '1BRI' : set(['A   3 ', 'B   3 ']), # similar
    '1BRJ' : set(['A   3 ', 'B   3 ', 'C   3 ']), # similar
    '1BRK' : set(['B   3 ']), # similar
    '1EHK' : set(['B   3 ']), # similar
    '1ZNJ' : set(['B  30 ', 'F   1 ']), # similar
    '487D' : set(['N   1 ']),

}

# For use with get_pdb_contents_to_pose_residue_map e.g. {'1A2P' : ('-ignore_zero_occupancy false',), ... }
HACKS_pdb_specific_hacks = {
}

### UniProt-related variables

known_chimeras = set([
    ('1M7T', 'A'), # chimera of UniProtKB ACs P0AA25 (previously P00274) and P10599
    ])

maps_to_multiple_uniprot_ACs = set([('1Z1I', 'A'), ])

### PDB hacks

missing_chain_ids = {
    '2MBP' : 'A', # The FASTA file lists this as 'A' so we need to patch records up to match
}

### Whitelist for PDB files with ACE residues (we could allow all to pass but it may be good to manually look at each case)

cases_with_ACE_residues_we_can_ignore = set(['3UB5', '1TIN', '2ZTA', '5CPV', '1ATN', '1LFO', '1OVA', '3PGK', '2FAL', '2SOD', '1SPD', '1UOX', '1UNQ', '1DFJ', '1B39', '1HRC', '1PNE', '1WEJ', '2BNH'])


### Some PDB files have been deprecated but not replaced. Again, it may be good to manually look at each case.

obsolete_pdb_ids_with_no_replacement_entries = set(['1CMW'])


### Parsing-related variables

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

modified_residues_patch = {
    '1A2C' : {
        '34H' : 'UNK',
        #'TYS' : 'TYR',
#        'NA'  : 'UNK',
#        'HOH' : 'UNK',
    },
    '2ATC' : {
        'ASX' : 'ASN',
    },
    '1XY1' : {
        'MPT' : 'UNK',
    },
    '1CVW' : { # Note: more recent versions of this file do not require this patch
        'ANS' : 'UNK',
        '0QE' : 'UNK',
    },
    '1FAK' : {
        'CGU' : 'GLU', # Gamma-carboxy-glutamic acid
    },
    '1JXQ' : {
        'PHQ' : 'UNK', # benzyl chlorocarbonate
        'CF0' : 'UNK', # fluoromethane
    },
    '1YJ1' : {
        'DGN' : 'GLN', # D-glutamine
    },
    '2CN0' : {
        'SIN' : 'UNK', # Succinic acid
    },
    '2FTL' : {
        'IAS' : 'ASP', # Beta-L-aspartic acid/L-isoaspartate. Mismatch to asparagine - "the expected l-Asn residue had been replaced with a non-standard amino acid" (10.1016/j.jmb.2006.11.003).
    },

}

### Record types

# It looks like (Florian/Colin?) got this list from the Order of Records section, probably in an older version of the standard.
order_of_records = [
    "HEADER","OBSLTE","TITLE","SPLIT","CAVEAT","COMPND","SOURCE","KEYWDS",
    "EXPDTA","NUMMDL","MDLTYP","AUTHOR","REVDAT","SPRSDE","JRNL","REMARK",
    "DBREF","DBREF1","DBREF2","DBREF1/DBREF2","SEQADV","SEQRES","MODRES",
    "HET","HETNAM","HETSYN","FORMUL","HELIX","SHEET","SSBOND","LINK","CISPEP",
    "SITE","CRYST1","ORIGX1","ORIGX2","ORIGX3","SCALE1","SCALE2","SCALE3",
    "MTRIX1","MTRIX2","MTRIX3","MODEL","ATOM","ANISOU","TER","HETATM",
    "ENDMDL","CONECT","MASTER","END"
]
order_of_records = [x.ljust(6) for x in order_of_records]

# I added allowed_record_types from the Types of Records section of the PDB format documentation at http://www.wwpdb.org/documentation/format33/sect1.html
# It is missing the following set ['DBREF1', 'DBREF1/DBREF2', 'DBREF2', 'ORIGX1', 'ORIGX2', 'ORIGX3', 'SCALE1', 'SCALE2', 'SCALE3', 'MTRIX1', 'MTRIX2', 'MTRIX3']
# that order_of_records has. ORIGX1, SCALE1, MTRIX1 etc. have probably been replaced by the Coordinate Transformation Operator record types ['MTRIXn', 'SCALEn', 'ORIGXn']
# which allowed_record_types has but order_of_records does not.

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

# This set is probably safer to use to allow backwards compatibility
all_record_types = allowed_record_types.union(set(order_of_records))

### Deprecated
def checkPDBAgainstMutations(pdbID, pdb, mutations): raise Exception("This function has been moved inside the class")
def checkPDBAgainstMutationsTuple(pdbID, pdb, mutations): raise Exception("This function has been moved inside the class as validate_mutations")

### Exception classes
class PDBParsingException(Exception): pass
class MissingRecordsException(Exception): pass
class NonCanonicalResidueException(Exception): pass
class PDBValidationException(Exception): pass
class PDBMissingMainchainAtomsException(Exception): pass

class JRNL(object):

    def __init__(self, lines):
        if not lines:
            raise Exception("Could not parse JRNL: No lines to parse.")
        self.d = {}
        self.d["lines"] = lines
        self.parse_REF()
        self.parse_REFN()
        self.parse_DOI()

    def get_info(self):
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
                if type.strip():
                    raise Exception("Invalid type for REFN field (%s)" % type)
            if not type.strip():
                pass # e.g. 1BXI has a null reference
            else:
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


class PDB:
    """A class to store and manipulate PDB data"""

    ### Constructor ###

    def __init__(self, pdb_content, pdb_id = None, strict = True):
        '''Takes either a pdb file, a list of strings = lines of a pdb file, or another object.'''

        self.pdb_content = pdb_content
        if type(pdb_content) is types.StringType:
            self.lines =  pdb_content.split("\n")
        else:
            self.lines = [line.strip() for line in pdb_content]
        self.parsed_lines = {}
        self.structure_lines = []                       # For ATOM and HETATM records
        self.ddGresmap = None
        self.ddGiresmap = None
        self.journal = None
        self.chain_types = {}
        self.format_version = None
        self.modified_residues = None
        self.modified_residue_mapping_3 = {}
        self.pdb_id = None
        self.strict = strict
        
        self.seqres_chain_order = []                    # A list of the PDB chains in document-order of SEQRES records
        self.seqres_sequences = {}                      # A dict mapping chain IDs to SEQRES Sequence objects
        self.atom_chain_order = []                      # A list of the PDB chains in document-order of ATOM records (not necessarily the same as seqres_chain_order)
        self.atom_sequences = {}                        # A dict mapping chain IDs to ATOM Sequence objects
        self.chain_atoms = {}                           # A dict mapping chain IDs to a set of ATOM types. This is useful to test whether some chains only have CA entries e.g. in 1LRP, 1AIN, 1C53, 1HIO, 1XAS, 2TMA

        # PDB deprecation fields
        self.deprecation_date = None
        self.deprecated = False
        self.replacement_pdb_id = None

        self.rosetta_to_atom_sequence_maps = {}
        self.rosetta_residues = []

        self.fix_pdb()
        self._split_lines()
        self.pdb_id = pdb_id
        self.pdb_id = self.get_pdb_id()                 # parse the PDB ID if it is not passed in
        self._apply_hacks()
        self._get_pdb_format_version()
        self._get_modified_residues()
        self._get_replacement_pdb_id()
        if missing_chain_ids.get(self.pdb_id):
            self._update_structure_lines()
        self._get_SEQRES_sequences()
        self._get_ATOM_sequences()


    def fix_pdb(self):
        '''A function to fix fatal errors in PDB files when they can be automatically fixed. At present, this only runs if
           self.strict is False. We may want a separate property for this since we may want to keep strict mode but still
           allow PDBs to be fixed.

           The only fixes at the moment are for missing chain IDs which get filled in with a valid PDB ID, if possible.'''

        if self.strict:
            return

        # Get the list of chains
        chains = set()
        for l in self.lines:
            if l.startswith('ATOM  ') or l.startswith('HETATM'):
                chains.add(l[21])

        # If there is a chain with a blank ID, change that ID to a valid unused ID
        if ' ' in chains:
            fresh_id = None
            allowed_chain_ids = list(string.uppercase) + list(string.lowercase) + map(str, range(10))
            for c in chains:
                try: allowed_chain_ids.remove(c)
                except: pass
            if allowed_chain_ids:
                fresh_id = allowed_chain_ids[0]

            # Rewrite the lines
            new_lines = []
            if fresh_id:
                for l in self.lines:
                    if (l.startswith('ATOM  ') or l.startswith('HETATM')) and l[21] == ' ':
                        new_lines.append('%s%s%s' % (l[:21], fresh_id, l[22:]))
                    else:
                        new_lines.append(l)
                self.lines = new_lines


    def _apply_hacks(self):
        if self.pdb_id:
            pdb_id = self.pdb_id.upper()
            if pdb_id == '2MBP':
                newlines = []
                added_COMPND = False
                for l in self.lines:
                    if l.startswith('COMPND'):
                        if not added_COMPND:
                            newlines.append('COMPND    MOL_ID: 1;')
                            newlines.append('COMPND   2 MOLECULE: MALTODEXTRIN-BINDING PROTEIN;')
                            newlines.append('COMPND   3 CHAIN: A;')
                            newlines.append('COMPND   4 ENGINEERED: YES')
                            added_COMPND = True
                    elif l.startswith("ATOM  ") or l.startswith("HETATM") or l.startswith("TER"):
                        newlines.append('%s%s%s' % (l[0:21], 'A', l[22:]))
                    elif l.startswith("SEQRES"):
                        newlines.append('%s%s%s' % (l[0:12], 'A', l[13:]))
                    else:
                        newlines.append(l)
                self.lines = newlines
            elif ROSETTA_HACKS_residues_to_remove.get(pdb_id):
                hacks = ROSETTA_HACKS_residues_to_remove[pdb_id]
                self.lines = [l for l in self.lines if not(l.startswith('ATOM'  )) or (l[21:27] not in hacks)]

        self._split_lines()

    ### Class functions ###

    @staticmethod
    def from_filepath(filepath, strict = True):
        '''A function to replace the old constructor call where a filename was passed in.'''
        return PDB(read_file(filepath), strict = strict)

    @staticmethod
    def from_lines(pdb_file_lines, strict = True):
        '''A function to replace the old constructor call where a list of the file's lines was passed in.'''
        return PDB("\n".join(pdb_file_lines), strict = strict)

    @staticmethod
    def retrieve(pdb_id, cache_dir = None, strict = True):
        '''Creates a PDB object by using a cached copy of the file if it exists or by retrieving the file from the RCSB.'''

        # Check to see whether we have a cached copy
        pdb_id = pdb_id.upper()
        if cache_dir:
            filename = os.path.join(cache_dir, "%s.pdb" % pdb_id)
            if os.path.exists(filename):
                return PDB(read_file(filename), strict = strict)

        # Get a copy from the RCSB
        contents = rcsb.retrieve_pdb(pdb_id)

        # Create a cached copy if appropriate
        if cache_dir:
            write_file(os.path.join(cache_dir, "%s.pdb" % pdb_id), contents)

        # Return the object
        return PDB(contents, strict = strict)

    ### Private functions ###

    def _split_lines(self):
        '''Creates the parsed_lines dict which keeps all record data in document order indexed by the record type.'''
        parsed_lines = {}
        for rt in all_record_types:
            parsed_lines[rt] = []
        parsed_lines[0] = []

        for line in self.lines:
            linetype = line[0:6]
            if linetype in all_record_types:
                parsed_lines[linetype].append(line)
            else:
                parsed_lines[0].append(line)

        self.parsed_lines = parsed_lines
        self._update_structure_lines() # This does a second loop through the lines. We could do this logic above but I prefer a little performance hit for the cleaner code

    def _update_structure_lines(self):
        '''ATOM and HETATM lines may be altered by function calls. When this happens, this function should be called to keep self.structure_lines up to date.'''
        structure_lines = []
        atom_chain_order = []
        chain_atoms = {}

        for line in self.lines:
            linetype = line[0:6]
            if linetype == 'ATOM  ' or linetype == 'HETATM' or linetype == 'TER   ':
                chain_id = line[21]
                if missing_chain_ids.get(self.pdb_id):
                    chain_id = missing_chain_ids[self.pdb_id]
                structure_lines.append(line)
                if (chain_id not in atom_chain_order) and (chain_id != ' '):
                    atom_chain_order.append(chain_id)
                if linetype == 'ATOM  ':
                    atom_type = line[12:16].strip()
                    if atom_type:
                        chain_atoms[chain_id] = chain_atoms.get(chain_id, set())
                        chain_atoms[chain_id].add(atom_type)
            if linetype == 'ENDMDL':
                colortext.warning("ENDMDL detected: Breaking out early. We do not currently handle NMR structures properly.")
                break

        self.structure_lines = structure_lines
        self.atom_chain_order = atom_chain_order
        self.chain_atoms = chain_atoms

    ### Basic functions ###

    def clone(self):
        '''A function to replace the old constructor call where a PDB object was passed in and 'cloned'.'''
        return PDB("\n".join(self.lines), pdb_id = self.pdb_id, strict = self.strict)

    def get_content(self):
        '''A function to replace the old constructor call where a PDB object was passed in and 'cloned'.'''
        return '\n'.join(self.lines)

    def write(self, pdbpath, separator = '\n'):
        write_file(pdbpath, separator.join(self.lines))

    def get_pdb_id(self):
        '''Return the PDB ID. If one was passed in to the constructor, this takes precedence, otherwise the header is
           parsed to try to find an ID. The header does not always contain a PDB ID in regular PDB files and appears to
           always have an ID of 'XXXX' in biological units so the constructor override is useful.'''
        if self.pdb_id:
            return self.pdb_id
        else:
            header = self.parsed_lines["HEADER"]
            assert(len(header) <= 1)
            if header:
                self.pdb_id = header[0][62:66]
                return self.pdb_id
        return None

    def get_ATOM_and_HETATM_chains(self):
        '''todo: remove this function as it now just returns a member element'''
        return self.atom_chain_order

    def get_annotated_chain_sequence_string(self, chain_id, use_seqres_sequences_if_possible, raise_Exception_if_not_found = True):
        '''A helper function to return the Sequence for a chain. If use_seqres_sequences_if_possible then we return the SEQRES
           Sequence if it exists. We return a tuple of values, the first identifying which sequence was returned.'''
        if use_seqres_sequences_if_possible and self.seqres_sequences and self.seqres_sequences.get(chain_id):
            return ('SEQRES', self.seqres_sequences[chain_id])
        elif self.atom_sequences.get(chain_id):
            return ('ATOM', self.atom_sequences[chain_id])
        elif raise_Exception_if_not_found:
            raise Exception('Error: Chain %s expected but not found.' % (str(chain_id)))
        else:
            return None

    def get_chain_sequence_string(self, chain_id, use_seqres_sequences_if_possible, raise_Exception_if_not_found = True):
        '''Similar to get_annotated_chain_sequence_string except that we only return the Sequence and do not state which sequence it was.'''
        chain_pair = self.get_annotated_chain_sequence_string(chain_id, use_seqres_sequences_if_possible, raise_Exception_if_not_found = raise_Exception_if_not_found)
        if chain_pair:
            return chain_pair[1]
        return None

    def _get_modified_residues(self):
        if not self.modified_residues:
            modified_residues = {}
            modified_residue_mapping_3 = {}

            # Add in the patch
            for k, v in modified_residues_patch.get(self.pdb_id, {}).iteritems():
                modified_residue_mapping_3[k] = v

            for line in self.parsed_lines["MODRES"]:
                restype = line[24:27].strip()
                restype_1 = residue_type_3to1_map.get(restype) or dna_nucleotides_2to1_map.get(restype)
                if not restype_1:
                    assert(restype in rna_nucleotides)
                    restype_1 = restype

                modified_residues["%s%s" % (line[16], line[18:23])] = {'modified_residue' : line[12:15], 'original_residue_3' : restype, 'original_residue_1' : restype_1}
                modified_residue_mapping_3[line[12:15]] = restype

            self.modified_residue_mapping_3 = modified_residue_mapping_3
            self.modified_residues = modified_residues


    def _get_replacement_pdb_id(self):
        '''Checks to see if the PDB file has been deprecated and, if so, what the new ID is.'''
        deprecation_lines = self.parsed_lines['OBSLTE']
        date_regex = re.compile('(\d+)-(\w{3})-(\d+)')
        if deprecation_lines:
            assert(len(deprecation_lines) == 1)
            tokens = deprecation_lines[0].split()[1:]
            if tokens[1].upper() in obsolete_pdb_ids_with_no_replacement_entries:
                assert(len(tokens) == 2)
            else:
                assert(len(tokens) == 3)
            if self.pdb_id:
                mtchs = date_regex.match(tokens[0])
                assert(mtchs)
                _day = int(mtchs.group(1))
                _month = mtchs.group(2)
                _year = int(mtchs.group(3)) # only two characters?
                assert(tokens[1] == self.pdb_id)
                self.deprecation_date = (_day, _month, _year) # no need to do anything fancier unless this is ever needed
                self.deprecated = True
                if len(tokens) == 3:
                    assert(len(tokens[2]) == 4)
                    self.replacement_pdb_id = tokens[2]

    ### PDB mutating functions ###

    def strip_to_chains(self, chains):
        '''Throw away all ATOM/HETATM/ANISOU/TER lines for chains that are not in the chains list.'''
        if chains:
            chains = set(chains)

            # Remove any structure lines associated with the chains
            self.lines = [l for l in self.lines if not(l.startswith('ATOM  ') or l.startswith('HETATM') or l.startswith('ANISOU') or l.startswith('TER')) or l[21] in chains]
            self._update_structure_lines()
            # todo: this logic should be fine if no other member elements rely on these lines e.g. residue mappings otherwise we need to update those elements here
        else:
            raise Exception('The chains argument needs to be supplied.')

    def strip_HETATMs(self, only_strip_these_chains = []):
        '''Throw away all HETATM lines. If only_strip_these_chains is specified then only strip HETATMs lines for those chains.'''
        if only_strip_these_chains:
            self.lines = [l for l in self.lines if not(l.startswith('HETATM')) or l[21] not in only_strip_these_chains]
        else:
            self.lines = [l for l in self.lines if not(l.startswith('HETATM'))]
        self._update_structure_lines()
        # todo: this logic should be fine if no other member elements rely on these lines e.g. residue mappings otherwise we need to update those elements here

    def generate_all_point_mutations_for_chain(self, chain_id):
        mutations = []
        if self.atom_sequences.get(chain_id):
            aas = sorted(residue_type_3to1_map.values())
            aas.remove('X')
            seq = self.atom_sequences[chain_id]
            for res_id in seq.order:
                r = seq.sequence[res_id]
                assert(chain_id == r.Chain)
                for mut_aa in aas:
                    if mut_aa != r.ResidueAA:
                        mutations.append(ChainMutation(r.ResidueAA, r.ResidueID, mut_aa, Chain = chain_id))
        return mutations

    ### FASTA functions ###


    def create_fasta(self, length = 80, prefer_seqres_order = True):
        fasta_string = ''
        if prefer_seqres_order:
            chain_order, sequences = self.seqres_chain_order or self.atom_chain_order, self.seqres_sequences or self.atom_sequences
        else:
            chain_order, sequences = self.atom_chain_order or self.seqres_chain_order, self.atom_sequences or self.seqres_sequences

        for c in chain_order:
            if c not in sequences:
                continue
            
            fasta_string += '>%s|%s|PDBID|CHAIN|SEQUENCE\n' % (self.pdb_id, c)
            seq = str(sequences[c])
            for line in [seq[x:x+length] for x in xrange(0, len(seq), length)]:
                fasta_string += line + '\n'

        return fasta_string


    ### PDB file parsing functions ###

    def _get_pdb_format_version(self):
        '''Remark 4 indicates the version of the PDB File Format used to generate the file.'''
        if not self.format_version:
            version = None
            version_lines = None
            try:
                version_lines = [line for line in self.parsed_lines['REMARK'] if int(line[7:10]) == 4 and line[10:].strip()]
            except: pass
            if version_lines:
                assert(len(version_lines) == 1)
                version_line = version_lines[0]
                version_regex = re.compile('.*?FORMAT V.(.*),')
                mtch = version_regex.match(version_line)
                if mtch and mtch.groups(0):
                    try:
                        version = float(mtch.groups(0)[0])
                    except:
                        pass
            self.format_version = version

    def get_resolution(self):
        resolution = None
        resolution_lines_exist = False
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
                resolution_lines_exist = True
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
        if resolution_lines_exist and not resolution:
            raise PDBParsingException("Could not determine resolution.")
        return resolution

    def get_title(self):
        if self.parsed_lines.get("TITLE "):
            return " ".join([line[10:80].strip() for line in self.parsed_lines["TITLE "] if line[10:80].strip()])
        return None

    def get_techniques(self):
        techniques = None
        technique_lines_exist = False
        for line in self.parsed_lines["EXPDTA"]:
            technique_lines_exist = True
            techniques = line[10:71].split(";")
            for k in range(len(techniques)):
                techniques[k] = techniques[k].strip()
            techniques = ";".join(techniques)
        if technique_lines_exist and not techniques:
            raise PDBParsingException("Could not determine techniques used.")
        return techniques

    def get_UniProt_ACs(self):
        return [v['dbAccession'] for k, v in self.get_DB_references().get(self.pdb_id, {}).get('UNIPROT', {}).iteritems()]

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

        DBref = {}
        for l in self.parsed_lines["DBREF "]: # [l for l in self.lines if l.startswith('DBREF')]
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

    def get_molecules_and_source(self):
        # Check the COMPND lines
        COMPND_lines = self.parsed_lines["COMPND"]
        for x in range(1, len(COMPND_lines)):
            assert(int(COMPND_lines[x][7:10]) == x+1)
        if not COMPND_lines:
            raise MissingRecordsException("No COMPND records were found. Handle this gracefully.")

        # Concatenate the COMPND lines into one string, removing double spaces
        COMPND_lines = " ".join([line[10:].strip() for line in COMPND_lines])
        COMPND_lines.replace("  ", " ")

        # Split the COMPND lines into separate molecule entries
        molecules = {}
        MOL_DATA = ["MOL_ID:%s".strip() % s for s in COMPND_lines.split('MOL_ID:') if s]

        # Parse the molecule entries
        # The hacks below are due to some PDBs breaking the grammar by not following the standard which states:
        #   Specification: A String composed of a token and its associated value separated by a colon.
        #   Specification List: A sequence of Specifications, separated by semi-colons.
        # COMPND records are a specification list so semi-colons should not appear inside entries.
        # The hacks below could probably be removed if I assumed that the standard was not followed (valid) by
        #   e.g. splitting the COMPND data by allowed tokens (the keys of COMPND_field_map)
        # but I would want lots of tests in place first.
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
            # Hack for 1JRH
            MD = MD.replace('FAB FRAGMENT;PEPSIN DIGESTION OF INTACT ANTIBODY', 'FAB FRAGMENT,PEPSIN DIGESTION OF INTACT ANTIBODY')
            # Hack for 1KJ1
            MD = MD.replace('SYNONYM: MANNOSE-SPECIFIC AGGLUTININ; LECGNA ', 'SYNONYM: MANNOSE-SPECIFIC AGGLUTININ, LECGNA ')
            # Hack for 1OCC - The Dean and I
            MD = MD.replace('SYNONYM: FERROCYTOCHROME C\:OXYGEN OXIDOREDUCTASE', 'SYNONYM: FERROCYTOCHROME C, OXYGEN OXIDOREDUCTASE')
            # Hack for 2AKY
            MD = MD.replace('SYNONYM: ATP\:AMP PHOSPHOTRANSFERASE, MYOKINASE', 'SYNONYM: ATP, AMP PHOSPHOTRANSFERASE, MYOKINASE')
            # Hack for 3BCI
            MD = MD.replace('SYNONYM: THIOL:DISULFIDE OXIDOREDUCTASE DSBA', 'SYNONYM: THIOL, DISULFIDE OXIDOREDUCTASE DSBA')
            # Hack for 3BCI
            MD = MD.replace('SYNONYM: THIOL:DISULFIDE OXIDOREDUCTASE DSBA', 'SYNONYM: THIOL, DISULFIDE OXIDOREDUCTASE DSBA')
            # Hack for 1ELV
            MD = MD.replace('FRAGMENT: CCP2-SP CATALYTIC FRAGMENT: ASP363-ASP-673 SEGMENT PRECEDED BY AN ASP-LEU SEQUENCE ADDED AT THE N-TERMINAL END',
                            'FRAGMENT: CCP2-SP CATALYTIC FRAGMENT; ASP363-ASP-673 SEGMENT PRECEDED BY AN ASP-LEU SEQUENCE ADDED AT THE N-TERMINAL END')
            # Hack for 1E6E
            MD = MD.replace('MOLECULE: NADPH\:ADRENODOXIN OXIDOREDUCTASE;', 'MOLECULE: NADPH;ADRENODOXIN OXIDOREDUCTASE;')
            # Hack for 1JZD
            MD = MD.replace('MOLECULE: THIOL:DISULFIDE INTERCHANGE PROTEIN', 'MOLECULE: THIOL;DISULFIDE INTERCHANGE PROTEIN')
            # Hack for 1N2C
            MD = MD.replace('OTHER_DETAILS: 2\:1 COMPLEX OF HOMODIMERIC FE-PROTEIN', 'OTHER_DETAILS: 2;1 COMPLEX OF HOMODIMERIC FE-PROTEIN')
            # Hack for 1S6P
            MD = MD.replace('MOLECULE: POL POLYPROTEIN [CONTAINS: REVERSE TRANSCRIPTASE]', 'MOLECULE: POL POLYPROTEIN [CONTAINS; REVERSE TRANSCRIPTASE]')
            # Hack for 1Z9E
            MD = MD.replace('FRAGMENT: SEQUENCE DATABASE RESIDUES 347-471 CONTAINS: HIV- 1 INTEGRASE-BINDING DOMAIN', 'FRAGMENT: SEQUENCE DATABASE RESIDUES 347-471 CONTAINS; HIV- 1 INTEGRASE-BINDING DOMAIN')
            # Hacks for 2GOX
            MD = MD.replace('FRAGMENT: FRAGMENT OF ALPHA CHAIN: RESIDUES 996-1287;', 'FRAGMENT: FRAGMENT OF ALPHA CHAIN; RESIDUES 996-1287;')
            MD = MD.replace('FRAGMENT: C-TERMINAL DOMAIN: RESIDUES 101-165;', 'FRAGMENT: C-TERMINAL DOMAIN; RESIDUES 101-165;')

            MOL_fields = [s.strip() for s in MD.split(';') if s.strip()]

            molecule = {}
            for field in MOL_fields:
                field = field.split(":")
                if not(1 <= len(field) <= 2):
                    print(MD, field)
                assert(1 <= len(field) <= 2)
                if len(field) == 2: # Hack for 1MBG - missing field value
                    field_name = COMPND_field_map[field[0].strip()]
                    field_data = field[1].strip()
                    molecule[field_name] = field_data

            ### Normalize and type the fields ###

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
                raise PDBParsingException("Error parsing ENGINEERED field of COMPND lines. Expected 'YES' or 'NO', got '%s'." % molecule['Engineered'])

            if molecule.get('Mutation'):
                if molecule['Mutation'] != 'YES':
                    raise PDBParsingException("Error parsing MUTATION field of COMPND lines. Expected 'YES', got '%s'." % molecule['Mutation'])
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
        SOURCE_lines = self.parsed_lines["SOURCE"]
        for x in range(1, len(SOURCE_lines)):
            assert(int(SOURCE_lines[x][7:10]) == x+1)
        if not SOURCE_lines:
            raise MissingRecordsException("No SOURCE records were found. Handle this gracefully.")

        # Concatenate the SOURCE lines into one string, removing double spaces
        SOURCE_lines = " ".join([line[10:].strip() for line in SOURCE_lines])
        SOURCE_lines.replace("  ", " ")

        # Split the SOURCE lines into separate molecule entries
        MOL_DATA = ["MOL_ID:%s".strip() % s for s in SOURCE_lines.split('MOL_ID:') if s]
        # Parse the molecule entries
        for MD in MOL_DATA:
            MOL_fields = [s.strip() for s in MD.split(';') if s.strip()]
            new_molecule = {}
            for field in MOL_fields:
                field = field.split(":")
                if SOURCE_field_map.get(field[0].strip()):
                    field_name = SOURCE_field_map[field[0].strip()]
                    field_data = field[1].strip()
                    new_molecule[field_name] = field_data

            MoleculeID = int(new_molecule['MoleculeID'])
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
                raise PDBParsingException("Error parsing SYNTHETIC field of SOURCE lines. Expected 'YES' or 'NO', got '%s'." % molecule['Synthetic'])

            # Add missing fields
            for k in SOURCE_field_map.values():
                if k not in molecule.keys():
                    molecule[k] = None

        return [v for k, v in sorted(molecules.iteritems())]

    def get_journal(self):
        if self.parsed_lines["JRNL  "]:
            if not self.journal:
                self.journal = JRNL(self.parsed_lines["JRNL  "])
            return self.journal.get_info()
        return None

    ### Sequence-related functions ###

    def _get_SEQRES_sequences(self):
        '''Creates the SEQRES Sequences and stores the chains in order of their appearance in the SEQRES records. This order of chains
           in the SEQRES sequences does not always agree with the order in the ATOM records.'''

        pdb_id = self.get_pdb_id()
        SEQRES_lines = self.parsed_lines["SEQRES"]

        modified_residue_mapping_3 = self.modified_residue_mapping_3
        # I commented this out since we do not need it for my current test cases
        #for k, v in self.modified_residues.iteritems():
        #    assert(v['modified_residue'] not in modified_residues)
        #    modified_residues[v['modified_residue']] = v['original_residue_3']

        for x in range(0, len(SEQRES_lines)):
            assert(SEQRES_lines[x][7:10].strip().isdigit())

        if not SEQRES_lines:
            #colortext.warning("WARNING: No SEQRES records were found. Kyle is trying to handle this gracefully, but Shane may need to fix it")
            return

        seqres_chain_order = []
        SEQRES_lines = [line[11:].rstrip() for line in SEQRES_lines] # we cannot strip the left characters as some cases e.g. 2MBP are missing chain identifiers

        # Collect all residues for all chains, remembering the chain order
        chain_tokens = {}
        for line in SEQRES_lines:
            chainID = line[0]
            if missing_chain_ids.get(self.pdb_id):
                chainID = missing_chain_ids[self.pdb_id]
            if chainID not in seqres_chain_order:
                seqres_chain_order.append(chainID)
            chain_tokens[chainID] = chain_tokens.get(chainID, [])
            chain_tokens[chainID].extend(line[6:].strip().split())

        sequences = {}
        self.chain_types = {}

        for chain_id, tokens in chain_tokens.iteritems():

            # Determine whether the chain is DNA, RNA, or a protein chain
            # 1H38 is a good test for this - it contains DNA (chains E and G and repeated by H, K, N, J, M, P), RNA (chain F, repeated by I, L, O) and protein (chain D, repeated by A,B,C) sequences
            # 1ZC8 is similar but also has examples of DU
            # 4IHY has examples of DI (I is inosine)
            # 2GRB has RNA examples of I and U
            # 1LRP has protein chains with only CA atoms
            # This will throw an exception when a non-canonical is found which is not listed in basics.py. In that case, the list in basics.py should be updated.

            chain_type = None
            set_of_tokens = set(tokens)
            if (set(tokens).union(all_recognized_dna) == all_recognized_dna):# or (len(set_of_tokens) <= 5 and len(set_of_tokens.union(dna_nucleotides)) == len(set_of_tokens) + 1): # allow one unknown DNA residue
                chain_type = 'DNA'
            elif (set(tokens).union(all_recognized_rna) == all_recognized_rna):# or (len(set_of_tokens) <= 5 and len(set_of_tokens.union(dna_nucleotides)) == len(set_of_tokens) + 1): # allow one unknown DNA residue
                chain_type = 'RNA'
            else:
                assert(len(set(tokens).intersection(dna_nucleotides)) == 0)
                assert(len(set(tokens).intersection(rna_nucleotides)) == 0)
                chain_type = 'Protein'
                if not self.chain_atoms.get(chain_id):
                    # possible for biological unit files
                    continue
                if self.chain_atoms[chain_id] == set(['CA']):
                    chain_type = 'Protein skeleton'

            # Get the sequence, mapping non-canonicals to the appropriate letter
            self.chain_types[chain_id] = chain_type
            sequence = []
            if chain_type == 'DNA':
                for r in tokens:
                    if dna_nucleotides_2to1_map.get(r):
                        sequence.append(dna_nucleotides_2to1_map[r])
                    else:
                        if non_canonical_dna.get(r):
                            sequence.append(non_canonical_dna[r])
                        else:
                            raise Exception("Unknown DNA residue %s." % r)
            elif chain_type == 'RNA':
                for r in tokens:
                    if r in rna_nucleotides:
                        sequence.append(r)
                    else:
                        if non_canonical_rna.get(r):
                            sequence.append(non_canonical_rna[r])
                        else:
                            raise Exception("Unknown RNA residue %s." % r)
            else:
                token_counter = 0
                for r in tokens:
                    token_counter += 1
                    if residue_type_3to1_map.get(r):
                        sequence.append(residue_type_3to1_map[r])
                    else:

                        if self.modified_residue_mapping_3.get(r):
                            sequence.append(residue_type_3to1_map[self.modified_residue_mapping_3.get(r)])
                        elif non_canonical_amino_acids.get(r):
                            #print('Mapping non-canonical residue %s to %s.' % (r, non_canonical_amino_acids[r]))
                            #print(SEQRES_lines)
                            #print(line)
                            sequence.append(non_canonical_amino_acids[r])
                        elif r == 'UNK':
                            continue
                        # Skip these residues
                        elif r == 'ACE' and token_counter == 1:
                            # Always allow ACE as the first residue of a chain
                            sequence.append('X')
                        elif r == 'ACE' and pdb_id in cases_with_ACE_residues_we_can_ignore:
                            sequence.append('X')
                            #continue
                        # End of skipped residues
                        else:
                            #print(modified_residue_mapping_3)
                            if modified_residue_mapping_3.get(r):
                                if modified_residue_mapping_3[r] == 'UNK':
                                    sequence.append('X')
                                else:
                                    assert(modified_residue_mapping_3[r] in residue_types_3)
                                    sequence.append(residue_type_3to1_map[modified_residue_mapping_3[r]])
                            else:
                                raise Exception("Unknown protein residue %s in chain %s." % (r, chain_id))
            sequences[chain_id] = "".join(sequence)

        self.seqres_chain_order = seqres_chain_order

        # Create Sequence objects for the SEQRES sequences
        for chain_id, sequence in sequences.iteritems():
            self.seqres_sequences[chain_id] = Sequence.from_sequence(chain_id, sequence, self.chain_types[chain_id])


    def _get_ATOM_sequences(self):
        '''Creates the ATOM Sequences.'''

        # Get a list of all residues with ATOM or HETATM records
        atom_sequences = {}
        structural_residue_IDs_set = set() # use a set for a quicker lookup
        ignore_HETATMs = True # todo: fix this if we need to deal with HETATMs

        residue_lines_by_chain = []
        structural_residue_IDs_set = []

        model_index = 0
        residue_lines_by_chain.append([])
        structural_residue_IDs_set.append(set())
        full_code_map = {}
        for l in self.structure_lines:
            if l.startswith("TER   "):
                model_index += 1
                residue_lines_by_chain.append([])
                structural_residue_IDs_set.append(set())
            else:
                residue_id = l[21:27]
                if residue_id not in structural_residue_IDs_set[model_index]:
                    residue_lines_by_chain[model_index].append(l)
                    structural_residue_IDs_set[model_index].add(residue_id)
                full_code_map[l[21]] = full_code_map.get(l[21], set())
                full_code_map[l[21]].add(l[17:20].strip())

        # Get the residues used by the residue lines. These can be used to determine the chain type if the header is missing.
        for chain_id in self.atom_chain_order:
            if full_code_map.get(chain_id):
                # The chains may contain other molecules e.g. MG or HOH so before we decide their type based on residue types alone,
                # we subtract out those non-canonicals
                canonical_molecules = full_code_map[chain_id].intersection(dna_nucleotides.union(rna_nucleotides).union(residue_types_3))
                if canonical_molecules.union(dna_nucleotides) == dna_nucleotides:
                    self.chain_types[chain_id] = 'DNA'
                elif canonical_molecules.union(rna_nucleotides) == rna_nucleotides:
                    self.chain_types[chain_id] = 'RNA'
                else:
                    self.chain_types[chain_id] = 'Protein'

        line_types_by_chain = []
        chain_ids = []
        for model_index in range(len(residue_lines_by_chain)):
            line_types = set()
            if residue_lines_by_chain[model_index]:
                if missing_chain_ids.get(self.pdb_id):
                    chain_ids.append(missing_chain_ids[self.pdb_id])
                else:
                    chain_ids.append(residue_lines_by_chain[model_index][0][21])
            for l in residue_lines_by_chain[model_index]:
                line_types.add(l[0:6])
            if line_types == set(['ATOM']):
                line_types_by_chain.append('ATOM')
            elif line_types == set(['HETATM']):
                line_types_by_chain.append('HETATM')
            else:
                line_types_by_chain.append('Mixed')

        for x in range(0, len(residue_lines_by_chain)):
            residue_lines = residue_lines_by_chain[x]
            line_types = line_types_by_chain[x]
            if ignore_HETATMs and line_types == 'HETATM':
                continue

            for y in range(len(residue_lines)):
                l = residue_lines[y]
                residue_type = l[17:20].strip()
                if l.startswith("HETATM"):
                    if self.modified_residue_mapping_3.get(residue_type):
                        residue_type = self.modified_residue_mapping_3[residue_type]
                    elif y == (len(residue_lines) - 1):
                        # last residue in the chain
                        if residue_type == 'NH2':
                            residue_type = 'UNK' # fixes a few cases e.g. 1MBG, 1K9Q, 1KA6
                        elif ignore_HETATMs:
                            continue

                    elif ignore_HETATMs:
                        continue

                residue_id = l[21:27]
                chain_id = l[21]
                if missing_chain_ids.get(self.pdb_id):
                    chain_id = missing_chain_ids[self.pdb_id]

                if chain_id in self.chain_types:
                    # This means the pdb had SEQRES and we constructed atom_sequences
                    chain_type = self.chain_types[chain_id]
                else:
                    # Otherwise assume this is protein
                    chain_type = 'Protein'

                atom_sequences[chain_id] = atom_sequences.get(chain_id, Sequence(chain_type))

                residue_type = self.modified_residue_mapping_3.get(residue_type, residue_type)

                short_residue_type = None
                if residue_type == 'UNK':
                    short_residue_type = 'X'
                elif chain_type == 'Protein' or chain_type == 'Protein skeleton':
                    short_residue_type = residue_type_3to1_map.get(residue_type) or protonated_residue_type_3to1_map.get(residue_type) or non_canonical_amino_acids.get(residue_type)
                elif chain_type == 'DNA':
                    short_residue_type = dna_nucleotides_2to1_map.get(residue_type) or non_canonical_dna.get(residue_type)
                elif chain_type == 'RNA':
                    short_residue_type = non_canonical_rna.get(residue_type) or residue_type

                if not short_residue_type:
                    if l.startswith("ATOM") and l[12:16] == ' OH2' and l[17:20] == 'TIP':
                        continue
                    elif not self.strict:
                        short_residue_type = 'X'
                    else:
                        raise NonCanonicalResidueException("Unrecognized residue type %s in PDB file '%s', residue ID '%s'." % (residue_type, str(self.pdb_id), str(residue_id)))

                #structural_residue_IDs.append((residue_id, short_residue_type))
                # KAB - way to allow for multiresidue noncanonical AA's
                if len(short_residue_type) == 1:
                    atom_sequences[chain_id].add(PDBResidue(residue_id[0], residue_id[1:], short_residue_type, chain_type))
                else:
                    for char in short_residue_type:
                        atom_sequences[chain_id].add(PDBResidue(residue_id[0], residue_id[1:], char, chain_type))

        self.atom_sequences = atom_sequences

    def _get_ATOM_sequences_2(self):
        '''Creates the ATOM Sequences.'''

        # Get a list of all residues with ATOM or HETATM records
        atom_sequences = {}
        structural_residue_IDs_set = set() # use a set for a quicker lookup
        ignore_HETATMs = True # todo: fix this if we need to deal with HETATMs
        for l in self.structure_lines:
            residue_type = l[17:20].strip()
            if l.startswith("HETATM"):
                if self.modified_residue_mapping_3.get(residue_type):
                    residue_type = self.modified_residue_mapping_3[residue_type]
                elif ignore_HETATMs:
                    continue

            residue_id = l[21:27]
            if residue_id not in structural_residue_IDs_set:
                chain_id = l[21]
                chain_type = self.chain_types[chain_id]
                atom_sequences[chain_id] = atom_sequences.get(chain_id, Sequence(chain_type))
                residue_type = l[17:20].strip()

                residue_type = self.modified_residue_mapping_3.get(residue_type, residue_type)
                short_residue_type = None
                if residue_type == 'UNK':
                    short_residue_type = 'X'
                elif chain_type == 'Protein' or chain_type == 'Protein skeleton':
                    short_residue_type = residue_type_3to1_map.get(residue_type) or protonated_residue_type_3to1_map.get(residue_type)
                elif chain_type == 'DNA':
                    short_residue_type = dna_nucleotides_2to1_map.get(residue_type) or non_canonical_dna.get(residue_type)
                elif chain_type == 'RNA':
                    short_residue_type = non_canonical_rna.get(residue_type) or residue_type
                elif not self.strict:
                    short_residue_type = 'X'
                else:
                    raise NonCanonicalResidueException("Unrecognized residue type %s in PDB file '%s', residue ID '%s'." % (residue_type, str(self.pdb_id), str(residue_id)))

                #structural_residue_IDs.append((residue_id, short_residue_type))
                atom_sequences[chain_id].add(PDBResidue(residue_id[0], residue_id[1:], short_residue_type, chain_type))
                structural_residue_IDs_set.add(residue_id)

        self.atom_sequences = atom_sequences


    def construct_seqres_to_atom_residue_map(self):
        '''Uses the SequenceAligner to align the SEQRES and ATOM sequences and return the mappings.
           If the SEQRES sequence does not exist for a chain, the mappings are None.
           Note: The ResidueRelatrix is better equipped for this job since it can use the SIFTS mappings. This function
           is provided for cases where it is not possible to use the ResidueRelatrix.'''
        from tools.bio.clustalo import SequenceAligner

        seqres_to_atom_maps = {}
        atom_to_seqres_maps = {}
        for c in self.seqres_chain_order:
            if c in self.atom_chain_order:

                # Get the sequences for chain c
                seqres_sequence = self.seqres_sequences[c]
                atom_sequence = self.atom_sequences[c]

                # Align the sequences. mapping will be a mapping between the sequence *strings* (1-indexed)
                sa = SequenceAligner()
                sa.add_sequence('seqres_%s' % c, str(seqres_sequence))
                sa.add_sequence('atom_%s' % c, str(atom_sequence))
                mapping, match_mapping = sa.get_residue_mapping()

                # Use the mapping from the sequence strings to look up the residue IDs and then create a mapping between these residue IDs
                seqres_to_atom_maps[c] = {}
                atom_to_seqres_maps[c] = {}
                for seqres_residue_index, atom_residue_index in mapping.iteritems():
                    seqres_residue_id = seqres_sequence.order[seqres_residue_index - 1] # order is a 0-based list
                    atom_residue_id = atom_sequence.order[atom_residue_index - 1] # order is a 0-based list
                    seqres_to_atom_maps[c][seqres_residue_id] = atom_residue_id
                    atom_to_seqres_maps[c][atom_residue_id] = seqres_residue_id

        return seqres_to_atom_maps, atom_to_seqres_maps


    def construct_pdb_to_rosetta_residue_map(self, rosetta_scripts_path, rosetta_database_path, extra_command_flags = None):
        ''' Uses the features database to create a mapping from Rosetta-numbered residues to PDB ATOM residues.
            Next, the object's rosetta_sequences (a dict of Sequences) element is created.
            Finally, a SequenceMap object is created mapping the Rosetta Sequences to the ATOM Sequences.

            The extra_command_flags parameter expects a string e.g. "-ignore_zero_occupancy false".
        '''

        ## Create a mapping from Rosetta-numbered residues to PDB ATOM residues

        # Apply any PDB-specific hacks
        specific_flag_hacks = None
        if self.pdb_id and HACKS_pdb_specific_hacks.get(self.pdb_id):
            specific_flag_hacks = HACKS_pdb_specific_hacks[self.pdb_id]

        skeletal_chains = sorted([k for k in self.chain_types.keys() if self.chain_types[k] == 'Protein skeleton'])
        if skeletal_chains:
            raise PDBMissingMainchainAtomsException('The PDB to Rosetta residue map could not be created as chains %s only have CA atoms present.' % ", ".join(skeletal_chains))

        # Get the residue mapping using the features database
        pdb_file_contents = "\n".join(self.structure_lines)
        success, mapping = get_pdb_contents_to_pose_residue_map(pdb_file_contents, rosetta_scripts_path, rosetta_database_path, pdb_id = self.pdb_id, extra_flags = ((specific_flag_hacks or '') + ' ' + (extra_command_flags or '')).strip())
        if not success:
            raise colortext.Exception("An error occurred mapping the PDB ATOM residue IDs to the Rosetta numbering.\n%s" % "\n".join(mapping))

        ## Create Sequences for the Rosetta residues (self.rosetta_sequences)

        # Initialize maps
        rosetta_residues = {}
        rosetta_sequences = {}
        for chain_id in self.atom_chain_order:
            chain_type = self.chain_types[chain_id]
            rosetta_residues[chain_id] = {}
            rosetta_sequences[chain_id] = Sequence(chain_type)

        # Create a map rosetta_residues, Chain -> Rosetta residue ID -> Rosetta residue information
        rosetta_pdb_mappings = {}
        for chain_id in self.atom_chain_order:
            rosetta_pdb_mappings[chain_id] = {}
        for k, v in mapping.iteritems():
            rosetta_residues[k[0]][v['pose_residue_id']] = v
            rosetta_pdb_mappings[k[0]][v['pose_residue_id']] = k

        # Create rosetta_sequences map Chain -> Sequence(Residue)
        for chain_id, v in sorted(rosetta_residues.iteritems()):
            chain_type = self.chain_types[chain_id]
            for rosetta_id, residue_info in sorted(v.iteritems()):
                short_residue_type = None

                if chain_type == 'Protein':
                    residue_type = residue_info['name3'].strip()
                    short_residue_type = residue_type_3to1_map[residue_type]
                else:
                    assert(chain_type == 'DNA' or chain_type == 'RNA')
                    residue_type = residue_info['res_type'].strip()
                    if residue_type.find('UpperDNA') != -1 or residue_type.find('LowerDNA') != -1:
                        residue_type = residue_type[:3]
                    short_residue_type = dna_nucleotides_3to1_map.get(residue_type) # Commenting this out since Rosetta does not seem to handle these "or non_canonical_dna.get(residue_type)"

                assert(short_residue_type)
                rosetta_sequences[chain_id].add(Residue(chain_id, rosetta_id, short_residue_type, chain_type))


        ## Create SequenceMap objects to map the Rosetta Sequences to the ATOM Sequences
        rosetta_to_atom_sequence_maps = {}
        for chain_id, rosetta_pdb_mapping in rosetta_pdb_mappings.iteritems():
            rosetta_to_atom_sequence_maps[chain_id] = SequenceMap.from_dict(rosetta_pdb_mapping)

        self.rosetta_to_atom_sequence_maps = rosetta_to_atom_sequence_maps
        self.rosetta_sequences = rosetta_sequences


    def map_pdb_residues_to_rosetta_residues(self, mutations):
        '''This function takes a list of Mutation objects and uses the PDB to Rosetta mapping to return the list of mutations
           using Rosetta numbering.
           e.g.
              p = PDB(...)
              p.construct_pdb_to_rosetta_residue_map()
              rosetta_mutations = p.map_pdb_residues_to_rosetta_residues(pdb_mutations)
        '''
        if not self.rosetta_to_atom_sequence_maps and self.rosetta_sequences:
            raise Exception('The PDB to Rosetta mapping has not been determined. Please call construct_pdb_to_rosetta_residue_map first.')
        import pprint
        pprint.pprint(self.rosetta_to_atom_sequence_maps)
        raise Exception('Here.')


    def assert_wildtype_matches(self, mutation):
        '''Check that the wildtype of the Mutation object matches the PDB sequence.'''
        readwt = self.getAminoAcid(self.getAtomLine(mutation.Chain, mutation.ResidueID))
        assert(mutation.WildTypeAA == residue_type_3to1_map[readwt])


    ### END OF REFACTORED CODE


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
                if missing_chain_ids.get(self.pdb_id):
                    chainID = missing_chain_ids[self.pdb_id]
                if chainID not in chains:
                    chains.append(chainID)
                residue_longname = line[17:20]
                if residue_longname in DNA_residues:
                    # Skip DNA
                    continue
                if residue_longname == 'UNK':
                    # Skip unknown residues
                    continue
                if residue_longname not in allowed_PDB_residues_types and not(ConvertMSEToAtom and residue_longname == 'MSE'):
                    if not self.strict:
                        # Skip unknown residues
                        continue
                    else:
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
                        if residue_longname in non_canonical_amino_acids:
                            sequences[chainID].append(non_canonical_amino_acids[residue_longname])
                        else:
                            sequences[chainID].append(residue_type_3to1_map[residue_longname])

                        residue_map[chainID] = residue_map.get(chainID, [])
                        if residue_longname in non_canonical_amino_acids:
                            residue_map[chainID].append((resid, non_canonical_amino_acids[residue_longname]))
                        else:
                            residue_map[chainID].append((resid, residue_type_3to1_map[residue_longname]))

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

    @staticmethod
    def ChainResidueID2String(chain, residueID):
        '''Takes a chain ID e.g. 'A' and a residueID e.g. '123' or '123A' and returns the 6-character identifier spaced as in the PDB format.'''
        return "%s%s" % (chain, PDB.ResidueID2String(residueID))

    @staticmethod
    def ResidueID2String(residueID):
        '''Takes a residueID e.g. '123' or '123A' and returns the 5-character identifier spaced as in the PDB format.'''
        if residueID.isdigit():
            return "%s " % (residueID.rjust(4))
        else:
            return "%s" % (residueID.rjust(5))

    def validate_mutations(self, mutations):
        '''This function has been refactored to use the SimpleMutation class.
           The parameter is a list of Mutation objects. The function has no return value but raises a PDBValidationException
           if the wildtype in the Mutation m does not match the residue type corresponding to residue m.ResidueID in the PDB file.
        '''
        # Chain, ResidueID, WildTypeAA, MutantAA
        resID2AA = self.get_residue_id_to_type_map()
        badmutations = []
        for m in mutations:
            wildtype = resID2AA.get(PDB.ChainResidueID2String(m.Chain, m.ResidueID), "")
            if m.WildTypeAA != wildtype:
                badmutations.append(m)
        if badmutations:
            raise PDBValidationException("The mutation(s) %s could not be matched against the PDB %s." % (", ".join(map(str, badmutations)), self.pdb_id))

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
        '''Takes in a list of (Chain, ResidueID, WildTypeAA, MutantAA) mutation tuples and returns the remapped
           mutations based on the ddGResmap (which must be previously instantiated).
           This function checks that the mutated positions exist and that the wild-type matches the PDB.
        '''
        raise Exception('This code is deprecated. Please use map_pdb_residues_to_rosetta_residues instead.')

        remappedMutations = []
        ddGResmap = self.get_ddGResmap()

        for m in mutations:
            ns = (PDB.ChainResidueID2String(m['Chain'], str(ddGResmap['ATOM-%s' % PDB.ChainResidueID2String(m['Chain'], m['ResidueID'])])))
            remappedMutations.append(Mutation(m['WildTypeAA'], ns[1:].strip(), m['MutantAA'], ns[0]))

        # Validate the mutations against the Rosetta residues
        sequences, residue_map = self.GetRosettaResidueMap()
        for rm in remappedMutations:
            offset = int(residue_map[rm.Chain][0][0])
            pr = residue_map[rm.Chain][int(rm.ResidueID) - offset]
            assert(pr[0] == rm.ResidueID)
            assert(pr[1] == rm.WildTypeAA)
        return remappedMutations

    def stripForDDG(self, chains = True, keepHETATM = False, numberOfModels = None):
        '''Strips a PDB to ATOM lines. If keepHETATM is True then also retain HETATM lines.
           By default all PDB chains are kept. The chains parameter should be True or a list.
           In the latter case, only those chains in the list are kept.
           Unoccupied ATOM lines are discarded.
           This function also builds maps from PDB numbering to Rosetta numbering and vice versa.
           '''
        raise Exception('This code is deprecated.')

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
          atomlines = [line for line in self.lines if line[0:4] == "ATOM" and line[17:20] in allowed_PDB_residues_types and line[26] == ' ']
        else:  
          atomlines = [line for line in self.lines if line[0:4] == "ATOM" and (line[17:20].strip() in allowed_PDB_residues_and_nucleotides) and line[26] == ' ']

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
            mean, stddev, variance = get_mean_and_standard_deviation(bfactorlist)
            BFPerResidue[residueID] = (mean, stddev)
            MeanPerResidue.append(mean)
        TotalAverage, TotalStandardDeviation, variance = get_mean_and_standard_deviation(MeanPerResidue)

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

    def get_residue_id_to_type_map(self):
        '''Returns a dictionary mapping 6-character residue IDs (Chain, residue number, insertion code e.g. "A 123B") to the
           corresponding one-letter amino acid.

           Caveat: This function ignores occupancy - this function should be called once occupancy has been dealt with appropriately.'''

        resid2type = {}
        atomlines = self.parsed_lines['ATOM  ']
        for line in atomlines:
            resname = line[17:20]
            if resname in allowed_PDB_residues_types and line[13:16] == 'CA ':
                resid2type[line[21:27]] = residue_type_3to1_map.get(resname) or protonated_residue_type_3to1_map.get(resname)
        return resid2type



    def pruneChains(self, chainsChosen):
        # If chainsChosen is non-empty then removes any ATOM lines of chains not in chainsChosen
        if chainsChosen and (sorted(chainsChosen) != sorted(self.chain_ids())):
            templines = []
            for line in self.lines:
                shortRecordName = line[0:4]
                if shortRecordName == "ATOM" and line[17:20] in allowed_PDB_residues_types and line[26] == ' ':
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
            if line[0:4] == "ATOM" and line[17:20] in allowed_PDB_residues_types and line[26] == ' ':
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
            lines = [line for line in self.atomlines(resid_list) if line[17:20] in allowed_PDB_residues_types]
        else:                # consider only given atoms
            lines = [line for line in self.atomlines(resid_list) if line[17:20] in allowed_PDB_residues_types and line[12:16] == atom]

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
            if line[17:20] in allowed_PDB_residues_types:
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

                if usingClassic and (residue not in allowed_PDB_residues_types):
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
            elif not line[0:6].rstrip() in all_record_types:
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
