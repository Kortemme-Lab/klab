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
import math
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
from rosettahelper import make755Directory, makeTemp755Directory, readFile, readFileLines, writeFile, permissions755, permissions775, normalize_for_bash
import time
import datetime
import pickle
import traceback
import analysis
			
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
		benchmark_binary = self.getBinary(taskparameters["BinaryName"])
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
echo "<user>"
whoami
echo "</user>"
echo "<usergroups>"
groups 2> /dev/null
echo "</usergroups>"
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


class OutputFilePath(object):
	def __init__(self, filetype, fileID, filename, path_to_file):
		self.filetype = filetype
		self.fileID = fileID
		self.filename = filename
		self.path_to_file = path_to_file 
		
class GenericBenchmarkJob(RosettaClusterJob):
	
	def __init__(self, sgec, parameters, benchmarksettings, benchmarkoptions, tempdir, targetroot, dldir, testonly = False):
		self.results = None
		self.PDFReport = None
		self.output_file_paths = []
		self.benchmarkoptions = benchmarkoptions
		parameters["BenchmarkOptions"] = pickle.loads(parameters["BenchmarkOptions"])
		self.benchmarksettings = benchmarksettings
		super(GenericBenchmarkJob, self).__init__(sgec, parameters, tempdir, targetroot, dldir, testonly, jobsubdir = str(parameters["ID"]))
	
	def addOutputFilePath(self, filetype, fileID, filename, path_to_file):
		self.output_file_paths.append(OutputFilePath(filetype, fileID, filename, path_to_file))
		
	def getOutputFilePaths(self):
		return self.output_file_paths
	
class KICBenchmarkTask(ClusterTask):

	# additional attributes
	benchmark_name = "KIC"
	prefix = "KICBenchmark"
	
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
			"in:file:s" : self.input_pdb, # Revisions 49521 upwards
			"loops:input_pdb" : self.input_pdb, # Revisions 49520 downwards
			"loops:loop_file" : self.loop_file,
			"in:file:native" : self.input_pdb,
			"out:prefix" : self.pdb_prefix,
			"loops:max_kic_build_attempts" : parameters["BenchmarkOptions"]["MaxKICBuildAttempts"],
		}
		kicCommand = [
			ct.getBinary(parameters["BinaryName"]),
			"-database %s" % ct.getDatabaseDir(),
			self.parameters["CommandLine"] % commandLineParams
		]
		if parameters["RunLength"] == 'Test':
			kicCommand.append('-run:test_cycles')
		
		kicCommand = [
			'# Run KIC', '', 
			#'mkdir $SGE_TASK_ID',
			'cd $SGE_TASK_ID',
			join(kicCommand, " "), '', 
		] 
		
		self.script = ct.createScript(kicCommand, type="BenchmarkKIC")
		
	def retire(self):
		passed = super(KICBenchmarkTask, self).retire()
		if passed:
			try:
				for i in range(self.firsttaskindex, self.firsttaskindex + self.numtasks):
					stdoutfile = self._workingdir_file_path("%s.o%s.%d" % (self.scriptfilename, self.jobid, i))
					assert(os.path.exists(stdoutfile))
					shutil.move(stdoutfile, self._workingdir_file_path(str(i)))
			except:
				return False
		return passed

		
class KICBenchmarkJob(GenericBenchmarkJob):

	suffix = "bmarkKIC"
	flatOutputDirectory = True
	name = "KIC Benchmark"
	results_flatfile = "scientific_benchmark_KIC.results"
	NumberOfBins = 100
				
	def _initialize(self):
		self.describe()
		self.pdblist = []
		
		parameters = self.parameters
		benchmarksettings = self.benchmarksettings

		scheduler = TaskScheduler(self.workingdir)
		 
		StartingStructuresDirectory = benchmarksettings.StartingStructuresDirectory
		LoopsInputDirectory = benchmarksettings.LoopsInputDirectory 
		StartingStructuresDirectory_contents=os.listdir(benchmarksettings.StartingStructuresDirectory)
		
		pdblist = []
		for item in StartingStructuresDirectory_contents:
			if item.endswith('.pdb'):
				pdblist.append(item)
		
		groupsize = int(round(len(pdblist) / 10.0))
		pdbsublists = [pdblist[i:i+groupsize] for i in range(0, len(pdblist), groupsize)]
		
		for sublist in pdbsublists:
			previousKICTask = None
			#previousPDB_prefix = None
			for item in sublist:
				input_pdb = os.path.join(StartingStructuresDirectory, item)
				self.pdblist.append(input_pdb)
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
				if previousKICTask:
					kicTask.addPrerequisite(previousKICTask, [])
				else:
					scheduler.addInitialTasks(kicTask)
				previousKICTask = kicTask
				#previousPDB_prefix = pdb_prefix
				if parameters["RunLength"] == 'Test':
					break
			if parameters["RunLength"] == 'Test':
				break
				
		self.scheduler = scheduler
	
	def _parse(self):
		'''Parses the KIC scientific benchmark results into a flat file.'''
		outfilepath = self._workingdir_file_path(KICBenchmarkJob.results_flatfile)
		try:
			outfile = open(outfilepath, 'w')
			outfile.write('#PDB\tModel\tLoop_rmsd\tTotal_energy\tRuntime\n')
			input_time_format = "%a %b %d %H:%M:%S %Z %Y"
			for kicTask in self.scheduler.tasks_in_order:
				pdbID = kicTask.pdb_prefix
				self._status(pdbID)
				num_models = 0
				pdb_dir = kicTask.workingdir
				for i in range(kicTask.firsttaskindex, kicTask.firsttaskindex + kicTask.numtasks):
					stdout_contents = None
					model_subdir = os.path.join(pdb_dir, str(i))
					model_subdir_contents = os.listdir(model_subdir)
					stdoutfilename = "%s.o%s.%d" % (kicTask.scriptfilename, kicTask.jobid, i)
					stdoutfile = os.path.join(kicTask._workingdir_file_path(str(i)), stdoutfilename)
					stdout_contents = readFile(stdoutfile)
					#self.addOutputFilePath("stdout", "%s-%04d" % (pdbID, i), stdoutfilename, stdoutfile)
					startdate = re.match(".*?<startdate>\s*(.*?)\s*</startdate>", stdout_contents, re.DOTALL)
					enddate = re.match(".*?<enddate>\s*(.*?)\s*</enddate>", stdout_contents, re.DOTALL)
					if startdate and enddate:
						# Calculate runtime
						_start_time = int(strftime(strptime(startdate.group(1), input_time_format), "%s"))
						_end_time = int(strftime(strptime(enddate.group(1), input_time_format), "%s"))
						runtime=_end_time - _start_time
						
						total_energy = None
						loop_rms = None
		
						# Determine loop RMSD and total energy of the pose
						if self.parameters["RosettaSVNRevision"] < 49521:
							for line in stdout_contents.split("\n")[-9:]:
								if 'total_energy' in line:
									total_energy = float(line.split('total_energy:')[1].strip(' '))
								elif 'loop_rms' in line:
									loop_rms = float(line.split('loop_rms:')[1].strip(' '))
						else:
							for line in stdout_contents.split("\n")[-30:]:
								energystr = "protocols.loop_build.LoopBuildMover: total_energy"
								looprmsstr = "protocols.loop_build.LoopBuildMover: loop_rms"
								if line.startswith(energystr):
									total_energy = float(line[len(energystr):])
								if line.startswith(looprmsstr):
									loop_rms = float(line[len(looprmsstr):])
							
						failstr = '''protocols.loops.loop_mover.perturb.LoopMover_Perturb_KIC: Unable to build this loop - a critical error occured. Moving on .. 
protocols.loops.loop_mover.perturb.LoopMover_Perturb_KIC: result of loop closure:0 success, 3 failure 1
protocols.looprelax: Structure  failed initial kinematic closure. Skipping...
protocols::checkpoint: Deleting checkpoints of Remodel
protocols::checkpoint: Deleting checkpoints of Loopbuild
protocols.loop_build.LoopBuild: Initial kinematic closure failed. Not outputting.'''

						if total_energy == None:
							self._status("Could not find total_energy in %s." % stdoutfile)
						elif loop_rms == None:
							self._status("Could not find loop_rms in %s." % stdoutfile)
						else:
							num_models += 1
							outfile.write('%s\t%d\t%f\t%f\t%d\n' % (pdbID, i, loop_rms, total_energy, runtime))
					else:
						raise Exception("Error parsing start/end date.")
		except Exception, e:
			if outfile:
				outfile.close()
			self._status(str(e))
			self._status(traceback.format_exc())
			return False
					
		outfile.close()
		self.addOutputFilePath("Flat file", 1, KICBenchmarkJob.results_flatfile, outfilepath)
		return True

	def _analyze(self):
		if not self.testonly:
			if not self._parse():
				return False
		self._status("analyzing")
		try:
			benchmarkRunSettings = self.parameters
			benchmarkoptions = self.parameters["BenchmarkOptions"]
			replacementPatterns = self.benchmarkoptions
			optionReplacementPatterns = {}
			for rp in replacementPatterns:
				optionReplacementPatterns[rp["OptionName"]] = {"Pattern" : rp["CommandLineVariable"], "Description" : rp["Description"], "ShowInReport" : rp["ShowInReport"]}
				
			try:
				reportsettings = {"NumberOfBins" : self.NumberOfBins, "TopX" : benchmarkoptions['NumberOfLowestEnergyModelsToConsiderForBestModel']}
				report = analysis.BenchmarkReport(self.targetdirectory, reportsettings, quiet = False, html = False)
				report.addBenchmark(benchmarkRunSettings["ID"], None, self._workingdir_file_path(self.results_flatfile), benchmarkRunSettings['RosettaSVNRevision'], benchmarkRunSettings['RosettaDBSVNRevision'], benchmarkRunSettings['CommandLine'], benchmarkoptions, optionReplacementPatterns, passingFileContents = False)
				self.PDFReport = report.run()
			except Exception, e:
				raise Exception("An error occurred creating the report.<br>Error: '%s'<br>Traceback:<br>%s" % (str(e), traceback.format_exc().replace("\n", "<br>")))
		except Exception, e:
			self._status(str(e))
			self._status(traceback.format_exc())
			return False
		
		return True

class KICBenchmarkJobAnalyzer(KICBenchmarkJob):
	
	def __init__(self, sgec, parameters, benchmarksettings, benchmarkoptions, tempdir, targetroot, dldir, testonly = False):
		super(KICBenchmarkJobAnalyzer, self).__init__(sgec, parameters, benchmarksettings, benchmarkoptions, tempdir, targetroot, dldir, testonly = True)

	def _initialize(self):
		scheduler = TaskScheduler(self.workingdir)
		self.scheduler = scheduler
		self.workingdir = "/netapp/home/klabqb3backrub/benchmarks/KIC/temp/tmpHlhXOv_bmarkKIC" 
		#"/netapp/home/klabqb3backrub/benchmarks/KIC/temp/tmpoQ_A6y_bmarkKIC"
		#"/netapp/home/klabqb3backrub/benchmarks/KIC/temp/tmpdB7VvK_bmarkKIC"
		self.targetdirectory = "/backrub/benchmarks/KIC/temp/tmpXgi577_bmarkKIC"
		#"/backrub/benchmarks/KIC/temp/tmp9NUsVU_bmarkKIC"
		self.describe()
		self.addOutputFilePath("Flat file", 1, KICBenchmarkJob.results_flatfile, self._workingdir_file_path(KICBenchmarkJob.results_flatfile))


		


