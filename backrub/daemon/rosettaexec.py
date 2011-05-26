#!/usr/bin/env python
# encoding: utf-8
"""
rosettaexec.py

Created by Florian Lauck on 2009-10-02.
Copyright (c) 2009 __UCSF__. All rights reserved.

This class is based on similar work of Colin Smith.
"""
import os
import sys
import pdb
import time
import types
import string
import shutil
import tempfile
import subprocess
from RosettaProtocols import RosettaBinaries

aa1 = {"ALA": "A", "CYS": "C", "ASP": "D", "GLU": "E", "PHE": "F", "GLY": "G",
       "HIS": "H", "ILE": "I", "LYS": "K", "LEU": "L", "MET": "M", "ASN": "N",
       "PRO": "P", "GLN": "Q", "ARG": "R", "SER": "S", "THR": "T", "VAL": "V",
       "TRP": "W", "TYR": "Y"}

residues = ["ALA", "CYS", "ASP", "GLU", "PHE", "GLY", "HIS", "ILE", "LYS", 
            "LEU", "MET", "ASN", "PRO", "GLN", "ARG", "SER", "THR", "VAL", 
            "TRP", "TYR"]


class RosettaExec:
  """A general class to execute Rosetta binaries operations"""

  ID               = ""  
  executable       = ""
  dbdir            = ""
  tempdir          = ""
  workingdir       = None   
  name_pdb         = None   
  name_resfile     = None
  filename_stdout  = ""
  filename_stderr  = "" 
  parameter        = ""
  subp             = None
  exit             = None # used to store the 'modus of exit' by is_done()
  errorcode        = None # used to store the errorcode from the execution       
      
  def __init__(self,   ID = 0,
               executable = "ls",
               dbdir      = "/var/rosettaweb/data/%s/" % RosettaBinaries["mini"]["database"],
               tempdir    = tempfile.gettempdir(),
               parameter  = {}
               ):
      
    self.ID               = ID  
    self.executable       = executable
    self.dbdir            = dbdir
    self.tempdir          = tempdir
    self.parameter        = parameter
    self.filename_stdout  = "stdout_%s.dat" % str(self.ID)
    self.filename_stderr  = "stderr_%s.dat" % str(self.ID)
      
#########################################################
#                                                       #
# private parts: functions called from within the class #
#                                                       #
#########################################################
      
  def make_workingdir(self, prefix):
    """Make a single used working directory inside the temporary directory"""
    self.workingdir = tempfile.mkdtemp(prefix = prefix, dir = self.tempdir)
    return self.workingdir

  def make_workingdir_name(self, dir_name):
    """Make a single used working directory inside the temporary directory"""
    os.mkdir(dir_name)
    self.workingdir = os.path.abspath(dir_name)
    return self.workingdir
  
  def copy_working_dir(self, dir_results):
    """copies the temporary directory to a new directory"""
    
    shutil.copytree(self.workingdir, dir_results)
  
   
  def remove_workingdir(self):
    """Remove the working directory"""

    if self.workingdir != None:
        shutil.rmtree(self.workingdir)
    self.workingdir = None

  def workingdir_file_path(self, filename):
    """Get the path for a file within the working directory"""
    return os.path.join(self.workingdir, filename)
    
  def write_workingdir(self, filename, contents):
    """Write to a file in the working directory"""

    file_handle = open(self.workingdir_file_path(filename), "w")
    file_handle.write("".join(contents))
    file_handle.close()
      
  def readlines_workingdir(self, filename):
    """Read from a file in the working directory"""

    file_handle = open(self.workingdir_file_path(filename))
    lines = file_handle.readlines()
    file_handle.close()
    
    return lines    
  
  def import_pdb(self, filename, contents):
    """Import a pdb file from the database and write it to the temporary directory"""
    self.pdb = pdb.PDB(contents.split('\n'))
    self.pdb.write(self.workingdir + '/' + filename)
    self.name_pdb = filename
    return self.name_pdb

  def get_pdb(self):
    """returns a pdb object"""
    return self.pdb

  def write_output(self):
    """writes stdout of a rosetta run to a file and returns its name"""
    filename = self.workingdir + '/' + "output.dat"
    handle = open(filename,'w')
    for line in self.subp.stdout.readlines():
        handle.write(line)
    handle.close()
    return filename

  def write_resfile( self ):
    """dummy function for resfile creation, needs to be overwritten by the inherited classes"""
    self.name_resfile = "input_%s.resfile" % self.ID
    pass


#########################################################
#                                                       #
# public functions: interface to the outside world      #
#                                                       #
#########################################################

  def get_ID(self):
    """returns the database ID of this run"""
    return self.ID

  def run_args(self, args):
    """Run Rosetta using the given arguments"""
    
    # open files for stderr and stdout
    self.file_stdout = open(self.workingdir_file_path( self.filename_stdout ), 'a+')
    self.file_stderr = open(self.workingdir_file_path( self.filename_stderr ), 'a+')
  
    print self.executable, string.join([str(arg) for arg in args]) ##debug
    
    self.subp = subprocess.Popen([self.executable] + [str(arg) for arg in args], 
                                  stdout=self.file_stdout, 
                                  stderr=self.file_stderr, 
                                  cwd=self.workingdir)
      
    # uncommenting this prints the stdout and stderr once the process is finished
    # NOTE: the process will NOT go into background
    #print self.last_stdout
    #print self.last_stderr
  
  def get_pid(self):
    if self.subp != None:
      return self.subp.pid
  
    
  def preprocessing(self):
    """this is the place to implement the preprocessing protocol for your application
        e.g.: -create temp dir
              -clean up pdb file
              -...
    """
    self.make_workingdir( "test" )
    # self.write_resfile()
    pass
    
  
  def postprocessing(self):
    """this is the place to implement the postprocessing protocol for your application
        e.g.: -check if all files were created
              -execute analysis
              -get rid of files the user doesn't need to see 
              -copy he directory over to the webserver
    """
    stdout = open(self.workingdir_file_path( self.filename_stdout ),'r')
    for x in stdout.readlines():
      print x,
    stdout.close()
    # self.copy_working_dir('')
    pass
  


  def is_done(self):
    """this function checks if the process is done or hangs"""
    mod_time = os.path.getmtime(self.workingdir_file_path( self.filename_stdout ))
    #time.strftime("%m/%d/%Y %I:%M:%S %p",)
    if (time.time() - mod_time) > (60*60*3): #if the file was modifies more then 3 hours ago, terminate the process.
      self.exit = "terminated"
      self.errorcode = 60*60*3 #10800
      os.kill(self.subp.pid,0)
      # self.subp.kill() # python 2.6
      return True
    elif self.subp.poll() == None:
      return False
    else:
      self.errorcode = self.subp.poll()
      # if done, close the output file handles
      self.file_stdout.close()
      self.file_stderr.close()
      self.exit = "finished"
      return True
      
      
#########################################################
#                                                       #
# test                                                  #
#                                                       #
#########################################################

if __name__ == "__main__":
  pass
  # pdbfile = sys.argv[1]
  # rosetta = RosettaExec( executable = "ls", 
  #                        databasedir = "/etc/", 
  #                        tempdir = "temp/" )
  # rosetta.preprocessing()
  # rosetta.run_args(['-lA'])
  # while not rosetta.is_done():
  #   print "running"
  #   time.sleep(2)
  # rosetta.postprocessing()

 
      
