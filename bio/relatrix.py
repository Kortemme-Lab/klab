#!/usr/bin/python
# encoding: utf-8
"""
relatrix.py
A class for relating residues using Rosetta numbering, PDB ATOM numbering, SEQRES/FASTA sequences, and UniParc sequences.

Created by Shane O'Connor 2013
"""

import traceback

from fasta import FASTA
from pdb import PDB
from pdbml import PDBML
from clustalo import PDBUniParcSequenceAligner, MultipleAlignmentException
from tools import colortext

class ResidueRelatrix(object):

    def __init__(self, pdb_id, rosetta_scripts_path, rosetta_database_path, chains_to_keep = [], min_clustal_cut_off = 80, cache_dir = None, silent = False): # keep_HETATMS = False

        self.pdb_id = pdb_id
        self.silent = silent
        self.rosetta_scripts_path = rosetta_scripts_path
        self.rosetta_database_path = rosetta_database_path

        self.FASTA = None
        self.pdb = None
        self.pdbml = None
        self.PDB_UniParc_SA = None

        self.alignment_cutoff = None

        self._create_objects(chains_to_keep, min_clustal_cut_off, True, cache_dir) # todo: at present, we always strip HETATMs. We may want to change this in the future.
        self._create_sequences()
        self._create_sequence_maps()
        self._validate()

    ### Private methods ###

    def _validate(self):
        '''Get all of the SequenceMaps - Rosetta->ATOM, ATOM->SEQRES/FASTA, SEQRES->UniParc.'''

        ## Make sure the domains and ranges of the SequenceMaps match the Sequences

        # rosetta_to_atom_sequence_maps
        for chain_id, sequence_map in self.rosetta_to_atom_sequence_maps.iteritems():
            # Check that all Rosetta residues have a mapping
            assert(sorted(sequence_map.keys()) == sorted(self.rosetta_sequences[chain_id].ids()))

            # Check that all ATOM residues in the mapping exist and that the mapping is injective
            rng = set(sequence_map.values())
            atom_ids = set(self.atom_sequences[chain_id].ids())
            assert(rng.intersection(set(self.atom_sequences[chain_id].ids())) == rng)
            assert(len(rng) == len(sequence_map.values()))

        # atom_to_seqres_sequence_maps
        #todo self.atom_to_seqres_sequence_maps

        # seqres_to_uniparc_sequence_maps
        #todo self.seqres_to_uniparc_sequence_maps


        #todo: make sure all the residue types map through translation

    def _create_sequence_maps(self):
        '''Get all of the SequenceMaps - Rosetta->ATOM, ATOM->SEQRES/FASTA, SEQRES->UniParc.'''

        self.rosetta_to_atom_sequence_maps = self.pdb.rosetta_to_atom_sequence_maps
        #todo self.atom_to_seqres_sequence_maps = self.pdb.atom_to_seqres_sequence_maps
        #todo self.seqres_to_uniparc_sequence_maps = ???

        #todo: make sure all the residue types map through translation

    def _create_sequences(self):
        '''Get all of the Sequences - Rosetta, ATOM, SEQRES, FASTA, UniParc.'''

        # Create the Rosetta sequences and the maps from the Rosetta sequences to the ATOM sequences
        self.pdb.construct_pdb_to_rosetta_residue_map(self.rosetta_scripts_path, self.rosetta_database_path)

        # Get all the Sequences
        self.uniparc_sequences = self.PDB_UniParc_SA.uniparc_sequences
        self.fasta_sequences = self.FASTA.get_sequences(self.pdb_id)
        self.seqres_sequences = self.pdb.seqres_sequences
        self.atom_sequences = self.pdb.atom_sequences
        self.rosetta_sequences = self.pdb.rosetta_sequences

        # Update the chain types for the UniParc sequences
        uniparc_pdb_chain_mapping = {}
        for pdb_chain_id, matches in self.PDB_UniParc_SA.clustal_matches.iteritems():
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

        # Update the chain types for the FASTA sequences
        for chain_id, sequence in self.seqres_sequences.iteritems():
            self.fasta_sequences[chain_id].set_type(sequence.sequence_type)


    def _create_objects(self, chains_to_keep, min_clustal_cut_off, strip_HETATMS, cache_dir):

        pdb_id = self.pdb_id
        assert(20 <= min_clustal_cut_off <= 100)

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

        # Check that the FASTA and SEQRES sequences agree (they sometimes differ)
        for chain_id, sequence in self.pdb.seqres_sequences.iteritems():
            if str(sequence) != self.FASTA[pdb_id][chain_id]:
                raise colortext.Exception("The SEQRES and FASTA sequences disagree for chain %s in %s. This can happen but special-case handling should be added to the file containing the %s class." % (chain_id, pdb_id, self.__class__.__name__))

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
            for x in range(100, min_clustal_cut_off, -1):
                cut_off = x
                if not self.silent:
                    colortext.warning("\tTrying to align sequences with a cut-off of %d%%." % cut_off)

                # todo: this will be slow for UniParc entries with large amounts of data/associated UniProt IDs since we create a UniParc entry each time. Refactor the code so that we do not create new entries each time.
                PDB_UniParc_SA = PDBUniParcSequenceAligner(pdb_id, cache_dir = '/home/oconchus/temp', cut_off = cut_off)
                num_matches_per_chain = set(map(len, PDB_UniParc_SA.clustal_matches.values()))
                if len(num_matches_per_chain) == 1 and num_matches_per_chain.pop() == 1:
                    if not self.silent:
                        colortext.message("\tSuccessful match with a cut-off of %d%%." % cut_off)
                    self.PDB_UniParc_SA = PDB_UniParc_SA
                    self.alignment_cutoff = cut_off
                    break
                else:
                    if [n for n in num_matches_per_chain if n > 1]:
                        raise MultipleAlignmentException("Too many matches found at cut-off %d." % cut_off)
        except MultipleAlignmentException, e:
            # todo: this will probably fail with DNA or RNA so do not include those in the alignment
            raise colortext.Exception("Relatrix construction failed creating the PDBUniParcSequenceAligner object for %s. The cut-off level reached %d without finding a match for all chains but at that level, the mapping from chains to UniParc IDs was not injective.\n%s" % (pdb_id, cut_off, str(e)))
        except:
            raise colortext.Exception("Relatrix construction failed creating the PDBUniParcSequenceAligner object for %s.\n%s" % (pdb_id, traceback.format_exc()))
