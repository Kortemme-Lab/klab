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
#sys.path.insert(1, "cluster")
from rosetta_daemon import RosettaDaemon
sys.path.insert(0, "/clustertest/")
import ddglib.ddgdbapi as ddgdbapi
from rosettahelper import * #RosettaError, get_files, grep, make755Directory, makeTemp755Directory
from RosettaProtocols import *
from cluster.RosettaTasks import PostProcessingException
from conf_daemon import *
from cluster.sge import SGEConnection, SGEXMLPrinter, ClusterException
from string import join
from statusprinter import StatusPrinter

import ddG
from ddG.protocols import *

class ddGDaemon(RosettaDaemon):
		
	MaxBatchSize	= 40
	MaxClusterJobs	= 600
	logfname		= "ddGDaemon.log"
	pidfile			= settings["ddGPID"]
	
	def __init__(self, stdout, stderr):
		
		self._setStatusPrintingParameters("_", statustype = "daemon", level = 0, color = "lightgreen")
		super(RosettaDaemon, self).__init__(self.pidfile, settings, stdout = stdout, stderr = stderr)
		self.configure()
		self.logfile = os.path.join(self.rosetta_tmp, self.logfname)
		self.sgec = SGEConnection()
		self._clusterjobjuststarted = None
		
		# Maintain a list of recent DB jobs started. This is to avoid any logical errors which 
		# would repeatedly start a job and spam the cluster. This should never happen but let's be cautious. 
		self.recentDBJobs = []				  
		self.JobsToDBIds = {}
		
		if not os.path.exists(netappRoot):
			make755Directory(netappRoot)
		if not os.path.exists(cluster_temp):
			make755Directory(cluster_temp)
		
	def __del__(self):
		pass
		#self.DBConnection.close()
		
	def configure(self):
		passwd = None
		F = open("../sqlpw", "r")
		while True:
			line = F.readline()
			if line == "":
				break
			else:
				line = line.split("=")
				if line[0].strip() == "ddGSQLPassword":
					passwd = line[1].strip()
					break
		F.close()
		if not passwd:
			raise Exception("Did not find password.")
		
		settings["SQLPassword"]		= passwd 
		self.email_admin		= settings["AdminEmail"]
		self.server_name		= settings["ServerName"]
		self.base_dir			= settings["BaseDir"]
		self.rosetta_tmp		= settings["TempDir"]
		self.rosetta_dl			= settings["DownloadDir"]
		self.store_time			= settings["StoreTime"]
		self.DBConnection		= ddgdbapi.ddGDatabase(passwd = passwd)
		self.PredictionDBConnection		= ddgdbapi.ddGPredictionDataDatabase(passwd = passwd)
		self.setUpProtocolMap()

	def setUpProtocolMap(self):
		ProtocolMap = {}
		for r in self.runSQL("SELECT ID, ClassName FROM Protocol"):
			jobclass = r["ClassName"]
			if jobclass:
				m_parts = jobclass.split(".")
				jobclass = globals()[m_parts[0]]
				for i in range(1, len(m_parts)):
					jobclass = getattr(jobclass, m_parts[i])
				ProtocolMap[r["ID"]] = jobclass
		self.ProtocolMap = ProtocolMap
		
	def callproc(self, procname, parameters = None, cursorClass = ddgdbapi.DictCursor):
		""" This function should be the only place in this class which calls stored procedures SQL.
			Previously, bugs were introduced by copy and pasting and executing the wrong SQL commands (stored as strings in copy and pasted variables).
			Using this function and passing the string in reduces the likelihood of these errors.
			It also allows us to log all executed procedures here if we wish.
			We use DictCursor by default for this class.
			""" 
		if self.logSQL:
			self.log("SQL: %s(%s)." % (procname, str(parameters)))
		results = []
		try: # 	TODO: check if try in old function
			results = self.DBConnection.callproc(procname, parameters, cursorClass)
			
		except Exception, e:
			self.log("%s." % e, error = True)
			self.log(traceback.format_exc(), error = True)
			raise Exception()
		return results

	def runSQL(self, query, parameters = None, cursorClass = ddgdbapi.DictCursor):
		""" This function should be the only place in this class which executes SQL.
			Previously, bugs were introduced by copy and pasting and executing the wrong SQL commands (stored as strings in copy and pasted variables).
			Using this function and passing the string in reduces the likelihood of these errors.
			It also allows us to log all executed SQL here if we wish.
			We use DictCursor by default for this class.
			""" 
		if self.logSQL:
			if parameters:
				self.log("SQL: %s, parameters = %s" % (query, parameters))
			else:
				self.log("SQL: %s" % query)
		results = []
		try: # 	TODO: check if try in old function
			results = self.DBConnection.execute(query, parameters, cursorClass)
			
		except Exception, e:
			self.log("%s." % e, error = True)
			self.log(traceback.format_exc(), error = True)
			raise Exception()
		return results
	
	def recordSuccessfulJob(self, clusterjob):
		for ID in clusterjob.jobIDs:
			if ID in clusterjob.failedIDs:
				self.runSQL('UPDATE Prediction SET Status="failed", Errors="Analysis", EndDate=NOW() WHERE ID=%s', parameters = (ID,)) 
			else:
				ddG = pickle.dumps(clusterjob.getddG(ID))
				self.runSQL('UPDATE Prediction SET Status="done", ddG=%s, NumberOfMeasurements=1, EndDate=NOW() WHERE ID=%s', parameters = (ddG, ID))
						
	def recordErrorInJob(self, clusterjob, errormsg, _traceback = None, _exception = None, jobID = None):
		suffix = ""
		if clusterjob:
			jobID = clusterjob.jobID
			clusterjob.error = errormsg
			clusterjob.failed = True
			suffix = clusterjob.suffix
		
		timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
		if _traceback and _exception:
			print("FAILED")
			_exception = str(_exception)
			self.log(_traceback, error = True)
			self.log(_exception, error = True)
			self.log("clusterjob is %s" % str(clusterjob))
			self.log("self.JobsToDBIds.get(clusterjob) = %s" % str(self.JobsToDBIds.get(clusterjob)))
			self.runSQL('''UPDATE Prediction SET Status='failed', Errors=%s, EndDate=NOW() ''' + ('WHERE ID IN (%s)' % self.JobsToDBIds[clusterjob]), parameters = ("%s. %s. %s. %s." % (timestamp, errormsg, str(_traceback), str(_exception))))
		else:
			print("FAILED")
			self.runSQL('''UPDATE Prediction SET Status='failed', Errors=%s, EndDate=NOW() ''' + ('WHERE ID IN (%s)' % self.JobsToDBIds[clusterjob]), parameters = ("%s. %s" % (errormsg, timestamp)))
		self.log("Error: The %s job %s failed at some point:\n%s" % (suffix, jobID, errormsg), error = True)
		#todo: enable this self.notifyAdminOfError(jobID, description = "ddG")
		
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

					clusterjob.saveProfile()
					try:
						clusterjob.analyze()
					except Exception:
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
		results = self.runSQL('SELECT ID from Prediction WHERE AdminCommand="restart" ORDER BY EntryDate', cursorClass = ddgdbapi.DictCursor)
		for result in results:
			jobID = result["ID"]
			self.runSQL('UPDATE Prediction SET AdminCommand=NULL, Errors=Null, Status="queued" WHERE ID=%s', parameters = (jobID,))
			# Allow the job to be restarted without error if it was recently run
			if jobID in self.recentDBJobs:
				self.recentDBJobs.remove[jobID]
	
	def addProtocolStructureToParameters(self, params, PROTOCOL_ID):
		#Kellogg:10.1002/prot.22921:protocol16:32231
		#PROTOCOL_ID = "Kellogg:10.1002/prot.22921:protocol16:32231"
		#PROTOCOL_ID = params
		ProtocolGraph = {}
		InitialTasks = []
		results = self.callproc("GetProtocolSteps", parameters = (PROTOCOL_ID,))
		for result in results:
			stepID = result["ProtocolStepID"]
			InitialTasks.append(stepID)
			ProtocolGraph[stepID] = result
			ProtocolGraph[stepID]["Dependents"] = []
			ProtocolGraph[stepID]["Parents"] = []
			ProtocolGraph[stepID]["Cleaners"] = []
		edges = self.runSQL("SELECT FromStep, ToStep FROM ProtocolGraphEdge WHERE ProtocolID=%s", parameters = (PROTOCOL_ID,))
		for e in edges:
			s = e["FromStep"]
			t = e["ToStep"]
			ProtocolGraph[s]["Dependents"].append(t)
			ProtocolGraph[t]["Parents"].append(s)
			if t in InitialTasks:
				InitialTasks.remove(t)
		CommandParameters = {}
		CmdParameters = self.runSQL("SELECT FromStep, ToStep, ParameterID, Value FROM ProtocolParameter WHERE ProtocolID=%s", parameters = (PROTOCOL_ID,))
		for p in CmdParameters:
			s = p["FromStep"]
			if s < 0:
				s = None
			tpl = (s, p["ToStep"])
			CommandParameters[tpl] = CommandParameters.get(tpl, [])
			CommandParameters[tpl].append((p["ParameterID"], p["Value"]))
		for stepID in ProtocolGraph.keys():
			stepCleaners = self.runSQL("SELECT FileMask, Operation, Arguments FROM ProtocolCleaner WHERE ProtocolID=%s AND StepID=%s", parameters = (PROTOCOL_ID, stepID))
			ProtocolGraph[stepID]["Cleaners"] = [{"mask" : cleaner["FileMask"] , "operation" : cleaner["Operation"], "arguments" : cleaner["Arguments"]} for cleaner in stepCleaners]
		
		params["ProtocolGraph"] = ProtocolGraph
		params["InitialTasks"] = InitialTasks
		params["CommandParameters"] = CommandParameters
						
	def startNewJobs(self):
		# Start more jobs
		newclusterjob = None
		MaxBatchSize = self.MaxBatchSize
		
		numRunningJobs = 0
		for job in self.runningJobs:
			numRunningJobs += len(job.jobIDs)
			
		if numRunningJobs < self.MaxClusterJobs:
			batches = {}
			results = self.runSQL("SELECT Prediction.ID as ID, Prediction.PredictionSet as PredictionSet, Experiment.ID as ExperimentID, Experiment.Structure as PDB_ID, ResidueMapping, StrippedPDB, InputFiles, CryptID, Protocol.ID AS ProtocolID, Protocol.Description AS Description FROM Prediction INNER JOIN Protocol ON Prediction.ProtocolID=Protocol.ID INNER JOIN Experiment ON Prediction.ExperimentID=Experiment.ID WHERE Prediction.Status='queued' ORDER BY ProtocolID, EntryDate LIMIT %d" % MaxBatchSize)
			try:
				jobID = None
				if len(results) != 0:
					
					# Create batches of jobs grouped together by protocol and prediction set
					for params in results:
						protocolID = (params["ProtocolID"], params["PredictionSet"])
						if not batches.get(protocolID):
							batches[protocolID] = {}
							batches[protocolID]["jobs"] = {}
							batches[protocolID]["cryptID"] = params["PredictionSet"]
							self.addProtocolStructureToParameters(batches[protocolID], params["ProtocolID"])
						protocol_job_batch = batches[protocolID]["jobs"]
						
						# Set up the parameters. We assume ProtocolParameters keys do not overlap with params.
						jobID = params["ID"]
						params["ResidueMapping"] = pickle.loads(params["ResidueMapping"])
						params["InputFiles"] = pickle.loads(params["InputFiles"])
						
						protocol_job_batch[jobID] = params
						
						
					for protocolID, batchdetails in batches.iteritems():
						# Remember that we are about to start this job to avoid repeatedly submitting the same job to the cluster
						# This should not happen but just in case.
						# Also, never let the list grow too large as the daemon should be able to run a long time
						newclusterjob = None
						jobIDs = sorted(batchdetails["jobs"].keys())
						self.log("Starting jobs with protocol %s: %s" % (protocolID, join(map(str, jobIDs), ",")))
						for jobID in jobIDs:
							if jobID in self.recentDBJobs:
								self.log("Error: Trying to run database job %d multiple times." % jobID, error = True)
								raise Exception("Trying to run database job %d multiple times")
							self.recentDBJobs.append(jobID)
							if len(self.recentDBJobs) > 2000:
								self.recentDBJobs = self.recentDBJobs[1000:]
						
						# Start the job						
						newclusterjob = self.start_job(protocolID[0], batchdetails)
						if newclusterjob:
							#change status and write start time to DB
							self.runningJobs.append(newclusterjob)
							jobs = sorted(batchdetails["jobs"].keys())
							joblist = join(map(str, jobs), ",")
							self.JobsToDBIds[newclusterjob] = joblist 
							self.runSQL("UPDATE Prediction SET Status='active', StartDate=NOW() WHERE ID IN (%s)" % joblist)
				
						numRunningJobs = 0
						for job in self.runningJobs:
							numRunningJobs += len(job.jobIDs)
						if numRunningJobs >= self.MaxClusterJobs:
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
					import colortext
					colortext.error(traceback.format_exc())
					colortext.error(e)
					colortext.error(jobID)
					self.recordErrorInJob(None, "Error starting job.", traceback.format_exc(), e, jobID)
									 
			self._clusterjobjuststarted = None

	def start_job(self, protocolID, batchdetails):

		clusterjob = None
		
		# Leave the results for remote jobs in a different directory 
		dldir = cluster_ddGdir
		
		for jobID in batchdetails["jobs"]:	
			self.log("Start new job ID = %s. %s" % (jobID, batchdetails["jobs"][jobID]["Description"]))
		
		jobclass = self.ProtocolMap[protocolID]
		self.log("Creating job object")
		clusterjob = jobclass(self.sgec, batchdetails, netappRoot, cluster_temp, dldir)
		self.log("Finished job object")
						
		# clusterjob will not be returned on exception and the reference will be lost
		self._clusterjobjuststarted = clusterjob 
		
		# Remove any old files in the same target location
		destpath = os.path.join(clusterjob.dldir, batchdetails["cryptID"])
		if os.path.exists(destpath):
			shutil.rmtree(destpath)
		self.log("Finished removing files")
		
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
			for ID in clusterjob.jobIDs:
				
				# Create the zip file
				os.chdir(result_dir)
				filename_zip = "data_%s.zip" % ( ID )
				all_output = zipfile.ZipFile(filename_zip, 'w', zipfile.ZIP_DEFLATED)
				abs_files = get_files(os.path.join(result_dir, str(ID)))
				os.chdir(result_dir)
				
				filenames_for_zip = [ string.replace(fn, os.getcwd()+'/','') for fn in abs_files ]
				if filename_zip in filenames_for_zip:
					filenames_for_zip.remove(filename_zip)
				for file in filenames_for_zip:
					all_output.write( file )
				all_output.close()

				# Save the zip in the database
				results = self.runSQL('SELECT StoreOutput FROM Prediction WHERE ID=%s', parameters = (ID,))
				if results[0]["StoreOutput"]:
					F = open(os.path.join(result_dir, filename_zip), "rb")
					blob = F.read()
					F.close() 
					existingRecord = self.PredictionDBConnection.execute('SELECT ID FROM PredictionData WHERE ID=%s', parameters = (ID, ))
					# todo: We may need to ask whether we want to overwrite		
					if existingRecord:
						self.PredictionDBConnection.execute('UPDATE PredictionData SET Data=%s WHERE ID=%s', parameters = (blob, ID))		
					else:
						self.PredictionDBConnection.execute('INSERT INTO PredictionData (ID, Data) VALUES(%s,%s)', parameters = (ID, blob))		
		except Exception, e: 
			os.chdir(current_dir)
			self.log("%s." % e, error = True)
			self.log(traceback.format_exc(), error = True)
			raise Exception()

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
			daemon = ddGDaemon(os.path.join(temppath, 'ddgrunning.log'), os.path.join(temppath, 'ddgrunning.log'))
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

