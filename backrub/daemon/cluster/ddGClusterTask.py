#!/usr/bin/python2.4
# encoding: utf-8
"""
ddGClusterTask.py

Created by Shane O'Connor 2012.
Copyright (c) 2012 __UCSF__. All rights reserved.
"""


import sys
import os
import time
import shutil
import tempfile
import re
import glob
from string import join, split
import traceback
from datetime import datetime

from conf_daemon import *
import SimpleProfiler
#import sge
from rosettahelper import make755Directory, makeTemp755Directory, writeFile
from RosettaProtocols import *

from ClusterTask import INITIAL_TASK, INACTIVE_TASK, QUEUED_TASK, ACTIVE_TASK, RETIRED_TASK, COMPLETED_TASK, FAILED_TASK, status
from ClusterTask import ClusterScript, ClusterTask

class ddGClusterScript(ClusterScript):
	
	def __init__(self, workingdir, targetdirectory, taskglobals, taskparameters, numtasks, jobIDs, maxhours = CLUSTER_maxhoursforjob, maxmins = CLUSTER_maxminsforjob):
		self.contents = []
		self.tasks = []
		self.parameters = {"workingdir": workingdir, "targetdirectory" : targetdirectory, "taskline": "", "taskparam" : "", "taskvar" : "", "maxhours": maxhours, "maxmins": maxmins}
		
		arrayname = "jobIDs"
		jobIDs = sorted(jobIDs)
		self.parameters["taskline"] += "%s=( dummy %s )\n" % (arrayname, join(map(str, jobIDs), " "))
		self.parameters["taskvar"]  += '%svar=${%s[$SGE_TASK_ID]}\n' % (arrayname, arrayname)	 
		
		if taskparameters:
			assert(not(taskparameters.get("jobIDs")))
			for arrayname, parametersbyjobid in sorted(taskparameters.iteritems()):
				sortedkeys = sorted(parametersbyjobid.keys())
				assert(jobIDs == sortedkeys) 
				contents = [parametersbyjobid[k] for k in sortedkeys]
				self.parameters["taskline"] += "%s=( dummy %s )\n" % (arrayname, join(contents, " "))
				self.parameters["taskvar"]  += '%svar=${%s[$SGE_TASK_ID]}\n' % (arrayname, arrayname)
		self.parameters["taskparam"] = "#$ -t 1-%d" % numtasks #len(tasks)
		taskglobals["BIN_DIR"] = os.path.join(clusterRootDir, taskglobals["BIN_DIR"]) 
		self.revision = taskglobals["BIN_DIR"]
		self.bindir = os.path.join(clusterRootDir, self.revision)
		taskglobals["DATABASE_DIR"] = os.path.join(clusterRootDir, taskglobals["DATABASE_DIR"], "rosetta_database") 
		self.taskglobals = taskglobals
		self.dbrevision = taskglobals["DATABASE_DIR"]
		self.databasedir = os.path.join(clusterRootDir, self.dbrevision)
		self.workingdir = workingdir
		self.script = None
		self.taskparameters = taskparameters

	def _addTask(self, lines, type, attributes):
		attstring = ""
		if attributes:
			for k,v in attributes:
				attstring += '%s = "%s" ' % (k, v)
		if attstring:
			attstring = " " + attstring	   
		if type:
			self.contents.append('echo -n "<%s%s"' % (type, attstring))
			self.contents.append('if [ -n "${SGE_TASK_ID+x}" ]; then')
			self.contents.append('echo -n " \\"subtask=$SGE_TASK_ID\\"" ')
			self.contents.append('fi')
			self.contents.append('echo ">"')
		
		lines = ['cd %s' % self.workingdir, 'cd $jobIDsvar'] + lines
		
		content = join(lines, "\n")
		#for taskglobal, value in self.taskglobals.iteritems():
		#	content.replace("%%(%s)s" % taskglobal, value)
		self.contents.append(content % self.taskglobals)
		
		if type:
			self.contents.append('echo "</%s>"\n' % type)
	
class ddGClusterTask(ClusterTask):	
	# SGE-Queued jobs have a non-zero jobid and a state of QUEUED_TASK
	# SGE-Running jobs have a non-zero jobid and a state of ACTIVE_TASK
	def __init__(self, workingdir, targetdirectory, scriptfilename, parameters = {}, name = ""):
		self.sgec = None
		self.profiler = SimpleProfiler.SimpleProfiler(name)
		self.profiler.PROFILE_START("Initialization")
		self.parameters = parameters
		self.failOnStdErr = True
		self.debug = True
		self.targetdirectory = targetdirectory
		self.jobid = 0
		self.script = None
		self.state = INACTIVE_TASK
		self.dependents = []
		self.prerequisites = {}
		self.workingdir = workingdir
		# Do not allow spaces in the script filename so that the SGE qstat parsing works
		scriptfilename.replace(" ", "_")
		self.scriptfilename = scriptfilename
		self.shortname = split(scriptfilename, ".")[0] # todo: do this better
		self.shortname = split(scriptfilename, "_")[0] # todo: do this better
		self.filename = os.path.join(workingdir, scriptfilename)
		self.cleanedup = False
		self.name = name or "unnamed"
		self.jobIDs = sorted(parameters["jobs"].keys()) # The fact that this is a sorted list is important
		self.numtasks = len(self.jobIDs)
		self.outputstreams = []
		self._initialize()
		self.profiler.PROFILE_STOP("Initialization")

	def copyFiles(self, targetdirectory, filemasks = ["*"]):
		for mask in filemasks:
			for jobID in self.jobIDs:
				jobID = str(jobID)
				tdir = os.path.join(targetdirectory, jobID)
				self._status('Copying %s/%s/%s to %s' % (self.workingdir, jobID, mask, tdir))
				if not os.path.isdir(tdir):
					self._status("Creating %s" % self.targetdirectory)
					make755Directory(tdir)
				for file in glob.glob(self._workingdir_file_path(mask, jobID)):
					shutil.copy(file, tdir)
		
	def _copyFilesBackToHost(self, filemasks = ["*"]):
		if type(filemasks) == type(""):
			filemasks = [filemasks]
		for p in filemasks:
			for jobID in self.jobIDs:
				jobID = str(jobID)
				tdir = os.path.join(targetdirectory, jobID)
				self._status('Copying %s/%s to %s' % (self.workingdir, p, tdir))
				if not os.path.isdir(tdir):
					self._status("Creating %s" % self.targetdirectory)
					make755Directory(tdir)
				for file in glob.glob(self._workingdir_file_path(p)):
					shutil.copy(file, tdir)	
		
	def retire(self):
		""" This is the place to implement any interim postprocessing steps for your task to generate input the dependents require (Pay it forward).
			All necessary input files for dependents should be copied back to the originating host here. 
			e.g.  -check if all files were created
				  -execute analysis
				  -optionally get rid of unused files
				  -copy any files needed for dependent steps back to the originating host.
			By default, this function creates a target directory on the host and copies all stdout and stderr files to it.
			If any of the stderr files have non-zero size, the default behaviour is to mark the task as failed."""
		
		self._status("Retiring %s" % self.name)
		
		if not os.path.isdir(self.targetdirectory):
			# The root of self.targetdirectory should exists - otherwise we should not
			# create the tree here as there is probably a bug in the code
			self._status("Creating %s" % self.targetdirectory)
			make755Directory(self.targetdirectory)

		for jobID in self.jobIDs:
			jobDir = os.path.join(self.targetdirectory, str(jobID))
			if not os.path.isdir(jobDir):
				make755Directory(jobDir)
		
		clusterScript = self._workingdir_file_path(self.scriptfilename)
		if os.path.exists(clusterScript):
			shutil.copy(clusterScript, self.targetdirectory)
					
		if self.scriptfilename:
			failedOutput = False
			self._status('Copying stdout and stderr output to %s' % (self.targetdirectory))		
			try:
				for i in range(1, self.numtasks + 1):
					
					jobID = str(self.jobIDs[i - 1])
					workingJobSubDir = os.path.normpath(os.path.join(self.workingdir, jobID))
					targetJobSubDir = os.path.normpath(os.path.join(self.targetdirectory, jobID))
					
					# Move the SGE script and delete the temp file
					sge_scriptfile = self._workingdir_file_path(self.scriptfilename)
					shutil.copy(sge_scriptfile, targetJobSubDir)
					shutil.move(sge_scriptfile, workingJobSubDir)
					sge_scriptfile_temp = sge_scriptfile + ".temp.out"
					if os.path.exists(sge_scriptfile_temp):
						os.remove(sge_scriptfile_temp)
						
					filename_stdout = "%s.o%s.%d" % (self.scriptfilename, self.jobid, i)
					filename_stderr = "%s.e%s.%d" % (self.scriptfilename, self.jobid, i)
					stdoutfile = self._workingdir_file_path(filename_stdout)
					if os.path.exists(stdoutfile):
						shutil.copy(stdoutfile, targetJobSubDir)
						shutil.move(stdoutfile, workingJobSubDir)
					else:
						self._status("Failed on %s, subtask %d. No stdout file %s." % (self.name, i, stdoutfile))
						filename_stdout = None
						failedOutput = True
					
					stderrfile = self._workingdir_file_path(filename_stderr)
					stderrHasFailed = False
					if os.path.exists(stderrfile):					
						stderrHasFailed = os.path.getsize(stderrfile) > 0
						if not stderrHasFailed:
							os.remove(stderrfile)
						elif self.failOnStdErr:
							shutil.copy(stderrfile, targetJobSubDir)
							shutil.move(stderrfile, workingJobSubDir)
							self._status("Failed on %s, subtask %d. stderr file %s has size %d" % (self.name, i, stderrfile, stderrHasFailed))
							self.state = FAILED_TASK
							failedOutput = True
					else:
						self._status("Failed on %s, subtask %d. No stderr file %s." % (self.name, i, stderrfile))
						filename_stderr = None
						failedOutput = True
					if stderrHasFailed:
						self.outputstreams.append({"stdout" : filename_stdout, "stderr" : filename_stderr})
					else:
						self.outputstreams.append({"stdout" : filename_stdout})
			except Exception, e:
				self._status("Exception: %s" % str(e))
			
			return not failedOutput
		else:
			self.state = FAILED_TASK
			return False

