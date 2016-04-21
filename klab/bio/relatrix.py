#!/usr/bin/python
# encoding: utf-8
"""
relatrix.py
A class for relating residues using Rosetta numbering, PDB ATOM numbering, SEQRES/FASTA sequences, and UniParc sequences.

Created by Shane O'Connor 2013
"""

import types
import traceback

from fasta import FASTA
from pdb import PDB, PDBMissingMainchainAtomsException, ROSETTA_HACKS_residues_to_remove
from pdbml import PDBML
from clustalo import PDBUniParcSequenceAligner, MultipleAlignmentException
from klab import colortext
from basics import Sequence, SequenceMap, UniParcPDBSequenceMap
from sifts import SIFTS, MissingSIFTSRecord, BadSIFTSMapping, NoSIFTSPDBUniParcMapping

use_seqres_sequence_for_fasta_sequence = set(['1A2C', '4CPA', '2ATC', '1OLR'])
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



class ResidueRelatrix(object):
    ''' A class for relating residue IDs from different schemes.
        Note: we assume throughout that there is one map from SEQRES to UniParc. This is not always true e.g. Polyubiquitin-C (UPI000000D74D) has 9 copies of the ubiquitin sequence.'''

    schemes = ['rosetta', 'atom', 'seqres', 'fasta', 'uniparc']

    def __init__(self, pdb_id, rosetta_scripts_path, rosetta_database_path = None, chains_to_keep = [], min_clustal_cut_off = 80, cache_dir = None, silent = False, acceptable_sequence_percentage_match = 80.0, acceptable_sifts_sequence_percentage_match = None, starting_clustal_cut_off = 100, bio_cache = None): # keep_HETATMS = False
        ''' acceptable_sequence_percentage_match is used when checking whether the SEQRES sequences have a mapping. Usually
            90.00% works but some cases e.g. 1AR1, chain C, have a low matching score mainly due to extra residues. I set
            this to 80.00% to cover most cases.'''

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
        if (not self.cache_dir) and self.bio_cache:
            self.cache_dir = self.bio_cache.cache_dir

        self.alignment_cutoff = None
        self.acceptable_sequence_percentage_match = acceptable_sequence_percentage_match
        self.acceptable_sifts_sequence_percentage_match = acceptable_sifts_sequence_percentage_match

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
                    raise colortext.Exception("The SEQRES and FASTA sequences disagree for chain %s in %s. This can happen but special-case handling (use_seqres_sequence_for_fasta_sequence) should be added to the file containing the %s class." % (chain_id, pdb_id, self.__class__.__name__))


    def _validate_mapping_signature(self):
        '''Make sure the domains and ranges of the SequenceMaps match the Sequences.'''

        # rosetta_to_atom_sequence_maps
        for chain_id, sequence_map in self.rosetta_to_atom_sequence_maps.iteritems():
            # Check that all Rosetta residues have a mapping
            assert(sorted(sequence_map.keys()) == sorted(self.rosetta_sequences[chain_id].ids()))

            # Check that all ATOM residues in the mapping exist and that the mapping is injective
            rng = set(sequence_map.values())
            atom_residue_ids = set(self.atom_sequences[chain_id].ids())
            assert(rng.intersection(atom_residue_ids) == rng)
            assert(len(rng) == len(sequence_map.values()))

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

        # seqres_to_uniparc_sequence_maps
        for chain_id, sequence_map in self.seqres_to_uniparc_sequence_maps.iteritems():
            # Check that acceptable_sequence_percentage_match% of all SEQRES residues have a mapping (there may have been
            # insertions or bad mismatches i.e. low BLOSUM62/PAM250 scores). I chose 80% arbitrarily but this can be overridden
            #  with the acceptable_sequence_percentage_match argument to the constructor.
            if self.sequence_types[chain_id] == 'Protein' or self.sequence_types[chain_id] == 'Protein skeleton':
                if sequence_map:
                    mapped_SEQRES_residues = set(sequence_map.keys())
                    all_SEQRES_residues = set(self.seqres_sequences[chain_id].ids())
                    if len(all_SEQRES_residues) >= 20:
                        match_percentage = 100.0 * (float(len(mapped_SEQRES_residues))/float((len(all_SEQRES_residues))))
                        if not (self.acceptable_sequence_percentage_match <= match_percentage <= 100.0):
                            if not set(list(str(self.seqres_sequences[chain_id]))) == set(['X']):
                                # Skip cases where all residues are unknown e.g. 1DEQ, chain M
                                raise Exception("Chain %s in %s only had a match percentage of %0.2f%%" % (chain_id, self.pdb_id, match_percentage))

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

                            raise Exception('\n'.join(err_msg))
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
                            if not self.clustal_seqres_to_uniparc_sequence_maps[c].matches(self.sifts_seqres_to_uniparc_sequence_maps[c]):
                                mismatched_keys = self.clustal_seqres_to_uniparc_sequence_maps[c].get_mismatches(self.sifts_seqres_to_uniparc_sequence_maps[c])
                                raise Exception("self.clustal_seqres_to_uniparc_sequence_maps[c].matches(self.sifts_seqres_to_uniparc_sequence_maps[c])")
                            self.seqres_to_uniparc_sequence_maps[c] = self.clustal_seqres_to_uniparc_sequence_maps[c] + self.sifts_seqres_to_uniparc_sequence_maps[c]
                        else:
                            self.seqres_to_uniparc_sequence_maps[c] = self.clustal_seqres_to_uniparc_sequence_maps[c]
                    except Exception, e:
                        colortext.warning(traceback.format_exc())
                        colortext.error(str(e))
                        raise colortext.Exception("Mapping cross-validation failed checking atom to seqres sequence maps between Clustal and SIFTS in %s, chain %s." % (self.pdb_id, c))
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
            self.pdb.construct_pdb_to_rosetta_residue_map(self.rosetta_scripts_path, rosetta_database_path = self.rosetta_database_path, cache_dir = self.cache_dir)
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
                self.sifts = self.bio_cache.get_sifts_object(pdb_id, acceptable_sequence_percentage_match  = self.acceptable_sifts_sequence_percentage_match)
            else:
                self.sifts = SIFTS.retrieve(pdb_id, cache_dir = self.cache_dir, acceptable_sequence_percentage_match = self.acceptable_sifts_sequence_percentage_match)
        except MissingSIFTSRecord:
            colortext.warning("No SIFTS entry was found for %s." % pdb_id)
        except BadSIFTSMapping:
            colortext.warning("The SIFTS mapping for %s was considered a bad mapping at the time of writing." % pdb_id)
        except NoSIFTSPDBUniParcMapping:
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
                        self.PDB_UniParc_SA = PDBUniParcSequenceAligner(pdb_id, cache_dir = self.cache_dir, cut_off = cut_off, sequence_types = self.sequence_types, replacement_pdb_id = self.replacement_pdb_id, added_uniprot_ACs = self.pdb.get_UniProt_ACs())
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
            raise colortext.Exception("Relatrix construction failed creating the PDBUniParcSequenceAligner object for %s. The cut-off level reached %d%% without finding a match for all chains but at that level, the mapping from chains to UniParc IDs was not injective.\n%s" % (pdb_id, cut_off, str(e)))
        except:
            raise colortext.Exception("Relatrix construction failed creating the PDBUniParcSequenceAligner object for %s.\n%s" % (pdb_id, traceback.format_exc()))
