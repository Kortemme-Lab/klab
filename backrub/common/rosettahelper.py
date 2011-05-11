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
import stat
import tempfile

#todo:
#server_root = "/var/www/html/rosettaweb"
server_root = "/home/oconchus/clustertest110428/rosettawebclustertest/backrub"

ROSETTAWEB_SK_AA = {"ALA": "A", "CYS": "C", "ASP": "D", "GLU": "E", "PHE": "F", "GLY": "G",
                    "HIS": "H", "ILE": "I", "LYS": "K", "LEU": "L", "MET": "M", "ASN": "N",
                    "PRO": "P", "GLN": "Q", "ARG": "R", "SER": "S", "THR": "T", "VAL": "V",
                    "TRP": "W", "TYR": "Y"}

ROSETTAWEB_SK_AAinv = {}
for k, v in ROSETTAWEB_SK_AA.items():
    ROSETTAWEB_SK_AAinv[v] = k

permissions755SGID = stat.S_ISGID | stat.S_IRUSR | stat.S_IWUSR | stat.S_IXUSR | stat.S_IRGRP | stat.S_IXGRP | stat.S_IROTH | stat.S_IXOTH
permissions755 = stat.S_IRUSR | stat.S_IWUSR | stat.S_IXUSR | stat.S_IRGRP | stat.S_IXGRP | stat.S_IROTH | stat.S_IXOTH

def readFile(filepath):
    output_handle = open(filepath,'r')
    contents = output_handle.read()
    output_handle.close()
    return contents

def writeFile(filepath, contents):
    output_handle = open(filepath,'w')
    output_handle.write(contents)
    output_handle.close()

# Tasks
def write_file(filename, contents):
   file = open(filename, 'w')
   file.write(contents)
   file.close()
   
def make755Directory(path):
    os.mkdir(path)
    if not os.path.isdir(path):
        raise os.error
    global permissions755SGID
    os.chmod(path, permissions755SGID)

def makeTemp755Directory(temproot, suffix = None):
    if suffix:
        path = tempfile.mkdtemp("_%s" % suffix, dir = temproot)
    else:
        path = tempfile.mkdtemp(dir = temproot)
    if not os.path.isdir(path):
        raise os.error
    global permissions755SGID
    os.chmod(path, permissions755SGID)
    return path

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
  for fn in os.listdir(os.path.abspath(dirname)):
    fn = os.path.abspath(fn)
    if os.path.isdir(fn):
      all_files += get_files(fn)
    else:
      all_files.append(fn)
  os.chdir('../')
  return all_files

def grep(string, list):
  expr = re.compile(string)
  results = filter(expr.search, [str(line) for line in list])
  return results
class RosettaError(Exception):
    def __init__(self, task, ID):
        self.task = task
        self.ID = ID
    def __str__(self):
        return repr(self.ID + ' ' + self.task)



if __name__ == "__main__":
    fn_list = [ string.replace(fn, os.getcwd() + '/3c5a0e1d0e465e80551b932b97a8344b', '.') for fn in get_files('./') ]
    print fn_list
  
    # print get_files('./designs/')

