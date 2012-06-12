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
import statsfns
			
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
	
	def __init__(self, sgec, parameters, benchmarksettings, tempdir, targetroot, dldir, testonly = False):
		self.results = None
		self.PDFReport = None
		self.output_file_paths = []
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
			"loops:input_pdb" : self.input_pdb,
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
		outfilepath = self._workingdir_file_path(KICBenchmarkJob.results_flatfile)
		try:
			outfile = open(outfilepath, 'w')
			outfile.write('#PDB\tModel\tLoop_rmsd\tTotal_energy\tRuntime\n')
			input_time_format = "%a %b %d %H:%M:%S %Z %Y"
			for kicTask in self.scheduler._initialtasks:
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
					self.addOutputFilePath("stdout", "%s-%04d" % (pdbID, i), stdoutfilename, stdoutfile)
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
						for line in stdout_contents.split("\n")[-9:]:
							if 'total_energy' in line:
								total_energy = float(line.split('total_energy:')[1].strip(' '))
							elif 'loop_rms' in line:
								loop_rms = float(line.split('loop_rms:')[1].strip(' '))
						
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
			num_models_offset = self.parameters["BenchmarkOptions"]["NumberOfModelsOffset"]
			num_models_per_PDB = self.parameters["BenchmarkOptions"]["NumberOfModelsPerPDB"]
			placeholder_image = os.path.join(os.path.split(os.path.realpath(__file__))[0], self.benchmarksettings.placeholder_image)
			top_X = self.parameters["BenchmarkOptions"]["NumberOfLowestEnergyModelsToConsiderForBestModel"]
			outdir = self._targetdir_file_path('analysis')
			if self.testonly and not(os.path.exists(self.targetdirectory)):
				make755Directory(self.targetdirectory)
			if not(os.path.exists(outdir)):
				make755Directory(outdir)
			
			# Parse models
			pdb_models = {} # PDB ID -> List[Model] 
			start_index = num_models_offset + 1
			end_index = num_models_offset + num_models_per_PDB
			total_runtime = 0
			lines = readFileLines(self._workingdir_file_path(self.results_flatfile))
			for line in lines:
				self._status(line)
				if not line.startswith('#'):
					data = line.strip('\n').split('\t')
					self._status(data)
					if len(data) > 4:
						pdb = data[0]
						pdb_models[pdb] = pdb_models.get(pdb, [])
						model_index = int(data[1])
						if model_index >= start_index and model_index <= end_index:
							runtime = int(data[4])
							model = statsfns.Model(pdb, model_index, float(data[2]), float(data[3]), runtime)
							pdb_models[pdb].append(model)
							total_runtime += runtime
							self._status(total_runtime)
					
			if total_runtime != 0:
				self._status('Total runtime [hours]: %d' % int(total_runtime/float(3600)))
			
			# Compute basic statistics and create RMSD vs. Rosetta score plots per PDB
			tex_tables = []
			best_models = []
			closest_models = []
			sorted_pdb_ids = sorted(pdb_models.keys())
			self._status("%d PDBs" % len(sorted_pdb_ids))
			
			# Init results tex table
			tex_table_string = ['''
\\begin{tabular}{rr|rrr|rrr}
PDB &\# models &Top %(top_X)d best model &Loop rmsd &Energy &Closest model &Loop rmsd &Energy\\\\\\hline
''' % vars()]
			for pdb in sorted_pdb_ids:
				self._status(pdb)
				models = pdb_models[pdb]
				self._status('%d successful models' % len(models))
				#determine best and closest model for the given pdb
				models_sorted_by_energy = sorted(models, lambda x, y: cmp(x.total_energy, y.total_energy))
				models_sorted_by_rmsd = sorted(models, lambda x, y: cmp(x.loop_rms, y.loop_rms))
				best_model = models_sorted_by_energy[0]
				
				# When looking for the best model, consider the top X lowest energy models and pick the one with lowest rmsd
				for i in range(top_X):
					if i < len(models_sorted_by_energy):
						best_model_candidate = models_sorted_by_energy[i] # here
						if best_model_candidate.loop_rms < best_model.loop_rms:
							best_model = best_model_candidate
				#--
				closest_model = models_sorted_by_rmsd[0]
				self._status('Best model of the top %d (i.e. lowest RMSD of top %d lowest energy models): %s, %f, %f' % (top_X, top_X, best_model.id, best_model.loop_rms, best_model.total_energy))
				self._status('Closest model (i.e. lowest RMSD): %s, %f, %f' % (closest_model.id, closest_model.loop_rms, closest_model.total_energy))
				best_models.append(best_model)
				closest_models.append(closest_model)
				#create scatterplot for each pdb

				outfile_name = os.path.join(outdir, '%s_models.out' % pdb)
				analysis.scatterplot(outdir, models_sorted_by_energy, best_model, outfile_name, top_X)
				num_bins = 100
				outfile_name = os.path.join(outdir, '%s_density.out' % pdb)
				analysis.densityplot(outdir, models_sorted_by_energy, outfile_name, num_bins)
				
				# Store data in results tex table
				tex_table_string.append('%s ' % pdb)
				tex_table_string.append('&%d ' % len(models))
				tex_table_string.append('&%s ' % best_model.runID)
				tex_table_string.append('&%0.2f ' % best_model.loop_rms)
				tex_table_string.append('&%0.2f' % best_model.total_energy)
				tex_table_string.append('&%s ' % closest_model.runID)
				tex_table_string.append('&%0.2f ' % closest_model.loop_rms) 
				tex_table_string.append('&%0.2f\\\\\n' % closest_model.total_energy)
			
			#write results tex table
			tex_table_string.append('\\end{tabular}\n')
			tex_table_string = join(tex_table_string, "")
			tex_outfile_name = os.path.join(outdir, 'results.tex')
			tex_tables.append(tex_outfile_name)
			writeFile(tex_outfile_name, tex_table_string)
			
			self._status(tex_outfile_name)
			
			#create rmsd boxplot for the best models
			boxplot_outfile_name = os.path.join(outdir, 'best_models_rmsd_dist.out')
			analysis.boxplot(outdir, best_models, boxplot_outfile_name)
			self._status(outdir)
			self._status(boxplot_outfile_name)
			
			#calculate global stats across all pdbs and write overall performance tex table
			self._status('Global statistics (median rmsd and energy):')
			outfile_name = os.path.join(outdir, 'global_results.tex')
			tex_tables.append(outfile_name)
			best_models_median_energy = round(analysis.getEnergyStats(best_models)[1], 2)
			best_models_median_rmsd = round(analysis.getRmsdStats(best_models)[1], 2)
			closest_models_median_energy = round(analysis.getEnergyStats(closest_models)[1], 2)
			closest_models_median_rmsd = round(analysis.getRmsdStats(closest_models)[1], 2)
			self._status('best models median rmsd and energy: %f\t%f' % (best_models_median_rmsd, best_models_median_energy))
			self._status('closest models median rmsd and energy: %f\t%f' % (closest_models_median_rmsd, closest_models_median_energy))
			outstring = '''
\\begin{tabular}{lrr}
Model selection &Median loop rmsd &Median energy\\\\\\hline
{\\bf Top %(top_X)d best model} &{\\bf %(best_models_median_rmsd)0.2f} &{\\bf %(best_models_median_energy)0.2f}\\\\
Closest model &%(closest_models_median_rmsd)0.2f &%(closest_models_median_energy)0.2f\\\\
\\end{tabular}
''' % vars()
			writeFile(outfile_name, outstring)
			
			self._status(outfile_name)
			
			#put all model output figures into a tex table
			score_vs_rmsd_plots = []
			num_pdbs = len(sorted_pdb_ids)
			num_rows = 4
			num_cols = 2
			num_plots_per_page = num_rows * num_cols
			num_pages = int(math.ceil(2 * num_pdbs/float(num_plots_per_page)))
			self._status('%d pdbs' % num_pdbs)
			self._status('%d pages' % num_pages)
			index = 0
			for i in range(num_pages):
				outfile_name=os.path.join(outdir, 'all_models_%d.tex' % (i+1))
				outstring = '''
\\begin{figure}
\\resizebox{\\textwidth}{!}{
\\begin{tabular}{%s}
''' % ('c' * num_cols)
				#-
				for j in range(num_rows):
					
					k = 0
					while k < num_cols:
						if index < num_pdbs:
							pdb = sorted_pdb_ids[index]
							outstring += '\\includegraphics{%s} &' % os.path.join(outdir, "%s_models_all.eps" % pdb)
							outstring += '\\includegraphics{%s} &' % os.path.join(outdir, "%s_density.eps" % pdb)
						else:
							outstring += '\\includegraphics{%s} &' % placeholder_image
							outstring += '\\includegraphics{%s} &' % placeholder_image
						k += 2
						index += 1
					
					outstring = outstring.rstrip(' &') + '\\\\\n'
				#-	
				outstring += '''
\\end{tabular}
}\\end{figure}
'''
				writeFile(outfile_name, outstring)
				score_vs_rmsd_plots.append(outfile_name)
				self._status(outfile_name)
			
			#create report pdf
			tempx = num_models_offset + 1
			reportname = 'KIC_scientific_benchmark_report_top%(top_X)d_models_%(tempx)d-%(num_models_per_PDB)d' % vars()
			outfile_name = os.path.join(outdir, '%s.tex' % reportname)
			
			outstring = analysis.texHeader()
			
			outstring += '''
\\section{Benchmark details}'''

			BenchmarkTex = '''
\\paragraph{Benchmark run %(BenchmarkNumber)d}
Rosetta version %(RosettaVersion)s%(RosettaDBVersion)s
\\begin{lstlisting}
%(RosettaCommandLine)s
\\end{lstlisting}
'''			
			BenchmarkNumber = self.parameters["ID"]
			RosettaVersion = self.parameters['RosettaSVNRevision']
			RosettaDBVersion = self.parameters['RosettaDBSVNRevision']
			if RosettaDBVersion != RosettaVersion:
				RosettaDBVersion = " (Rosetta database version %s)" % RosettaDBVersion
			else:
				RosettaDBVersion = ''
			RosettaCommandLine = self.parameters['CommandLine']
			RosettaCommandLine = statsfns.breakCommandLine(RosettaCommandLine) 
			outstring += BenchmarkTex % vars() 


			outstring += '''
\\section{Overall benchmark performance}
\\begin{center}
\\input{%s}

\\includegraphics[width=10cm]{%s}
\\end{center}

\\clearpage
\\section{Individual results per input structure}
\\begin{table}[ht]
\\input{%s}
\\end{table}

\\clearpage''' % (tex_tables[1], '%s.eps' % boxplot_outfile_name.split('.out')[0], tex_tables[0])
			
			for i in range(len(score_vs_rmsd_plots)):
				outstring += '''
\\input{%s}''' % score_vs_rmsd_plots[i]
			#-
			outstring+='''
\\end{document}'''
			
			writeFile(outfile_name, outstring)
			for i in range(2):
				#error = statsfns.Popen(outdir, ['pdflatex', '-output-directory', outdir, outfile_name]).getError()
				#if error:
			#		raise Exception(error)
				self._status(outfile_name)
				error = statsfns.Popen(outdir, ['latex', '-output-directory', outdir, outfile_name]).getError()
				if error:
					raise Exception(error)
				error = statsfns.Popen(outdir, ['dvips', '%s.dvi' % reportname]).getError()
				if error:
					raise Exception(error)
				error = statsfns.Popen(outdir, ['ps2pdf', '%s.ps' % reportname]).getError()
				if error:
					raise Exception(error)
			
			reportFile = os.path.join(outdir, '%s.pdf' % reportname)
			self.PDFReport = readFile(reportFile)
			self._status('Final report: %s' % reportFile)
		except Exception, e:
			import traceback
			self._status(str(e))
			self._status(traceback.format_exc())
			return False
		
		return True

class KICBenchmarkJobAnalyzer(KICBenchmarkJob):
	
	def __init__(self, sgec, parameters, benchmarksettings, tempdir, targetroot, dldir, testonly = False):
		super(KICBenchmarkJobAnalyzer, self).__init__(sgec, parameters, benchmarksettings, tempdir, targetroot, dldir, testonly = True)

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
		self.shortname = split(scriptfilename, "_")[0]
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
	

