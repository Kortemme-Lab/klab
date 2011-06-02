#!/usr/bin/python2.4
# encoding: utf-8
"""
RosettaTasks.py

Created by Shane O'Connor 2011.
Copyright (c) 2011 __UCSF__. All rights reserved.
"""


import sys
import os
import time
import shutil
import glob
import re
from string import join
import decimal
import traceback
import rosettahelper
import itertools
import subprocess
import math
from weblogolib import *

from conf_daemon import *
import chainsequence       
import pdb
from analyze_mini import AnalyzeMini
from ClusterTask import ClusterTask, ClusterScript, getClusterDatabasePath, FAILED_TASK
from ClusterScheduler import TaskScheduler, RosettaClusterJob

server_root = rosettahelper.server_root
specificityRScript = os.path.join(server_root, "daemon", "specificity.R")
specificity_classicRScript = os.path.join(server_root, "daemon", "specificity_classic.R")

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

# todo: Move into common file
class SequenceToleranceException(Exception): pass
class PostProcessingException(Exception): pass

#todo: Does the backrub ever use the pdb file? 

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



class BackrubSequenceToleranceSK(ClusterTask):

    # additional attributes
    prefix = "Seq.Tolerance"
         
    def __init__(self, workingdir, targetdirectory, parameters, backrub_resfile, seqtol_resfile, movemap=None, name=""):
        self.backrub_resfile    = backrub_resfile
        self.seqtol_resfile     = seqtol_resfile
        self.movemap            = movemap
        self.residues           = {}   # contains the residues and their modes according to rosetta: { (chain, resID):["PIKAA","PHKL"] }
        self.pivot_res          = []   # list of pivot residues, consecutively numbered from 1 [1,...]
        self.map_res_id         = {}   # contains the mapping from (chain,resid) to pivot_res
        
        if not parameters.get("binary") or not(parameters["binary"] == "seqtolJMB" or parameters["binary"] == "seqtolP1"):
            raise
                        
        super(BackrubSequenceToleranceSK, self).__init__(workingdir, targetdirectory, '%s_%d.cmd' % (self.prefix, parameters["ID"]), parameters, name, parameters["nstruct"])          
    
    def _initialize(self):
        self._prepare_backrub()
        parameters = self.parameters
                
        self.br_output_prefixes = ["%04i_" % (i + 1) for i in range(parameters["nstruct"])]
        self.low_files = [getOutputFilenameSK(parameters["pdbRootname"], i + 1, "low") for i in range(parameters["nstruct"])]
        self.prefixes = [lfilename[:-4] for lfilename in self.low_files]
        self.low_files = [self._workingdir_file_path(lfilename) for lfilename in self.low_files]
        
        self.parameters["ntrials"] = 10000 # This should be 10000 on the live webserver
        self.parameters["pop_size"] = 2000 # This should be 2000 on the live webserver
        if CLUSTER_debugmode:
            self.parameters["ntrials"] = 10   
            self.parameters["pop_size"] = 20
        
        # Create script
        
        taskarrays = {
            "broutprefixes" : self.br_output_prefixes, 
            "lowfiles" : self.low_files, 
            "prefixes" : self.prefixes}
        ct = ClusterScript(self.workingdir, parameters["binary"], numtasks = self.numtasks, dataarrays = taskarrays)
        

        # See the backrub_seqtol.py file in the RosettaCon repository: RosettaCon2010/protocol_capture/protocol_capture/backrub_seqtol/scripts/backrub_seqtol.py        
        if parameters["binary"] == "seqtolJMB":
            no_hb_env_dep_weights_file = os.path.join(ct.getBinaryDir(), "standard_NO_HB_ENV_DEP.wts")
            score_weights = no_hb_env_dep_weights_file
            score_patch = ""
            ref_offsets = "HIS 1.2"
        elif parameters["binary"] == "seqtolP1":
            score_weights = "standard"
            score_patch = "score12"
            ref_offsets = "HIS 1.2"
            
        # Setup backrub
        backrubCommand = [
            ct.getBinary("backrub"),  
            "-database %s" % ct.getDatabaseDir(), 
            "-s %s/%s" % (ct.getWorkingDir(), parameters["pdb_filename"]),
            "-ignore_unrecognized_res", 
            "-ex1 -ex2",  
            "-extrachi_cutoff 0", 
             "-backrub:ntrials %d" % parameters["ntrials"], 
            "-resfile %s" % os.path.join(ct.getWorkingDir(), self.backrub_resfile),
            "-out:prefix $broutprefixesvar",
            "-score:weights", score_weights,
            "-score:patch", score_patch
            ]
        if self.movemap:
            backrubCommand.append("-backrub:minimize_movemap %s/%s" % (ct.getWorkingDir(), self.movemap))

        backrubCommand = [
            '# Run backrub', '', 
            join(backrubCommand, " "), '', 
            'mv ${SGE_TASK_ID4}_%s_0001_low.pdb %s_${SGE_TASK_ID4}_low.pdb' % (parameters["pdbRootname"], parameters["pdbRootname"]),
            'rm ${SGE_TASK_ID4}_%s_0001_last.pdb' % parameters["pdbRootname"], ''] 
        
        # Setup sequence tolerance
        seqtolCommand = [
            ct.getBinary("sequence_tolerance"),   
            "-database %s" % ct.getDatabaseDir(), 
            "-s $lowfilesvar",
            "-ex1 -ex2 -extrachi_cutoff 0",
            "-seq_tol:fitness_master_weights %s" % join(map(str,parameters["Weights"]), " "),
            "-ms:generations 5",
            "-ms:pop_size %d" % parameters["pop_size"],
            "-ms:pop_from_ss 1",
            "-ms:checkpoint:prefix $prefixesvar",
            "-ms:checkpoint:interval 200",
            "-ms:checkpoint:gz",
            "-ms:numresults", "0",
            "-out:prefix $prefixesvar", 
            "-packing:resfile %s/%s" % (self.workingdir, self.seqtol_resfile),
            "-score:ref_offsets HIS 1.2",
            "-score:weights", score_weights,
            "-score:patch", score_patch]

        if ref_offsets:
            seqtolCommand.append("-score:ref_offsets %s" % ref_offsets)
        
        
        seqtolCommand = [
            '# Run sequence tolerance', '', 
            join(seqtolCommand, " ")]        
        
        self.script = ct.createScript(backrubCommand + seqtolCommand, type="SequenceTolerance")
        
    def _prepare_backrub( self ):
        """prepare data for a full backbone backrub run"""
        self.pdb = pdb.PDB(self.parameters["pdb_info"].split('\n'))
        self.map_res_id = self.parameters["map_res_id"] 
        self.residue_ids = self.pdb.aa_resids()

        # backrub is applied to all residues: append all residues to the backrub list
        backrub = []   # residues to which backrub should be applied: [ (chain,resid), ... ]
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
        passed = super(BackrubSequenceToleranceSK, self).retire()
                               
        try:
            # Run the analysis on the originating host
            errors = []
            # check whether files were created (and write the total scores to a file)
            for x in range(1, self.parameters['nstruct']+1):
                low_file   = self._workingdir_file_path(getOutputFilenameSK(self.parameters["pdbRootname"], x, "low"))          
                if not os.path.exists( low_file ): 
                    errors.append('%s missing' % low_file)
                            
            # Copy the files from the cluster submission host back to the originating host
            self._status('Copying pdb, gz, and resfiles back')
            self._copyFilesBackToHost(["*.pdb", "*.gz", "*.resfile"])
        except Exception, e:
            errors.append(str(e))
            errors.append(traceback.format_exc())
            
        # At this stage we are actually done but do not mark ourselves as completed otherwise the scheduler will get confused
        if errors:
            errs = join(errors,"</error>\n\t<error>")
            print("<errors>\n\t<error>%s</error>\n</errors>" % errs)
            self.state = FAILED_TASK
            return False
          
        return passed
    
    
#@finalupgradetodo Remove this class
class BackrubClusterSKTask(ClusterTask):

    # additional attributes
    prefix = "backrub"
    
    def __init__(self, workingdir, targetdirectory, parameters, resfile, movemap=None, name=""):
        self.resfile       = resfile
        self.movemap       = movemap
        self.residues      = {}   # contains the residues and their modes according to rosetta: { (chain, resID):["PIKAA","PHKL"] }
        self.pivot_res     = []   # list of pivot residues, consecutively numbered from 1 [1,...]
        self.map_res_id    = {}   # contains the mapping from (chain,resid) to pivot_res
        super(BackrubClusterSKTask, self).__init__(workingdir, targetdirectory, '%s_%d.cmd' % (self.prefix, parameters["ID"]), parameters, name)          
    
    def _initialize(self):
        self._prepare_backrub()
        parameters = self.parameters
        
        self.parameters["ntrials"] = 10000 # This should be 10000 on the live webserver
        if CLUSTER_debugmode:
            self.parameters["ntrials"] = 10   
    
        # Setup backrub
        ct = ClusterScript(self.workingdir, parameters["binary"])
        args = [ct.getBinary("backrub"),  
                "-database %s" % ct.getDatabaseDir(), 
                "-s %s/%s" % (ct.getWorkingDir(), parameters["pdb_filename"]),
                "-ignore_unrecognized_res", 
                "-ex1 -ex2", 
                "-nstruct %d" % parameters["nstruct"],
                "-backrub:ntrials %d" % parameters["ntrials"], 
                "-pivot_atoms CA"] 
        if self.movemap:
            args.append("-backrub:minimize_movemap %s/%s" % (ct.getWorkingDir(), self.movemap))
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
        backrub = []   # residues to which backrub should be applied: [ (chain,resid), ... ]
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
        passed = super(BackrubClusterSKTask, self).retire()
        
        self._status('Copying files from %s to %s' % (self.workingdir, self.targetdirectory))
                   
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
            return False
          
        return passed
        
            
#@finalupgradetodo Remove this class
class SequenceToleranceClusterTask(ClusterTask):
           
    prefix = "seqtol"
       
    def __init__(self, workingdir, targetdirectory, parameters, resfile, name=""):
        self.resfile = resfile
        super(SequenceToleranceClusterTask, self).__init__(workingdir, targetdirectory, '%s_%d.cmd' % (self.prefix, parameters["ID"]), parameters, name, parameters["nstruct"])          

    def _initialize(self):
        parameters = self.parameters
        
        self.low_files = [getOutputFilenameSK(parameters["pdbRootname"], i + 1, "low") for i in range(parameters["nstruct"])]
        self.prefixes = [lfilename[:-4] for lfilename in self.low_files]
        self.low_files = [self._workingdir_file_path(lfilename) for lfilename in self.low_files]
        
        parameters["pop_size"] = 2000 # This should be 2000 on the live webserver
        if CLUSTER_debugmode:
            self.parameters["pop_size"] = 200
        
        # Setup backrub
        ct = ClusterScript(self.workingdir, parameters["binary"], numtasks = self.numtasks, dataarrays = {"lowfiles" : self.low_files, "prefixes" : self.prefixes})
        commandlines = ['# Run sequence tolerance', '',
            join(
                [ct.getBinary("sequence_tolerance"),  
                "-database %s" % ct.getDatabaseDir(), 
                "-s $lowfilesvar",
                "-ex1 -ex2 -extrachi_cutoff 0",
                "-seq_tol:fitness_master_weights %s" % join(map(str,parameters["Weights"]), " "),
                "-ms:generations 5",
                "-ms:pop_size %d" % parameters["pop_size"],
                "-ms:pop_from_ss 1",
                "-ms:checkpoint:prefix $prefixesvar",
                "-ms:checkpoint:interval 200",
                "-ms:checkpoint:gz",
                "-ms:numresults", "0",
                "-out:prefix $prefixesvar", 
                "-packing:resfile %s/%s" % (self.workingdir, self.resfile),
                "-score:ref_offsets TRP 0.9" 
                 ])]
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
                
        self.parameters["ntrials"] = 10000 # This should be 10000 on the live webserver
        if CLUSTER_debugmode:
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
        
        wdpath = self._workingdir_file_path
        self._status('Copying files from %s to %s' % (self.workingdir, self.targetdirectory))
        try:
            shutil.copy(wdpath("backrub.resfile"), self.targetdirectory)

            #for file in glob.glob(self._workingdir_file_path("*low*.pdb")):
            #    self._status('copying %s' % file)
            #    shutil.copy(file, self.targetdirectory)
            #for file in glob.glob(self._workingdir_file_path("*last*.pdb")):
            #    self._status('copying %s' % file)
            #    shutil.copy(file, self.targetdirectory)
                
            # Run the analysis on the originating host
            errors = []
            # check whether files were created
            for x in range(1, int(self.parameters['nstruct'])+1):
                #low_file  = self._targetdir_file_path(getOutputFilenameHK(self.parameters['pdbRootname'], x, "low"))
                #last_file = self._targetdir_file_path(getOutputFilenameHK(self.parameters['pdbRootname'], x, "last"))
                
                low_file  = self._workingdir_file_path(getOutputFilenameHK(self.parameters['pdbRootname'], x, "low"))
                last_file = self._workingdir_file_path(getOutputFilenameHK(self.parameters['pdbRootname'], x, "last"))
                
                if not os.path.exists( low_file ): 
                    errors.append('%s missing' % low_file)
                if not os.path.exists( last_file ):
                    errors.append('%s missing' % ( last_file ))
                
                #shutil.copy( low_file, self.workingdir + '/' + low_file.split('/')[-1] )

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
        super(SequenceToleranceHKClusterTask, self).__init__(workingdir, targetdirectory, '%s_%d.cmd' % (self.prefix, parameters["ID"]), parameters, name, parameters["nstruct"])          
    
    def _initialize(self):
        parameters = self.parameters
        
        self.low_files = [getOutputFilenameHK(parameters["pdbRootname"], i + 1, "low") for i in range(parameters["nstruct"])]
        self.prefixes = [lfilename[:-4] for lfilename in self.low_files]
        
        parameters["pop_size"] = 2000 # This should be 2000 on the live webserver        
        if CLUSTER_debugmode:
            self.parameters["pop_size"] = 60
        
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
        # PDB files etc. are copied by the Job.
        sr = super(SequenceToleranceHKClusterTask, self).retire()
        shutil.copy(self._workingdir_file_path("seqtol.resfile"), self.targetdirectory)            
        return sr and True
              
    
# Cluster jobs

class SequenceToleranceJobSK(RosettaClusterJob):

    suffix = "seqtolSK"
    flatOutputDirectory = True
    name = "Sequence Tolerance (SK, JMB)"
    
    def _defineOutputFiles(self):
        self.resultFilemasks.append((".", "*.pdb"))
        self.resultFilemasks.append((".", "stderr*"))
        self.resultFilemasks.append((".", "stdout*"))
        self.resultFilemasks.append((".", "timing_profile.txt"))
        self.resultFilemasks.append((".", "tolerance_*"))
        self.resultFilemasks.append((".", "*.ga.entities.gz"))
        self.resultFilemasks.append(("backrub", "*.cmd*"))
        self.resultFilemasks.append(("backrub", "*.resfile"))
        self.resultFilemasks.append(("backrub", "*.movemap"))
        self.resultFilemasks.append(("backrub", "backrub_scores.dat"))
        self.resultFilemasks.append(("sequence_tolerance", "*.resfile"))
        self.resultFilemasks.append(("sequence_tolerance", "*.cmd*"))
        self.resultFilemasks.append(("sequence_tolerance", "*low*.pdb"))
            
    def __init__(self, sgec, parameters, tempdir, targetroot, dldir, testonly = False):
        # The tempdir is the one on the submission host e.g. chef
        # targetdirectory is the one on your host e.g. your PC or the webserver
        # The taskdirs are subdirectories of the tempdir on the submission host and the working directories for the tasks
        # The targetdirectories of the tasks are subdirectories of the targetdirectory named like the taskdirs
        self.map_res_id = {}
        super(SequenceToleranceJobSK, self).__init__(sgec, parameters, tempdir, targetroot, dldir, testonly)
    
    def _initialize(self):
        self.describe()
        
        # Create input files        
        if not testonly:
            self._import_pdb(self.parameters["pdb_filename"], self.parameters["pdb_info"])
            self._write_backrub_resfile()
            self._write_seqtol_resfile()
            self._write_backrub_movemap()
        
        scheduler = TaskScheduler(self.workingdir, files = [self.parameters["pdb_filename"], self.seqtol_resfile, self.backrub_resfile, self.backrub_movemap])
        
        targetsubdirectory = "backrub"
        taskdir = self._make_taskdir(targetsubdirectory, [self.parameters["pdb_filename"], self.backrub_resfile, self.backrub_movemap])
        brTask = BackrubClusterSKTask(taskdir, os.path.join(self.targetdirectory, targetsubdirectory), self.parameters, self.backrub_resfile, movemap = self.backrub_movemap, name = "Backrub step for sequence tolerance protocol")
        
        targetsubdirectory = "sequence_tolerance"
        taskdir = self._make_taskdir(targetsubdirectory, [self.seqtol_resfile])
        stTask = SequenceToleranceClusterTask(taskdir, os.path.join(self.targetdirectory,targetsubdirectory), self.parameters, self.seqtol_resfile, name="Sequence tolerance step for sequence tolerance protocol")
        stTask.addPrerequisite(brTask, [getOutputFilenameSK(self.parameters["pdbRootname"], i + 1, "low") for i in range(self.parameters["nstruct"])])
         
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
        
        cmd = '''/bin/echo "process_seqtol(\'%s\', %s, %s, %s, %s, %s);\" \\
                  | /bin/cat %s - \\
                  | /usr/bin/R --vanilla''' % ( self.targetdirectory, fitness_coef, thresh_or_temp, type_st, percentile, prefix, specificityRScript)
                         
        self._status(cmd)
        
        #targetTaskDir =  os.path.join(self.targetdirectory, "sequence_tolerance")
        # Move any output files to the root so all R output gets located there
        for file in glob.glob(self._taskresultsdir_file_path("sequence_tolerance", "*ga.entities*")):
            self._status('copying %s' % file)
            shutil.move(file, self.targetdirectory)
        
        # Create the standard output file where the R script expects it
        firststdout = None
        firstlowfile = None
        for file in glob.glob(self._taskresultsdir_file_path("sequence_tolerance", "*.cmd.o*.1")):
            firststdout = file
            break
        for file in glob.glob(self._taskresultsdir_file_path("sequence_tolerance", "*0001_low.pdb")):
            firstlowfile = file
            break
        if firststdout and firstlowfile:
            self._status("Copying stdout and lowfile for R script boxplot names: (%s, %s)" % (firststdout, firstlowfile))
            shutil.copy(firststdout, self._targetdir_file_path("seqtol_1_stdout.txt"))
            shutil.copy(firstlowfile, self.targetdirectory)
        else:
            self._status("Could not find stdout or lowfile for R script boxplot names: (%s, %s)" % (firststdout, firstlowfile))
                            
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
        
        # create weblogo from the created fasta file
        success = True
        try:
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
        except Exception, e:
            self._appendError("An error occurred creating the motifs.\n%s\n%s" % (str(e), traceback.format_exc()))
            success = False
        
        # Delete the *last.pdb and generation files:
        try:
            for file in glob.glob(self._taskresultsdir_file_path("sequence_tolerance", "*_last.pdb")):
                self._status('deleting %s' % file)
                os.remove(file)
            for file in glob.glob(self._taskresultsdir_file_path("sequence_tolerance", "*_low.ga.generations.gz")):
                self._status('deleting %s' % file)
                os.remove(file)
        except Exception, e:
            self._appendError("An error occurred deleting files.\n%s\n%s" % (str(e), traceback.format_exc()))
            success = False

        return success
    
    def _import_pdb(self, filename, contents):
        """Import a pdb file from the database and write it to the temporary directory"""
        self.pdb = pdb.PDB(contents.split('\n'))
      
        # remove everything but the chosen chains or keep all chains if the list is empty
        # pdb_content is passed directly to backrub so remove the pruned chain lines before the backrub
        self.pdb.pruneChains(self.parameters['Partners'])
        self.pdb.remove_hetatm()  # rosetta doesn't like heteroatoms so let's remove them
        self.parameters['pdb_info'] = join(self.pdb.lines, '\n')        
        # internal mini resids don't correspond to the pdb file resids
        # the pivot residues need to be numbered consecutively from 1 up
        self.map_res_id = self.pdb.get_residue_mapping()
        self.parameters["map_res_id"] = self.map_res_id 
        
        self.pdb.write(self._workingdir_file_path(filename))
    
    def _write_backrub_movemap( self ):
        """create a movemap minimizing all chi angles"""
        self.backrub_movemap = "allchi_%s.movemap" % self.parameters["ID"]
        rosettahelper.writeFile(self._workingdir_file_path(self.backrub_movemap), 'RESIDUE * CHI\n')
    
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
        rosettahelper.writeFile(self._workingdir_file_path(self.backrub_resfile), 'NATAA\nstart\n%s\n' % s)
        
        
    def _write_seqtol_resfile( self ):
        """create a resfile for the chains
            residues in interface: NATAA (conformation can be changed)
            residues mutation: PIKAA ADEFGHIKLMNPQRSTVWY (design sequence)"""
        
        resfileHasContents, contents = make_seqtol_resfile( self.pdb, self.parameters, self.parameters['radius'], self.pdb.aa_resids())
                
        if resfileHasContents:
            self.seqtol_resfile = "seqtol_%s.resfile" % self.parameters["ID"]
            rosettahelper.writeFile(self._workingdir_file_path(self.seqtol_resfile), "%s\n" % contents)
        else:
            sys.stderr.write("An error occurred during the sequence tolerance execution. The chosen designed residues resulting in an empty resfile and so could not be used.")
            raise SequenceToleranceException          

import pprint
class SequenceToleranceMultiJobSK(SequenceToleranceJobSK):

    suffix = "seqtolMultiSK"
    horizontaltiles = 4
    name = "Multiple Sequence Tolerance (SK, JMB)"
    
    def _renamedefineOutputFiles(self):
        self.resultFilemasks.append((".", "stderr*"))
        self.resultFilemasks.append((".", "stdout*"))
        self.resultFilemasks.append((".", "timing_profile.txt"))
        self.resultFilemasks.append((".", "tolerance_*"))
        self.resultFilemasks.append((".", "*.ga.entities.gz"))
        self.resultFilemasks.append((".", "*.pdb"))
        for i in range(self.numberOfRuns):
            backrubSubdirectory = "backrub%d" % i
            seqtolSubdirectory = "sequence_tolerance%d" % i
            self.resultFilemasks.append((backrubSubdirectory, "*.cmd*"))
            self.resultFilemasks.append((backrubSubdirectory, "backrub_scores.dat"))
            self.resultFilemasks.append((backrubSubdirectory, "*.resfile"))
            self.resultFilemasks.append((backrubSubdirectory, "*.movemap"))        
            self.resultFilemasks.append((seqtolSubdirectory, "*.resfile"))
            self.resultFilemasks.append((seqtolSubdirectory, "*.cmd*"))
            self.resultFilemasks.append((seqtolSubdirectory, "*low*.pdb"))
            
    def __init__(self, sgec, parameters, tempdir, targetroot, dldir, testonly = False):
        # The tempdir is the one on the submission host e.g. chef
        # targetdirectory is the one on your host e.g. your PC or the webserver
        # The taskdirs are subdirectories of the tempdir on the submission host and the working directories for the tasks
        # The targetdirectories of the tasks are subdirectories of the targetdirectory named like the taskdirs
        self.map_res_id = {}
        super(SequenceToleranceMultiJobSK, self).__init__(sgec, parameters, tempdir, targetroot, dldir, testonly)
    
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

    def _expandParameters(self):
        # Expand out the premutations
        premut = []
        for chain, reslist in self.parameters["Premutated"].iteritems():
            for resid, premutations in reslist.iteritems():
                premut.append((chain, resid, premutations))
        choices = []
        for i in range(len(premut)):
            choices = SequenceToleranceMultiJobSK._tmultiply(choices, premut[i])
        
        # Create an array of parameters
        multiparameters = []
        numberOfRuns = len(choices)
        self.numberOfRuns = numberOfRuns
        for i in range(numberOfRuns):
            premutated = {}
            for premutation in choices[i]:
                if not premutated.get(premutation[0]):
                    premutated[premutation[0]] = {}
                premutated[premutation[0]][premutation[1]] = premutation[2]
                
            multiparameters.append({
                "binary"            : self.parameters["binary"],
                "ID"                : self.parameters["ID"],
                "pdb_filename"      : self.parameters["pdb_filename"],
                #"pdb_info"          : self.parameters["pdb_info"],
                "nstruct"           : self.parameters["nstruct"],
                "radius"            : self.parameters["radius"],
                "kT"                : self.parameters["kT"],
                "Partners"          : self.parameters["Partners"],
                "Weights"           : self.parameters["Weights"],
                "Premutated"        : premutated,
                "Designed"          : self.parameters["Designed"],
                })
        self.multiparameters = multiparameters
        
    def _initialize(self):
        self.describe()
        
        parameters = self.parameters
        
        # Create input files
        self._expandParameters()
        
        self._import_pdb(parameters["pdb_filename"], parameters["pdb_info"])
        self._write_backrub_resfiles()
        self._write_seqtol_resfile()
        self._write_backrub_movemap()
        
        scheduler = TaskScheduler(self.workingdir, files = [parameters["pdb_filename"], self.seqtol_resfile, self.backrub_movemap] + self.backrub_resfiles)
        
        for i in range(self.numberOfRuns):
            targetsubdirectory = "backrub%d" % i
            taskdir = self._make_taskdir(targetsubdirectory, [parameters["pdb_filename"], self.backrub_resfiles[i], self.backrub_movemap])
            brTask = BackrubClusterSKTask(taskdir, os.path.join(self.targetdirectory, targetsubdirectory), parameters, self.backrub_resfiles[i], movemap = self.backrub_movemap, name="Backrub step for run %d of the sequence tolerance protocol" % i)
                
            targetsubdirectory = "sequence_tolerance%d" % i
            taskdir = self._make_taskdir(targetsubdirectory, [self.seqtol_resfile])
            stTask = SequenceToleranceClusterTask(taskdir, os.path.join(self.targetdirectory,targetsubdirectory), parameters, self.seqtol_resfile, name="Sequence tolerance step for run %d of the sequence tolerance protocol" % i)
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
        
        success = True
        for i in range(self.numberOfRuns):
            
            targettaskdir = os.path.join(self.targetdirectory, "sequence_tolerance%d" % i)

            cmd = '''/bin/echo "process_seqtol(\'%s\', %s, %s, %s, %s, %s);\" \\
                      | /bin/cat %s - \\
                      | /usr/bin/R --vanilla''' % ( targettaskdir, fitness_coef, thresh_or_temp, type_st, percentile, prefix, specificityRScript)
                             
            self._status(cmd)
            
            # open files for stderr and stdout 
            self.file_stdout = open(self._targetdir_file_path( self.filename_stdout ), 'a+')
            self.file_stderr = open(self._targetdir_file_path( self.filename_stderr ), 'a+')
            self.file_stdout.write("*********************** R output ***********************\n")
            subp = subprocess.Popen(cmd, stdout=self.file_stdout, stderr=self.file_stderr, cwd=targettaskdir, shell=True, executable='/bin/bash')
                    
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
            if not os.path.exists(os.path.join(targettaskdir, "tolerance_sequences.fasta") ) and count < 10 :
                time.sleep(1) # make sure the fasta file gets written
                count += 1
              
            try:
                # create weblogo from the created fasta file
                shutil.move(os.path.join(targettaskdir, "tolerance_sequences.fasta"), self._targetdir_file_path("tolerance_sequences%d.fasta" % i))
                seqs = read_seq_data(open(self._targetdir_file_path("tolerance_sequences%d.fasta" % i)))
                logo_data = LogoData.from_seqs(seqs)
                logo_data.alphabet = std_alphabets['protein'] # this seems to affect the coloring, but not the actual motif
                logo_options = LogoOptions()
                logo_options.title = "Sequence profile"
                logo_options.number_interval = 1
                logo_options.color_scheme = std_color_schemes["chemistry"]
                ann = getResIDs(self.parameters)
                logo_options.annotate = ann    
                logo_format = LogoFormat(logo_data, logo_options)
                png_print_formatter(logo_data, logo_format, open(self._targetdir_file_path( "tolerance_motif%d.png" % i), 'w'))
            except Exception, e:
                self._appendError("An error occurred creating the motifs.\n%s\n%s" % (str(e), traceback.format_exc()))
                success = False
            
            # Delete the *last.pdb and generation files:
            try:
                for file in glob.glob(self._taskresultsdir_file_path("sequence_tolerance%d" % i, "*_last.pdb")):
                    self._status('deleting %s' % file)
                    os.remove(file)
                for file in glob.glob(self._taskresultsdir_file_path("sequence_tolerance%d" % i, "*_low.ga.generations.gz")):
                    self._status('deleting %s' % file)
                    os.remove(file)
            except Exception, e:
                self._appendError("An error occurred deleting files.\n%s\n%s" % (str(e), traceback.format_exc()))
                success = False
        
        try:
            # Generate tolerance motif montage
            self.verticaltiles = int(math.ceil(float(self.numberOfRuns) / float(self.horizontaltiles)))
            montagecmd = "montage -geometry +2+2 -tile %dx%d -pointsize 80 -font Times-Roman "% (self.horizontaltiles, self.verticaltiles)
            # todo: This is error-prone if we change the logic in _write_backrub_resfiles. Separate this iteration into a separate function and use for both
            for i in range(self.numberOfRuns):
                params = self.multiparameters[i]
                lbl = []
                for partner in params['Partners']:
                    if params['Premutated'].get(partner):
                        pm = params['Premutated'][partner]
                        for residue in pm:
                            lbl.append("%s%d:%s" % (partner, residue, pm[residue]))
                montagecmd += "\( tolerance_motif%d.png -set label '%s' \) " % (i, join(lbl,"\\n"))             
            montagecmd += "multi_tolerance_motif.png"
            self._status(montagecmd)
            
            self.file_stdout = open(self._targetdir_file_path( self.filename_stdout ), 'a+')
            self.file_stderr = open(self._targetdir_file_path( self.filename_stderr ), 'a+')
            self.file_stdout.write("*********************** montage output ***********************\n")
            subp = subprocess.Popen(montagecmd, stdout=self.file_stdout, stderr=self.file_stderr, cwd=self.targetdirectory, shell=True, executable='/bin/bash')
        except Exception, e:
            self._appendError("An error occurred creating the motif montage.\n%s\n%s" % (str(e), traceback.format_exc()))
            success = False
                
        return success
            
    def _write_backrub_resfiles( self ):
        """create a resfile of premutations for the backrub"""
        
        # Write out the premutated residues
        self.backrub_resfiles = []
        for i in range(self.numberOfRuns):
            s = ""
            params = self.multiparameters[i]
            for partner in params['Partners']:
                if params['Premutated'].get(partner):
                    pm = params['Premutated'][partner]
                    for residue in pm:
                        #todo: check that residue exists -  # get all residues:  residue_ids     = self.pdb.aa_resids()
                        s += ("%d %s PIKAA %s\n" % (residue, partner, pm[residue]))
            
            # Only create a file if there are any premutations
            backrub_resfile = ("backrub_%s_%d.resfile" % (self.parameters["ID"], i))
            rosettahelper.writeFile(self._workingdir_file_path(backrub_resfile), 'NATAA\nstart\n%s\n' % s)
            self.backrub_resfiles.append(backrub_resfile)
               

class SequenceToleranceJobSKAnalyzer(SequenceToleranceJobSK):

    suffix = "seqtolSK"
    flatOutputDirectory = True
    name = "Sequence Tolerance Analyzer (SK, JMB)"
               
    def __init__(self, sgec, parameters, tempdir, targetroot, dldir):
        # The tempdir is the one on the submission host e.g. chef
        # targetdirectory is the one on your host e.g. your PC or the webserver
        # The taskdirs are subdirectories of the tempdir on the submission host and the working directories for the tasks
        # The targetdirectories of the tasks are subdirectories of the targetdirectory named like the taskdirs
        self.map_res_id = {}
        super(SequenceToleranceJobSKAnalyzer, self).__init__(sgec, parameters, tempdir, targetroot, dldir)
    
    def _initialize(self):
        self.describe()
        
        parameters = self.parameters
        
        # Create input files
        self._import_pdb(parameters["pdb_filename"], parameters["pdb_info"])
        self._write_backrub_resfiles()
        self._write_seqtol_resfile()
        self._write_backrub_movemap()
        
        self.targetdirectory = "/home/oconchus/1KI1test"
        
        scheduler = TaskScheduler(self.workingdir, files = [parameters["pdb_filename"], self.seqtol_resfile, self.backrub_movemap] + self.backrub_resfiles)
        
        self.scheduler = scheduler


class SequenceToleranceMultiJobSKAnalyzer(SequenceToleranceJobSK):

    suffix = "seqtolMultiSK"
    horizontaltiles = 4
    name = "Multiple Sequence Tolerance Analyzer (SK, JMB)"
    
    def __init__(self, sgec, parameters, tempdir, targetroot, dldir):
        # The tempdir is the one on the submission host e.g. chef
        # targetdirectory is the one on your host e.g. your PC or the webserver
        # The taskdirs are subdirectories of the tempdir on the submission host and the working directories for the tasks
        # The targetdirectories of the tasks are subdirectories of the targetdirectory named like the taskdirs
        self.map_res_id = {}
        super(SequenceToleranceMultiJobSKAnalyzer, self).__init__(sgec, parameters, tempdir, targetroot, dldir)
    
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

    def _expandParameters(self):
        # Expand out the premutations
        premut = []
        for chain, reslist in self.parameters["Premutated"].iteritems():
            for resid, premutations in reslist.iteritems():
                premut.append((chain, resid, premutations))
        choices = []
        for i in range(len(premut)):
            choices = SequenceToleranceMultiJobSK._tmultiply(choices, premut[i])
        
        # Create an array of parameters
        multiparameters = []
        numberOfRuns = len(choices)
        self.numberOfRuns = numberOfRuns
        for i in range(numberOfRuns):
            premutated = {}
            for premutation in choices[i]:
                if not premutated.get(premutation[0]):
                    premutated[premutation[0]] = {}
                premutated[premutation[0]][premutation[1]] = premutation[2]
                
            multiparameters.append({
                "binary"            : self.parameters["binary"],
                "ID"                : self.parameters["ID"],
                "pdb_filename"      : self.parameters["pdb_filename"],
                #"pdb_info"          : self.parameters["pdb_info"],
                "nstruct"           : self.parameters["nstruct"],
                "radius"            : self.parameters["radius"],
                "kT"                : self.parameters["kT"],
                "Partners"          : self.parameters["Partners"],
                "Weights"           : self.parameters["Weights"],
                "Premutated"        : premutated,
                "Designed"          : self.parameters["Designed"],
                })
        self.multiparameters = multiparameters
        
    def _initialize(self):
        self.describe()
        
        parameters = self.parameters
        
        # Create input files
        self._expandParameters()
        
        self._import_pdb(parameters["pdb_filename"], parameters["pdb_info"])
        self._write_backrub_resfiles()
        self._write_seqtol_resfile()
        self._write_backrub_movemap()
        
        self.targetdirectory = "/home/oconchus/1KI1"
        
        scheduler = TaskScheduler(self.workingdir, files = [parameters["pdb_filename"], self.seqtol_resfile, self.backrub_movemap] + self.backrub_resfiles)
        
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
        
        for i in range(self.numberOfRuns):
            targettaskdir = os.path.join(self.targetdirectory, "sequence_tolerance%d" % i)

            cmd = '''/bin/echo "process_seqtol(\'%s\', %s, %s, %s, %s, %s);\" \\
                      | /bin/cat %s - \\
                      | /usr/bin/R --vanilla''' % ( targettaskdir, fitness_coef, thresh_or_temp, type_st, percentile, prefix, specificityRScript)
                             
            self._status(cmd)
            
            # open files for stderr and stdout 
            self.file_stdout = open(self._targetdir_file_path( self.filename_stdout ), 'a+')
            self.file_stderr = open(self._targetdir_file_path( self.filename_stderr ), 'a+')
            self.file_stdout.write("*********************** R output ***********************\n")
            subp = subprocess.Popen(cmd, stdout=self.file_stdout, stderr=self.file_stderr, cwd=targettaskdir, shell=True, executable='/bin/bash')
                    
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
            if not os.path.exists(os.path.join(targettaskdir, "tolerance_sequences.fasta") ) and count < 10 :
                time.sleep(1) # make sure the fasta file gets written
                count += 1
              
            try:
                # create weblogo from the created fasta file
                shutil.move(os.path.join(targettaskdir, "tolerance_sequences.fasta"), self._targetdir_file_path("tolerance_sequences%d.fasta" % i))
                seqs = read_seq_data(open(self._targetdir_file_path("tolerance_sequences%d.fasta" % i)))
                logo_data = LogoData.from_seqs(seqs)
                logo_data.alphabet = std_alphabets['protein'] # this seems to affect the coloring, but not the actual motif
                logo_options = LogoOptions()
                logo_options.title = "Sequence profile"
                logo_options.number_interval = 1
                logo_options.color_scheme = std_color_schemes["chemistry"]
                ann = getResIDs(self.parameters)
                logo_options.annotate = ann
                logo_format = LogoFormat(logo_data, logo_options)
                png_print_formatter(logo_data, logo_format, open(self._targetdir_file_path( "tolerance_motif%d.png" % i), 'w'))
            except Exception, e:
                self._appendError("An error occurred creating the motifs.\n%s\n%s" % (str(e), traceback.format_exc()))
                success = False
            
            try:
                # Delete the *last.pdb and generation files:
                for file in glob.glob(self._taskresultsdir_file_path("sequence_tolerance%d" % i, "*_last.pdb")):
                    self._status('deleting %s' % file)
                    os.remove(file)
                for file in glob.glob(self._taskresultsdir_file_path("sequence_tolerance%d" % i, "*_low.ga.generations.gz")):
                    self._status('deleting %s' % file)
                    os.remove(file)
            except Exception, e:
                self._appendError("An error occurred deleting files.\n%s\n%s" % (str(e), traceback.format_exc()))
                success = False
        
        # Generate tolerance motif montage
        self.verticaltiles = int(math.ceil(float(self.numberOfRuns) / float(self.horizontaltiles)))
        montagecmd = "montage -geometry +2+2 -tile %dx%d -pointsize 80 -font Times-Roman "% (self.horizontaltiles, self.verticaltiles)
        # todo: This is error-prone if we change the logic in _write_backrub_resfiles. Separate this iteration into a separate function and use for both
        for i in range(self.numberOfRuns):
            params = self.multiparameters[i]
            lbl = []
            for partner in params['Partners']:
                if params['Premutated'].get(partner):
                    pm = params['Premutated'][partner]
                    for residue in pm:
                        lbl.append("%s%d:%s" % (partner, residue, pm[residue]))
            montagecmd += "\( tolerance_motif%d.png -set label '%s' \) " % (i, join(lbl,"\\n"))             
        montagecmd += "multi_tolerance_motif.png"
        self._status(montagecmd)
        
        self.file_stdout = open(self._targetdir_file_path( self.filename_stdout ), 'a+')
        self.file_stderr = open(self._targetdir_file_path( self.filename_stderr ), 'a+')
        self.file_stdout.write("*********************** montage output ***********************\n")
        subp = subprocess.Popen(montagecmd, stdout=self.file_stdout, stderr=self.file_stderr, cwd=self.targetdirectory, shell=True, executable='/bin/bash')
        
        return True
            
    def _write_backrub_resfiles( self ):
        """create a resfile of premutations for the backrub"""
        
        # Write out the premutated residues
        self.backrub_resfiles = []
        for i in range(self.numberOfRuns):
            s = ""
            params = self.multiparameters[i]
            for partner in params['Partners']:
                if params['Premutated'].get(partner):
                    pm = params['Premutated'][partner]
                    for residue in pm:
                        #todo: check that residue exists -  # get all residues:  residue_ids     = self.pdb.aa_resids()
                        s += ("%d %s PIKAA %s\n" % (residue, partner, pm[residue]))
            
            # Only create a file if there are any premutations
            backrub_resfile = ("backrub_%s_%d.resfile" % (self.parameters["ID"], i))
            rosettahelper.writeFile(self._workingdir_file_path(backrub_resfile), 'NATAA\nstart\n%s\n' % s)
            self.backrub_resfiles.append(backrub_resfile)
               

        
class SequenceToleranceJobHK(RosettaClusterJob):

    suffix = "seqtolHK"
    name = "Sequence Tolerance (HK)"
    
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
            
        
    def __init__(self, sgec, parameters, tempdir, targetroot, dldir):
        # The tempdir is the one on the submission host e.g. chef
        # targetdirectory is the one on your host e.g. your PC or the webserver
        # The taskdirs are subdirectories of the tempdir on the submission host and the working directories for the tasks
        # The targetdirectories of the tasks are subdirectories of the targetdirectory named like the taskdirs
        self.residues      = {}   # contains the residues and their modes according to rosetta: { (chain, resID):["PIKAA","PHKL"] }
        self.backrub       = []   # residues to which backrub should be applied: [ (chain,resid), ... ]
        self.failed_runs   = []
        self.executable    = ''
        super(SequenceToleranceJobHK, self).__init__(sgec, parameters, tempdir, targetroot, dldir)
    
    def _initialize(self):
        self.describe()
        
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
        
        self._status("Checking output")
        successFSA = re.compile("DONE ::\s+\d+ starting structures built\s+\d+ \(nstruct\) times")
        streams = self.stTask.getOutputStreams()
        failed_runs = []
        list_outfiles = []
        for i in range(len(streams)):
            stdfile = streams[i]["stdout"]
            if stdfile:
                stdoutput = self._taskresultsdir_file_path("sequence_tolerance", stdfile)
                contents = rosettahelper.readFile(stdoutput)
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
            rosettahelper.writeFile(self._targetdir_file_path("failed_jobs.txt"), s)
            
        self._status("Analyzing results")
        handle_err = open( self._targetdir_file_path( 'error.log' ), 'a+' )
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
            handle2 = open(self._targetdir_file_path(frequency_file), 'w')
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

        cmd = '''/bin/echo \"plot_specificity_list(%s)\" \\
                | /bin/cat %s - > specificity.R ; \\
                /usr/bin/R CMD BATCH specificity.R''' % ( parameter, specificity_classicRScript )
        
        self._status(cmd)
        
        # Move all output files to the root so all R output gets located there
        #for file in glob.glob(self._taskresultsdir_file_path("sequence_tolerance", "*.pdb")):
        #    self._status('copying %s' % file)
        #    shutil.move(file, self.targetdirectory)
        #for file in glob.glob(self._taskresultsdir_file_path("sequence_tolerance", "*.pdb")):
        #    self._status('copying %s' % file)
        #    shutil.move(file, self.targetdirectory)
                            
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
        
        # CREATE SEQUENCE MOTIF    ## this all would be better off in the postprocessing of the onerun class
        print "\tCreate Sequence Motif\n\t+-- copy PDB files from cluster"
        # 1st, get the data
        sequences_list_total = []
        
        rosettahelper.make755Directory(self._targetdir_file_path("best_scoring_pdb"))
        
        list_files = []        
        #for file in glob.glob(self._taskresultsdir_file_path("sequence_tolerance", "BR*low_*_*.pdb")):
        for file in glob.glob(os.path.join(self.workingdir, "sequence_tolerance", "BR*low_*_*.pdb")):
            list_files.append(file.split('/')[-1].strip())
        list_files.sort()
        for filename in list_outfiles:
            print(filename)
            si = int(filename.split('.')[-1]) # get the run id
            sequences_list = []
            output_handle = open(filename, 'r')
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
            list_this_run = rosettahelper.grep('BR%slow_%04.i_[A-Z]*\.pdb' % (self.parameters['pdbRootname'], si), list_files)
            #best_scoring_pdbs = []
            structure_counter = 0 # ok it seems that not all the sequences have a corresponding pdb file. Therefore we keep the first 10 we can find!
            
            print("sequences list:%s\n" % sequences_list)
            
            for designed_sequence in sequences_list: # keep the 10 best scoring structures
                best_scoring_pdb = 'BR%slow_%04.i_%s.pdb' % (self.parameters['pdbRootname'], si, designed_sequence[0])
                if best_scoring_pdb in list_this_run:
                    print("copying %s back as best_scoring_pdb" % best_scoring_pdb)
                    #self.stTask._copyFilesBackToHost(best_scoring_pdb)
                    bspdb = os.path.join(self._workingdir_file_path("sequence_tolerance"), best_scoring_pdb)
                    shutil.copy(bspdb, self._targetdir_file_path("best_scoring_pdb"))        
                    structure_counter += 1
                if structure_counter >= 10:
                    break
        
            sequences_list_total.extend(sequences_list[0:10]) # add 10 best scoring to the total list
        
        # write the actual fasta file with the 10 best scoring sequences of each run
        if not sequences_list_total:
            sys.stderr.write("There were no sequences for the fasta file. Try increasing the value of pop_size.")
            raise PostProcessingException
                
        fasta_file = self._targetdir_file_path("tolerance_sequences.fasta")
        handle_fasta = open(fasta_file, 'w')
        i = 0
        for sequence in sequences_list_total:
            i += 1
            handle_fasta.write('>%s\n%s\n' % (i, sequence[0]))
        handle_fasta.close()
        
        # 3rd, create the motif
        count = 0
        if not os.path.exists( self._targetdir_file_path("tolerance_sequences.fasta") ) and count < 10 :
            time.sleep(1) # make sure the fasta file gets written
            count += 1
        # create weblogo from the created fasta file
        seqs = read_seq_data(open(self._targetdir_file_path("tolerance_sequences.fasta")))
        logo_data = LogoData.from_seqs(seqs)
        logo_data.alphabet = std_alphabets['protein'] # this seems to affect the coloring, but not the actual motif
        logo_options = LogoOptions()
        logo_options.title = "Sequence profile"
        logo_options.number_interval = 1
        logo_options.color_scheme = std_color_schemes["chemistry"]
        logo_options.annotate = [partner0 + str(resid) for resid in designed[partner0]] + [partner1 + str(resid) for resid in designed[partner1]] #res_nums this is for Gregs hacked version that I don't have
        logo_format = LogoFormat(logo_data, logo_options)
        png_print_formatter(logo_data, logo_format, open(self._targetdir_file_path( "tolerance_motif.png" ), 'w'))
        
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
        try:
            shutil.copy(self._taskresultsdir_file_path("minimization", self.parameters['pdb_filename']), self._targetdir_file_path("%s_minimized.pdb" % self.parameters['pdbRootname']))        
            shutil.copy(self._taskresultsdir_file_path("minimization", "%s_submission.pdb" % self.parameters['pdbRootname']), self._targetdir_file_path(self.parameters['pdb_filename']))        
        except:
            print("Exception copying PDBs back.")        
        
        return True
    
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
        self.parameters['pdb_info'] = join(self.pdb.lines, '\n')                
        
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
        rosettahelper.writeFile(self._workingdir_file_path(self.pathsfile), pathfilecontents % pathsdict)
            
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

class ParallelSequenceToleranceJobSK(RosettaClusterJob):

    suffix = "seqtolSK"
    flatOutputDirectory = True
    name = "Sequence Tolerance (SK, JMB)"
    
    def _defineOutputFiles(self):
        self.resultFilemasks.append((".", "*.pdb"))
        self.resultFilemasks.append((".", "stderr*"))
        self.resultFilemasks.append((".", "stdout*"))
        self.resultFilemasks.append((".", "timing_profile.txt"))
        self.resultFilemasks.append((".", "tolerance_*"))
        self.resultFilemasks.append((".", "*.ga.entities.gz"))
        self.resultFilemasks.append(("sequence_tolerance", "*.resfile"))
        self.resultFilemasks.append(("sequence_tolerance", "*.movemap"))
        self.resultFilemasks.append(("sequence_tolerance", "backrub_scores.dat"))
        self.resultFilemasks.append(("sequence_tolerance", "*.cmd*"))
        self.resultFilemasks.append(("sequence_tolerance", "*low*.pdb"))
            
    def __init__(self, sgec, parameters, tempdir, targetroot, dldir):
        # The tempdir is the one on the submission host e.g. chef
        # targetdirectory is the one on your host e.g. your PC or the webserver
        # The taskdirs are subdirectories of the tempdir on the submission host and the working directories for the tasks
        # The targetdirectories of the tasks are subdirectories of the targetdirectory named like the taskdirs
        self.map_res_id = {}
        super(ParallelSequenceToleranceJobSK, self).__init__(sgec, parameters, tempdir, targetroot, dldir)
    
    def _initialize(self):
        self.describe()
        
        # Create input files        
        self._import_pdb(self.parameters["pdb_filename"], self.parameters["pdb_info"])
        self._write_backrub_resfile()
        self._write_seqtol_resfile()
        self._write_backrub_movemap()
        
        scheduler = TaskScheduler(self.workingdir, files = [self.parameters["pdb_filename"], self.seqtol_resfile, self.backrub_resfile, self.backrub_movemap])
         
        targetsubdirectory = "sequence_tolerance"
        inputfiles = [self.parameters["pdb_filename"], self.backrub_resfile, self.backrub_movemap, self.seqtol_resfile]
        taskdir = self._make_taskdir(targetsubdirectory, inputfiles)
        targetdir = os.path.join(self.targetdirectory, targetsubdirectory)
        
        if self.parameters["binary"] == "seqtolJMB":
            jobname = "Sequence tolerance (SK JMB)"
        elif self.parameters["binary"] == "seqtolP1":
            jobname = "Sequence tolerance (SK PLoS One)"
        else:
            self._status('Unrecognised binary passed as parameter to cluster job: %s' % self.parameters["binary"])
            raise
        
        stTask = BackrubSequenceToleranceSK(taskdir, targetdir, self.parameters, self.backrub_resfile, self.seqtol_resfile, movemap = self.backrub_movemap, name=jobname)
         
        scheduler.addInitialTasks(stTask)
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
        
        #targetTaskDir =  os.path.join(self.targetdirectory, "sequence_tolerance")
        # Move any output files to the root so all R output gets located there
        for file in glob.glob(self._taskresultsdir_file_path("sequence_tolerance", "*ga.entities*")):
            self._status('copying %s' % file)
            shutil.move(file, self.targetdirectory)
        
        # Create the standard output file where the R script expects it
        firststdout = None
        firstlowfile = None
        for file in glob.glob(self._taskresultsdir_file_path("sequence_tolerance", "*.cmd.o*.1")):
            firststdout = file
            break
        for file in glob.glob(self._workingdir_file_path(self.parameters["pdb_filename"])):
            originalpdb = file
            break
        if firststdout and originalpdb:
            self._status("Copying stdout and original PDB for R script boxplot names: (%s, %s)" % (firststdout, firstlowfile))
            shutil.copy(firststdout, self._targetdir_file_path("seqtol_1_stdout.txt"))
            shutil.copy(originalpdb, self.targetdirectory)
        else:
            self._status("Could not find stdout or original PDB for R script boxplot names: (%s, %s)" % (firststdout, firstlowfile))
                            
        # Run the R script and pipe stderr and stdout to file 
        cmd = '''/bin/echo "process_seqtol(\'%s\', %s, %s, %s, %s, %s);\" \\
                  | /bin/cat %s - \\
                  | /usr/bin/R --vanilla''' % ( self.targetdirectory, fitness_coef, thresh_or_temp, type_st, percentile, prefix, specificityRScript)                
        self._status(cmd)
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
        
        success = True
        try:
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
            
            # Change the logo size of the X-axis for readability
            logo_options.number_fontsize = 3.5
            
            # Change the logo size of the Weblogo 'fineprint' - the default Weblogo text
            logo_options.small_fontsize = 4
            
            # Move the Weblogo fineprint to the left hand side for readability
            fineprinttabs = "\t" * (int(2.7 * float(len(ann))))
            logo_options.fineprint = "%s\t%s" % (logo_options.fineprint, fineprinttabs)


            logo_format = LogoFormat(logo_data, logo_options)
            png_print_formatter(logo_data, logo_format, open(self._targetdir_file_path( "tolerance_motif.png" ), 'w'))
        except Exception, e:
            self._appendError("An error occurred creating the motifs.\n%s\n%s" % (str(e), traceback.format_exc()))
            success = False
        
        try:
            # Delete the generation files, empty files, and duplicated stdout file
            for file in glob.glob(self._taskresultsdir_file_path("sequence_tolerance", "*_low.ga.generations.gz")):
                self._status('deleting %s' % file)
                os.remove(file)
            for file in glob.glob(self._targetdir_file_path("*")):
                if os.path.getsize(file) == 0:
                    self._status('Deleting empty file %s' % file)
                    os.remove(file)
            os.remove(self._targetdir_file_path("seqtol_1_stdout.txt"))    
        except Exception, e:
            self._appendError("An error occurred deleting files.\n%s\n%s" % (str(e), traceback.format_exc()))
            success = False
        
        return success
    
    def _import_pdb(self, filename, contents):
        """Import a pdb file from the database and write it to the temporary directory"""
        self.pdb = pdb.PDB(contents.split('\n'))
      
        # remove everything but the chosen chains or keep all chains if the list is empty
        # pdb_content is passed directly to backrub so remove the pruned chain lines before the backrub
        self.pdb.pruneChains(self.parameters['Partners'])
        self.pdb.remove_hetatm()  # rosetta doesn't like heteroatoms so let's remove them
        self.parameters['pdb_info'] = join(self.pdb.lines, '\n')        
        # internal mini resids don't correspond to the pdb file resids
        # the pivot residues need to be numbered consecutively from 1 up
        self.map_res_id = self.pdb.get_residue_mapping()
        self.parameters["map_res_id"] = self.map_res_id 
        
        self.pdb.write(self._workingdir_file_path(filename))
    
    def _write_backrub_movemap( self ):
        """create a movemap minimizing all chi angles"""
        self.backrub_movemap = "allchi_%s.movemap" % self.parameters["ID"]
        rosettahelper.writeFile(self._workingdir_file_path(self.backrub_movemap), 'RESIDUE * CHI\n')
    
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
        rosettahelper.writeFile(self._workingdir_file_path(self.backrub_resfile), 'NATAA\nstart\n%s\n' % s)
        
        
    def _write_seqtol_resfile( self ):
        """create a resfile for the chains
            residues in interface: NATAA (conformation can be changed)
            residues mutation: PIKAA ADEFGHIKLMNPQRSTVWY (design sequence)"""
        
        resfileHasContents, contents = make_seqtol_resfile( self.pdb, self.parameters, self.parameters['radius'], self.pdb.aa_resids())
                
        if resfileHasContents:
            self.seqtol_resfile = "seqtol_%s.resfile" % self.parameters["ID"]
            rosettahelper.writeFile(self._workingdir_file_path(self.seqtol_resfile), "%s\n" % contents)
        else:
            sys.stderr.write("An error occurred during the sequence tolerance execution. The chosen designed residues resulting in an empty resfile and so could not be used.")
            raise SequenceToleranceException 
        
        