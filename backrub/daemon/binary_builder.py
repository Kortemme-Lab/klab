# Copyright (C) 2011,2012 Shane O'Connor and the Regents of the University of California, San Francisco

import sys
import os
import time
import re
from datetime import datetime
import traceback
sys.path.insert(0, "../common/")
from daemon import Daemon
from conf_daemon import *
from cluster.statusprinter import StatusPrinter
import rosettadb
import klfilesystem
					

email_text_error	= """
Dear administrator,

An error occurred building the binary %(binary_name).

The Kortemme Lab Binary Building Daemon
"""

class BinaryBuilderDaemon(Daemon, StatusPrinter):
	pidfile			= "/tmp/binary_builder.pid"
	logfile			= "/backrub/temp/binary_builder.log"
	build_root		= "/home/oconchus/binarybuilder"
	logSQL			= False
	
	def __init__(self, stdout, stderr):
		self.DBInterface = None
		super(BinaryBuilderDaemon, self).__init__(self.pidfile, settings, stdout = stdout, stderr = stderr)
		self._setStatusPrintingParameters("_", statustype = "daemon", level = 0, color = "lightgreen")
		self.configure()
		# todo: create source checkout root directory here
		if False:
			if not os.path.exists(netappRoot):
				make755Directory(netappRoot)
		
	def __del__(self):
		if self.DBInterface:
			del self.DBInterface
	
	def log(self, s, error = False):
		s = "<daemon time='%s'>%s</daemon>" % (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), s)
		log = open(self.logfile, 'a+')
		log.write(s)
		log.write("\n")
		log.close()

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
		self.DBInterface = rosettadb.DatabaseInterface(settings, db = "LabServices") 
		
	def recordSuccessfulJob(self, buildjob):
		pass
					
	def recordErrorInJob(self, buildjob, errormsg, _traceback = None, _exception = None, jobID = None):
		pass

	def run(self):
		"""The main loop and job controller of the daemon."""
		
		self.log("Starting daemon.")
		self.runningJobs = []		   # list of running processes
		
		while True:
			self.writepid()
			self.checkBinaries()
			self.checkRunningJobs()
			self.startNewJobs()
			time.sleep(60)
		
	def checkBinaries(self):
		account_home = os.path.join("/netapp", "home", "klabqb3backrub")
		rosettaDirectories = []
		subdirs = [subdir for subdir in klfilesystem.getSubdirectories(account_home) if subdir[0] == 'r' and subdir[1:].replace(".", "").isdigit()]
		
		results = self.runSQL('SELECT ID, Tool, VersionType, Version, BuildType, Static, Graphics, MySQL FROM Binaries')
		for record in results:
			dir = "r%(Version)s" % record
			filename = "%(Tool)s_r%(Version)s" % record
			if record['BuildType'] == 'debug':
				filename += "_debug"
			if record['Static']:
				filename += "_static"
			if record['Graphics']:
				filename += "_graphics"
			if record['MySQL']:
				filename += "_mysql"
			if record['Tool'] == "database":
				expectedPath = os.path.join(account_home, dir, "rosetta_database")
			else:
				expectedPath = os.path.join(account_home, dir, filename)
			if not os.path.exists(expectedPath):
				# Remove records with missing associated binaries/databases
				self.runSQL('DELETE FROM Binaries WHERE ID=%s', parameters = (record["ID"],))
					
		for subdir in subdirs:
			for f in os.listdir(os.path.join(account_home, subdir)):
				if f == "rosetta_database":
					details = {
						'Tool'			: "database",
						'VersionType'	: None,
						'Version'	 	: subdir[1:],
						'BuildType'		: "database",
						'Static'		: False,
						'Graphics'		: False,
						'MySQL'			: False,
					}
					
					if details['Version'].isdigit() and details['Version'] > 100:
						details['VersionType'] = 'SVN Revision'
					else:
						details['VersionType'] = 'Release'
					sql = "SELECT ID FROM Binaries WHERE Tool=%s AND VersionType=%s AND Version=%s AND BuildType=%s AND Static=%s AND Graphics=%s AND MySQL=%s"
					parameters = (details["Tool"], details["VersionType"], details["Version"], details["BuildType"], details["Static"], details["Graphics"], details["MySQL"])
					existingRecord = self.runSQL(sql, parameters)
					if not existingRecord:
						self.DBInterface.insertDict("Binaries", details)
				else:				
					m = re.match("^(?P<Tool>.*?)_r(?P<Version>[\d.]+)(?P<BuildType>(_debug)?)(?P<Extras>(_.*)*)$", f)
					if m:
						details = {
							'Tool'			: m.group('Tool'),
							'VersionType'	: None,
							'Version'	 	: m.group('Version'),
							'BuildType'		: m.group('BuildType') or 'release',
							'Static'		: False,
							'Graphics'		: False,
							'MySQL'			: False,
						}
						if ("r%s" % details['Version']) != subdir:
							# VERSION MISMATCH - FILE %s with version %s found in subdirectory %s." % (f, details['Version'], subdir))
							continue
							
						if details['Version'].isdigit() and details['Version'] > 100:
							details['VersionType'] = 'SVN Revision'
						else:
							details['VersionType'] = 'Release'
						extras = [e for e in m.group('Extras').split('_') if e]
						if 'static' in extras:
							details['Static'] = True
							extras.remove('static')
						if 'graphics' in extras:
							details['Graphics'] = True
							extras.remove('graphics')
						if 'mysql' in extras:
							details['MySQL'] = True
							extras.remove('mysql')
						
						# todo: remove these lines when all binaries are consistently named
						if extras:
							if 'unpatched' in extras:
								extras.remove('unpatched')
							if 'alwaysfailed' in extras:
								extras.remove('alwaysfailed')
							if extras:
								self.log("Found unexpected extra build flags: %s" % extras)
								#print("Found unexpected extra build flags: %s" % extras)
						else:
							sql = "SELECT ID FROM Binaries WHERE Tool=%s AND VersionType=%s AND Version=%s AND BuildType=%s AND Static=%s AND Graphics=%s AND MySQL=%s"
							parameters = (details["Tool"], details["VersionType"], details["Version"], details["BuildType"], details["Static"], details["Graphics"], details["MySQL"])
							existingRecord = self.runSQL(sql, parameters)
							if not existingRecord:
								self.DBInterface.insertDict("Binaries", details)
				
			
	def checkRunningJobs(self):
		pass
	
	def startNewJobs(self):
		pass
			
if __name__ == "__main__":
	printUsageString = True
	if len(sys.argv) > 1:
		if len(sys.argv) == 2:
			logfile = "/backrub/temp/binary_builder.run.log"
			daemon = BinaryBuilderDaemon(logfile, logfile)
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

