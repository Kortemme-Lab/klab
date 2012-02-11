#!/usr/bin/python2.4
# encoding: utf-8
"""
ddGClusterScheduler.py

Created by Shane O'Connor 2012.
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
from datetime import datetime

#import sge

from ClusterScheduler import checkGraphReachability, traverseGraph, TaskSchedulerException, SchedulerTaskAddedAfterStartException, BadSchedulerException, TaskCompletionException, SchedulerDeadlockException, SchedulerStartException
from ClusterScheduler import TaskScheduler, RosettaClusterJob 

import SimpleProfiler
from Graph import JITGraph

from rosettahelper import make755Directory, makeTemp755Directory, writeFile, permissions755, permissions775

class ClusterBatchJob(RosettaClusterJob):

	def __init__(self, sgec, parameters, tempdir, targetroot, dldir, testonly = False):
		self.jobIDs = sorted(parameters["jobs"].keys()) # The fact that this is a sorted list is important
		self.jobID = "%s-%s" % (parameters["cryptID"], parameters["ID"])
		self.profiler = SimpleProfiler.SimpleProfiler("%s-%s" % (self.suffix, parameters["ID"]))
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
		self.profiler.PROFILE_START("Initialization")
		self._initialize()
		self.profiler.PROFILE_STOP("Initialization")
		self.failed = False
		self.error = None
		self.resultFilemasks = []
		self._defineOutputFiles()

	def moveFilesTo(self, permissions = permissions755):
		destpath = self.dldir
		
		self._status("Moving files to %s" % destpath)

		if not os.path.exists(destpath):
			make755Directory(destpath)

		for jobID in self.jobIDs:
			destjobpath = os.path.join(destpath, str(jobID))
			targetjobpath = os.path.join(self.targetdirectory, str(jobID))
			if os.path.exists(destjobpath):
				shutil.rmtree(destjobpath)
			make755Directory(destjobpath)
			if self.resultFilemasks:
				for mask in self.resultFilemasks:
					fromSubdirectory = os.path.join(targetjobpath, mask[0])
					toSubdirectory = os.path.join(destjobpath, mask[0])
					self._status("Moving files from %s to %s using mask '%s'.\n" % (fromSubdirectory, toSubdirectory, mask[1]))
					if not os.path.exists(toSubdirectory):
						make755Directory(toSubdirectory)
					for file in os.listdir(fromSubdirectory):
						self._status("File: %s" % file)
						if fnmatch.fnmatch(file, mask[1]):
							try:
								shutil.move(os.path.join(fromSubdirectory, file), toSubdirectory)
								self._status("Moved.")
							except Exception, e:
								self._status("Exception moving %s to %s: %s" % (os.path.join(fromSubdirectory, file), toSubdirectory, str(e)))
			else:
				if os.path.exists(destjobpath):
					shutil.rmtree(destjobpath)
				shutil.move(targetjobpath, destjobpath)

		os.chmod( destpath, permissions )
		return destpath

	def _make_taskdir(self, dirname, files = []):
		""" Make a subdirectory dirname in the working directory and copy all files into it.
			Filenames should be relative to the working directory."""
		if not self.testonly:
			for jobID in self.jobIDs: 
				taskdir = os.path.join(self.workingdir, str(jobID), dirname)
				if not os.path.isdir(taskdir):
					make755Directory(taskdir)
				if not os.path.isdir(taskdir):
					raise os.error
				for file in files:
					shutil.copyfile("%s/%s" % (self.workingdir, file), "%s/%s" % (taskdir, file))
		return self.workingdir
