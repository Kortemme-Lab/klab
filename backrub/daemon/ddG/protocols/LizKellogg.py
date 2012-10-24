#!/usr/bin/python2.4
# encoding: utf-8
"""
LizKellogg.py
Classes to run jobs based on a paper by Elizabeth H. Kellogg, Andrew Leaver-Fay, and David Baker (doi: 10.1002/prot.22921).

Created by Shane O'Connor 2012.
Copyright (c) 2012 __UCSF__. All rights reserved.
"""

import os
import re
import traceback
from string import join
import rosettahelper
from ddG.jobs import GenericDDGJob, GenericDDGTask
from ClusterTask import FAILED_TASK

# Jobs and tasks for specific protocols

class Protocol16(GenericDDGJob):
	
	def _generateFiles(self, jobID):
		'''Creates input files.'''
		jobParameters = self.parameters["jobs"][jobID]
		
		# Create PDB file
		pdb_filename = self._workingdir_file_path("%(_FILE_ID)s.pdb" % jobParameters, jobID = jobID)
		rosettahelper.writeFile(pdb_filename, jobParameters["StrippedPDB"])

		# Create lst
		lst_filename = self._workingdir_file_path("%(_FILE_ID)s.lst" % jobParameters, jobID = jobID)
		rosettahelper.writeFile(lst_filename, pdb_filename)
		jobParameters['_CMD']['in:file:l'] = lst_filename
		
		# Create resfile
		resfile = jobParameters["InputFiles"].get("RESFILE")
		if resfile:
			res_filename = self._workingdir_file_path("%(_FILE_ID)s.resfile" % jobParameters, jobID = jobID)
			rosettahelper.writeFile(res_filename, resfile)
			jobParameters['_CMD']['resfile'] = res_filename
		
	def _analyze(self):
		# Run the analysis on the originating host
		
		wasSuccessful = True

		for i in range(len(self.jobIDs)):
			jobID = self.jobIDs[i]
			try:
				Scores = {}
				
				ddGtask = self.ProtocolGraph["ddG"]["_task"] 
				ddGout = rosettahelper.readFileLines(ddGtask._workingdir_file_path(ddGtask.getExpectedOutputFileNames()[i], jobID))
				self._status("Examining ddg output for DB job %s:" % str(jobID), level = 0)
				ddGout = [l for l in ddGout if l.strip() and l.startswith("protocols.moves.ddGMover: mutate")]
				self._status(join(ddGout, "\n"))
				assert(len(ddGout) == 1)
				ddGout = ddGout[0].strip()
				ddGregex = re.compile("^protocols.moves.ddGMover:\s*mutate\s*.*?\s*wildtype_dG\s*is:\s*.*?and\s*mutant_dG\s*is:\s*.*?\s*ddG\s*is:\s*(.*)$")
				mtchs = ddGregex.match(ddGout)
				assert(mtchs)
				Scores["ddG"] = float(mtchs.group(1))
				
				score_data = rosettahelper.readFileLines(ddGtask._workingdir_file_path("ddg_predictions.out", jobID))
				score_data = [l for l in score_data if l.strip()]
				self._status("examining ddg_predictions.out:", level = 5)
				assert(len(score_data) == 1) # Assuming only one line here
				score_data = score_data[0].split() 
				assert(len(score_data) > 2)
				assert(score_data[0] == "ddG:")
				scores = map(float, score_data[2:])
				Scores["components"] = scores
				self.ddG[jobID].setData(Scores)
		
			except Exception, e:
				self.failedIDs.append(jobID)
				errors = [str(e), traceback.format_exc()]
				self._status("<errors>\n\t<error>%s</error>\n</errors>" % join(errors,"</error>\n\t<error>"))
				wasSuccessful = False
		
		return wasSuccessful	

class Protocol16Preminimization(GenericDDGTask):

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
		passed = super(Protocol16Preminimization, self).retire()
		for i in range(len(self.jobIDs)):
			jobID = self.jobIDs[i]
			try:
				# self.jobIDs is sorted so we can rely on the indexing of getExpectedOutputFileNames
				stdoutfile = self._workingdir_file_path(self.getExpectedOutputFileNames()[i], jobID)
				
				# Set the input PDB filename for the ddG step
				self.setOutput(jobID, "in:file:s", self._workingdir_file_path(self.getOutputFilename(stdoutfile), jobID), taskID = "ddG")
				
				# Create the constraints file
				cstfile = self._workingdir_file_path("constraints.cst", jobID)
				constraints = self.createConstraintsFile(stdoutfile, cstfile)
				self.setOutput(jobID, "constraints::cst_file", cstfile, taskID = "ddG")
				self._status("Set outputs: %s" % self.outputs, level = 5)
				
			except Exception, e:
				passed = False
				self.state = FAILED_TASK
				errors = [str(e), traceback.format_exc()]
				self._status("<errors>\n\t<error>%s</error>\n</errors>" % join(errors,"</error>\n\t<error>"))
		  
		return passed