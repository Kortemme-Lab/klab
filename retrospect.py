import os
import re
import datetime
import codecs

# Attributes/flags for Retrospect log lines. 
RETROSPECT_HEADER = 0
RETROSPECT_SUBHEADER = 1
RETROSPECT_EVENT = 2
RETROSPECT_PLAIN = 4
RETROSPECT_UNHANDLED_ERROR = 8
RETROSPECT_WARNING = 16
RETROSPECT_FAIL = 32

# The amount of extra leeway in days to allow before we consider a job to have stopped running
# This value is used by default for the LogReader functions. 
TYPICAL_LAPSE = 1.5

# If you call these functions from multiple scripts, you can use this value to ensure all scripts read the same
# amount of log
DEFAULT_LOG_SIZE = 60 * 1024 * 1024 # Read 60 MB from the end of the log. Change this value to suit

SECONDS_IN_A_DAY = 60 * 60 * 24


class Script(object):
	
	def __init__(self):
		raise Exception("This is an abstract class. Define a concrete derived class.")
	
	def check(self, dateOfLastSuccess):
		raise Exception("This is an abstract class. Define a concrete derived class.")

class SimpleScript(Script):
	
	def __init__(self, allowedLapse):
		self.allowedLapse = allowedLapse
	
	def check(self, dateOfLastSuccess, extralapse):
		lapse = self.getDaysSinceLastSuccess(dateOfLastSuccess) - extralapse
		if lapse > self.allowedLapse:
			return False
		else:
			return True
	
	def getDaysSinceLastSuccess(self, dateOfLastSuccess):
		td = (datetime.datetime.today() - dateOfLastSuccess)
		return td.days + (float(td.seconds) / float(SECONDS_IN_A_DAY))
			
class ExpectedScripts(object):
	
	def __init__(self):
		self.scripts = {}
	
	def add(self, scriptname, script):
		self.scripts[scriptname] = script

	def get(self, scriptname):
		return self.scripts.get(scriptname)

	def checkAll(self):
		result = True
		for k in self.scripts.keys():
			result = self.check(k) and result
	
	def check(self, scriptname, dateOfLastSuccess, criteria):
		return self.scripts[scriptname].check(dateOfLastSuccess, criteria)
				
	def SymmetricDifference(self, scriptnames):
		'''Takes in a set, list, or tuple scriptnames and returns the symmetric difference (as a list)
		of scriptnames and the stored names.'''
		scriptnames = set(scriptnames)
		myscripts = set(self.scripts.keys())
		return list(scriptnames.difference(myscripts).union(myscripts.difference(scriptnames)))


class LogReader(object):
	
	def __init__(self, logfile, expectedScripts, maxchars = DEFAULT_LOG_SIZE):
		'''This function reads up to maxchars of the logfile. 
		   
		   It creates a dict for the object called log which maps job dates to dicts with the keys "script" (jobname),
		   "status" (a number made up from the flags above, "lines" (an array of [line attributes, line] pairs),
		   and "type" (job type e.g. "Restore", "Backup").
		   
		   If also creates a dict called scriptsRun mapping script names to dicts with the keys "status" (a number
		   from the most recent run made up from the flags above), "lastRun" (the date of the most recent run), and
		   "lastSuccess" (the date of the most recent success).
		   
		   Finally, we check whether all scripts in expectedScripts are found and report the missing scripts as
		   failures in scriptsRun. 
		   '''
		
		self.log = None
		self.scriptsRun = None
		self.expectedScripts = expectedScripts
		self.earliestEntry = None
		
		errorStrings = {
			"Script error" : "Script error",
			"Execution incomplete" : "Execution incomplete.",
			"Catalog File invalid/damaged" : "error -2241",
			"Network communication failed" : "error -519",
			"Cannot access volume" : "Can't access volume ",
		}
		warningStrings = {
			"Read error (feature unsupported)" : "error -1012",
			"Read error (unknown)" : "error -39",
			"File/directory not found" : "error -1101",
			"Backup stopped manually" : "error -1201",
			"Transaction already complete" : "error -557", 
		}
		
		# Read in up to maxchars from the file and store in memory
		sz = os.path.getsize(logfile)
		F = codecs.open( logfile, "r", "utf-16" )
		contents = F.read(4)
		if maxchars < sz:
			F.seek(sz - maxchars - 4)
		else:
			maxchars = sz
		contents = F.read(maxchars)
		F.close()
	
		# Remove all nested $[...] sections from the log 
		internalregex = re.compile("\$\[[^[]*?\]") 
		lasts = None
		while contents != lasts:
			lasts = contents
			contents = internalregex.sub("", contents)
		
		# Convert from UTF-16 to ASCII ignoring any conversion errors
		contents = contents.encode('ascii', 'ignore')
			
		# Optional: Remove whitespace from lines 
		contents = re.sub("\n\t+", "\n", contents)
		contents = re.sub("\n\n", "\n", contents)
		contents = re.sub("-\t", "-", contents)
		
		# Entries seem to begin with a plus sign. Skip to the first full entry or use the entire string if no full entry exists.
		# Each element of contents will contain the record for a retrospect event
		contents = contents[contents.find("\n+"):]
		contents = contents.split("\n+")
		if not contents[0]:
			contents = contents[1:]
			
		# After this, each element of contents will contain a list of lines of the record for a retrospect event
		for i in range(len(contents)):
			contents[i] = contents[i].split("\n")
		
		# Regular expressions used to match common strings
		backupJob = re.compile(".*Normal backup using (.*?) at (.*?)/(.*?)/(.*?) (.*?):(.*?) (.M).*")
		scriptJob = re.compile(".*Executing (.*?) at (.*?)/(.*?)/(.*?) (.*?):(.*?) (.M).*")
		restoreJob1 = re.compile(".*Executing (Restore Assistant) .* at (.*?)/(.*?)/(.*?) (.*?):(.*?) (.M).*")
		restoreJob2 = re.compile(".*Restore using Restore Assistant - (.*?) at (.*?)/(.*?)/(.*?) (.*?):(.*?) (.M).*")
		engineStart = re.compile (".*Retrospect version [.\d]+\s*")
		engineStartTime = re.compile(".*(Launched at) (.*?)/(.*?)/(.*?) (.*?):(.*?) (.M).*")
		
		# Parse the log, record by record
		log = {}
		scriptsRun = {}
		for record in contents:
			firstline = record[0]
			type = None
			jobmatch = restoreJob1.match(firstline) or restoreJob2.match(firstline)
			if jobmatch:
				type = "Restore"
			else:
				jobmatch = backupJob.match(firstline) or scriptJob.match(firstline)
				if jobmatch:
					type = "Backup"
				else:
					jobmatch = engineStart.match(firstline)
					if jobmatch:
						type = "Engine start"
						jobmatch = engineStartTime.match(record[1])
			
			# NOTE: If we could not match the record to one of the above types, it is not stored in the log.
			# Instead, we just print out the record for debugging.
			if type and jobmatch:
				record[-1] = record[-1].strip()
	
				# Parse the date
				hour = int(jobmatch.group(5))
				if jobmatch.group(7) == "PM":
					hour = (hour + 12) % 24				
				dt = datetime.datetime(int(jobmatch.group(4)), int(jobmatch.group(2)), int(jobmatch.group(3)), hour, int(jobmatch.group(6)))
				
				# Store the date of the earliest entry
				if not(self.earliestEntry) or dt < self.earliestEntry:
					self.earliestEntry = dt
				
				# rscript is typically the name of the script as assigned in Retrospect 
				rscript = None
				
				# We assign attributes to lines of records. Lines can have multiple attributes. These allow us to format lines appropriately to the user. 
				# The first line of a record is a RETROSPECT_HEADER indicating that it is the title of a job.
				# RETROSPECT_SUBHEADER is used to mark lines which indicate the beginning of a part of the job e.g. "Copying...", "Verifying...", etc.
				# RETROSPECT_EVENT indicates that a line contains log information.
				# RETROSPECT_WARNING indicates that something did not go smoothly but not that a critical error necessarily occurred.
				# RETROSPECT_FAIL indicates that the job failed. 
				# RETROSPECT_UNHANDLED_ERROR indicates that a possible error occurred which this function does not yet handle.
				# RETROSPECT_PLAIN is used for all other lines.
				record[0] = (RETROSPECT_HEADER, firstline.strip() + "\n")
				if type == "Engine start":
					rscript = "Engine start"
					status = RETROSPECT_EVENT
					for i in range(1, len(record)):
						record[i] = (RETROSPECT_EVENT, record[i]) 
				elif type in ["Backup", "Restore"]:
					if type == "Restore":
						rscript = "Restore"
					else:
						rscript = jobmatch.group(1)
					
					
					#Iterate through the lines of a record, setting the attributes of each appropriately
					status = 0
					for i in range(1, len(record)):
						line = record[i]
						
						if line:
							if line[0] == '-':
								record[i] = (RETROSPECT_SUBHEADER, line[1:])
								continue
						
						skipOtherCases = False
						for k, s in warningStrings.iteritems():
							if line.find(s) != -1:
								record[i] = (RETROSPECT_WARNING, line)
								status |= RETROSPECT_WARNING
								skipOtherCases = True
								break
						for k, s in errorStrings.iteritems():
							if line.find(s) != -1:
								# This message does not seem to indicate a failure?
								if line.find("#Script error: no source Media Set specified") == -1:
									record[i] = (RETROSPECT_FAIL, line)
									status |= RETROSPECT_FAIL
									skipOtherCases = True
									break
						if skipOtherCases:
							continue
						
						if line.find("error -") != -1:
							# Unhandled error
							record[i] = (RETROSPECT_UNHANDLED_ERROR, line)
							status |= RETROSPECT_UNHANDLED_ERROR	
						else:
							record[i] = (RETROSPECT_PLAIN, line)
							status |= RETROSPECT_PLAIN	
					
					# We index jobs by date which are not necessarily unique. This is a hack to avoid throwing 
					# away records in case multiple jobs are started simultaneously
					while log.get(dt):
						dt = dt + datetime.timedelta(0, 1)
				
				# Store the record
				log[dt] = {
					"script"	: rscript,
					"status"	: status,
					"lines"		: record, 
					"type"		: type, 
				}
				
				lastSuccess = None
				success = False
				if not(status & RETROSPECT_FAIL):
					success = True
					lastSuccess = dt
				
				# Record the most recent successful date and/or the most recent run of a particular script
				if scriptsRun.get(rscript):
					data = scriptsRun[rscript]
					if success:
						if not(data["lastSuccess"]) or (dt > data["lastSuccess"]):
							data["lastSuccess"] = dt
					if dt > data["lastRun"]:
						data["lastRun"] = dt
						data["status"] = status
				else:
					scriptsRun[rscript] = {"status" : status, "lastRun" : dt, "lastSuccess" : lastSuccess} 
				
			else:
				# Not pretty but it will be displayed pretty obviously
				print(join(record,"<br>") + "<br><br>")
		
		# Check against expected scripts
		missingScripts = expectedScripts.SymmetricDifference(scriptsRun.keys())
		
		# NOTE: We ignore these special script types. This list is probably not comprehensive and so may need to be added to.
		for t in ['Kortemme (offsite)', 'Ming', 'Ming (offsite)', 'Restore', 'Grooming', 'Engine start', 'Rebuild', 'Retrieve Snapshot']:
			if t in missingScripts:
				missingScripts.remove(t)
				del scriptsRun[t]
		for ms in missingScripts:
			scriptsRun[ms] = {"status" : RETROSPECT_FAIL, "lastRun" : None, "lastSuccess" : None} 
			
		self.log = log
		self.scriptsRun = scriptsRun
	
	def getFailedJobIDs(self, extraLapse = TYPICAL_LAPSE):
		'''Returns a list of which identify failed jobs in the scriptsRun table.
			If a time stamp for a job can be found, we return this. The time stamp can be used to index the log.
			If no time stamp was found, return the name of the script instead.
		''' 
		scriptsRun = self.scriptsRun
		
		failedJobTimestamps = []
		nodata = []
		for name, details in sorted(scriptsRun.iteritems()):
			if details["lastSuccess"] and expectedScripts.get(name):
				if not expectedScripts.check(name, details["lastSuccess"], extraLapse): 
					if details["lastRun"]:
						failedJobTimestamps.append(details["lastRun"])
					else:
						nodata.append(name)
					continue
			else:
				if details["lastRun"]:
					failedJobTimestamps.append(details["lastRun"])
				else:
					nodata.append(name)
				continue
			
			if details["status"] & RETROSPECT_FAIL:
				failedJobTimestamps.append(details["lastRun"])
			elif details["status"] & RETROSPECT_WARNING:
				failedJobTimestamps.append(details["lastRun"])
		
		return failedJobTimestamps, nodata
	
	def generateSummary(self, extraLapse = TYPICAL_LAPSE):
		'''Generates a summary of the status of the expected scripts broken based on the log.
			This summary (a list of strings) is returned as well as a list with the dates (which
			can be used to index the log)of the most recent attempts at the failed jobs. 
		'''
		scriptsRun = self.scriptsRun
		
		body = []
		
		numberOfFailed = 0
		numberWithWarnings = 0
		failedList = []
		successList = []
		warningsList = []
		
		for name, details in sorted(scriptsRun.iteritems()):
			status = None
			daysSinceSuccess = None
			
			if details["lastSuccess"] and expectedScripts.get(name):
				daysSinceSuccess = expectedScripts.get(name).getDaysSinceLastSuccess(details["lastSuccess"])
				if not expectedScripts.check(name, details["lastSuccess"], extraLapse): 
					status = "FAILED"
			else:
				status = "FAILED"
			
			if not status:
				if details["status"] & RETROSPECT_FAIL:
					status = "FAILED"
				elif details["status"] & RETROSPECT_WARNING:
					status = "WARNINGS"
				elif status != "FAILED":
					status = "OK"
			
			if details["lastSuccess"] and daysSinceSuccess:
				lastSuccessDetails = "Last successful run on %s (%0.1f days ago)" % (details["lastSuccess"], daysSinceSuccess)
			else:
				lastSuccessDetails = "No recent successful run."
			
			if details["lastRun"]:
				lastRunDetails = "Last run on %s (%s)" % (details["lastRun"], status)
			else:
				lastRunDetails = "No recent run (%s)" % status
				 
			if status == "FAILED":
				numberOfFailed += 1
				failedList.append("%s: %s. %s" % (name, lastRunDetails, lastSuccessDetails))
			elif status == "WARNINGS":
				numberWithWarnings += 1
				warningsList.append("%s: %s. %s" % (name, lastRunDetails, lastSuccessDetails))
			else:
				successList.append("%s: %s. %s" % (name, lastRunDetails, lastSuccessDetails))
		
		body = []
		if failedList:
			body.append("FAILED JOBS (%d)" % numberOfFailed)
			body.append("****************")
			for j in failedList:
				body.append(j)
			body.append("\n")
		if warningsList:
			body.append("JOBS WITH WARNINGS (%d)" % numberWithWarnings)
			body.append("***********************")
			for j in warningsList:
				body.append(j)
			body.append("\n")
		if successList:
			body.append("SUCCESSFUL JOBS")
			body.append("***************")
			for j in successList:
				body.append(j)
		
		return body, failedList
	
	def createAnchorID(self, scriptname, date):
		'''This creates a string to be used in an anchor (<a>) HTML tag.'''
		return ("%s%s" % (scriptname, str(date))).replace(" ","")
	
	def generateSummaryHTMLTable(self, extraLapse = TYPICAL_LAPSE):
		'''Generates a summary in HTML of the status of the expected scripts broken based on the log.
			This summary is returned as a list of strings. 
		'''
		scriptsRun = self.scriptsRun
		
		html = []
		html.append("<table style='text-align:center;border:1px solid black;margin-left: auto;margin-right: auto;'>\n") # Start summary table
		html.append('	<tr><td colspan="4" style="text-align:center"></td></tr>\n')
		html.append('	<tr style="font-weight:bold;background-color:#cccccc;text-align:center"><td>Script</td><td>Last status</td><td>Last run</td><td>Last success</td></tr>\n')
		
		# Alternate shades between rows
		tablestyle = ['background-color:#33dd33;', 'background-color:#33ff33;']
		warningstyle = ['background-color:#EA8737;', 'background-color:#f5b767;']
		failstyle = ['background-color:#dd3333;', 'background-color:#ff3333;']
		
		count = 0
		for name, details in sorted(scriptsRun.iteritems()):
			status = None
			
			rowstyle = tablestyle[count % 2]
			if details["lastSuccess"] and expectedScripts.get(name):
				if not expectedScripts.check(name, details["lastSuccess"], extraLapse): 
					status = "STOPPED"
			else:
				rowstyle = failstyle[count % 2]
				status = "FAIL"
				
			laststatusstyle = tablestyle[count % 2]
			if details["status"] & RETROSPECT_FAIL:
				laststatusstyle = failstyle[count % 2]
				status = "FAIL"
			elif status != "STOPPED" and details["status"] & RETROSPECT_WARNING:
				laststatusstyle = warningstyle[count % 2]
				status = "WARNINGS"
			elif status != "FAIL" and status != "STOPPED":
				status = "OK"
				
			# Start a row	
			html.append('<tr style="text-align:left;%s">\n' % rowstyle)
			
			# Script name field
			if status == "STOPPED":
				html.append('\t<td style="%s">%s</td>\n' % (failstyle[count % 2], name))
			else:
				html.append('\t<td style="%s">%s</td>' % (tablestyle[count % 2], name))
			
				
			# Last status field
			if details["lastRun"]:
				if status == "STOPPED":
					html.append('\t<td style="%s"><a href="#%s">%s</a></td>\n' % (failstyle[count % 2], self.createAnchorID(name, details["lastRun"]), status))
				else:
					html.append('\t<td style="%s"><a href="#%s">%s</a></td>\n' % (laststatusstyle, self.createAnchorID(name, details["lastRun"]), status))
			else:
				html.append('\t<td style="%s">%s</td>\n' % (laststatusstyle, status))
			
			# Last run field
			if details["lastRun"]:
				html.append('\t<td style="%s"><a href="#%s">%s</a></td>\n' % (laststatusstyle, self.createAnchorID(name, details["lastRun"]), details["lastRun"]))
			else:
				html.append('\t<td style="%s">none found</td>\n' % laststatusstyle)
			
			# Last success field
			if details["lastSuccess"]:
				html.append('\t<td><a href="#%s">%s</a></td>\n' % (self.createAnchorID(name, details["lastSuccess"]), details["lastSuccess"]))
			else:
				html.append('\t<td>none found</td>\n')
			html.append('</tr>\n')
			count += 1
		html.append("</table>")
		return html

	# ACCESSORS
	def getLog(self):
		return self.log
	
	def getEarliestEntry(self):
		return self.earliestEntry
# End of class

# Add script names (e.g. "MyPC") expected to run daily here 
expectedScripts = ExpectedScripts()
for s in []:
	expectedScripts.add(s, SimpleScript(1))
# Add script names (e.g. "EveryoneElsesPC") expected to run weekly here 
for s in []:
	expectedScripts.add(s, SimpleScript(7))

	
# Private
for s in ["kortemme-cd", "kortemme-fplc", "kortemme-hplc", "kortemme-spec",
		"kortemmelab-admin", "kortemmelab-data", "kortemmelab-home", "kortemmelab-shared",
		"AmelieStein", "Bobal", "Kortemme", "Lab Admin", 
		"Epona", "Ganon", "Web Server", "Workstations"]:
	expectedScripts.add(s, SimpleScript(1))
for s in ["kortemme-cd (offsite)", "kortemme-fplc (offsite)", "kortemme-hplc (offsite)", "kortemme-spec (offsite)",
		"kortemmelab-alumni-data", "kortemmelab-alumni-home", "kortemmelab-weekly",
		"AmelieStein (offsite)", "Bobal (offsite)", "Kortemme (offsite backup)", "Lab Admin (offsite)", 
		"Epona (offsite)", "Ganon", "Web Server (offsite)", "Workstations (offsite)"]:
	expectedScripts.add(s, SimpleScript(7))
