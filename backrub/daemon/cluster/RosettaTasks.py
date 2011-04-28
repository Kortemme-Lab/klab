#!/usr/bin/env python

# Set up array jobs for QB3 cluster.
import sys
import os
sys.path.insert(0, "../common/")
import time
import shutil
import glob
import tempfile
import re
from string import join
import decimal
import traceback
import rosettahelper
import itertools

import chainsequence       
import pdb
from analyze_mini import AnalyzeMini
# RosettaTasks.py

from ClusterTask import ClusterTask, ClusterScript, getClusterDatabasePath
from ClusterScheduler import TaskScheduler, RosettaClusterJob

# Helper functions
            
pathfilecontents = """Rosetta Input/Output Paths (order essential)
path is first '/', './',or  '../' to next whitespace, must end with '/'
INPUT PATHS:
pdb1                            %(workingdir)s/
pdb2                            %(workingdir)s/
alternate data files            %(workingdir)s/
fragments                       ./
structure dssp,ssa (dat,jones)  ./
sequence fasta,dat,jones        ./
constraints                     ./
starting structure              %(workingdir)s/
data files                      %(databasepath)s/
OUTPUT PATHS:
movie                           ./
pdb path                        %(workingdir)s/
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
"""

resfileheader = """This file specifies which residues will be varied
    
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
"""

def readFile(filepath):
    output_handle = open(filepath,'r')
    contents = output_handle.read()
    output_handle.close()
    return contents

def writeFile(filepath, contents):
    output_handle = open(filepath,'w')
    output_handle.write(contents)
    output_handle.close()

def printException(e):
    print("<exception>%s<br>%s</exception>" % (traceback.format_exc(), str(e)))
            
def getOutputFilenameSK(pdbname, index, suffix):
    return '%s_%04.i_%s.pdb'  % (pdbname, index, suffix)          

def getOutputFilenameHK(pdbname, index, suffix):
    return 'BR%s%s_%04.i.pdb' % (pdbname, suffix, index)

def getResIDs(params, justification = 0):
    design = []
    for partner in params['Partners']:
        if params['Designed'].get(partner):
            pm = params['Designed'][partner]
            for residue in pm:
                design.append('%s%s' % (partner, str(residue).rjust(justification)))
    return design

def make_seqtol_resfile( pdb, params, radius, residue_ids = None):
    """create a resfile for the chains
       Returns True, contents_of_resfile if a non-empty sequence tolerance residue file is made 
       Returns False, error_message if the sequence tolerance residue file is empty 
       residues in interface: NATAA (conformation can be changed)
       residues mutation: PIKAA ADEFGHIKLMNPQRSTVWY (design sequence)"""
        
    # get all residues:
    if not residue_ids:
        residue_ids = pdb.aa_resids() #todo: cache these values locally on first access and clear on pdb editing
    # turn list of ints in chainid, resid strings
    # e.g. design := ['A  23', 'B 123', 'A1234']
        
    # Compile a formatted list of designed residues
    design = getResIDs(params, justification = 4)
        
    # get the neighbors for each residue:
    resentry = {}            
    neighbor_lists = pdb.fastneighbors2( float(radius), design, atom = " CA ")

    # Add any residues neighboring designed residues to the flexible set
    for designres, neighbors in neighbor_lists.items():
        for neighbor in neighbors:
            resentry["%s %s" % (neighbor[1:].strip(), neighbor[0])] = " NATAA\n"  
        
    #for res in design:
    #    for neighbor in neighbor_lists.get(res) or []:
    #        resentry["%s %s" % (neighbor[1:].strip(), neighbor[0])] = " NATAA\n"  
    # Add the designed residues to the designed set, overriding any existing flexible entries
    for res in design:
        resentry["%s %s" % (res[1:].strip(), res[0])] = " PIKAA ADEFGHIKLMNPQRSTVWY\n"        
    
    if not resentry:
        return False, "The chosen designed residues resulting in an empty resfile and so could not be used."    
    
    contents = 'NATRO\nstart\n'
    for k,v in iter(sorted(resentry.iteritems())):
        contents += k + v
        
    return True, contents

# Tasks

class BackrubClusterTask(ClusterTask):

    # additional attributes
    residues      = {}   # contains the residues and their modes according to rosetta: { (chain, resID):["PIKAA","PHKL"] }
    pivot_res     = []   # list of pivot residues, consecutively numbered from 1 [1,...]
    map_res_id    = {}   # contains the mapping from (chain,resid) to pivot_res
    prefix = "backrub"
    
    def __init__(self, workingdir, targetdirectory, parameters, resfile, name=""):
        self.resfile = resfile
        super(BackrubClusterTask, self).__init__(workingdir, targetdirectory, '%s_%d.cmd' % (self.prefix, parameters["ID"]), parameters, name)          
    
    def _initialize(self):
        self._prepare_backrub()
        parameters = self.parameters
        
        self.parameters["ntrials"] = 10000 # todo: should be 10000 on the live webserver
        if True: #read_config_file()["server_name"] == 'albana.ucsf.edu':
            self.parameters["ntrials"] = 10   
    
        # Setup backrub
        ct = ClusterScript(self.workingdir, parameters["binary"])
        args = [ct.getBinary("backrub"),  
                "-database %s" % ct.getDatabaseDir(), 
                "-s %s/%s" % (ct.getWorkingDir(), parameters["pdb_filename"]),
                "-ignore_unrecognized_res", 
                "-nstruct %d" % parameters["nstruct"],
                "-backrub:ntrials %d" % parameters["ntrials"], 
                "-pivot_atoms CA"]
        if self.resfile:
            args.append("-resfile %s/%s" % (ct.getWorkingDir(), self.resfile))
        if len(self.pivot_res) > 0:
            args.append("-pivot_residues")
            self.pivot_res.sort()
            args.extend([str(resid) for resid in self.pivot_res])

        commandline = join(args, " ")
        self.script = ct.createScript([commandline], type="Backrub")

    def _prepare_backrub( self ):
        """prepare data for a full backbone backrub run"""
        
        self.pdb = pdb.PDB(self.parameters["pdb_info"].split('\n'))
        self.map_res_id = self.parameters["map_res_id"] 
        self.residue_ids = self.pdb.aa_resids()

        # backrub is applied to all residues: append all residues to the backrub list
        backrub       = []   # residues to which backrub should be applied: [ (chain,resid), ... ]
        for res in self.residue_ids:
            x = [ res[0], res[1:].strip() ] # 0: chain ID, 1..: resid
            if len(x) == 1:
                backrub.append( ( "_", int(x[0].lstrip())) )
            else:
                backrub.append( ( x[0], int(x[1].lstrip())) )
               
        # translate resid to absolute mini rosetta res ids
        for residue in backrub:
            self.pivot_res.append( self.map_res_id[ '%s%4.i' % residue  ] )
                
    
    def retire(self):
        passed = super(BackrubClusterTask, self).retire()
        
        #todo: This will copy the files from the cluster submission host back to the originating host
        self._status('shutil.copytree(%s %s")' % (self.workingdir, self.targetdirectory))
        
        for file in glob.glob(self._workingdir_file_path("*low.pdb")):
            self._status('copying %s' % file)
            shutil.copy(file, self.targetdirectory)
        for file in glob.glob(self._workingdir_file_path("*last.pdb")):
            self._status('copying %s' % file)
            shutil.copy(file, self.targetdirectory)
            
        # Run the analysis on the originating host
        errors = []
        # check whether files were created (and write the total scores to a file)
        for x in range(1, self.parameters['nstruct']+1):
            low_file   = self._targetdir_file_path(getOutputFilenameSK(self.parameters["pdbRootname"], x, "low"))          
            last_file  = self._targetdir_file_path(getOutputFilenameSK(self.parameters["pdbRootname"], x, "last"))          

            if not os.path.exists( low_file ): 
                errors.append('%s missing' % low_file)
            if not os.path.exists( last_file ):
                errors.append('%s missing' % ( last_file ))
        
        if self.filename_stdout and os.path.exists(self._targetdir_file_path( self.filename_stdout )):
            Analysis = AnalyzeMini(filename=self._targetdir_file_path( self.filename_stdout ))
            Analysis.analyze(outfile=self._targetdir_file_path('backrub_scores.dat'))
        else:
            errors.append("Standard output is missing; no analysis was performed.")
                    
        # At this stage we are actually done but do not mark ourselves as completed otherwise the scheduler will get confused
        if errors:
            errs = join(errors,"</error>\n\t<error>")
            print("<errors>\n\t<error>%s</error>\n</errors>" % errs)
            self.state = FAILED_TASK
            printException(e)
            return False
          
        return passed
        
            
class SequenceToleranceClusterTask(ClusterTask):
           
    prefix = "seqtol"
       
    def __init__(self, workingdir, targetdirectory, parameters, resfile, name=""):
        self.resfile = resfile
        super(SequenceToleranceClusterTask, self).__init__(workingdir, targetdirectory, '%s_%d.cmd' % (self.prefix, parameters["ID"]), parameters, name)          

    def _initialize(self):
        parameters = self.parameters
        
        self.low_files = [getOutputFilenameSK(parameters["pdbRootname"], i + 1, "low") for i in range(parameters["nstruct"])]
        self.prefixes = [lfilename[:-4] for lfilename in self.low_files]
        self.low_files = [self._workingdir_file_path(lfilename) for lfilename in self.low_files]
        self.numtasks = parameters["nstruct"]
        
        parameters["pop_size"] = 2000 # todo: should be 2000 on the live webserver
        if True: #read_config_file()["server_name"] == 'albana.ucsf.edu':
            self.parameters["pop_size"] = 20
        
        # Setup backrub
        ct = ClusterScript(self.workingdir, parameters["binary"], numtasks = self.numtasks, dataarrays = {"lowfiles" : self.low_files, "prefixes" : self.prefixes})
        commandlines = ['# Run sequence tolerance', '',
            join(
                [ct.getBinary("sequence_tolerance"),  
                "-database %s" % ct.getDatabaseDir(), 
                "-s $lowfilesvar",
                "-packing:resfile %s/%s" % (self.workingdir, self.resfile),
                "-ex1 -ex2 -extrachi_cutoff 0",
                "-score:ref_offsets TRP 0.9",  # todo: Ask Colin
                "-ms:generations 5",
                "-ms:pop_size %d" % parameters["pop_size"],
                "-ms:pop_from_ss 1",
                "-ms:checkpoint:prefix $prefixesvar",
                "-ms:checkpoint:interval 200",
                "-ms:checkpoint:gz",
                "-out:prefix $prefixesvar",
                "-seq_tol:fitness_master_weights %s" % join(map(str,parameters["Weights"]), " ") ])]
        self.script = ct.createScript(commandlines, type="SequenceTolerance")

    def retire(self):
        #try:
            sr = super(SequenceToleranceClusterTask, self).retire()
            self._copyFilesBackToHost(["*.pdb", "*.gz", "*.resfile"])
            return sr
        #except Exception, e:
        #    self.state = FAILED_TASK
        #    printException(e)
        #    raise
        #    return False
        
        
# Sequence Tolerance HK Tasks        

#todo: Add a required files list to all tasks and check before running

class MinimizationSeqTolHKClusterTask(ClusterTask):
                     
    prefix = "minimization"
                     
    def __init__(self, workingdir, targetdirectory, parameters, resfile, name=""):
        self.resfile = resfile
        super(MinimizationSeqTolHKClusterTask, self).__init__(workingdir, targetdirectory, '%s_%d.cmd' % (self.prefix, parameters["ID"]), parameters, name)          
        
    def _initialize(self):
        parameters = self.parameters

        # Setup minimization
        self._status("Running minimization")
        ct = ClusterScript(self.workingdir, parameters["binary"])
        args = [ct.getBinary("minimize"),  
                "-series", "MN",
                "-protein", parameters["pdbRootname"],
                "-chain", "_", 
                "-s %s" % parameters["pdb_filename"],
                "-paths", "paths.txt",
                "-resfile", "%s" % self.resfile,
                "-farlx", "-minimize", "-fa_input",
                "-sc_only", "-relax", 
                "-read_all_chains", "-use_input_sc", 
                "-fixbb", "-try_both_his_tautomers",
                "-ex1", "-ex2", "-ex1aro", "-ex2aro", 
                "-extrachi_cutoff", "-1",
                "-ndruns", "1", 
                "-use_pdb_numbering", 
                "-skip_missing_residues",
                "-norepack_disulf", "-find_disulf"]
                                
        commandline = join(args, " ")
        self.script = ct.createScript([commandline], type="Minimization")

    def retire(self):
        passed = super(MinimizationSeqTolHKClusterTask, self).retire()
        wdpath = self._workingdir_file_path
        self._status('shutil.copytree(%s %s")' % (self.workingdir, self.targetdirectory))
        try:
            os.rename(wdpath(self.parameters["pdb_filename"]), wdpath("%s_submission.pdb" % self.parameters["pdbRootname"]))
            os.rename(wdpath("MN%s_0001.pdb" % self.parameters["pdbRootname"]), wdpath(self.parameters["pdb_filename"]))
            os.remove(wdpath("MN%s.fasc" % self.parameters["pdbRootname"]))
            self._copyFilesBackToHost()
        except Exception, e:
            self.state = FAILED_TASK
            printException(e)
            return False
                               
        # At this stage we are actually done but do not mark ourselves as completed otherwise the scheduler will get confused
        return passed

class BackrubClusterTaskHK(ClusterTask):

    prefix = "backrub"
                
    def __init__(self, workingdir, targetdirectory, parameters, resfile, name=""):
        self.resfile = resfile
        super(BackrubClusterTaskHK, self).__init__(workingdir, targetdirectory, '%s_%d.cmd' % (self.prefix, parameters["ID"]), parameters, name)          
    
    def _initialize(self):
        parameters = self.parameters
        self._prepare_backrub()
                
        self.parameters["ntrials"] = 10000 # todo: should be 10000 on the live webserver
        if True: #read_config_file()["server_name"] == 'albana.ucsf.edu':
            self.parameters["ntrials"] = 10   

        # Setup backrub
        ct = ClusterScript(self.workingdir, parameters["binary"])
        args = [ct.getBinary("backrub"),  
                  "-paths", "%s/paths.txt" % ct.getWorkingDir(),
                  "-pose1","-backrub_mc",
                  "-fa_input",
                  "-norepack_disulf", "-find_disulf",
                  "-s %s" % parameters["pdb_filename"],
                  "-read_all_chains" ] + self.parameters["chain_parameter"] + ["-series","BR",
                  "-protein", self.parameters['pdbRootname'],
                  "-resfile", "%s" % self.resfile,
                  "-bond_angle_params","bond_angle_amber",
                  "-use_pdb_numbering",
                  "-ex1","-ex2",
                  "-skip_missing_residues",
                  "-extrachi_cutoff","0",
                  "-max_res", "12", 
                  "-only_bb", ".5", 
                  "-only_rot", ".5",
                  "-nstruct %d" % self.parameters['nstruct'],
                  "-ntrials %d" % self.parameters['ntrials']]
        
        commandline = join(args, " ")
        self.script = ct.createScript([commandline], type="Backrub")
    
    
    def _prepare_backrub( self ):
        """prepare data for a full backbone backrub run"""
        
        self.pdb = pdb.PDB(self.parameters["pdb_info"].split('\n'))
        
        # Specific to HK Backrub
        resid2type = self.pdb.aa_resid2type()
        chain_parameter = []
        for chain in self.pdb.chain_ids():
            chain_parameter.append("-chain")
            chain_parameter.append(str(chain))
        self.parameters["chain_parameter"] = chain_parameter

                
    def retire(self):
        passed = super(BackrubClusterTaskHK, self).retire()
        
        #todo: This will copy the files from the cluster submission host back to the originating host
        wdpath = self._workingdir_file_path
        self._status('shutil.copytree(%s %s")' % (self.workingdir, self.targetdirectory))
        try:
            shutil.copy(wdpath("backrub.resfile"), self.targetdirectory)

            for file in glob.glob(self._workingdir_file_path("*low*.pdb")):
                self._status('copying %s' % file)
                shutil.copy(file, self.targetdirectory)
            for file in glob.glob(self._workingdir_file_path("*last*.pdb")):
                self._status('copying %s' % file)
                shutil.copy(file, self.targetdirectory)
                
            # Run the analysis on the originating host
            errors = []
            # check whether files were created
            for x in range(1, int(self.parameters['nstruct'])+1):
                low_file  = self._targetdir_file_path(getOutputFilenameHK(self.parameters['pdbRootname'], x, "low"))
                last_file = self._targetdir_file_path(getOutputFilenameHK(self.parameters['pdbRootname'], x, "last"))
                
                if not os.path.exists( low_file ): 
                    errors.append('%s missing' % low_file)
                if not os.path.exists( last_file ):
                    errors.append('%s missing' % ( last_file ))
                
                shutil.copy( low_file, self.workingdir + '/' + low_file.split('/')[-1] )

            # At this stage we are actually done but do not mark ourselves as completed otherwise the scheduler will get confused
            if errors:
                errs = join(errors,"</error>\n\t<error>")
                print("<errors>\n\t<error>%s</error>\n</errors>" % errs)
                passed = False
                    
            return passed

        except Exception, e:
            self.state = FAILED_TASK
            printException(e)
            return False

class SequenceToleranceHKClusterTask(ClusterTask):
    
    prefix = "seqtol"
       
    def __init__(self, workingdir, targetdirectory, parameters, resfile, name=""):
        self.resfile = resfile
        super(SequenceToleranceHKClusterTask, self).__init__(workingdir, targetdirectory, '%s_%d.cmd' % (self.prefix, parameters["ID"]), parameters, name)          
    
    def _initialize(self):
        parameters = self.parameters
        
        self.low_files = [getOutputFilenameHK(parameters["pdbRootname"], i + 1, "low") for i in range(parameters["nstruct"])]
        self.prefixes = [lfilename[:-4] for lfilename in self.low_files]
        self.numtasks = parameters["nstruct"]
        
        parameters["pop_size"] = 2000 # todo: should be 2000 on the live webserver
        if True: #read_config_file()["server_name"] == 'albana.ucsf.edu':
            self.parameters["pop_size"] = 20
        
        # Setup backrub
        # todo: Could use > seqtol_${SGE_TASK_ID}_stdout.txt 2> seqtol_${SGE_TASK_ID}_stderr.txt
        ct = ClusterScript(self.workingdir, parameters["binary"], numtasks = self.numtasks, dataarrays = {"lowfiles" : self.low_files, "prefixes" : self.prefixes})
        commandlines = ['# Run sequence tolerance', '',
            join(
                [ct.getBinary("sequence_tolerance"),  
                "-design", "-multistate", 
                "-read_all_chains", "-fixbb",
                "-use_pdb_numbering", "-try_both_his_tautomers",
                "-ex1 -ex2 -ex1aro -ex2aro -extrachi_cutoff -1",
                "-ndruns 1",
                "-resfile %s" % self.resfile,
                "-s $lowfilesvar",
                "-paths paths.txt ",
                "-generations 5",
                "-population %d" % self.parameters["pop_size"],
                "-bind_thresh 0.01",
                "-fold_thresh 0.01",
                "-ms_fit 1 -no_bb_terms", 
                "-output_all_structures",
                "-norepack_disulf", 
                "-find_disulf"])]        
        self.script = ct.createScript(commandlines, type="SequenceTolerance")

    def retire(self):
        sr = super(SequenceToleranceHKClusterTask, self).retire()
        return sr and True
        #todo: This will copy the files from the cluster submission host back to the originating host
              
    
# Cluster jobs

class SequenceToleranceJobSK(RosettaClusterJob):

    map_res_id = {}
    suffix = "seqtolSK"

    def __init__(self, parameters, tempdir, targetroot):
        # The tempdir is the one on the submission host e.g. chef
        # targetdirectory is the one on your host e.g. your PC or the webserver
        # The taskdirs are subdirectories of the tempdir on the submission host and the working directories for the tasks
        # The targetdirectories of the tasks are subdirectories of the targetdirectory named like the taskdirs
        super(SequenceToleranceJobSK, self).__init__(parameters, tempdir, targetroot)
    
    def _initialize(self):
        self._status("Creating RosettaSeqTol object in %s." % self.targetdirectory)
        parameters = self.parameters
        
        # Create input files        
        self._import_pdb(parameters["pdb_filename"], parameters["pdb_info"])
        self._write_backrub_resfile()
        self._write_seqtol_resfile()
        
        scheduler = TaskScheduler(self.workingdir, files = [parameters["pdb_filename"], self.seqtol_resfile, self.backrub_resfile])
        
        targetsubdirectory = "backrub"
        taskdir = self._make_taskdir(targetsubdirectory, [parameters["pdb_filename"], self.backrub_resfile])
        brTask = BackrubClusterTask(taskdir, os.path.join(self.targetdirectory, targetsubdirectory), parameters, self.backrub_resfile, name="Backrub step for sequence tolerance protocol")
            
        targetsubdirectory = "sequence_tolerance"
        taskdir = self._make_taskdir(targetsubdirectory, [self.seqtol_resfile])
        stTask = SequenceToleranceClusterTask(taskdir, os.path.join(self.targetdirectory,targetsubdirectory), parameters, self.seqtol_resfile, name="Sequence tolerance step for sequence tolerance protocol")
        stTask.addPrerequisite(brTask, [getOutputFilenameSK(parameters["pdbRootname"], i + 1, "low") for i in range(parameters["nstruct"])])
         
        scheduler.addInitialTasks(brTask)
        self.scheduler = scheduler

    def _analyze(self):
        # Run the analysis on the originating host
        
        self._status("Analyzing results")
        # run Colin's analysis script: filtering and profiles/motifs
        thresh_or_temp = self.parameters['kT']
        
        weights = self.parameters['Weights']
        fitness_coef = 'c(%s' % weights[0]
        for i in range(1, len(weights)):
            fitness_coef += ', %s' % weights[i]
        fitness_coef += ')'
        
        type_st = '\\"boltzmann\\"'
        prefix  = '\\"tolerance\\"'
        percentile = '.5'
        
        return True
        #todo: server_root not defined on chef
        
        # todo when webserver is calling this 
        cmd = '''/bin/echo "process_seqtol(\'%s\', %s, %s, %s, %s, %s);\" \\
                  | /bin/cat %sdaemon/specificity.R - \\
                  | /usr/bin/R --vanilla''' % ( self.targetdirectory, fitness_coef, thresh_or_temp, type_st, percentile, prefix, server_root)
                         
        self._status(cmd)
            
        # open files for stderr and stdout 
        self.file_stdout = open(self._targetdir_file_path( self.filename_stdout ), 'a+')
        self.file_stderr = open(self._targetdir_file_path( self.filename_stderr ), 'a+')
        self.file_stdout.write("*********************** R output ***********************\n")
        subp = subprocess.Popen(cmd, stdout=self.file_stdout, stderr=self.file_stderr, cwd=self.targetdirectory, shell=True, executable='/bin/bash')
                
        while True:
            returncode = subp.poll()
            if returncode != None:
                if returncode != 0:
                    sys.stderr.write("An error occurred during the postprocessing script. The errorcode is %d." % returncode)
                    raise PostProcessingException
                break;
            time.sleep(2)
        self.file_stdout.close()
        self.file_stderr.close()
        
        count = 0
        if not os.path.exists( self._targetdir_file_path("tolerance_sequences.fasta") ) and count < 10 :
            time.sleep(1) # make sure the fasta file gets written
            count += 1
        
        #todo: should fail gracefully here if the fasta file still isn't written
          
        # create weblogo from the created fasta file
        seqs = read_seq_data(open(self._targetdir_file_path("tolerance_sequences.fasta")))
        logo_data = LogoData.from_seqs(seqs)
        logo_data.alphabet = std_alphabets['protein'] # this seems to affect the coloring, but not the actual motif
        logo_options = LogoOptions()
        logo_options.title = "Sequence profile"
        logo_options.number_interval = 1
        logo_options.color_scheme = std_color_schemes["chemistry"]
        
        ann = getResIDs(self.parameters)
        logo_options.annotate = ann
        
        logo_format = LogoFormat(logo_data, logo_options)
        png_print_formatter(logo_data, logo_format, open(self._targetdir_file_path( "tolerance_motif.png" ), 'w'))
        
        # let's just quickly delete the *last.pdb and generation files:
        list_files = os.listdir(self._targetdir_file_path)
        list_files.sort()
        for pdb_fn in rosettahelper.grep('%s_[0-9]_[0-9]{4}_last\.pdb' % (self.parameters['pdb_id']), list_files):
            os.remove( self._targetdir_file_path(pdb_fn) )
        for pdb_fn in rosettahelper.grep('%s_[0-9]_[0-9]{4}_low\.ga\.generations\.gz' % (self.parameters['pdb_id']), list_files):
            os.remove( self._targetdir_file_path(pdb_fn) )
        
        return True
    
    def _import_pdb(self, filename, contents):
        """Import a pdb file from the database and write it to the temporary directory"""
        
        self.pdb = pdb.PDB(contents.split('\n'))
      
        # remove everything but the chosen chains or keep all chains if the list is empty
        # pdb_content is passed directly to backrub so remove the pruned chain lines before the backrub
        self.pdb.pruneChains(self.parameters['Partners'])
        self.pdb.remove_hetatm()  # rosetta doesn't like heteroatoms so let's remove them
        self.parameters['pdb_content'] = join(self.pdb.lines, '\n')        
        
        # internal mini resids don't correspond to the pdb file resids
        # the pivot residues need to be numbered consecutively from 1 up
        self.map_res_id = self.pdb.get_residue_mapping()
        self.parameters["map_res_id"] = self.map_res_id 
        
        self.pdb.write(self._workingdir_file_path(filename))
            
    def _write_backrub_resfile( self ):
        """create a resfile of premutations for the backrub"""
               
        # Write out the premutated residues
        s = ""
        params = self.parameters
        for partner in params['Partners']:
            if params['Premutated'].get(partner):
                pm = params['Premutated'][partner]
                for residue in pm:
                    #todo: check that residue exists -  # get all residues:  residue_ids     = self.pdb.aa_resids()
                    s += ("%d %s PIKAA %s\n" % (residue, partner, pm[residue]))
        
        # Only create a file if there are any premutations
        self.backrub_resfile = "backrub_%s.resfile" % self.parameters["ID"]
        writeFile(self._workingdir_file_path(self.backrub_resfile), 'NATAA\nstart\n%s\n' % s)
        
        
    def _write_seqtol_resfile( self ):
        """create a resfile for the chains
            residues in interface: NATAA (conformation can be changed)
            residues mutation: PIKAA ADEFGHIKLMNPQRSTVWY (design sequence)"""
        
        resfileHasContents, contents = make_seqtol_resfile( self.pdb, self.parameters, self.parameters['radius'], self.pdb.aa_resids())
                
        if resfileHasContents:
            self.seqtol_resfile = "seqtol_%s.resfile" % self.parameters["ID"]
            writeFile(self._workingdir_file_path(self.seqtol_resfile), "%s\n" % contents)
        else:
            sys.stderr.write("An error occurred during the sequence tolerance execution. The chosen designed residues resulting in an empty resfile and so could not be used.")
            raise SequenceToleranceException          

import pprint
class SequenceToleranceMultiJobSK(RosettaClusterJob):

    map_res_id = {}
    suffix = "seqtolMultiSK"

    def __init__(self, parameters, tempdir, targetroot):
        # The tempdir is the one on the submission host e.g. chef
        # targetdirectory is the one on your host e.g. your PC or the webserver
        # The taskdirs are subdirectories of the tempdir on the submission host and the working directories for the tasks
        # The targetdirectories of the tasks are subdirectories of the targetdirectory named like the taskdirs
        super(SequenceToleranceMultiJobSK, self).__init__(parameters, tempdir, targetroot)
    
    @staticmethod
    def _tmultiply(biglist, nextlist):
        e = []
        for aa in nextlist[2]:
            e.append([(nextlist[0], nextlist[1], aa)])
        if biglist == []:
            return e
        else:
            newlist = []
            for x in biglist:
                for y in e:
                    el = []
                    if type(x) == type(e):
                        el.extend(x)
                    else:
                        el.append(x)
                    el.extend(y)
                    newlist.append(el)
            return newlist

    def _write_backrub_resfiles(self):
        premut = []
        for chain, reslist in self.parameters["Premutated"].iteritems():
            for resid, premutations in reslist.iteritems():
                premut.append((chain, resid, premutations))

        choices = []
        for i in range(len(premut)):
            choices = SequenceToleranceMultiJobSK._tmultiply(choices, premut[i])
        pprint.pprint(choices) 
        print(len(choices)) 


    def _initialize(self):
        self._status("Creating RosettaSeqTol multi object in %s." % self.targetdirectory)
        parameters = self.parameters
        
        # Create input files
        self._write_backrub_resfiles()
        sys.exit(1)        
        self._import_pdb(parameters["pdb_filename"], parameters["pdb_info"])
        self._write_backrub_resfile()
        self._write_seqtol_resfile()
        
        scheduler = TaskScheduler(self.workingdir, files = [parameters["pdb_filename"], self.seqtol_resfile, self.backrub_resfile])
        
        targetsubdirectory = "backrub"
        taskdir = self._make_taskdir(targetsubdirectory, [parameters["pdb_filename"], self.backrub_resfile])
        brTask = BackrubClusterTask(taskdir, os.path.join(self.targetdirectory, targetsubdirectory), parameters, self.backrub_resfile, name="Backrub step for sequence tolerance protocol")
            
        targetsubdirectory = "sequence_tolerance"
        taskdir = self._make_taskdir(targetsubdirectory, [self.seqtol_resfile])
        stTask = SequenceToleranceClusterTask(taskdir, os.path.join(self.targetdirectory,targetsubdirectory), parameters, self.seqtol_resfile, name="Sequence tolerance step for sequence tolerance protocol")
        stTask.addPrerequisite(brTask, [getOutputFilenameSK(parameters["pdbRootname"], i + 1, "low") for i in range(parameters["nstruct"])])
         
        scheduler.addInitialTasks(brTask)
        self.scheduler = scheduler

    def _analyze(self):
        # Run the analysis on the originating host
        
        self._status("Analyzing results")
        # run Colin's analysis script: filtering and profiles/motifs
        thresh_or_temp = self.parameters['kT']
        
        weights = self.parameters['Weights']
        fitness_coef = 'c(%s' % weights[0]
        for i in range(1, len(weights)):
            fitness_coef += ', %s' % weights[i]
        fitness_coef += ')'
        
        type_st = '\\"boltzmann\\"'
        prefix  = '\\"tolerance\\"'
        percentile = '.5'
        
        return True
        #todo: server_root not defined on chef
        
        # todo when webserver is calling this 
        cmd = '''/bin/echo "process_seqtol(\'%s\', %s, %s, %s, %s, %s);\" \\
                  | /bin/cat %sdaemon/specificity.R - \\
                  | /usr/bin/R --vanilla''' % ( self.targetdirectory, fitness_coef, thresh_or_temp, type_st, percentile, prefix, server_root)
                         
        self._status(cmd)
            
        # open files for stderr and stdout 
        self.file_stdout = open(self._targetdir_file_path( self.filename_stdout ), 'a+')
        self.file_stderr = open(self._targetdir_file_path( self.filename_stderr ), 'a+')
        self.file_stdout.write("*********************** R output ***********************\n")
        subp = subprocess.Popen(cmd, stdout=self.file_stdout, stderr=self.file_stderr, cwd=self.targetdirectory, shell=True, executable='/bin/bash')
                
        while True:
            returncode = subp.poll()
            if returncode != None:
                if returncode != 0:
                    sys.stderr.write("An error occurred during the postprocessing script. The errorcode is %d." % returncode)
                    raise PostProcessingException
                break;
            time.sleep(2)
        self.file_stdout.close()
        self.file_stderr.close()
        
        count = 0
        if not os.path.exists( self._targetdir_file_path("tolerance_sequences.fasta") ) and count < 10 :
            time.sleep(1) # make sure the fasta file gets written
            count += 1
        
        #todo: should fail gracefully here if the fasta file still isn't written
          
        # create weblogo from the created fasta file
        seqs = read_seq_data(open(self._targetdir_file_path("tolerance_sequences.fasta")))
        logo_data = LogoData.from_seqs(seqs)
        logo_data.alphabet = std_alphabets['protein'] # this seems to affect the coloring, but not the actual motif
        logo_options = LogoOptions()
        logo_options.title = "Sequence profile"
        logo_options.number_interval = 1
        logo_options.color_scheme = std_color_schemes["chemistry"]
        
        ann = getResIDs(self.parameters)
        logo_options.annotate = ann
        
        logo_format = LogoFormat(logo_data, logo_options)
        png_print_formatter(logo_data, logo_format, open(self._targetdir_file_path( "tolerance_motif.png" ), 'w'))
        
        # let's just quickly delete the *last.pdb and generation files:
        list_files = os.listdir(self._targetdir_file_path)
        list_files.sort()
        for pdb_fn in rosettahelper.grep('%s_[0-9]_[0-9]{4}_last\.pdb' % (self.parameters['pdb_id']), list_files):
            os.remove( self._targetdir_file_path(pdb_fn) )
        for pdb_fn in rosettahelper.grep('%s_[0-9]_[0-9]{4}_low\.ga\.generations\.gz' % (self.parameters['pdb_id']), list_files):
            os.remove( self._targetdir_file_path(pdb_fn) )
        
        return True
    
    def _import_pdb(self, filename, contents):
        """Import a pdb file from the database and write it to the temporary directory"""
        
        self.pdb = pdb.PDB(contents.split('\n'))
      
        # remove everything but the chosen chains or keep all chains if the list is empty
        # pdb_content is passed directly to backrub so remove the pruned chain lines before the backrub
        self.pdb.pruneChains(self.parameters['Partners'])
        self.pdb.remove_hetatm()  # rosetta doesn't like heteroatoms so let's remove them
        self.parameters['pdb_content'] = join(self.pdb.lines, '\n')        
        
        # internal mini resids don't correspond to the pdb file resids
        # the pivot residues need to be numbered consecutively from 1 up
        self.map_res_id = self.pdb.get_residue_mapping()
        self.parameters["map_res_id"] = self.map_res_id 
        
        self.pdb.write(self._workingdir_file_path(filename))
            
    def _write_backrub_resfile( self ):
        """create a resfile of premutations for the backrub"""
               
        # Write out the premutated residues
        s = ""
        params = self.parameters
        for partner in params['Partners']:
            if params['Premutated'].get(partner):
                pm = params['Premutated'][partner]
                for residue in pm:
                    #todo: check that residue exists -  # get all residues:  residue_ids     = self.pdb.aa_resids()
                    s += ("%d %s PIKAA %s\n" % (residue, partner, pm[residue]))
        
        # Only create a file if there are any premutations
        self.backrub_resfile = "backrub_%s.resfile" % self.parameters["ID"]
        writeFile(self._workingdir_file_path(self.backrub_resfile), 'NATAA\nstart\n%s\n' % s)
        
        
    def _write_seqtol_resfile( self ):
        """create a resfile for the chains
            residues in interface: NATAA (conformation can be changed)
            residues mutation: PIKAA ADEFGHIKLMNPQRSTVWY (design sequence)"""
        
        resfileHasContents, contents = make_seqtol_resfile( self.pdb, self.parameters, self.parameters['radius'], self.pdb.aa_resids())
                
        if resfileHasContents:
            self.seqtol_resfile = "seqtol_%s.resfile" % self.parameters["ID"]
            writeFile(self._workingdir_file_path(self.seqtol_resfile), "%s\n" % contents)
        else:
            sys.stderr.write("An error occurred during the sequence tolerance execution. The chosen designed residues resulting in an empty resfile and so could not be used.")
            raise SequenceToleranceException          


class SequenceToleranceJobHK(RosettaClusterJob):

    suffix = "seqtolHK"
    
    # additional attributes
    residues      = {}   # contains the residues and their modes according to rosetta: { (chain, resID):["PIKAA","PHKL"] }
    backrub       = []   # residues to which backrub should be applied: [ (chain,resid), ... ]
    failed_runs   = []
    executable    = ''
    
    #todo: Remove after testing / add as test
    def __testinginit__(self, parameters, tempdir, targetroot):
        self.parameters = parameters
        self.debug = True
        self.tempdir = tempdir
        self.targetroot = targetroot
        self.workingdir = "/netapp/home/shaneoconner/temp/tmpnlKCQ0_seqtolHK/sequence_tolerance"
        self.targetdirectory = "/netapp/home/shaneoconner/results/tmpQHVAHJ_seqtolHK"
        taskdir = "/netapp/home/shaneoconner/temp/tmpnlKCQ0_seqtolHK/"
        self.jobID = self.parameters.get("ID") or 0
        self.filename_stdout = "stdout_%s_%d.txt" % (self.suffix, self.jobID)
        self.filename_stderr = "stderr_%s_%d.txt" % (self.suffix, self.jobID)
        self.seqtol_resfile = "seqtol.resfile"
        self._import_pdb(parameters["pdb_filename"], parameters["pdb_info"])
        self._prepare_backrub_resfile() # fills in self.backrub for resfile creation
        self._write_seqtol_resfile()
                               
        targetsubdirectory = "sequence_tolerance"
        stTask = SequenceToleranceHKClusterTask(taskdir, os.path.join(self.targetdirectory, targetsubdirectory), parameters, self.seqtol_resfile, name="Sequence tolerance step for sequence tolerance protocol")
        self.stTask = stTask
        stTask.outputstreams = [
            {"stdout" : "seqtol_1234.cmd.o6054336.1", "stderr" : "seqtol_1234.cmd.e6054336.1", "failed" : False},
            {"stdout" : "seqtol_1234.cmd.o6054336.2", "stderr" : "seqtol_1234.cmd.e6054336.2", "failed" : False}]
            
        
    def __init__(self, parameters, tempdir, targetroot):
        # The tempdir is the one on the submission host e.g. chef
        # targetdirectory is the one on your host e.g. your PC or the webserver
        # The taskdirs are subdirectories of the tempdir on the submission host and the working directories for the tasks
        # The targetdirectories of the tasks are subdirectories of the targetdirectory named like the taskdirs
        super(SequenceToleranceJobHK, self).__init__(parameters, tempdir, targetroot)
    
    def _initialize(self):
        self._status("Creating RosettaSeqTol object in %s." % self.targetdirectory)
        parameters = self.parameters
      
        # Create input files        
        self.minimization_resfile = "minimize.resfile" 
        self.backrub_resfile = "backrub.resfile"
        self.seqtol_resfile = "seqtol.resfile"
        
        self._import_pdb(parameters["pdb_filename"], parameters["pdb_info"])
        self._prepare_backrub_resfile() # fills in self.backrub for resfile creation
        self._write_resfile( "NATRO", {}, [], self.minimization_resfile)
        self._write_resfile( "NATAA", {}, self.backrub, self.backrub_resfile )
        self._write_seqtol_resfile()
           
        scheduler = TaskScheduler(self.workingdir, files = [parameters["pdb_filename"], self.minimization_resfile, self.backrub_resfile, self.seqtol_resfile])
        
        targetsubdirectory = "minimization"
        self._write_paths_file("%s/%s" % (self.workingdir, targetsubdirectory), 0)
        taskdir = self._make_taskdir(targetsubdirectory, [parameters["pdb_filename"], self.pathsfile, self.minimization_resfile])
        minTask = MinimizationSeqTolHKClusterTask(taskdir, os.path.join(self.targetdirectory, targetsubdirectory), parameters, self.minimization_resfile, name="Minimization step for sequence tolerance protocol")

        targetsubdirectory = "backrub"
        self._write_paths_file("%s/%s" % (self.workingdir, targetsubdirectory), 0)
        taskdir = self._make_taskdir(targetsubdirectory, [parameters["pdb_filename"], self.pathsfile, self.backrub_resfile])
        brTask = BackrubClusterTaskHK(taskdir, os.path.join(self.targetdirectory, targetsubdirectory), parameters, self.backrub_resfile, name="Backrub step for sequence tolerance protocol")
        brTask.addPrerequisite(minTask, [parameters["pdb_filename"]])
            
        targetsubdirectory = "sequence_tolerance"
        self._write_paths_file("%s/%s" % (self.workingdir, targetsubdirectory), 1)
        taskdir = self._make_taskdir(targetsubdirectory, [self.pathsfile, self.seqtol_resfile])
        stTask = SequenceToleranceHKClusterTask(taskdir, os.path.join(self.targetdirectory, targetsubdirectory), parameters, self.seqtol_resfile, name="Sequence tolerance step for sequence tolerance protocol")
        stTask.addPrerequisite(brTask, [getOutputFilenameHK(parameters["pdbRootname"], i + 1, "low") for i in range(parameters["nstruct"])])
        self.stTask = stTask
        
        scheduler.addInitialTasks(minTask)
        self.scheduler = scheduler
        
    def _analyze(self):
        """ this recreates Elisabeth's analysis scripts in /kortemmelab/shared/publication_data/ehumphris/Structure_2008/CODE/SCRIPTS """
        
        parameters = self.parameters
        partner0 = parameters['Partners'][0]
        partner1 = parameters['Partners'][1]
        designed = parameters['Designed']        
        designed[partner0] = designed.get(partner0) or [] # todo: Only needed for testing separately 
        designed[partner1] = designed.get(partner1) or [] 
        return True
        sys.exit(1)
        
        self._status("Checking output")
        successFSA = re.compile("DONE ::\s+\d+ starting structures built\s+\d+ \(nstruct\) times")
        streams = self.stTask.getOutputStreams()
        failed_runs = []
        list_outfiles = []
        for i in range(len(streams)):
            stdfile = streams[i]["stdout"]
            if stdfile:
                stdoutput = self._taskresultsdir_file_path("sequence_tolerance", stdfile)
                contents = readFile(stdoutput)
                success = successFSA.search(contents)
                if not success:
                    failed_runs.append(i)
                    self._status("%s failed" % stdoutput)
                else:
                    self._status("%s succeeded" % stdoutput)
                    list_outfiles.append(stdoutput)
            else:
                failed_runs.append(i)
        
        if failed_runs != []: # check if any failed
            s = ""
            for fn in failed_runs:
                s += "%s\n" % self.stTask.getExpectedOutputFileNames()[fn]
            print(s)
            writeFile(self._workingdir_file_path("failed_jobs.txt"), s)
            
        self._status("Analyzing results")
        handle_err = open( self._workingdir_file_path( 'error.log' ), 'a+' )
        # AMINO ACID FREQUENCIES
        self._status("\tAmino Acid frequencies")
        list_res = []
        for x in designed[partner0]:
            list_res.append(partner0 + str(x))
        for x in designed[partner1]:
            list_res.append(partner1 + str(x))
        
        # this does the same as get_data.pl
        for design_res in list_res:
            one_pos = []
            for filename in list_outfiles:
                handle = open(filename,'r')
                # print "grep:", 
                # print '^ %s' % self.map_chainres2seq[design_res], "result: "
                grep_result = rosettahelper.grep('^ %s' % self.map_chainres2seq[design_res], handle)
                # print 'list:',  grep_result
                # print 'string', grep_result[0]
                # print 'split:', grep_result[0].split()
                # print grep_result
                if grep_result != []:
                    one_pos.append( grep_result[0].split() )
                else:
                    handle_err.write('Single sequence tolerance prediction run failed: see %s for details\n' % filename)
                handle.close()
            
            # sort and transpose the data of one_pos table: invert_textfiles.pl
            # the values are in the following order:
            order = ['id','A','D','E','F','G','H','I','K','L','M','N','P','Q','R','S','T','V','W','Y']
            # they should be in this order:
            res_order = ['W','F','Y','M','L','I','V','A','G','S','T','R','K','H','N','Q','D','E','P']
            # transpose:
            dict_res2values = {}
            for res in order:
                i = order.index(res)
                values4oneres = []
                for line in one_pos:
                    values4oneres.append(line[i])
                dict_res2values[res] = values4oneres
            
            # sort and write the table to a file
            frequency_file = "freq_%s.txt" % design_res
            handle2 = open(self._workingdir_file_path(frequency_file), 'w')
            for res in res_order:
                for freq in dict_res2values[res]:
                    handle2.write('%s ' % freq)
                handle2.write('\n')
            handle2.write('\n')
            handle2.close()
        
        # run the R script for all positions and create the boxplots 
        parameter = "c("
        for design_res in list_res:
            parameter += "\'%s\'," % design_res
        parameter = parameter[:-1] + ")" # gets rid of the last ','
          
        return True
        sys.exit(1)
        #todo: Define server_root for this
        
        cmd = '''/bin/echo \"plot_specificity_list(%s)\" \\
                | /bin/cat %sdaemon/specificity_classic.R - > specificity.R ; \\
                /usr/bin/R CMD BATCH specificity.R''' % ( parameter, server_root )
        print cmd
        
        # todo: This is as much as I can test using chef
        self.execute_log(cmd)
        
        # CREATE SEQUENCE MOTIF    ## this all would be better off in the postprocessing of the onerun class
        print "\tCreate Sequence Motif\n\t+-- copy PDB files from cluster"
        # 1st, get the data
        sequences_list_total = []
        handle_list_files = open(self.workingdir_file_path('pdbs.out'),'r')
        list_files = [line.split('/')[-1].strip() for line in handle_list_files] # os.listdir(self.workingdir)
        list_files.sort()
        for filename in self.list_outfiles:
            si = int(filename.split('_')[1])
            sequences_list = []
            output_handle = open(filename,'r')
            # read only last generation "Generation 5"
            for line in output_handle:
                if line[0:13] == "Generation  5":
                    # sequences_list.append( line.split()[5] )
                    break                                    # and break
            # now the stuff we actually need to read in:
            for line in output_handle:
                if line[0:10] == "Generation":
                    # sequences_list.append( line.split()[5] )
                    pass
                elif len(line) > 1:                        # normal line is not empty and the sequence is at the beginning
                    data_line = line.split() # (sequence, fitness, interface score, complex score)
                    sequences_list.append( (data_line[0], data_line[2]) )
                else:
                    break # break for the first empty line. This means we're done.
            output_handle.close()
            # now sort after score:
            self._filter(sequences_list)
            # get all pdb files associated with this run:
            list_this_run = rosettahelper.grep('BR%slow_%04.i_[A-Z]*\.pdb' % (self.parameter['pdb_id'], si), list_files)
            #best_scoring_pdbs = []
            structure_counter = 0 # ok it seems that not all the sequences have a corresponding pdb file. Therefore we keep the first 10 we can find!
            for designed_sequence in sequences_list: # keep the 10 best scoring structures
                best_scoring_pdb = 'BR%slow_%04.i_%s.pdb' % (self.parameter['pdb_id'], si, designed_sequence[0])
                if best_scoring_pdb in list_this_run:  
                    self.exec_cmd("scp lauck@chef.compbio.ucsf.edu:~/job_%s/%s . " % (self.ID, best_scoring_pdb))
                    structure_counter += 1
                if structure_counter >= 10: break
        
            sequences_list_total.extend(sequences_list[0:10]) # add 10 best scoring to the total list
        # write the actual fasta file with the 10 best scoring sequences of each run
        fasta_file = "tolerance_sequences.fasta"
        handle_fasta = open(fasta_file,'w')
        i = 0
        for sequence in sequences_list_total:
            i += 1
            handle_fasta.write('>%s\n%s\n' % (i,sequence[0]))
        handle_fasta.close()
        
        # 3rd, create the motif
        count = 0
        if not os.path.exists( self.workingdir_file_path("tolerance_sequences.fasta") ) and count < 10 :
            time.sleep(1) # make sure the fasta file gets written
            count += 1
        # create weblogo from the created fasta file
        seqs = read_seq_data(open(self.workingdir_file_path("tolerance_sequences.fasta")))
        logo_data = LogoData.from_seqs(seqs)
        logo_data.alphabet = std_alphabets['protein'] # this seems to affect the coloring, but not the actual motif
        logo_options = LogoOptions()
        logo_options.title = "Sequence profile"
        logo_options.number_interval = 1
        logo_options.color_scheme = std_color_schemes["chemistry"]
        logo_options.annotate = [self.parameter['partner_1'] + str(resid) for resid in self.parameter['design_1']] + [self.parameter['partner_2'] + str(resid) for resid in self.parameter['design_2']] #res_nums this is for Gregs hacked version that I don't have
        logo_format = LogoFormat(logo_data, logo_options)
        png_print_formatter(logo_data, logo_format, open(self.workingdir_file_path( "tolerance_motif.png" ), 'w'))
        
        # clean up and remove backrub directory
        #shutil.rmtree( self.workingdir_file_path("backrub") )
        
        # end analysis
        handle_err.close()
        # stdout = open(self.workingdir_file_path( self.filename_stdout ),'r')
        # for x in stdout.readlines():
        #   print x,
        # stdout.close()
        # # self.copy_working_dir('')
        
        # rename a few files
        print "rename initial PDB files"
        self.exec_cmd('mv %s.pdb %s_minimized.pdb' % (self.parameter['pdb_id'],self.parameter['pdb_id']) )
        self.exec_cmd('mv %s_submission.pdb %s.pdb' % (self.parameter['pdb_id'],self.parameter['pdb_id']) )
        
    def _filter(self,list_seq):
        """this sorts sequences after fitness score"""
        decimal.getcontext().prec = 1
        list_seq.sort(lambda x,y: cmp(decimal.Decimal(x[1]), decimal.Decimal(y[1])), reverse=True)
        return list_seq
    
    def _import_pdb(self, filename, contents):
        """Import a pdb file from the database and write it to the temporary directory"""
              
        self.pdb = pdb.PDB(contents.split('\n'))
      
        # remove everything but the chosen chains or keep all chains if the list is empty
        # pdb_content is passed directly to backrub so remove the pruned chain lines before the backrub
        self.pdb.pruneChains(self.parameters['Partners'])
        self.pdb.remove_hetatm()  # rosetta doesn't like heteroatoms so let's remove them
        # This was removed by Shane: self.pdb.fix_chain_id()
        self.parameters['pdb_content'] = join(self.pdb.lines, '\n')                
        
        self.pdb.write(self._workingdir_file_path(filename))
        self.residue_ids = self.pdb.aa_resids()
                
        # get chains
        seqs = chainsequence.ChainSequences()
        # create dict with key = chain ID, value = list of residue IDs
        self.dict_chain2resnums = seqs.parse_atoms(self.pdb)
    
    def _prepare_backrub_resfile(self):
        self.pdb = pdb.PDB(self.parameters["pdb_info"].split('\n'))
        resid2type = self.pdb.aa_resid2type()
        residue_ids = self.pdb.aa_resids()
         
        # backrub is applied to all residues: append all residues to the backrub list
        backrub = []
        for res in residue_ids:
            x = [ res[0], res[1:].strip() ]
            if len(x) == 1:
                backrub.append( ( "_", int(x[0].lstrip())) )
            elif resid2type[res] != "C": # no backrub for cystein residues to avoid S=S breaking
                backrub.append( ( x[0], int(x[1].lstrip())) )
        self.backrub = backrub

    def _write_line(self, chain, sequential_residue_number, pdb_residue_number, mode ):
        return " %s %4.i %4.i %s\n" % (chain, sequential_residue_number, pdb_residue_number, mode)
       
    def _write_paths_file(self, workingdir, databaseindex = 0):
        self.pathsfile = "paths.txt"
        pathsdict = {
            "workingdir": workingdir,
            "databasepath": getClusterDatabasePath(self.parameters["binary"], databaseindex)
            }
        writeFile(self._workingdir_file_path(self.pathsfile), pathfilecontents % pathsdict)
            
    def _write_resfile( self, default_mode, mutations, backbone, filename ):
        """create resfile from list of mutations and backbone"""
        
        output_handle = open(self.workingdir + "/%s" % filename,'w')        
        output_handle.write(resfileheader)
        
        # get chains
        seqs = chainsequence.ChainSequences()
        # create dict with key = chain ID, value = list of residue IDs
        chain_resnums = seqs.parse_atoms(self.pdb)
        
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
        
    
    def _write_seqtol_resfile( self ):
        """Create a resfile for the two chains.
            residues in interface: NATAA (conformation can be changed)
            residues mutation: PIKAA ADEFGHIKLMNPQRSTVWY (design sequence)"""
        
        # turn list of ints in chainid, resid strings
        partner0 = self.parameters['Partners'][0]
        partner1 = self.parameters['Partners'][1]
        designed = self.parameters['Designed']        
        designed[partner0] = designed.get(partner0) or [] 
        designed[partner1] = designed.get(partner1) or [] 
                                        
        self.design =  [ '%s%s' % (partner0, str(residue).rjust(4)) for residue in designed[partner0] ]
        self.design += [ '%s%s' % (partner1, str(residue).rjust(4)) for residue in designed[partner1] ]
        
        output_handle = open( self._workingdir_file_path(self.seqtol_resfile), 'w')
        output_handle.write(resfileheader)
    
        # get neighbors of all designed residues
        neighbor_list = []
        for residue in self.design:
            neighbor_list.extend( self.pdb.neighbors3(self.parameters['radius'], residue) )
        
        uniquelist = {}
        for n in neighbor_list:
            uniquelist[n] = True
        neighbor_list = uniquelist.keys() #(neighbor_list)
        neighbor_list.sort()
    
        self.map_chainres2seq = {}
        
        # get list of chain IDs
        chains = self.dict_chain2resnums.keys()
        chains.sort()
        seq_resnum = 0
        for chain in chains:
            for resnum in self.dict_chain2resnums[chain]:
                seq_resnum += 1 # important
                resnum = int(resnum)
                residue = "%s%4.i" % (chain, resnum)
                if residue in self.design:
                    output_handle.write( self._write_line(chain, seq_resnum, resnum, "ALLAA") )
                elif residue in neighbor_list:
                    output_handle.write( self._write_line(chain, seq_resnum, resnum, "NATAA") )
                else:
                    output_handle.write( self._write_line(chain, seq_resnum, resnum, "NATRO") )
                self.map_chainres2seq[chain+str(resnum)] = str(seq_resnum) # save this for later
                
        output_handle.write( "\n" )
        output_handle.close()
        return
