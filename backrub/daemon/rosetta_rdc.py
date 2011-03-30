#!/usr/bin/python2.4

###########################################################
#
# Colin Smith 2008
# modified by Florian Lauck
#
###########################################################
import os
import sys
import pdb
import time
import types
import string ##debug
import shutil
import tempfile
import subprocess
import chainsequence


aa1 = {"ALA": "A", "CYS": "C", "ASP": "D", "GLU": "E", "PHE": "F", "GLY": "G",
       "HIS": "H", "ILE": "I", "LYS": "K", "LEU": "L", "MET": "M", "ASN": "N",
       "PRO": "P", "GLN": "Q", "ARG": "R", "SER": "S", "THR": "T", "VAL": "V",
       "TRP": "W", "TYR": "Y"}

residues = ["ALA", "CYS", "ASP", "GLU", "PHE", "GLY", "HIS", "ILE", "LYS", 
            "LEU", "MET", "ASN", "PRO", "GLN", "ARG", "SER", "THR", "VAL", 
            "TRP", "TYR"]

class Rosetta_RDC:
    """A class to execute Rosetta++ operations"""

    def __init__(self, ID = 0, mini = False, tempdir = tempfile.gettempdir() ):
        
        self.ID           = ID
        self.pdb          = None
        self.name_pdb     = None
        self.mini         = mini
        self.workingdir   = None
        self.tempdir      = tempdir
        self.filename_stdout = "stdout_%s.dat" % str(self.ID)
        self.filename_stderr = "stderr_%s.dat" % str(self.ID)
        self.exit         = None # used to store the 'modus of exit' by is_done()
        self.errorcode    = None

    
    def make_workingdir(self):
        """Make a single used working directory inside the temporary directory"""
        
        self.workingdir = tempfile.mkdtemp(prefix = "extra_", dir = self.tempdir)
        os.chmod( self.workingdir, 0777 )
    
    def remove_workingdir(self):
        """Remove the working directory"""
        
        if self.workingdir != None:
            shutil.rmtree(self.workingdir)
        self.workingdir = None
    
    def workingdir_file_path(self, filename):
        """Get the path for a file within the working directory"""
    
        return os.path.join(self.workingdir, filename)
   
    def get_ID(self):
        return self.ID
    
    def set_pdb(self, filename, contents):
        
        self.pdb = pdb.PDB(contents.split('\n'))
        #remove heteroatoms to avoid distractions of rosetta
        self.pdb.remove_hetatm()
        self.pdb.fix_chain_id()
        self.pdb.write(self.workingdir + '/' + filename)
        self.name_pdb = filename
        return self.name_pdb   
    
    def run_args(self, args):
        """Run Rosetta++ using the given arguments"""
        
        self.file_stdout = open(self.workingdir_file_path( self.filename_stdout ),'w')
        self.file_stderr = open(self.workingdir_file_path( self.filename_stderr ),'w')
       
        print string.join([str(arg) for arg in args]) ##debug
        self.subp = subprocess.Popen( [str(arg) for arg in args], 
                                      stdout=self.file_stdout, 
                                      stderr=self.file_stderr, 
                                      cwd=self.workingdir )
        
        # LEAVE this commented, else the process will not go to background
        #print self.last_stdout
        #print self.last_stderr
        
        #self.write_workingdir("stdout", self.last_stdout)
        #self.write_workingdir("stderr", self.last_stderr)
  
    def get_pid(self):
      if self.subp != None:
        return self.subp.pid

    def is_done(self):
        mod_time = os.path.getmtime(self.workingdir_file_path( self.filename_stdout ))
        #time.strftime("%m/%d/%Y %I:%M:%S %p",)
        if (time.time() - mod_time) > (60*60*24*5): #if the file was modifies more than 5 days ago, terminate the process.
          self.exit = "terminated"
          self.errorcode = 60*60*24*5 #432,000 
          try:
            self.subp.kill()
          except AttributeError: # this takes effect if the process already crashed
            return True
          return True
        elif self.subp.poll() == None:
            #print self.subp.poll()
            return False
        else:
            #(self.last_stdout, self.last_stderr) = self.subp.communicate()
            self.errorcode = self.subp.poll()
            self.file_stdout.close()
            self.file_stderr.close()
            self.exit = "finished"
            return True




if __name__ == "__main__":

    print "run"

    
    

