#!/usr/bin/python
# encoding: utf-8
"""
relatrix.py
A class for relating residues using Rosetta numbering, PDB ATOM numbering, SEQRES/FASTA sequences, and UniParc sequences.

Created by Shane O'Connor 2013
"""

import types
import traceback
import pprint

from fasta import FASTA
from pdb import PDB, PDBMissingMainchainAtomsException, ROSETTA_HACKS_residues_to_remove
from pdbml import PDBML, MissingPDBMLException
from clustalo import PDBUniParcSequenceAligner, MultipleAlignmentException
from klab import colortext
from basics import Sequence, SequenceMap, UniParcPDBSequenceMap
from sifts import SIFTS, MissingSIFTSRecord, BadSIFTSMapping, NoSIFTSPDBUniParcMapping

use_seqres_sequence_for_fasta_sequence = set(['1A2C', '4CPA', '2ATC', '1OLR', '1DS2'])
use_fasta_sequence_for_seqres_sequence = set(['1DEQ'])

# In these
use_SIFTS_match_for_seqres_sequence = set([
    ('1AAR', 'A'), ('1AAR', 'B'), # not surprising since this is Polyubiquitin-C
    ('1AR1', 'D'), # for seqres to uniparc, chain D, Clustal maps 94->None, 95->None, 96->95, 97->96 whereas SIFTS maps 94->94, 95->95, 96->None, 97->96. Either mapping seems acceptable on a purely sequential level (although SIFTS seems better) but I am assuming that the SIFTS mapping makes more sense.
    ('1BF4', 'A'), # for seqres to uniparc, chain A, Clustal maps 35->36, 36->None, 37->None, 38->38 whereas SIFTS maps 35->36, 36->37, 37->38, 38->None. Either mapping seems acceptable on a purely sequential level (although SIFTS seems better) but I am assuming that the SIFTS mapping makes more sense.
    ('1CPM', 'A'), # DBREF / UniProt says UPI000012BD97, SIFTS says UPI000005F74B. Either fits from a purely sequential standpoint as these two proteins have the same sequence apart from the 38th residue which is R in the former and P in the latter
    ('1DEQ', 'C'), ('1DEQ', 'F'), ('1DEQ', 'P'), ('1DEQ', 'S'), # Clustal maps 222->247, SIFTS maps 222->245. Either one is correct - the sequence in GTG where one G is mapped to and the TG (or GT) is unmapped.
    ('1OTR', 'B'), # Poly-ubiquitin. Clustal matches at position 153 (3rd copy), SIFTS matches at position 305 (5th and last copy).
    ('1UBQ', 'A'), # Poly-ubiquitin. Clustal matches at position 305 (5th copy), SIFTS matches at position 609 (9th and last full copy). Clustal also maps the final residue weirdly (to the final residue of the 6th copy rather than the 5th copy)
    ('1SCE', 'A'), ('1SCE', 'B'), ('1SCE', 'C'), ('1SCE', 'D'), # SIFTS has a better mapping
    ('1ORC', 'A'), # Both matches are valid but neither are ideal (I would have done 53->53,...56->56,...62->57, 63->58,... skipping the inserted residues with ATOM IDs 56A-56E). I'll go with SIFTS since that is somewhat standard.
])

known_bad_clustal_to_sifts_mappings = set([
    ('1AAR', 'A'), ('1AAR', 'B'),
    ('1BF4', 'A'),
    ('1CPM', 'A'),
    ('1DEQ', 'C'), ('1DEQ', 'F'), ('1DEQ', 'P'), ('1DEQ', 'S'), # the residue types actually agree but the key check will fail
    ('1SCE', 'A'), ('1SCE', 'B'), ('1SCE', 'C'), ('1SCE', 'D'),
    ('487D', 'H'), ('487D', 'I'), ('487D', 'J'), ('487D', 'K'), ('487D', 'L'), ('487D', 'M'), ('487D', 'N'), # The mapping SIFTS gets (from UniProt) is not as close as the DBREF entries
    ('1ORC', 'A'), # the residue types actually agree but the key check will fail
])

do_not_use_SIFTS_for_these_chains = set([
    ('1HGH', 'A'), # The DBREF match (UPI000012C4CD) is better in terms of sequence and the reference also states that the A/Aichi/2/1968 (H3N2) isolate is under study
    ('1URK', 'A'), # The DBREF/UniProt match (UPI00002BDB5) is a super-sequence of the SIFTS match (UPI000002C604)
    ('2ATC', 'B'), # Clustal maps the K129 lysine deletion correctly, mapping RRADD->R(K)RAND. SIFTS maps RRADD->RKR(A)ND
    ('487D', 'H'), ('487D', 'I'), ('487D', 'J'), ('487D', 'K'), ('487D', 'L'), ('487D', 'M'), ('487D', 'N'), # The mapping SIFTS gets (from UniProt) is not as close as the DBREF entries
    ('1E6N', 'A'), ('1E6N', 'B'), # The DBREF match (UPI0000000F1C) matches the sequence. The UniProt SIFTS match (UPI00000B96E8) is not exact but is close. I don't know which is the better match but I chose the DBREF one.
])

pdbs_with_do_not_use_SIFTS_for_these_chains = set([p[0] for p in do_not_use_SIFTS_for_these_chains])

do_not_use_the_sequence_aligner = set([
    '1CBW',
    '1KJ1', # The sequences are too close for Clustal to match properly
    '1M7T', # Chimera. SIFTS maps this properly
    '1Z1I', # This (306 residues) maps to P0C6U8/UPI000018DB89 (Replicase polyprotein 1a,  4,382 residues) A 3241-3546, the '3C-like proteinase' region
            #                         and P0C6X7/UPI000019098F (Replicase polyprotein 1ab, 7,073 residues) A 3241-3546, the '3C-like proteinase' region
            # which gives our Clustal sequence aligner an ambiguous mapping. Both are valid mappings. SIFTS chooses the the longer one, UPI000019098F.
])


class ClustalSIFTSCrossValidationException(Exception): pass


class ResidueRelatrix(object):
    ''' A class for relating residue IDs from different schemes.
        Note: we assume throughout that there is one map from SEQRES to UniParc. This is not always true e.g. Polyubiquitin-C (UPI000000D74D) has 9 copies of the ubiquitin sequence.'''

    schemes = ['rosetta', 'atom', 'seqres', 'fasta', 'uniparc']

    def __init__(self, pdb_id, rosetta_scripts_path, rosetta_database_path = None, chains_to_keep = [], min_clustal_cut_off = 80, cache_dir = None, silent = False, acceptable_sequence_percentage_match = 80.0, acceptable_sifts_sequence_percentage_match = None, starting_clustal_cut_off = 100, bio_cache = None, restrict_to_uniparc_values = [], trust_sifts = None, restrict_match_percentage_errors_to_these_uniparc_ids = None, extra_rosetta_mapping_command_flags = None, strict = True): # keep_HETATMS = False
        ''' acceptable_sequence_percentage_match is used when checking whether the SEQRES sequences have a mapping. Usually
            90.00% works but some cases e.g. 1AR1, chain C, have a low matching score mainly due to extra residues. I set
            this to 80.00% to cover most cases.

            extra_rosetta_mapping_command_flags should typically be left unspecified but some cases require these to be set
            for mappings to Rosetta e.g. 4CPA.
        '''

        # todo: add an option to not use the Clustal sequence aligner and only use the SIFTS mapping. This could be useful for a web interface where we do not want to have to fix things manually.

        if acceptable_sifts_sequence_percentage_match == None:
            acceptable_sifts_sequence_percentage_match = acceptable_sequence_percentage_match
        assert(0.0 <= acceptable_sequence_percentage_match <= 100.0)
        assert(0.0 <= acceptable_sifts_sequence_percentage_match <= 100.0)

        if not((type(pdb_id) == types.StringType or type(pdb_id) == type(u'')) and len(pdb_id) == 4 and pdb_id.isalnum()):
            raise Exception("Expected an 4-character long alphanumeric PDB identifer. Received '%s'." % str(pdb_id))
        self.pdb_id = pdb_id.upper()
        self.silent = silent
        self.rosetta_scripts_path = rosetta_scripts_path
        self.rosetta_database_path = rosetta_database_path
        self.bio_cache = bio_cache
        self.cache_dir = cache_dir
        self.restrict_match_percentage_errors_to_these_uniparc_ids = restrict_match_percentage_errors_to_these_uniparc_ids
        print('self.restrict_match_percentage_errors_to_these_uniparc_ids', self.restrict_match_percentage_errors_to_these_uniparc_ids)
        self.trust_sifts = trust_sifts
        if (not self.cache_dir) and self.bio_cache:
            self.cache_dir = self.bio_cache.cache_dir

        self.alignment_cutoff = None
        self.acceptable_sequence_percentage_match = acceptable_sequence_percentage_match
        self.acceptable_sifts_sequence_percentage_match = acceptable_sifts_sequence_percentage_match
        self.extra_rosetta_mapping_command_flags = None
        self.strict = strict
        self.uniparc_maps_are_injective = True

        self.replacement_pdb_id = None

        self.FASTA = None
        self.pdb = None
        self.pdbml = None
        self.PDB_UniParc_SA = None
        self.sifts = None

        self.uniparc_sequences = None
        self.fasta_sequences = None
        self.seqres_sequences = None
        self.atom_sequences = None
        self.rosetta_sequences = None
        self.pdb_to_rosetta_residue_map_error = False

        # Used to resolve ambiguous cases e.g. 1M9D chain C (and D) matches UPI000217CB5A and UPI0000106BB1 and the sequence of those UniParc entries is identical in the range where 1M9D matches.
        # We cannot tell which match is "better" by sequence alone. Here, we rely on external sources like SIFTS which provide an unambiguous match (UPI000217CB5A).
        #
        # Example code for handling these errors:
        #
        #  try:
        #      rr = ResidueRelatrix(pdb_id, '/some/path/rosetta_scripts.linuxgccrelease', None, min_clustal_cut_off = 90, cache_dir = self.cache_dir, bio_cache = self.bio_cache)
        #  except MultipleAlignmentException, e:
        #      restrict_to_uniparc_values = [get the correct UniParc entries from some source e.g. SIFTS]
        #      rr = ResidueRelatrix(pdb_id, '/some/path/rosetta_scripts.linuxgccrelease', None, min_clustal_cut_off = 90, cache_dir = self.cache_dir, bio_cache = self.bio_cache, restrict_to_uniparc_values = restrict_to_uniparc_values)
        #
        self.restrict_to_uniparc_values = restrict_to_uniparc_values

        self.rosetta_to_atom_sequence_maps = None
        self.atom_to_seqres_sequence_maps = None
        self.seqres_to_uniparc_sequence_maps = None

        self.atom_to_rosetta_sequence_maps = None
        self.seqres_to_atom_sequence_maps = None
        self.uniparc_to_seqres_sequence_maps = None # This map is indexed by PDB chain IDs

        self.pdbml_atom_to_seqres_sequence_maps = None
        self.clustal_seqres_to_uniparc_sequence_maps = None

        self.sifts_atom_to_seqres_sequence_maps = None
        self.sifts_seqres_to_uniparc_sequence_maps = None
        self.sifts_atom_to_uniparc_sequence_maps = None

        self.pdb_chain_to_uniparc_chain_mapping = {}

        self.sifts_exception = None

        self._create_objects(chains_to_keep, starting_clustal_cut_off, min_clustal_cut_off, True) # todo: at present, we always strip HETATMs. We may want to change this in the future.
        self._create_sequences()
        self._create_sequence_maps()
        self._merge_sifts_maps()
        self._prune_maps_to_sequences()
        self._validate()
        self._create_inverse_maps()

    ### API functions###

    def convert(self, chain_id, residue_id, from_scheme, to_scheme):
        '''The API conversion function. This converts between the different residue ID schemes.'''

        # At the cost of three function calls, we ignore the case of the scheme parameters to be more user-friendly.
        from_scheme = from_scheme.lower()
        to_scheme = to_scheme.lower()
        assert(from_scheme in ResidueRelatrix.schemes)
        assert(to_scheme in ResidueRelatrix.schemes)
        return self._convert(chain_id, residue_id, from_scheme, to_scheme)

    def _convert(self, chain_id, residue_id, from_scheme, to_scheme):
        '''The actual 'private' conversion function.'''

        # There are 12 valid combinations but rather than write them all out explicitly, we will use recursion, sacrificing speed for brevity
        if from_scheme == 'rosetta':
            atom_id = self.rosetta_to_atom_sequence_maps.get(chain_id, {})[residue_id]
            if to_scheme == 'atom':
                return atom_id
            else:
                return self._convert(chain_id, atom_id, 'atom', to_scheme)
        if from_scheme == 'atom':
            if to_scheme == 'rosetta':
                return self.atom_to_rosetta_sequence_maps.get(chain_id, {})[residue_id]
            else:
                seqres_id = self.atom_to_seqres_sequence_maps.get(chain_id, {})[residue_id]
                if to_scheme == 'seqres':
                    return seqres_id
                return self.convert(chain_id, seqres_id, 'seqres', to_scheme)
        if from_scheme == 'seqres':
            if to_scheme == 'uniparc':
                return self.seqres_to_uniparc_sequence_maps.get(chain_id, {})[residue_id]
            else:
                atom_id = self.seqres_to_atom_sequence_maps.get(chain_id, {})[residue_id]
                if to_scheme == 'atom':
                    return atom_id
                return self.convert(chain_id, atom_id, 'atom', to_scheme)
        if from_scheme == 'uniparc':
            seqres_id = self.uniparc_to_seqres_sequence_maps.get(chain_id, {})[residue_id]
            if to_scheme == 'seqres':
                return seqres_id
            else:
                return self._convert(chain_id, seqres_id, 'seqres', to_scheme)

        raise Exception("We should never reach this line.")


    def convert_from_rosetta(self, residue_id, to_scheme):
        '''A simpler conversion function to convert from Rosetta numbering without requiring the chain identifier.'''

        assert(type(residue_id) == types.IntType)

        # Find the chain_id associated with the residue_id
        # Scan *all* sequences without breaking out to make sure that we do not have any duplicate maps
        chain_id = None
        for c, sequence in self.rosetta_sequences.iteritems():
            for id, r in sequence:
                if r.ResidueID == residue_id:
                    assert(chain_id == None)
                    chain_id = c

        if chain_id:
            return self.convert(chain_id, residue_id, 'rosetta', to_scheme)
        else:
            return None

    ### Private validation methods ###

    def _validate(self):
        '''Validate the mappings.'''

        self._validate_fasta_vs_seqres()
        self._validate_mapping_signature()
        self._validate_id_types()
        self._validate_residue_types()

    def _validate_fasta_vs_seqres(self):
        '''Check that the FASTA and SEQRES sequences agree (they sometimes differ)'''
        pdb_id = self.pdb_id
        for chain_id, sequence in self.pdb.seqres_sequences.iteritems():
            if str(sequence) != self.FASTA[pdb_id][chain_id]:
                if self.pdb_id in use_seqres_sequence_for_fasta_sequence:
                    self.FASTA.replace_sequence(self.pdb_id, chain_id, str(sequence))
                elif self.pdb_id in use_fasta_sequence_for_seqres_sequence:
                    self.pdb.seqres_sequences[chain_id] = Sequence.from_sequence(chain_id, self.FASTA[pdb_id][chain_id], self.sequence_types[chain_id])
                    sequence = self.FASTA[pdb_id][chain_id]
                if str(sequence) != self.FASTA[pdb_id][chain_id]:
                    seq_str = str(sequence)
                    fasta_str = self.FASTA[pdb_id][chain_id]
                    if len(seq_str) != len(fasta_str):
                        msg = 'The chains are different lengths.'
                    else:
                        diff_pos = []
                        for x in xrange(len(seq_str)):
                            if seq_str[x] != fasta_str[x]:
                                diff_pos.append('position {0} {1}->{2}'.format(x, seq_str[x], fasta_str[x]))
                        assert(diff_pos)
                        msg = 'The chains differ at this positions (SEQRES -> FASTA): {0}'.format(', '.join(diff_pos))
                    raise colortext.Exception("The SEQRES and FASTA sequences disagree for chain %s in %s. This can happen but special-case handling (use_seqres_sequence_for_fasta_sequence) should be added to the file containing the %s class.\n%s" % (chain_id, pdb_id, self.__class__.__name__, msg))


    def _validate_mapping_signature(self):
        '''Make sure the domains and ranges of the SequenceMaps match the Sequences.'''

        # rosetta_to_atom_sequence_maps
        for chain_id, sequence_map in self.rosetta_to_atom_sequence_maps.iteritems():
            # Check that all Rosetta residues have a mapping
            assert(sorted(sequence_map.keys()) == sorted(self.rosetta_sequences[chain_id].ids()))

            # Check that all ATOM residues in the mapping exist and that the mapping is injective
            rng = set(sequence_map.values())
            atom_residue_ids = set(self.atom_sequences[chain_id].ids())
            if rng.intersection(atom_residue_ids) != rng:
                colortext.pcyan('{0} chain {1}'.format(self.pdb_id, chain_id))
                print(self.atom_sequences[chain_id])
                colortext.pcyan('{0} chain {1}'.format(self.pdb_id, chain_id))
                print(sequence_map)
                print(map(str, sorted(rng)))
                print(map(str, sorted(atom_residue_ids)))
                print(map(str, sorted(rng.intersection(atom_residue_ids))))
                missing_residues = rng.difference(rng.intersection(atom_residue_ids))
                print('missing_residues')
                print(map(str, sorted(missing_residues)))
                assert(rng.intersection(atom_residue_ids) == rng)
            assert(len(rng) == len(sequence_map.values()))



#1->'E  16 ', 2->'E  17 ', 3->'E  18 ', 4->'E  19 ', 5->'E  20 ', 6->'E  21 ', 7->'E  22 ', 8->'E  23 ', 9->'E  24 ', 10->'E  25 ', 11->'E  26 ', 12->'E  27 ', 13->'E  28 ', 14->'E  29 ', 15->'E  30 ', 16->'E  31 ', 17->'E  32 ', 18->'E  33 ', 19->'E  34 ', 20->'E  37 ', 21->'E  38 ', 22->'E  39 ', 23->'E  40 ', 24->'E  41 ', 25->'E  42 ', 26->'E  43 ', 27->'E  44 ', 28->'E  45 ', 29->'E  46 ', 30->'E  47 ', 31->'E  48 ', 32->'E  49 ', 33->'E  50 ', 34->'E  51 ', 35->'E  52 ', 36->'E  53 ', 37->'E  54 ', 38->'E  55 ', 39->'E  56 ', 40->'E  57 ', 41->'E  58 ', 42->'E  59 ', 43->'E  60 ', 44->'E  61 ', 45->'E  62 ', 46->'E  63 ', 47->'E  64 ', 48->'E  65 ', 49->'E  66 ', 50->'E  67 ', 51->'E  69 ', 52->'E  70 ', 53->'E  71 ', 54->'E  72 ', 55->'E  73 ', 56->'E  74 ', 57->'E  75 ', 58->'E  76 ', 59->'E  77 ', 60->'E  78 ', 61->'E  79 ', 62->'E  80 ', 63->'E  81 ', 64->'E  82 ', 65->'E  83 ', 66->'E  84 ', 67->'E  85 ', 68->'E  86 ', 69->'E  87 ', 70->'E  88 ', 71->'E  89 ', 72->'E  90 ', 73->'E  91 ', 74->'E  92 ', 75->'E  93 ', 76->'E  94 ', 77->'E  95 ', 78->'E  96 ', 79->'E  97 ', 80->'E  98 ', 81->'E  99 ', 82->'E 100 ', 83->'E 101 ', 84->'E 102 ', 85->'E 103 ', 86->'E 104 ', 87->'E 105 ', 88->'E 106 ', 89->'E 107 ', 90->'E 108 ', 91->'E 109 ', 92->'E 110 ', 93->'E 111 ', 94->'E 112 ', 95->'E 113 ', 96->'E 114 ', 97->'E 115 ', 98->'E 116 ', 99->'E 117 ', 100->'E 118 ', 101->'E 119 ', 102->'E 120 ', 103->'E 121 ', 104->'E 122 ', 105->'E 123 ', 106->'E 124 ', 107->'E 125 ', 108->'E 127 ', 109->'E 128 ', 110->'E 129 ', 111->'E 130 ', 112->'E 132 ', 113->'E 133 ', 114->'E 134 ', 115->'E 135 ', 116->'E 136 ', 117->'E 137 ', 118->'E 138 ', 119->'E 139 ', 120->'E 140 ', 121->'E 141 ', 122->'E 142 ', 123->'E 143 ', 124->'E 144 ', 125->'E 145 ', 126->'E 146 ', 127->'E 147 ', 128->'E 148 ', 129->'E 149 ', 130->'E 150 ', 131->'E 151 ', 132->'E 152 ', 133->'E 153 ', 134->'E 154 ', 135->'E 155 ', 136->'E 156 ', 137->'E 157 ', 138->'E 158 ', 139->'E 159 ', 140->'E 160 ', 141->'E 161 ', 142->'E 162 ', 143->'E 163 ', 144->'E 164 ', 145->'E 165 ', 146->'E 166 ', 147->'E 167 ', 148->'E 168 ', 149->'E 169 ', 150->'E 170 ', 151->'E 171 ', 152->'E 172 ', 153->'E 173 ', 154->'E 174 ', 155->'E 175 ', 156->'E 176 ', 157->'E 177 ', 158->'E 178 ', 159->'E 179 ', 160->'E 180 ', 161->'E 181 ', 162->'E 182 ', 163->'E 183 ', 164->'E 184A', 165->'E 184 ', 166->'E 185 ', 167->'E 186 ', 168->'E 187 ', 169->'E 188A', 170->'E 188 ', 171->'E 189 ', 172->'E 190 ', 173->'E 191 ', 174->'E 192 ', 175->'E 193 ', 176->'E 194 ', 177->'E 195 ', 178->'E 196 ', 179->'E 197 ', 180->'E 198 ', 181->'E 199 ', 182->'E 200 ', 183->'E 201 ', 184->'E 202 ', 185->'E 203 ', 186->'E 204 ', 187->'E 209 ', 188->'E 210 ', 189->'E 211 ', 190->'E 212 ', 191->'E 213 ', 192->'E 214 ', 193->'E 215 ', 194->'E 216 ', 195->'E 217 ', 196->'E 219 ', 197->'E 220 ', 198->'E 221A', 199->'E 221 ', 200->'E 222 ', 201->'E 223 ', 202->'E 224 ', 203->'E 225 ', 204->'E 226 ', 205->'E 227 ', 206->'E 228 ', 207->'E 229 ', 208->'E 230 ', 209->'E 231 ', 210->'E 232 ', 211->'E 233 ', 212->'E 234 ', 213->'E 235 ', 214->'E 236 ', 215->'E 237 ', 216->'E 238 ', 217->'E 239 ', 218->'E 240 ', 219->'E 241 ', 220->'E 242 ', 221->'E 243 ', 222->'E 244 ', 223->'E 245 '
#set([u'E  61 ', u'E 120 ', u'E  96 ', u'E 244 ', u'E 240 ', u'E 173 ', u'E  75 ', u'E 235 ', u'E 113 ', u'E  51 ', u'E  29 ', u'E 185 ', u'E  69 ', u'E 228 ', u'E  16 ', u'E 103 ', u'E 203 ', u'E 204 ', u'E  22 ', u'E  42 ', u'E  58 ', u'E 219 ', u'E 221 ', u'E 153 ', u'E  19 ', u'E 163 ', u'E 217 ', u'E  84 ', u'E 143 ', u'E  97 ', u'E 160 ', u'E  56 ', u'E 104 ', u'E  60 ', u'E 186 ', u'E 112 ', u'E  28 ', u'E  76 ', u'E 172 ', u'E  17 ', u'E 188A', u'E 136 ', u'E 168 ', u'E 212 ', u'E 216 ', u'E  45 ', u'E 191 ', u'E  59 ', u'E  21 ', u'E 232 ', u'E 220 ', u'E 211 ', u'E 132 ', u'E 152 ', u'E  87 ', u'E 124 ', u'E 144 ', u'E 199 ', u'E 137 ', u'E 161 ', u'E 119 ', u'E  57 ', u'E  86 ', u'E 159 ', u'E 245 ', u'E  67 ', u'E  94 ', u'E 105 ', u'E 238 ', u'E 128 ', u'E 175 ', u'E  77 ', u'E 197 ', u'E 202 ', u'E 169 ', u'E 111 ', u'E  27 ', u'E 123 ', u'E  44 ', u'E 190 ', u'E 129 ', u'E  20 ', u'E 233 ', u'E 151 ', u'E 127 ', u'E 145 ', u'E 198 ', u'E 223 ', u'E 243 ', u'E  54 ', u'E  81 ', u'E 118 ', u'E 146 ', u'E  70 ', u'E 106 ', u'E  66 ', u'E  38 ', u'E  95 ', u'E 174 ', u'E 196 ', u'E 158 ', u'E 180 ', u'E 110 ', u'E  26 ', u'E  78 ', u'E 239 ', u'E  37 ', u'E 230 ', u'E  89 ', u'E  47 ', u'E 166 ', u'E 133 ', u'E 222 ', u'E 150 ', u'E  80 ', u'E 147 ', u'E  71 ', u'E  49 ', u'E  39 ', u'E 117 ', u'E  55 ', u'E 195 ', u'E  65 ', u'E 107 ', u'E  25 ', u'E 181 ', u'E 177 ', u'E  79 ', u'E  41 ', u'E 134 ', u'E  30 ', u'E 201 ', u'E 122 ', u'E  88 ', u'E  46 ', u'E 225 ', u'E 242 ', u'E 188 ', u'E 167 ', u'E 130 ', u'E 157 ', u'E 209 ', u'E  92 ', u'E  72 ', u'E 241 ', u'E  48 ', u'E  52 ', u'E 231 ', u'E  83 ', u'E 116 ', u'E 148 ', u'E 100 ', u'E  64 ', u'E 176 ', u'E  40 ', u'E 194 ', u'E  31 ', u'E 221A', u'E 200 ', u'E 224 ', u'E 164 ', u'E 189 ', u'E 236 ', u'E 140 ', u'E 156 ', u'E 108 ', u'E  93 ', u'E 155 ', u'E 214 ', u'E  63 ', u'E 115 ', u'E  53 ', u'E  82 ', u'E 149 ', u'E 171 ', u'E  73 ', u'E 101 ', u'E  43 ', u'E 193 ', u'E 210 ', u'E  98 ', u'E 139 ', u'E 182 ', u'E 135 ', u'E  24 ', u'E 227 ', u'E  32 ', u'E 237 ', u'E 215 ', u'E 141 ', u'E 179 ', u'E 184A', u'E  90 ', u'E 109 ', u'E 187 ', u'E 165 ', u'E 154 ', u'E  62 ', u'E  91 ', u'E  74 ', u'E 170 ', u'E 213 ', u'E  50 ', u'E 184 ', u'E 114 ', u'E 192 ', u'E 229 ', u'E 121 ', u'E 102 ', u'E  34 ', u'E 138 ', u'E  23 ', u'E 183 ', u'E  18 ', u'E  33 ', u'E  99 ', u'E 142 ', u'E 125 ', u'E 178 ', u'E 226 ', u'E 162 ', u'E 234 ', u'E  85 '])
#set(['E  61 ', 'E 120 ', 'E  96 ', 'E  20 ', 'E 173 ', 'E  75 ', 'E 113 ', 'E  51 ', 'E  29 ', 'E 185 ', 'E 128 ', 'E 228 ', 'E  16 ', 'E 103 ', 'E 204 ', 'E  22 ', 'E  42 ', 'E  58 ', 'E 219 ', 'E 221 ', 'E 153 ', 'E  19 ', 'E 163 ', 'E 235 ', 'E  84 ', 'E 143 ', 'E  97 ', 'E 192 ', 'E 160 ', 'E  56 ', 'E 104 ', 'E  60 ', 'E 186 ', 'E 112 ', 'E  28 ', 'E  76 ', 'E 172 ', 'E  17 ', 'E 203 ', 'E  55 ', 'E 168 ', 'E 195 ', 'E  45 ', 'E 191 ', 'E  59 ', 'E 245 ', 'E 232 ', 'E 220 ', 'E 132 ', 'E 152 ', 'E  87 ', 'E  65 ', 'E 144 ', 'E 199 ', 'E  54 ', 'E 161 ', 'E 119 ', 'E  57 ', 'E  86 ', 'E 159 ', 'E  21 ', 'E  67 ', 'E  94 ', 'E 105 ', 'E 238 ', 'E  69 ', 'E 175 ', 'E  77 ', 'E 197 ', 'E 202 ', 'E 169 ', 'E 111 ', 'E  27 ', 'E 187 ', 'E  44 ', 'E 190 ', 'E 129 ', 'E 244 ', 'E 233 ', 'E 151 ', 'E  62 ', 'E  66 ', 'E 145 ', 'E 198 ', 'E 223 ', 'E 137 ', 'E  81 ', 'E 118 ', 'E 146 ', 'E  70 ', 'E 106 ', 'E 127 ', 'E  38 ', 'E  95 ', 'E 212 ', 'E 196 ', 'E 158 ', 'E 180 ', 'E 110 ', 'E  26 ', 'E  78 ', 'E 239 ', 'E  53 ', 'E 174 ', 'E 230 ', 'E  89 ', 'E  47 ', 'E 166 ', 'E  50 ', 'E 222 ', 'E 150 ', 'E  80 ', 'E 147 ', 'E  71 ', 'E  49 ', 'E  39 ', 'E 117 ', 'E 136 ', 'E 216 ', 'E 124 ', 'E 107 ', 'E  25 ', 'E 181 ', 'E 177 ', 'E  79 ', 'E  41 ', 'E 134 ', 'E  30 ', 'E 201 ', 'E  63 ', 'E  88 ', 'E  46 ', 'E 225 ', 'E 242 ', 'E 188 ', 'E 167 ', 'E 231 ', 'E 125 ', 'E 157 ', 'E 209 ', 'E  92 ', 'E  72 ', 'E 241 ', 'E  48 ', 'E  52 ', 'E  83 ', 'E 116 ', 'E 148 ', 'E 100 ', 'E 188A', 'E 176 ', 'E  40 ', 'E 217 ', 'E  31 ', 'E 221A', 'E 200 ', 'E  37 ', 'E 224 ', 'E 164 ', 'E 189 ', 'E 236 ', 'E 140 ', 'E 156 ', 'E 108 ', 'E  93 ', 'E  33 ', 'E 155 ', 'E 214 ', 'E 122 ', 'E 130 ', 'E  82 ', 'E 149 ', 'E 171 ', 'E  73 ', 'E 101 ', 'E  43 ', 'E 193 ', 'E 210 ', 'E  98 ', 'E 139 ', 'E 182 ', 'E 135 ', 'E 240 ', 'E 227 ', 'E  32 ', 'E 237 ', 'E 215 ', 'E 243 ', 'E 179 ', 'E 184A', 'E  90 ', 'E 109 ', 'E 165 ', 'E 154 ', 'E 123 ', 'E  91 ', 'E  74 ', 'E 170 ', 'E 194 ', 'E 213 ', 'E 133 ', 'E 184 ', 'E 114 ', 'E 211 ', 'E 229 ', 'E 121 ', 'E 102 ', 'E  34 ', 'E 138 ', 'E  23 ', 'E 183 ', 'E  18 ', 'E 141 ', 'E  24 ', 'E  99 ', 'E 142 ', 'E  64 ', 'E 178 ', 'E 226 ', 'E 162 ', 'E 234 ', 'E  85 '])
#set(['E  61 ', 'E 120 ', 'E  96 ', 'E 244 ', 'E 173 ', 'E  75 ', 'E 113 ', 'E  51 ', 'E  29 ', 'E 185 ', 'E  69 ', 'E 228 ', 'E  16 ', 'E 103 ', 'E 204 ', 'E  22 ', 'E  42 ', 'E  58 ', 'E 219 ', 'E 221 ', 'E 153 ', 'E  19 ', 'E 163 ', 'E 235 ', 'E  84 ', 'E 143 ', 'E  97 ', 'E 160 ', 'E  56 ', 'E 104 ', 'E  60 ', 'E 186 ', 'E 112 ', 'E  28 ', 'E  76 ', 'E 172 ', 'E  17 ', 'E 203 ', 'E 136 ', 'E 168 ', 'E 216 ', 'E  45 ', 'E 191 ', 'E  59 ', 'E  21 ', 'E 232 ', 'E 220 ', 'E 211 ', 'E 132 ', 'E 152 ', 'E  87 ', 'E 124 ', 'E 144 ', 'E 199 ', 'E 137 ', 'E 161 ', 'E 119 ', 'E  57 ', 'E  86 ', 'E 159 ', 'E 245 ', 'E  67 ', 'E  94 ', 'E 105 ', 'E 238 ', 'E 128 ', 'E 175 ', 'E  77 ', 'E 197 ', 'E 202 ', 'E 169 ', 'E 111 ', 'E  27 ', 'E 187 ', 'E  44 ', 'E 190 ', 'E 129 ', 'E  20 ', 'E 233 ', 'E 151 ', 'E 127 ', 'E 145 ', 'E 198 ', 'E 223 ', 'E  74 ', 'E  54 ', 'E  81 ', 'E 118 ', 'E 146 ', 'E  70 ', 'E 106 ', 'E  66 ', 'E  38 ', 'E  95 ', 'E 212 ', 'E 196 ', 'E 158 ', 'E 180 ', 'E 110 ', 'E  26 ', 'E  78 ', 'E 239 ', 'E 174 ', 'E 230 ', 'E  89 ', 'E  47 ', 'E  24 ', 'E 166 ', 'E 133 ', 'E 222 ', 'E 150 ', 'E  80 ', 'E 147 ', 'E  71 ', 'E  49 ', 'E  39 ', 'E 117 ', 'E  55 ', 'E 195 ', 'E  65 ', 'E 107 ', 'E  25 ', 'E 181 ', 'E 177 ', 'E  79 ', 'E  41 ', 'E 134 ', 'E  30 ', 'E 201 ', 'E 122 ', 'E  88 ', 'E  46 ', 'E 225 ', 'E 242 ', 'E 188 ', 'E 167 ', 'E 231 ', 'E 157 ', 'E 209 ', 'E  92 ', 'E  72 ', 'E 241 ', 'E  48 ', 'E  52 ', 'E  83 ', 'E 116 ', 'E 148 ', 'E 100 ', 'E 125 ', 'E 176 ', 'E  40 ', 'E 217 ', 'E  31 ', 'E 221A', 'E 200 ', 'E  37 ', 'E 224 ', 'E 164 ', 'E 189 ', 'E 236 ', 'E 140 ', 'E 156 ', 'E 108 ', 'E  93 ', 'E 155 ', 'E 214 ', 'E  63 ', 'E  53 ', 'E  82 ', 'E 149 ', 'E 171 ', 'E  73 ', 'E 101 ', 'E  43 ', 'E 193 ', 'E 210 ', 'E  98 ', 'E 139 ', 'E 182 ', 'E 135 ', 'E 240 ', 'E 227 ', 'E  32 ', 'E 237 ', 'E 215 ', 'E 243 ', 'E 179 ', 'E 184A', 'E  90 ', 'E 109 ', 'E 165 ', 'E 130 ', 'E 154 ', 'E  62 ', 'E  91 ', 'E 123 ', 'E 170 ', 'E 194 ', 'E 213 ', 'E  50 ', 'E 184 ', 'E 114 ', 'E 192 ', 'E 229 ', 'E 121 ', 'E 102 ', 'E 162 ', 'E  34 ', 'E 138 ', 'E  23 ', 'E 183 ', 'E  18 ', 'E 141 ', 'E  33 ', 'E  99 ', 'E 142 ', 'E 188A', 'E 178 ', 'E 226 ', 'E  64 ', 'E 234 ', 'E  85 '])
#set([u'E  61 ', u'E 120 ', u'E  96 ', u'E 244 ', u'E 240 ', u'E 173 ', u'E  75 ', u'E 235 ', u'E 113 ', u'E  51 ', u'E  29 ', u'E 185 ', u'E  69 ', u'E 228 ', u'E  16 ', u'E 103 ', u'E 203 ', u'E 204 ', u'E  22 ', u'E  42 ', u'E  58 ', u'E 219 ', u'E 221 ', u'E 153 ', u'E  19 ', u'E 163 ', u'E 217 ', u'E  84 ', u'E 143 ', u'E  97 ', u'E 160 ', u'E  56 ', u'E 104 ', u'E  60 ', u'E 186 ', u'E 112 ', u'E  28 ', u'E  76 ', u'E 172 ', u'E  17 ', u'E 188A', u'E 136 ', u'E 168 ', u'E 212 ', u'E 216 ', u'E  45 ', u'E 191 ', u'E  59 ', u'E  21 ', u'E 232 ', u'E 220 ', u'E 211 ', u'E 132 ', u'E 152 ', u'E  87 ', u'E 124 ', u'E 144 ', u'E 199 ', u'E 137 ', u'E 161 ', u'E 119 ', u'E  57 ', u'E  86 ', u'E 159 ', u'E 245 ', u'E  67 ', u'E  94 ', u'E 105 ', u'E 238 ', u'E 128 ', u'E 175 ', u'E  77 ', u'E 197 ', u'E 202 ', u'E 169 ', u'E 111 ', u'E  27 ', u'E 123 ', u'E  44 ', u'E 190 ', u'E 129 ', u'E  20 ', u'E 233 ', u'E 151 ', u'E 127 ', u'E 145 ', u'E 198 ', u'E 223 ', u'E 243 ', u'E  54 ', u'E  81 ', u'E 118 ', u'E 146 ', u'E  70 ', u'E 106 ', u'E  66 ', u'E  38 ', u'E  95 ', u'E 174 ', u'E 196 ', u'E 158 ', u'E 180 ', u'E 110 ', u'E  26 ', u'E  78 ', u'E 239 ', u'E  37 ', u'E 230 ', u'E  89 ', u'E  47 ', u'E 166 ', u'E 133 ', u'E 222 ', u'E 150 ', u'E  80 ', u'E 147 ', u'E  71 ', u'E  49 ', u'E  39 ', u'E 117 ', u'E  55 ', u'E 195 ', u'E  65 ', u'E 107 ', u'E  25 ', u'E 181 ', u'E 177 ', u'E  79 ', u'E  41 ', u'E 134 ', u'E  30 ', u'E 201 ', u'E 122 ', u'E  88 ', u'E  46 ', u'E 225 ', u'E 242 ', u'E 188 ', u'E 167 ', u'E 130 ', u'E 157 ', u'E 209 ', u'E  92 ', u'E  72 ', u'E 241 ', u'E  48 ', u'E  52 ', u'E 231 ', u'E  83 ', u'E 116 ', u'E 148 ', u'E 100 ', u'E  64 ', u'E 176 ', u'E  40 ', u'E 194 ', u'E  31 ', u'E 221A', u'E 200 ', u'E 224 ', u'E 164 ', u'E 189 ', u'E 236 ', u'E 140 ', u'E 156 ', u'E 108 ', u'E  93 ', u'E 155 ', u'E 214 ', u'E  63 ', u'E 115 ', u'E  53 ', u'E  82 ', u'E 149 ', u'E 171 ', u'E  73 ', u'E 101 ', u'E  43 ', u'E 193 ', u'E 210 ', u'E  98 ', u'E 139 ', u'E 182 ', u'E 135 ', u'E  24 ', u'E 227 ', u'E  32 ', u'E 237 ', u'E 215 ', u'E 141 ', u'E 179 ', u'E 184A', u'E  90 ', u'E 109 ', u'E 187 ', u'E 165 ', u'E 154 ', u'E  62 ', u'E  91 ', u'E  74 ', u'E 170 ', u'E 213 ', u'E  50 ', u'E 184 ', u'E 114 ', u'E 192 ', u'E 229 ', u'E 121 ', u'E 102 ', u'E  34 ', u'E 138 ', u'E  23 ', u'E 183 ', u'E  18 ', u'E  33 ', u'E  99 ', u'E 142 ', u'E 125 ', u'E 178 ', u'E 226 ', u'E 162 ', u'E 234 ', u'E  85 '])




        # atom_to_seqres_sequence_maps
        for chain_id, sequence_map in self.atom_to_seqres_sequence_maps.iteritems():
            # Check that all ATOM residues have a mapping
            #print(sorted(sequence_map.keys()))
            #print(sorted(self.atom_sequences[chain_id].ids()))
            assert(sorted(sequence_map.keys()) == sorted(self.atom_sequences[chain_id].ids()))

            # Check that all SEQRES residues in the mapping exist and that the mapping is injective
            rng = set(sequence_map.values())
            seqres_residue_ids = set(self.seqres_sequences[chain_id].ids())
            assert(rng.intersection(seqres_residue_ids) == rng)
            assert(len(rng) == len(sequence_map.values()))

        #if not(self.restrict_match_percentage_errors_to_these_uniparc_ids) or (UniParcID and (UniParcID in self.restrict_match_percentage_errors_to_these_uniparc_ids)):
        colortext.porange('HERE')
        pprint.pprint(self.restrict_match_percentage_errors_to_these_uniparc_ids)
        pprint.pprint(self.pdb_chain_to_uniparc_chain_mapping)
        pprint.pprint(self.seqres_to_uniparc_sequence_maps)
        colortext.porange('THERE')

        # seqres_to_uniparc_sequence_maps
        for chain_id, sequence_map in sorted(self.seqres_to_uniparc_sequence_maps.iteritems()):

            mapped_uniparc_id = self.pdb_chain_to_uniparc_chain_mapping.get(chain_id)
            related_uniparc_ids = set()
            if mapped_uniparc_id:
                related_uniparc_ids.add(mapped_uniparc_id)
            for seqres_res_id, uniparc_res_id, substitution_scores in sequence_map:
                if self.restrict_match_percentage_errors_to_these_uniparc_ids and (uniparc_res_id[0] not in self.restrict_match_percentage_errors_to_these_uniparc_ids):
                    related_uniparc_ids.add(uniparc_res_id[0])

            # If self.restrict_match_percentage_errors_to_these_uniparc_ids is set then we skip checking any chains which have no associated residues
            if self.restrict_match_percentage_errors_to_these_uniparc_ids:
                if len(self.restrict_match_percentage_errors_to_these_uniparc_ids.intersection(related_uniparc_ids)) == 0:
                    continue

            # Check that acceptable_sequence_percentage_match% of all SEQRES residues have a mapping (there may have been
            # insertions or bad mismatches i.e. low BLOSUM62/PAM250 scores). I chose 80% arbitrarily but this can be overridden
            #  with the acceptable_sequence_percentage_match argument to the constructor.
            if self.sequence_types[chain_id] == 'Protein' or self.sequence_types[chain_id] == 'Protein skeleton':
                if sequence_map:
                    mapped_SEQRES_residues = set(sequence_map.keys())
                    all_SEQRES_residues = set(self.seqres_sequences[chain_id].ids())

                    # If restrict_match_percentage_errors_to_these_uniparc_ids is set and this chain contains some residues*
                    # associated with those UniParc IDs then we only want to consider residues which have mappings to those
                    # UniParc IDs. It seems more informative to throw away residues rather than chains - this lets us
                    # handle or flag chimeric chains among other cases.
                    #
                    # We should therefore disregard any residues which do not map to our list of UniParc IDs *and which are mismatches*
                    # i.e. if the match was correct, we do not disregard it - this helps to keep the match_percentage up.
                    #
                    # As substitution_scores is not always provided, we test using the Sequence objects:
                    #     1. num_disregarded_residues := the number of residues which do not map to restrict_match_percentage_errors_to_these_uniparc_ids *and* which are mismatches
                    #     2. match_percentage := 100.0 * (float(len(mapped_SEQRES_residues) - num_disregarded_residues)/float(len(all_SEQRES_residues) - num_disregarded_residues))
                    #
                    # * Otherwise, we skipped this chain above.
                    num_disregarded_residues = 0
                    for seqres_res_id, uniparc_res_id, substitution_scores in sequence_map:
                        if self.restrict_match_percentage_errors_to_these_uniparc_ids and (uniparc_res_id[0] not in self.restrict_match_percentage_errors_to_these_uniparc_ids):
                            if self.uniparc_sequences[uniparc_res_id[0]][uniparc_res_id[1]].ResidueAA != self.seqres_sequences[chain_id][seqres_res_id].ResidueAA:
                                num_disregarded_residues += 1

                    if len(all_SEQRES_residues) >= 20:
                        # old code: match_percentage = 100.0 * (float(len(mapped_SEQRES_residues))/float(len(all_SEQRES_residues)))
                        match_percentage = 100.0 * (float(len(mapped_SEQRES_residues) - num_disregarded_residues)/float(len(all_SEQRES_residues) - num_disregarded_residues))

                        # In some cases, the SEQRES sequences are longer than the UniParc sequences e.g. 1AHW. In these cases, we
                        # would consider the percentage residues matched based on the percentage of the UniParc sequence that was
                        # matched rather than the length of the SEQRES sequence.
                        # todo: this code is duplicated in sifts.py; we should compute this once (in sifts.py)
                        uniparc_sequence_counts = {}
                        for pc_id, up_tpl, sub_score in sequence_map:
                            uniparc_sequence_counts[up_tpl[0]] = uniparc_sequence_counts.get(up_tpl[0], set())
                            uniparc_sequence_counts[up_tpl[0]].add(up_tpl[1])
                        if len(uniparc_sequence_counts) == 1:
                            matched_uniparc_id = uniparc_sequence_counts.keys()[0]
                            num_matched_uniparc_id_residues = len(uniparc_sequence_counts[matched_uniparc_id])
                            match_percentage_2 = max(match_percentage, float(num_matched_uniparc_id_residues)*100.0/float(len(self.uniparc_sequences[matched_uniparc_id])))
                            print('num_matched_uniparc_id_residues', num_matched_uniparc_id_residues)
                            print('len(self.uniparc_sequences[matched_uniparc_id])', matched_uniparc_id, len(self.uniparc_sequences[matched_uniparc_id]))
                            print(match_percentage_2)
                            match_percentage = max(match_percentage, match_percentage_2)




                        if not (self.acceptable_sequence_percentage_match <= match_percentage <= 100.0):
                            if not set(list(str(self.seqres_sequences[chain_id]))) == set(['X']):
                                # Skip cases where all residues are unknown e.g. 1DEQ, chain M
                                if self.sifts_exception:
                                    raise self.sifts_exception
                                else:
                                    raise Exception("Chain %s in %s only had a match percentage of %0.2f%%. self.acceptable_sequence_percentage_match is set to %0.2f%%." % (chain_id, self.pdb_id, match_percentage, self.acceptable_sequence_percentage_match))

            # Check that all UniParc residues in the mapping exist and that the mapping is injective
            if self.pdb_chain_to_uniparc_chain_mapping.get(chain_id):
                rng = set([v[1] for v in sequence_map.values()])
                uniparc_chain_id = self.pdb_chain_to_uniparc_chain_mapping[chain_id]
                uniparc_residue_ids = set(self.uniparc_sequences[uniparc_chain_id].ids())
                assert(rng.intersection(uniparc_residue_ids) == rng)
                if len(rng) != len(sequence_map.values()):
                    rng_vals = set()
                    for x in sequence_map.values():
                        if x[1] in rng_vals:
                            err_msg = ['The SEQRES to UniParc map is not injective for %s, chain %s; the element %s occurs more than once in the range.' % (self.pdb_id, chain_id, str(x))]

                            err_msg.append(colortext.make('The seqres_to_uniparc_sequence_maps mapping is:', color = 'green'))
                            for k, v in sequence_map.map.iteritems():
                                err_msg.append(' %s -> %s' % (str(k).ljust(7), str(v).ljust(20)))

                            err_msg.append(colortext.make('The clustal_seqres_to_uniparc_sequence_maps mapping is:', color = 'green'))
                            for k, v in self.clustal_seqres_to_uniparc_sequence_maps[chain_id].map.iteritems():
                                err_msg.append(' %s -> %s' % (str(k).ljust(7), str(v).ljust(20)))

                            err_msg.append(colortext.make('The sifts_seqres_to_uniparc_sequence_maps mapping is:', color = 'green'))
                            for k, v in self.sifts_seqres_to_uniparc_sequence_maps[chain_id].map.iteritems():
                                err_msg.append(' %s -> %s' % (str(k).ljust(7), str(v).ljust(20)))

                            if self.strict:
                                raise Exception('\n'.join(err_msg))
                            else:
                                self.uniparc_maps_are_injective = False
                        rng_vals.add(x[1])


    def _validate_id_types(self):
        '''Check that the ID types are integers for Rosetta, SEQRES, and UniParc sequences and 6-character PDB IDs for the ATOM sequences.'''

        for sequences in [self.uniparc_sequences, self.fasta_sequences, self.seqres_sequences, self.rosetta_sequences]:
            for chain_id, sequence in sequences.iteritems():
                sequence_id_types = set(map(type, sequence.ids()))
                if sequence_id_types:
                    assert(len(sequence_id_types) == 1)
                    assert(sequence_id_types.pop() == types.IntType)

        for chain_id, sequence in self.atom_sequences.iteritems():
            sequence_id_types = set(map(type, sequence.ids()))
            assert(len(sequence_id_types) == 1)
            sequence_id_type = sequence_id_types.pop()
            assert(sequence_id_type == types.StringType or sequence_id_type == types.UnicodeType)


    def _validate_residue_types(self):
        '''Make sure all the residue types map through translation.'''

        for chain_id, sequence_map in self.rosetta_to_atom_sequence_maps.iteritems():
            rosetta_sequence = self.rosetta_sequences[chain_id]
            atom_sequence = self.atom_sequences[chain_id]
            for rosetta_id, atom_id, _ in sequence_map:
                assert(rosetta_sequence[rosetta_id].ResidueAA == atom_sequence[atom_id].ResidueAA)

        for chain_id, sequence_map in self.atom_to_seqres_sequence_maps.iteritems():
            atom_sequence = self.atom_sequences[chain_id]
            seqres_sequence = self.seqres_sequences[chain_id]
            for atom_id, seqres_id, _ in sorted(sequence_map):
                assert(atom_sequence[atom_id].ResidueAA == seqres_sequence[seqres_id].ResidueAA)

        for chain_id, sequence_map in self.seqres_to_uniparc_sequence_maps.iteritems():
            if self.pdb_chain_to_uniparc_chain_mapping.get(chain_id):
                seqres_sequence = self.seqres_sequences[chain_id]
                uniparc_sequence = self.uniparc_sequences[self.pdb_chain_to_uniparc_chain_mapping[chain_id]]
                for seqres_id, uniparc_id_resid_pair, substitution_match in sequence_map:
                    uniparc_id = uniparc_id_resid_pair[1]
                    # Some of the matches may not be identical but all the '*' Clustal Omega matches should be identical
                    if substitution_match and substitution_match.clustal == 1:
                        assert(seqres_sequence[seqres_id].ResidueAA == uniparc_sequence[uniparc_id].ResidueAA)

    ### Private Sequence and SequenceMap collection functions ###

    def _create_inverse_maps(self):
        '''Create the inverse mappings (UniParc -> SEQRES -> ATOM -> Rosetta).'''

        # We have already determined that the inverse maps are well-defined (the normal maps are injective). The inverse maps will be partial maps in general.

        self.atom_to_rosetta_sequence_maps = {}
        for chain_id, sequence_map in self.rosetta_to_atom_sequence_maps.iteritems():
            s = SequenceMap()
            for k, v, substitution_match in sequence_map:
                s.add(v, k, substitution_match)
            self.atom_to_rosetta_sequence_maps[chain_id] = s

        self.seqres_to_atom_sequence_maps = {}
        for chain_id, sequence_map in self.atom_to_seqres_sequence_maps.iteritems():
            s = SequenceMap()
            for k, v, substitution_match in sequence_map:
                s.add(v, k, substitution_match)
            self.seqres_to_atom_sequence_maps[chain_id] = s

        # This map uses PDB chain IDs as PDB chains may map to zero or one UniParc IDs whereas UniParc IDs may map to many PDB chains
        self.uniparc_to_seqres_sequence_maps = {}
        for chain_id, sequence_map in self.seqres_to_uniparc_sequence_maps.iteritems():
            s = UniParcPDBSequenceMap()
            for k, v, substitution_match in sequence_map:
                s.add(v, k, substitution_match)
            self.uniparc_to_seqres_sequence_maps[chain_id] = s

    def _create_sequence_maps(self):
        '''Get all of the SequenceMaps - Rosetta->ATOM, ATOM->SEQRES/FASTA, SEQRES->UniParc.'''

        if self.sifts:
            self.sifts_atom_to_seqres_sequence_maps = self.sifts.atom_to_seqres_sequence_maps
            self.sifts_seqres_to_uniparc_sequence_maps = self.sifts.seqres_to_uniparc_sequence_maps
            self.sifts_atom_to_uniparc_sequence_maps = self.sifts.atom_to_uniparc_sequence_maps
            if self.pdb_id in pdbs_with_do_not_use_SIFTS_for_these_chains:
                for chain_id in self.sifts_atom_to_seqres_sequence_maps.keys() + self.sifts_seqres_to_uniparc_sequence_maps.keys() + self.sifts_atom_to_uniparc_sequence_maps.keys():
                    if (self.pdb_id, chain_id) in do_not_use_SIFTS_for_these_chains:
                        self.sifts_atom_to_seqres_sequence_maps[chain_id] = SequenceMap()
                        self.sifts_seqres_to_uniparc_sequence_maps = SequenceMap()
                        self.sifts_atom_to_uniparc_sequence_maps = SequenceMap()

        if self.pdb_to_rosetta_residue_map_error:
            self.rosetta_to_atom_sequence_maps = {}
            for c in self.atom_sequences.keys():
                self.rosetta_to_atom_sequence_maps[c] = SequenceMap()
        else:
            self.rosetta_to_atom_sequence_maps = self.pdb.rosetta_to_atom_sequence_maps

        # If we removed atoms from the PDB file, we need to remove them from the maps so that our validations hold later on
        self.pdbml_atom_to_seqres_sequence_maps = self.pdbml.atom_to_seqres_sequence_maps
        if self.pdb_id in ROSETTA_HACKS_residues_to_remove:
            for residue_to_remove in ROSETTA_HACKS_residues_to_remove[self.pdb_id]:
                chain_id = residue_to_remove[0]
                self.pdbml_atom_to_seqres_sequence_maps[chain_id].remove(residue_to_remove)
                #if self.sifts:
                #    self.sifts_atom_to_seqres_sequence_maps[chain_id].remove(residue_to_remove)

        if self.pdb_id not in do_not_use_the_sequence_aligner:
            self.clustal_seqres_to_uniparc_sequence_maps = self.PDB_UniParc_SA.seqres_to_uniparc_sequence_maps

    def _merge_sifts_maps(self):
        ''' Make sure that the pdbml_atom_to_seqres_sequence_maps and clustal_seqres_to_uniparc_sequence_maps agree with SIFTS and merge the maps.
                SIFTS may have more entries since we discard PDB residues which break Rosetta.
                SIFTS may have less entries for some cases e.g. 1AR1, chain C where SIFTS does not map ATOMs 99-118.
                SIFTS does not seem to contain ATOM to SEQRES mappings for (at least some) DNA chains e.g. 1APL, chain A
            Because of these cases, we just assert that the overlap agrees so that we can perform a gluing of maps.'''

        if self.pdb_id in do_not_use_the_sequence_aligner:
            assert(self.sifts)
            self.atom_to_seqres_sequence_maps = self.sifts_atom_to_seqres_sequence_maps
            self.seqres_to_uniparc_sequence_maps = self.sifts_seqres_to_uniparc_sequence_maps
        elif self.sifts:
            self.atom_to_seqres_sequence_maps = {}
            self.seqres_to_uniparc_sequence_maps = {}
            for c, seqmap in sorted(self.pdbml_atom_to_seqres_sequence_maps.iteritems()):
                if self.sequence_types[c] == 'Protein' or self.sequence_types[c] == 'Protein skeleton':
                    try:
                        if self.sifts_atom_to_seqres_sequence_maps.get(c):
                            assert(self.pdbml_atom_to_seqres_sequence_maps[c].matches(self.sifts_atom_to_seqres_sequence_maps[c]))
                            self.atom_to_seqres_sequence_maps[c] = self.pdbml_atom_to_seqres_sequence_maps[c] + self.sifts_atom_to_seqres_sequence_maps[c]
                        else:
                            self.atom_to_seqres_sequence_maps[c] = self.pdbml_atom_to_seqres_sequence_maps[c]
                    except Exception, e:
                        raise colortext.Exception("Mapping cross-validation failed checking atom to seqres sequence maps between PDBML and SIFTS in %s, chain %s: %s" % (self.pdb_id, c, str(e)))
                else:
                    self.atom_to_seqres_sequence_maps[c] = seqmap

            for c, seqmap in sorted(self.clustal_seqres_to_uniparc_sequence_maps.iteritems()):
                if self.sequence_types[c] == 'Protein' or self.sequence_types[c] == 'Protein skeleton':
                    if (self.pdb_id, c) in use_SIFTS_match_for_seqres_sequence:
                        #assert(seqres_sequence[seqres_id].ResidueAA == uniparc_sequence[uniparc_id].ResidueAA)
                        if (self.pdb_id, c) not in known_bad_clustal_to_sifts_mappings:
                            # Flag cases for manual inspection
                            assert(self.clustal_seqres_to_uniparc_sequence_maps[c].keys() == self.sifts_seqres_to_uniparc_sequence_maps[c].keys())
                        for k in self.clustal_seqres_to_uniparc_sequence_maps[c].keys():
                            v_1 = self.clustal_seqres_to_uniparc_sequence_maps[c][k]
                            v_2 = self.sifts_seqres_to_uniparc_sequence_maps[c][k]

                            if (self.pdb_id, c) not in known_bad_clustal_to_sifts_mappings and v_2:
                                # Make sure the UniParc IDs agree
                                assert(v_1[0] == v_2[0])

                            if (self.pdb_id, c) not in known_bad_clustal_to_sifts_mappings:
                                # Make sure the residue types agree
                                assert(self.uniparc_sequences[v_1[0]][v_1[1]].ResidueAA == self.uniparc_sequences[v_1[0]][v_2[1]].ResidueAA)

                                # Copy the substitution scores over. Since the residue types agree, this is valid
                                self.sifts_seqres_to_uniparc_sequence_maps[c].substitution_scores[k] = self.clustal_seqres_to_uniparc_sequence_maps[c].substitution_scores[k]

                        self.clustal_seqres_to_uniparc_sequence_maps[c] = self.sifts_seqres_to_uniparc_sequence_maps[c]

                    try:
                        if self.sifts_seqres_to_uniparc_sequence_maps.get(c):

                            print('self.sifts_seqres_to_uniparc_sequence_maps', c)
                            pprint.pprint(self.sifts_seqres_to_uniparc_sequence_maps[c])
                            print('self.clustal_seqres_to_uniparc_sequence_maps[c]', c)
                            pprint.pprint(self.clustal_seqres_to_uniparc_sequence_maps[c])


                            if not self.clustal_seqres_to_uniparc_sequence_maps[c].matches(self.sifts_seqres_to_uniparc_sequence_maps[c]):
                                mismatched_keys = self.clustal_seqres_to_uniparc_sequence_maps[c].get_mismatches(self.sifts_seqres_to_uniparc_sequence_maps[c])
                                if self.trust_sifts:
                                    colortext.warning("self.clustal_seqres_to_uniparc_sequence_maps[c].matches(self.sifts_seqres_to_uniparc_sequence_maps[c])")
                                    self.seqres_to_uniparc_sequence_maps[c] = self.sifts_seqres_to_uniparc_sequence_maps[c]
                                else:
                                    raise Exception("self.clustal_seqres_to_uniparc_sequence_maps[c].matches(self.sifts_seqres_to_uniparc_sequence_maps[c])")
                            else:
                                self.seqres_to_uniparc_sequence_maps[c] = self.clustal_seqres_to_uniparc_sequence_maps[c] + self.sifts_seqres_to_uniparc_sequence_maps[c]
                        else:
                            self.seqres_to_uniparc_sequence_maps[c] = self.clustal_seqres_to_uniparc_sequence_maps[c]
                    except Exception, e:
                        colortext.warning(traceback.format_exc())
                        colortext.error(str(e))
                        raise ClustalSIFTSCrossValidationException(colortext.mred("Mapping cross-validation failed checking atom to seqres sequence maps between Clustal and SIFTS in %s, chain %s." % (self.pdb_id, c)))
                else:
                    self.clustal_seqres_to_uniparc_sequence_maps[c] = seqmap
        else:
            self.atom_to_seqres_sequence_maps = self.pdbml_atom_to_seqres_sequence_maps
            self.seqres_to_uniparc_sequence_maps = self.clustal_seqres_to_uniparc_sequence_maps

    def _prune_maps_to_sequences(self):
        ''' When we merge the SIFTS maps, we can extend the sequence maps such that they have elements in their domain that we removed
            from the sequence e.g. 1A2P, residue 'B   3 ' is removed because Rosetta barfs on it. Here, we prune the maps so that their
            domains do not have elements that were removed from sequences.'''

        for c, seq in self.atom_sequences.iteritems():
            res_ids = [r[0] for r in seq]
            for_removal = []
            for k, _, _ in self.atom_to_seqres_sequence_maps[c]:
                if k not in res_ids:
                    for_removal.append(k)
            for res_id in for_removal:
                self.atom_to_seqres_sequence_maps[c].remove(res_id)



        #print(self.fasta_sequences)
        #print(self.seqres_sequences)

        #self.atom_to_seqres_sequence_maps = None
        #self.seqres_to_uniparc_sequence_maps = None

        #self.pdbml_atom_to_seqres_sequence_maps = None
        #self.clustal_seqres_to_uniparc_sequence_maps = None

        #self.sifts_atom_to_seqres_sequence_maps = None
        #self.sifts_seqres_to_uniparc_sequence_maps = None
        #self.sifts_atom_to_uniparc_sequence_maps = None

    def _create_sequences(self):
        '''Get all of the Sequences - Rosetta, ATOM, SEQRES, FASTA, UniParc.'''

        # Create the Rosetta sequences and the maps from the Rosetta sequences to the ATOM sequences
        try:
            self.pdb.construct_pdb_to_rosetta_residue_map(self.rosetta_scripts_path, rosetta_database_path = self.rosetta_database_path, cache_dir = self.cache_dir, extra_command_flags = self.extra_rosetta_mapping_command_flags)
        except PDBMissingMainchainAtomsException:
            self.pdb_to_rosetta_residue_map_error = True

        # Get all the Sequences
        if self.pdb_id not in do_not_use_the_sequence_aligner:
            self.uniparc_sequences = self.PDB_UniParc_SA.uniparc_sequences
        else:
            self.uniparc_sequences = self.sifts.get_uniparc_sequences()

        self.fasta_sequences = self.FASTA.get_sequences(self.pdb_id)
        self.seqres_sequences = self.pdb.seqres_sequences
        self.atom_sequences = self.pdb.atom_sequences

        if self.pdb_to_rosetta_residue_map_error:
            self.rosetta_sequences = {}
            for c in self.atom_sequences.keys():
                self.rosetta_sequences[c] = Sequence()
        else:
            self.rosetta_sequences = self.pdb.rosetta_sequences

        # Update the chain types for the UniParc sequences
        uniparc_pdb_chain_mapping = {}
        if self.pdb_id not in do_not_use_the_sequence_aligner:
            for pdb_chain_id, matches in self.PDB_UniParc_SA.clustal_matches.iteritems():
                if matches:
                    # we are not guaranteed to have a match e.g. the short chain J in 1A2C, chimeras, etc.
                    uniparc_chain_id = matches.keys()[0]
                    assert(len(matches) == 1)
                    uniparc_pdb_chain_mapping[uniparc_chain_id] = uniparc_pdb_chain_mapping.get(uniparc_chain_id, [])
                    uniparc_pdb_chain_mapping[uniparc_chain_id].append(pdb_chain_id)
        else:
            for pdb_chain_id, uniparc_chain_ids in self.sifts.get_pdb_chain_to_uniparc_id_map().iteritems():
                for uniparc_chain_id in uniparc_chain_ids:
                    uniparc_pdb_chain_mapping[uniparc_chain_id] = uniparc_pdb_chain_mapping.get(uniparc_chain_id, [])
                    uniparc_pdb_chain_mapping[uniparc_chain_id].append(pdb_chain_id)

        for uniparc_chain_id, pdb_chain_ids in uniparc_pdb_chain_mapping.iteritems():
            sequence_type = set([self.seqres_sequences[p].sequence_type for p in pdb_chain_ids])
            assert(len(sequence_type) == 1)
            sequence_type = sequence_type.pop()
            assert(self.uniparc_sequences[uniparc_chain_id].sequence_type == None)
            self.uniparc_sequences[uniparc_chain_id].set_type(sequence_type)
            for p in pdb_chain_ids:
                self.pdb_chain_to_uniparc_chain_mapping[p] = uniparc_chain_id

        # Update the chain types for the FASTA sequences
        for chain_id, sequence in self.seqres_sequences.iteritems():
            self.fasta_sequences[chain_id].set_type(sequence.sequence_type)


    ### Private object creation functions ###

    def _create_objects(self, chains_to_keep, starting_clustal_cut_off, min_clustal_cut_off, strip_HETATMS):

        pdb_id = self.pdb_id
        assert(20 <= min_clustal_cut_off <= starting_clustal_cut_off <= 100)

        # Create the FASTA object
        if not self.silent:
            colortext.message("Creating the FASTA object.")
        try:
            if self.bio_cache:
                self.FASTA = self.bio_cache.get_fasta_object(pdb_id)
            else:
                self.FASTA = FASTA.retrieve(pdb_id, cache_dir = self.cache_dir)
        except:
            raise colortext.Exception("Relatrix construction failed creating the FASTA object for %s.\n%s" % (pdb_id, traceback.format_exc()))

        # Create the PDB object
        if not self.silent:
            colortext.message("Creating the PDB object.")
        try:
            if self.bio_cache:
                self.pdb = self.bio_cache.get_pdb_object(pdb_id)
            else:
                self.pdb = PDB.retrieve(pdb_id, cache_dir = self.cache_dir)
            if chains_to_keep:
                self.pdb.strip_to_chains(chains_to_keep)
            if strip_HETATMS:
                self.pdb.strip_HETATMs()
        except:
            raise colortext.Exception("Relatrix construction failed creating the PDB object for %s.\n%s" % (pdb_id, traceback.format_exc()))

        # Copy PDB properties
        if self.pdb.deprecated:
            self.replacement_pdb_id = self.pdb.replacement_pdb_id

        self.sequence_types = self.pdb.chain_types

        # todo: benchmark why PDBML creation is slow for some files e.g. 3ZKB.xml (lots of repeated chains)
        # Create the PDBML object
        if not self.silent:
            colortext.message("Creating the PDBML object.")
        try:
            if self.bio_cache:
                self.pdbml = self.bio_cache.get_pdbml_object(pdb_id)
            else:
                self.pdbml = PDBML.retrieve(pdb_id, cache_dir = self.cache_dir, bio_cache = self.bio_cache)
        except MissingPDBMLException, e:
            raise # cascade
        except:
            raise colortext.Exception("Relatrix construction failed creating the PDBML object for %s.\n%s" % (pdb_id, traceback.format_exc()))

        # Copy PDBML properties
        if self.pdbml.deprecated:
            if self.replacement_pdb_id:
                assert(self.replacement_pdb_id == self.pdbml.replacement_pdb_id)
            else:
                self.replacement_pdb_id = self.pdbml.replacement_pdb_id

        # Create the SIFTS object
        try:
            if self.bio_cache:
                # Warning: restrict_match_percentage_errors_to_these_uniparc_ids may not have been passed if the object was previously created
                #          we could extend the cache to store constructor attributes with objects so we could store multiple copies of a SIFTS
                #          object for a given PDB ID where the attributes (e.g. restrict_match_percentage_errors_to_these_uniparc_ids) differ.
                self.sifts = self.bio_cache.get_sifts_object(pdb_id, acceptable_sequence_percentage_match  = self.acceptable_sifts_sequence_percentage_match, restrict_match_percentage_errors_to_these_uniparc_ids = self.restrict_match_percentage_errors_to_these_uniparc_ids)
            else:
                self.sifts = SIFTS.retrieve(pdb_id, cache_dir = self.cache_dir, acceptable_sequence_percentage_match = self.acceptable_sifts_sequence_percentage_match, restrict_match_percentage_errors_to_these_uniparc_ids = self.restrict_match_percentage_errors_to_these_uniparc_ids)
        except MissingSIFTSRecord, e:
            self.sifts_exception = e
            colortext.warning("No SIFTS entry was found for %s." % pdb_id)
        except BadSIFTSMapping, e:
            self.sifts_exception = e
            colortext.warning("The SIFTS mapping for %s was considered a bad mapping at the time of writing." % pdb_id)
        except NoSIFTSPDBUniParcMapping, e:
            self.sifts_exception = e
            colortext.warning("The PDB file %s has a known bad SIFTS mapping at the time of writing." % pdb_id)

        # Create the PDBUniParcSequenceAligner object. We try the best alignment at first (100%) and then fall back to more relaxed alignments down to min_clustal_cut_off percent.
        if not self.silent:
            colortext.message("Creating the PDB to UniParc SequenceAligner object.")
        cut_off = 0
        try:
            matched_chains = set()
            matched_all_chains = False
            self.PDB_UniParc_SA = None

            if self.pdb_id not in do_not_use_the_sequence_aligner:
                cut_off = None
                for x in range(starting_clustal_cut_off, min_clustal_cut_off - 1, -1):
                    cut_off = x
                    if not self.silent:
                        colortext.warning("\tTrying to align sequences with a cut-off of %d%%." % cut_off)

                    if not self.PDB_UniParc_SA:
                        # Initialize the PDBUniParcSequenceAligner the first time through
                        self.PDB_UniParc_SA = PDBUniParcSequenceAligner(pdb_id, cache_dir = self.cache_dir, cut_off = cut_off, sequence_types = self.sequence_types, replacement_pdb_id = self.replacement_pdb_id, added_uniprot_ACs = self.pdb.get_UniProt_ACs(), restrict_to_uniparc_values = self.restrict_to_uniparc_values)
                    else:
                        # We have already retrieved the UniParc entries. We just need to try the mapping again. This saves
                        # lots of time for entries with large numbers of UniProt entries e.g. 1HIO even if disk caching is used.
                        # We also stop trying to match a chain once a match has been found in a previous iteration.
                        # This speeds up the matching in multiple ways. First, we do not waste time by recreating the same UniParcEntry.
                        # Next, we do not waste time rematching chains we previously matched. Finally, we only match equivalence
                        # classes of chains where the equivalence is defined as having an identical sequence.
                        # For example we sped up:
                        #   matching 1YGV (3 protein chains, 2 identical) starting at 100% by 67% (down from 86s to 28.5s with a match at 85%); (this case may be worth profiling)
                        #       speed ups at each stage; not recreating PDB_UniParc_SA (due to low match%), only matching chains once (as A, C are found at 95%), and skipping sequence-equivalent chains (as A and C have the same sequence)
                        #   matching 1HIO (4 protein chains, all unique) starting at 100% by 83% down from 33s to 5.5s (match at 95%);
                        #       main speed-up due to not recreating PDB_UniParc_SA
                        #   matching 1H38 (4 identical protein chains) starting at 100% by 5% down from 57s to 54s (match at 100%);
                        #       no real speed-up since the match is at 100%
                        #   matching the extreme case 487D (7 protein chains, all unique) starting at 100% by 94% down from 1811s to 116s (with a min_clustal_cut_off of 71%). A lot of the time in this case is in constructing the UniParcEntry object.
                        #       main speed-up due to not recreating PDB_UniParc_SA
                        #   matching 3ZKB (16 protein chains, all identical) starting at 100% by 90% (down from 31s to 3s with a match at 98%); (this case may be worth profiling)
                        #       a lot of time was spent in PDBML creation (another optimization problem) so I only profiled this PDB_UniParc_SA section
                        #       minor speed-up (31s to 27s) by not recreating PDB_UniParc_SA (match at 98%), main speed-up due to skipping sequence-equivalent chain (we only have to match one sequence)
                        self.PDB_UniParc_SA.realign(cut_off, chains_to_skip = matched_chains)

                    # We only care about protein chain matches so early out as soon as we have them all matched
                    protein_chain_matches = {}
                    for _c, _st in self.sequence_types.iteritems():
                        if _st == 'Protein' or _st == 'Protein skeleton':
                            protein_chain_matches[_c] = self.PDB_UniParc_SA.clustal_matches[_c]
                            if protein_chain_matches[_c]:
                                matched_chains.add(_c)

                    num_matches_per_chain = set(map(len, protein_chain_matches.values()))
                    if len(num_matches_per_chain) == 1 and num_matches_per_chain.pop() == 1:
                        # We have exactly one match per protein chain. Early out.
                        if not self.silent:
                            colortext.message("\tSuccessful match with a cut-off of %d%%." % cut_off)
                        matched_all_chains = True
                        self.alignment_cutoff = cut_off
                        break
                    else:
                        # We have ambiguity - more than one match per protein chain. Exception.
                        if [n for n in num_matches_per_chain if n > 1]:
                            raise MultipleAlignmentException("Too many matches found at cut-off %d." % cut_off)

                if not matched_all_chains:
                    protein_chains = [c for c in self.sequence_types if self.sequence_types[c].startswith('Protein')]

                    if not self.silent:
                        colortext.warning('\nNote: Not all chains were matched:')
                        for c in protein_chains:
                            if protein_chain_matches.get(c):
                                colortext.message('  %s matched %s' % (c, protein_chain_matches[c]))
                            else:
                                colortext.warning('  %s was not matched' % c)
                        print('')

                    num_matches_per_chain = set(map(len, self.PDB_UniParc_SA.clustal_matches.values()))
                    if num_matches_per_chain == set([0, 1]):
                        # We got matches but are missing chains
                        self.alignment_cutoff = cut_off
        except MultipleAlignmentException, e:
            # todo: this will probably fail with DNA or RNA so do not include those in the alignment
            colortext.error(str(e))
            colortext.error(traceback.format_exc())
            colortext.error("Relatrix construction failed creating the PDBUniParcSequenceAligner object for %s. The cut-off level reached %d%% without finding a match for all chains but at that level, the mapping from chains to UniParc IDs was not injective.\n%s" % (pdb_id, cut_off, str(e)))
            colortext.error('''This seems like an ambiguous cases e.g. 1M9D chain C (and D) matches UPI000217CB5A and UPI0000106BB1 and the sequence of those UniParc entries is identical in the range where 1M9D matches.\n''' +
                            '''We cannot tell which match is "better" by sequence alone. Here, we rely on external sources like SIFTS which provide an unambiguous match (UPI000217CB5A).\n''' +
                            '''Example code for handling these errors:\n\n''' +
                            '''    try:\n''' +
                            '''        rr = ResidueRelatrix(pdb_id, '/some/path/rosetta_scripts.linuxgccrelease', None, min_clustal_cut_off = 90, cache_dir = self.cache_dir, bio_cache = self.bio_cache)\n''' +
                            '''    except MultipleAlignmentException, e:\n''' +
                            '''        restrict_to_uniparc_values = [get the correct UniParc entries from some source e.g. SIFTS]\n''' +
                            '''        rr = ResidueRelatrix(pdb_id, '/some/path/rosetta_scripts.linuxgccrelease', None, min_clustal_cut_off = 90, cache_dir = self.cache_dir, bio_cache = self.bio_cache, restrict_to_uniparc_values = restrict_to_uniparc_values)\n''')
            raise
        except:
            raise colortext.Exception("Relatrix construction failed creating the PDBUniParcSequenceAligner object for %s.\n%s" % (pdb_id, traceback.format_exc()))
