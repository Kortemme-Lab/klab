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
from pdb import PDB, PDBMissingMainchainAtomsException
from pdbml import PDBML
from clustalo import PDBUniParcSequenceAligner, MultipleAlignmentException
from tools import colortext
from basics import Sequence, SequenceMap

use_seqres_sequence_for_fasta_sequence = set(['1A2C'])

class ResidueRelatrix(object):
    ''' A class for relating residue IDs from different schemes.
        Note: we assume throughout that there is one map from SEQRES to UniParc. This is not always true e.g. Polyubiquitin-C (UPI000000D74D) has 9 copies of the ubiquitin sequence.'''

    schemes = ['rosetta', 'atom', 'seqres', 'fasta', 'uniparc']

    def __init__(self, pdb_id, rosetta_scripts_path, rosetta_database_path, chains_to_keep = [], min_clustal_cut_off = 80, cache_dir = None, silent = False, acceptable_sequence_percentage_match = 90.0, starting_clustal_cut_off = 100): # keep_HETATMS = False
        '''acceptable_sequence_percentage_match is used when checking whether the SEQRES sequences have a mapping. Usually 90.00% works but some cases e.g. 1AR1, chain C, have a low matching score mainly due to extra residues.'''

        assert(0.0 <= acceptable_sequence_percentage_match <= 100.0)

        self.pdb_id = pdb_id
        self.silent = silent
        self.rosetta_scripts_path = rosetta_scripts_path
        self.rosetta_database_path = rosetta_database_path

        self.alignment_cutoff = None
        self.acceptable_sequence_percentage_match = acceptable_sequence_percentage_match

        self.FASTA = None
        self.pdb = None
        self.pdbml = None
        self.PDB_UniParc_SA = None

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
        self.uniparc_to_seqres_sequence_maps = None # this map uses PDB chain IDs as PDB chains may map to zero or one UniParc IDs whereas UniParc IDs may map to many PDB chains

        self.pdb_chain_to_uniparc_chain_mapping = {}

        self._create_objects(chains_to_keep, starting_clustal_cut_off, min_clustal_cut_off, True, cache_dir) # todo: at present, we always strip HETATMs. We may want to change this in the future.
        self._create_sequences()
        self._create_sequence_maps()
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
                if str(sequence) != self.FASTA[pdb_id][chain_id]:
                    #print(str(sequence))
                    #print(self.FASTA[pdb_id][chain_id])
                    raise colortext.Exception("The SEQRES and FASTA sequences disagree for chain %s in %s. This can happen but special-case handling should be added to the file containing the %s class." % (chain_id, pdb_id, self.__class__.__name__))


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
            assert(sorted(sequence_map.keys()) == sorted(self.atom_sequences[chain_id].ids()))

            # Check that all SEQRES residues in the mapping exist and that the mapping is injective
            rng = set(sequence_map.values())
            seqres_residue_ids = set(self.seqres_sequences[chain_id].ids())
            assert(rng.intersection(seqres_residue_ids) == rng)
            assert(len(rng) == len(sequence_map.values()))

        # seqres_to_uniparc_sequence_maps
        for chain_id, sequence_map in self.seqres_to_uniparc_sequence_maps.iteritems():
            # Check that 90% of all SEQRES residues have a mapping (there may have been insertions or bad mismatches i.e.
            # low BLOSUM62/PAM250 scores). I chose 90% arbitrarily but this can be overridden with the
            # acceptable_sequence_percentage_match argument to the constructor.
            if self.sequence_types[chain_id] == 'Protein' or self.sequence_types[chain_id] == 'Protein skeleton':
                mapped_SEQRES_residues = set(sequence_map.keys())
                all_SEQRES_residues = set(self.seqres_sequences[chain_id].ids())
                if len(all_SEQRES_residues) >= 20:
                    match_percentage = 100.0 * (float(len(mapped_SEQRES_residues))/float((len(all_SEQRES_residues))))
                    if not (self.acceptable_sequence_percentage_match <= match_percentage <= 100.0):
                        raise Exception("Chain %s in %s only had a match percentage of %0.2f%%" % (chain_id, self.pdb_id, match_percentage))

            # Check that all UniParc residues in the mapping exist and that the mapping is injective
            if self.pdb_chain_to_uniparc_chain_mapping.get(chain_id):
                rng = set(sequence_map.values())
                uniparc_chain_id = self.pdb_chain_to_uniparc_chain_mapping[chain_id]
                uniparc_residue_ids = set(self.uniparc_sequences[uniparc_chain_id].ids())
                assert(rng.intersection(uniparc_residue_ids) == rng)
                assert(len(rng) == len(sequence_map.values()))


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
            for atom_id, seqres_id, _ in sequence_map:
                assert(atom_sequence[atom_id].ResidueAA == seqres_sequence[seqres_id].ResidueAA)

        for chain_id, sequence_map in self.seqres_to_uniparc_sequence_maps.iteritems():
            if self.pdb_chain_to_uniparc_chain_mapping.get(chain_id):
                seqres_sequence = self.seqres_sequences[chain_id]
                uniparc_sequence = self.uniparc_sequences[self.pdb_chain_to_uniparc_chain_mapping[chain_id]]
                for seqres_id, uniparc_id, substitution_match in sequence_map:
                    # Some of the matches may not be identical but all the '*' Clustal Omega matches should be identical
                    if substitution_match.clustal == 1:
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
            s = SequenceMap()
            for k, v, substitution_match in sequence_map:
                s.add(v, k, substitution_match)
            self.uniparc_to_seqres_sequence_maps[chain_id] = s

    def _create_sequence_maps(self):
        '''Get all of the SequenceMaps - Rosetta->ATOM, ATOM->SEQRES/FASTA, SEQRES->UniParc.'''

        if self.pdb_to_rosetta_residue_map_error:
            self.rosetta_to_atom_sequence_maps = {}
            for c in self.atom_sequences.keys():
                self.rosetta_to_atom_sequence_maps[c] = SequenceMap()
        else:
            self.rosetta_to_atom_sequence_maps = self.pdb.rosetta_to_atom_sequence_maps
        self.atom_to_seqres_sequence_maps = self.pdbml.atom_to_seqres_sequence_maps
        self.seqres_to_uniparc_sequence_maps = self.PDB_UniParc_SA.seqres_to_uniparc_sequence_maps

    def _create_sequences(self):
        '''Get all of the Sequences - Rosetta, ATOM, SEQRES, FASTA, UniParc.'''

        # Create the Rosetta sequences and the maps from the Rosetta sequences to the ATOM sequences
        try:
            self.pdb.construct_pdb_to_rosetta_residue_map(self.rosetta_scripts_path, self.rosetta_database_path)
        except PDBMissingMainchainAtomsException:
            self.pdb_to_rosetta_residue_map_error = True

        # Get all the Sequences
        self.uniparc_sequences = self.PDB_UniParc_SA.uniparc_sequences
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
        for pdb_chain_id, matches in self.PDB_UniParc_SA.clustal_matches.iteritems():
            if matches:
                # we are not guaranteed to have a match e.g. the short chain J in 1A2C, chimeras, etc.
                uniparc_chain_id = matches.keys()[0]
                assert(len(matches) == 1)
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

    def _create_objects(self, chains_to_keep, starting_clustal_cut_off, min_clustal_cut_off, strip_HETATMS, cache_dir):

        pdb_id = self.pdb_id
        assert(20 <= min_clustal_cut_off <= starting_clustal_cut_off <= 100)

        # Create the FASTA object
        if not self.silent:
            colortext.message("Creating the FASTA object.")
        try:
            self.FASTA = FASTA.retrieve(pdb_id, cache_dir = cache_dir)
        except:
            raise colortext.Exception("Relatrix construction failed creating the FASTA object for %s.\n%s" % (pdb_id, traceback.format_exc()))

        # Create the PDB object
        if not self.silent:
            colortext.message("Creating the PDB object.")
        try:
            self.pdb = PDB.retrieve(pdb_id, cache_dir = cache_dir)
            self.pdb.strip_to_chains(chains_to_keep)
            if strip_HETATMS:
                self.pdb.strip_HETATMs()
        except:
            raise colortext.Exception("Relatrix construction failed creating the PDB object for %s.\n%s" % (pdb_id, traceback.format_exc()))

        self.sequence_types = self.pdb.chain_types

        # Create the PDBML object
        if not self.silent:
            colortext.message("Creating the PDBML object.")
        try:
            self.pdbml = PDBML.retrieve(pdb_id, cache_dir = cache_dir)
        except:
            raise colortext.Exception("Relatrix construction failed creating the PDBML object for %s.\n%s" % (pdb_id, traceback.format_exc()))

        # Create the PDBUniParcSequenceAligner object. We try the best alignment at first (100%) and then fall back to more relaxed alignments down to min_clustal_cut_off percent.
        if not self.silent:
            colortext.message("Creating the PDB to UniParc SequenceAligner object.")
        cut_off = 0
        try:
            PDB_UniParc_SA = None
            cut_off = None
            for x in range(starting_clustal_cut_off, min_clustal_cut_off, -1):
                cut_off = x
                if not self.silent:
                    colortext.warning("\tTrying to align sequences with a cut-off of %d%%." % cut_off)

                # todo: this will be slow for UniParc entries with large amounts of data/associated UniProt IDs since we create a UniParc entry each time. Refactor the code so that we do not create new entries each time.
                PDB_UniParc_SA = PDBUniParcSequenceAligner(pdb_id, cache_dir = '/home/oconchus/temp', cut_off = cut_off, sequence_types = self.sequence_types)

                # We only care about protein chain matches so early out as soon as we have them all matched
                protein_chain_matches = {}
                for _c, _st in self.sequence_types.iteritems():
                    if _st == 'Protein' or _st == 'Protein skeleton':
                        protein_chain_matches[_c] = PDB_UniParc_SA.clustal_matches[_c]

                num_matches_per_chain = set(map(len, protein_chain_matches.values()))
                if len(num_matches_per_chain) == 1 and num_matches_per_chain.pop() == 1:
                    # We have exactly one match per protein chain. Early out.
                    if not self.silent:
                        colortext.message("\tSuccessful match with a cut-off of %d%%." % cut_off)
                    self.PDB_UniParc_SA = PDB_UniParc_SA
                    self.alignment_cutoff = cut_off
                    break
                else:
                    # We have ambiguity - more than one match per protein chain. Exception.
                    if [n for n in num_matches_per_chain if n > 1]:
                        raise MultipleAlignmentException("Too many matches found at cut-off %d." % cut_off)
            if not self.PDB_UniParc_SA:
                print(PDB_UniParc_SA.clustal_matches.values())
                num_matches_per_chain = set(map(len, PDB_UniParc_SA.clustal_matches.values()))
                if num_matches_per_chain == set([0, 1]):
                    # We got matches but are missing chains
                    self.PDB_UniParc_SA = PDB_UniParc_SA
                    self.alignment_cutoff = cut_off
        except MultipleAlignmentException, e:
            # todo: this will probably fail with DNA or RNA so do not include those in the alignment
            raise colortext.Exception("Relatrix construction failed creating the PDBUniParcSequenceAligner object for %s. The cut-off level reached %d without finding a match for all chains but at that level, the mapping from chains to UniParc IDs was not injective.\n%s" % (pdb_id, cut_off, str(e)))
        except:
            raise colortext.Exception("Relatrix construction failed creating the PDBUniParcSequenceAligner object for %s.\n%s" % (pdb_id, traceback.format_exc()))
