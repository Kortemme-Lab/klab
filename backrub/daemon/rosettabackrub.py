#!/usr/bin/env python
# encoding: utf-8
"""
untitled.py

Created by Florian Lauck on 2009-10-02.
Copyright (c) 2009 __UCSF__. All rights reserved.
"""

import os
import sys
import pdb
import time
import types
import string ##debug
import shutil
import tempfile
import subprocess

from rosettahelper import * 
from rosettaexec import RosettaExec
from analyze_mini import AnalyzeMini

class RosettaBackrub(RosettaExec):
  """Rosetta Backrub with Mini class"""
  
  ## 'parameter' should contain the following list of parameter:
  # pdb_id, pdb_content, ensemble_size, mode
  ## optional (depending on mode)
  # chain, resid, newres, radius 
    
  # additional attributes
  default       = ""   # resfile default for amino acids
  residues      = {}   # contains the residues and their modes according to rosetta: { (chain, resID):["PIKAA","PHKL"] }
  backrub       = []   # residues to which backrub should be applied: [ (chain,resid), ... ]
  pivot_res     = []   # list of pivot residues, consecutively numbered from 1 [1,...]
  map_res_id    = {}   # contains the mapping from (chain,resid) to pivot_res
  filenames_low = []   # filename with low structures, is used by Sequence Tolerance Algorithm
  
  def get_low_filenames(self):
    return self.filenames_low
  
  def import_pdb( self, filename, contents ):
    """Import a pdb file from the database and write it to the temporary directory"""
    self.pdb = pdb.PDB(contents.split('\n'))
    self.pdb.remove_hetatm()  # rosetta doesn't like heteroatoms so let's remove them
    #self.pdb.fix_chain_id()   # adds a chain ID if the column is empty
          
    # internal mini resids don't correspond to the pdb file resids
    # the pivot residues need to be numbered consecuively from 1 up
    self.map_res_id = self.pdb.get_residue_mapping()
    self.pdb.write(self.workingdir + '/' + filename)
    self.name_pdb = filename
    return self.name_pdb
    
  
  def prepare_backrub( self ):
    """prepare data for a full backbone backrub run"""
    
    residue_ids = self.pdb.aa_resids()
    
    # backrub is applied to all residues: append all residues to the backrub list
    for res in residue_ids:
      x = [ res[0], res[1:].strip() ] # 0: chain ID, 1..: resid
      if len(x) == 1:
        self.backrub.append( ( "_", int(x[0].lstrip())) )
      else:
        self.backrub.append( ( x[0], int(x[1].lstrip())) )
  
  def prepare_pointmutation( self ):
    pass
  
  def prepare_multiplemutations( self ):
    pass
  
  def write_resfile( self ):
    """function for resfile creation"""

    default_mode = 'NATAA'
    # store filename
    self.name_resfile = self.workingdir_file_path("backrub_%s.resfile" % self.ID)
    # write resfile 
    output_handle = open(self.name_resfile,'w')
    # default line
    output_handle.write('%s\nstart\n' % default_mode)
    
    for (key, value) in self.residues.iteritems():  # { (chain, resID):["PIKAA","PHKL"] } + ("""111 A PIKAA I""")
      output_handle.write("%s %s %s %s\n" % (key[1], key[0], value[0], value[1]) )
    output_handle.write( "\n" )
    
    # translate resid to absolute mini rosetta res ids
    for residue in self.backrub:
      self.pivot_res.append( self.map_res_id[ '%s%4.i' % residue  ] )
    
    output_handle.close()
    
    # final check if file was created
    return os.path.exists( self.name_resfile )
    
  
  def preprocessing( self, resfile = None ):
    """prepare the data for a backrub run"""
      
    # self.make_workingdir_name( "backrub" )
    self.workingdir = os.path.abspath('./')
    
    self.import_pdb("%s_%s.pdb" % (self.parameter['pdb_id'], self.ID), self.parameter['pdb_content'])
    
    # get stuff depending on the mode and create resfile:
    if self.parameter['mode'] == 'no_mutation':
      self.prepare_backrub()
      if resfile:
          self.name_resfile = self.workingdir_file_path(resfile)
      else:
          self.write_resfile()
    else:
      print 'wrong mode'

    return self.workingdir

  
  def run( self ):
    """gather data for the command line and start the job"""
    
    ntrials = "10000" # should be 10000 on the live webserver
    
    settings = WebsiteSettings(sys.argv, os.environ['PWD'])
    if not(settings["LiveWebserver"]):
        ntrials = "10"
            
    args = [ "-database", self.dbdir, 
             "-s", self.name_pdb, 
             "-ignore_unrecognized_res", 
             "-resfile", self.name_resfile, 
             "-nstruct", self.parameter['ensemble_size'], 
             "-backrub:ntrials", ntrials, 
             "-pivot_atoms", "CA" ]
    
    if len(self.pivot_res) > 0:
      args.append("-pivot_residues")
      self.pivot_res.sort()
      args.extend([str(resid) for resid in self.pivot_res])
    
    self.filename_stdout = 'backrub_%s_stdout.txt' % self.ID
    self.filename_stderr = 'backrub_%s_stderr.txt' % self.ID
      
    self.run_args(args)


  def postprocessing( self, result_dir = None ):
    """this is the place to implement the postprocessing protocol for your application
        e.g.: -check if all files were created
              -execute analysis
              -get rid of files the user doesn't need to see
              -copy he directory over to the webserver\n"""
    error = ''
    
    # handle_out = open( self.workingdir_file_path('scores.dat') , 'w')
    # handle_out.write( '#initial score:\t%s\n' % initial_score )
    # handle_out.write( '#structure\tlast score\tlowest score\n' )
    
    # check whether files were created (and write the total scores to a file)
    for x in range(1, self.parameter['ensemble_size']+1):
      last_file = self.workingdir_file_path( '%s_%04.i_last.pdb' % (self.name_pdb[:-4], x ))
      low_file  = self.workingdir_file_path( '%s_%04.i_low.pdb'  % (self.name_pdb[:-4], x ))
                          
      if not os.path.exists( low_file ): 
        error += ' %s missing, ' % low_file # return False
      else:
        self.filenames_low.append( low_file )
      
      if not os.path.exists( last_file ):
        error += ' %s missing, ' % ( last_file ) # return False
      
      # write scores
      #handle_out.write( '%04.i\t%s\t%s\n' % (x, get_score_from_pdb_file(last_file), get_score_from_pdb_file(low_file)))
      
    # handle_out.write('\n')
    # handle_out.close()
    
    Analysis = AnalyzeMini(filename=self.workingdir_file_path( self.filename_stdout ))
    Analysis.analyze(outfile=self.workingdir_file_path('backrub_scores.dat'))
        
    if result_dir != None:
      self.copy_working_dir(result_dir)
    
    if error != '':
      print error
      return False
    
    return True
  
  
  
  
  

  
  
  
  