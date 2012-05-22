#!/usr/bin/python2.4
# encoding: utf-8
"""
jobs.py

Created by Shane O'Connor 2012.
KIC code adapted from code written by Roland A. Pache, Ph.D., Copyright (c) 2011, 2012.
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
from conf_daemon import CLUSTER_maxhoursforjob, CLUSTER_maxminsforjob, clusterRootDir
import SimpleProfiler
from ClusterTask import INITIAL_TASK, INACTIVE_TASK, QUEUED_TASK, ACTIVE_TASK, RETIRED_TASK, COMPLETED_TASK, FAILED_TASK, status
from ClusterTask import ClusterScript, ClusterTask
from rosettahelper import make755Directory, makeTemp755Directory, writeFile, permissions755, permissions775, normalize_for_bash
import time
import datetime
import pickle

strftime = datetime.datetime.strftime
def strptime(date_string, format):
	'''For 2.4.3 compatibility'''
	return datetime.datetime(*(time.strptime(date_string, format)[0:6]))

# Generic classes

class benchmarkClusterScript(ClusterScript):
	
	def __init__(self, workingdir, targetdirectory, taskparameters, benchmarksettings, numtasks, firsttaskindex = 1, dataarrays = {}, benchmark_name = ""):
		self.contents = []
		self.tasks = []
		self.parameters = {
			"workingdir": workingdir,
			"targetdirectory" : targetdirectory,
			"taskline": "",
			"taskparam" : "",
			"taskvar" : "",
			"benchmark_name" : "%s_Scientific_Benchmark" % benchmark_name,
			"ClusterQueue" : taskparameters['ClusterQueue'],
			"ClusterArchitecture" : taskparameters['ClusterArchitecture'],
			"ClusterMemoryRequirementInMB" : int(taskparameters['ClusterMemoryRequirementInGB'] * 1024),
			"ClusterWalltime" : "%02d:%02d:00" % (int(taskparameters["ClusterWalltimeLimitInMinutes"] / 60), taskparameters["ClusterWalltimeLimitInMinutes"] % 60),
		}
		
		if numtasks > 0:
			if dataarrays:
				for arrayname, contents in sorted(dataarrays.iteritems()):
					self.parameters["taskline"] += "%s=( dummy %s )\n" % (arrayname, join(contents, " "))
					self.parameters["taskvar"]  += '%svar=${%s[$SGE_TASK_ID]}\n' % (arrayname, arrayname)	 
			self.parameters["taskparam"] = "#$ -t %d-%d" % (firsttaskindex, firsttaskindex + numtasks - 1) 
		
		bin_revision = "r%s" % int(taskparameters["RosettaSVNRevision"])
		self.revision = bin_revision
		self.bindir = os.path.join(clusterRootDir, bin_revision)
		db_revision = "r%s" % int(taskparameters["RosettaDBSVNRevision"])
		self.databasedir = os.path.join(clusterRootDir, db_revision)
		missing_dirs = []
		if not os.path.exists(self.bindir):
			missing_dirs.append(self.bindir)
		if not os.path.exists(self.databasedir):
			missing_dirs.append(self.databasedir)
		if missing_dirs:
			raise Exception("The required Rosetta directories %s are missing." % join(missing_dirs, " and "))
		benchmark_binary = self.getBinary(benchmarksettings.rosetta_executable)
		if not os.path.exists(benchmark_binary):
			raise Exception("The required Rosetta binary %s is missing." % benchmark_binary)
			
		 
		self.workingdir = workingdir
		self.script = None
		self.taskparameters = taskparameters

	def _addPreamble(self):

		self.contents.insert(0, """\
#!/bin/bash
#
#$ -N %(benchmark_name)s
#$ -S /bin/bash
#$ -o %(workingdir)s
#$ -e %(workingdir)s
#$ -cwd
#$ -r y
#$ -j n
#$ -q %(ClusterQueue)s
#$ -l arch=%(ClusterArchitecture)s
#$ -l mem_free=%(ClusterMemoryRequirementInMB)sM
#$ -l netapp=1G,scratch=1G,mem_total=3G
#$ -l h_rt=%(ClusterWalltime)s
		
%(taskparam)s
%(taskline)s
%(taskvar)s
echo off

echo "<startdate>"
date
echo "</startdate>"
echo "<host>"
hostname
echo "</host>"
echo "<cwd>"
pwd
echo "</cwd>"

echo "<arch>"
uname -i
echo "</arch>"

echo "<taskid>"
echo "- $SGE_TASK_ID -"
echo "</taskid>"

# 4-character (zero padded) counter
if [ "$SGE_TASK_ID" != "undefined" ]; then SGE_TASK_ID4=`printf %%04d $SGE_TASK_ID`; fi
""" % self.parameters)

		

class GenericBenchmarkJob(RosettaClusterJob):
	
	def __init__(self, sgec, parameters, benchmarksettings, tempdir, targetroot, dldir, testonly = False):
		self.results = None
		parameters["BenchmarkOptions"] = pickle.loads(parameters["BenchmarkOptions"])
		self.benchmarksettings = benchmarksettings
		super(GenericBenchmarkJob, self).__init__(sgec, parameters, tempdir, targetroot, dldir, testonly, jobsubdir = str(parameters["ID"]))
	
	def getResults(self):
		raise Exception("Implement this method")
	
class KICBenchmarkTask(ClusterTask):

	# additional attributes
	benchmark_name = "KIC"
	prefix = "KICBenchmark"
	input_time_format = "%a %b %d %H:%M:%S %Z %Y"

	def __init__(self, workingdir, targetdirectory, parameters, benchmarksettings, input_pdb, loop_file, pdb_prefix, numtasks, firsttaskindex, name = ""):
		'''Note: firsttaskindex is 1-based to conform the SGE's task IDs. If your array is 0-based you will need to add 1 to the firsttaskindex when creating the ClusterTask.'''  
		self.benchmarksettings = benchmarksettings
		self.input_pdb = input_pdb
		self.loop_file = loop_file
		self.pdb_prefix = pdb_prefix
		super(KICBenchmarkTask, self).__init__(workingdir, targetdirectory, '%s_%d.cmd' % (self.prefix, parameters["ID"]), parameters, name, numtasks = numtasks, firsttaskindex = firsttaskindex)		  
	
	def _initialize(self):
		parameters = self.parameters
		benchmarksettings = self.benchmarksettings
				
		# Create working directory paths
		for i in range(self.firsttaskindex, self.firsttaskindex + self.numtasks):
			make755Directory(self._workingdir_file_path(str(i)))

		# Create script
		ct = benchmarkClusterScript(self.workingdir, self.targetdirectory, parameters, benchmarksettings, self.numtasks, self.firsttaskindex, benchmark_name = self.benchmark_name)
	
		# Setup command
		commandLineParams = {
			"loops:input_pdb" : self.input_pdb,
			"loops:loop_file" : self.loop_file,
			"in:file:native" : self.input_pdb,
			"out:prefix" : self.pdb_prefix,
			"loops:max_kic_build_attempts" : parameters["BenchmarkOptions"]["MaxKICBuildAttempts"],
		}
		kicCommand = [
			ct.getBinary(benchmarksettings.rosetta_executable),
			"-database %s" % ct.getDatabaseDir(),
			self.parameters["CommandLine"] % commandLineParams
			#"-loops:input_pdb %s" % self.input_pdb,
			#"-in:file:fullatom",
			#"#-loops:loop_file %s" % self.loop_file,
			#"-loops:remodel perturb_kic",
			#"-loops:refine refine_kic",
			#"-in:file:native %s" % self.input_pdb,
			#"-out:prefix %s" % self.pdb_prefix,
			#"-overwrite",
			#"-out:path $SGE_TASK_ID/",
			#"-ex1", "-ex2",
			#"-nstruct 1",
			#"-out:pdb_gz",
			#"-loops:max_kic_build_attempts %d" % parameters["BenchmarkOptions"]["MaxKICBuildAttempts"],
		]
		if parameters["RunLength"] == 'Test':
			kicCommand.append('-run:test_cycles')
			kicCommand.append('-constant_seed')
		
		kicCommand = [
			'# Run KIC', '', 
			'cd $SGE_TASK_ID',
			join(kicCommand, " "), '', 
			'echo',
			'echo moving .e and .o files to task subdir...',
			'mv ../*.e$JOB_ID.$SGE_TASK_ID .',
			'mv ../*.o$JOB_ID.$SGE_TASK_ID .',
			'',
		] 
		
		self.script = ct.createScript(kicCommand, type="BenchmarkKIC")
		print(self.script)
		
		def retire(self):
			pass
		
class KICBenchmarkJob(GenericBenchmarkJob):

	suffix = "bmarkKIC"
	flatOutputDirectory = True
	name = "KIC Benchmark"
	results_flatfile = "scientific_benchmark_KIC_score12prime.results"
	
	def _initialize(self):
		self.describe()
		
		parameters = self.parameters
		benchmarksettings = self.benchmarksettings

		scheduler = TaskScheduler(self.workingdir)
		 
		StartingStructuresDirectory = benchmarksettings.StartingStructuresDirectory
		LoopsInputDirectory = benchmarksettings.LoopsInputDirectory 
		StartingStructuresDirectory_contents=os.listdir(benchmarksettings.StartingStructuresDirectory)
		for item in StartingStructuresDirectory_contents:
			if item.endswith('.pdb'):
				input_pdb = os.path.join(StartingStructuresDirectory, item)
				pdb_prefix = item.split('.pdb')[0].split('_')[0]
				
				#check for existence of corresponding loop file
				loop_file = os.path.join(LoopsInputDirectory, '%s.loop' % pdb_prefix)
				if not os.path.isfile(loop_file):
					errormsg = 'ERROR: loop file of %s not found in %s' % (item, LoopsInputDirectory)
					self._status(errormsg)
					raise Exception(errormsg)
		
				taskdir = self._make_taskdir(pdb_prefix)
				targetdir = os.path.join(self.targetdirectory, pdb_prefix)
				# The task indexing in ClusterTask is 1-based. NumberOfModelsOffset is 0-based so add 1.
				kicTask = KICBenchmarkTask(taskdir, targetdir, self.parameters, self.benchmarksettings, input_pdb, loop_file, pdb_prefix, self.parameters["BenchmarkOptions"]["NumberOfModelsPerPDB"], self.parameters["BenchmarkOptions"]["NumberOfModelsOffset"] + 1, name=self.name)
				scheduler.addInitialTasks(kicTask)
				
		self.scheduler = scheduler
	
	def _parse(self):
		'''Parses the KIC scientific benchmark results into a flat file.'''
	
		start_time = time.time()
		
		# Write headers
		outfile = open(self._workingdir_file_path(self.results_flatfile), 'w')
		outfile.write('#PDB\tModel\tLoop_rmsd\tTotal_energy\tRuntime\n')
		
		# Parse benchmark results
		start_index = self.parameters["BenchmarkOptions"]["NumberOfModelsOffset"] + 1
		end_index = self.parameters["BenchmarkOptions"]["NumberOfModelsOffset"] + self.parameters["BenchmarkOptions"]["NumberOfModelsPerPDB"]
		sorted_indir_contents = sorted(os.walk(self.workingdir).next()[1])
		
		for pdbID in sorted_indir_contents:
			self._status(pdbID)
			num_models = 0
			pdb_dir = os.path.join(self.workingdir, pdbID)
			pdb_dir_contents = os.listdir(pdb_dir)
			continue # todo
		
			# Copy output and error files to model subdirectories
			for flname in pdb_dir_contents:
				if '.o' in flname or '.e' in flname: # todo: make this more robust
					model_subdir=flname.split('.')[-1]
					assert(os.path.isdir(model_subdir))
					shutil.copy(os.path.join(pdb_dir, flname), os.path.join(pdb_dir, model_subdir))
		
			#parse output files to collect energies, rmsds and runtimes
			for flname in pdb_dir_contents:
				flpath = os.path.join(pdb_dir, flname)
				# Iterate through numbered directories
				if os.path.isdir(flpath) and flname.isdigit() and int(flname) >= start_index and int(flname) <= end_index:
					model_subdir = flpath
					model_subdir_contents = os.listdir(model_subdir)
					for taskflname in model_subdir_contents:
						if '.o' in taskflname: # todo: make this more robust
							stats=[]
							stdout_contents = rosettahelp.readFileLines(os.path.join(flpath, taskflname))
							lines = stdout_contents[0:4] + stdout_contents[-9:] # get the first 4 lines and the last 9 lines 
							#todo : I'll need to parse the file here
							if len(lines) > 11 and lines[-3] == 'end_date:':
								
								#calculate runtime
								_start_time = 0 #todo int(strftime(strptime(lines[3],self.input_time_format), "%s"))
								_end_time = 0 #todo int(strftime(strptime(lines[-2],self.input_time_format), "%s"))
								runtime=_end_time - _start_time
								
								total_energy = None
								loop_rms = None
		
								#determine loop rmsd and total energy of the pose
								for line in lines:
									if 'total_energy' in line:
										total_energy = float(line.split('total_energy:')[1].strip(' '))
									elif 'loop_rms' in line:
										loop_rms = float(line.split('loop_rms:')[1].strip(' '))
		
								if total_energy != None and loop_rms != None:
									num_models += 1
									outfile.write('%s\t%s\t%s\t%s\t%s\n' % (pdbID, flname, str(loop_rms), str(total_energy), str(runtime)))
		
		outfile.close()
		self._status("Time consumed: " + str(time.time() - start_time))


	def _analyze(self):
		if not self._parse():
			return False
		return True

	#def getResults(self):
		#return self.results


class GenericKICTask(ClusterTask):

	# additional attributes
	
	def __init__(self, workingdir, targetdirectory, jobparameters, taskparameters, name="", prefix = "KIC"):
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
		
		ct = kicClusterScript(self.workingdir, self.targetdirectory, self.taskglobals, normalized_inputs, self.numtasks, self.jobIDs)
		self.script = ct.createScript(commandLines, type="KIC")
		self.runlength = ct.parameters["maxhours"] * 60 + ct.parameters["maxmins"]
			
		return super(GenericKICTask, self).start(sgec, dbID)

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
		
class GenericKICJob(ClusterBatchJob):

	suffix = "KIC"
	flatOutputDirectory = True
	name = "KIC"

	def _defineOutputFiles(self):
		self.resultFilemasks.append((".", "*"))
		
	def __init__(self, sgec, parameters, tempdir, targetroot, dldir, testonly = False):
		# The tempdir is the one on the submission host e.g. chef
		# targetdirectory is the one on your host e.g. your PC or the webserver
		# The taskdirs are subdirectories of the tempdir on the submission host and the working directories for the tasks
		# The targetdirectories of the tasks are subdirectories of the targetdirectory named like the taskdirs
		jobs = sorted(parameters["jobs"].keys())
		if len(jobs) > 1:
			parameters["ID"] = "%d-%d" % (jobs[0], jobs[-1])
		else:
			parameters["ID"] = jobs[0]
		super(GenericKICJob, self).__init__(sgec, parameters, tempdir, targetroot, dldir, testonly)
		
			
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
			#jobparams['_FILE_ID'] = "%s-%s" % (jobparams[ddgfields.ExperimentID], jobparams[ddgfields.PDB_ID])
		
		# Create files
		self.describe()
		try:
			jobID = None
			for jobID in self.jobIDs:
				self._generateFiles(jobID)
		except Exception, e:
			estr = str(e) + "\n" + traceback.format_exc()
			raise Exception("An error occurred creating the files for the KIC job %(jobID)s.\n%(estr)s" % vars())
			
		# Create tasks from the protocol steps
		tasks = {}
		ProtocolGraph = parameters["ProtocolGraph"]
		for taskID, taskdetails in ProtocolGraph.iteritems():
			taskcls = taskdetails["ClassName"] or "GenericKICTask"
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
	

