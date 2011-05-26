#!/usr/bin/env python2.4
# encoding: utf-8
"""
analyze_mini.py

Created by Florian Lauck on 2009-10-21.
Copyright (c) 2009 __UCSF__. All rights reserved.

This class analyzes the raw output of a mini run. It parses the output file and reads out the energies.

"""

import os
import sys
if __name__ == "__main__":
    sys.path.insert(0, "../common/")
import re
import time
import string
import subprocess
import rosettahelper


class AnalyzeMini:
  
  filename       = ''
  dict_scores    = {}
  score_keys = [ 'total',
                 'fa_atr', 'fa_rep', 'fa_sol', 'fa_intra_rep', 'mm_bend', 'pro_close', 
                 'fa_pair', 'hbond_sr_bb', 'hbond_lr_bb', 'hbond_bb_sc', 'hbond_sc', 
                 'dslf_ss_dst', 'dslf_cs_ang', 'dslf_ss_dih', 'dslf_ca_dih', 
                 'rama', 'omega', 'fa_dun', 'p_aa_pp', 'ref']
    
  def __init__(self, filename=None):
    
    self.filename = filename
    self.dict_scores = {}
    
    
  def parse_file(self):

    handle_in = open(self.filename,'r')
    i = 1    
    for line in handle_in:
      # if the line indicates the start of the table AND the table is for one of the LOW structures
      # then: call read_score_table
      if line.strip() == 'apps.backrub: Score After PDB Load:':
        self.dict_scores['input'] = self.read_score_table(handle_in)
      elif line.strip() == 'apps.backrub: Low Score:':
        self.dict_scores['%04.i' % i] = self.read_score_table(handle_in)
        i+=1

    handle_in.close()
  
  def read_score_table(self, handle):
    """reads exactly one table from the buffer and returns a dictionary with the values"""
    scores = {}
    for line in handle:
      value = line.split()
      if value[0] == 'Total':
        scores['total'] = ( '-', '-', value[3] )
        break # the table ends after the total score and we can break
      elif value[0] != 'Scores' and value[0] != 'apps.backrub:' and value[0][0] != '-':
        scores[value[0]] = (value[1],value[2],value[3]) # tuple: see self.weight_keys

    return scores
    
    
  def make_line_score(self, structure_id):
    """format a dict with scores into a line"""
    line = structure_id
    for key in self.score_keys:
      line += ' %s' % self.dict_scores[structure_id][key][2]

    return line
    
  def make_line_weights(self):
    """format a dict with scores into a line"""
    line = 'weights'
    for key in self.score_keys:
      line += ' %s' % self.dict_scores['input'][key][2]
    return line
  
  def make_score_table(self):
    """makes a table"""
    table = 'structure'

    # header with score names
    for key in self.score_keys:
      table += ' ' + key
    
    # write line with weights
    table += '\n' + self.make_line_weights() + '\n'
    
    # write scores for input structure
    table += self.make_line_score('input') + '\n'
    
    # write scores for created structures
    for i in range(1,len(self.dict_scores.keys()) ):
      table += self.make_line_score('%04.i' % i) + '\n'
    
    return table
  
  
  def make_simple_table(self):
    table = 'input'
    table += '\t%s\n' % self.dict_scores['input']['total'][2]
    for i in range(1,len(self.dict_scores.keys()) ):
      sid = '%04.i' % i
      table += '%s\t%s\n' % (sid, self.dict_scores[sid]['total'][2])
    
    return table
      
  
  def analyze(self, outfile=None, outfile2=None):
    try:
      self.parse_file()
      if outfile == None and outfile2 == None:
        print self.make_score_table()
        return True
      if outfile != None:
        handle_out = open(outfile,'w')
        handle_out.write("# All scores below are weighted scores, not raw scores.\n")
        handle_out.write(self.make_score_table())
        handle_out.close()
      if outfile2 != None:
        handle_out = open(outfile2,'w')
        handle_out.write("# All scores below are weighted scores, not raw scores.\n")
        handle_out.write(self.make_simple_table())
        handle_out.close()
    except:
      return False
    
    return True

# the following functions are unique to mini and n/a for classic
# Run the score analysis on residue level, extract the scores from the pdb files and write them in individual files
 
  def extract_scores_from_PDB(self, fn_in):
    '''this extracts the resdidue scrores from the PDB file'''
    handle = open(fn_in,'r')
    read = False
    score_lines = ''
    for line in handle:
      value = line.split()
      if value[0] == '#BEGIN_POSE_ENERGIES_TABLE':
        read = True
        score_lines += value[0] + ' %s\n' % fn_in.split('/')[-1]
      elif value[0] == '#END_POSE_ENERGIES_TABLE':
        score_lines += value[0] + ' %s\n' % fn_in.split('/')[-1]
        break
      elif read:
        score_lines += line
    
    handle.close()
    return score_lines
    
 
  def calculate_residue_scores(self, base_dir, postprocessingBinary, databaseDir, workingdir, scores_out_fn):
    if workingdir[-1] != '/' : workingdir = workingdir+'/'
    try:
      # open scores file, this file will contain all scores for all structures
      handle = open(scores_out_fn,'w')
      handle.write("# All scores below are weighted scores, not raw scores.\n")
    
      # get files:
      files = os.listdir( workingdir )
      files.sort()
      # print files
      for fn in files:
        if re.match ('.*low.*(pdb|PDB)', fn):
          # add pairwise energies to the pdb file
          args = [ postprocessingBinary,
                   '-database', databaseDir,
                   '-s', workingdir + fn,
                   '-no_optH',
                   '-score:weights', base_dir + "data/scores.txt" ]
        
          #print 'compute residue scores for %s' % fn
          #print string.join([str(arg) for arg in args])
          subp = subprocess.Popen([str(arg) for arg in args], stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=workingdir )
        
          while subp.poll() == None:
            time.sleep(1)
          # # overwrite the old pdb file with the resulting pdb file that contains the scores 
          #print workingdir + fn[:-4] + '_0001' + fn[-4:], '->', workingdir+fn 
          os.rename( workingdir + fn[:-4] + '_0001' + fn[-4:], workingdir+fn )
          # extract the scores and add them to a file
          handle.write( self.extract_scores_from_PDB( workingdir+fn ) )
        
      handle.close()
    except:
      return False
      
    return True
    
    
if __name__ == "__main__":
  """test"""
  if len(sys.argv) < 4:
    print 'usage: %s <mini Rosetta stdout file> <energy matrix output file> <simple score list>' % sys.argv[0]
    sys.exit(1)
  obj = AnalyzeMini(filename=sys.argv[1])
  if obj.analyze(outfile=sys.argv[2],outfile2=sys.argv[3]):
    print "Success!"
  
  # obj2 = AnalyzeMini()
  # obj2.calculate_residue_scores( '/opt/rosettabackend/', 
  #                                '/opt/rosettabackend/data/minirosetta_database/', 
  #                                '/opt/lampp/htdocs/rosettaweb/backrub/downloads/a4327fe4878a9445831062d735f162d5/', 
  #                                '/opt/lampp/htdocs/rosettaweb/backrub/downloads/a4327fe4878a9445831062d735f162d5/scores_residues.txt' )
  
  
  
  
  
  
  
  
  
  
  
  
  
  
  
  
  
  
  
  
  
  