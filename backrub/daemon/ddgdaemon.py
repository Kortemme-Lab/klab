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
import ddgproject
from rosettahelper import * #RosettaError, get_files, grep, make755Directory, makeTemp755Directory
from RosettaProtocols import *
from cluster import ddgTasks
from cluster.RosettaTasks import PostProcessingException
from conf_daemon import *
from cluster.sge import SGEConnection, SGEXMLPrinter, ClusterException

dbfields = ddgproject.FieldNames()
class ddGDaemon(RosettaDaemon):
	#todo: daemon adds self.parameters[dbfields.ExtraParameters] to dict
		
	MaxClusterJobs	= 200
	logfname		= "ddGDaemon.log"
	pidfile			= settings["ddGPID"]
	
	def __init__(self, stdout, stderr):
		
		super(RosettaDaemon, self).__init__(self.pidfile, settings, stdout = stdout, stderr = stderr)
		self.configure()
		self.logfile = os.path.join(self.rosetta_tmp, self.logfname)
		self.sgec = SGEConnection()
		self._clusterjobjuststarted = None
		
		# Maintain a list of recent DB jobs started. This is to avoid any logical errors which 
		# would repeatedly start a job and spam the cluster. This should never happen but let's be cautious. 
		self.recentDBJobs = []				  
		
		if not os.path.exists(netappRoot):
			make755Directory(netappRoot)
		if not os.path.exists(cluster_temp):
			make755Directory(cluster_temp)
	
	def __del__(self):
		self.DBConnection.close()
		
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
		self.DBConnection		= ddgproject.ddGDatabase(passwd = passwd)
		self.PredictionDBConnection		= ddgproject.ddGPredictionDataDatabase(passwd = passwd)
	
	def callproc(self, procname, parameters = None, cursorClass = ddgproject.DictCursor):
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
			self.log("%s." % e)
			self.log(traceback.format_exc())
			raise Exception()
		return results

	def runSQL(self, query, parameters = None, cursorClass = ddgproject.DictCursor):
		""" This function should be the only place in this class which executes SQL.
			Previously, bugs were introduced by copy and pasting and executing the wrong SQL commands (stored as strings in copy and pasted variables).
			Using this function and passing the string in reduces the likelihood of these errors.
			It also allows us to log all executed SQL here if we wish.
			We use DictCursor by default for this class.
			""" 
		if self.logSQL:
			self.log("SQL: %s." % query)
		results = []
		try: # 	TODO: check if try in old function
			results = self.DBConnection.execute(query, parameters, cursorClass)
			
		except Exception, e:
			self.log("%s." % e)
			self.log(traceback.format_exc())
			raise Exception()
		return results
	
	def recordSuccessfulJob(self, clusterjob):
		jobID = clusterjob.jobID		
		ddG = pickle.dumps(clusterjob.getddG())
		self.runSQL('UPDATE Prediction SET Status="done", ddG=%s, NumberOfMeasurements=1, EndDate=NOW() WHERE ID=%s', 
				parameters = (ddG, jobID))
						
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
			self.log(_traceback)
			self.log(_exception)
			self.runSQL('''UPDATE Prediction SET Status='failed', Errors=%s, EndDate=NOW() WHERE ID=%s''', parameters = ("%s. %s. %s. %s." % (timestamp, errormsg, str(_traceback), str(_exception)), jobID))
		else:
			print("FAILED")
			self.runSQL('''UPDATE Prediction SET Status='failed', Errors=%s, EndDate=NOW() WHERE ID=%s''', parameters = ("%s. %s" % (errormsg, timestamp), jobID))
		self.log("Error: The %s job %d failed at some point:\n%s" % (suffix, jobID, errormsg))
		self.notifyAdminOfError(jobID, description = "ddG")
		
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
					clusterjob.analyze()
					
					self.end_job(clusterjob)
					clusterjob.dumpJITGraph()
					
					print("<profile>")
					print(clusterjob.getprofileXML())
					print("</profile>")
																		   
			except RosettaTasks.PostProcessingException, e:
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
		results = self.runSQL('SELECT ID from Prediction WHERE AdminCommand="restart" ORDER BY EntryDate', cursorClass = ddgproject.DictCursor)
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
		
		params["ProtocolGraph"] = ProtocolGraph
		params["InitialTasks"] = InitialTasks
		params["CommandParameters"] = CommandParameters
						
	def startNewJobs(self):
		# Start more jobs
		newclusterjob = None
		if len(self.runningJobs) < self.MaxClusterJobs:
			# get all jobs in queue
			#results = self.runSQL("SELECT Prediction.ID as ID, StrippedPDB, InputFiles, cryptID, Tool.Name AS ToolName, Tool.Version AS ToolVersion, Tool.SVNRevision AS ToolSVNRevision, Command.Type AS CommandType, Command.Command as Command, Command.Description as Description FROM Prediction INNER JOIN Tool ON Prediction.ToolID=Tool.ID INNER JOIN Command ON Prediction.CommandID=Command.ID WHERE Prediction.Status='%(queued)s' ORDER BY EntryDate" % dbfields)

			results = self.runSQL("SELECT %(Prediction)s.%(ID)s as ID, %(Experiment)s.%(ID)s as ExperimentID, %(Experiment)s.%(Structure)s as PDB_ID, %(ResidueMapping)s, %(StrippedPDB)s, %(InputFiles)s, %(CryptID)s, %(Protocol)s.%(ID)s AS ProtocolID, %(Protocol)s.%(Description)s AS Description FROM %(Prediction)s INNER JOIN %(Protocol)s ON %(Prediction)s.%(ProtocolID)s=%(Protocol)s.%(ID)s INNER JOIN %(Experiment)s ON %(Prediction)s.%(ExperimentID)s=%(Experiment)s.%(ID)s WHERE %(Prediction)s.%(Status)s='%(queued)s' ORDER BY %(EntryDate)s" % dbfields)
			try:
				if len(results) != 0:
					jobID = None
					for params in results:
						# Set up the parameters. We assume ProtocolParameters keys do not overlap with params.
						jobID = params["ID"]
						params["ResidueMapping"] = pickle.loads(params["ResidueMapping"])
						params["InputFiles"] = pickle.loads(params["InputFiles"])
						self.addProtocolStructureToParameters(params, params["ProtocolID"])
						
						# Remember that we are about to start this job to avoid repeatedly submitting the same job to the cluster
						# This should not happen but just in case.
						# Also, never let the list grow too large as the daemon should be able to run a long time						
						self.log("Starting job %(ID)d (%(ProtocolID)s)." % params)
						if jobID in self.recentDBJobs:
							self.log("Error: Trying to run database job %d multiple times." % jobID)
							raise Exception("Trying to run database job %d multiple times")
						self.recentDBJobs.append(jobID)
						if len(self.recentDBJobs) > 400:
							self.recentDBJobs = self.recentDBJobs[200:]
						
						# Start the job						
						newclusterjob = self.start_job(params)
						if newclusterjob:
							#change status and write start time to DB
							self.runningJobs.append(newclusterjob)
							self.runSQL("UPDATE Prediction SET Status='active', StartDate=NOW() WHERE ID=%s", parameters = (jobID,))
																						
						if len(self.runningJobs) >= self.MaxClusterJobs:
							break
						
			except ClusterException, e:
				newclusterjob = newclusterjob or self._clusterjobjuststarted
				self._clusterjobjuststarted = None
				self.log("Error: startNewJobs()\nTraceback:''%s''" % traceback.format_exc())
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
				self.log("Error: startNewJobs()\nTraceback:''%s''" % traceback.format_exc())
				if newclusterjob:
					newclusterjob.kill()
					self.recordErrorInJob(newclusterjob, "Error starting job.", traceback.format_exc(), e)
					if newclusterjob in self.runningJobs:
						self.runningJobs.remove(newclusterjob)
				else:
					self.recordErrorInJob(None, "Error starting job.", traceback.format_exc(), e, jobID)
									 
			self._clusterjobjuststarted = None

	def start_job(self, params):

		clusterjob = None
		jobID = params["ID"]
		
		# Leave the results for remote jobs in a different directory 
		dldir = cluster_ddGdir
			
		self.log("Start new job ID = %s. %s" % (jobID, params["Description"]) )
		clusterjob = ddgTasks.ddGK16Job(self.sgec, params, netappRoot, cluster_temp, dldir) # todo: generalise to different classes   
						
		# clusterjob will not be returned on exception and the reference will be lost
		self._clusterjobjuststarted = clusterjob 
		
		# Remove any old files in the same target location
		destpath = os.path.join(clusterjob.dldir, params["cryptID"])
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
			self.log("moveFilesOnJobCompletion failure. Error moving files to the download directory.")
			self.log("%s\n%s" % (str(e), traceback.print_exc()))		
	
	def copyAndZipOutputFiles(self, clusterjob):
			
		ID = clusterjob.jobID						
		
		# move the data to a webserver accessible directory 
		result_dir = self.moveFilesOnJobCompletion(clusterjob)
		
		# remember directory
		current_dir = os.getcwd()
		os.chdir(result_dir)
		
		# let's remove all empty files to not confuse the user
		self.exec_cmd('find . -size 0 -exec rm {} \";\"', result_dir)
		
		# store all files also in a zip file, to make it easier accessible
		filename_zip = "data_%s.zip" % ( ID )
		all_output = zipfile.ZipFile(filename_zip, 'w', zipfile.ZIP_DEFLATED)
		abs_files = get_files('./')
		
		# Do not include the timing profile in the zip
		timingprofile = os.path.join(result_dir, "timing_profile.txt")
		if timingprofile in abs_files:
			abs_files.remove(timingprofile)
			
		os.chdir(result_dir)
		filenames_for_zip = [ string.replace(fn, os.getcwd()+'/','') for fn in abs_files ] # os.listdir(result_dir)
								
		for file in filenames_for_zip:
			if file != filename_zip:
				all_output.write( file )
				
		all_output.close()
		
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

		# go back to our working dir 
		os.chdir(current_dir)
	
	def removeClusterTempDir(self, clusterjob):
		try:
			clusterjob.removeClusterTempDir()
		except Exception, e:
			self.log("Error removing the temporary directory on the cluster.")
			self.log("%s\n%s" % (str(e), traceback.print_exc()))		


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
			elif 'test' == sys.argv[1]:
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
				DBConnection = ddgproject.ddGDatabase(passwd = passwd)
				
				# Extract the graph information from the database
				#Kellogg:10.1002/prot.22921:protocol16:32231
				PROTOCOL_ID = "Kellogg:10.1002/prot.22921:protocol16:32231"
				ProtocolGraph = {}
				initialTasks = []
				results = DBConnection.callproc("GetProtocolSteps", parameters = (PROTOCOL_ID,))
				for result in results:
					stepID = result["ProtocolStepID"]
					initialTasks.append(stepID)
					ProtocolGraph[stepID] = result
					ProtocolGraph[stepID]["Dependents"] = []
					ProtocolGraph[stepID]["Parents"] = []
				edges = DBConnection.execute("SELECT FromStep, ToStep FROM ProtocolGraphEdge WHERE ProtocolID=%s", parameters = (PROTOCOL_ID,))
				for e in edges:
					s = e["FromStep"]
					t = e["ToStep"]
					ProtocolGraph[s]["Dependents"].append(t)
					ProtocolGraph[t]["Parents"].append(s)
					if t in initialTasks:
						initialTasks.remove(t)
				CommandParameters = {}
				CmdParameters = DBConnection.execute("SELECT FromStep, ToStep, ParameterID, Filename FROM ProtocolParameter WHERE ProtocolID=%s", parameters = (PROTOCOL_ID,))
				for p in CmdParameters:
					s = p["FromStep"]
					if s < 0:
						s = None
					tpl = (s, p["ToStep"])
					CommandParameters[tpl] = CommandParameters.get(tpl, [])
					CommandParameters[tpl].append((p["ParameterID"], p["Filename"]))
				ddgTasks.test(ProtocolGraph, initialTasks, CommandParameters)
			else:
				printUsageString = True
		
	if printUsageString:
		print "usage: %s start|stop|restart" % sys.argv[0]
	sys.exit(2)

