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

ROSETTAWEB_SK_AA = {"ALA": "A", "CYS": "C", "ASP": "D", "GLU": "E", "PHE": "F", "GLY": "G",
                    "HIS": "H", "ILE": "I", "LYS": "K", "LEU": "L", "MET": "M", "ASN": "N",
                    "PRO": "P", "GLN": "Q", "ARG": "R", "SER": "S", "THR": "T", "VAL": "V",
                    "TRP": "W", "TYR": "Y"}

ROSETTAWEB_SK_AAinv = {}
for k, v in ROSETTAWEB_SK_AA.items():
    ROSETTAWEB_SK_AAinv[v] = k

# Set this to the machine you are debugging from
DEVELOPMENT_HOSTS = ["cabernet.ucsf.edu", "zin.ucsf.edu"]
DEVELOPER_USERNAMES = ["oconchus"]

permissions755SGID = stat.S_ISGID | stat.S_IRUSR | stat.S_IWUSR | stat.S_IXUSR | stat.S_IRGRP | stat.S_IXGRP | stat.S_IROTH | stat.S_IXOTH
permissions755     =                stat.S_IRUSR | stat.S_IWUSR | stat.S_IXUSR | stat.S_IRGRP | stat.S_IXGRP | stat.S_IROTH | stat.S_IXOTH

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

class WebsiteSettings(object):
    settings = {}
    base_dir = None
    
    def __init__(self, argv, scriptname):
        self.settings["ServerScript"] = scriptname 
        if argv[0].find("/") != -1:
            self.base_dir = self._getSourceRoot(argv[0])
        else:
            self.base_dir = self._getSourceRoot(scriptname)
        self._read_config_file()

    def _read_config_file(self):
        base_dir = self.base_dir
        settings = self.settings
        settingsFilename = os.path.join(base_dir, "settings.ini")
            
        # Read settings from file
        try:
            handle = open(settingsFilename, 'r')
            lines  = handle.readlines()
            handle.close()
            for line in lines:
                if line[0] != '#' and len(line) > 1  : # skip comments and empty lines
                    # format is: "parameter = value"
                    list_data = line.split()
                    if len(list_data) < 3:
                        raise IndexError(line)
                    settings[list_data[0]] = list_data[2]
        except IOError:
            raise Exception("settings.ini could not be found in %s." % base_dir)
            sys.exit(2)
        
        # Create derived settings
        settings["BaseDir"] = base_dir
        settings["BinDir"] = os.path.join(base_dir, "bin")
        settings["DataDir"] = os.path.join(base_dir, "data")
        settings["ShortServerName"] = string.split(settings["ServerName"], ".")[0]
        settings["LiveWebserver"] = bool(int(settings["LiveWebserver"]))
        settings["ClusterDebugMode"] = bool(int(settings["ClusterDebugMode"]))
        settings["SQLPort"] = int(settings["SQLPort"])
        settings["MaxLocalProcesses"] = int(settings["MaxLocalProcesses"])
        settings["MaxClusterJobs"] = int(settings["MaxClusterJobs"])
        
        # Constant settings (these can be optionally overwritten in the settings file)
        if not settings.get("TempDir"):
            settings["TempDir"] = os.path.join(base_dir, "temp")
        if not settings.get("EnsembleTempDir"):
            settings["EnsembleTempDir"] = os.path.join(base_dir, "temp")
        if not settings.get("DownloadDir"):
            settings["DownloadDir"] = os.path.join(base_dir, "downloads")
        if not settings.get("RemoteDownloadDir"):
            settings["RemoteDownloadDir"] = os.path.join(base_dir, "remotedownloads")
        if not settings.get("ErrorDir"):
            settings["ErrorDir"] = os.path.join(base_dir, "error")
        if not settings.get("StoreTime"):
            settings["StoreTime"] = 60
        if not settings.get("CookieExpiration"):
            settings["CookieExpiration"] = 60 * 60
        if not settings.get("ClusterDownloadDir"):
            settings["ClusterDownloadDir"] = os.path.join(base_dir, "downloads")
        if not settings.get("ClusterRemoteDownloadDir"):
            settings["ClusterRemoteDownloadDir"] = os.path.join(base_dir, "remotedownloads")
        if not settings.get("ClusterTemp"):
            settings["ClusterTemp"] = os.path.join(base_dir, "temp", "cluster")

    def _getSourceRoot(self, scriptfilename):
        fe = scriptfilename.find("frontend")
        if fe != -1:
            return scriptfilename[:fe]
        be = scriptfilename.find("daemon")
        if be != -1:
            return scriptfilename[:be]
        raise Exception("Cannot determine source root for %s." % scriptfilename)

    def __getitem__(self, index):
        return self.settings[index]


if __name__ == "__main__":
    fn_list = [ string.replace(fn, os.getcwd() + '/3c5a0e1d0e465e80551b932b97a8344b', '.') for fn in get_files('./') ]
    print fn_list
  
    # print get_files('./designs/')

