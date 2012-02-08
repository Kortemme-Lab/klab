#!/usr/bin/python2.4
# encoding: utf-8
"""
RosettaTasks.py

Created by Shane O'Connor 2011.
Copyright (c) 2011 __UCSF__. All rights reserved.
"""


import sys
if __name__ == "__main__":
	sys.path.insert(0, "../common/")
	sys.path.insert(1, "/clustertest/daemon/")
 
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
from corebio.seq import unambiguous_protein_alphabet 

from conf_daemon import *
import chainsequence       
import pdb
from analyze_mini import AnalyzeMini
from ClusterTask import ClusterTask, ClusterScript, ddGClusterScript, getClusterDatabasePath, FAILED_TASK
from ClusterScheduler import TaskScheduler, RosettaClusterJob

if os.environ.get('PWD'):
	settings = WebsiteSettings(sys.argv, os.environ['PWD'])
else:
	settings = WebsiteSettings(sys.argv, os.environ['SCRIPT_NAME'])

server_root = settings["BaseDir"]
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

def testMotifs():
	from corebio.seq import unambiguous_protein_alphabet

	#select ID, cryptID from backrub where ID in (2083, 2084, 2085, 2086, 2087, 2088, 2099, 2135, 2140, 2169);

	lst = [
		(2083, ["A5"], "eee056255a1cdffd9e2930f3e79462c7"),
		(2084, ["A7"], "5d3942ad60e2fe3c0037c4205c7a9b10"),
		(2085, ["A16"], "cd39310c0fe815b480301f92618abdb4"),
		(2086, ["A18"], "d5c1718732c031b185880697d6886021"),
		(2087, ["A30"], "d8c3a7c1655bb831953c00905fa9ab50"),
		(2088, ["A33"], "66cdb2db3ac129a5b3ef19063f13276e"),
		(2099, ["A320", "A324", "A266", "A302", "A306", "A339", "A309", "A278", "A343", "A282"], "046f425345acfc0185900aaac3fac75e"),
		(2135, ["B32", "B34", "B9", "B10", "B11", "B13", "B14", "B15", "B16", "B17"], "1459b26408f3d7a90997ecf638a6a816"),
		(2140, ["B36", "B37", "B39", "B11", "B12", "B13", "B15", "B16", "B17", "B18"], "93f3ae634c088f87e0fb1945c918c7b5"),
		(2169, ["A57", "A58", "A59", "A60", "A61", "A62"], "ddf3952befe9921848678a94642d7927"),
	]
	# 2169 molson - Mark Olson molson@compbiophys.org
	# 2140, 2135 jehg - Jorge Hernandez jehg@fbio.uh.cu
	# 2099 jkoerber - James Koerber	 jtkoerber@gmail.com
	# 2083-2088 grigori - Grigori Ermakov	   grigori.ermakov@merck.com
	for i in range(len(lst)):
		jobID = lst[i][0]
		infasta = "/home/oconchus/ticket146/%s.fasta" % jobID
		dlroot = "/var/www/html/rosettaweb/backrub/downloads/"
		dldir = os.path.join(dlroot, lst[i][2])
		outpng = os.path.join(dldir, "tolerance_motif.png")
		expectedStdout = os.path.join(dldir, "stdout_seqtolSK_%s.txt" % jobID)
		if not os.path.exists(expectedStdout):
			print("Are we sure this is the correct path? %s for job %s. Missing %s." % (dldir, jobID, expectedStdout))
			sys.exit(1)
		annotations = lst[i][1] 
		
		# create weblogo from the created fasta file
		seqs = read_seq_data(open(infasta), alphabet=unambiguous_protein_alphabet)
		logo_data = LogoData.from_seqs(seqs)	
		logo_options = LogoOptions()
		logo_options.title = "Sequence profile"
		logo_options.number_interval = 1
		logo_options.color_scheme = std_color_schemes["chemistry"]
		logo_options.annotate = sorted(annotations)
		
		# Change the logo size of the X-axis for readability
		logo_options.number_fontsize = 3.5
		
		# Change the logo size of the Weblogo 'fineprint' - the default Weblogo text
		logo_options.small_fontsize = 4

		# Move the Weblogo fineprint to the left hand side for readability
		fineprinttabs = "\t" * (int(2.7 * float(len(annotations))))
		logo_options.fineprint = "%s\t%s" % (logo_options.fineprint, fineprinttabs)

		logo_format = LogoFormat(logo_data, logo_options)
		if not os.path.exists(outpng):
			print("Missing original motif for job %s." % jobID)
		png_print_formatter(logo_data, logo_format, open(outpng, 'w'))
		
		
def createSequenceMotif(infasta, annotations, outpng):
	# create weblogo from the created fasta file
	seqs = read_seq_data(open(infasta), alphabet=unambiguous_protein_alphabet)
	logo_data = LogoData.from_seqs(seqs)	
	logo_options = LogoOptions()
	logo_options.title = "Sequence profile"
	logo_options.number_interval = 1
	logo_options.color_scheme = std_color_schemes["chemistry"]
	logo_options.annotate = annotations
	
	# Change the logo size of the X-axis for readability
	logo_options.number_fontsize = 3.5
	
	# Change the logo size of the Weblogo 'fineprint' - the default Weblogo text
	logo_options.small_fontsize = 4
	
	# Move the Weblogo fineprint to the left hand side for readability
	fineprinttabs = "\t" * (int(2.7 * float(len(annotations))))
	logo_options.fineprint = "%s\t%s" % (logo_options.fineprint, fineprinttabs)

	logo_format = LogoFormat(logo_data, logo_options)
	png_print_formatter(logo_data, logo_format, open(outpng, 'w'))

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
	#	for neighbor in neighbor_lists.get(res) or []:
	#		resentry["%s %s" % (neighbor[1:].strip(), neighbor[0])] = " NATAA\n"  
	# Add the designed residues to the designed set, overriding any existing flexible entries
	for res in design:
		resentry["%s %s" % (res[1:].strip(), res[0])] = " PIKAA ADEFGHIKLMNPQRSTVWY\n"		
	
	if not resentry:
		return False, "The chosen designed residues resulting in an empty resfile and so could not be used."	
	
	contents = 'NATRO\nstart\n'
	for k,v in iter(sorted(resentry.iteritems())):
		contents += k + v
		
	return True, contents


class SequenceToleranceSKTask(ClusterTask):

	# additional attributes
	prefix = "SeqTolerance"
		 
	def __init__(self, workingdir, targetdirectory, parameters, backrub_resfile, seqtol_resfile, movemap=None, name=""):
		self.backrub_resfile	= backrub_resfile
		self.seqtol_resfile	 = seqtol_resfile
		self.movemap			= movemap
		self.residues		   = {}   # contains the residues and their modes according to rosetta: { (chain, resID):["PIKAA","PHKL"] }
		self.pivot_res		  = []   # list of pivot residues, consecutively numbered from 1 [1,...]
		self.map_res_id		 = {}   # contains the mapping from (chain,resid) to pivot_res
		
		if not parameters.get("binary") or not(parameters["binary"] == "seqtolJMB" or parameters["binary"] == "seqtolP1" or parameters["binary"] == "multiseqtol"):
			raise Exception
						
		super(SequenceToleranceSKTask, self).__init__(workingdir, targetdirectory, '%s_%d.cmd' % (self.prefix, parameters["ID"]), parameters, name, parameters["nstruct"])		  
	
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
		elif parameters["binary"] == "seqtolP1" or parameters["binary"] == "multiseqtol":
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
			if residue[1] == 0:
				self.pivot_res.append( self.map_res_id[ '%s   0' % residue[0]  ] )
			else:
				self.pivot_res.append( self.map_res_id[ '%s%4.i' % residue  ] )
	
	def retire(self):
		passed = super(SequenceToleranceSKTask, self).retire()
							   
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


# Sequence Tolerance SK Tasks        
class SequenceToleranceSKTaskFixBB(SequenceToleranceSKTask):

	# additional attributes
	prefix = "SeqTolerance"
		 
	def __init__(self, workingdir, targetdirectory, parameters, seqtol_resfile, name=""):
		self.seqtol_resfile	 = seqtol_resfile
		self.residues		   = {}   # contains the residues and their modes according to rosetta: { (chain, resID):["PIKAA","PHKL"] }
		self.pivot_res		  = []   # list of pivot residues, consecutively numbered from 1 [1,...]
		self.map_res_id		 = {}   # contains the mapping from (chain,resid) to pivot_res
		
		if not parameters.get("binary") or not(parameters["binary"] == "multiseqtol"):
			raise Exception
						
		super(SequenceToleranceSKTask, self).__init__(workingdir, targetdirectory, '%s_%d.cmd' % (self.prefix, parameters["ID"]), parameters, name, parameters["nstruct"])		  
	
	def _initialize(self):
		self._prepare_backrub()
		parameters = self.parameters
				
		self.br_output_prefixes = ["%04i_" % (i + 1) for i in range(parameters["nstruct"])]
		self.low_files = [getOutputFilenameSK(parameters["pdbRootname"], i + 1, "low") for i in range(parameters["nstruct"])]
		self.prefixes = [lfilename[:-4] for lfilename in self.low_files]
		self.low_files = [self._workingdir_file_path(lfilename) for lfilename in self.low_files]
		#% (ct.getWorkingDir(), parameters["pdb_filename"])
		
		
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
		elif parameters["binary"] == "seqtolP1" or parameters["binary"] == "multiseqtol":
			score_weights = "standard"
			score_patch = "score12"
			ref_offsets = "HIS 1.2"
		
		# The input was generated using Rosetta 3.3 release and the following commands
		fixBBcmd = '''
./fixbb.static.linuxgccrelease -database /home/oconchus/ddgsrc/r3.3/rosetta_database -s 1KI1.pdb -resfile 1KI1.resfile -nstruct 1 -ignore_unrecognized_res -ex1 -ex2 -extrachi_cutoff 0 -score:weights standard -score:patch score12 -overwrite
mv 1KI1_0001.pdb 1KI1_fixbb_out.pdb
'''

		backrubCommand = [
			'# Setup seqtol', '', 
			'cp 1KI1_fixbb_out.pdb %s_${SGE_TASK_ID4}_low.pdb' % (parameters["pdbRootname"]), ''] 
		
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
			if residue[1] == 0:
				self.pivot_res.append( self.map_res_id[ '%s   0' % residue[0]  ] )
			else:
				self.pivot_res.append( self.map_res_id[ '%s%4.i' % residue  ] )
	
	def retire(self):
		passed = super(SequenceToleranceSKTaskFixBB, self).retire()
							   
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
		

# Sequence Tolerance HK Tasks        

#todo: Add a required files list to all tasks and check before running

class MinimizationSeqTolHKClusterTask(ClusterTask):
					 
	prefix = "Minimization"
					 
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

	prefix = "Backrub"
				
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
			#	self._status('copying %s' % file)
			#	shutil.copy(file, self.targetdirectory)
			#for file in glob.glob(self._workingdir_file_path("*last*.pdb")):
			#	self._status('copying %s' % file)
			#	shutil.copy(file, self.targetdirectory)
				
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
	
	prefix = "SeqTolerance"
	   
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
		
class SequenceToleranceHKJob(RosettaClusterJob):

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
			
	def __init__(self, sgec, parameters, tempdir, targetroot, dldir, testonly = False):
		# The tempdir is the one on the submission host e.g. chef
		# targetdirectory is the one on your host e.g. your PC or the webserver
		# The taskdirs are subdirectories of the tempdir on the submission host and the working directories for the tasks
		# The targetdirectories of the tasks are subdirectories of the targetdirectory named like the taskdirs
		self.residues	  = {}   # contains the residues and their modes according to rosetta: { (chain, resID):["PIKAA","PHKL"] }
		self.backrub	   = []   # residues to which backrub should be applied: [ (chain,resid), ... ]
		super(SequenceToleranceHKJob, self).__init__(sgec, parameters, tempdir, targetroot, dldir, testonly)
	
	def _initialize(self):
		self.describe()
		
		parameters = self.parameters
		parameters["radius"] = 10.0		
		
		# Fill in missing parameters to avoid bad key lookups
		designed = parameters['Designed']
		partners = parameters['Partners']
		designed[partners[0]] = designed.get(partners[0]) or [] 
		designed[partners[1]] = designed.get(partners[1]) or [] 

		# Create input files		
		self.minimization_resfile = "minimize.resfile" 
		self.backrub_resfile = "backrub.resfile"
		self.seqtol_resfile = "seqtol.resfile"
		
		self._import_pdb(parameters["pdb_filename"], parameters["pdb_info"])
		self._prepare_backrub_resfile() # fills in self.backrub for resfile creation
		self._write_resfile( "NATRO", {}, [], self.minimization_resfile)
		self._write_resfile( "NATAA", {}, self.backrub, self.backrub_resfile )
		self._write_seqtol_resfile()
		   
		scheduler = TaskScheduler(self.workingdir)
		
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
	
	# *** Analysis functions ***
	def _analyze(self):
		""" this recreates Elisabeth's analysis scripts in /kortemmelab/shared/publication_data/ehumphris/Structure_2008/CODE/SCRIPTS """
				
		operations = [
			 ("checking output",				self._checkOutput),
			 ("writing amino acid frequencies", self._writeAminoAcidFrequencies),
			 ("running the R script",		   self._runRScript),
			 ("parsing output files",		   self._parseOutputFiles),
			 ("copying the best scoring pdbs",  self._copyBestScoringPDBs),
			 ("creating the sequence motif",	self._createSequenceMotif),
			 ("renaming initial PDBs",		  self._renameInitialPDBs)]
		
		for op in operations:
			try:
				self._status(op[0])
				op[1]()
			except Exception, e:
				self._status("An exception occured while %s.\n%s\n%s" % (op[0], str(e), traceback.format_exc()))
				return False
				
		return True
	
	def _checkOutput(self):
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
			self._status(s)
			if not self.testonly:
				rosettahelper.writeFile(self._targetdir_file_path("failed_jobs.txt"), s)
		
		self.list_outfiles = list_outfiles
	
	def _writeAminoAcidFrequencies(self):
		
		parameters = self.parameters
		partners = parameters['Partners']
		designed = parameters['Designed']
		
		self._status("Analyzing results")
		# AMINO ACID FREQUENCIES
		self._status("Amino Acid frequencies")
		list_res = []
		for i in range(2):
			for x in (designed[partners[i]]):
				list_res.append(partners[i] + str(x))
		
		handle_err = open( self._targetdir_file_path( 'error.log' ), 'a+' )
		# this does the same as get_data.pl
		for design_res in list_res:
			one_pos = []
			for filename in self.list_outfiles:
				handle = open(filename,'r')
				grep_result = rosettahelper.grep('^ %s' % self.map_chainres2seq[design_res], handle)
				if grep_result != []:
					one_pos.append( grep_result[0].split() )
				else:
					self.handle_err.write('Single sequence tolerance prediction run failed: see %s for details\n' % filename)
				handle.close()
			
			# sort and transpose the data of one_pos table: invert_textfiles.pl
			# the values are in the following order whereas they should be in res_order
			order = ['id','A','D','E','F','G','H','I','K','L','M','N','P','Q','R','S','T','V','W','Y']
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
		handle_err.close()
		
		Rparameter = "c("
		if not list_res:
			self._status("No residues to process.")
			raise Exception
		for design_res in list_res:
			Rparameter += "\'%s\'," % design_res
		self.Rparameter = Rparameter[:-1] + ")" # gets rid of the last ','
	
	def _runRScript(self):
		'''Run the R script for all positions and create the boxplots. Depends on _writeAminoAcidFrequencies.''' 
		cmd = '''/bin/echo \"plot_specificity_list(%s)\" \\
				| /bin/cat %s - > specificity.R ; \\
				/usr/bin/R CMD BATCH specificity.R''' % ( self.Rparameter, specificity_classicRScript )
		
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
					self._status("An error occurred during the postprocessing script. The errorcode is %d." % returncode)
					raise PostProcessingException
				break;
			time.sleep(2)
		self.file_stdout.close()
		self.file_stderr.close()
	
	def _parseOutputFiles(self):
		'''Read the output files to read in the sequences. Depends on _checkOutput.'''
		# CREATE SEQUENCE MOTIF	## this all would be better off in the postprocessing of the onerun class
		sequences_list_total = {}
		sequences_list_pdbs = {}
		
		if not self.testonly:
			rosettahelper.make755Directory(self._targetdir_file_path("best_scoring_pdb"))
		list_files = []		
		for file in glob.glob(os.path.join(self.workingdir, "sequence_tolerance", "BR*low_*_*.pdb")):
			list_files.append(file.split('/')[-1].strip())
		list_files.sort()
		
		GeneticAlgorithmResultsString = re.compile("^\s*FIT\s*INT\s*FOLD")
		ExhaustiveSearchResultsString = re.compile("^\s*INT\s*FOLD")
		
		searchtype = None
		for filename in self.list_outfiles:
			si = int(filename.split('.')[-1]) # get the run id
			output_handle = open(filename, 'r')
			
			# Skip down until we get to the sequence tables
			for line in output_handle:
				if line.find("Done with initialization.  Starting individual sequence calculations"):
					break
			
			for line in output_handle:
				if GeneticAlgorithmResultsString.match(line):
					# Genetic algorithm - Generations data follows
					searchtype = 2
					break
				elif ExhaustiveSearchResultsString.match(line):
					# Exhaustive search - No generations data follows
					searchtype = 1
					break			
			if not searchtype:
				PostProcessingException("Could not find sequence scores.")
			elif searchtype == 1:
				# Exhaustive search
				for line in output_handle:
					if len(line) > 1:		  # normal line is not empty and the sequence is at the beginning
						data_line = line.split() # (sequence, interface score, complex score)
						# Index over both score and sequence to remove any duplicates
						sequences_list_pdbs[(float(data_line[1]), data_line[0])] = (1, si)
						# Index over score, sequence, and run id to remove any duplicate scores within a run
						sequences_list_total[(float(data_line[1]), data_line[0], si)] = (1, si)
					else:
						break # break for the first empty line. This means we're done.
					
			elif searchtype == 2:
				# Genetic algorithm
				for line in output_handle:			
					if line[0:10] == "Generation":
						GenNumber = int(line[12:13])
						break
					
				# Now the stuff we actually need to read in:
				for line in output_handle:
					if line[0:10] == "Generation":
						GenNumber = int(line[12:13])
						pass
					elif len(line) > 1:		  # normal line is not empty and the sequence is at the beginning
						data_line = line.split() # (sequence, fitness, interface score, complex score)
						# Index over both score and sequence to remove any duplicates
						sequences_list_pdbs[(float(data_line[2]), data_line[0])] = (GenNumber, si)
						# Index over score, sequence, and run id to remove any duplicate scores within a run
						sequences_list_total[(float(data_line[2]), data_line[0], si)] = (GenNumber, si)
					else:
						break # break for the first empty line. This means we're done.
			
			output_handle.close()
			
		# If the same sequence appears more than once in the same generation, remove the lower scoring ones
		pruned_sequences_list_total = {}
		listOfKeysToDelete = []
		for k, v in sequences_list_total.iteritems():
			if pruned_sequences_list_total.get((k[1], k[2])):
				existingScore = pruned_sequences_list_total[(k[1], k[2])]
				if k[0] < existingScore:
					listOfKeysToDelete.append((existingScore, k[1], k[2]))
					pruned_sequences_list_total[(k[1], k[2])] = k[0]
				else:					
					listOfKeysToDelete.append((k[0], k[1], k[2]))
			else:
				pruned_sequences_list_total[(k[1], k[2])] = k[0]
		for i in range(len(listOfKeysToDelete)):
			del sequences_list_total[listOfKeysToDelete[i]]
			   
		self.sequences_list_total = sequences_list_total
		self.sequences_list_pdbs = sequences_list_pdbs
		self.list_files = list_files
	
	def _copyBestScoringPDBs(self):
		'''Get the best scoring pdb files associated with this job. Depends on _parseOutputFiles.'''
		
		structure_counter = 0 
		
		# keep the 10 best scoring structures
		bestScoringOrder = []
		for designed_sequence, origin in sorted(self.sequences_list_pdbs.iteritems()):
			GenNumber = origin[0]
			structureIndex = origin[1]
			sequence = designed_sequence[1]
			interfaceScore = designed_sequence[0]
			best_scoring_pdb = 'BR%slow_%04.i_%s.pdb' % (self.parameters['pdbRootname'], structureIndex, sequence)
			
			if best_scoring_pdb in self.list_files:
				bspdb = os.path.join(self._workingdir_file_path("sequence_tolerance"), best_scoring_pdb)
				self._status("copying %s (%f) from run %d, generation %d back as best_scoring_pdb" % (best_scoring_pdb, interfaceScore, structureIndex, GenNumber))
				if not self.testonly:
					shutil.copy(bspdb, self._targetdir_file_path("best_scoring_pdb"))		
				bestScoringOrder.append(best_scoring_pdb)
				structure_counter += 1
			if structure_counter >= 10:
				break
		if not self.testonly:
			JmolOrder = os.path.join(self._targetdir_file_path("best_scoring_pdb"), "order.txt")
			rosettahelper.writeFile(JmolOrder, join(bestScoringOrder, "\n"))
			
	def _createSequenceMotif(self):
		'''Write the fasta file with the 50 best scoring sequences overall. Depends on _parseOutputFiles.'''
		parameters = self.parameters
		partners = parameters['Partners']
		designed = parameters['Designed']
		
		if not self.sequences_list_total:
			sys.stderr.write("There were no sequences for the fasta file. Try increasing the value of pop_size.")
			raise PostProcessingException(traceback.format_exc())
		  
		fasta_file = self._targetdir_file_path("tolerance_sequences.fasta")
		handle_fasta = open(fasta_file, 'w')
		i = 0
		for designed_sequence, origin in sorted(self.sequences_list_total.iteritems()):
			i += 1
			handle_fasta.write('>%s\n%s\n' % (i, designed_sequence[1]))
		handle_fasta.close()
   
		annotations = [partners[0] + str(resid) for resid in designed[partners[0]]] + [partners[1] + str(resid) for resid in designed[partners[1]]]
		createSequenceMotif(fasta_file, annotations, self._targetdir_file_path( "tolerance_motif.png" ))
	
	def _renameInitialPDBs(self):
		parameters = self.parameters
		shutil.copy(self._taskresultsdir_file_path("minimization", parameters['pdb_filename']), self._targetdir_file_path("%s_minimized.pdb" % parameters['pdbRootname']))		
		shutil.copy(self._taskresultsdir_file_path("minimization", "%s_submission.pdb" % parameters['pdbRootname']), self._targetdir_file_path(parameters['pdb_filename']))		
	
	# *** End of analysis functions ***
	
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
		
		parameters = self.parameters
		partners = parameters['Partners']
		designed = parameters['Designed']

		# turn list of ints in chainid, resid strings								
		self.design =  [ '%s%s' % (partners[0], str(residue).rjust(4)) for residue in designed[partners[0]] ]
		self.design += [ '%s%s' % (partners[1], str(residue).rjust(4)) for residue in designed[partners[1]] ]
		
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

		
class SequenceToleranceSKJob(RosettaClusterJob):

	suffix = "seqtolSK"
	flatOutputDirectory = True
	name = "Sequence Tolerance (SK, JMB/PLoS ONE)"
	
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
		 
	def __init__(self, sgec, parameters, tempdir, targetroot, dldir, testonly = False):
		# The tempdir is the one on the submission host e.g. chef
		# targetdirectory is the one on your host e.g. your PC or the webserver
		# The taskdirs are subdirectories of the tempdir on the submission host and the working directories for the tasks
		# The targetdirectories of the tasks are subdirectories of the targetdirectory named like the taskdirs
		self.map_res_id = {}
		super(SequenceToleranceSKJob, self).__init__(sgec, parameters, tempdir, targetroot, dldir, testonly)
		
	def _initialize(self):
		self.describe()
		self._checkBinaries()
		self.parameters["radius"] = 10.0		
		
		# Create input files
		self._import_pdb(self.parameters["pdb_filename"], self.parameters["pdb_info"])
		self._write_backrub_resfile()
		self._write_seqtol_resfile()
		self._write_backrub_movemap()
		
		scheduler = TaskScheduler(self.workingdir)
		 
		targetsubdirectory = "sequence_tolerance"
		inputfiles = [self.parameters["pdb_filename"], self.backrub_resfile, self.backrub_movemap, self.seqtol_resfile]
		taskdir = self._make_taskdir(targetsubdirectory, inputfiles)
		targetdir = os.path.join(self.targetdirectory, targetsubdirectory)
				
		stTask = SequenceToleranceSKTask(taskdir, targetdir, self.parameters, self.backrub_resfile, self.seqtol_resfile, movemap = self.backrub_movemap, name=self.jobname)
		 
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
		
		Fpwm = open(self._targetdir_file_path("tolerance_pwm.txt"))
		annotations = Fpwm.readline().split()
		if len(set(annotations).difference(set(getResIDs(self.parameters)))) != 0:
			self._status("Warning: There is a difference in the set of designed residues from the pwm (%s) and from getResIDs (%s)." % (str(getResIDs(self.parameters)), str(annotations)))
		Fpwm.close()
		success = True
		try:
			fasta_file = self._targetdir_file_path("tolerance_sequences.fasta")				
			createSequenceMotif(fasta_file, annotations, self._targetdir_file_path( "tolerance_motif.png" ))
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
					#todo: check that residue exists -  # get all residues:  residue_ids	 = self.pdb.aa_resids()
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

	def _checkBinaries(self):
		if self.parameters["binary"] == "seqtolJMB":
			self.jobname = "Sequence tolerance (SK JMB)"
		elif self.parameters["binary"] == "seqtolP1":
			self.jobname = "Sequence tolerance (SK PLoS One)"
		else:
			self._status('Unrecognised binary passed as parameter to cluster job: %s' % self.parameters["binary"])
			raise Exception

#todo: fix this with new task class
import pprint
class SequenceToleranceSKMultiJob(SequenceToleranceSKJob):

	suffix = "seqtolMultiSK"
	horizontaltiles = 4
	name = "Multiple Sequence Tolerance (SK, JMB)"
	
	def _defineOutputFiles(self):
		self.resultFilemasks.append((".", "*.pdb"))
		self.resultFilemasks.append((".", "*.png"))
		self.resultFilemasks.append((".", "stderr*"))
		self.resultFilemasks.append((".", "stdout*"))
		self.resultFilemasks.append((".", "timing_profile.txt"))
		self.resultFilemasks.append((".", "tolerance_*"))
		for i in range(self.numberOfRuns):
			seqtolSubdirectory = "sequence_tolerance%d" % i
			self.resultFilemasks.append((seqtolSubdirectory, "*.ga.entities.gz"))
			self.resultFilemasks.append((seqtolSubdirectory, "*.resfile"))
			self.resultFilemasks.append((seqtolSubdirectory, "*.movemap"))		
			self.resultFilemasks.append((seqtolSubdirectory, "backrub_scores.dat"))
			self.resultFilemasks.append((seqtolSubdirectory, "*.cmd*"))
			self.resultFilemasks.append((seqtolSubdirectory, "*low*.pdb"))
			self.resultFilemasks.append((seqtolSubdirectory, "*.png"))
			self.resultFilemasks.append((seqtolSubdirectory, "*.pdf"))
			self.resultFilemasks.append((seqtolSubdirectory, "*.txt"))
		
	def __init__(self, sgec, parameters, tempdir, targetroot, dldir, testonly = False):
		# The tempdir is the one on the submission host e.g. chef
		# targetdirectory is the one on your host e.g. your PC or the webserver
		# The taskdirs are subdirectories of the tempdir on the submission host and the working directories for the tasks
		# The targetdirectories of the tasks are subdirectories of the targetdirectory named like the taskdirs
		self.map_res_id = {}
		self.radius = 10.0
		super(SequenceToleranceSKMultiJob, self).__init__(sgec, parameters, tempdir, targetroot, dldir, testonly)
	
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
		self.parameters["radius"] = self.radius
		
		# Expand out the premutations
		premut = []
		for chain, reslist in self.parameters["Premutated"].iteritems():
			for resid, premutations in reslist.iteritems():
				premut.append((chain, resid, premutations))
		choices = []
		for i in range(len(premut)):
			choices = SequenceToleranceSKMultiJob._tmultiply(choices, premut[i])
		
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
				"binary"			: self.parameters["binary"],
				"ID"				: self.parameters["ID"],
				"pdb_filename"	  : self.parameters["pdb_filename"],
				#"pdb_info"		  : self.parameters["pdb_info"],
				"nstruct"		   : self.parameters["nstruct"],
				"radius"			: self.parameters["radius"],
				"kT"				: self.parameters["kT"],
				"Partners"		  : self.parameters["Partners"],
				"Weights"		   : self.parameters["Weights"],
				"Premutated"		: premutated,
				"Designed"		  : self.parameters["Designed"],
				})
		self.multiparameters = multiparameters
			
	def _initialize(self):
		 
		self.describe()
		self._checkBinaries()
				
		# Create input files
		parameters = self.parameters
		self._expandParameters()

		self._import_pdb(parameters["pdb_filename"], parameters["pdb_info"])
		self._write_backrub_resfiles()
		self._write_seqtol_resfile()
		self._write_backrub_movemap()
		
		scheduler = TaskScheduler(self.workingdir)
		
		for i in range(self.numberOfRuns):
			targetsubdirectory = "sequence_tolerance%d" % i
			inputfiles = [self.parameters["pdb_filename"], self.backrub_resfiles[i], self.backrub_movemap, self.seqtol_resfile]
			taskdir = self._make_taskdir(targetsubdirectory, inputfiles)
			targetdir = os.path.join(self.targetdirectory, targetsubdirectory)
			
			stTask = SequenceToleranceSKTask(taskdir, targetdir, parameters, self.backrub_resfiles[i], self.seqtol_resfile, movemap = self.backrub_movemap, name=self.jobname + "for run %d of the sequence tolerance protocol" % i)
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
		
		success = True
		
		for i in range(self.numberOfRuns):
			
			# Run the R script inside the subdirectory otherwise the recursive search will find output files from the other runs
			targettaskdir = os.path.join(self.targetdirectory, "sequence_tolerance%d" % i)
			
			# Create the standard output file where the R script expects it
			firststdout = None
			firstlowfile = None
			for file in glob.glob(self._taskresultsdir_file_path("sequence_tolerance%d" % i, "*.cmd.o*.1")):
				firststdout = file
				break
			for file in glob.glob(self._workingdir_file_path(self.parameters["pdb_filename"])):
				originalpdb = file
				shutil.copy(originalpdb, self.targetdirectory)
				break
			if firststdout and originalpdb:
				self._status("Copying stdout and original PDB for R script boxplot names: (%s, %s)" % (firststdout, firstlowfile))
				shutil.copy(firststdout, self._taskresultsdir_file_path("sequence_tolerance%d" % i, "seqtol_1_stdout.txt"))
				shutil.copy(originalpdb, targettaskdir)
			else:
				self._status("Could not find stdout or original PDB for R script boxplot names: (%s, %s)" % (firststdout, firstlowfile))
				
			
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
			   
			success = True
			Fpwm = open(os.path.join(targettaskdir, "tolerance_pwm.txt"))
			annotations = Fpwm.readline().split()
			if len(set(annotations).difference(set(getResIDs(self.parameters)))) != 0:
				self._status("Warning: There is a difference in the set of designed residues from the pwm (%s) and from getResIDs (%s)." % (str(getResIDs(self.parameters)), str(annotations)))
			Fpwm.close()
			
			try:
				# create weblogo from the created fasta file
				fasta_file = self._targetdir_file_path("tolerance_sequences%d.fasta" % i)				
				shutil.move(os.path.join(targettaskdir, "tolerance_sequences.fasta"), fasta_file)
				createSequenceMotif(fasta_file, annotations, self._targetdir_file_path( "tolerance_motif%d.png" % i))
			except Exception, e:
				self._appendError("An error occurred creating the motifs.\n%s\n%s" % (str(e), traceback.format_exc()))
				success = False
			
			# Delete the *last.pdb and generation files:
			try:
				for file in glob.glob(self._targetdir_file_path("*")):
					if os.path.getsize(file) == 0:
						self._status('Deleting empty file %s' % file)
						os.remove(file)
				#for file in glob.glob(self._taskresultsdir_file_path("sequence_tolerance%d" % i, "*_last.pdb")):
				#	self._status('deleting %s' % file)
				#	os.remove(file)
				for file in glob.glob(self._taskresultsdir_file_path("sequence_tolerance%d" % i, "*_low.ga.generations.gz")):
					self._status('deleting %s' % file)
					os.remove(file)
				#os.remove(self._targetdir_file_path("seqtol_1_stdout.txt"))
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
			montagecmd += "multi_tolerance_motif.png;"
			self._status(montagecmd)
			
			self.file_stdout = open(self._targetdir_file_path( self.filename_stdout ), 'a+')
			self.file_stderr = open(self._targetdir_file_path( self.filename_stderr ), 'a+')
			self.file_stdout.write("*********************** montage output ***********************\n")
			subp = subprocess.Popen(montagecmd, stdout=self.file_stdout, stderr=self.file_stderr, cwd=self.targetdirectory, shell=True, executable='/bin/bash')
			
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
						#todo: check that residue exists -  # get all residues:  residue_ids	 = self.pdb.aa_resids()
						s += ("%d %s PIKAA %s\n" % (residue, partner, pm[residue]))
			
			# Only create a file if there are any premutations
			backrub_resfile = ("backrub_%s_%d.resfile" % (self.parameters["ID"], i))
			rosettahelper.writeFile(self._workingdir_file_path(backrub_resfile), 'NATAA\nstart\n%s\n' % s)
			self.backrub_resfiles.append(backrub_resfile)

	def _checkBinaries(self):
		if self.parameters["binary"] != "multiseqtol":
			self._status('Unrecognised binary passed as parameter to cluster job: %s' % self.parameters["binary"])
			raise Exception
		self.jobname = "Sequence tolerance (SK JMB)"

# Analysis classes for quick testing of the analysis functions. No cluster jobs are submitted so these rely on existing data for analysis

class SequenceToleranceHKJobAnalyzer(SequenceToleranceHKJob):
			   
	def __init__(self, sgec, parameters, tempdir, targetroot, dldir, (directoryToAnalyse, jobid)):
		self.directoryToAnalyse = directoryToAnalyse 
		self.jobid = jobid
		super(SequenceToleranceHKJobAnalyzer, self).__init__(sgec, parameters, tempdir, targetroot, dldir, testonly = True)
	
	def _initialize(self):
		self.describe()
		
		parameters = self.parameters
		
		# Fill in missing parameters to avoid bad key lookups
		designed = parameters['Designed']
		partners = parameters['Partners']
		designed[partners[0]] = designed.get(partners[0]) or [] 
		designed[partners[1]] = designed.get(partners[1]) or [] 

		# Create input files		
		self.minimization_resfile = "minimize.resfile" 
		self.backrub_resfile = "backrub.resfile"
		self.seqtol_resfile = "seqtol.resfile"
		
		self._import_pdb(parameters["pdb_filename"], parameters["pdb_info"])
		self._prepare_backrub_resfile() # fills in self.backrub for resfile creation
		self._write_resfile( "NATRO", {}, [], self.minimization_resfile)
		self._write_resfile( "NATAA", {}, self.backrub, self.backrub_resfile )
		self._write_seqtol_resfile()
		
		self.targetdirectory = self.directoryToAnalyse
		self.workingdir = self.directoryToAnalyse
		
		scheduler = TaskScheduler(self.workingdir)
		self.stTask = SequenceToleranceHKClusterTask(self.targetdirectory, self.targetdirectory, parameters, self.seqtol_resfile, name="Sequence tolerance step for sequence tolerance protocol")
		numtasks = parameters["nstruct"] 
		for i in range(1, numtasks + 1):
			if numtasks == 1:
				filename_stdout = "%s.o%s" % (self.stTask.scriptfilename, self.jobid)
				filename_stderr = "%s.e%s" % (self.stTask.scriptfilename, self.jobid)
			else:
				filename_stdout = "%s.o%s.%d" % (self.stTask.scriptfilename, self.jobid, i)
				filename_stderr = "%s.e%s.%d" % (self.stTask.scriptfilename, self.jobid, i)
			self.stTask.outputstreams.append({"stdout" : filename_stdout, "stderr" : filename_stderr})
		
		self.scheduler = scheduler
	
	# *** Analysis functions ***
	def _analyze(self):
		""" This recreates Elisabeth's analysis scripts in /kortemmelab/shared/publication_data/ehumphris/Structure_2008/CODE/SCRIPTS """
		
		operations = [
			 ("checking output",					self._checkOutput),
			 ("parsing output files",			   self._parseOutputFiles),
			 ("determining the best scoring pdbs",  self._copyBestScoringPDBs),
			 ("printing out the best scoring",	  self._printbestscoring)]
		
		for op in operations:
			try:
				self._status(op[0])
				op[1]()
			except Exception, e:
				self._status("An exception occured while %s.\n%s\n%s" % (op[0], str(e), traceback.format_exc()))
				return False
				
		return True
	
	def _printbestscoring(self):
		bestscoring = ["\n\n", "	 Score\t\tSequence\tGeneration\tRun#", "	 *******\t\t********\t**********\t****"]
		frequency = {}
		counter = 1
		for k,v in sorted(self.sequences_list_total.iteritems()):
			location = "Run%03d-Gen%d:%.2f" % (v[1], v[0], k[0])
			if frequency.get(k[1]):
				frequency[k[1]] = (frequency[k[1]][0] + 1, frequency[k[1]][1] + [location])
			else:
				frequency[k[1]] = (1, [location])
			bestscoring.append("%03d: %.3f\t\t%s\t\t%d\t\t%d" % (counter, k[0], k[1], v[0], v[1]))
			counter += 1
		print("Sequences with a frequency greater than 1:")
		for k, v in sorted(frequency.iteritems(), key=lambda(k,v): (v[0], k)):
			if v[0] > 1:
				print("%s, %d, %s" % (k, v[0], sorted(v[1])))
		print(join(bestscoring[:150], "\n"))

class SequenceToleranceSKMultiJobFixBB(SequenceToleranceSKMultiJob):

	def _initialize(self):
		 
		self.describe()
		self._checkBinaries()
				
		# Create input files
		parameters = self.parameters
		self._expandParameters()

		self._import_pdb(parameters["pdb_filename"], parameters["pdb_info"])
		self._write_seqtol_resfile()
		
		scheduler = TaskScheduler(self.workingdir)
		
		for i in range(self.numberOfRuns):
			targetsubdirectory = "sequence_tolerance%d" % i
			inputfiles = [self.parameters["pdb_filename"], self.seqtol_resfile]
			taskdir = self._make_taskdir(targetsubdirectory, inputfiles)
			targetdir = os.path.join(self.targetdirectory, targetsubdirectory)
			
			stTask = SequenceToleranceSKTaskFixBB(taskdir, targetdir, parameters, self.seqtol_resfile, name=self.jobname + "for run %d of the sequence tolerance protocol" % i)
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
		
		success = True
		
		for i in range(self.numberOfRuns):
			
			# Run the R script inside the subdirectory otherwise the recursive search will find output files from the other runs
			targettaskdir = os.path.join(self.targetdirectory, "sequence_tolerance%d" % i)
			
			# Create the standard output file where the R script expects it
			firststdout = None
			firstlowfile = None
			for file in glob.glob(self._taskresultsdir_file_path("sequence_tolerance%d" % i, "*.cmd.o*.1")):
				firststdout = file
				break
			for file in glob.glob(self._workingdir_file_path(self.parameters["pdb_filename"])):
				originalpdb = file
				shutil.copy(originalpdb, self.targetdirectory)
				break
			if firststdout and originalpdb:
				self._status("Copying stdout and original PDB for R script boxplot names: (%s, %s)" % (firststdout, firstlowfile))
				shutil.copy(firststdout, self._taskresultsdir_file_path("sequence_tolerance%d" % i, "seqtol_1_stdout.txt"))
				shutil.copy(originalpdb, targettaskdir)
			else:
				self._status("Could not find stdout or original PDB for R script boxplot names: (%s, %s)" % (firststdout, firstlowfile))
				
			
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
			   
			success = True
			Fpwm = open(os.path.join(targettaskdir, "tolerance_pwm.txt"))
			annotations = Fpwm.readline().split()
			if len(set(annotations).difference(set(getResIDs(self.parameters)))) != 0:
				self._status("Warning: There is a difference in the set of designed residues from the pwm (%s) and from getResIDs (%s)." % (str(getResIDs(self.parameters)), str(annotations)))
			Fpwm.close()
			
			try:
				# create weblogo from the created fasta file
				fasta_file = self._targetdir_file_path("tolerance_sequences%d.fasta" % i)				
				shutil.move(os.path.join(targettaskdir, "tolerance_sequences.fasta"), fasta_file)
				createSequenceMotif(fasta_file, annotations, self._targetdir_file_path( "tolerance_motif%d.png" % i))
			except Exception, e:
				self._appendError("An error occurred creating the motifs.\n%s\n%s" % (str(e), traceback.format_exc()))
				success = False
			
			# Delete the *last.pdb and generation files:
			try:
				for file in glob.glob(self._targetdir_file_path("*")):
					if os.path.getsize(file) == 0:
						self._status('Deleting empty file %s' % file)
						os.remove(file)
				#for file in glob.glob(self._taskresultsdir_file_path("sequence_tolerance%d" % i, "*_last.pdb")):
				#	self._status('deleting %s' % file)
				#	os.remove(file)
				for file in glob.glob(self._taskresultsdir_file_path("sequence_tolerance%d" % i, "*_low.ga.generations.gz")):
					self._status('deleting %s' % file)
					os.remove(file)
				#os.remove(self._targetdir_file_path("seqtol_1_stdout.txt"))
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
			montagecmd += "multi_tolerance_motif.png;"
			self._status(montagecmd)
			
			self.file_stdout = open(self._targetdir_file_path( self.filename_stdout ), 'a+')
			self.file_stderr = open(self._targetdir_file_path( self.filename_stderr ), 'a+')
			self.file_stdout.write("*********************** montage output ***********************\n")
			subp = subprocess.Popen(montagecmd, stdout=self.file_stdout, stderr=self.file_stderr, cwd=self.targetdirectory, shell=True, executable='/bin/bash')
			
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

		except Exception, e:
			self._appendError("An error occurred creating the motif montage.\n%s\n%s" % (str(e), traceback.format_exc()))
			success = False
				
		return success

class SequenceToleranceSKJobAnalyzer(SequenceToleranceSKJob):
			   
	def __init__(self, sgec, parameters, tempdir, targetroot, dldir, directoryToAnalyse):
		self.directoryToAnalyse = directoryToAnalyse 
		super(SequenceToleranceSKJobAnalyzer, self).__init__(sgec, parameters, tempdir, targetroot, dldir)
	
	def _initialize(self):
		self.describe()
		self._checkBinaries()
		
		parameters = self.parameters
		
		# Create input files
		self._import_pdb(parameters["pdb_filename"], parameters["pdb_info"])
		self._write_backrub_resfile()
		self._write_seqtol_resfile()
		self._write_backrub_movemap()
		
		self.targetdirectory = self.directoryToAnalyse
		
		scheduler = TaskScheduler(self.workingdir)
		
		self.scheduler = scheduler
		
class SequenceToleranceSKMultiJobAnalyzer(SequenceToleranceSKMultiJob):
		
	def __init__(self, sgec, parameters, tempdir, targetroot, dldir, directoryToAnalyse, testonly = False):
		self.directoryToAnalyse = directoryToAnalyse
		print("***")
		print(directoryToAnalyse)
		super(SequenceToleranceSKMultiJobAnalyzer, self).__init__(sgec, parameters, tempdir, targetroot, dldir, testonly)
		
	def _initialize(self):
		self.describe()
		
		parameters = self.parameters
		
		# Create input files
		self._expandParameters()
		
		self._import_pdb(parameters["pdb_filename"], parameters["pdb_info"])
		#self._write_backrub_resfiles()
		#self._write_seqtol_resfile()
		#self._write_backrub_movemap()
		
		# Change this to the target directory for analysis
		self.targetdirectory = self.directoryToAnalyse
		
		scheduler = TaskScheduler(self.workingdir)
		
		self.scheduler = scheduler

##### CUT HERE
import ddgproject
ddgfields = ddgproject.FieldNames()

class GenericDDGTask(ClusterTask):

	# additional attributes
		 
	def __init__(self, workingdir, targetdirectory, jobparameters, taskparameters, name="", prefix = "ddG"):
		self.prefix = prefix
		self.taskparameters = taskparameters
		self.inputs = {"BIN_DIR" : taskparameters["ToolVersion"], "DATABASE_DIR" : taskparameters["DBToolVersion"]}
		self.outputs = {}
		super(GenericDDGTask, self).__init__(workingdir, targetdirectory, '%s_%d.cmd' % (self.prefix, jobparameters["ID"]), jobparameters, name, numtasks = 1) # todo: do not hardcode numtasks
		
	def addInputs(self, inpts):
		self._status("Adding inputs: %s" % inpts)
		for k, v in inpts.iteritems():
			if self.inputs.get(k):
				raise Exception("Overwriting task input %s (old value = %s, attempted new value = %s)", (k, self.inputs[k], v))
			self.inputs[k] = v
		
	def addOutputs(self, outputs):
		self.outputs = outputs
	
	def getOutputs(self, taskref):
		self._status("Asking for outputs for %s" % str(taskref))
		for taskRefandIDPair, params in self.outputs.iteritems():
			if taskRefandIDPair[0] == taskref:
				self._status("Found a match: %s" % params)
				return params
		self._status("No match for you! Come back, one year!")
		return {}			
		
	def setOutput(self, key, val, taskID = None):
		outputs = self.outputs
		if taskID:
			# Set the value for a specific task based on the StepID field of the ProtocolStep table
			for taskRefandIDPair, params in outputs.iteritems():
				self._status("YOP %s:%s" % taskRefandIDPair, params)
				if taskRefandIDPair[1] == taskID:
					if key in params:
						params[key] = val
						break
					else:
						raise Exception("Trying to set a value %s for key %s between tasks %s->%s when the key does not exist in the parameter table for the target task." % (val, key, self.name, taskID))
		else:
			# Set the value for all tasks
			foundkey = False
			for taskRefandIDPair, params in outputs.iteritems():
				if key in params:
					params[key] = val
					foundkey = True
			if not foundkey:
				raise Exception("Trying to set a value %s for key %s of task %s when the key does not exist in the parameter table." % (val, key, self.name))

	def _initialize(self):
		pass
		#jobparameters = self.parameters
		#taskparameters = self.taskparameters
		
	def start(self, sgec, dbID):
		# Create script
		self._status("starting")
		inputs = self.inputs
		for k, v in inputs.iteritems():
			if not v:
				self._status("The input parameter %s has not been specified." % k)
				raise Exception("The input parameter %s has not been specified." % k)
		ct = ddGClusterScript(self.workingdir, inputs, numtasks = self.numtasks)
		self.script = ct.createScript(self.taskparameters["Command"].split("\n"), type="ddG")
		return super(GenericDDGTask, self).start(sgec, dbID)
				

class ddgScore(object):
	type = None
	version = None
	
	def __init__(self, data = {}):
		self.data = data
	
	def getType(self):
		return type
	
	def getVersion(self):
		return version
	
	def setData(self, data):
		self.data = data

	def getScores(self):
		return {"type" : self.type, "version" : self.version, "data" : self.data}

class ddgTestScore(ddgScore):
	type = "test"
	version = "0.1"

class GenericddGJob(RosettaClusterJob):

	suffix = "ddG"
	flatOutputDirectory = True
	name = "ddG"

	def _defineOutputFiles(self):
		self.resultFilemasks.append((".", "*"))
		
	def getddG(self):
		return self.ddG.getScores()

	def __init__(self, sgec, parameters, tempdir, targetroot, dldir, testonly = False):
		# The tempdir is the one on the submission host e.g. chef
		# targetdirectory is the one on your host e.g. your PC or the webserver
		# The taskdirs are subdirectories of the tempdir on the submission host and the working directories for the tasks
		# The targetdirectories of the tasks are subdirectories of the targetdirectory named like the taskdirs
		self.ddG = ddgTestScore()
		super(GenericddGJob, self).__init__(sgec, parameters, tempdir, targetroot, dldir, testonly)
			
	def _initialize(self):
		parameters = self.parameters
		parameters['_CMD'] = {} # This stores task parameters set up by the Job. The keys must have unique names per task if different values are required for each task.
		parameters['_FILE_ID'] = "%s-%s" % (parameters[ddgfields.ExperimentID], parameters[ddgfields.PDB_ID])
		ProtocolGraph = parameters["ProtocolGraph"]
		for taskID, details in ProtocolGraph.iteritems():
			if details["ToolVersion"][0] != "r":
				details["ToolVersion"] = "r%s" % details["ToolVersion"]
			if details["DBToolVersion"][0] != "r":
				details["DBToolVersion"] = "r%s" % details["DBToolVersion"]
		
		# Create files
		self.describe()
		self._generateFiles()
		
		# Create tasks from the protocol steps
		tasks = {}
		ProtocolGraph = parameters["ProtocolGraph"]
		for taskID, details in ProtocolGraph.iteritems():
			taskcls = details["ClassName"] or "GenericDDGTask"
			taskcls = taskcls.replace(".", "") # todo : remove this step later when everything is separated into modules
			taskcls = globals()[taskcls]
			targetsubdirectory = details["DirectoryName"]
			taskdir = self._make_taskdir(targetsubdirectory)
			details["_task"] = taskcls(taskdir, os.path.join(self.targetdirectory, targetsubdirectory), parameters, details, name=details["ProtocolStepID"], prefix=details["ProtocolStepID"])

		# Define the input and output parameters
		for taskID, details in ProtocolGraph.iteritems():
			task_inputs = {}
			task_outputs = {}
			stepID = details["ProtocolStepID"]
			for tpl, cparams in parameters["CommandParameters"].iteritems():
				jobparam = None
				if tpl[0] == tpl[1]:
					raise Exception("Badly specified protocol parameters - step %s feeds into itself." % tpl[0])
				elif tpl[0] == stepID:
					trgt_o = ProtocolGraph[tpl[1]]["_task"]
					for cmdparam in cparams:
						task_outputs[(trgt_o, trgt_o.prefix)] = task_outputs.get((trgt_o, trgt_o.prefix), {})
						task_outputs[(trgt_o, trgt_o.prefix)][cmdparam[0]] = cmdparam[1] or jobparam 
				elif tpl[1] == stepID:
					for cmdparam in parameters["CommandParameters"][tpl]:
						jobparam = parameters['_CMD'].get(cmdparam[0])
						if jobparam and cmdparam[1]:
							raise Exception("Task #%d: %s is defined by both the Job and the database entry." % (stepID, cmdparam[0]))
						elif not(jobparam or cmdparam[1]) and tpl[0] == None: # Allow null values to be filled in by parent tasks
							raise Exception("Task #%d: %s is undefined." % (stepID, cmdparam[0]))
						else:
							task_inputs[cmdparam[0]] = cmdparam[1] or jobparam
			ProtocolGraph[stepID]["_task"].addInputs(task_inputs)
			ProtocolGraph[stepID]["_task"].addOutputs(task_outputs)
		
		self.ProtocolGraph = ProtocolGraph
				 
		# Create a scheduler from the protocol graph
		scheduler = TaskScheduler(self.workingdir) 
		for taskID, details in ProtocolGraph.iteritems():
			for p in details["Parents"]:
				details["_task"].addPrerequisite(ProtocolGraph[p]["_task"])
		for itask in parameters["InitialTasks"]:
			scheduler.addInitialTasks(ProtocolGraph[itask]["_task"])
		self.scheduler = scheduler

	def _generateFiles(self):
		'''Create input files here. This function must be implemented.'''
		# todo: Add profiling step for this
		raise Exception("Implement this function.")
	
	def _analyze(self):
		'''Run analysis here.'''
		raise Exception("Implement this function.")

class ddGK16Job(GenericddGJob):
	
	def _generateFiles(self):
		# Create input files
		self._write_lst(self._write_pdb())
		self._write_resfile()

	#def _name_constraints_file(self):
	#	self.parameters['CONSTRAINTS_FILE'] = self._workingdir_file_path("%(_FILE_ID)s.cst" % self.parameters)
	
	def _write_pdb(self):
		"""Import a pdb file from the database and write it to the temporary directory"""
		filename = self._workingdir_file_path("%(_FILE_ID)s.pdb" % self.parameters)
		F = open(filename, "w")
		F.write(self.parameters[ddgfields.StrippedPDB])
		F.close()
		return filename
		
	def _write_lst(self, pdbfilename):
		# Create lst file
		pdbfilename = self._workingdir_file_path("%(_FILE_ID)s.pdb" % self.parameters)
		filename = self._workingdir_file_path("%(_FILE_ID)s.lst" % self.parameters)
		F = open(filename, "w")
		F.write(pdbfilename)
		F.close()
		self.parameters['_CMD']['in:file:l'] = filename
		return filename

	def _write_resfile(self):
		"""create a resfile for the chains
			residues in interface: NATAA (conformation can be changed)
			residues mutation: PIKAA ADEFGHIKLMNPQRSTVWY (design sequence)"""
		
		resfile = self.parameters[ddgfields.InputFiles].get("RESFILE")
		if resfile:
			filename = self._workingdir_file_path("%(_FILE_ID)s.resfile" % self.parameters)
			F = open(filename, "w")
			F.write(resfile)
			F.close()
			self.parameters['_CMD']['resfile'] = filename
			return filename
		else:
			raise Exception("An error occurred creating a resfile for the ddG job.")

	def _analyze(self):
		# Run the analysis on the originating host
		
		try:
			Scores = {}
			
			ddGtask = self.ProtocolGraph["ddG"]["_task"] 
			ddGout = rosettahelper.readFileLines(ddGtask._workingdir_file_path(ddGtask.getExpectedOutputFileNames()[0]))
			self._status("examining ddg output:")
			ddGout = [l for l in ddGout if l.startswith("protocols.moves.ddGMover: mutate")]
			self._status(ddGout)
			assert(len(ddGout) == 1)
			ddGout = ddGout[0].strip()
			ddGregex = re.compile("^protocols.moves.ddGMover:\s*mutate\s*.*?\s*wildtype_dG\s*is:\s*.*?and\s*mutant_dG\s*is:\s*.*?\s*ddG\s*is:\s*(.*)$")
			mtchs = ddGregex.match(ddGout)
			assert(mtchs)
			Scores["ddG"] = float(mtchs.group(1))
			
			score_data = rosettahelper.readFileLines(ddGtask._workingdir_file_path("ddg_predictions.out"))
			score_data = [l for l in score_data if l.strip()]
			self._status("examining ddg_predictions.out:")
			assert(len(score_data) == 1) # Assuming only one line here
			score_data = score_data[0].split() 
			assert(len(score_data) > 2)
			assert(score_data[0] == "ddG:")
			scores = map(float, score_data[2:])
			Scores["components"] = scores
			
			self.ddG.setData(Scores)
			
			return True
		except Exception, e:
			errors = [str(e), traceback.format_exc()]
			self._status("<errors>\n\t<error>%s</error>\n</errors>" % join(errors,"</error>\n\t<error>"))
			return False

		return True
		#def parseResults(logfile, predictions_file):
		scoresHeader='''
	------------------------------------------------------------
	 Scores                       Weight   Raw Score Wghtd.Score
	------------------------------------------------------------'''
		scoresFooter = '''---------------------------------------------------'''
		
		F = open(logfile, "r")
		log = F.read()
		F.close()
		
		componentNames = []
		idx = log.find(scoresHeader)
		if idx:
			log = log[idx + len(scoresHeader):]
			idx = log.find(scoresFooter)
			if idx:
				log = log[:idx].strip()
				log = log.split("\n")
				for line in log:
					componentNames.append(line.strip().split()[0])
				componentNames.remove("atom_pair_constraint")
		
		F = open(predictions_file, "r")
		predictions = F.read().split('\n')
		F.close()
		results = {}
		for p in predictions:
			if p.strip():
				components = p.split()
				assert[components[0] == "ddG:"]
				mutation = components[1]
				score = components[2]
				components = components[3:]
				assert(len(components) == len(componentNames))
				results["Overall"] = score
				componentsd = {}
				for i in range(len(componentNames)):
					componentsd[componentNames[i]] = components[i]
				results["Components"] = componentsd
		return results

class ddGK16ddGTask(GenericDDGTask):
	pass

class ddGK16PreminTask(GenericDDGTask):

	def getOutputFilename(self, preminimizationLog):
		cmd = self.taskparameters["Command"]
		o = "-ddg::out_pdb_prefix"
		i = cmd.find(o)
		if i != -1: 
			prefix = cmd[i + len(o):].strip().split(" ")[0]
		
		if prefix:
			pdbfilepaths = []
			outputLines = rosettahelper.readFileLines(preminimizationLog)
			str = "examining file:"
			for line in outputLines: 
				if line.startswith(str):
					pdbfilepaths.append(line[len(str):].strip().split()[0])
			
			# todo: The following assumes that the lst file contains only one PDB file which will probably work better in practice w.r.t. running parallel jobs
			if pdbfilepaths:
				fdir, fname = os.path.split(pdbfilepaths[0])
				fname = fname.split(".")[0]
				return os.path.join(fdir, "%(prefix)s.%(fname)s_0001.pdb" % vars())
			else:
				raise Exception("Could not find the input PDB file paths in the log.")
		else:
			raise Exception("Could not determine the out_pdb_prefix of the command.")

	def createConstraintsFile(self, preminimizationLog, outfilepath):
		'''This does the work of convert_to_cst_file.sh'''
		self._status("Creating constraints file")
		constraints = []
		outputLines = rosettahelper.readFileLines(preminimizationLog)
		for line in outputLines: 
			if line.startswith("c-alpha"):
				line = line.split()
				constraints.append("AtomPair CA %s CA %s HARMONIC %s %s" % (line[5], line[7], line[9], line[12]))
		rosettahelper.writeFile(outfilepath, join(constraints, "\n"))

	def retire(self):
		passed = super(ddGK16PreminTask, self).retire()
		try:
			# todo: Expecting only one output file
			stdoutfile = self._workingdir_file_path(self.getExpectedOutputFileNames()[0])
			
			# Set the input PDB filename for the ddG step
			self.setOutput("in:file:s", self._workingdir_file_path(self.getOutputFilename(stdoutfile)), taskID = "ddG")
			
			# Create the constraints file
			cstfile = self._workingdir_file_path("constraints.cst")
			constraints = self.createConstraintsFile(stdoutfile, cstfile)
			self.setOutput("constraints::cst_file", cstfile, taskID = "ddG")
			self._status("Set outputs: %s" % self.outputs)
			# Check whether files were created (and write the total scores to a file)
			# Copy the files from the cluster submission host back to the originating host
			#self._status('Copying pdb, gz, and resfiles back')
			#self._copyFilesBackToHost(["*.pdb", "*.gz", "*.resfile"])
		except Exception, e:
			passed = False
			self.state = FAILED_TASK
			errors = [str(e), traceback.format_exc()]
			self._status("<errors>\n\t<error>%s</error>\n</errors>" % join(errors,"</error>\n\t<error>"))
		  
		return passed


	
	