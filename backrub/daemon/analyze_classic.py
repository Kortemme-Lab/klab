#!/usr/bin/env python2.4
# encoding: utf-8
"""
analyze_classic.py

Created by Florian Lauck on 2009-10-21.
Copyright (c) 2009 __UCSF__. All rights reserved.

This class analyzes the raw output of a classic Rosetta run. It parses the output file and reads out the energies.

"""

import os
import sys
import string


class AnalyzeClassic:
  
  filename       = ''
  dict_scores    = {}
  score_keys = [ 'SCORE', 'RAMACHANDRAN', 'FA_ATR', 'FA_REP', 'FA_SOL', 'FA_ELEC', 'FA_PAIR', 'FA_REF', 
                 'FA_DUN', 'FA_PROB', 'FA_H2O', 'HB_SRBB', 'HB_LRBB', 'HB_SC', 'FA_INTRA', 'GB', 'PLANE', 
                 'BOND_ANGLE', 'BARCODE', 'BAR_ENRG', 'CST']

    
  def __init__(self, filename=None):
    
    self.filename = filename
    
    
  def parse_file(self):

    handle_in = open(self.filename,'r')
    i = 1    
    for line in handle_in:
      if line.strip()   == 'Initial Scores:':
        self.dict_scores['input'] = self.read_score_table(handle_in)
      elif line.strip() == 'Low Scores:':
        self.dict_scores['%04.i' % i] = self.read_score_table(handle_in)
        i+=1

    handle_in.close()
  
  
  def read_score_table(self, handle):
    """reads exactly one table from the buffer and returns a dictionary with the values"""
    scores = {}
    for line in handle:
      value = line.split()
      i=0
      while i <= 40:
        scores[value[i]] = value[i+1]
        i+=2
      break # there is only one line to read, so break out of the for loop
      
    return scores
    
    
  def make_line_score(self, structure_id):
    """format a dict with scores into a line"""
    line = structure_id
    for key in self.score_keys:
      line += '\t%s' % self.dict_scores[structure_id][key]

    return line
  
  
  def make_score_table(self):
    """makes a table"""
    table = 'structure'
    # header with score names
    for key in self.score_keys:
      table += ' ' + key
    table += '\n'
    
    # write scores for input structure
    table += self.make_line_score('input') + '\n'

    # write scores for created structures
    for i in range(1,len(self.dict_scores.iteritems()) ):
      table += self.make_line_score('%04.i' % i) + '\n'

    return table

  def make_simple_table(self):
    table = 'input'
    table += '\t%s\n' % self.dict_scores['input']['SCORE']
    for i in range(1,len(self.dict_scores.iteritems()) ):
      sid = '%04.i' % i
      table += '%s\t%s\n' % (sid, self.dict_scores[sid]['SCORE'] )
      
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
      
    
if __name__ == "__main__":

  if len(sys.argv) < 4:
    print 'usage: %s <classic Rosetta stdout file> <energy matrix output file> <simple score list>' % sys.argv[0]
    sys.exit(1)
  obj = AnalyzeClassic(filename=sys.argv[1])
  if obj.analyze(outfile=sys.argv[2], outfile2=sys.argv[3]):
    print "Success!"
    
  
