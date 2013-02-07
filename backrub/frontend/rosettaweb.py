#!/usr/bin/python
# -*- coding: iso-8859-15 -*-

# This module functions as a CGI script, parsing the CGI arguments 
# and calling the appropriate functions from the lower levels to
# produce web pages.

# import the basics
import sys, os
# Append document_root to sys.path to be able to find user modulesface

sys.path.insert(0, "..")
sys.path.insert(0, "../common/")
sys.path.insert(1, "../daemon/")
sys.path.insert(2, "../daemon/ddglib")
sys.path.insert(3, "../daemon/cluster/")
import common
import shutil
import sha, time
import cgi
import cgitb
cgitb.enable()
import Cookie

# set Python egg dir MscOSX only
if os.uname()[0] == 'Darwin':
	os.environ['PYTHON_EGG_CACHE'] = '/Applications/XAMPP/xamppfiles/tmp'

import _mysql_exceptions
import socket
import md5
import traceback

import urllib2

import session
from rosettahtml import RosettaHTML
import rosettadb
from rwebhelper import *
from rosettahelper import WebsiteSettings, DEVELOPMENT_HOSTS, DEVELOPER_USERNAMES, make755Directory, writeFile, readBinaryFile
from RosettaProtocols import *
from rosettadatadir import RosettaDataDir

from datetime import datetime, date
from string import *
from cStringIO import StringIO
from cgi import escape

import string
import pickle

# Get IP address and hostname
IP = os.environ['REMOTE_ADDR']
hostname = IP
try:
	hostname = socket.gethostbyaddr(IP)[0]
except:
	pass

###############################################################################################
# Setup: Change these values according to your settings and usage of the server
###############################################################################################

settings = WebsiteSettings(sys.argv, os.environ['SCRIPT_NAME'])

from pdb import PDB
from RosettaTasks import make_seqtol_resfile
if not(settings["LiveWebserver"]):
	import profile 

# open connection to MySQL
DBConnection = None

# Keep a reference to the Apache error stream in case we need to use it for debugging scripts timing out.
apacheerr = sys.stderr
########################################## Setup End ##########################################

# todo: These would be tidier as member elements of a ws class
errors = []
warnings = []

def getKlabDBConnection():
	return rosettadb.RosettaDB(settings, host = "kortemmelab.ucsf.edu")

def getKortemmelabUsersConnection():
	return rosettadb.RosettaDB(settings, host = "kortemmelab.ucsf.edu", db = "KortemmeLab")

def getBenchmarksConnection():
	return rosettadb.DatabaseInterface(settings, host = "kortemmelab.ucsf.edu", db = "Benchmarks")

def getLabServicesConnection():
	#return rosettadb.DatabaseInterface(settings, host = "kortemmelab.ucsf.edu", db = "LabServices")
	return rosettadb.RosettaDB(settings, host = "kortemmelab.ucsf.edu", db = "LabServices")

def getGen9Connection():
	return rosettadb.DatabaseInterface(settings, host = "kortemmelab.ucsf.edu", db = "Gen9Design")

def fixFilename(filename):
	
	highestSeparator = filename.rfind('/')
	if highestSeparator != -1:
		filename = filename[highestSeparator + 1:]
	highestSeparator = filename.rfind('\\')
	if highestSeparator != -1:
		filename = filename[highestSeparator + 1:]
	
	filename = filename.replace(' ', '_')
	filename = filename.replace('.', '_')
	filename = filename.replace(':', '_')
	filename = filename.replace('\t', '_')
	filename = filename.replace('\n', '_')
	if filename[-3:] not in ['pdb', 'PDB' ]:
		filename = filename + '.pdb'
	else:
		filename = filename[:-4] + '.pdb'
	return filename
	
def saveTempPDB(SID, pdb_object, pdb_filename):
	tempdir = os.path.join(settings["TempDir"], "pdbs") 
	innertempdir = os.path.join(tempdir, SID)
		
	try:
		if not os.path.exists(tempdir):
			os.mkdir(tempdir, 0775)
		if not os.path.exists(innertempdir):
			os.mkdir(innertempdir, 0775)
		
		pdb_filename = fixFilename(pdb_filename)
		filepath = os.path.join(innertempdir, pdb_filename)
		pdb_object.write(filepath)		
		filepath = os.path.join("pdbs", SID, pdb_filename)
		return True, filepath
	
	except:
		estring = traceback.format_exc()
		errors.append(estring)
		if estring.find("IOError: [Errno 13] Permission denied") != -1:
			estring = "Write permission was denied when creating the file. If this persists, please contact support@kortemmelab.ucsf.edu."
		else:
			# We don't know what the error was but returning the string back as is gives the user too much internal information
			# todo: We should log this error and should email the admin as well (update error string to indicate that admin was notified)
			estring = "An error occurred uploading the file. If this persists, please contact support@kortemmelab.ucsf.edu." 
		errors.append(estring)
		return False, ''

# Used on submission. ChosenBinary should be set by uploading the PDB and be propagated down to this stage
def getRosettaVersion(form):
	if form.has_key("ChosenBinary") and form["ChosenBinary"].value:
		return form["ChosenBinary"].value
	else:
		return None
   
# Used on parsing the PDB. Mini should be set by the Rosetta version select group
def usingMini(form):
	if form.has_key("Mini"):
		return RosettaBinaries[form["Mini"].value]["mini"]
	else:
		return None	

###############################################################################################
# ws()                                                                                        #
# This is the main function call. It parses the CGI arguments and generates web pages.        #
# It takes no formal arugments, but parses the following CGI form fields:                     #
#  query  [ register | login | logout | index | terms_of_service | submit | queue | update ]  #
###############################################################################################

protocolGroups = []
protocols = []

def ws():
	s = sys.stdout
	if not(settings["LiveWebserver"]):
		sys.stderr = s
		cgitb.enable(display=0, logdir="/tmp")
		#cgitb(False,'/var/log/rosettaweb')
	debug = ''

	html_content = ''
	query_type = 'dftba'
	SID = ''
	username = ''
	userid = ''
	title = ''
	
	comment = ''
	adminWarning = ''
	
	# get the POST data from the webserver
	form = cgi.FieldStorage()
	
	# SECURITY CHECK
	#print("Content-type: text/html\n\n")
	for key in form:
		#print(key)
		#print(form[key])
		# Escape HTML code
		if type(form[key]) != type([]):
			form[key].value = escape(form[key].value)
		if (key == "Password" or key == "ConfirmPassword" or key == "myPassword" or key == "password" or key == "confirmpassword"):
			# Store the password as an MD5 hex digest
			tgb = str(form[key].value)
			form[key].value = md5.new(tgb.encode('utf-8')).hexdigest()

	####################################### 
	# cookie check                        #
	####################################### 

	# create session object
	my_session = session.Session(expires=settings["CookieExpiration"], cookie_path='/')
	# get time of last visit
	lastvisit = my_session.data.get('lastvisit')
	
	# set session ID
	SID = my_session.cookie['sid'].value
	# get present time as datetime object
	t = datetime.now()
	
	# s.write(str(my_session.cookie)+'\n')
	# s.write("Content-type: text/html\n\n")
	# s.write("%s\n" % (lastvisit))
	# s.write("%s\n" % (SID))
	# my_session.close()
	# s.close() 
	# return
	result = None
	
	if not (form.has_key("query") and form["query"].value == "datadir"):
		sql = 'SELECT * FROM Sessions WHERE SessionID="%s"' % SID
		results = DBConnection.execQuery(sql)
		if not results:
			lv_strftime = t.strftime("%Y-%m-%d %H:%M:%S")
			sql = "INSERT INTO Sessions (SessionID,Date,query,loggedin) VALUES (\"%s\",\"%s\",\"%s\",\"%s\") " % (SID, lv_strftime, "login", "0")
			result = DBConnection.execQuery(sql)
			
		if lastvisit == None:  # lastvisit == None means that the user doesn't have a cookie
			# set the session object to the actual time and also write the time to the database
			my_session.data['lastvisit'] = repr(time.time())
			lv_strftime = t.strftime("%Y-%m-%d %H:%M:%S")
			sql = "INSERT INTO Sessions (SessionID,Date,query,loggedin) VALUES (\"%s\",\"%s\",\"%s\",\"%s\") " % (SID, lv_strftime, "login", "0")
			result = DBConnection.execQuery(sql)
			# redirect user to the index page
			query_type = "index"
			 
			# then create the HTTP header which includes the cookie. THESE LINES MUST NOT BE REMOVED!
			# s.write(str(my_session.cookie)+'\n')  # DO NOT REMOVE OR COMMENT THIS LINE!!!
			# s.write("Content-type: text/html\n\n")
			# s.write("Location: %s?query=%s\n\n" % ( ROSETTAWEB_server_script, query_type ) ) # this line reloads the page
			# close session object
			# my_session.close()
			# s.close() 
			# return

		else: # we have a cookie already, let's look it up in the database and check whether the user is logged in
			# set cookie to the present time with time() function
			
			my_session.data['lastvisit'] = repr(time.time())
			# get infos about session
			#sql = 'SELECT loggedin, UserName, KortemmeLabMember FROM Sessions INNER JOIN Users on UserID=Users.ID WHERE SessionID = "%s"' % SID  # is the user logged in?
			sql = 'SELECT loggedin, UserName, KortemmeLabMember FROM Sessions INNER JOIN Users on UserID=Users.ID WHERE SessionID = "%s"' % SID  # is the user logged in?
			result = DBConnection.execQuery(sql)
			
			allowedQueries = ["register", "login", "loggedin", "logout", "index"]
			subAllowedQueries = ["register", "index", "login", "terms_of_service", "oops", "doc"]
			if settings["LiveWebserver"]:
				allowedQueries.extend(["jobinfo", "terms_of_service", "submit", "submitted", "queue", "update", "doc", "delete", "parsePDB", "sampleData"])
			if not(settings["LiveWebserver"]):
				if result and result[0][1] == 'oconchus':
					allowedQueries.extend(["admin", "ddg", "Gen9", "Gen9File", "Gen9Comment", "benchmarks", "PDB", "admincmd", "benchmarkreport"])
					subAllowedQueries.extend(["admin", "ddg", "Gen9", "Gen9File", "Gen9Comment", "benchmarks", "PDB", "admincmd", "benchmarkreport"])
				elif result and result[0][2] == 1:
					allowedQueries.extend(["Gen9", "Gen9File", "Gen9Comment", "benchmarks", "PDB", "benchmarkreport"])
					subAllowedQueries.extend(["Gen9", "Gen9File", "Gen9Comment", "benchmarks", "PDB", "benchmarkreport"])

			# if this session is active (i.e. the user is logged in) allow all modes. If not restrict access or send him to login.
			if result and result[0][0] == 1:
				sql = "SELECT u.UserName,u.ID FROM Sessions s, Users u WHERE s.SessionID = \"%s\" AND u.ID=s.UserID" % SID
				userresult = DBConnection.execQuery(sql)
				if userresult and userresult[0][0] != () and userresult[0][0] != (): #todo
					username = userresult[0][0]
					userid = int(userresult[0][1])
			if  form.has_key("query") and form['query'].value in allowedQueries:
				query_type = form["query"].value
			elif form.has_key("query") and form['query'].value in subAllowedQueries:
				query_type = form["query"].value
			else:
				query_type = "index" # fallback, shouldn't occur
		# send cookie info to webbrowser. DO NOT DELETE OR COMMENT THIS LINE!
		s.write(str(my_session.cookie) + '\n')
		
		if not(form.has_key("query")) or form["query"].value not in ["PDB", "benchmarkreport", "Gen9File"]:
			s.write("Content-type: text/html\n\n")
		
		s.write(debug)
		my_session.close()
	
	###############################
	# HTML CODE GENERATION
	###############################

	########## DEBUG Cookies ########## 
	#s.write(string_cookie+'\n<br><br>')
	#s.write('%s <br> sess.cookie = %s <br> sess.data = %s\n<br><br>' % (my_session.cookie, my_session.cookie, my_session.data))
	#s.write(str(my_session.cookie)+'\n<br><br>')
	########## DEBUG Cookies ##########

	if not os.path.exists('/tmp/rosettaweb-rosettadaemon.pid'): #upgradetodo: Store this filename in the conf file
		if hostname in DEVELOPMENT_HOSTS and False:
			adminWarning = 'Backend not running. Jobs will not be processed immediately.'

	rosettaDD = RosettaDataDir(settings["ServerName"], settings["ServerTitle"], settings["ServerScript"], settings["ContactName"], settings["DownloadDir"])
	rosettaHTML =  RosettaHTML(settings["ServerName"], settings["ServerTitle"], settings["ServerScript"], settings["ContactName"], settings["DownloadDir"], username=username, comment=comment, adminWarning=adminWarning)
	
	global protocolGroups
	global protocols
	feProtocols = FrontendProtocols(rosettaDD, rosettaHTML)
	protocolGroups, protocols = feProtocols.getProtocols()
	
	#######################################
	# show the result files, no login     #
	#######################################
	if form.has_key("query") and form["query"].value == "datadir":
		s.write("Content-type: text/html\n\n")
		
		cryptID = ''
		status = ''
		task = ''
		html_content = ''
		mini = False

		if form.has_key("job"):
			cryptID = form["job"].value
			sql = 'SELECT ID,Status,task,mini,PDBComplexFile,ProtocolParameters FROM backrub WHERE cryptID="%s"' % (cryptID)

			if form.has_key("local") and form["local"].value == "false":
				isLocal = False
				rosettaDD.download_dir = settings["RemoteDownloadDir"]
				rosettaDD.ddir = "../remotedownloads"
				result = getKlabDBConnection().execQuery(sql)
			else:
				result = DBConnection.execQuery(sql)

			if len(result) > 0:
				jobid = result[0][0]
				status = result[0][1]
				task = result[0][2]
				binary = result[0][3]
				pdb_filename = result[0][4]
				protoparams = result[0][5]
			else:
				html_content = "Either an invalid job ID was given or else the job no longer exists in the database."  
		else:
			html_content = "Invalid link. No job ID given."

		if status == 1: # running
			html_content = '<br>Job is Running. Please check again later.'
		elif status == 0:
			html_content = '<br>Job in queue. Please check again later.'
		elif status in [3, 4]:
			html_content = '<br>No data.'

		found = False
		if html_content == '':
			for p in protocols:
				if task == p.dbname:
					found = True
					p.getDataDirFunction()(cryptID, jobid, binary, pdb_filename, protoparams)
					break
		if not found:
			html_content = "No data."

		s.write(rosettaDD.main(html_content))
		s.close()
		return

	# session is now active, execute function
	# if query_type == "index":
	#   html_content = rosettaHTML.index()
	#   title = 'Home'
	propagatedValues = ['ChosenBinary']
	extraValues = {}
	for pv in propagatedValues:
		if form.has_key(pv):
			extraValues[pv] = form[pv].value

	if query_type == "login" or query_type == "index":
		login_return = login(form, my_session, t)
		if login_return == True:
			username = form["myUserName"].value
			html_content = rosettaHTML.loggedIn(username)
		elif login_return in ['no_password', 'wrong_password', 'wrong_username']:
			html_content = rosettaHTML.login(message='Wrong username or password. Please try again.')
		elif login_return == 'logged_in':
			html_content = rosettaHTML.login(message='You are already logged in.', login_disabled=True)
		else:
			html_content = rosettaHTML.login()
		title = 'Home'

	elif query_type == "loggedin":
		html_content = rosettaHTML.loggedIn(username) 

	elif query_type == "logout":
		if logout(form, my_session):
			html_content = rosettaHTML.logout(username)
		else:
			html_content = rosettaHTML.index()
		title = 'Logout'

	elif query_type == "parsePDB" or query_type == "sampleData":
		#html_content = rosettaHTML.submit(jobname='')
		#form
		
		protocol = (form["protocolgroup"].value, form["protocoltask"].value)
		
		#if False:
		pdb_okay, pdbfile, pdb_filename, pdb_object = parsePDB(rosettaHTML, form)
		if not pdb_okay:
			# reset the query for the JS startup function
			query_type = "submit"
			html_content = rosettaHTML.submit(jobname='', errors=errors, activeProtocol = protocol, extraValues = extraValues)
		else:
			saveSucceeded, newfilepath = saveTempPDB(SID, pdb_object, pdb_filename)
			if not saveSucceeded:
				# reset the query for the JS startup function
				query_type = "submit"
				html_content = rosettaHTML.submit(jobname='', errors=errors, extraValues = extraValues)
			else:
				PDBchains = pdb_object.chain_ids() 
				numPDBchains = len(PDBchains)
				

				if numPDBchains > ROSETTAWEB_SK_Max_Chains:
					errors.append('The PDB file contains %d chains. The maximum number of chains currently supported by the applications is %d.' % (numPDBchains, ROSETTAWEB_SK_Max_Chains))

				extraValues['ChosenBinary'] = form["Mini"].value
				html_content = rosettaHTML.submit('', errors, protocol, pdb_filename, newfilepath, pdb_object.chain_ids(), form["MiniTextValue"].value, extraValues, query_type == "sampleData")
		title = 'Submission Form'

	elif query_type == "submitted":    
		return_val = submit(rosettaHTML, form, SID)
		if return_val: # data was submitted and written to the database
			html_content = rosettaHTML.submitted('', return_val[0], return_val[1], return_val[2], warnings)
			title = 'Job submitted'
		else: # no data was submitted/there is an error
			html_content = rosettaHTML.submit(jobname='', errors=errors, extraValues = extraValues)
			title = 'Submission Form'

	elif query_type == "submit":
		html_content = rosettaHTML.submit(jobname='', extraValues = extraValues)
		title = 'Submission Form'

	elif query_type == "queue":
		output = StringIO()
		output.write('<TD align="center">')
		job_list = queue(form, userid)
		html_content = rosettaHTML.printQueue(job_list, userid)
		title = 'Job Queue'

	elif query_type == "jobinfo":
		parameter = jobinfo(form, SID)
		if parameter[0]:
			html_content = rosettaHTML.jobinfo(parameter[1], parameter[2])
		else:
			html_content = '<td align="center">No Data<br><br></td>'
		title = 'Job Info'

	elif query_type == "register":
		register_result = register(form, SID)
		if register_result[0]:
			if register_result[1] == 'updated':
				html_content = rosettaHTML.updated()
			else:
				html_content = rosettaHTML.registered()
		else:
			html_content = rosettaHTML.register(errors=errors)
		title = 'Registration'

	elif query_type == "PDB":
		if not(settings["LiveWebserver"]):
			jobID = form["job"].value
			executionserver = form["server"].value
			nolinenums = False
			if form.has_key("plain"):
				nolinenums = form["plain"] 
			
			# This logic does not currently generalize to multiple test servers
			StorageDBConnection = DBConnection
			if executionserver == "kortemmelab":
				StorageDBConnection = getKlabDBConnection()
			
			quotas = StorageDBConnection.execQuery("SELECT PDBComplex FROM backrub WHERE ID=%s", parameters = (jobID,))
			s.write("Content-type: text/plain\n\n")
			if quotas:
				pdbfile = quotas[0][0]
				if not nolinenums:
					import math
					linenum = 1
					pdbfile = pdbfile.split("\n")
					numzeros = math.ceil(math.log10(len(pdbfile)))
					for line in pdbfile:
						s.write("%0*d: %s\n" % (int(numzeros), linenum, line))
						linenum += 1
				else:
				 s.write(pdbfile)
			else:
				s.write("Could not retrieve the PDB from the database.")
			#html_content = rosettaHTML.adminPage(quotas, usage, users, settings)
			title = 'Job #%s' % jobID

	elif query_type == "admincmd":
		if not(settings["LiveWebserver"]):
			jobID = form["job"].value
			executionserver = form["server"].value
			cmd = form["cmd"].value
			
			# This logic does not currently generalize to multiple test servers
			StorageDBConnection = DBConnection
			if executionserver == "kortemmelab":
				StorageDBConnection = getKlabDBConnection()
			
			success = True
			error = None
			allowedAdminCommands = ["restart", "kill", "clear", "expire", "revive"]
			try:
				if cmd == "clear":
					quotas = StorageDBConnection.execQuery("UPDATE backrub SET AdminCommand=NULL WHERE ID=%s", parameters = (jobID,))
				elif cmd == "expire":
					quotas = StorageDBConnection.execQuery("UPDATE backrub SET Expired=1 WHERE ID=%s", parameters = (jobID,))
				elif cmd == "revive":
					quotas = StorageDBConnection.execQuery("UPDATE backrub SET Expired=0 WHERE ID=%s", parameters = (jobID,))
				elif cmd in allowedAdminCommands:
					quotas = StorageDBConnection.execQuery("UPDATE backrub SET AdminCommand=%s WHERE ID=%s", parameters = (cmd, jobID))
				else:
					oldcmd = cmd
					#cmd = "administrat"
					raise Exception("Unknown command %s passed." % oldcmd)
			except Exception, e:
				success = False
				error = "Error: '%s'<br><br>%s" % (str(e), join(traceback.format_exc().split("\n"), "<br>"))
			html_content = rosettaHTML.jobAdminCommand(success, cmd, jobID, error)
			title = 'Job #%s %sed' % (jobID, cmd)
		
	elif query_type == "admin":
		if not(settings["LiveWebserver"]):
			numberOfDays = 30
			dstart = date.fromtimestamp(time.time() - (60*60*24*numberOfDays)) 
			dend = date.today()
			quotas = getKortemmelabUsersConnection().execQuery("SELECT Date, Quotas, DriveUsage, OtherData, GroupUsage FROM Quota WHERE Date >= %s AND Date <= %s ORDER BY Date", parameters = (dstart, dend))
			usage = getKortemmelabUsersConnection().execQuery("SELECT * FROM DailyUsage WHERE Date >= %s AND Date <= %s ORDER BY Username, Date", parameters = (dstart, dend))
			users = getKortemmelabUsersConnection().execQuery("SELECT * FROM Users ORDER BY Username")
			
			html_content = rosettaHTML.adminPage(quotas, usage, users, settings, form)
			title = 'Admin'

	elif query_type == "Gen9":
		if not(settings["LiveWebserver"]):
			html_content = rosettaHTML.gen9Page(settings, form, userid)
			title = 'Gen9'
	
	elif query_type == "Gen9Comment":
		if not(settings["LiveWebserver"]):
			Gen9Error = None
			success = True
			try:
				assert(form.has_key('Gen9Page'))
				assert(form.has_key('gen9sort1'))
				assert(form.has_key('gen9sort2'))
			except:
				success = False
				print("Error: Could not find form values for Gen9 page settings.")
			
			DesignID = None
			Gen9Username = None
			try:
				assert(form.has_key('DesignID'))
				assert(form.has_key('Username'))
				DesignID = int(form['DesignID'].value)
				Gen9Username = form['Username'].value
			except:
				success = False
				print("Error: Could not find form values for username and design ID.")
			
			if success:
				gen9db = getGen9Connection()
				
				design_rating = None
				if form.has_key('user-design-rating-%d' % DesignID):
					if form['user-design-rating-%d' % DesignID].value != 'None':
						design_rating = form['user-design-rating-%d' % DesignID].value
				design_notes = None
				if form.has_key('user-design-comments-%d' % DesignID):
					if form['user-design-comments-%d' % DesignID].value != 'None':
						design_notes = form['user-design-comments-%d' % DesignID].value
					
				scaffold_rating = None
				if form.has_key('user-scaffold-rating-%d' % DesignID):
					if form['user-scaffold-rating-%d' % DesignID].value != 'None':
						scaffold_rating = form['user-scaffold-rating-%d' % DesignID].value
				scaffold_notes = None
				if form.has_key('user-scaffold-comments-%d' % DesignID):
					if form['user-scaffold-comments-%d' % DesignID].value != 'None':
						scaffold_notes = form['user-scaffold-comments-%d' % DesignID].value
				
				gres = gen9db.execute("SELECT * FROM UserDesignRating WHERE UserID=%s AND DesignID=%s", parameters=(Gen9Username, DesignID))
				if gres:
					assert(len(gres) == 1)
					gen9db.execute("UPDATE UserDesignRating SET Rating=%s WHERE UserID=%s AND DesignID=%s", parameters=(design_rating, Gen9Username, DesignID))
					gen9db.execute("UPDATE UserDesignRating SET RatingNotes=%s WHERE UserID=%s AND DesignID=%s", parameters=(design_notes, Gen9Username, DesignID))
				elif design_rating and (not(design_notes) or (design_notes =="") or (design_notes == "None")):
					Gen9Error = "You need to specify a design rating AND add notes."
				elif design_notes and (not(design_rating) or (design_rating =="") or (design_rating == "None")):
					Gen9Error = "You need to specify a design rating AND add notes."
				elif design_rating and design_notes: 
					details = {
						'UserID'			: Gen9Username,
						'DesignID'			: DesignID,
						'Rating'			: design_rating,
						'RatingNotes'		: design_notes,
					}
					gen9db.insertDict('UserDesignRating', details,)

				ComplexID = gen9db.execute("SELECT ComplexID FROM Design INNER JOIN PDBBiologicalUnit ON Design.WildtypeScaffoldPDBFileID=PDBFileID AND Design.WildtypeScaffoldBiologicalUnit=BiologicalUnit WHERE ID=%s", parameters=(DesignID,))
				assert(ComplexID)
				assert(len(ComplexID) == 1)
				ComplexID = ComplexID[0]['ComplexID']
				
				gres = gen9db.execute("SELECT * FROM UserScaffoldRating WHERE UserID=%s AND ComplexID=%s", parameters=(Gen9Username, ComplexID))
				if gres:
					assert(len(gres) == 1)
					gen9db.execute("UPDATE UserScaffoldRating SET Rating=%s WHERE UserID=%s AND ComplexID=%s", parameters=(scaffold_rating, Gen9Username, ComplexID))
					gen9db.execute("UPDATE UserScaffoldRating SET RatingNotes=%s WHERE UserID=%s AND ComplexID=%s", parameters=(scaffold_notes, Gen9Username, ComplexID))
				elif scaffold_rating and (not(scaffold_notes) or (scaffold_notes =="") or (scaffold_notes == "None")):
					Gen9Error = "You need to specify a scaffold rating AND add notes."
				elif scaffold_notes and (not(scaffold_rating) or (scaffold_rating =="") or (scaffold_rating == "None")):
					Gen9Error = "You need to specify a scaffold rating AND add notes."
				elif scaffold_rating and scaffold_notes: 
					details = {
						'UserID'			: Gen9Username,
						'ComplexID'			: ComplexID,
						'Rating'			: scaffold_rating,
						'RatingNotes'		: scaffold_notes,
						'TerminiAreOkay'	: None,
					}
					gen9db.insertDict('UserScaffoldRating', details,)
					
			#form.has_key('Gen9Page').value
			
			html_content = rosettaHTML.gen9Page(settings, form, userid, Gen9Error)
			title = 'Gen9'
			
			#html_content = rosettaHTML.gen9Page(settings, form, userid)
			#title = 'Gen9'
	
	
	elif query_type == "Gen9File":
		if not(settings["LiveWebserver"]):
			if form.has_key('download'):
				gen9db = getGen9Connection()
				if form['download'].value == 'PDB':
					if form.has_key('DesignID'):
						results = gen9db.execute("SELECT FilePath FROM Design WHERE ID=%s", parameters = (form['DesignID'].value,))
						if not results:
							s.write("Content-type: text/html\n\n")
							print("No files found for design ID %s." % form['DesignID'].value)
						else:
							assert(len(results) == 1)
							filepath = results[0]['FilePath']
							contents = readBinaryFile(filepath)
							filename = os.path.split(filepath)[1]
							
							print 'Content-Type: application/x-gzip'
							print 'Content-Disposition: attachment; filename="%s"' % (filename)
							print "Content-Length: %d" % len(contents)
							print
							sys.stdout.write(contents)
							sys.stdout.flush()
					else:
						s.write("Content-type: text/html\n\n")
						print("Badly specified query.")


				elif form['download'].value == 'PSE':
					if form.has_key('DesignID') and form.has_key('RankingSchemeID'):
						results = gen9db.execute("SELECT PyMOLSessionFile FROM RankedScore WHERE DesignID=%s AND RankingSchemeID=%s", parameters = (form['DesignID'].value, form['RankingSchemeID'].value))
						if not results:
							s.write("Content-type: text/html\n\n")
							print("No files found for design ID %s." % form['DesignID'].value)
						else:
							assert(len(results) == 1)
							filepath = results[0]['PyMOLSessionFile']
							contents = readBinaryFile(filepath)
							filename = os.path.split(filepath)[1]
							
							print 'Content-Type: application/octet-stream'
							print 'Content-Disposition: attachment; filename="%s"' % (filename)
							print "Content-Length: %d" % len(contents)
							print
							sys.stdout.write(contents)
							sys.stdout.flush()
					else:
						s.write("Content-type: text/html\n\n")
						print("Badly specified query.")
			else:
				print("No files found for design ID %s." % form['DesignID'].value)

						
	elif query_type == "ddg":
		if not(settings["LiveWebserver"]):
			html_content = rosettaHTML.ddgPage(settings, form)
			title = '&#916;&#916;G'

	elif query_type == "benchmarkreport":
		if not(settings["LiveWebserver"]):
			import benchmarks as benchmarkspage
			if form.has_key('Benchmark1ID') and form.has_key('Benchmark2ID') and form.has_key('BenchmarksType'):
				try:
					PDFReport = None
					if not(form.has_key('generatefresh')):
						PDFReport = getBenchmarksConnection().execute("SELECT PDFReport FROM BenchmarkRunComparison WHERE BenchmarkRunID1=%s AND BenchmarkRunID2=%s", parameters = (form["Benchmark1ID"].value,form["Benchmark2ID"].value))
					if PDFReport:
						PDFReport = PDFReport[0]['PDFReport']
						print 'Content-Type: application/pdf'
						print 'Content-Disposition: inline; filename="%s-Run_%s_vs_Run_%s.pdf"' % (form['BenchmarksType'].value, form['Benchmark1ID'].value, form['Benchmark2ID'].value)
						print "Content-Length: %d" % len(PDFReport)
						print
						sys.stdout.write(PDFReport)
						sys.stdout.flush()
					else:
						PDFReport = benchmarkspage.generateComparisonReport(form, getBenchmarksConnection())
						if PDFReport:
							ExistingPDFReport = getBenchmarksConnection().execute("SELECT PDFReport FROM BenchmarkRunComparison WHERE BenchmarkRunID1=%s AND BenchmarkRunID2=%s", parameters = (form["Benchmark1ID"].value,form["Benchmark2ID"].value))
							if ExistingPDFReport:
								getBenchmarksConnection().execute("UPDATE BenchmarkRunComparison SET PDFReport=%s WHERE BenchmarkRunID1=%s AND BenchmarkRunID2=%s", parameters = (PDFReport, form["Benchmark1ID"].value,form["Benchmark2ID"].value))
							else:
								getBenchmarksConnection().insertDict("BenchmarkRunComparison", {'BenchmarkRunID1' : form["Benchmark1ID"].value, 'BenchmarkRunID2' : form["Benchmark2ID"].value, 'PDFReport' : PDFReport})
							print 'Content-Type: application/pdf'
							print 'Content-Disposition: inline; filename="%s-Run_%s_vs_Run_%s.pdf"' % (form['BenchmarksType'].value, form['Benchmark1ID'].value, form['Benchmark2ID'].value)
							print "Content-Length: %d" % len(PDFReport)
							print
							sys.stdout.write(PDFReport)
							sys.stdout.flush()
						else:
							print 'Content-type: text/html'
							print
							print("<html><body>The PDF report was not created.</body></html>")
				except Exception, e:
						print 'Content-type: text/html'
						print
						print("<html><body>The PDF report was not created.<br>%s<br>%s</body></html>" % (e, traceback.format_exc().replace('\n', '<br>')))
			elif form.has_key("id"):
				PDFReport = getBenchmarksConnection().execute("SELECT ID, BenchmarkID, PDFReport FROM BenchmarkRun WHERE ID=%s", parameters = (form["id"].value,))
				if PDFReport:
					PDFReport = PDFReport[0]
					report = PDFReport['PDFReport']
					if report:
						if True:
							if form.has_key("action") and form['action'].value == "download":
								# Push the file to the user
								print 'Content-Type: application/octet-stream'
								print 'Content-Disposition: attachment; filename="%(BenchmarkID)s-%(ID)s.pdf"' % PDFReport
								print "Content-Length: %d" % len(report)
								print
								sys.stdout.write(report)
								sys.stdout.flush()
							elif form.has_key("action") and form['action'].value == "regenerate":
								report = None
								try:
									report = benchmarkspage.generateSingleRunReport(form, getBenchmarksConnection())
								except Exception, e:
									print 'Content-type: text/html'
									print
									print("<html><body>The PDF report was not created.<br>%s<br>%s</body></html>" % (e, traceback.format_exc().replace('\n', '<br>')))
									
								if report:
									# Enable this line to store generated reports back into the database e.g. in case the report creation script gets updated
									#getBenchmarksConnection().execute("UPDATE BenchmarkRun SET PDFReport=%s WHERE ID=%s", parameters = (report, form["id"].value,))
									print 'Content-Type: application/pdf'
									print 'Content-Disposition: inline; filename="%(BenchmarkID)s-%(ID)s.pdf"' % PDFReport
									print "Content-Length: %d" % len(report)
									print
									sys.stdout.write(report)
									sys.stdout.flush()
							else:
								# Instead, show the PDF on the page
								print 'Content-Type: application/pdf'
								print 'Content-Disposition: inline; filename="%(BenchmarkID)s-%(ID)s.pdf"' % PDFReport
								print "Content-Length: %d" % len(report)
								print
								sys.stdout.write(report)
								sys.stdout.flush()
							#print("Content-Type: application/force-download")
							#print("Content-Type: application/octet-stream")
							#print("Content-Type: application/download")
							#print("Content-Description: File Transfer")
						else:
							# todo: delete this code
							tempdir = os.path.join(settings["TempDir"], "benchmarkdata") 
							if not os.path.exists(tempdir):
								os.mkdir(tempdir, 0775)
							filepath = os.path.join(tempdir, "%(BenchmarkID)s-%(ID)s.pdf" % PDFReport)
							writeFile(filepath, report)
							filepath = os.path.join("..", "temp", "benchmarkdata", "%(BenchmarkID)s-%(ID)s.pdf" % PDFReport)
							s.write("Content-type: text/html\n\n")
							s.write("<html><body><a href='%s'>Download here</a></body></html>" % filepath)
					else:
						s.write("Content-type: text/html\n\n")
						s.write("The report has not been created.")
				else:
					s.write("Content-type: text/html\n\n")
					s.write("Could not retrieve the PDB from the database.")

	elif query_type == "benchmarks":
		if not(settings["LiveWebserver"]):
			import benchmarks as benchmarkspage
			ExistingBinaries = getLabServicesConnection().execQuery('SELECT ID, Tool, VersionType, Version, BuildType, Static, Graphics, MySQL FROM Binaries', cursorClass = rosettadb.DictCursor)
			
			benchmarks = {}
			BenchmarksDB = getBenchmarksConnection()
			
			for b in BenchmarksDB.execute('SELECT * FROM Benchmark', cursorClass = rosettadb.DictCursor):
				benchmarks[b['BenchmarkID']] = b
				benchmarks[b['BenchmarkID']]['Revisions'] = {}
			
			for brevision in BenchmarksDB.execute('SELECT * FROM BenchmarkRevision', cursorClass = rosettadb.DictCursor):
				benchmarks[brevision['BenchmarkID']]['Revisions'][int(brevision['RevisionFrom'])] = brevision # Cast to int for JSON
				benchmarks[brevision['BenchmarkID']]['Revisions'][int(brevision['RevisionFrom'])]['alternate_flags'] = [] # Cast to int for JSON
			
			qry = 'SELECT COLUMN_TYPE FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = "BenchmarkRun" AND COLUMN_NAME = "RunLength"'
			runlengths = BenchmarksDB.execute(qry)[0]['COLUMN_TYPE']
			if runlengths.startswith("enum(") and runlengths.endswith(")"):
				runlengths = (runlengths[5:-1]).split(",")
				runlengths = [b.strip()[1:-1] for b in runlengths]
			
			qry = 'SELECT COLUMN_TYPE FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = "BenchmarkRun" AND COLUMN_NAME = "ClusterQueue"'
			ClusterQueues = BenchmarksDB.execute(qry)[0]['COLUMN_TYPE']
			if ClusterQueues.startswith("enum(") and ClusterQueues.endswith(")"):
				ClusterQueues = (ClusterQueues[5:-1]).split(",")
				ClusterQueues = [b.strip()[1:-1] for b in ClusterQueues]
			
			qry = 'SELECT COLUMN_TYPE FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = "BenchmarkRun" AND COLUMN_NAME = "ClusterArchitecture"'
			ClusterArchitectures = BenchmarksDB.execute(qry)[0]['COLUMN_TYPE']
			if ClusterArchitectures.startswith("enum(") and ClusterArchitectures.endswith(")"):
				ClusterArchitectures = (ClusterArchitectures[5:-1]).split(",")
				ClusterArchitectures = [b.strip()[1:-1] for b in ClusterArchitectures]
			
			qry = 'SELECT BenchmarkID, RevisionFrom, AlternateFlags FROM BenchmarkAlternateFlags ORDER BY ID'
			for alternate_flags in BenchmarksDB.execute(qry):
				benchmarks[alternate_flags['BenchmarkID']]['Revisions'][int(alternate_flags['RevisionFrom'])]['alternate_flags'].append(alternate_flags['AlternateFlags']) # Cast to int for JSON
				
			qry = 'SELECT * FROM BenchmarkOption ORDER BY ID'
			for benchmark_options in BenchmarksDB.execute(qry, cursorClass = rosettadb.DictCursor):
				benchmarks[benchmark_options["BenchmarkID"]]['options'] = benchmarks[benchmark_options["BenchmarkID"]].get('options', [])
				benchmarks[benchmark_options["BenchmarkID"]]['options'].append(benchmark_options)
			
			if not(benchmarks and runlengths):
				raise Exception("Failed parsing Benchmarks database schema.")
			
			benchmark_details = {
				"benchmarks" 			: benchmarks,
				#"revisions"				: [],
				"runlengths" 			: runlengths,
				"ClusterQueues"			: ClusterQueues,
				"ClusterArchitectures"	: ClusterArchitectures,
				"ExistingBinaries"		: ExistingBinaries,
			}
			
			if form.has_key('submitted') and form['submitted'].value == "T":
				parameters = benchmarkspage.getRunParameters(form, benchmark_details)
				BenchmarksDB.insertDict("BenchmarkRun", parameters)
				BenchmarksDB.execute('UPDATE BenchmarkRun SET EntryDate=NOW() WHERE ID=%s', parameters = (BenchmarksDB.getLastRowID(),))
			
			benchmark_runs = BenchmarksDB.execute('SELECT ID, BenchmarkID, RunLength, RosettaSVNRevision, RosettaDBSVNRevision, RunType, CommandLine, BenchmarkOptions, ClusterQueue, ClusterArchitecture, ClusterMemoryRequirementInGB, ClusterWalltimeLimitInMinutes, NotificationEmailAddress, EntryDate, StartDate, EndDate, Status, AdminCommand, Errors FROM BenchmarkRun ORDER BY ID')
			runsWithPDFs = set([result["ID"] for result in BenchmarksDB.execute('SELECT ID FROM BenchmarkRun WHERE PDFReport IS NOT NULL')])
			for benchmark_run in benchmark_runs:
				if benchmark_run["ID"] in runsWithPDFs:
					benchmark_run["HasPDF"] = True
				else:
					benchmark_run["HasPDF"] = False
			
			benchmark_details["BenchmarkRuns"] = benchmark_runs
			
			html_content = rosettaHTML.benchmarksPage(settings, form, benchmark_details)
			title = 'Benchmarks'

	elif query_type == "update":
		user_data = getUserData(form, SID)
		html_content = rosettaHTML.register(
			username=user_data['username'],
			firstname=user_data['firstname'],
			lastname=user_data['lastname'],
			institution=user_data['institution'],
			email=user_data['email'],
			address=user_data['address'],
			city=user_data['city'],
			zip=user_data['zip'],
			state=user_data['state'],
			country=user_data['country'],
			update=True)
		title = 'User Information'

	elif query_type == "terms_of_service":
		html_content = rosettaHTML.terms_of_service()
		title = 'Terms of Service'

	elif query_type == "doc":
		html_content = rosettaHTML.help()
		title = 'Documentation'

	elif query_type == "delete":
		html = deletejob(form, SID)
		title = 'Job Deleted'

	elif query_type == "oops":
		password_result = send_password(form)
		if password_result[0]:
			html_content = rosettaHTML.passwordUpdated(password_result[1])
		else:
			html_content = rosettaHTML.sendPassword(password_result[1])
		title = 'Password'

	else:
		html = "this is impossible" # should never happen since we only allow states from list above 

	if query_type not in ["PDB", "benchmarkreport", "Gen9File"]:
		s.write(rosettaHTML.main(html_content, title, query_type))
	
	s.close()

def logBrowser(sid, userid):
	log_dir = os.path.join(os.environ['DOCUMENT_ROOT'], 'rosettaweb', 'logs')
	if not os.path.exists(log_dir):
		make755Directory(log_dir)
	
	F = open(os.path.join(log_dir, "browser-%s.txt" % sid), "w")
	F.write("User\t%s\n" % userid)
	F.write("User-Agent\t%s\n" % os.environ.get("HTTP_USER_AGENT", "N/A"))
	F.write("IP\t%s\n" % IP)
	F.write("Hostname\t%s\n" % hostname)
	F.write("Time\t%s\n" % datetime.today())
	F.close()
	
########################################## end of ws() ########################################



###############################################################################################
# login()                                                                                     #
#   performs all necessary actions to log in a users                                          # 
###############################################################################################


def login(form, my_session, t):

	# get session info
	SID = my_session.cookie['sid'].value
	lv_strftime = t.strftime("%Y-%m-%d %H:%M:%S")
		
	# Disable guest login to albana
	if not(settings["LiveWebserver"]) and form.has_key('myUserName') and form["myUserName"].value == "guest":
		return False
	
	## we first check if the user can login
	if form.has_key('login') and form['login'].value == "login":
		# this is for the guest user
		
		if not form.has_key('myUserName'):
			return 'wrong_username'
		elif settings["LiveWebserver"] and (form["myUserName"].value == "guest" and not form.has_key('myPassword')):
			password_entered = ''
		elif not form.has_key('myPassword'):
			return 'wrong_password'
		else:
			password_entered = form["myPassword"].value
		
		# check for userID and password
		sql = 'SELECT ID,Password FROM Users WHERE UserName = "%s"' % form["myUserName"].value
		result = DBConnection.execQuery(sql)
		try:
			UserID = result[0][0]
			PW = result[0][1]
			if password_entered == PW: 
				# all clear ... go!
				sql = "UPDATE Sessions SET UserID = \"%s\", Date = \"%s\", loggedin = \"%s\" WHERE SessionID = \"%s\" " % (UserID, lv_strftime, "1", SID)
				result = DBConnection.execQuery(sql)
				logBrowser(SID, UserID)	
				return True # successfully logged in

			else:
				return 'wrong_password'
		except IndexError:
			return 'wrong_username'

	else: # need form
		sql = "SELECT loggedin FROM Sessions WHERE SessionID = \"%s\"" % SID
		result = DBConnection.execQuery(sql)
		if result and result[0][0] == 1:
			return 'logged_in'

		return False

################################### end login() ###############################################

###############################################################################################
# logout()                                                                                    #
#  set logged in status to not logged in                                                      #
###############################################################################################

def logout(form, my_session, SID=None):
		# get sessionID
		if SID == None:
			SID = my_session.cookie['sid'].value
		# update database
		sql = "UPDATE Sessions SET loggedin = \"%s\" WHERE SessionID = \"%s\" " % ("0", SID)
		DBConnection.execQuery(sql)

		return True

################################### end logout() ##############################################

###############################################################################################
# send_password()                                                                             #
# asks for an email address to send password to                                               #
###############################################################################################

def send_password(form):
	password_updated = True
	message = ''
	
	if form.has_key("Email"):
		import random
		Email = form["Email"].value
		
		sql = "SELECT ID,FirstName,UserName FROM Users where Email=\"%s\"" % Email
		result = DBConnection.execQuery(sql)
		
		if len(result) < 1:
			password_updated = False
			message = 'Your email address is not in our database. Please <A href="rosettaweb.py?query=register">register</A>.<br><br> \n'
		else:
			password = join(random.sample('0123456789abcdefghijklmnopqrstuvwxyz0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789', 6), '')
			crypt_pw = md5.new(password.encode('utf-8')).hexdigest()
			
			sql = 'UPDATE Users SET Password="%s" WHERE ID=%s' % (crypt_pw, result[0][0])
			result_null = DBConnection.execQuery(sql)
			
			text = """Dear %s,

Your username and a temporary Password are listed below. This email was 
generated upon request to send you a new password. Please login and change
your password.

If you DID NOT request to reset your password, please let us know.
mailto:support@kortemmelab.ucsf.edu 
  
-----------------------
LOGIN NAME AND PASSWORD
-----------------------
              
LOGIN NAME:  %s
  PASSWORD:  %s
  
Have a nice day!

The Kortemme Lab Server Daemon

""" % (result[0][1], result[0][2], password)
				
			if sendMail(settings["SendmailBinary"], Email, settings["AdminEmail"], "[Kortemme Lab Server] Forgotten Password Request", text) == 1:
					message = 'New password was send to %s <br><br> \n' % Email
			else:
					password_updated = False
					message = 'Sending password failed. <br><br> \n'
	
	else: 
		password_updated = False
	
	return (password_updated, message)

################################### end send_password() #######################################

###############################################################################################
# register()                                                                                  #
#  present either a form for registration or check if user or emailadress already exist       #
#  if not add new user to database                                                            #
###############################################################################################


def _checkUserInfo(form):
	# check whether email or username are already in database
	# other values are checked by java script when entering in form
	process_data = True
	error = None
	
	sql = "SELECT * FROM Users WHERE UserName =\"%s\"" % form["username"].value
	sql_out = DBConnection.execQuery(sql)
	if len(sql_out) >= 1:		   # if we get something, name is already taken
		form["username"].value = ''   # reset
		process_data = False 
		error = 'Username is already in use.'
	
	sql = "SELECT * FROM Users WHERE Email = \"%s\"" % form["email"].value
	sql_out = DBConnection.execQuery(sql)
	if len(sql_out) >= 1:
		form["email"].value = ''
		process_data = False
		error = 'Email address is already registered.'
	
	# check whether password is correct:
	if form["password"].value != form["confirmpassword"].value:
		process_data = False
		error = 'Passwords do not match.'	

	return (process_data, error)

def _updateUserInfo(form, SID):
	# transmit values to database
	# define allowed fields 
	value_list = ["username", "firstname", "lastname", "institution", "email", "password"]
	value_list_o = ["address", "city", "zip", "state", "country"]  
	value_names = {"username" : "UserName", "firstname" : "FirstName", "lastname" : "LastName", "email" : "Email", "institution" : "Institution", "address":"Address1", "city":"City", "state" : "State", "zip" : "Zip", "country" : "Country", "password" : "Password"}
	
	# check whether each parameter has a value and if so append it to the database string
	fields = ""
	variables = ""
	# get userid from db
	sql = "SELECT UserID from Sessions WHERE SessionID = \"%s\" " % SID
	result = DBConnection.execQuery(sql)
	userid = result[0][0]
	
	for value_name in value_list:
		if form.has_key(value_name):
			fields += value_names[value_name] + "=\"" + form[value_name].value + "\", "
	for value_name in value_list_o:
		if form.has_key(value_name):
			fields += value_names[value_name] + "=\"" + form[value_name].value + "\", "
	sql = "UPDATE Users SET %s WHERE ID=%s" % (fields[:-2], userid)
	#print sql
	DBConnection.execQuery(sql)


def register(form, SID):
	
	# define allowed fields 
	value_list = ["username", "firstname", "lastname", "email", "password"]
	value_list_o = ["address", "institution", "city", "zip", "state", "country"]	
	value_names = {"username" : "UserName", "firstname" : "FirstName", "lastname" : "LastName", "email" : "Email", "institution" : "Institution", "address":"Address1", "city":"City", "state" : "State", "zip" : "Zip", "country" : "Country", "password" : "Password"}
	process_data = True
	form_db = {}		# store values retrieved from Database
	
	if form.has_key("mode") and form["mode"].value == "check":
		process_data, error = _checkUserInfo(form)
		if error:
			errors.append(error)
	elif form.has_key("mode") and form["mode"].value == "update":
		_updateUserInfo(form, SID)
		return (True, 'updated')
	else:
		process_data = False
		return (False, None)
	
	if process_data:
		# transmit values to database
		# check whether each parameter has a value and if so append it to the database string
		fields = ""
		variables = ""
		for value_name in value_list:
			if form.has_key(value_name):
				fields += value_names[value_name] + ","
				variables += "\"%s\"," % form[value_name].value
		for value_name in value_list_o:
			if form.has_key(value_name):
				fields += value_names[value_name] + ","
				variables += "\"%s\"," % form[value_name].value
			sql = "INSERT INTO Users (Date, %s) VALUES (NOW(), %s)" % (fields[:-1], variables[:-1])
		
		DBConnection.execQuery(sql)

		# send a conformation email
		text = """Dear %s,

Thank you for creating an account at the %s. If you have questions or if you did not create an account please let us know: %s 

-----------------------
login:       %s
Name:        %s %s

Have a nice day!

The Kortemme Lab Server Daemon
      
      """ % (form["firstname"].value, settings["ServerTitle"], settings["AdminEmail"], form["username"].value, form["firstname"].value, form["lastname"].value)
    
		sendMail(settings["SendmailBinary"], form["email"].value, settings["AdminEmail"], "[Kortemme Lab Server] New Account", text)

		text_to_admin = """Dear administrator,
    
A new user account for %s was created:

login:       %s
Name:        %s %s
Country:     %s

Have a nice day!

The Kortemme Lab Server Daemon

    """ % (settings["ServerTitle"], form["username"].value, form["firstname"].value, form["lastname"].value, form["country"].value)

		sendMail(settings["SendmailBinary"], settings["AdminEmail"], settings["AdminEmail"], "[Kortemme Lab Server] New Account created", text_to_admin)

	return (process_data, None)


################################### end register() ############################################

###############################################################################################
# update()                                                                                    #
#  here we have a little redundancy (register()) that might be removed sometime               #
#  for now this is better. due to the database call I have to make a different type of map    #
#  than the one used for "form". yes ... i dunno, works though! ;)                            #
###############################################################################################

def getUserData(form, SID):
	# define allowed fields 
	value_list = ["username", "firstname", "lastname", "institution", "email", "password"]
	value_list_o = ["address", "city", "zip", "state", "country"]	
	value_names = {"username" : "UserName", "firstname" : "FirstName", "lastname" : "LastName", "email" : "Email", "institution" : "Institution", "address":"Address1", "city":"City", "state" : "State", "zip" : "Zip", "country" : "Country", "password" : "Password"}
	process_data = True
	form_db = {}	 # store values retrieved from Database
	
	# get userid from db
	sql = "SELECT UserID from Sessions WHERE SessionID = \"%s\"" % SID
	result = DBConnection.execQuery(sql)
	# get all user data from DB
	UserID = result[0][0]
	sql = "SELECT * FROM Users WHERE ID = \"%s\"" % UserID
	sql_out = DBConnection.execQuery(sql)
	
	# create a dict with that information
 
	if len(sql_out) >= 1 :
		form_db["username"] = sql_out[0][1]
		form_db["lastname"] = sql_out[0][2]
		form_db["firstname"] = sql_out[0][3]
		form_db["email"] = sql_out[0][4]
		form_db["institution"] = sql_out[0][5]
		form_db["address"] = sql_out[0][6]
		#form_db["Address2"]			= sql_out[0][7]
		form_db["city"] = sql_out[0][8]
		form_db["state"] = sql_out[0][9]
		form_db["zip"] = sql_out[0][10]
		form_db["country"] = sql_out[0][11]
		#form_db["Phone"]				 = sql_out[0][12]
		#form_db["Password"]			= sql_out[0][13]
		#form_db["Date"]					= sql_out[0][14]
		#form_db["LastLoginDate"] = sql_out[0][15]
		#form_db["Priority"]			= sql_out[0][16]
		#form_db["Jobs"]					= sql_out[0][17]
		#form_db["EmailList"]		 = sql_out[0][18]
	
	# this simply converts the mysql None entries into empty strings, noone pick None as value now! 
	for key, value in form_db.iteritems():
		if value == 'None':
			form_db[key] = ''
	
	return form_db

################################### end update() ##############################################

def check_pdb(pdb_object, pdb_filename, usingClassic, ableToUseMini):
	'''checks pdb file for errors'''
	
	# check the formatting of the file
	pdb_check_output, wrns = pdb_object.check_format(usingClassic, ableToUseMini)
	if pdb_check_output != True:
		errors.append("PDB format incorrect in %s:<p style='text-align:left'>" % pdb_filename)
		errors.extend(pdb_check_output)
		errors.append("</p>")
		return False
	else:
		warnings.extend(wrns)
	
	# check the number of atoms/residues/chains;
	# numbers are derived from 1KYO wich is huge: {'models': 0, 'chains': 23, 'residues': 4459, 'atoms': 35248}
	counts = pdb_object.get_stats()
	if counts["atoms"] > ROSETTAWEB_PDB_MAX_ATOMS:
		errors.append("Maximum number of atoms exceeded;<br>The maximum is %d, the PDB contained %d." % (10000, counts["atoms"]))
		return False
	elif counts["residues"] > ROSETTAWEB_PDB_MAX_RESIDUES:
		errors.append("Maximum number of residues exceeded;<br>The maximum is %d, the PDB contained %d." % (500, counts["residues"]))
		return False
	elif counts["chains"] > ROSETTAWEB_PDB_MAX_CHAINS:
		errors.append("Maximum number of chains exceeded;<br>The maximum is %d, the PDB contained %d." % (ROSETTAWEB_SK_Max_Chains, counts["chains"]))
		return False
	elif counts["cys"] > ROSETTAWEB_PDB_MAX_CYSTEINE:
		errors.append("Maximum number of Cysteine residues exceeded;<br>The maximum is %d, the PDB contained %d." % (50, counts["cys"]))
		return False
	else:
		return True
	

def extract_1stmodel(pdbfile):
	# check if structure is NMR or X-RAY. Problem: if headerinfo and EXPDTA line are missing there is no way of telling.
	# Consider only the first model. Copy everything until the first ENDMDL entry.
	new_pdbfile = ''
	for line in pdbfile.split('\n'):
		new_pdbfile += line + '\n'
		if line.rstrip() == 'ENDMDL':
			new_pdbfile += 'END\n'
			break
	return new_pdbfile

###############################################################################################
# submit()                                                                                    #
# this function processes the parameter of the input form and adds a new job to the database  # 
###############################################################################################

def parsePDB(rosettaHTML, form):
	############## PDB STUFF ###################
	pdb_okay = True
	pdbfile = ''
	pdb_filename = None
	pdb_object = None

	pgroup, ptask = int(form["protocolgroup"].value), int(form["protocoltask"].value)
	protocol = protocolGroups[pgroup][ptask]
	usingClassic = not(usingMini(form))
	ableToUseMini = protocol.canUseMini()
	if form.has_key("PDBComplex") and form["PDBComplex"].value != '':
		try:
			pdbfile = form["PDBComplex"].value
			if not form["PDBComplex"].file:
				errors.append("PDB data is not a file.")
			pdb_filename = form["PDBComplex"].filename
			pdb_filename = fixFilename(pdb_filename)
		except:
			errors.append("Invalid PDB file.")
			pdb_okay = False
	
	elif form.has_key("PDBID") and form["PDBID"].value != '':
		pdb_filename = form["PDBID"].value.upper() + '.pdb'
		if pdb_filename[0] == '@':
			# This indicates that the file is locally stored 
			pdb_filename = pdb_filename[1:]
			try:
				F = open(os.path.join(settings["BaseDir"], "test", pdb_filename), "r") 
				pdbfile = F.read()
				F.close()
			except Exception, e:
				errors.append("An I/O error (%s) occurred reading the uploaded file. Please contact support@kortemmelab.ucsf.edu." % e)
				pdb_okay = False
		else:
			try:
				pdb_filename = form["PDBID"].value.upper() + '.pdb'
				url = "http://www.pdb.org/pdb/files/%s" % pdb_filename
				req = urllib2.Request(url)
				response = urllib2.urlopen(req)
				pdbfile = response.read()
				if len(pdbfile) <= 2:
					errors.append("Invalid PDB identifier.")
					pdb_okay = False
			except:
				errors.append("Invalid PDB identifier.")
				pdb_okay = False
	elif form.has_key("StoredPDB"):
		# We should have gotten here from a ParsePDB generated webpage
		# The filename in StoredPDB should have been created by saveTempPDB 
		sPDB = form["StoredPDB"].value
		if sPDB != '' and re.match("pdbs/[A-Z\d]+/[^\\/]+\.pdb", sPDB, re.IGNORECASE):
			# The filename should be generated from always match this if SID is alphanumeric
			try:
				pdb_filename = sPDB
				F = open(os.path.join(settings["TempDir"], pdb_filename), "r") 
				pdbfile = F.read()
				F.close()
			except Exception, e:
				errors.append("An I/O error (%s) occurred reading the uploaded file. Please contact support@kortemmelab.ucsf.edu." % e)
				pdb_okay = False
		else:
			# Something odd happened. We have gremlins on the bus.
			errors.append("The uploaded file could not be retrieved. Please contact support@kortemmelab.ucsf.edu.")
			pdb_okay = False
			
	else:
		errors.append("Invalid structure file.")
		pdb_okay = False
	
	if not pdb_okay:
		return pdb_okay, pdbfile, pdb_filename, pdb_object
	else:
		pdbfile = pdbfile.replace('"', ' ')  # removes \" that mislead python. not needed anyway
		pdbfile = extract_1stmodel(pdbfile) # removes everything but one model for NMR structures
		
		pdb_object = PDB(pdbfile.split('\n'))
		if form["AtomOccupancy"].value == "remove":
			pdb_object.removeUnoccupied()
		elif form["AtomOccupancy"].value == "fill":
			pdb_object.fillUnoccupied()
		
		pdb_check_result = check_pdb(pdb_object, pdb_filename, usingClassic, ableToUseMini)
		if not pdb_check_result:
			return pdb_check_result, pdbfile, pdb_filename, pdb_object
	
	# Specific check for sequence tolerance protocol
	if protocol.dbname == "sequence_tolerance":
		if len(pdb_object.chain_ids()) < 2:
			errors.append("The %s protocol requires at least two chains to be selected - the PDB only contains %d." % (protocol.name, len(pdb_object.chain_ids())))
			pdb_okay = False

	return pdb_okay, pdbfile, pdb_filename, pdb_object


def submit(rosettaHTML, form, SID):
	''' This function processes the general parameters and writes them to the database'''
	s = StringIO()
	
	# get information from the database
	sql = 'SELECT UserID FROM Sessions WHERE SessionID = "%s"' % SID
	result = DBConnection.execQuery(sql)
	UserID = result[0][0]
	sql = 'SELECT UserName, Email FROM Users WHERE ID = "%s"' % UserID
	sql_out = DBConnection.execQuery(sql)
	UserName = sql_out[0][0]
	Email = sql_out[0][1]
	JobName = ""
	Partner = ""
	cryptID = ''
	pdbfile = ''
	pdb_object = None
	pgroup = None
	ptask = None
	StorageDBConnection = None
	
	IDtoDelete = None
	try:
		# 2 modes: check and show form
		if form.has_key("mode") and form["mode"].value == "check":
			
			# check whether all arguments were entered is done by javascript
			# if that is not the case, something went wrong and we'll get a python exception here
			# so here we could add error handling if it would be necessary
			if form.has_key("JobName"):
				JobName = escape(form["JobName"].value)
	
			try:
				pgroup, ptask = int(form["protocolgroup"].value), int(form["protocoltask"].value)		
				modus = protocolGroups[pgroup][ptask].dbname
			except:
				errors.append("No Application selected.")
				return False

			############## PDB STUFF ###################
						
			pdb_okay, pdbfile, pdb_filename, pdb_object = parsePDB(rosettaHTML, form)
			if not pdb_okay:
				return False
			############## PDB STUFF END ###############
					
											
			# Note: Forces a cap on the number of structures
			#	   This should be unnecessary as the JavaScript should enforce it
			nos = min(int(form["nos"].value), protocolGroups[pgroup][ptask].getNumStructures()[2])
				
			if form.has_key("keep_output") and int(form["keep_output"].value) == 1:
				keep_output = 1
			else:
				keep_output = 1 # ALWAYS KEEP OUTPUT FOR NOW
			
			mini = getRosettaVersion(form)

			if mini == None:
				# this is preselected in HTML code, so this case should never occur, we still make sure!
				errors.append("No Rosetta binary selected.")
				return False
			
			ProtocolParameters = {}	
			
			for protocol in protocols:					   
				if protocol.dbname == modus:
					ProtocolParameters = protocol.StoreFunction(form, pdb_object)
					if not ProtocolParameters:
						errors.append("[Admin] Server error: The store procedure for the protocol %s failed." % modus)
						return False   
			
			# todo: output where the time is going on Albana
			ProtocolParameters = pickle.dumps(ProtocolParameters)
			
			if not errors:
				# Cluster jobs are stored in the kortemmelab database
				# That database will not have access to fields in the local one e.g. different set of UserIDs messes up the UserNames, Email fields			
				RemoteInformation = {}	
				StorageDBConnection = DBConnection
				isLocalJob = True			
				if not(settings["LiveWebserver"]) and RosettaBinaries[mini]["runOnCluster"]:
					RemoteInformation = {"UserName": UserName, "Email": Email}
					StorageDBConnection = getKlabDBConnection()
					isLocalJob = False
				RemoteInformation = pickle.dumps(RemoteInformation)
				
				# if we're good to go, create new job				
				# Strip the path information from  the pdb
				m = re.match("pdbs/[A-Z\d]+/([^\\/]+\.pdb)", pdb_filename, re.IGNORECASE)
				if m:
					pdb_filename = m.group(1)
				
				# lock table
				StorageDBConnection.execQuery("LOCK TABLES backrub WRITE")
				
				# Remove other unwanted characters from pdb_filename
				pdb_filename = pdb_filename.replace("\n", "")
				
				# write information to database
				# Add a dummy hashkey as this field should not be NULL
				sql = """INSERT INTO backrub ( Date,RemoteInformation,BackrubServer,hashkey,Email,UserID,Notes, PDBComplex,PDBComplexFile,IPAddress,Host,Mini,EnsembleSize,KeepOutput,task, ProtocolParameters) 
								VALUES (NOW(), "%s", "%s", "0", "%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s")""" % (RemoteInformation, settings["ShortServerName"], Email, UserID, JobName, pdbfile, pdb_filename, IP, hostname, mini, nos, keep_output, modus, ProtocolParameters)
				
				try: 
					import random
					StorageDBConnection.execQuery(sql)
					sql = """SELECT ID FROM backrub WHERE UserID="%s" AND Notes="%s" ORDER BY Date DESC""" % (UserID , JobName)
					result = StorageDBConnection.execQuery(sql)
					ID = result[0][0]
					IDtoDelete = ID
					# create a unique key as name for directories from the ID and host, for the case we need to hide the results
					# do not just use the ID but also a random sequence
					tgb = str(ID) + settings["SQLHost"] + join(random.sample('0123456789abcdefghijklmnopqrstuvwxyz0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789', 6), '')
					cryptID = md5.new(tgb.encode('utf-8')).hexdigest()
					return_vals = (cryptID, "new", isLocalJob)
		   
					sql = 'UPDATE backrub SET cryptID="%s" WHERE ID="%s"' % (cryptID, ID)
					result = StorageDBConnection.execQuery(sql)
					# success
					
					hash_key = StorageDBConnection.generateHash(ID)
			
					# now find if there's a key like that already:
					sql = '''SELECT ID, cryptID, PDBComplexFile FROM backrub WHERE backrub.hashkey="%s" AND (Status="2" OR Status="5") AND BackrubServer="%s" AND ID!="%s"''' % (hash_key, settings["ShortServerName"], ID)
					result = StorageDBConnection.execQuery(sql)
					for r in result:
						if str(r[0]) != str(ID): # if there is ANOTHER, FINISHED simulation with the same hash
							if isLocalJob:
								oldResultsDirectory = os.path.join(settings["DownloadDir"], r[1])
								if not os.path.exists(oldResultsDirectory):
									break
								shutil.copytree(oldResultsDirectory, os.path.join(settings["DownloadDir"], cryptID)) # copy the data to a new directory
							else:
								oldResultsDirectory = os.path.join(settings["RemoteDownloadDir"], r[1])
								if not os.path.exists(oldResultsDirectory):
									break
								shutil.copytree(oldResultsDirectory, os.path.join(settings["RemoteDownloadDir"], cryptID)) # copy the data to a new directory
							sql = 'UPDATE backrub SET Status="2", StartDate=NOW(), EndDate=NOW(), PDBComplexFile="%s" WHERE ID="%s"' % (r[2], ID) # save the new/old filename and the simulation "end" time.
							result = StorageDBConnection.execQuery(sql)
							return_vals = (cryptID, "old", isLocalJob)
							break
					
					# otherwise, see if there are already two similar jobs in the queue to avoid server spamming
					sql = '''SELECT ID, cryptID, PDBComplexFile, Status FROM backrub WHERE backrub.hashkey="%s" AND (Status="0" OR Status="1") AND ID!="%s"''' % (hash_key, ID)
					results = StorageDBConnection.execQuery(sql)
					if results and len(results) > 0:
						job = results[0]
						#similarJobs = []
						#for job in results:
						#	similarJobs.append(job[0])
						#join(map(str,similarJobs),", ")
						if isLocalJob:
							localstr = ""
						else:
							localstr = "&local=false"
							
						if job[3] == 0:
							errors.append('''There is a job (<a href="%s?query=jobinfo%s&jobnumber=%s" target="_blank">#%s</a>) in the active queue with the same parameters. Please wait until it is finished to see the results.''' % (settings["ServerScript"], localstr, job[1], job[0]))
						elif job[3] == 1:
							errors.append('''There is an active job (<a href="%s?query=jobinfo%s&jobnumber=%s" target="_blank">#%s</a>) running with the same parameters. Please wait until it is finished to see the results.''' % (settings["ServerScript"], localstr, job[1], job[0]))
						else:
							errors.append('''Server error checking the job status.''')
						sql = """DELETE FROM backrub WHERE ID="%s" """ % ID
						result = StorageDBConnection.execQuery(sql)
						return False
					 
				except _mysql_exceptions.OperationalError, e:
					# This html is not used
					errors.append("Database error.")
					html = '<H1 class="title">New Job not submitted</H1>'
					if e[0] == 1054:
						errors.append("""An error occurred submitting the job.<br>SQL Error - please contact the website administrator.""")# %d: %s % (e[0], e[1]))
						#print(e[1])
					elif e[0] == 1153:
						errors.append("""<P>We are sorry but the size of the PDB file exceeds the upload limit. 
						Please revise your file and delete unneccessary entries (e.g. copies of chains, MODELS, etc.).</P>
						<P><A href="rosettaweb.py?query=submit">Submit</A> a new job.</P>""")
					else:
						errors.append("""<P>An error occurred. Please revise your data and <A href="rosettaweb.py?query=submit">submit</A> a new job. If you keep getting error messages please contact <img src="../images/support_email.png" style="vertical-align:text-bottom;" height="15">.</P>""")

					#errors.append(str(e))
					return_vals = False
			
				# unlock tables
				StorageDBConnection.execQuery("UNLOCK TABLES")
				
				return return_vals
			else:
				return False
		else:
			form['error_msg'] = 'wrong mode for submit()'
			return False
	except Exception, e:
		excinfo = sys.exc_info()
		estring = traceback.format_exc()		
		
		if StorageDBConnection:
			if IDtoDelete:
				sql = """DELETE FROM backrub where ID=%d""" % IDtoDelete
				result = StorageDBConnection.execQuery(sql)	
			StorageDBConnection.execQuery("UNLOCK TABLES")
		
		if hostname in DEVELOPMENT_HOSTS:
			errors.append("Server error: An exception occurred: %s." % estring)
		# todo: Log this to file
		errors.append("An error occurred during submission.")
		errors.append("[Admin] Server error: An exception occurred: %s." % estring)
		
		return False
	#return (True, cryptID, "new")
					


###############################################################################################
# queue()                                                                                     #
# this function shows active, pending and finished jobs                                       #
###############################################################################################

def queue(form, userid):
	# Get all jobs for this server only which have not expired		
	thisserver = settings["ShortServerName"]
	liveprefix = "SELECT True as JobIsLocal, '%s' AS server," % thisserver
	testprefix = "SELECT False as JobIsLocal, 'kortemmelab' AS server,"
	columns = "backrub.ID, backrub.cryptID, backrub.Status, Users.UserName, backrub.Date, backrub.Notes, backrub.Mini, backrub.EnsembleSize, backrub.Errors, backrub.task, Users.ID FROM backrub INNER JOIN Users WHERE backrub.UserID=Users.ID AND Expired=0 AND BackrubServer='%(thisserver)s' ORDER BY backrub.ID DESC" % vars()
	
	# Get local jobs
	sql = "%(liveprefix)s %(columns)s" % vars() 
	results = DBConnection.execQuery(sql)

	# Hide developers' jobs from the public so we can test away
	results = [line for line in results if line[5] not in DEVELOPER_USERNAMES or hostname in DEVELOPMENT_HOSTS]
	
	if not (settings["LiveWebserver"]):
		# Get all jobs on the live webserver which were submitted from this server and which have not expired
		KlabDBConnection = getKlabDBConnection()
		sql = "%(testprefix)s %(columns)s" % vars() 
		results.extend(KlabDBConnection.execQuery(sql))
		KlabDBConnection.close()

	# Sort the jobs by date rather than ID since they come from multiple databases
	# On the live server, we rely on the ID just in case the date gets messed up
	if thisserver != 'kortemmelab':
		results.sort(key = lambda x:x[6], reverse = True) 
		
	return results
########################################## end of queue() ####################################

###############################################################################################
# deletejob()                                                                                 #
# this function deletes a queued job from the database                                        #
###############################################################################################

def deletejob(form, SID):
	html = '<TD align="center">'
	
	# get logged in user
	sql = 'SELECT UserID FROM Sessions WHERE SessionID="%s"' % SID
	userID1 = DBConnection.execQuery(sql)[0][0]	
		
	if form.has_key("jobID"): # check if there is in fact a jobID
		# get user id for this job
		sql = 'SELECT UserID,Status FROM backrub WHERE ID="%s"' % (form["jobID"].value)
		userID2 = DBConnection.execQuery(sql)
		
		# job does no longer exist
		if len(userID2) == 0:
			html += "Job %s not found. <br><br>" % (form["jobID"].value)
		elif userID2[0][1] == 1:
			html += "Unable to delete job %s. Already running! <br><br>" % (form["jobID"].value)
		elif userID2[0][1] == 2:
			html += "Job %s is done. It will automatically be deleted after 10 days.<br><br>" % (form["jobID"].value)
		# see whether logged in user and job owner are the same, if not, log the cheater out!
		elif userID1 != userID2[0][0]:
			html += 'You are not allowed to delete this job! <br><font color="red"> Logout forced.</font><br><br>'
			logout(form, None, SID=SID)
			return html
		else:
			# delete the job from database only if it's still not running
			if form.has_key("button") and form["button"].value == "Delete":
				sql = 'DELETE FROM backrub WHERE ID="%s" AND UserID="%s" AND Status=0' % (form["jobID"].value, userID1)
				result = DBConnection.execQuery(sql)
				html += 'Job %s deleted. <br> <br> \n' % (form["jobID"].value)
			else:
				html += "Invalid. <br><br>"
	else:
		html += "No Job given. <br><br>"
	html += 'Proceed to <A href="rosettaweb.py?query=submit">Simulation Form</A>	or \n<A href="rosettaweb.py?query=queue">Queue</A> . <br><br> \n'
		
	return html
	
####################################### end of deletejob() ####################################

###############################################################################################
# jobinfo()                                                                                   #
# this function shows information about active, pending and finished jobs                     #
###############################################################################################

def jobinfo(form, SID):
	if form.has_key("jobnumber"):
		cryptID = form["jobnumber"].value
		isLocal = True
		if form.has_key("local") and form["local"].value == "false":
			isLocal = False
			parameter = getKlabDBConnection().getData4cryptID('backrub', cryptID)
		else:		
			parameter = DBConnection.getData4cryptID('backrub', cryptID)
		# for x,y in parameter.iteritems():
		#   print x, y, '<br>'
		if len(parameter) > 0:
			return (True, parameter, isLocal)
	
	return (False, None, True)

########################################## end of jobinfo() ###################################

def checkResidues(pdb_object, chainsreslists):
	success  = True
	
	# Check the list of residues for matches within the pdb structure
	all_chains = pdb_object.chain_ids()
	all_resids = pdb_object.aa_resids()
	resid2type = pdb_object.aa_resid2type()
	
	for (chain, lst_resid, cysteinAllowed) in chainsreslists:
		if chain in all_chains:
			for res_no in lst_resid:
				resid = "%s%4.i" % (chain, int(res_no))
				if not resid in all_resids:
					success = False
					errors.append("Residue %s not found.<br>Valid residues (displaying at most 1000) are:" % resid)
					rnumber = 0
					validres = ""
					for r in all_resids:
						validres += "%s, " % str(r)
						rnumber += 1
						if rnumber > 1000:
							break;
					errors.append(validres)
				elif resid2type[resid] == "C" and not cysteinAllowed:
					success = False
					errors.append("Mutation/design of Cysteine (CYS, C) is not permitted.")
		else:
			success = False
			errors.append("Chain '%s' not found." % chain)
	
	return success

###############################################################################################
# Protocol-specific functions - database storage                                                                                           #
###############################################################################################

def storePointMutation(form, pdb_object):						  
	"""
	 The submission logic for the single point mutations protocol.
	 If submission fails then return None.
	 Otherwise, returns a dictionary of parameters with the following fields:
		Mutations	List[(string, int, string, float)]
					 A list (of one element) containing a tuple with the fields chain, residue id, new residue, and radius
					 We use a list to allow similar logic to the Multiple Point Mutations protocol.
	"""
	key = "PM_chain"
	if form.has_key(key) and form[key].value != '':
		chain = form[key].value
		key = "PM_resid"
		if form.has_key(key) and form[key].value != '':
			resid = form[key].value
			key = "PM_newres"
			if form.has_key(key) and form[key].value != '':
				newres = form[key].value
				key = "PM_radius"
				if form.has_key(key) and form[key].value != '':
					radius = form[key].value
					
					chainsreslists = [(chain, [resid], False)] # Mutation of Cysteine is not permitted
					if checkResidues(pdb_object, chainsreslists):					   
						return {"Mutations" : [(chain, int(resid), newres, float(radius))]}
	return None

def storeMultiplePointMutations(form, pdb_object):						  
	"""
	 The submission logic for the multiple point mutations protocol.
	 If submission fails then return None.
	 Otherwise, returns a dictionary of parameters with the following fields:
		Mutations	List[(string, int, string, float)]	
					 A list of tuples containing the fields chain, residue id, new residue, and radius
	"""
	Mutations = []
	chainsreslists = []
	chainres = {}
	for x in range(ROSETTAWEB_max_point_mutation):
		key = "PM_chain%d" % x
		if form.has_key(key) and form[key].value != '':
			chain = form[key].value
			key = "PM_resid%d" % x
			if form.has_key(key) and form[key].value != '':
				resid = form[key].value
				chainres[chain] = chainres.get(chain) or []
				chainres[chain].append(resid)
				key = "PM_newres%d" % x
				if form.has_key(key) and form[key].value != '':
					newres = form[key].value
					key = "PM_radius%d" % x
					if form.has_key(key) and form[key].value != '':
						radius = form[key].value
						Mutations.append((chain, int(resid), newres, float(radius)))
		
	# Build up the chain/residues lists then check for matches within the pdb structure
	if Mutations:
		for p, residues in chainres.iteritems():
			chainsreslists.append((p, residues, False))		
		if checkResidues(pdb_object, chainsreslists):
			return {"Mutations" : sorted(Mutations)} # sort the tuples
	return None

def storeEnsemble(form, pdb_object):
	return {"dummy" : 0}
	
def storeEnsembleDesign(form, pdb_object):
	"""
	 The submission logic for the ensemble design protocol.
	 If submission fails then return None.
	 Otherwise, returns a dictionary of parameters with the following fields:
		Temperature			Float	  The temperature in kT
		NumDesignsPerStruct	Int		The number of designed sequences per ensemble structure
		SegmentLength		  Int		Length of the segment to which backrub is applied
	"""
	ProtocolParameters = None
	if form.has_key("ENS_temperature") and form["ENS_temperature"].value != '':
		if form.has_key("ENS_num_designs_per_struct") and form["ENS_num_designs_per_struct"].value != '':
			if form.has_key("ENS_segment_length") and form["ENS_segment_length"].value != '':
				ProtocolParameters = {
					"Temperature"		   :   float(form["ENS_temperature"].value),
					"NumDesignsPerStruct"   :   int(form["ENS_num_designs_per_struct"].value),
					"SegmentLength"		 :   int(form["ENS_segment_length"].value),
				}
	return ProtocolParameters

def storeSequenceToleranceHK(form, pdb_object):
	"""
	 The submission logic for the first sequence tolerance protocol.
	 If submission fails then return None.
	 Otherwise, returns a dictionary of parameters with the following fields:
		Partners	 List[Char]				 A list of chain names
		Designed	 Partners -> [Int]		  A mapping from chain names to a list of designed residues
		Weights	  List[Float]				A list of weights in the order Other, kP0P0, kP1P1, kP0P1
	"""
	if not (form.has_key("seqtol_chain1") and form["seqtol_chain1"].value != '') or not(form.has_key("seqtol_chain2") and form["seqtol_chain2"].value != ''):
		errors.append("Two chains must be entered.")
		return None						
					
	Designed = {}
	chain1 = str(form["seqtol_chain1"].value)
	chain2 = str(form["seqtol_chain2"].value)
	Designed[chain1] = []
	Designed[chain2] = []
					  
	for x in range(ROSETTAWEB_max_seqtol_design):
		key1 = "seqtol_mut_c_" + str(x)
		key2 = "seqtol_mut_r_" + str(x)
		if form.has_key(key1) and form.has_key(key2):
			chain = form[key1].value
			resid = form[key2].value
			if chain != '' and resid != '':
				if chain == chain1 or chain == chain2:
					Designed[chain].append(int(resid))
				else:
					errors.append("Chain not found.")
					return None
		else:
			break

	if not Designed[chain1] and not Designed[chain2]:
		errors.append("There must be at least one designed residue.")
		return None

	chainsreslists = []
	chainsreslists.append((chain1, Designed[chain1], False))
	chainsreslists.append((chain2, Designed[chain2], False))
	if not checkResidues(pdb_object, chainsreslists):
		return None
	
	ProtocolParameters = {
		"Partners"	  :   [chain1, chain2],
		"Designed"	  :   Designed,
		"Weights"	   :   [1.0, 1.0, 2.0],
	}
	return ProtocolParameters

def storeSequenceToleranceSK(form, pdb_object):
	"""
	 The submission logic for the second sequence tolerance protocol and the multi protocol.
	 If submission fails then return None.
	 Otherwise, returns a dictionary of parameters with the following fields:
		Partners	 List[Char]				 A list of chain names
		Premutated   Partners -> Int -> Char	A mapping from chain names to a mapping from residue positions to amino acids codes (the single letter codes used in resfiles) 
		Designed:	Partners -> Int -> {True}  A mapping from chain names to a mapping from designed residues to True
		Weights	  List[Float]				A list of weights in the order Other, kP0P0, .., kPnPn, kP0P1, .. kP0Pn, kP1P2, .., kP1Pn, .. , kPn-1Pn. This order matches the seqtol protocol documentation
		kT		   Float
	 where n+1 is the number of selected chains.
	"""
	success = True
	
	Partners = {}	   # For convenience with the weights remapping, Partners is initially a mapping from names to their entered order on the form
	Premutated = {}
	Designed = {}
	Weights = []	
	
	formproto = "%d_%d" % (int(form["protocolgroup"].value), int(form["protocoltask"].value))
	
	# Store the Partner identifiers
	# Only read up to the number of chains selected by the user
	numChainsToRead = int(form["numPartners"].value)
	numPartners = 0				
	for i in range(0, numChainsToRead):
		mkey = "seqtol_SK_chain%d" % i
		if form.has_key(mkey):
			formvalue = form[mkey].value
			#todo: one of these checks may not be needed
			if formvalue != '' and formvalue != 'ignore':
				# Sanity check: Ensure partners are distinct chains
				if Partners.get(formvalue) != None:
					success = False
					errors.append("Partner %s was chosen multiple times." % formvalue)
				Partners[formvalue] = i
				Premutated[formvalue] = {}
				Designed[formvalue] = {}
				numPartners = numPartners + 1
	
	if len(Partners) != numChainsToRead:
		errors.append("Please check that all chains were filled in.")
		return None		
		
	# If the user specified the chains in a different order from the PDB, we will need to correct this
	# all_chains is ordered by appearance in the PDB	
	all_chains = pdb_object.chain_ids()
	weightRemap = []
	for i in range(0, len(all_chains)):
		if all_chains[i] in Partners:
			weightRemap.append(Partners[all_chains[i]])
		
	# Store the Score Reweighting values, using the mapping above to fix the order. We assume the JS has done its job properly. 
	try: 
		# We order the weights to match the command-line input format e.g. Other A B A-B, or A B C A-B A-C B-C, etc.				
		
		# Add the Other energy
		Weights.append("0.4") 
			
		# Add the self-energies
		for i in range(0, numChainsToRead):
			uI = weightRemap[i]
			mkey = "seqtol_SK_kP%dP%d" % (uI, uI)
			if not(form.has_key(mkey)) or form[mkey].value == '':
				success = False
				errors.append("Partner %d was specified but its interaction energy k<sub>P<sub>%d</sub>P<sub>%d</sub></sub> was missing." % (x, x, x)) # todo: x is undefined
			else:
				Weights.append(float(form[mkey].value))
							
		# Add the interaction energies
		for i in range(0, numChainsToRead):
			uI = weightRemap[i]
			for j in range(i + 1, numChainsToRead):
				uJ = weightRemap[j]
				x = min(uI, uJ)
				y = max(uI, uJ)
				# Check that the interaction energy is filled in
				mkey = "seqtol_SK_kP%dP%d" % (x, y)
				if not(form.has_key(mkey)) or form[mkey].value == '':
					success = False
					errors.append("Partners %d and %d were specified but their interaction energy k<sub>P<sub>%d</sub>P<sub>%d</sub></sub> was missing." % (x, y, x, y))
					# else we could assign the default value of 1.0 here
				else:
					# Store kPiPj where the partners are ordered as in the PDB 
					Weights.append(float(form[mkey].value))
	except:
		errors.append("An error occurred reordering the weights matrix to match the PDB file.")
		return None
		
	# Store the residues
	scs, numDesignedResidues = storeSequenceToleranceSKResidues(form, Partners, Designed, ROSETTAWEB_SK_MaxMutations, "designed", "seqtol_SK_mut_c_", "seqtol_SK_mut_r_", None)
	success = success and scs
	if formproto == "2_1":
		scs, numPremutations = storeSequenceToleranceSKResidues(form, Partners, Premutated, ROSETTAWEB_SK_MaxPremutations, "premutated", "seqtol_SK_pre_mut_c_", "seqtol_SK_pre_mut_r_", "premutatedAA")
	elif formproto == "3_0":
		scs, numPremutations = storeSequenceToleranceSKMultiPremutations(form, Partners, Premutated, ROSETTAWEB_SK_MaxPremutations, "premutated", "seqtol_SKMulti_pre_mut_c_", "seqtol_SKMulti_pre_mut_r_", "premutatedAAMulti")
	success = success and scs
	if numDesignedResidues < 1:
		success = False
		errors.append("There must be at least one designed residue.")							   
	
	#todo: check in JS whether numeric values are actually numeric 
							   
	# Store the Boltzmann Factor
	kT = None
	if not(form.getvalue("customBoltzmann")) and form.has_key("seqtol_SK_Boltzmann") and form["seqtol_SK_Boltzmann"].value != '':
		userkT = str(form["seqtol_SK_Boltzmann"].value)
		try:
			kT = float(userkT)
		except ValueError:
			success = False
			errors.append("The Boltzmann factor was specified as '%s' which could not be read as a numeric value." % userkT)
		else:
			warnings.append("Using a user-defined value for kT (%s) rather than the published value." % userkT)
	else:
		kT = ROSETTAWEB_SK_InitialBoltzmann + numPremutations * ROSETTAWEB_SK_BoltzmannIncrease
		warnings.append("Running the job with the published value for kT = %f + %d * %f = %f." % (ROSETTAWEB_SK_InitialBoltzmann, numPremutations, ROSETTAWEB_SK_BoltzmannIncrease, kT))	
	
	parameters = {
			"Partners"	  :   Partners.keys(),
			"Premutated"	:   Premutated,
			"Designed"	  :   Designed,
			"Weights"	   :   Weights,
			"kT"			:   kT,
		}
	
	if success and SequenceToleranceSKChecks(parameters, pdb_object):
		return parameters
	else:
		return None

def storeSequenceToleranceSKResidues(form, Partners, Residues, maxNumResidues, restype, chainprefix, idprefix, aaprefix):
	success = True
	numResidues = 0
	lastRes = maxNumResidues
	for x in range(maxNumResidues):
		lastRes = x
		sx = str(x)
		key1 = chainprefix + sx
		key2 = idprefix + sx
		key3 = (not aaprefix) or (aaprefix + sx)
		if form.has_key(key1) and form[key1].value != '' and form.has_key(key2) and form[key2].value != '' and ((not aaprefix) or (len(form[key3].value) == 3)):
			numResidues = numResidues + 1
			p = form[key1].value
			residueID = int(form[key2].value)
			AAid = (not aaprefix) or (ROSETTAWEB_SK_AA[form[key3].value])
			if Partners.get(p) != None: # This is important as Python treats numeric zero as False
				if Residues[p].get(residueID):
					success = False
					errors.append("There are multiple %s residues at position %s in chain %s." % (restype, residueID, p))								
				else:
					Residues[p][residueID] = AAid
			else:
				success = False
				errors.append("The chain %s was not found for %s residue %i ('%s%4.i')." % (p, restype, x + 1, p, int(residueID)))
		else:
			break
	
	# Warn if the user left gaps in the residue list
	for x in range(lastRes + 1, maxNumResidues):
		key1 = chainprefix + str(x)
		key2 = idprefix + str(x)
		if form.has_key(key1) and form[key1].value != '' and form.has_key(key2) and form[key2].value != '':
			warnings.append("The %s residue %d ('%s%4.i') was not added to the run as previous residues were left blank." % (restype, x + 1, form[key1].value, int(form[key2].value)))

	return success, numResidues

def storeSequenceToleranceSKMultiPremutations(form, Partners, Residues, maxNumResidues, restype, chainprefix, idprefix, aaprefix):
	success = True
	numResidues = 0
	lastRes = maxNumResidues
	for x in range(maxNumResidues):
		lastRes = x
		sx = str(x)
		key1 = chainprefix + sx
		key2 = idprefix + sx
		key3 = aaprefix + sx
		AAlist = form.getlist(key3)
		if form.has_key(key1) and form[key1].value != '' and form.has_key(key2) and form[key2].value != '' and len(AAlist) > 0:
			numResidues = numResidues + 1
			p = form[key1].value
			residueID = int(form[key2].value)
			if Partners.get(p) != None: # This is important as Python treats numeric zero as False
				if Residues[p].get(residueID):
					success = False
					errors.append("There are multiple %s residues at position %s in chain %s." % (restype, residueID, p))								
				else:
					Residues[p][residueID] = AAlist
			else:
				success = False
				errors.append("The chain %s was not found for %s residue %i ('%s%4.i')." % (p, restype, x + 1, p, int(residueID)))
		else:
			break
	
	# Warn if the user left gaps in the residue list
	for x in range(lastRes + 1, maxNumResidues):
		key1 = chainprefix + str(x)
		key2 = idprefix + str(x)
		if form.has_key(key1) and form[key1].value != '' and form.has_key(key2) and form[key2].value != '':
			warnings.append("The %s residue %d ('%s%4.i') was not added to the run as previous residues were left blank." % (restype, x + 1, form[key1].value, int(form[key2].value)))

	return success, numResidues

def SequenceToleranceSKChecks(params, pdb_object):
	# Sanity checks:
	
	# Check if chain/residue pairs exist in the structure
	# Build up the chain/residues lists then check for matches within the pdb structure
	chainsreslists = []
	for p in params["Partners"]:
		chainsreslists.append((p, params["Designed"][p].keys(), False))
		chainsreslists.append((p, params["Premutated"][p].keys(), True))
	success = checkResidues(pdb_object, chainsreslists)

	# Test to see if the seqtol resfile would be empty before proceeding 
	# todo: Tidy this logic up with RosettaTasks.py and with analysis function of seqtol SK job	   
	all_resids = pdb_object.aa_resids() # todo: Calling this twice (in checkResidues as well)
	resfileHasContents, contents = make_seqtol_resfile(pdb_object, params, ROSETTAWEB_SK_Radius, all_resids)
	
	if not resfileHasContents:
		success = False
		errors.append(contents)					 
	
	return success

	
class FrontendProtocols(WebserverProtocols):

	def __init__(self, rosettaDD, rosettaHTML):
		super(FrontendProtocols, self).__init__()
		
		# Add frontend specific information
		refIDs = rosettaHTML.refs.getReferences()
		protocolGroups = self.protocolGroups
		protocols = self.protocols

		for p in protocols:
			if p.dbname == "point_mutation":
				p.setSubmitFunction(rosettaHTML.submitformPointMutation)
				p.setShowResultsFunction(rosettaHTML.showPointMutation)
				p.setStoreFunction(storePointMutation)
				p.setDataDirFunction(rosettaDD.PointMutation)
				p.setReferences("SmithKortemme:2008")
				refstring = join(['<a href="#ref%s">%d</a>' % (s, refIDs[s]) for s in p.references], ",")
				p.setDescription('''A single amino acid residue will be substituted and the neighboring 
									residues within a radius of 6&#197; of the mutated residues will be 
									allowed to change their side-chain conformations (\"repacked\"). 
									The method, choice of parameters and benchmarking are described 
									in [%s].''' % refstring)
				p.specialname = None
						
			elif p.dbname == "multiple_mutation":
				p.setSubmitFunction(rosettaHTML.submitformMultiplePointMutations)
				p.setShowResultsFunction(rosettaHTML.showMultiplePointMutations)
				p.setStoreFunction(storeMultiplePointMutations)
				p.setDataDirFunction(rosettaDD.MultiplePointMutations)
				p.setReferences("SmithKortemme:2008")
				refstring = join(['<a href="#ref%s">%d</a>' % (s, refIDs[s]) for s in p.references], ",")
				p.setDescription('''Up to 30 residues can be mutated and their neighborhoods repacked. 
									The modeling protocol is as described above for single mutations (but
									 has not been benchmarked yet).''')
				p.specialname = None

			elif p.dbname == "no_mutation":
				p.setSubmitFunction(rosettaHTML.submitformEnsemble)
				p.setShowResultsFunction(rosettaHTML.showEnsemble)	
				p.setStoreFunction(storeEnsemble)
				p.setDataDirFunction(rosettaDD.Ensemble)
				p.setReferences("SmithKortemme:2008")
				refstring = join(['<a href="#ref%s">%d</a>' % (s, refIDs[s]) for s in p.references], ",")				
				p.setDescription('''Backrub is applied to the entire input structure to generate a 
									flexible backbone ensemble of modeled protein conformations. Near-native 
									ensembles made using this method have been shown to be consistent 
									with measures of protein dynamics by Residual Dipolar Coupling 
									measurements on Ubiquitin [%s].''' % refstring)
				p.specialname = None
								
			elif p.dbname == "ensemble":
				p.setSubmitFunction(rosettaHTML.submitformEnsembleDesign)
				p.setShowResultsFunction(rosettaHTML.showEnsembleDesign)
				p.setStoreFunction(storeEnsembleDesign)
				p.setDataDirFunction(rosettaDD.EnsembleDesign)
				p.setReferences("FriedlandEtAl:2009")
				refstring = join(['<a href="#ref%s">%d</a>' % (s, refIDs[s]) for s in p.references], ",")				
				p.setDescription('''This method first creates an ensemble of structures to model 
								protein flexibility. In a second step, the generated protein structures 
								are used to predict an ensemble of low-energy sequences consistent with 
								the input structures, using computational design implemented in Rosetta. 
								The output is a sequence profile of this family of structures. For 
								ubiquitin, the predicted conformational and sequence ensembles resemble 
								those of the natural occurring protein family [%s].''' % refstring)
				p.specialname = None
						  
			elif p.dbname == "sequence_tolerance":
				p.setSubmitFunction(rosettaHTML.submitformSequenceToleranceHK)
				p.setShowResultsFunction(rosettaHTML.showSequenceToleranceHK)
				p.setStoreFunction(storeSequenceToleranceHK)
				p.setDataDirFunction(rosettaDD.SequenceToleranceHK)
				p.setReferences("HumphrisKortemme:2008")
				refstring = join(['<a href="#ref%s">%d</a>' % (s, refIDs[s]) for s in p.references], ",")				
				p.setDescription('''Predicts tolerated sequence space for up to 10 positions in protein-protein 
									interfaces.  This method is based on Rosetta 2.0.''')
				p.specialname = "Interface sequence plasticity method [%s]" % refstring
				p.progressDisplayHeight = "100px"

			elif p.dbname == "sequence_tolerance_SK":
				# Test server-specific hack to override minimum number of structures for shorter runs
				if not(settings["LiveWebserver"]):
					nos = p.getNumStructures()
					p.setNumStructures(2, nos[1], nos[2])
				p.setSubmitFunction(rosettaHTML.submitformSequenceToleranceSK)
				p.setShowResultsFunction(rosettaHTML.showSequenceToleranceSK)
				p.setStoreFunction(storeSequenceToleranceSK)
				p.setDataDirFunction(rosettaDD.SequenceToleranceSK)
				p.setReferences("SmithKortemme:2010", "SmithKortemme:2011")
				refstring = join(['<a href="#ref%s">%d</a>' % (s, refIDs[s]) for s in p.references], ", ")				
				p.setDescription('''Predicts tolerated sequences for proteins or protein-protein 
							interfaces.  This is the most recent protocol based on Rosetta 3.0.''')
				p.specialname = "Generalized RosettaBackrub sequence tolerance method [%s]"  % refstring
				p.progressDisplayHeight = "100px"
			elif p.dbname == "multi_sequence_tolerance":
				# Test server-specific hack to override minimum number of structures for shorter runs
				if not(settings["LiveWebserver"]):
					nos = p.getNumStructures()
					p.setNumStructures(2, nos[1], nos[2])
				p.setSubmitFunction(rosettaHTML.submitformSequenceToleranceSK)
				p.setShowResultsFunction(rosettaHTML.showSequenceToleranceSKMulti)
				p.setStoreFunction(storeSequenceToleranceSK)
				p.setDataDirFunction(rosettaDD.SequenceToleranceSKMulti)
				p.setReferences("SmithKortemme:2010", "SmithKortemme:2011")
				refstring = join(['<a href="#ref%s">%d</a>' % (s, refIDs[s]) for s in p.references], ", ")				
				p.setDescription('''Predicts tolerated sequences for proteins or protein-protein 
							interfaces. This does multiple runs of the PLoS ONE Sequence Tolerance protocol.''')
				p.specialname = "Generalized RosettaBackrub sequence tolerance method (multi) [%s]"  % refstring
				p.progressDisplayHeight = "660px"
			else:
				raise
		
		for pgroup in protocolGroups:
			if pgroup.name == "Point Mutation":
				desc = '''
					This function utilizes the backrub protocol implemented in Rosetta and applies it to the neighborhood of a mutated amino acid residue to model conformational changes in this region.
					There are two options.
					<dl style="text-align:left">'''
				for i in range(pgroup.getSize()):
					p = pgroup[i] 
					desc += '''<dt><b>%s</b></dt><dd style="margin-bottom:2ex">%s</dd>''' % (p.specialname or p.name, p.description)
				desc += '''</dl>'''
				pgroup.setDescription(desc)
			elif pgroup.name == "Backrub Ensemble":
				desc = '''
					This function utilizes backrub and design protocols implemented in Rosetta. 
					There are two options.
					<dl style="text-align:left;">'''
				for i in range(pgroup.getSize()):
					p = pgroup[i] 
					desc += '''<dt><b>%s</b></dt><dd style="margin-bottom:2ex">%s</dd>''' % (p.specialname or p.name, p.description)
				desc += '''</dl>'''
				pgroup.setDescription(desc)
			elif pgroup.name == "Sequence Tolerance":
				desc = '''			   
					This function utilizes backrub and design protocols in Rosetta.
					There are two implementations:
					<dl style="text-align:left;">'''
				# Add them backwards
				for i in range(pgroup.getSize() - 1, -1, -1):
					p = pgroup[i] 
					desc += '''<dt><b>%s</b></dt><dd style="margin-bottom:2ex">%s</dd>''' % (p.specialname or p.name, p.description)
				desc += '''</dl>				
					Both implementations first apply the RosettaBackrub method to generate 
					a conformational ensemble, design sequences consistent with the members 
					in the ensemble, and then combine the sequences to build a predicted sequence profile.'''
				pgroup.setDescription(desc)
			elif pgroup.name == "Private Protocols":
				desc = '''
					Private protocols for the lab go here. 
					There is currently one option.
					<dl style="text-align:left;">'''
				for i in range(pgroup.getSize()):
					p = pgroup[i] 
					desc += '''<dt><b>%s</b></dt><dd style="margin-bottom:2ex">%s</dd>''' % (p.specialname or p.name, p.description)
				desc += '''</dl>
					Tell Shane to add yours!'''
				pgroup.setDescription(desc)
			else:
				raise
					  
		# Create references for the HTML generators	
		rosettaDD.protocolGroups = protocolGroups
		rosettaHTML.protocolGroups = protocolGroups
		rosettaDD.protocols = protocols
		rosettaHTML.protocols = protocols
		

try:
	# Change True to False here to display the maintenance page
	# The maintenance page should be updated before doing so e.g. go to the website, copy the source, paste into maintenance.html, and edit to remove links etc.
	if True or hostname in DEVELOPMENT_HOSTS: 
		DBConnection = rosettadb.RosettaDB(settings)
		ws()
	else:
		F=open("maintenance.html")
		contents = F.read()
		F.close()
		sys.stdout.write("Content-type: text/html\n\n")
		sys.stdout.write(contents)
		sys.stdout.close()		
except Exception, e:
	sys.stdout.write("Content-type: text/html\n\n")
	if True or hostname in DEVELOPMENT_HOSTS:
		cgitb.handler()
		print("<br><pre>e = %s" % e)
		print("\n")
		print(str(traceback.format_exc()))
		print("<pre>")
	print "An unhandled exception occurred on the server. Please contact us if the problem persists."
