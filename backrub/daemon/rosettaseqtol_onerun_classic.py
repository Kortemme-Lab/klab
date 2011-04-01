#!/usr/bin/env python
# encoding: utf-8
"""
untitled.py

Created by Florian Lauck on 2009-10-02.
Copyright (c) 2009 __UCSF__. All rights reserved.
"""

import os
import sys
sys.path.insert(0, "../common/")
import pdb
import gzip
import time
import types
import string ##debug
import shutil
import tempfile
import subprocess

from rosettaexec import RosettaExec

aa1 = {"ALA": "A", "CYS": "C", "ASP": "D", "GLU": "E", "PHE": "F", "GLY": "G",
       "HIS": "H", "ILE": "I", "LYS": "K", "LEU": "L", "MET": "M", "ASN": "N",
       "PRO": "P", "GLN": "Q", "ARG": "R", "SER": "S", "THR": "T", "VAL": "V",
       "TRP": "W", "TYR": "Y"}

residues = ["ALA", "CYS", "ASP", "GLU", "PHE", "GLY", "HIS", "ILE", "LYS", 
            "LEU", "MET", "ASN", "PRO", "GLN", "ARG", "SER", "THR", "VAL", 
            "TRP", "TYR"]


class RosettaSeqTolONE(RosettaExec):
  """Rosetta Sequence Tolerance Code class.
     This class executes one design run"""
  
  ## 'parameter' should contain the following list of parameter:
  # name_pdb, resfile
  ## optional (depending on mode)
    
  def import_pdb(self, filename):
    self.name_pdb = filename
    
  def preprocessing(self):
    """  """
    #self.make_workingdir_name( "seqtol_%s" % self.ID )
    self.workingdir = os.path.abspath('./')
    self.import_pdb( self.parameter['name_pdb'] )
    

  def run(self):
    """run a single design run"""
    
    # This should be the PDB filename without the suffix
    self.prefix = self.name_pdb.split('/')[-1][:-4]
    args = [ "-design", "-multistate", 
             "-read_all_chains", "-fixbb",
             "-use_pdb_numbering",
             "-try_both_his_tautomers", 
             "-ex1", "-ex2", "-ex1aro", "-ex2aro", 
             "-extrachi_cutoff", "-1", 
             "-ndruns", "1", 
             "-resfile", self.parameter['resfile'].split('/')[-1], 
             "-s", self.name_pdb, 
             "-paths", "paths.txt", 
             "-generations", "5", # should be 5
             "-population", "2000", # should be 2000
             "-bind_thresh", "0.01", 
             "-fold_thresh", "0.01", 
             "-ms_fit", "1", 
             # "-ms_repack", # repack an 8A shell around the designed residue
             "-no_bb_terms",
             "-output_all_structures",
             "-norepack_disulf", "-find_disulf", # don't break/touch disulfide bonds
             # "-print_all_seq", 
	     ] 
    
    # for mini:
    # args = [ "-database", self.dbdir,
    #          "-s", self.name_pdb,
    #          "-resfile", self.parameter['resfile'],
    #          "-ex1", "-ex2", "-ex1aro", "-ex2aro", "-extrachi_cutoff", "0",
    #          "-score:ref_offsets", "TRP", "0.9",
    #          "-seq_tol:fitness_master_weights", "1", self.parameter['weights'][0], self.parameter['weights'][1], self.parameter['weights'][2], 
    #          "-ms:generations", "5",
    #          "-ms:pop_size", "2000", #  should be 2000
    #          "-ms:pop_from_ss", "1",
    #          "-ms:checkpoint:prefix", self.prefix,
    #          "-ms:checkpoint:interval", "200",
    #          "-ms:checkpoint:gz",
    #          "-out:prefix", self.prefix
    #          ]
    
    self.filename_stdout = 'seqtol_%s_stdout.txt' % self.ID
    self.filename_stderr = 'seqtol_%s_stderr.txt' % self.ID
    
    self.run_args(args)
    

  def postprocessing(self):
    """do some analysis as in Elisabeth's scripts"""
    
    self.file_stdout.close()
    self.file_stderr.close()
    
    # NO DON'T do it here
    # handle = open( self.filename_stdout, 'r' )
    # 
    # lines = []
    # for line in handle:
    #   if line.split()[0] == "POS":
    #     lines.append( self._read_matrix(handle) ):
    #     break

    
    # raw_filename   = self.workingdir_file_path( '%s.ga.entities.gz' % self.prefix )
    #     fasta_filename = self.workingdir_file_path( '%s_sequences.fa' % self.prefix )
    #     png_filename   = self.workingdir_file_path( '%s_profile.png' % self.prefix )
    # 
    #     handle = gzip.open(raw_filename,'r')
    #     i=0
    #     sequences = []
    #     # res_nums = []
    #     
    #     for line in handle:
    #       lst_line = line.split()
    #       if lst_line[0] == 'traits':
    #         sequence = ''
    #         for residue in lst_line[1:-4]:
    #           sequence += aa1[ residue.split('.')[1] ] # aa1 global map with 3 letter to 1 letter mapping, residue = res_id.aminoacid
    #           # if i == 0: # do this only once
    #           #   res_nums.append(residue.split('.')[0])
    #         i+=1
    #         sequences.append(sequence)
    #           
    #     handle.close()
    #     
    #     # write the sequences to a file, we could also write it directly without the 'sequences' string 
    #     # but this way we can also print it to stdout if necessary
    # 
    #     fasta_handle = open(fasta_filename, 'w')
    #     i=0
    #     for sequence in sequences:
    #       fasta_handle.write( '>%s\n%s\n' % (i,sequence) )
    #       i+=1
    #     fasta_handle.close()

  def _read_matrix(self, handle):
    lines = []
    for line in handle:
      if line[0] != "=":
        lines.append(line)
      else:
        return lines
    return lines
  

if __name__ == "__main__":
  '''test the postprocessing'''
  pass
  # one_run = RosettaSeqTolONE( ID = 1,
  #                             executable = "/var/rosettabackend/bin/rosetta_1Oct_08.gcc",
  #                             dbdir      = "/var/rosettabackend/data/rosetta_database/",
  #                             tempdir    = "./",
  #                             parameter  = {} )
  # one_run.workingdir = './'
  # one_run.prefix = 'input_0_0002_low'
  # one_run.postprocessing()
  
  
  

      
      

