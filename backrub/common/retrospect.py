import datetime
import codecs
import os, re

RETROSPECT_HEADER = 0
RETROSPECT_SUBHEADER = 1
RETROSPECT_EVENT = 2
RETROSPECT_PLAIN = 4
RETROSPECT_UNHANDLED = 8
RETROSPECT_WARNING = 16
RETROSPECT_FAIL = 32

#'Engine start'
expectedScripts = [
	# Script name, max days allowed since last successful backup
	("kortemme-cd", 1),
	("kortemme-cd (offsite)", 7),
	("kortemme-fplc", 1),
	("kortemme-fplc (offsite)", 7),
	("kortemme-hplc", 1),
	("kortemme-hplc (offsite)", 7),
	("kortemme-spec", 1),
	("kortemme-spec (offsite)", 7),
	("kortemmelab-admin", 1),
	("kortemmelab-data", 1),
	("kortemmelab-home", 1),
	("kortemmelab-alumni-data", 7),
	("kortemmelab-alumni-home", 7),
	("AmelieStein", 1),
	("Bobal", 1),
	("Bobal (offsite)", 7),
	("Epona", 1),
	("Epona (offsite)", 7),
	("Ganon", 1),
	("Kortemme", 1),
	("Kortemme (offsite)", 7),
	("Lab Admin", 1),
	("Lab Admin (offsite)", 7),
	("Web Server", 1),
	("Web Server (offsite)", 7),
	("Workstations", 1),
	("Workstations (offsite)", 7),
]

def readRetrospectLog(logfile, maxchars):
	errorStrings = {
		"Script error" : "Script error",
		"Execution incomplete" : "Execution incomplete.",
		"Catalog File invalid/damaged" : "error -2241",
		"Network communication failed" : "error -519", 
	
	}
	warningStrings = {
		"Read error (feature unsupported)" : "error -1012",
		"Read error (unknown)" : "error -39",
		"File/directory not found" : "error -1101",
		"Backup stopped manually" : "error -1201",
		"Transaction already complete" : "error -557", 
	}
	internalregex = re.compile("\$\[[^[]*?\]") 
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
	contents = contents[contents.find("\n+"):]
	contents = contents.split("\n+")
	if not contents[0]:
		contents = contents[1:]
		
	for i in range(len(contents)):
		contents[i] = contents[i].split("\n")
	backupJob = re.compile(".*Normal backup using (.*?) at (.*?)/(.*?)/(.*?) (.*?):(.*?) (.M).*")
	restoreJob1 = re.compile(".*Executing (Restore Assistant) .* at (.*?)/(.*?)/(.*?) (.*?):(.*?) (.M).*")
	scriptJob = re.compile(".*Executing (.*?) at (.*?)/(.*?)/(.*?) (.*?):(.*?) (.M).*")
	restoreJob2 = re.compile(".*Restore using Restore Assistant - (.*?) at (.*?)/(.*?)/(.*?) (.*?):(.*?) (.M).*")
	engineStart = re.compile (".*Retrospect version [.\d]+\s*")
	engineStartTime = re.compile(".*(Launched at) (.*?)/(.*?)/(.*?) (.*?):(.*?) (.M).*")
			
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

		if type and jobmatch:
			record[-1] = record[-1].strip()

			# Parse the date
			hour = int(jobmatch.group(5))
			if jobmatch.group(7) == "PM":
				hour = (hour + 12) % 24				
			dt = datetime.datetime(int(jobmatch.group(4)), int(jobmatch.group(2)), int(jobmatch.group(3)), hour, int(jobmatch.group(6)))
				
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
				
				
				status = 0
				for i in range(1, len(record)):
					line = record[i]
					
					if line:
						if line[0] == '-':
							record[i] = (RETROSPECT_SUBHEADER, line[1:])
							continue
					
					outercontinue = False
					for k, s in warningStrings.iteritems():
						if line.find(s) != -1:
							record[i] = (RETROSPECT_WARNING, line)
							status |= RETROSPECT_WARNING
							outercontinue = True
							break
					if outercontinue:
						continue
			
					for k, s in errorStrings.iteritems():
						if line.find(s) != -1:
							record[i] = (RETROSPECT_FAIL, line)
							status |= RETROSPECT_FAIL
							outercontinue = True
							break
					if outercontinue:
						continue
					
					if line.find("error -") != -1:
						# Unhandled error
						record[i] = (RETROSPECT_UNHANDLED, line)
						status |= RETROSPECT_UNHANDLED	
					else:
						record[i] = (RETROSPECT_PLAIN, line)
						status |= RETROSPECT_PLAIN	
				
				while log.get(dt):
					dt = dt + datetime.timedelta(0, 1)
				
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
			if scriptsRun.get(rscript):
				data = scriptsRun[rscript]
				# Record the most recent successful date
				if success:
					if not(data["lastSuccess"]) or (dt > data["lastSuccess"]):
						data["lastSuccess"] = dt
				if dt > data["lastRun"]:
					data["lastRun"] = dt
					data["status"] = status
			else:
				scriptsRun[rscript] = {"status" : status, "lastRun" : dt, "lastSuccess" : lastSuccess} 
			
		else:
			print(join(record,"<br>") + "<br><br>")
	
	# Check against expected scripts
	scriptsRead = set(scriptsRun.keys())
	scriptsMaintained = set([es[0] for es in expectedScripts])
	missingScripts = list(scriptsRead.difference(scriptsMaintained).union(scriptsMaintained.difference(scriptsRead)))
	for t in ['Restore', 'Grooming', 'Engine start']:
		if t in missingScripts:
			missingScripts.remove(t)
			del scriptsRun[t]
	for ms in missingScripts:
		scriptsRun[rscript] = {"status" : RETROSPECT_FAIL, "lastRun" : None, "lastSuccess" : None} 
			
	return log, scriptsRun

def getFailedJobs(scriptsRun):
	expectedScriptLastSuccess = {}
	for es in expectedScripts:
		expectedScriptLastSuccess[es[0]] = es[1]
	expectedScriptsNames = expectedScriptLastSuccess.keys()
	
	failedJobTimestamps = []
	for name, details in sorted(scriptsRun.iteritems()):
		if details["lastSuccess"] and (name in expectedScriptLastSuccess.keys()):
			td = (datetime.datetime.today() - details["lastSuccess"])
			days = td.days + (float(td.seconds) / float(60 * 60 * 24))
			if (days > expectedScriptLastSuccess[name] + 1.5): # Allow two days of grace period before indicating failure
				failedJobTimestamps.append(details["lastRun"])
				continue
		else:
			failedJobTimestamps.append(details["lastRun"])
			continue
		
		if details["status"] & RETROSPECT_FAIL:
			failedJobTimestamps.append(details["lastRun"])
		elif details["status"] & RETROSPECT_WARNING:
			failedJobTimestamps.append(details["lastRun"])
	
	return failedJobTimestamps

def generateSummaryHTMLTable(scriptsRun):
	html = []
	html.append("<table style='text-align:center;border:1px solid black;margin-left: auto;margin-right: auto;'>\n") # Start summary table
	html.append('	<tr><td colspan="4" style="text-align:center"></td></tr>\n')
	html.append('	<tr style="font-weight:bold;background-color:#cccccc;text-align:center"><td>Script</td><td>Last status</td><td>Last run</td><td>Last success</td></tr>\n')
	tablestyle = ['background-color:#33dd33;', 'background-color:#33ff33;']
	warningstyle = ['background-color:#EA8737;', 'background-color:#f5b767;']
	failstyle = ['background-color:#dd3333;', 'background-color:#ff3333;']
	count = 0
	
	expectedScriptLastSuccess = {}
	for es in expectedScripts:
		expectedScriptLastSuccess[es[0]] = es[1]
	expectedScriptsNames = expectedScriptLastSuccess.keys()
	
	for name, details in sorted(scriptsRun.iteritems()):
		status = None
		
		rowstyle = tablestyle[count % 2]
		if details["lastSuccess"] and (name in expectedScriptLastSuccess.keys()):
			td = (datetime.datetime.today() - details["lastSuccess"])
			days = td.days + (float(td.seconds) / float(60 * 60 * 24))
			if (days > expectedScriptLastSuccess[name] + 1.5): # Allow two days of grace period before indicating failure
				rowstyle = failstyle[count % 2]		 
				status = "STOPPED"
		else:
			rowstyle = failstyle[count % 2]
			status = "FAIL"
		#
		if details["status"] & RETROSPECT_FAIL:
			laststatusstyle = failstyle[count % 2]
			status = "FAIL"
		elif details["status"] & RETROSPECT_WARNING:
			laststatusstyle = warningstyle[count % 2]
			status = "WARNINGS"
		elif status != "FAIL" and status != "STOPPED":
			laststatusstyle = tablestyle[count % 2]
			status = "OK"
			
		html.append('<tr style="text-align:left;%s">\n' % rowstyle)
		html.append('\t<td>%s</td>\n' % name)
		if details["lastRun"]:
			html.append('\t<td style="%s"><a href="#%s">%s</a></td>\n' % (laststatusstyle, ("%s%s" % (name, str(details["lastRun"]))).replace(" ",""), status))
		else:
			html.append('\t<td style="%s">%s</td>\n' % (laststatusstyle, status))
		if details["lastRun"]:
			html.append('\t<td style="%s"><a href="#%s">%s</a></td>\n' % (laststatusstyle, ("%s%s" % (name, str(details["lastRun"]))).replace(" ",""), details["lastRun"]))
		else:
			html.append('\t<td style="%s">none found</td>\n' % laststatusstyle)
		if details["lastSuccess"]:
			html.append('\t<td><a href="#%s">%s</a></td>\n' % (("%s%s" % (name, str(details["lastSuccess"]))).replace(" ",""), details["lastSuccess"]))
		else:
			html.append('\t<td>none found</td>\n')
		html.append('</tr>\n')
		count += 1
	html.append("</table>")
	return html
