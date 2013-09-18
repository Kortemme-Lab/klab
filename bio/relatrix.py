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

    def __init__(self, pdb_id, chains_to_keep = [], min_clustal_cut_off = 80, cache_dir = None, silent = False): # keep_HETATMS = False
        self.pdb_id = pdb_id
        self.silent = silent

        self.FASTA = None
        self.pdb = None
        self.pdbml = None
        self.PDB_UniParc_SA = None

        self.alignment_cutoff = None

        self._create_objects(chains_to_keep, min_clustal_cut_off, True, cache_dir) # todo: at present, we always strip HETATMs. We may want to change this in the future.

    ### Private methods ###

    def _create_objects(self, chains_to_keep, min_clustal_cut_off, strip_HETATMS, cache_dir):

        pdb_id = self.pdb_id
        assert(20 <= min_clustal_cut_off <= 100)

        # Create the FASTA object
        if not self.silent:
            colortext.message("Creating the FASTA object.")
        try:
            self.FASTA = FASTA.retrieve(pdb_id, cache_dir = cache_dir)[pdb_id]
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
            if sequence != self.FASTA[chain_id]:
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

        print(self.PDB_UniParc_SA.clustal_matches)
