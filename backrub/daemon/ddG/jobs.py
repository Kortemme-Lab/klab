#!/usr/bin/python2.4
# encoding: utf-8
"""
jobs.py

Created by Shane O'Connor 2012.
Copyright (c) 2012 __UCSF__. All rights reserved.
"""

import os
import re
import shutil
import glob
from string import join, split
import fnmatch
from conf_daemon import *
from ClusterScheduler import checkGraphReachability, traverseGraph, TaskSchedulerException, SchedulerTaskAddedAfterStartException, BadSchedulerException, TaskCompletionException, SchedulerDeadlockException, SchedulerStartException
from ClusterScheduler import TaskScheduler, RosettaClusterJob, ClusterBatchJob
from RosettaTasks import PostProcessingException
import ddglib.ddgdbapi as ddgdbapi
from conf_daemon import CLUSTER_maxhoursforjob, CLUSTER_maxminsforjob, clusterRootDir
import SimpleProfiler
from ClusterTask import INITIAL_TASK, INACTIVE_TASK, QUEUED_TASK, ACTIVE_TASK, RETIRED_TASK, COMPLETED_TASK, FAILED_TASK, status
from ClusterTask import ClusterScript, ClusterTask
from rosettahelper import make755Directory, makeTemp755Directory, writeFile, permissions755, permissions775, normalize_for_bash
import ddG
from ddglib.score import ddgTestScore
ddgfields = ddgdbapi.FieldNames()

# Generic classes

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

class GenericDDGTask(ClusterTask):

	# additional attributes
	
	def __init__(self, workingdir, targetdirectory, jobparameters, taskparameters, name="", prefix = "ddG"):
		self.prefix = prefix
		self.taskparameters = taskparameters
		self.inputs = {}
		self.outputs = {}
		self.taskglobals = {"BIN_DIR" : taskparameters["ToolVersion"], "DATABASE_DIR" : taskparameters["DBToolVersion"]}
		for jobID in jobparameters["jobs"].keys():
			self.inputs[jobID] = {}
			self.outputs[jobID] = {}
		
		scriptfilename = '%s_%s.cmd' % (self.prefix, jobparameters["ID"])
		self.sgec = None
		self.profiler = SimpleProfiler.SimpleProfiler(name)
		self.profiler.PROFILE_START("Initialization")
		self.parameters = jobparameters
		self.failOnStdErr = True
		self.debug = True
		self.targetdirectory = targetdirectory
		self.jobid = 0
		self._setStatusPrintingParameters(self.jobid, "task", level = 0, color = "purple")
		self.script = None
		self.state = INACTIVE_TASK
		self.dependents = []
		self.prerequisites = {}
		self.workingdir = workingdir
		# Do not allow spaces in the script filename so that the SGE qstat parsing works
		scriptfilename.replace(" ", "_")
		self.scriptfilename = scriptfilename
		self.shortname = split(scriptfilename, "_")[0] # todo: do this better
		self.filename = os.path.join(workingdir, scriptfilename)
		self.cleanedup = False
		self.name = name or "unnamed"
		self.jobIDs = sorted(jobparameters["jobs"].keys()) # The fact that this is a sorted list is important
		self.numtasks = len(self.jobIDs)
		self.outputstreams = []
		self._initialize()
		self.profiler.PROFILE_STOP("Initialization")
		self.cleaners = []
	
	def addInputs(self, jobID, inpts):
		self._status("Adding inputs: %s for job %d" % (inpts, jobID), level = 4)
		for k, v in inpts.iteritems():
			if self.inputs[jobID].get(k):
				raise Exception("Overwriting task input %s (old value = %s, attempted new value = %s)", (k, self.inputs[jobID][k], v))
			self.inputs[jobID][k] = v
		
	def addOutputs(self, jobID, outputs):
		self.outputs[jobID] = outputs
	
	def getOutputs(self, jobID, taskref):
		self._status("Asking for outputs for %s for job %d" % (str(taskref), jobID), level = 4)
		for taskRefandIDPair, params in self.outputs[jobID].iteritems():
			if taskRefandIDPair[0] == taskref:
				self._status("Found a match: %s" % params, level = 10)
				return params
		self._status("No match for you! Come back, one year!")
		return {}			
		
	def setOutput(self, jobID, key, val, taskID = None):
		outputs = self.outputs[jobID]
		if taskID:
			# Set the value for a specific task based on the StepID field of the ProtocolStep table
			for taskRefandIDPair, params in outputs.iteritems():
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
		
	def start(self, sgec, dbID):
		# Create script
		self._status("Preparing %s" % self.name)
		
		input_strings = {}
		commandLines = self.taskparameters["Command"]
		for jobID, inputs in sorted(self.inputs.iteritems()):
			for input in inputs:
				commandLines = commandLines.replace("%(" + input + ")s", "$" + normalize_for_bash(input) + "var")
			break
		commandLines = commandLines.split("\n")
		
		normalized_inputs = {} # These are used in bash scripts so we need to remove any special characters
		for jobID, inputs in sorted(self.inputs.iteritems()):
			job_inputs = {}
			for k, v in inputs.iteritems():
				if not v:
					errstr = "The input parameter %s has not been specified for job %d." % (k, jobID)
					self._status(errstr)
					raise Exception(errstr)
				job_inputs[normalize_for_bash(k)] = v
				norm_key = normalize_for_bash(k)
				normalized_inputs[norm_key] = normalized_inputs.get(norm_key, {})
				normalized_inputs[norm_key][jobID] = v
			#normalized_inputs[jobID] = job_inputs
			if len(job_inputs) != len(inputs):
				raise Exception("The keys %s in the parameters are not unique after normalization (%s)." % (input.keys(), job_inputs.keys()))
		
		ct = ddGClusterScript(self.workingdir, self.targetdirectory, self.taskglobals, normalized_inputs, self.numtasks, self.jobIDs)
		self.script = ct.createScript(commandLines, type="ddG")
		self.runlength = ct.parameters["maxhours"] * 60 + ct.parameters["maxmins"]
			
		return super(GenericDDGTask, self).start(sgec, dbID)

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
			self._status("Creating %s" % self.targetdirectory, level = 10)
			make755Directory(self.targetdirectory)

		for jobID in self.jobIDs:
			jobDir = os.path.join(self.targetdirectory, str(jobID))
			if not os.path.isdir(jobDir):
				make755Directory(jobDir)

		if self.scriptfilename:
			failedOutput = False
			self._status('Copying stdout and stderr output to %s' % (self.targetdirectory), level = 5)		
			try:
				for i in range(1, self.numtasks + 1):
					
					jobID = str(self.jobIDs[i - 1])
					workingJobSubDir = os.path.normpath(os.path.join(self.workingdir, jobID))
					targetJobSubDir = os.path.normpath(os.path.join(self.targetdirectory, jobID))
					
					# Move the SGE script and delete the temp file
					sge_scriptfile = self._workingdir_file_path(self.scriptfilename)
					if i == 1:
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
					
					for cleaner in self.cleaners:
						#todo: factor in taskdetails["DirectoryName"] here when it becomes an issue
						if cleaner["operation"] == "keep":
							mask = cleaner["mask"]
							self._status("Cleaner (keep): Moving files from %s to %s using mask '%s'.\n" % (workingJobSubDir, targetJobSubDir, mask), level = 10)
							for file in os.listdir(workingJobSubDir):
								if fnmatch.fnmatch(file, mask):
									try:
										shutil.copy(os.path.join(workingJobSubDir, file), targetJobSubDir)
									except Exception, e:
										self._status("Exception moving %s to %s: %s" % (os.path.join(fromSubdirectory, file), toSubdirectory, str(e)))
								 
			except Exception, e:
				self._status("Exception: %s" % str(e))
			
			return not failedOutput
		else:
			self.state = FAILED_TASK
			return False
		
	def copyFiles(self, targetdirectory, filemasks = ["*"]):
		for mask in filemasks:
			for jobID in self.jobIDs:
				jobID = str(jobID)
				tdir = os.path.join(targetdirectory, jobID)
				self._status('Copying %s/%s/%s to %s' % (self.workingdir, jobID, mask, tdir), level = 10)
				if not os.path.isdir(tdir):
					self._status("Creating %s" % self.targetdirectory, level = 10)
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
				self._status('Copying %s/%s to %s' % (self.workingdir, p, tdir), level = 10)
				if not os.path.isdir(tdir):
					self._status("Creating %s" % self.targetdirectory, level = 10)
					make755Directory(tdir)
				for file in glob.glob(self._workingdir_file_path(p)):
					shutil.copy(file, tdir)	
		
class GenericDDGJob(ClusterBatchJob):

	suffix = "ddG"
	flatOutputDirectory = True
	name = "ddG"

	def _defineOutputFiles(self):
		self.resultFilemasks.append((".", "*"))
		
	def getddG(self, jobID):
		return self.ddG[jobID].getScores()

	def __init__(self, sgec, parameters, tempdir, targetroot, dldir, testonly = False):
		# The tempdir is the one on the submission host e.g. chef
		# targetdirectory is the one on your host e.g. your PC or the webserver
		# The taskdirs are subdirectories of the tempdir on the submission host and the working directories for the tasks
		# The targetdirectories of the tasks are subdirectories of the targetdirectory named like the taskdirs
		jobs = sorted(parameters["jobs"].keys())
		self.ddG = {}
		for job in jobs:
			self.ddG[job] = ddgTestScore()
		if len(jobs) > 1:
			parameters["ID"] = "%d-%d" % (jobs[0], jobs[-1])
		else:
			parameters["ID"] = jobs[0]
		super(GenericDDGJob, self).__init__(sgec, parameters, tempdir, targetroot, dldir, testonly)
		
			
	def _initialize(self):
		parameters = self.parameters
		
		ProtocolGraph = parameters["ProtocolGraph"]
		for taskID, taskdetails in ProtocolGraph.iteritems():
			if taskdetails["ToolVersion"][0] != "r":
				taskdetails["ToolVersion"] = "r%s" % taskdetails["ToolVersion"]
			if taskdetails["DBToolVersion"][0] != "r":
				taskdetails["DBToolVersion"] = "r%s" % taskdetails["DBToolVersion"]
		
		for jobid, jobparams in parameters["jobs"].iteritems():
			jobparams['_CMD'] = {} # This stores task parameters set up by the Job. The keys must have unique names per task if different values are required for each task.
			jobparams['_FILE_ID'] = "%s-%s" % (jobparams[ddgfields.ExperimentID], jobparams[ddgfields.PDB_ID])
		
		# Create files
		self.describe()
		try:
			jobID = None
			for jobID in self.jobIDs:
				self._generateFiles(jobID)
		except Exception, e:
			estr = str(e) + "\n" + traceback.format_exc()
			raise Exception("An error occurred creating the files for the ddG job %(jobID)s.\n%(estr)s" % vars())
			
		# Create tasks from the protocol steps
		tasks = {}
		ProtocolGraph = parameters["ProtocolGraph"]
		for taskID, taskdetails in ProtocolGraph.iteritems():
			taskcls = taskdetails["ClassName"] or "GenericDDGTask"
			#taskcls = taskcls.split(".")[-1] # todo : remove this step later when everything is separated into modules
			m_parts = taskcls.split(".")
			taskcls = globals()[m_parts[0]]
			for i in range(1, len(m_parts)):
				taskcls = getattr(taskcls, m_parts[i])
			#taskcls = globals()[taskcls]
			targetsubdirectory = taskdetails["DirectoryName"] or "."
			taskdir = self._make_taskdir(targetsubdirectory)
			taskdetails["_task"] = taskcls(taskdir, self.targetdirectory, parameters, taskdetails, name=taskdetails["ProtocolStepID"], prefix=taskdetails["ProtocolStepID"])
		
		# Define the input and output parameters
		for jobid, jobparams in parameters["jobs"].iteritems():
			for taskID, taskdetails in ProtocolGraph.iteritems():
				task_inputs = {}
				task_outputs = {}
				stepID = taskdetails["ProtocolStepID"]
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
							jobparam = jobparams['_CMD'].get(cmdparam[0])
							if jobparam and cmdparam[1]:
								raise Exception("Task #%d: %s is defined by both the Job and the database entry." % (stepID, cmdparam[0]))
							elif not(jobparam or cmdparam[1]) and tpl[0] == None: # Allow null values to be filled in by parent tasks
								raise Exception("Task #%d: %s is undefined." % (stepID, cmdparam[0]))
							else:
								task_inputs[cmdparam[0]] = cmdparam[1] or jobparam
				ProtocolGraph[stepID]["_task"].addInputs(jobid, task_inputs)
				ProtocolGraph[stepID]["_task"].addOutputs(jobid, task_outputs)
				ProtocolGraph[stepID]["_task"].cleaners = ProtocolGraph[stepID]["Cleaners"]
				
		
		self.ProtocolGraph = ProtocolGraph
				 
		# Create a scheduler from the protocol graph
		scheduler = TaskScheduler(self.workingdir) 
		for taskID, taskdetails in ProtocolGraph.iteritems():
			for p in taskdetails["Parents"]:
				taskdetails["_task"].addPrerequisite(ProtocolGraph[p]["_task"])
		for itask in parameters["InitialTasks"]:
			scheduler.addInitialTasks(ProtocolGraph[itask]["_task"])
		self.scheduler = scheduler

	def _generateFiles(self, jobID):
		'''Create input files here. This function must be implemented.'''
		# todo: Add profiling step for this
		raise Exception("Implement this function.")
	
	def _analyze(self):
		'''Run analysis here.'''
		raise Exception("Implement this function.")
	

