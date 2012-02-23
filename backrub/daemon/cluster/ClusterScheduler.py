#!/usr/bin/python2.4
# encoding: utf-8
"""
ClusterScheduler.py

Created by Shane O'Connor 2011.
Copyright (c) 2011 __UCSF__. All rights reserved.
"""


import sys
import os
import time
import shutil
import re
from string import join
import distutils.dir_util
import fnmatch
import traceback

#import sge

from ClusterTask import INITIAL_TASK 	as ClusterTask_INITIAL_TASK
from ClusterTask import INACTIVE_TASK 	as ClusterTask_INACTIVE_TASK
from ClusterTask import ACTIVE_TASK 	as ClusterTask_ACTIVE_TASK
from ClusterTask import RETIRED_TASK 	as ClusterTask_RETIRED_TASK
from ClusterTask import COMPLETED_TASK 	as ClusterTask_COMPLETED_TASK
from ClusterTask import FAILED_TASK 	as ClusterTask_FAILED_TASK
from ClusterTask import status		 	as ClusterTask_status

import SimpleProfiler
from Graph import JITGraph
from statusprinter import StatusPrinter

from rosettahelper import make755Directory, makeTemp755Directory, writeFile, permissions755, permissions775

todo='''
	We allow directed acylic graphs, not necessarily strongly connected.
	This needs to be fixed. Use Tarjan's algorithm.
	http://en.wikipedia.org/wiki/Tarjan%E2%80%99s_strongly_connected_components_algorithm	
	CyclicDependencyException
	IncompleteGraphException
	
	def traverseDependents(self, availabletasks, task):
		del availabletasks[task]
		for d in task.getDependents():
			if not allowedtasks[d]:
				# We have either encountered a task previously removed or else one which
				# was never in the list to begin with. 
				# todo: Distinguish these cases
				raise CyclicDependencyException 
			traverseDependents(d)

	def checkGraphReachability(tasks, initialtasks):
		check initial in tasks
		
		for task in initialtasks:
			if not tasks[task]:
				raise IncompleteGraphException
			traverseDependents(tasks, task)
'''
def checkGraphReachability(initialtasks):
	pass

# todo: Can this handle all DAGs?
def traverseGraph(parenttasks, reachedNodes):
	for t in parenttasks:
		if t not in reachedNodes:
			reachedNodes.append(t)
			traverseGraph(t.getDependents(), reachedNodes)
	return reachedNodes
		

# Scheduler exceptions
class TaskSchedulerException(Exception):
	def __init__(self, pending, retired, completed, msg = ""):
		self.message = msg
		self.pending = pending
		self.retired = retired
		self.completed = completed
	def __str__(self):
		s = ""
		# todo: List the remaining tasks and the completed ones
		print('<SchedulerException message="%s">' % self.message)
		for p in self.pending:
			print("<pending>%s</pending>" % p.getName())
		print("</SchedulerException>")
		# etc.
		return s

class SchedulerTaskAddedAfterStartException(TaskSchedulerException): pass
class BadSchedulerException(TaskSchedulerException): pass
class TaskCompletionException(TaskSchedulerException): pass
class SchedulerDeadlockException(TaskSchedulerException): pass
class SchedulerStartException(TaskSchedulerException): pass

class TaskScheduler(StatusPrinter):

	def __init__(self, workingdir):
		self._initialtasks = []	   # As well as the initial queue, we remember the initial tasks so we can generate the dependency graph 
		self.sgec = None
		self.dbID = 0
		self._setStatusPrintingParameters(self.dbID, statustype = "scheduler", level = 0, color = "green")
		self.debug = True
		# todo: The task states here have different meanings to those of ClusterTask. Maybe separate them entirely.
		self.tasks = {ClusterTask_INITIAL_TASK: [],
					  ClusterTask_ACTIVE_TASK: [],
					  ClusterTask_RETIRED_TASK: [],
					  ClusterTask_COMPLETED_TASK: []}
		
		self.pendingtasks = {}
		self.workingdir = workingdir
		self.failed = False
		self.started = False
		self.tasks_in_order = []
		self.graph = None
	
	def _movequeue(self, task, oldqueue, newqueue):
		# todo: The active queue actually contains both queued and active jobs w.r.t. the cluster head node 
		self._status("Moving %d (%s) from %s to %s" % (task.jobid, task.getName(), ClusterTask_status.get(oldqueue), ClusterTask_status.get(newqueue)))
		self.tasks[oldqueue].remove(task)
		self.tasks[newqueue].append(task)
		
	def _getAllTasks(self):
		tasks = []
		tasks.extend(self.tasks[ClusterTask_INITIAL_TASK])
		tasks.extend(self.tasks[ClusterTask_ACTIVE_TASK])
		tasks.extend(self.tasks[ClusterTask_RETIRED_TASK])
		tasks.extend(self.tasks[ClusterTask_COMPLETED_TASK])
		return tasks		
	
	def killAllTasks(self):
		success = True
		checkGraphReachability(self._initialtasks)
		tasklist = traverseGraph(self._initialtasks, [])
		for task in tasklist:
			if task.isActiveOnCluster():
				success = task.kill() and success
		return success
		
	def getprofile(self):
		profile = []
		count = 1
		ts = self._getAllTasks()
		
		for task in self.tasks_in_order:
			status = ClusterTask_status.get(task.getState(allowToRetire = False))
			profile.append(('task id="%d" name="%s" status="%s"' % (count, task.getName(), status), task.getprofile()))
			ts.remove(task)
			count += 1
		
		if ts:
			profile.append(("Logical error in getprofile! (%s)" % str(ts), 0))
			
		for task in ts:
			profile.append(("%s@%d" % (task.getName(), count), task.getprofile()))
			count += 1
		
		return profile
		
	# API		  
	
	def addInitialTasks(self, *tasks):
		if self.started:
			raise SchedulerTaskAddedAfterStartException(self.pendingtasks, self.tasks[ClusterTask_RETIRED_TASK], self.tasks[ClusterTask_COMPLETED_TASK], msg = "Exception adding initial task: %s" % task.getName())
		for task in tasks:
			self._initialtasks.append(task)
			self.tasks[ClusterTask_INITIAL_TASK].append(task)

	def raiseFailure(self, exception = None):
		self.failed = True
		if exception:
			raise exception
			
	def getJITGraph(self):
		# Write the progress to file
		g = JITGraph(self._initialtasks, self.dbID)						
		if g.isATree():
			return (g.getSpaceTree(), g.getHTML())
		else:
			return g.getForceDirected()
				   
	def start(self, sgec, dbID):
		# todo: Check the reachability and acyclicity of the graph here
		self.sgec = sgec
		self.dbID = dbID
		self._setStatusPrintingParameters(self.dbID)
		checkGraphReachability(self.tasks[ClusterTask_INITIAL_TASK])
			
		tasksToStart = []
		for task in self.tasks[ClusterTask_INITIAL_TASK]:
			tasksToStart.append(task)
			
		for task in tasksToStart:
			#todo: pass in files?
			started = task.start(self.sgec, self.dbID)
			if started:
				self._status("Queued %d (%s)" % (task.jobid, task.getName()))
				self.tasks_in_order.append(task)
				self._movequeue(task, ClusterTask_INITIAL_TASK, ClusterTask_ACTIVE_TASK)	
			else:
				self.raiseFailure(SchedulerStartException(self.pendingtasks, self.tasks[ClusterTask_RETIRED_TASK], self.tasks[ClusterTask_COMPLETED_TASK], msg = "Exception starting: %s" % task.getName()))
				return False
		
		return True
		
	def isAlive(self):
		return self.failed == False
	
	def hasFailed(self):
		return self.failed
	
	def step(self):
		'''This determines whether the system state changes by checking the 
		   state of the individual tasks.
		   We return True iff all tasks are completed.
		   Note that qstat must be called before the scheduler is stepped as otherwise the qstat cached table of job statuses will not exist.
		   '''
		
		# I told you I was sick. Don't step a broken scheduler.
		if self.failed:
			 raise BadSchedulerException(self.pendingtasks, self.tasks[ClusterTask_RETIRED_TASK], self.tasks[ClusterTask_COMPLETED_TASK], msg = "The scheduler has failed.") 
							  
		# Retire tasks
		activeTasks = self.tasks[ClusterTask_ACTIVE_TASK][:]
		for task in activeTasks:
			tstate = task.getState()
			if tstate == ClusterTask_RETIRED_TASK:
				self._movequeue(task, ClusterTask_ACTIVE_TASK, ClusterTask_RETIRED_TASK)
			elif tstate == ClusterTask_FAILED_TASK:
				self._movequeue(task, ClusterTask_ACTIVE_TASK, ClusterTask_RETIRED_TASK)
				self.raiseFailure(TaskCompletionException(self.pendingtasks, self.tasks[ClusterTask_RETIRED_TASK], self.tasks[ClusterTask_COMPLETED_TASK], msg = "The task %s failed." % task.getName()))
				return False
		
		# Complete tasks
		retiredTasks = self.tasks[ClusterTask_RETIRED_TASK][:]
		for task in retiredTasks:
			dependents = task.getDependents()
			completed = True
			for dependent in dependents:
				if dependent.getState() != ClusterTask_COMPLETED_TASK:
					completed = False
					break
			if completed:
				completed = task.complete()
				if completed:
					self._movequeue(task, ClusterTask_RETIRED_TASK, ClusterTask_COMPLETED_TASK)
				else:
					self.raiseFailure(TaskCompletionException(self.pendingtasks, self.tasks[ClusterTask_RETIRED_TASK], self.tasks[ClusterTask_COMPLETED_TASK], msg = "The task %s failed." % task.getName()))
			
			# Try to start any dependents if we can
			# A dependent *should* fire once all its prerequisite tasks have finished
			dependents = task.getDependents()
			for dependent in dependents:
				assert(task.jobIDs == dependent.jobIDs)
				if dependent.getState() == ClusterTask_INACTIVE_TASK:
					self.pendingtasks[dependent] = True
					self._status("Starting %s." % dependent.getName())
					for jobID in task.jobIDs:
						dependent.addInputs(jobID, task.getOutputs(jobID, dependent))
					started = dependent.start(self.sgec, self.dbID)
					if started:
						self.tasks_in_order.append(dependent)
						del self.pendingtasks[dependent]
						self.tasks[ClusterTask_ACTIVE_TASK].append(dependent)

		
		# Bad scheduler. No biscuit.
		if self.tasks[ClusterTask_INITIAL_TASK]:
			raise BadSchedulerException(self.pendingtasks, self.tasks[ClusterTask_RETIRED_TASK], self.tasks[ClusterTask_COMPLETED_TASK], msg = "The scheduler has failed.")  
		
		# If we have no more tasks which will trigger other tasks to start i.e. active tasks
		# and we have pending tasks which have not been started, they never will be started.
		# John Hodgman - "Halting problem - solved. You're welcome."
		if self.pendingtasks and not (self.tasks[ClusterTask_ACTIVE_TASK]):
			 raise SchedulerDeadlockException(self.pendingtasks, self.tasks[ClusterTask_RETIRED_TASK], self.tasks[ClusterTask_COMPLETED_TASK])
									
		# We are finished when there are no active or retired tasks
		return not(self.tasks[ClusterTask_ACTIVE_TASK] or self.tasks[ClusterTask_RETIRED_TASK]) 
	
	def cleanup(self):
		tasks = self._getAllTasks()
		for task in tasks:
			task.cleanup()
				

import pprint
class RosettaClusterJob(StatusPrinter):
	
	suffix = "job"
	flatOutputDirectory = False
	name = "Cluster job"
		
	def __init__(self, sgec, parameters, tempdir, targetroot, dldir, testonly = False):
		self.jobIDs = []
		self.jobID = self.parameters.get("ID") or 0
		self._setStatusPrintingParameters(self.jobID, statustype = "job", level = 0, color = "lightpurple")
		self.profiler = SimpleProfiler.SimpleProfiler("%s-%d" % (self.suffix, self.jobID))
		self.parameters = parameters
		self.sgec = sgec
		self.debug = True
		self.tempdir = tempdir
		self.targetroot = targetroot
		self.testonly = testonly
		self.dldir = os.path.join(dldir, parameters["cryptID"])
		if not testonly:
			self._make_workingdir()
			self._make_targetdir()
		else:
			self.workingdir = "/home/oconchus/clustertest110428/rosettawebclustertest/backrub/temp/test" #todo
			self.targetdirectory = "/home/oconchus/clustertest110428/rosettawebclustertest/backrub/temp/test"
		self.filename_stdout = "stdout_%s_%d.txt" % (self.suffix, self.jobID)
		self.filename_stderr = "stderr_%s_%d.txt" % (self.suffix, self.jobID)
		self.profiler.PROFILE_START("Initialization")
		self._initialize()
		self.profiler.PROFILE_STOP("Initialization")
		self.failed = False
		self.error = None
		self.resultFilemasks = []
		self._defineOutputFiles()
	
	def describe(self):
		self._status("Name: %s" % self.name)
		self._status("Working directory: %s" % self.workingdir)
		self._status("Target directory: %s" % self.targetdirectory)	
		self._status("Download directory: %s" % self.dldir)	
		
	def _defineOutputFiles(self):
		pass
	
	def _initialize(self):
		'''Override this function.'''
		raise Exception
	
	def start(self):
		try:
			self.scheduler.start(self.sgec, self.jobID)
			self.dumpJITGraph()
		except TaskSchedulerException, e:
			self.error = "The job failed during startup"
			self.failed = True
			print(e)
	
	def kill(self):
		success = True
		
		# Move the files to the dl directory
		destpath = self.dldir
		self._status("Copying files to %s" % destpath)
		try:
			if os.path.exists(destpath):
				shutil.rmtree(destpath)
			shutil.copytree(self.workingdir, destpath)
		except Exception, e:
			self._status("Error copying files:\n%s\n%s" % (e, traceback.print_exc()))
			success = False   
				
		dirsToDelete = [(self.tempdir, self.workingdir, "working"), (self.targetroot, self.targetdirectory, "target")]
		for dirpair in dirsToDelete:
			# Being a little cautious here
			try:
				commonprefix = os.path.commonprefix([dirpair[0], dirpair[1]])
				if not commonprefix == dirpair[0]:
					self._status("Error: Unexpected common prefix %s found when removing %s directory." % (commonprefix, dirpair[2]))
					raise
				else:
					self._status("Removing %s directory %s." % (dirpair[2], dirpair[1]))
					shutil.rmtree(dirpair[1])
			except Exception, e:
				self._status("Error removing %s directory:\n%s\n%s" % (dirpair[2], e, traceback.print_exc()))
				success = False			
		return self.scheduler.killAllTasks() and success
	
	def isCompleted(self):
		if not self.failed:
			if self.scheduler.step():
				self.scheduler.cleanup()
				#self._status('distutils.dir_util.copy_tree(%s, %s)' % (self.workingdir, self.targetdirectory))
				return True
			else:
				# A little hacky but avoids waiting another cycle if all jobs have completed
				if not(self.scheduler.tasks[ClusterTask_ACTIVE_TASK]):
					if self.scheduler.step():
						self.scheduler.cleanup()
						return True
			return False
		else:
			raise

	def _analyze(self):
		'''Override this function.'''
		raise Exception("Virtual function called where a concrete function is required.")
	
	def getprofileXML(self):
		return SimpleProfiler.listsOfTuplesToXML(self.getprofile())

	def getprofile(self):
		stats = self.profiler.PROFILE_STATS()
		stats.insert(-1, ("scheduler", self.scheduler.getprofile()))
		
		attr = None
		if self.scheduler.hasFailed():
			attr = 'succeeded="false"' 
		else:	
			attr = 'succeeded="true"' 
		
		stats = [('%s %s workingDir="%s" targetDir="%s" downloadsDir="%s"' % (self.suffix, attr, self.workingdir, self.targetdirectory, self.dldir), stats)]
		SimpleProfiler.sumTuples(stats)
		return stats
		
	def analyze(self):
		'''Any final output can be generated here. We assume here that all necessary files have been copied in place.'''
		self.profiler.PROFILE_START("Analysis")
		result = self._analyze()
		self.profiler.PROFILE_STOP("Analysis")
		if not result:
			raise Exception("Analysis failed")
	
	def saveProfile(self):
		contents = "<profile>\n%s</profile>" % self.getprofileXML()
		writeFile(self._targetdir_file_path("timing_profile.txt"), contents)

	def _make_workingdir(self):
		"""Make a single used working directory inside the temporary directory"""
		# make a tempdir on the host
		try:
			self.workingdir = makeTemp755Directory(self.tempdir, self.suffix)
			for jobID in self.jobIDs:
				make755Directory(os.path.join(self.workingdir, str(jobID)))
		except Exception, e:
			# This is a fatal error.
			print("The cluster daemon could not create the working directory inside %s. Are you running it under the correct user?" % self.tempdir)
			os._exit(0)
		return self.workingdir

	def _targetdir_file_path(self, filename):
		"""Get the path for a file within the working directory"""
		return os.path.join(self.targetdirectory, filename)   

	def _make_targetdir(self):
		"""Make a single used target directory inside the target directory"""
		# make a tempdir on the host
		try:
			self.targetdirectory = makeTemp755Directory(self.targetroot, self.suffix) 
			for jobID in self.jobIDs:
				make755Directory(os.path.join(self.targetdirectory, str(jobID)))
		except:
			# This is a fatal error.
			print("The cluster daemon could not create the target directory inside %s. Are you running it under the correct user?" % self.targetroot)
			os._exit(0)
		return self.targetdirectory
	
	def _taskresultsdir_file_path(self, taskdir, filename):
		return os.path.join(self.targetdirectory, taskdir, filename)

	def moveFilesTo(self, permissions = permissions755):
		destpath = self.dldir
		
		self._status("Moving files to %s" % destpath)
			
		if self.resultFilemasks:
			if not os.path.exists(destpath):
				make755Directory(destpath)
			for mask in self.resultFilemasks:
				fromSubdirectory = os.path.join(self.targetdirectory, mask[0])
				toSubdirectory = os.path.join(destpath, mask[0])
				self._status("Moving files from %s to %s using mask (%s, %s)\n" % (fromSubdirectory, toSubdirectory, mask[0], mask[1]))
				if not os.path.exists(toSubdirectory):
					make755Directory(toSubdirectory)
				for file in os.listdir(fromSubdirectory):
					self._status("File: %s" % file, level = 10)
					if fnmatch.fnmatch(file, mask[1]):
						shutil.move(os.path.join(fromSubdirectory, file), toSubdirectory)
						self._status("Moved.", level = 10)
					
		else:
			if os.path.exists(destpath):
				shutil.rmtree(destpath)
			shutil.move(self.targetdirectory, destpath)
		
		os.chmod( destpath, permissions )
		return destpath

	def removeClusterTempDir(self):
		self._status("Deleting working directory %s" % self.workingdir)
		shutil.rmtree(self.workingdir)

	def _appendError(self, errmsg):
		if self.error:
			self.error = "%s\n%s" % (self.error, errmsg)
		else:
			self.error = errmsg
		self._status(errmsg)

	def _make_taskdir(self, dirname, files = []):
		""" Make a subdirectory dirname in the working directory and copy all files into it.
			Filenames should be relative to the working directory."""
		if not self.testonly:
			taskdir = os.path.join(self.workingdir, dirname)
			if not os.path.isdir(taskdir):
				make755Directory(taskdir)
			if not os.path.isdir(taskdir):
				raise os.error
			for file in files:
				shutil.copyfile("%s/%s" % (self.workingdir, file), "%s/%s" % (taskdir, file))
			return taskdir
		return self.workingdir

	def _workingdir_file_path(self, filename, jobID = "."):
		"""Get the path for a file within the working directory"""
		return os.path.normpath(os.path.join(self.workingdir, str(jobID), filename))

	def dumpJITGraph(self):
		destpath = self.dldir
		rootname = os.path.join(destpath, "progress")
		JITjs = "%s.js" % rootname 
		JIThtml = "%s.html" % rootname 
		contents = self.scheduler.getJITGraph()
		if not os.path.exists(destpath):
			make755Directory(destpath)
		writeFile(JITjs, contents[0])
		writeFile(JIThtml, contents[1])
