# Copyright (C) 2011,2012 Shane O'Connor and the Regents of the University of California, San Francisco

import sys
import os
from datetime import datetime
#import pdb
import time
#import string
import pickle
import shutil
import zipfile
import traceback
sys.path.insert(0, "../common/")
#sys.path.insert(1, "cluster")
from rosetta_daemon import RosettaDaemon
from rosettahelper import * #RosettaError, get_files, grep, make755Directory, makeTemp755Directory
from RosettaProtocols import *
from cluster.RosettaTasks import PostProcessingException
from conf_daemon import *
from cluster.sge import SGEConnection, SGEXMLPrinter, ClusterException
from string import join
from statusprinter import StatusPrinter
import rosettadb
import rosettahelper
import klfilesystem
					
import benchmark_kic
import benchmark_kic.jobs as jobs

class KICSettings(object):
	settings = {}
	base_dir = None
	
	def __init__(self, argv, scriptname):
		KIC_directory = "benchmark_kic"
		self.ServerScript = scriptname 
		if argv[0].find("/") != -1:
			self.base_dir = os.path.join(self._getSourceRoot(argv[0]), "daemon", KIC_directory)
		else:
			self.base_dir = os.path.join(self._getSourceRoot(scriptname), "daemon", KIC_directory)
		self._read_config_file()
		self.input_time_format = "%a %b %d %H:%M:%S %Z %Y"
	
	def _read_config_file(self):
		base_dir = self.base_dir
		settings = {}
		settingsFilename = os.path.join(base_dir, "settings.ini")
			
		# Read settings from file
		try:
			lines = rosettahelper.readFileLines(settingsFilename)
			for line in lines:
				if line.strip() and line[0] != '#': # skip comments and empty lines
					# format is: "parameter = value"
					list_data = line.split("=")
					if len(list_data) != 2:
						raise IndexError(list_data)
					settings[list_data[0].strip()] = list_data[1].strip()
		
			# Constant settings
			self.StartingStructuresDirectory = settings['minimized_starting_structures']
			self.LoopsInputDirectory = settings['loop_definitions']
			self.placeholder_image = settings['placeholder_image']
			self.cluster_results_dir = settings['cluster_results_dir']
			self.local_temp_dir = settings['local_temp_dir']
			self.local_results_dir = settings['local_results_dir'] 
			
		except IOError:
			raise Exception("settings.ini could not be found in %s." % base_dir)
			sys.exit(2)

	def _getSourceRoot(self, scriptfilename):
		fe = scriptfilename.find("frontend")
		if fe != -1:
			return scriptfilename[:fe]
		be = scriptfilename.find("daemon")
		if be != -1:
			return scriptfilename[:be]
		raise Exception("Cannot determine source root for %s." % scriptfilename)


class KICDaemon(RosettaDaemon):
	MaxClusterJobs	= 2
	logfname		= "KICDaemon.log"
	pidfile			= settings["benchmarkKICPID"]
	
	def __init__(self, stdout, stderr):
		
		self._setStatusPrintingParameters("_", statustype = "daemon", level = 0, color = "lightgreen")
		super(RosettaDaemon, self).__init__(self.pidfile, settings, stdout = stdout, stderr = stderr)
		self.configure()
		self.logfile = os.path.join(self.rosetta_tmp, self.logfname)
		self.sgec = SGEConnection()
		self._clusterjobjuststarted = None
		if os.environ.get('PWD'):
			self.KICSettings = KICSettings(sys.argv, os.environ['PWD'])
		else:
			self.KICSettings = KICSettings(sys.argv, os.environ['SCRIPT_NAME'])
		self.log("KIC Benchmark daemon")
		
		self.BenchmarkMap = {"KIC" : jobs.KICBenchmarkJob}
		#self.BenchmarkMap = {"KIC" : jobs.KICBenchmarkJobAnalyzer}
		self.BenchmarkSettings = {"KIC" : self.KICSettings}
		
		# Maintain a list of recent DB jobs started. This is to avoid any logical errors which 
		# would repeatedly start a job and spam the cluster. This should never happen but let's be cautious. 
		self.recentDBJobs = []				  
		self.JobsToDBId = {}
		
		if not os.path.exists(netappRoot):
			make755Directory(netappRoot)
		if not os.path.exists(cluster_temp):
			make755Directory(cluster_temp)
		
	def __del__(self):
		if self.DBInterface:
			del self.DBInterface
	
	def runSQL(self, sql, parameters = None, cursorClass = rosettadb.DictCursor):
		""" This function should be the only place in this class which executes SQL.
			Previously, bugs were introduced by copy and pasting and executing the wrong SQL commands (stored as strings in copy and pasted variables).
			Using this function and passing the string in reduces the likelihood of these errors.
			It also allows us to log all executed SQL here if we wish.
			
			We are lock-happy here but SQL performance is not currently an issue daemon-side. 
			""" 
		if self.logSQL:
			if parameters:
				self.log("SQL: %s, parameters = %s" % (sql, parameters))
			else:
				self.log("SQL: %s" % sql)
		results = []
		try:
			return self.DBInterface.locked_execute(sql, parameters, cursorClass)
		except Exception, e:
			raise
		return results

	def configure(self):
		passwd = None
		F = open("../sqlpw", "r")
		while True:
			line = F.readline()
			if line == "":
				break
			else:
				line = line.split("=")
				if line[0].strip() == "WebserverSQLPassword":
					passwd = line[1].strip()
					break
		F.close()
		if not passwd:
			raise Exception("Did not find password.")
		
		settings["SQLPassword"]	= passwd 
		self.email_admin		= settings["AdminEmail"]
		self.server_name		= settings["ServerName"]
		self.base_dir			= settings["BaseDir"]
		self.rosetta_tmp		= settings["TempDir"]
		
		self.DBInterface		= rosettadb.DatabaseInterface(settings, db = "Benchmarks")  # RosettaDB(settings, db = "Benchmarks", numTries = 32)

	def recordSuccessfulJob(self, clusterjob):
		jobID = clusterjob.jobID
		self.runSQL('UPDATE BenchmarkRun SET Status="done", EndDate=NOW() WHERE ID=%s', parameters = (jobID,))
					
	def recordErrorInJob(self, clusterjob, errormsg, _traceback = None, _exception = None, jobID = None):
		suffix = ""
		if clusterjob:
			jobID = clusterjob.jobID
			clusterjob.error = errormsg
			clusterjob.failed = True
			suffix = clusterjob.suffix
		
		timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
		if _traceback and _exception:
			_exception = str(_exception)
			self.log(_traceback, error = True)
			self.log(_exception, error = True)
			self.runSQL('''UPDATE BenchmarkRun SET Status='failed', Errors=%s, EndDate=NOW() WHERE ID=%s''', parameters = ("%s. %s. %s. %s." % (timestamp, errormsg, str(_traceback), str(_exception)), jobID))
		else:
			self.runSQL('''UPDATE BenchmarkRun SET Status='failed', Errors=%s, EndDate=NOW() WHERE ID=%s''', parameters = ("%s. %s" % (errormsg, timestamp), jobID))
		self.log("Error: The %s job %s failed at some point:\n%s" % (suffix, jobID, errormsg), error = True)
	
	def notifyUsersOfCompletedJob(self, clusterjob):
		parameters = clusterjob.parameters 
		if parameters['NotificationEmailAddress']:
			addresses = [address for address in parameters['NotificationEmailAddress'].split(";") if address]
			if addresses:			
				if clusterjob.failed or clusterjob.error:
					subject  = "Kortemme Lab Benchmark Server - %(BenchmarkID)s job #%(ID)d failed" % parameters
					mailTXT = "An error occurred during the job.\n%s" % str(clusterjob.error)
					for address in addresses:
						if not self.sendMail(address, self.email_admin, subject, mailTXT):
							self.log("Error: sendMail() ID = %s." % ID )				 
				else:
					subject  = "Kortemme Lab Benchmark Server - %(BenchmarkID)s job #%(ID)d passed" % parameters
					mailTXT = "The benchmark run completed successfully."
					for address in addresses:
						if not self.sendMail(address, self.email_admin, subject, mailTXT):
							self.log("Error: sendMail() ID = %s." % ID )				 
						
	def run(self):
		"""The main loop and job controller of the daemon."""
		
		self.log("Starting daemon.")
		self.runningJobs = []		   # list of running processes
		sgec = self.sgec
		self.statusprinter = SGEXMLPrinter(sgec)
		self.diffcounter = CLUSTER_printstatusperiod
		
		while True:
			self.writepid()
			self.checkRunningJobs()
			self.restartJobs()
			self.startNewJobs()
			check_cluster = False
			for clusterjob in self.runningJobs:
				if not(clusterjob.testonly):
					check_cluster = True
			if True or check_cluster:
				sgec.qstat(waitForFresh = True) # This should sleep until qstat can be called again
				time.sleep(5)
				self.printStatus()
	
	def checkRunningJobs(self):
		completedJobs = []
		failedjobs = []
		
		# Remove failed jobs from the list
		# Any errors should already have been logged in the database
		for clusterjob in self.runningJobs:
			if clusterjob.failed:
				failedjobs.append(clusterjob)
				self.recordErrorInJob(clusterjob, clusterjob.error)
		for clusterjob in failedjobs:
			self.runningJobs.remove(clusterjob)
				
		# Check if jobs are finished
		for clusterjob in self.runningJobs:
			try:
				jobID = clusterjob.jobID
				clusterjob.dumpJITGraph()
				if clusterjob.isCompleted():
					completedJobs.append(clusterjob)

					if not clusterjob.testonly:
						clusterjob.saveProfile()
					try:
						clusterjob.analyze()
					except Exception, e:
						clusterjob.error = "Analysis failed. %s" % str(e)
						clusterjob.failed = True
						self.log("Analysis failed.")
					
					self.end_job(clusterjob)
					clusterjob.dumpJITGraph()
					
					print("<profile>")
					print(clusterjob.getprofileXML())
					print("</profile>")
																		   
			except PostProcessingException, e:
				self.recordErrorInJob(clusterjob, "Post-processing error.", traceback.format_exc(), e)
				self.end_job(clusterjob, Failed = True)
				clusterjob.dumpJITGraph()
			except ClusterException, e:
				self.recordErrorInJob(clusterjob, "Problem with cluster. Job to be rerun.", traceback.format_exc(), e)
				self.end_job(clusterjob, Failed = True)
				clusterjob.dumpJITGraph()
			except Exception, e:
				self.recordErrorInJob(clusterjob, "Failed.", traceback.format_exc(), e)
				self.end_job(clusterjob, Failed = True)
				clusterjob.dumpJITGraph()
							
		# Remove completed jobs from the list
		for cj in completedJobs:
			self.runningJobs.remove(cj)
	
	def restartJobs(self):
		results = self.runSQL('SELECT ID from BenchmarkRun WHERE AdminCommand="restart" ORDER BY EntryDate', cursorClass = rosettadb.DictCursor)
		for result in results:
			jobID = result["ID"]
			self.runSQL('UPDATE BenchmarkRun SET AdminCommand=NULL, Errors=Null, Status="queued" WHERE ID=%s', parameters = (jobID,))
			# Allow the job to be restarted without error if it was recently run
			if jobID in self.recentDBJobs:
				self.recentDBJobs.remove[jobID]
	
	def startNewJobs(self):
		# Start more jobs
		newclusterjob = None
		
		numRunningJobs = 0
		numRunningJobs = len(self.runningJobs)
		
		#tmpparameters = {
		#	'NumberOfLowestEnergyModelsToConsiderForBestModel'	:	5,
		#	'MaxKICBuildAttempts'								:	1000,
		#	'NumberOfModelsPerPDB'								:	20,
		#	'NumberOfModelsOffset'								:	0,
		#}
		#self.runSQL("UPDATE BenchmarkRun SET BenchmarkOptions=%s WHERE ID=2", parameters = (pickle.dumps(tmpparameters),))
		if numRunningJobs < self.MaxClusterJobs:
			results = self.runSQL("SELECT BenchmarkRun.*, Benchmark.BinaryName AS BinaryName FROM BenchmarkRun INNER JOIN Benchmark ON BenchmarkRun.BenchmarkID=Benchmark.BenchmarkID WHERE BenchmarkRun.Status='queued' ORDER BY EntryDate LIMIT %d" % self.MaxClusterJobs)
			try:
				jobID = None
				if len(results) != 0:
					for parameters in results:
						# Remember that we are about to start this job to avoid repeatedly submitting the same job to the cluster
						# This should not happen but just in case.
						# Also, never let the list grow too large as the daemon should be able to run a long time
						newclusterjob = None
						jobID = parameters["ID"]
						self.log("Starting %s benchmark run with ID %d." % (parameters["BenchmarkID"], jobID))
						if jobID in self.recentDBJobs:
							self.log("Error: Trying to run database job %d multiple times." % jobID, error = True)
							raise Exception("Trying to run database job %d multiple times")
						self.recentDBJobs.append(jobID)
						if len(self.recentDBJobs) > 200:
							self.recentDBJobs = self.recentDBJobs[100:]
						
						# Start the job						
						newclusterjob = self.start_job(parameters)
						if newclusterjob:
							#change status and write start time to DB
							self.runningJobs.append(newclusterjob)
							self.JobsToDBId[newclusterjob] = jobID 
							self.runSQL("UPDATE BenchmarkRun SET Status='active', StartDate=NOW(), EndDate=NULL WHERE ID=%s" % jobID)
				
						if len(self.runningJobs) >= self.MaxClusterJobs:
							break
						
			except ClusterException, e:
				newclusterjob = newclusterjob or self._clusterjobjuststarted
				self._clusterjobjuststarted = None
				self.log("Error: startNewJobs()\nTraceback:''%s''" % traceback.format_exc(), error = True)
				if newclusterjob:
					newclusterjob.kill()
					self.recordErrorInJob(newclusterjob, "Problem with cluster. Job to be rerun.", traceback.format_exc(), e)
					if newclusterjob in self.runningJobs:
						self.runningJobs.remove(newclusterjob)
				else:
					self.recordErrorInJob(None, "Problem with cluster. Job to be rerun.", traceback.format_exc(), e, jobID)
			except Exception, e:
				newclusterjob = newclusterjob or self._clusterjobjuststarted
				self._clusterjobjuststarted = None
				self.log("Error: startNewJobs()\nTraceback:''%s''" % traceback.format_exc(), error = True)
				if newclusterjob:
					newclusterjob.kill()
					self.recordErrorInJob(newclusterjob, "Error starting job.", traceback.format_exc(), e)
					if newclusterjob in self.runningJobs:
						self.runningJobs.remove(newclusterjob)
				else:
					self.recordErrorInJob(None, "Error starting job.", traceback.format_exc(), e, jobID)
									 
			self._clusterjobjuststarted = None

	def start_job(self, parameters):

		clusterjob = None

		self.log("Start new job ID = %(ID)s. %(BenchmarkID)s benchmark." % parameters)
		
		bsettings = self.BenchmarkSettings[parameters["BenchmarkID"]]
		jobclass = self.BenchmarkMap[parameters["BenchmarkID"]]
		
		if not os.path.exists(bsettings.cluster_results_dir):
			rosettahelper.make755Directory(bsettings.cluster_results_dir)
		if not os.path.exists(bsettings.local_results_dir):
			rosettahelper.make755Directory(bsettings.local_results_dir)
		if not os.path.exists(bsettings.local_temp_dir):
			rosettahelper.make755Directory(bsettings.local_temp_dir)
		
		clusterjob = jobclass(self.sgec, parameters, bsettings, bsettings.cluster_results_dir, bsettings.local_temp_dir, bsettings.local_results_dir)
			
		# clusterjob will not be returned on exception and the reference will be lost
		self._clusterjobjuststarted = clusterjob 
		
		# Remove any old files in the same target location
		destpath = os.path.join(bsettings.local_results_dir, str(clusterjob.jobID))
		if os.path.exists(destpath):
			shutil.rmtree(destpath)
		
		# Start the job
		clusterjob.start()
		return clusterjob
	
	def printStatus(self):
		'''Print the status of all jobs.'''
		statusprinter = self.statusprinter
		
		if self.runningJobs:
			someoutput = False
			diff = statusprinter.qdiff()
			
			if False: # For debugging
				sys.stdout.write("\n")
				if self.sgec.CachedList:
					sys.stdout.write(self.sgec.CachedList)
				
			if diff:
				sys.stdout.write("\n")
				self.diffcounter += 1
				if self.diffcounter >= CLUSTER_printstatusperiod:
					# Every x diffs, print a full summary
					summary = statusprinter.summary()
					statusList = statusprinter.statusList()
					if summary:
						sys.stdout.write(summary)
					if statusList:
						sys.stdout.write(statusList)
					self.diffcounter = 0
				sys.stdout.write(diff)
			else:
				# Indicate tick
				sys.stdout.write(".")
		else:
			sys.stdout.write(".")
		sys.stdout.flush()
			
			
	def end_job(self, clusterjob, Failed = False):
		ID = clusterjob.jobID 
				
		try:
			self.copyAndZipOutputFiles(clusterjob)
		except Exception, e:
			self.recordErrorInJob(clusterjob, "Error archiving files.", traceback.format_exc(), e)
		
		try:
			if not Failed:
				# On reflection, it's best to not remove directories of failed jobs so we can figure out what happened.
				pass
				#self.removeClusterTempDir(clusterjob)
		except Exception, e:
			self.recordErrorInJob(clusterjob, "Error removing temporary directory on the cluster", traceback.format_exc(), e)
		
		if not clusterjob.error:
			self.recordSuccessfulJob(clusterjob)

	def moveFilesOnJobCompletion(self, clusterjob):
		try:
			return clusterjob.moveFilesTo()
		except Exception, e:
			self.log("moveFilesOnJobCompletion failure. Error moving files to the download directory.", error = True)
			self.log("%s\n%s" % (str(e), traceback.print_exc()), error = True)		
	
	def copyAndZipOutputFiles(self, clusterjob):
		
		# move the data to a webserver accessible directory 
		result_dir = self.moveFilesOnJobCompletion(clusterjob)
		current_dir = os.getcwd()
		try:
			ID = clusterjob.parameters["ID"]
			
			# Save the output in the database
			existingRecord = self.runSQL('SELECT ID FROM BenchmarkRun WHERE ID=%s', parameters = (ID, ))
			#if existingRecord:
			self.runSQL('UPDATE BenchmarkRun SET PDFReport=%s WHERE ID=%s', parameters = (clusterjob.PDFReport, ID))		
			#else:
			#self.runSQL('INSERT INTO BenchmarkRun (ID, PDFReport) VALUES(%s,%s)', parameters = (ID, clusterjob.PDFReport))
			
			existingRecord = self.runSQL('DELETE FROM BenchmarkRunOutputFile WHERE BenchmarkRunID=%s', parameters = (ID, ))
			for outputFilePath in clusterjob.getOutputFilePaths():
				d = {
					'BenchmarkRunID'	: ID,
					'FileType'			: outputFilePath.filetype, 
					'FileID'			: outputFilePath.fileID,
					'Filename'			: outputFilePath.filename,
					'File'				: rosettahelper.readFile(outputFilePath.path_to_file),
				}
				self.DBInterface.insertDict('BenchmarkRunOutputFile', d)
			
		except Exception, e: 
			os.chdir(current_dir)
			self.log("%s." % e, error = True)
			self.log(traceback.format_exc(), error = True)
			raise Exception("Failed while copying and zipping output files.")

		os.chdir(current_dir)
		
	def removeClusterTempDir(self, clusterjob):
		try:
			clusterjob.removeClusterTempDir()
		except Exception, e:
			self.log("Error removing the temporary directory on the cluster.", error = True)
			self.log("%s\n%s" % (str(e), traceback.print_exc()), error = True)		


if __name__ == "__main__":
	temppath = os.path.join(settings["BaseDir"], 'temp')	
	printUsageString = True
	if len(sys.argv) > 1:
		if len(sys.argv) == 2:
			daemon = KICDaemon(os.path.join(temppath, 'benchmarks-running.log'), os.path.join(temppath, 'benchmarks-running.log'))
			printUsageString = False
			if 'start' == sys.argv[1]:
				daemon.start()
			elif 'stop' == sys.argv[1]:
				daemon.stop()
			elif 'restart' == sys.argv[1]:
				daemon.restart()
			else:
				printUsageString = True
		
	if printUsageString:
		print "usage: %s start|stop|restart" % sys.argv[0]
	sys.exit(2)

