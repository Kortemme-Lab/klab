#!/usr/bin/env python
# encoding: utf-8
"""
untitled.py

Created by Florian Lauck on 2009-10-06.
Copyright (c) 2009 __UCSF__. All rights reserved.
"""

import os
import sys
import re
import string


def get_score_from_pdb_file(self, filename):
  handle = open(filename, 'r')
  handle.readline() # discard first line, 2nd is interesting to us
  score = handle.readline().split()[-1]
  handle.close()
  return score


def get_residue_scores_from_pdb(self, filename):
  handle = open(filename, 'r')

  for line in handle: # read til the interesting part starts
    if line.split()[0] == '#BEGIN_POSE_ENERGIES_TABLE':
      break # break the loop
    
  scores = ''
  for line in handle:
    if line.split()[0] != '#END_POSE_ENERGIES_TABLE':
      scores += line
    
  handle.close()
  return scores

def get_files(dirname):
  '''recursion rockz'''
  all_files = []
  os.chdir(dirname)
  for fn in os.listdir( os.path.abspath(dirname) ):
    fn = os.path.abspath(fn)
    if os.path.isdir(fn):
      all_files += get_files(fn)
    else:
      all_files.append( fn )
  os.chdir('../')
  return all_files

def grep(string,handle):
  expr = re.compile(string)
  results = filter(expr.search,[str(line) for line in handle])
  return results



# def analyze_residue_level():
#     args = [  self.parameter["rosetta_score_jd2"],
#               '-database', self.parameter["rosetta_mini_db"], 
#               '-s', low_file,
#               '-no_optH',
#               '-score:weights', string.join( self.parameter["rosetta_mini_db"].split('/')[:-1],'/') + '/scores.txt' # /opt/rosettabackend/data/scores.txt
#               ]
#               
#     subp = subprocess.Popen([str(arg) for arg in args], 
#                             stdout=PIPE, 
#                             stderr=PIPE, 
#                             cwd=workingdir )
# 
#     while self.subp.poll() == None:
#       time.sleep(0.5)
#     
#     get_residue_scores_from_pdb()
  
class RosettaError(Exception):
  def __init__(self, task, ID):
    self.task = task
    self.ID   = ID
  def __str__(self):
    return repr( self.ID + ' ' + self.task )



if __name__ == "__main__":
  fn_list = [ string.replace(fn,os.getcwd()+'/3c5a0e1d0e465e80551b932b97a8344b','.') for fn in get_files( './' ) ]
  print fn_list
  
  # print get_files('./designs/')

