#!/usr/bin/python2.4

###########################################################
#
# Colin Smith 2008
# modified by Florian Lauck
#
###########################################################
import os
import sys
sys.path.insert(0, "../common/")
import pdb
import time
import types
import string
import shutil
import tempfile
import subprocess
import chainsequence

#from molprobity_analysis import MolProbityAnalysis

aa1 = {"ALA": "A", "CYS": "C", "ASP": "D", "GLU": "E", "PHE": "F", "GLY": "G",
       "HIS": "H", "ILE": "I", "LYS": "K", "LEU": "L", "MET": "M", "ASN": "N",
       "PRO": "P", "GLN": "Q", "ARG": "R", "SER": "S", "THR": "T", "VAL": "V",
       "TRP": "W", "TYR": "Y"}

residues = ["ALA", "CYS", "ASP", "GLU", "PHE", "GLY", "HIS", "ILE", "LYS", 
            "LEU", "MET", "ASN", "PRO", "GLN", "ARG", "SER", "THR", "VAL", 
            "TRP", "TYR"]

class RosettaPlusPlus:
    """A class to execute Rosetta++ operations"""

    def __init__(self, ID, executable, datadir, tempdir, mini = False, auto_cleanup = False):
        
        self.ID           = ID
        self.mini         = mini
        self.pivot_res    = []
        self.executable   = executable
        self.datadir      = datadir
        self.tempdir      = tempdir
        self.auto_cleanup = auto_cleanup
        self.workingdir   = None
        self.last_stdout  = ""
        self.last_stderr  = ""
        self.last_energy  = ""
        self.name_pdb     = None
        self.name_resfile = None
        self._map_res_id  = None            # only used by mini
        self.filename_stdout = "stdout_%s.dat" % str(self.ID)
        self.filename_stderr = "stderr_%s.dat" % str(self.ID)
        self.exit         = None # used to store the 'modus of exit' by is_done()
        
        self.rosetta_is_done  = False
        

    
    def make_workingdir(self):
        """Make a single used working directory inside the temporary directory"""
        if self.mini:
          prefix = "mini_"
        else:
          prefix = "rpp_"
          
        self.workingdir = tempfile.mkdtemp(prefix = prefix, dir = self.tempdir)
        if not os.path.isdir(self.workingdir):
            raise os.error
        return self.workingdir
    
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

    def set_pdb(self, filename, contents):
        
        self.pdb = pdb.PDB(contents.split('\n'))
        #remove heteroatoms to avoid distractions of rosetta
        self.pdb.remove_hetatm()
        self.pdb.fix_chain_id()
        # fix it only if Rosetta++ is used ... THIS IS NOT THE ISSUE AND NEVER WAS! its a mini numbering problem
        #if not self.mini:
            #self.map_res_id = self.pdb.fix_residue_numbering()
        
        # mini has odd resid numbering behavior ... the pivot residues need to be numbered with absolute values:
        self._map_res_id = self.pdb.get_residue_mapping()
            
        self.pdb.write(self.workingdir + '/' + filename)
        self.name_pdb = filename
        return self.name_pdb
    
    def get_pdb(self):
        return self.pdb
    
    
    def get_ID(self):
        return self.ID
    
    def write_output(self):
        filename = self.workingdir + '/' + "output.dat"
        handle = open(filename,'w')
        for line in self.subp.stdout.readlines():
            handle.write(line)
        handle.close()
        return filename
        
        
    def write_paths(self):
    
        paths = """Rosetta Input/Output Paths (order essential)
path is first '/', './',or  '../' to next whitespace, must end with '/'
INPUT PATHS:
pdb1                            ./
pdb2                            ./
alternate data files            ./
fragments                       ./
structure dssp,ssa (dat,jones)  ./
sequence fasta,dat,jones        ./
constraints                     ./
starting structure              ./
data files                      %s/
OUTPUT PATHS:
movie                           ./
pdb path                        ./
score                           ./
status                          ./
user                            ./
FRAGMENTS: (use '*****' in place of pdb name and chain)
2                                      number of valid fragment files
3                                      frag file 1 size
aa*****03_05.???_v1_3                               name
9                                      frag file 2 size
aa*****09_05.???_v1_3                               name
-------------------------------------------------------------------------
CVS information:
$Revision: 20460 $
$Date: 2008-02-18 20:02:35 -0800 (Mon, 18 Feb 2008) $
$Author: possu $
this information may be out of date
-------------------------------------------------------------------------
""" % self.datadir

        self.write_workingdir("paths.txt", paths)
    
    def run_args(self, args):
        """Run Rosetta++ using the given arguments"""
        
        self.file_stdout = open(self.workingdir_file_path( self.filename_stdout ),'w')
        self.file_stderr = open(self.workingdir_file_path( self.filename_stderr ),'w')
        
        if len(self.pivot_res) > 0:
             args.append("-pivot_residues")
             self.pivot_res.sort()
             args.extend(self.pivot_res)
        
        self.command = self.executable + ' ' + string.join([str(arg) for arg in args]) ##debug
        print(self.command)
        # print [self.executable] + [str(arg) for arg in args]
        self.subp = subprocess.Popen( [self.executable] + [str(arg) for arg in args], 
                                      stdout=self.file_stdout, 
                                      stderr=self.file_stderr, 
                                      cwd=self.workingdir )
        
        ## NOTE: argh  subprocess.PIPE
        
        # LEAVE this commented, else the process will not go to background
        #print self.last_stdout
        #print self.last_stderr
        
        #self.write_workingdir("stdout", self.last_stdout)
        #self.write_workingdir("stderr", self.last_stderr)

    def get_pid(self):
      if self.subp != None:
        return self.subp.pid


    def start_molprobity(self):
      pass
      #bindir = string.join(self.executable.split('/')[:-1],'/')
      
      #self.molprobity = MolProbityAnalysis(ID=0,
      #                                     bin_dir=bindir,  #"/opt/rosettabackend/bin/",
      #                                     workingdir=self.workingdir,
      #                                     initial_structure=self.name_pdb)
      #self.molprobity.preprocessing()
      #self.molprobity.run()
    
    def end_molprobity(self):
      pass
      #self.molprobity.postprocessing()
      #self.molprobity.write_results()
      #self.molprobity.plot_results('molprobity_plot')
    

    def is_done(self):
      """this function checks if the process is done"""
      mod_time = os.path.getmtime(self.workingdir_file_path( self.filename_stdout ))
      #time.strftime("%m/%d/%Y %I:%M:%S %p",)
      if (time.time() - mod_time) > (60*60*3): #if the file was modifies more then 1 hour ago, terminate the process.
        self.exit = "terminated"
	try:
          self.subp.kill()
	except AttributeError:
	  return True
        return True
      elif self.subp.poll() == None:
        return False
      else:
        # if done, close the output file handles
        self.file_stdout.close()
        self.file_stderr.close()
        self.exit = "finished"
        return True

    # def is_done(self):
    #     if self.subp.poll() == None and not self.rosetta_is_done:
    #       #print self.subp.poll()
    #       return False
    #     elif self.subp.poll() != None and not self.rosetta_is_done:
    #       self.start_molprobity()
    #       self.rosetta_is_done = True
    #       return False        
    #     elif self.rosetta_is_done and not self.molprobity.is_done():
    #       return False
    #     elif self.rosetta_is_done and self.molprobity.is_done():
    #       self.end_molprobity()
    #       #(self.last_stdout, self.last_stderr) = self.subp.communicate()
    #       self.file_stdout.close()
    #       self.file_stderr.close()
    #       return True
    #     else: # impossible
    #       print 'impossible'
    #       return False

    def write_resfile( self, default_mode, mutations, backbone, name=None ):
        if name == None:
          name = "input"
        """create resfile from list of mutations and backbone"""
        output_handle = open(self.workingdir + "/%s.resfile" % name,'w')
        self.name_resfile = "input.resfile"
        
        if self.mini:
            output_handle.write("%s\nstart\n" % default_mode)
            for (key, value) in mutations.iteritems():  # { (chain, resID):["PIKAA","PHKL"] } + ("""111 A PIKAA I""")
                output_handle.write("%s %s %s %s\n" % (key[1], key[0], value[0], value[1]) )
            output_handle.write( "\n" )
            
            for (chain,resid) in backbone:
              if resid == 0:
                  # Python formats stupidly for 0
                  self.pivot_res.append( self._map_res_id[ '%s   0' % chain ] )
              else:
                  self.pivot_res.append( self._map_res_id[ '%s%4.i' % (chain, resid) ] )

        else:
            output_handle.write("""This file specifies which residues will be varied

 Column   2:  Chain
 Column   4-7:  sequential residue number
 Column   9-12:  pdb residue number
 Column  14-18: id  (described below)
 Column  20-40: amino acids to be used

 NATAA  => use native amino acid
 ALLAA  => all amino acids
 NATRO  => native amino acid and rotamer
 PIKAA  => select inividual amino acids
 POLAR  => polar amino acids
 APOLA  => apolar amino acids

 The following demo lines are in the proper format

 A    1    3 NATAA
 A    2    4 ALLAA
 A    3    6 NATRO
 A    4    7 NATAA
 B    5    1 PIKAA  DFLM
 B    6    2 PIKAA  HIL
 B    7    3 POLAR
 -------------------------------------------------
 start
""")
            # get chains
            seqs = chainsequence.ChainSequences()
            # create dict with key = chain ID, value = list of residue IDs
            chain_resnums = seqs.parse_atoms(self.pdb)
            # create working directory
            if self.workingdir == None:
                make_workingdir()
            # create paths file
            self.write_paths()
            # get list of chain IDs
            chains = chain_resnums.keys()
            chains.sort()
            counter_total = 1
    
            # iterate over chains and residues in chain
            for chain in chains:
                for resid in chain_resnums[chain]:
                    resid = int(resid)
                    # check which mode the residue at this position should have 
                    if mutations.has_key( (chain,resid) ):
                        code = mutations[ (chain,resid) ][0]
                        # check for mutations to be used
                        if code == "PIKAA":
                            aa = mutations[ (chain,resid) ][1]
                        else:
                            aa = " "
                    else:
                        code = default_mode
                        aa   = " "
                    # check if backrub should be applied for this residue
                    if (chain,resid) in backbone:
                        bb = "B"
                    else:
                        bb = " "
                    # write line of resfile for this residue
                    output_handle.write(" " + chain + " " + str(counter_total).rjust(4) + " " + str(resid).rjust(4) + " " + code + bb + " " + aa + "\n")
                    counter_total += 1
        ######## else end #########
        output_handle.write('\n')
        output_handle.close()
        
        return self.name_resfile


if __name__ == "__main__":
    pass
    # file = "1BRS.pdb"
    # rosetta = RosettaPlusPlus( executable = "/kortemmelab/home/flolauck/Projects/Rosetta/rosetta++/rosetta.gcc", datadir = "/kortemmelab/home/flolauck/Projects/Rosetta/rosetta_database", tempdir = "temp", auto_cleanup = False)
    # rosetta.make_workingdir()
    # handle = open(file, 'r')
    # filename_pdb = rosetta.set_pdb(file,handle.read())
    # handle.close()
    # filename_resfile = rosetta.write_resfile({ ('A',21):["PIKAA","PHKL"] }, [('A',12),('A',13),('A',14)] )
    # 
    # print filename_pdb, " ", filename_resfile
    # 
    # rosetta.run_args( ["-design", "-fixbb", "-s", filename_pdb, "-resfile", filename_resfile] )
    # 
    # while not rosetta.is_done():
    #     print "sleep 2 sec"
    #     time.sleep(2)
    # 
    # for line in rosetta.subp.stdout.readlines():
    #     print line.rstrip()
    
    

