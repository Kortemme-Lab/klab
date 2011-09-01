#!/usr/bin/python2.4
# -*- coding: iso-8859-15 -*-

########################################
# Code for the admin page
########################################

from datetime import date
from string import join
import pickle
import string
from sys import maxint
import rosettadb
import calendar

userColors = {}
showHistoryForDays = 31

settings = None
protocols = None
script_filename = None

def initGoogleCharts(chartfnlist):
    html = []
    # The corechart library contains AreaChart, BarChart, and PieChart among others.
    html.append("""
            <!--Load the AJAX API-->
            <script type="text/javascript" src="https://www.google.com/jsapi"></script>
            <script type="text/javascript">
            
            // Load the Visualization API and the piechart package.
            google.load('visualization', '1', {'packages':['corechart', 'gauge']});
            </script>

            <script type="text/javascript">
            // Set a callback to run when the Google Visualization API is loaded.
            google.setOnLoadCallback(drawCharts);
            function drawCharts() {
                %s
            }
            </script>
            """ % join(chartfnlist,"\n"))
    return html

def addGroupUsageChart(GroupUsage):
    # Return values
    title = "Storage space usage by group"
    html = []
    chartsfns = []
 
    userdirs = ["home", "data", "archive"]
        
    CurrentMembers = "Current Members"
    LabAlumni = "Lab Alumni"
    PastRotationStudents = "Past Rotation Students"
    Unaccounted = "Unaccounted"
    colors = {CurrentMembers : "#ADA", LabAlumni : "#AAD", PastRotationStudents : "#D8A9DE", Unaccounted : "#EFEFEF"}

    #GroupUsage = pickle.loads(GroupUsage[0])
    
    for userdir in userdirs:
        if GroupUsage.get(userdir):
            data = GroupUsage[userdir]
            fnname = "drawGroupUsage%s" % string.capwords(userdir)
            chartsfns.append(fnname)
            html.append('''
                          
<script type="text/javascript">
function %(fnname)s() {
    // Create our data table.
    var data = new google.visualization.DataTable();
    data.addColumn('string', 'Group');
    data.addColumn('number', 'Percentage');
    data.addRows([''' % vars())
            
            chartcolors = []
            for group, percentage in sorted(data.iteritems()):
                chartcolors.append("'%s'" % colors[group])
            chartcolors = join(chartcolors, ",")
            
            for group, percentage in sorted(data.iteritems()):
                html.append('''
        ['%s', %0.2f],''' % (group, percentage))
            html.append('''
              ]);
        
              // Instantiate and draw our chart, passing in some options.
              var chart = new google.visualization.PieChart(document.getElementById('GroupUsageChart%(userdir)s'));
              chart.draw(data, {is3D: true, width: 400, height: 240, colors:[%(chartcolors)s]});
            }
            </script>
            ''' % vars())
    html.append('''<span style="text-align:center; font-size:15pt"><A NAME="%(title)s"></A>%(title)s</span><br><br><table><tr>''' % vars())
    
    for userdir in userdirs:
        if GroupUsage.get(userdir):
            html.append("<td align=center>/kortemmelab/%s</td>" % userdir)
    html.append('''</tr><tr>''')
    for userdir in userdirs:
        if GroupUsage.get(userdir):
            html.append('''<td id="GroupUsageChart%s"></td>''' % userdir)
    html.append('''</tr></table>''')
    return title, html, chartsfns  

def addDriveUsageChart(DriveUsage):
    # Return values
    title = "Drive usage"
    html = []
    chartsfns = []
 
    drives = ["ganon", "zin", "link", "zelda", "hyrule", "Webserver", "Test webserver"]
    #colors = {CurrentMembers : "#ADA", LabAlumni : "#AAD", PastRotationStudents : "#D8A9DE", Unaccounted : "#EFEFEF"}
    for drive in drives:
        nospdrive = drive.replace(" ", "")
        if DriveUsage.get(drive):
            data = DriveUsage[drive]
            fnname = "drawDriveUsage%s" % string.capwords(drive.replace(" ",""))
            chartsfns.append(fnname)
            html.append('''
                          
<script type="text/javascript">
function %(fnname)s() {
    // Create our data table.
    var data = new google.visualization.DataTable();
    data.addColumn('string', 'Label');
    data.addColumn('number', 'Value');
    data.addRows([''' % vars())
            
            #chartcolors = []
            #for group, percentage in sorted(data.iteritems()):
            #    chartcolors.append("'%s'" % colors[group])
            #chartcolors = join(chartcolors, ",")
            
            html.append('''
        ['%s', %d],''' % (drive, int(data["Use%"][0:-1])))
            html.append('''
              ]);
        
              // Instantiate and draw our chart, passing in some options.
              var chart = new google.visualization.Gauge(document.getElementById('DriveUsageChart%(nospdrive)s'));
              chart.draw(data, {width: 300, height: 180, greenColor: '#ff0', greenFrom: 70, greenTo: 80, yellowFrom: 80, yellowTo: 90, redFrom: 90, redTo: 100,});
            }
            </script>
            ''' % vars())
    html.append('''<span style="text-align:center; font-size:15pt"><A NAME="%(title)s"></A>%(title)s</span>''' % vars())
    
    html.append('''<table style="border-spacing:40pt 1pt"><tr>''')
    
    counter = 0
    for drive in drives:
        nospdrive = drive.replace(" ", "")
        if DriveUsage.get(drive):
            html.append('''<td><table><tr><td id="DriveUsageChart%s"></td></tr><tr><td align=center>Size: %s</td></tr></table></td>''' % (nospdrive, DriveUsage[drive]["Size"]))
        counter += 1
        if counter >= 5:
            # Show 5 drives per row
            html.append('''</tr><tr>''')
            counter = 0
    html.append('''</tr></table>''')
    return title, html, chartsfns  

def addStorageSpaceChart(quotas, usage, users):
    # Return values
    title = "Storage space usage"
    html = []
    chartsfns = []
    latestdate = usage[-1][0]
    
    # Assume ordered by date and get the most recent data
    dailyquotas = quotas[-showHistoryForDays:]
    
    # Convert the data into a table indexed by dates whose values are tables indexed by user of their storage on that day     
    usagetbl = {}
    for use in usage:
        usagetbl[use[0]] = usagetbl.get(use[0]) or {}
        usagetbl[use[0]][use[1]] = pickle.loads(use[2])
        
    CurrentMembers = "Current Members"
    LabAlumni = "Lab Alumni"
    PastRotationStudents = "Past Rotation Students"
    Unaccounted = "Unaccounted"
    colors = {CurrentMembers : "#ADA", LabAlumni : "#AAD", PastRotationStudents : "#D8A9DE", Unaccounted : "#EFEFEF"}

    #GroupUsage = pickle.loads(GroupUsage[0])
    
    userdirs = ["home", "data", "archive", "numfiles"]
    
    for userdir in userdirs:
 
        sortedUsers = []
        if userdir != "numfiles":
            for k,v in sorted(usagetbl[latestdate].iteritems(), key=lambda(k,v): -v.get(userdir, {}).get("SizeInMB", 0)):
                sortedUsers.append(k)
        else:
            for k,v in sorted(usagetbl[latestdate].iteritems(), key=lambda(k,v): -v.get(userdir, 0)):
                sortedUsers.append(k)
        missingUsernames = set([u[0] for u in users])
        missingUsernames = missingUsernames.difference(set(sortedUsers))
        sortedUsers.extend(list(missingUsernames))
        
        if userdir == "numfiles":
            yAxisTitle = "Number of files"
        else:
            yAxisTitle = "Usage in GB"
            
        fnname = "drawSpaceUsage%s" % string.capwords(userdir)
        chartsfns.append(fnname)
        html.append('''
                      
    <script type="text/javascript">
    function %(fnname)s() {
    // Create our data table.
    var data = new google.visualization.DataTable();''' % vars())
    
        # Add X-axis
        html.append(''' data.addColumn('string', 'Date');''')
        
        # Add quota datapoint
        if userdir == "archive":
            
            OtherData = None
            suffix = ""
            if dailyquotas[-1][3]:
                OtherData = pickle.loads(dailyquotas[-1][3])
                suffix = " (90%)"
            
            html.append(''' data.addColumn('number', 'Stress threshold%s');''' % suffix)
        else:
            html.append(''' data.addColumn('number', 'Quota');''')

        # Add used datapoint
        if userdir == "archive":
            html.append(''' data.addColumn('number', 'Used');''')

        # Add user datapoints
        for user in sortedUsers:
            html.append('''data.addColumn('number', '%s');''' % user)    
        
        html.append('''data.addRows(%d);''' % len(dailyquotas))
        
        diff = 0
        minValue = 0 # Prefer zero-based graphs
        maxValue = 0
        for i in range(len(dailyquotas)):
            # Date, Quotas, DriveUsage, OtherData, GroupUsage
            quota = dailyquotas[i]
            Quotas = pickle.loads(quota[1])
            OtherData = None
            if quota[3]:
                OtherData = pickle.loads(quota[3])

            dt = quota[0]
            
            quotaValue = (Quotas.get(userdir) or 0)
            if userdir == "archive" and OtherData and OtherData.get("ArchiveHogThresholdInGB"):
                quotaInGB = OtherData["ArchiveHogThresholdInGB"]
            else:
                quotaInGB = quotaValue / 1024
            
            # Add quota
            html.append('''data.setValue(%d, 0, '%s');''' % (i, dt))
            if userdir == "numfiles":
                html.append('''data.setValue(%d, 1, %d);''' % (i, quotaValue))
            else:
                html.append('''data.setValue(%d, 1, %d);''' % (i, quotaInGB))
            
            # Add user datapoints
            startindex = 2
            if userdir == "archive":
                startindex = 3
            sumUsageInGB = 0
                
            if userdir == "numfiles":
                for j in range(len(sortedUsers)):
                    
                    Filecount = 0
                    if usagetbl[dt].get(sortedUsers[j]):
                        Filecount = usagetbl[dt][sortedUsers[j]][userdir]
                    maxValue = max(maxValue, Filecount)
                    minValue = min(maxValue, Filecount)
                    html.append('''data.setValue(%d, %d, %d);''' % (i, j + startindex, Filecount))
                    diff += 4
            else:
                for j in range(len(sortedUsers)):
                    UsageInGB = 0
                    if usagetbl[dt].get(sortedUsers[j]):
                        UsageInGB = float(usagetbl[dt][sortedUsers[j]][userdir]["SizeInMB"]) / float(1024)
                    sumUsageInGB += UsageInGB
                    maxValue = max(maxValue, UsageInGB)
                    minValue = min(maxValue, UsageInGB)
                    html.append('''data.setValue(%d, %d, %0.3f);''' % (i, j + startindex, UsageInGB))
                    diff += 4
            
            if userdir == "archive":
                html.append('''data.setValue(%d, 2, %d);''' % (i, sumUsageInGB))
                
            
            diff += 10
            
            
            #chartcolors = []
            #for group, percentage in sorted(data.iteritems()):
            #    chartcolors.append("'%s'" % colors[group])
            #chartcolors = join(chartcolors, ",")
        
        maxValue *= 1.05
        
        if userdir == "archive":
            usages = pickle.loads(quotas[-1][2])
            tuserdir = "/%s usage (current : %s)" % (userdir, usages["zin"]["Use%"])
        elif userdir == "numfiles":
            tuserdir = 'Number of files in storage'
        else:
            tuserdir = '/%(userdir)s usage' % vars()
            
        if userdir == "archive":
            colorlist = [('black', 4), ('red', 4)]
        else:
            colorlist = [('black', 4)]
        
        global userColors
        for i in range(len(sortedUsers)):
            colorlist.append((userColors[sortedUsers[i]], 2))
        
        seriesformat = ["%d:{color: '%s', lineWidth: %d}" % (i, colorlist[i][0], colorlist[i][1]) for i in range(len(colorlist))]
        seriesformat = join(seriesformat,", ")
        seriesformat = "series:{%s}" % seriesformat 
        
        html.append('''
          // Instantiate and draw our chart, passing in some options.
          var chart = new google.visualization.LineChart(document.getElementById('SpaceUsageChart%(userdir)s'));
          chart.draw(data, {hAxis:{slantedText:true,slantedTextAngle:60}, backgroundColor:{strokeWidth:3}, pointSize:2, vAxis:{title:'%(yAxisTitle)s', minValue:%(minValue)d, maxValue:%(maxValue)d}, lineWidth: 2, %(seriesformat)s, width: 1200, height: 640, title: '%(tuserdir)s'});
        }
        </script>
        ''' % vars())
        
    html.append('''<span style="text-align:center; font-size:15pt"><A NAME="%(title)s"></A>%(title)s</span><br><br>''' % vars())

    #html.append("<table>")
    subtitles = []
    for userdir in userdirs:
        subtitle = "/%s usage" % userdir
        subtitles.append(subtitle)
        html.append('''<A NAME="%s"></A><div id="SpaceUsageChart%s"></div><br><br>''' % (subtitle, userdir))
        #html.append('''<tr><td id="SpaceUsageChart%s"><span><A NAME="%s">.</A></span></td></tr>''' % (userdir, subtitle))
    #html.append('''</table>''')
    return (title, subtitles), html, chartsfns  


def simpleHash(instr):
    hash = 0
    i = 7
    instr = map(ord, instr)
    for c in instr:
        hash += (i * c) % 157
        i += 19
    hash = hex(hash % 256)[2:]
    if len(hash) == 1:
        hash = "0" + str(hash)
    return hash

def generateDiskStatsSubpage(quotas, usage, users):
    html = []
    charthtml = []
    chartfns = []
    titles = []
    
    GroupUsage = None
    DriveUsage = None
    
    # Create colors for users
    global userColors
    userColors = {}
    for j in range(len(users)):
        userColors[users[j][0]] = "#%s%s%s" % (simpleHash(users[j][0]), simpleHash(users[j][1]), simpleHash(users[j][3]))
    
    # Assume ordered by date and get the most recent data
    quota = quotas[-1]
    dt = quota[0]
    DriveUsage = pickle.loads(quota[2])
    GroupUsage = pickle.loads(quota[4])
    
    generators = [
        [addDriveUsageChart, DriveUsage],
        [addStorageSpaceChart, quotas, usage, users],
        [addGroupUsageChart, GroupUsage],
    ]
    
    for g in generators:
        if len(g) > 1:
            gtitles, ghtml, gchartfns = g[0](*g[1:])
            titles.append(gtitles)
            charthtml.extend(ghtml)
            charthtml.append("<br><br>")
            chartfns.extend(gchartfns)
        else:
            charthtml.extend(g[0]())
    
    # Prepare javascript calls
    for i in range(len(chartfns)):
        chartfns[i] += "();"

    # Titles
    html.append('''<table><tr><td style="text-align:left"><div style="font-size:15pt">Statistics up to %s:</div><ol>''' % dt)
    for i in range(0, len(titles)):
        title = titles[i]
        if type(title) == type(""):
            html.append('''<li><a href="#%s">%s</a>''' % (title, title))
        elif type(title) == type((None,)):
            html.append('''<li><a href="#%s">%s</a>
                           <ol>''' % (title[0], title[0]))
            for j in range(0, len(title[1])):
                html.append('''<li><a href="#%s">%s</a>''' % (title[1][j], title[1][j]))
            html.append("</ol>")
                
    html.append("</ol></td></tr></table><br><br>")
    
    html.extend(initGoogleCharts(chartfns))
    html.extend(charthtml)
    return html

from cStringIO import StringIO

def getKlabDBConnection():
	return rosettadb.RosettaDB(settings, host = "kortemmelab.ucsf.edu")

def getKortemmelabUsersConnection():
	return rosettadb.RosettaDB(settings, host = "kortemmelab.ucsf.edu", db = "KortemmeLab", admin = True)

def getAlbanaConnection():
	return rosettadb.RosettaDB(settings)

def getWebsiteUsers():
	# Get all jobs on the live webserver which were submitted from this server and which have not expired
	connection = getKlabDBConnection()
	sql = '''SELECT ID, UserName, Concat(FirstName, ' ', LastName) AS Name, Email, Institution, Address1, Address2, City, State, Zip, Country, Phone, Date, LastLoginDate, Priority, Jobs, EmailList FROM Users ORDER BY UserName''' 
	result = connection.execQuery(sql, cursorClass = rosettadb.DictCursor)
	return result

def getUsers():
	# Get all jobs on the live webserver which were submitted from this server and which have not expired
	connection = getKortemmelabUsersConnection()
	sql = '''SELECT Concat(FirstName, ' ', Surname), Username, Email, SecondaryEmail, Status, DOB, ReceiveDailyMeetingsEmail, ReceiveWeeklyMeetingsEmail, ReceiveUpdateMeetingsEmail FROM Users WHERE Status="current" ORDER BY FirstName, Surname''' 
	result = list(connection.execQuery(sql))
	sql = '''SELECT Concat(FirstName, ' ', Surname), Username, Email, SecondaryEmail, Status, DOB, ReceiveDailyMeetingsEmail, ReceiveWeeklyMeetingsEmail, ReceiveUpdateMeetingsEmail FROM Users WHERE Status="alumni" ORDER BY FirstName, Surname''' 
	result.extend(list(connection.execQuery(sql)))
	sql = '''SELECT Concat(FirstName, ' ', Surname), Username, Email, SecondaryEmail, Status, DOB, ReceiveDailyMeetingsEmail, ReceiveWeeklyMeetingsEmail, ReceiveUpdateMeetingsEmail FROM Users WHERE Status="pastrotationstudent" ORDER BY FirstName, Surname''' 
	result.extend(list(connection.execQuery(sql)))
	users = []
	for record in result:
		users.append({
						"name" : record[0],
						"username" : record[1],
						"email" : [record[2], record[3]],
						"status" : record[4],
						"DOB"	: record[5],
						"daily" : record[6],
						"weekly" : record[7],
						"update" : record[8],
					})
	return users

def generateWebUsersSubpage():
	html = []
	userlist = getWebsiteUsers()
	html.append("""<H1 align=left > Kortemme Lab users </H1> <br>
		<div >
		<table  border=1 cellpadding=2 cellspacing=0 width=1200 >
		<colgroup>
			 <col >
			 <col width="30">
			 <col width="200">
			 <col width="150">
			 <col width="200">
			 <col width="150">
			 <col width="50">
			 <col width="200">
			 <col width="120">
			 <col >
			 <col >
			 <col >
		</colgroup>
		<tr align=left bgcolor="#828282" style="color:white;"> 
		<td> Username </td> 
		<td> ID </td> 
		<td> Name </td> 
		<td> Email </td>
		<td> Institution</td>
		<td> Address</td>
		<td> Phone </td>
		<td> Member since </td>
		<td> Last login </td>
		<td> Priority </td>
		<td> Jobs </td>
		<td> EmailList </td>
		</tr>""")
	
	for user in userlist:
		html.append("""<tr bgcolor='#ffe' onmouseover="this.style.background='#5d5';" onmouseout="this.style.background='#ffe'; ">""")
		html.append("<td>%(UserName)s</td>" % user) 
		html.append("<td>%(ID)s</td>" % user) 
		html.append("<td>%(Name)s</td>" % user) 
		if "@" in user["Email"] and '"' not in user["Email"]:
			html.append("""<td><a href="mailto:%(Email)s">%(Email)s</a></td>""" % user) 
		else:
			html.append("<td>%(Email)s</td>" % user) 
		html.append("<td>%(Institution)s</td>" % user)
		address = [user["Address1"], user["Address2"], user["City"], user["State"], user["Zip"], user["Country"]]
		address = [a for a in address if a] 
		html.append("<td>%s</td>" % join(address, "<br>"))
		html.append("<td>%(Phone)s</td>" % user)
		dt = user["Date"]
		if dt:
			html.append("<td>%s-%s-%s</td>" % (dt.year, dt.month, dt.day))
		else:
			html.append("<td></td>")
		html.append("<td>%(LastLoginDate)s</td>" % user)
		html.append("<td>%(Priority)s</td>" % user)
		html.append("<td>%(Jobs)s</td>" % user)
		if user["EmailList"]:
			html.append("<td>Y</td>" % user)
		else:
			html.append("<td>N</td>" % user)
		html.append("</tr>")
	html.append('</table> </div>')
	return html

def generateLabUsersSubpage():
	html = []
	userlist = getUsers()
	html.append("""<H1 align=left > Website users </H1> <br>
		<div >
		<table  border=0 cellpadding=2 cellspacing=0 width=800 >
		<colgroup>
			 <col width="200">
			 <col width="80">
			 <col width="90">
			 <col width="250">
			 <col width="150">
			 <col >
			 <col >
		</colgroup>
		<tr align=center style="color:white;">
		<td colspan="5"></td>
		<td colspan="3" bgcolor="#828282">Lab meetings emails</td>
		</tr> 
		<tr align=left bgcolor="#828282" style="color:white;"> 
		<td > Name </td> 
		<td > Username </td> 
		<td > Email </td>
		<td > Status</td>
		<td > Birthday </td>
		<td > Daily </td>
		<td > Weekly </td>
		<td > Update </td>
		</tr>""")
	
	CurrentMembers = "Current Members"
	LabAlumni = "Lab Alumni"
	PastRotationStudents = "Past Rotation Students"
	Unaccounted = "Unaccounted"
	colors = {CurrentMembers : "#ADA", LabAlumni : "#AAD", PastRotationStudents : "#D8A9DE", Unaccounted : "#EFEFEF"}
	
	for user in userlist:
		html.append("<tr ")
		if user["status"] == "current":
			html.append('bgcolor="%s"' % colors[CurrentMembers])
			user["status"] = "Current"
		elif user["status"] == "alumni":
			html.append('bgcolor="%s"' % colors[LabAlumni])
			user["status"] = "Alumni"
		elif user["status"] == "pastrotationstudent":
			html.append('bgcolor="%s"' % colors[PastRotationStudents])
			user["status"] = "Past rotation student"
			
		html.append("><td>%(name)s</td>" % user) 
		html.append("<td>%(username)s</td>" % user)
		html.append("<td>")
		addresses = []
		for address in user["email"]:
			if address:
				addresses.append(address)
		if addresses:
			html.append(join(addresses, ", "))
		html.append("</td>")
		html.append("<td>%(status)s</td>" % user)
		if user["DOB"]:
			month = calendar.month_name[user["DOB"].month]
			day = user["DOB"].day
			html.append("<td>%(month)s %(day)s</td>" % vars())
		else:
			html.append("<td></td>") 
		
		if user["daily"]:
			html.append("<td align=center>Y</td>")
		else:
			html.append("<td></td>")
		if user["weekly"]:
			html.append("<td align=center>Y</td>")
		else:
			html.append("<td></td>")
		if user["update"]:
			html.append("<td align=center>Y</td>")
		else:
			html.append("<td></td>")
			
		html.append("</tr>")
	html.append('</table> </div>')
	return html

def getJobs():
	'''Get all jobs on the live webserver which were submitted from this server and which have not expired'''
	results = []
	querystr = []

	querystr.append("SELECT '%s' AS ExecutionServer, backrub.ID, backrub.cryptID, backrub.Status, Users.UserName, backrub.Date, backrub.Notes, backrub.AdminErrors,")
	querystr.append("backrub.Mini, backrub.EnsembleSize, backrub.Errors, backrub.task, backrub.backrubserver AS SubmissionServer, backrub.Expired, backrub.AdminCommand")
	querystr.append("FROM backrub INNER JOIN Users WHERE backrub.UserID=Users.ID ORDER BY backrub.ID DESC") 
	querystr = join(querystr, " ")
	connections = [('kortemmelab', getKlabDBConnection()), ('albana', getAlbanaConnection())]
	for connection in connections:
		results.extend(connection[1].execQuery(querystr % connection[0], cursorClass = rosettadb.DictCursor))
		connection[1].close()

	# Sort the jobs by date
	results.sort(key = lambda x:x["Date"], reverse = True) 

	return results

def generateJobAdminSubpage():
	html = []
	job_list = getJobs() 
	html.append("""<H1> Job queue </H1> <br>
		<div>
		<table border=0 cellpadding=2 cellspacing=0 width=1600>
		 <colgroup>
		   <col width="50">
		   <col width="35">
		   <col width="70">
		   <col width="80">
		   <col width="30">
		   <col width="35">
		   <col width="120">
		   <col width="185">
		   <col width="160">
		   <col width="25">
		   <col width="95">
		   <col width="100">
		 </colgroup>
		<tr><td colspan="11">If a job has failed, mouse-over the Status field to display a stacktrace (if available).</td></tr>
		<tr><td colspan="11">Expired jobs should not be visible to users of the public website.</td></tr>
		<tr><td></td></tr>
		<tr align=center bgcolor="#828282" style="color:white;"> 
		 <td> Server </td> 
		 <td> ID </td> 
		 <td> User Name </td>
		 <td> Job Name </td>
		 <td> Status </td> 
		 <td> Expired </td> 
		 <td> Date (PST) </td>
		 <td> Admin </td>
		 <td> Rosetta Application </td>
		 <td> Structures </td>
		 <td> PDB </td>
		 <td> CryptID </td>
		 </tr>
		 \n""")

	for line in job_list:
		thisserver = settings["ShortServerName"]
		submissionserver = line["SubmissionServer"]
		executionserver = line["ExecutionServer"]
		jobIsLocal = (executionserver == submissionserver)
		
		task = line["task"]
		task_color = "#888888"
		for p in protocols:
			if task == p.dbname:
				task = p.name
				task_color = p.group.color
				break
		
		bgcolor = "#EEEEEE"
		if not jobIsLocal:
			bgcolor = "#DDDDFF"

		if submissionserver != thisserver:
			link_to_job = 'onclick="window.location.href=\'https://%s.ucsf.edu/%s?query=jobinfo&amp;jobnumber=%s\'"' % ( submissionserver, script_filename, line["cryptID"] )
		elif jobIsLocal:
			link_to_job = 'onclick="window.location.href=\'%s?query=jobinfo&amp;jobnumber=%s\'"' % ( script_filename, line["cryptID"] )
		else:
			link_to_job = 'onclick="window.location.href=\'%s?query=jobinfo&amp;local=false&amp;jobnumber=%s\'"' % ( script_filename, line["cryptID"] )
		
		html.append("""<tr align=center bgcolor="%s" onmouseover="this.style.background='#447DAE'; this.style.color='#FFFFFF';" onmouseout="this.style.background='%s'; this.style.color='#000000';" >""" % (bgcolor, bgcolor))

		# write submission server
		colors = {"kortemmelab" : '#aaaaff', "albana" : "#FFA500"} # todo: use the actual colors here
		if not jobIsLocal:
			html.append('<td %s bgcolor="%s" class="lw">%s&rarr;%s</td>' % (link_to_job, colors.get(submissionserver, "#666666"), submissionserver, executionserver))
		else:
			html.append('<td %s bgcolor="%s" class="lw">%s</td>' % (link_to_job, colors.get(submissionserver, "#666666"), submissionserver))

		# write ID
		html.append('<td %s class="lw">%s </td>' % (link_to_job, str(line["ID"])))
		
		# write username
		html.append('<td %s class="lw">%s</td>' % (link_to_job, str(line["UserName"])))
		
		# write jobname
		html.append('<td %s class="lw">%s</td>' % ( link_to_job, str(line["Notes"])))
		
		# write status 
		status = int(line["Status"])
		admincmd = line["AdminCommand"] or ""
		if admincmd:
			admincmd = "<br><font color='#00f'>[%s]</font>" % admincmd
		if status == 0:
			html.append('<td %s class="lw"><font color="orange">in queue%s</font></td>' % (link_to_job, admincmd) )
		elif status == 1:
			html.append('<td %s class="lw"><font color="green">active%s</font></td>' % (link_to_job, admincmd))
		elif status == 2:
			html.append('<td %s class="lw"><font color="black">done%s</font></td>' % (link_to_job, admincmd)) # <font color="darkblue" %s></font>
		elif status == 5:
			html.append('<td %s class="lw" style="background-color: #AFE2C2;"><font color="darkblue">sample%s</font></td>' % (link_to_job, admincmd))
		else:
			# write error
			errors = line["Errors"]
			errorstr = str(errors) 
			if  errorstr != '' and errors != None:
				adminerrorstr = ''
				if line["AdminErrors"]:
					adminerrorstr = str(line["AdminErrors"])
				tooltiptext = "%s\n%s" % (errorstr, adminerrorstr)
				
				html.append('''<td %(link_to_job)s title='%(tooltiptext)s' >
					<font color="FF0000">error</font>
					(<a href="https://kortemmelab.ucsf.edu/backrub/wiki/Error#Errors_during_the_simulation" target="_blank"
					onmouseover="this.style.color=clear'#FFFFFF'" onmouseout="this.style.color='#365a79'">%(errorstr)s%(admincmd)s</a>)</td>''' % vars())
			else:
				html.append('<td class="lw"><font color="FF0000">error%s</font></td>' % admincmd)
		
		# write expiration 
		expired = int(line["Expired"])
		if expired:
			expiredcmd = "revive"
			html.append('<td %s class="lw"><font color="red"><b>Y</b></font></td>' % link_to_job)
		else:
			expiredcmd = "expire"
			html.append('<td %s class="lw">N</td>'  % link_to_job)
		
		# write date
		html.append('<td %s class="lw" style="font-size:small;">%s</td>' % (link_to_job, str(line["Date"])))
		
		# Admin commands
		#   Restart job and kill buttons
		html.append('''<td class="lw" bgcolor="#ddd">''')
		
		# Add this after if we want to switch focus: //if (window.focus) {newwindow.focus();}
		if status == 2:
			html.append('''<button onclick="
			if (confirm('Are you sure you want to restart the job?') && confirm('Really?!')){
				window.open('%s?query=admincmd&amp;cmd=restart&amp;job=%d&amp;server=%s','KortemmeLabAdmin','height=400,width=850');
				document.adminform.query.value='admin';
				document.adminform.submit();
			}">restart</button>''' % (script_filename, line["ID"], executionserver))
			html.append('''<button disabled="disabled">kill</button>''')
		else:
			html.append('''<button disabled="disabled">restart</button>''')
			html.append('''<button onclick="
			if (confirm('Are you sure you want to kill the job?') && confirm('Really?!')){
				window.open('%s?query=admincmd&amp;cmd=kill&amp;job=%d&amp;server=%s','KortemmeLabAdmin','height=400,width=850');
				document.adminform.query.value='admin';
				document.adminform.submit();
			}">kill</button>''' % (script_filename, line["ID"], executionserver))
			
		html.append('''<button onclick="
			window.open('%s?query=admincmd&amp;cmd=%s&amp;job=%d&amp;server=%s','KortemmeLabAdmin','height=400,width=850');
			document.adminform.query.value='admin';
			document.adminform.submit();
			">%s</button>''' % (script_filename, expiredcmd, line["ID"], executionserver, expiredcmd))
		if admincmd:
			html.append('''<button onclick="
			window.open('%s?query=admincmd&amp;cmd=clear&amp;job=%d&amp;server=%s','KortemmeLabAdmin','height=400,width=850');
			document.adminform.query.value='admin';
			document.adminform.submit();
			">clear</button>''' % (script_filename, line["ID"], executionserver))
		else:
			html.append('''<button disabled="disabled">clear</button>''')
		
		html.append("</td>")
				
		# Rosetta version
		# todo: the mini/classic distinction is somewhat deprecated with the new seqtol protocol
		miniVersion = line["Mini"]
		html.append('<td %s class="lw" style="font-size:small;" bgcolor="%s"><i>%s</i><br>%s</td>' % (link_to_job, task_color, miniVersion, task))
		
		# write size of ensemble
		html.append('<td %s class="lw">%s</td>' % (link_to_job, str(line["EnsembleSize"])))
		
		html.append('''<td class="lw" bgcolor="#ddd"><button onclick="window.open('%s?query=PDB&amp;job=%d&amp;server=%s')">PDB</button><button onclick="window.open('%s?query=PDB&amp;job=%d&amp;server=%s&amp;plain=true')">Raw</button></td>''' % (script_filename, line["ID"], executionserver, script_filename, line["ID"], executionserver))
		
		html.append('<td %s class="lw">%s</td>' % (link_to_job, line["cryptID"]))
		
		html.append("</tr>\n")
		link_to_job
	html.append('</table> </div>')
	return html

def generateAdminPage(quotas, usage, users, settings_, rosettahtml, form):

	global settings
	global protocols
	global script_filename
	settings = settings_
	protocols = rosettahtml.protocols
	script_filename = rosettahtml.script_filename 
	
	adminpage = ""
	if form.has_key("AdminPage"):
		adminpage = form["AdminPage"].value
		
	# Create menu
	html = []
	html.append("<td align=center>")
	html.append('''<FORM name="adminform" method="post">''')
	html.append('''<input type="button" value="Disk stats" onClick="showPage('diskstats');">''')
	html.append('''<input type="button" value="Job administration" onClick="showPage('jobadmin');">''')
	html.append('''<input type="button" value="Website users" onClick="showPage('webusers');">''')
	html.append('''<input type="button" value="Lab users" onClick="showPage('labusers');">''')
	html.append('''<input type="button" value="Refresh" onClick="document.adminform.query.value='admin'; document.adminform.submit();">''')
	html.append('''<input type="hidden" NAME="AdminPage" VALUE="%s">''' % adminpage)
	html.append('''<input type="hidden" NAME="query" VALUE="">''')
	html.append('''</FORM>''')
	html.append("</td></tr><tr>")
	
	html.append("<td align=left>")
	
	# Disk stats
	html.append('<div style="display:none" id="diskstats">')
	html.extend(generateDiskStatsSubpage(quotas, usage, users))
	html.append("</div>")
	
	# Job admin
	html.append('<div style="display:none" id="jobadmin">')
	html.extend(generateJobAdminSubpage())
	html.append("</div>")

	# Website users
	html.append('<div style="display:none" id="webusers">')
	html.extend(generateWebUsersSubpage())
	html.append("</div>")

	# Job admin
	html.append('<div style="display:none" id="labusers">')
	html.extend(generateLabUsersSubpage())
	html.append("</div>")
		
	html.append("</td>")
	html.append('''<script src="/backrub/frontend/admin.js" type="text/javascript"></script>''')

	return html