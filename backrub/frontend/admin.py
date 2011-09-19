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
from rosettahelper import DEVELOPMENT_HOSTS, DEVELOPER_USERNAMES

import locale
locale.setlocale(locale.LC_ALL, 'en_US')

userColors = {}
showHistoryForDays = 31

settings = None
protocols = None
script_filename = None

CurrentMembers = "Current Members"
LabAlumni = "Lab Alumni"
PastRotationStudents = "Past Rotation Students"
Unaccounted = "Unaccounted"
LimboUsers = "Recently left"
colors = {CurrentMembers : "#ADA", LabAlumni : "#AAD", PastRotationStudents : "#D8A9DE", LimboUsers : "#AAD", Unaccounted : "#EFEFEF"}

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

def getSortedUsers(usagetbl, latestdate, users, userdir):
	sortedUsers = []
	if userdir == "numfiles":
		for k,v in sorted(usagetbl[latestdate].iteritems(), key=lambda(k,v): -v.get(userdir, 0)):
			sortedUsers.append(k)
	else:
		for k,v in sorted(usagetbl[latestdate].iteritems(), key=lambda(k,v): -v.get(userdir, {}).get("SizeInMB", 0)):
			sortedUsers.append(k)
	missingUsernames = set([u[0] for u in users])
	missingUsernames = missingUsernames.difference(set(sortedUsers))
	sortedUsers.extend(list(missingUsernames))
	return sortedUsers

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
		
	# todo: Store this info in the db. Special case for users who are not current users but whose data directories have not been moved
	limbousers = ['colin', 'meames', 'dmandell']

	userstatus = {}
	for user in users:
		userstatus[user[0]] = user[4]
	
	# Create the numfiles chart
	userdirs = ["home", "data", "archive"]
	for dirname_ in ["numfiles"]:
		sortedUsers = getSortedUsers(usagetbl, latestdate, users, "numfiles")
		yAxisTitle = "Number of files"
		fnname = "drawSpaceUsageNumfiles"
		chartsfns.append(fnname)
						
		html.append('''<script type="text/javascript">
	var numfiles_chart;
	var numfiles_dataview;
	var numfiles_currentusers;
	var numfiles_pastusers;
	var numfiles_allusers;
	var numfiles_nousers;
		  
	function %(fnname)s() {
	// Create our data table.
	var data = new google.visualization.DataTable();\n
	data.addColumn('string', 'Date');\n''' % vars())
	
		html.append('''data.addColumn('number', 'Quota home + data');\n''')
		for userdir in userdirs:
			html.append('''data.addColumn('number', 'Quota %(userdir)s');\n	''' % vars())
		
		# Add user datapoints
		numpoints = len(dailyquotas)
		numrows = numpoints * (len(userdirs) + 1) # 1 extra for data + home
		for user in sortedUsers:
			html.append('''data.addColumn('number', '%s');\n''' % user)	
		html.append('''data.addRows(%d);\n''' % numrows)
		minValue = 0 # Prefer zero-based graphs
		maxValue = 0
		startindex = 1 + 1 + len(userdirs) # Date, home+data, userdirs
		
		# Counters for the total number of files
		dirtotals = {}
		for userdir in userdirs:
			dirtotals[userdir] = 0
		
		sumFilecount = [[] for i in range(numpoints)]
		for i in range(numpoints):
			# Date, Quotas, DriveUsage, OtherData, GroupUsage
			quota = dailyquotas[i]
			Quotas = pickle.loads(quota[1])
			OtherData = None
			if quota[3]:
				OtherData = pickle.loads(quota[3])

			dt = quota[0]
			quotaValue = 0 #(Quotas.get("numfiles") or 0)
			
			quotaValue = Quotas["numfiles"][CurrentMembers]
			alumniQuotaValue = Quotas["numfiles"][LabAlumni]
			
			sumFilecount[i] = [0 for sfc in range(len(userdirs) + 1)]
			
			# Add quota
			for rangedi in range(i, numrows, numpoints):
				html.append('''data.setValue(%d, 0, '%s');\n''' % (rangedi, dt))
			
			for rangedi in range(i, numrows, numpoints):
				if rangedi == i:
					html.append('''data.setValue(%d, 1, %d);\n''' % (rangedi, quotaValue + quotaValue))
				else:
					html.append('''data.setValue(%d, 1, 0);\n''' % (rangedi))
				
			k = 2
			for userdir in userdirs:
				for rangedi in range(i, numrows, numpoints):
					if rangedi == i + (numpoints * (k - 1)):
						html.append('''data.setValue(%d, %d, %d);\n''' % (rangedi, k, quotaValue))
					else:
						html.append('''data.setValue(%d, %d, 0);\n''' % (rangedi, k))						
				k += 1
			
			# Add user datapoints
			for j in range(len(sortedUsers)):			
				username = sortedUsers[j]
				Filecount = []
				
				rangedi = i
				homePlusData = 0
				if usagetbl[dt].get(username) and usagetbl[dt][username].get("home") and usagetbl[dt][username].get("data"):
					homePlusData = usagetbl[dt][username].get("home")["numfiles"] + usagetbl[dt][username]["data"]["numfiles"]
				sumFilecountIndex = 0 
				sumFilecount[i][sumFilecountIndex] += homePlusData
				html.append('''data.setValue(%d, %d, %d);\n''' % (rangedi, j + startindex, homePlusData))
				rangedi += numpoints
				for userdir in userdirs:
					sumFilecountIndex += 1
					Filecount = 0
					if usagetbl[dt].get(username):
						Filecount = usagetbl[dt][username][userdir]["numfiles"]
						sumFilecount[i][sumFilecountIndex] += Filecount
					html.append('''data.setValue(%d, %d, %d);\n''' % (rangedi, j + startindex, Filecount))
					rangedi += numpoints
			sumFilecount[i] = [dt] + sumFilecount[i]
			

		# Maintain lists of the user indices to enable us to hide different sets
		# todo: also add the list of colors here to keep them consistent when you switch sets
		startindex = 4
		JScurrentusers = range(0, startindex) 
		JSpastusers = range(0, startindex) 
		JSallusers = range(0, startindex + len(sortedUsers))
		JSnousers = range(0, startindex)
		for j in range(len(sortedUsers)):
			username = sortedUsers[j]
			if userstatus[username] == CurrentMembers or username in limbousers:
				JScurrentusers.append(j + startindex)
			else:
				JSpastusers.append(j + startindex)
					
		maxValue *= 1.05
		sumFilecountHeadings = str(["data + home"] +userdirs)
		currentSumFilecount = str([locale.format("%d", nsfc, grouping=True) for nsfc in sumFilecount[-1][1:]])  
		tuserdir = 'Number of files in storage (current = %(currentSumFilecount)s)' % vars()
		colorlist = [('#333', 4), ('#300', 4), ('#030', 4), ('#003', 4)]
		
		# Colors
		global userColors
		for i in range(len(sortedUsers)):
			colorlist.append((userColors[sortedUsers[i]], 2))
		seriesformat = ["%d:{color: '%s', lineWidth: %d}" % (i, colorlist[i][0], colorlist[i][1]) for i in range(len(colorlist))]
		seriesformat = join(seriesformat,", ")
		seriesformat = "{%s}" % seriesformat 
		
		groupcolors = colorlist[0:4]
		for i in range(len(sortedUsers)):
			u = sortedUsers[i]
			if userstatus[u] == CurrentMembers or u in limbousers:
				groupcolors.append((userColors[u], 2))
		seriesformatcurrent = ["%d:{color: '%s', lineWidth: %d}" % (i, groupcolors[i][0], groupcolors[i][1]) for i in range(len(groupcolors))]
		seriesformatcurrent = "{%s}" % join(seriesformatcurrent,", ") 
		
		groupcolors = colorlist[0:4]
		for i in range(len(sortedUsers)):
			u = sortedUsers[i]
			if not(userstatus[u] == CurrentMembers or u in limbousers):
				groupcolors.append((userColors[u], 2))
		seriesformatpast = ["%d:{color: '%s', lineWidth: %d}" % (i, groupcolors[i][0], groupcolors[i][1]) for i in range(len(groupcolors))]
		seriesformatpast = "{%s}" % join(seriesformatpast,", ") 

		html.append('''
		// Instantiate and draw our chart, passing in some options.
		numfiles_chart = new google.visualization.LineChart(document.getElementById('SpaceUsageChartnumfiles'));
		numfiles_dataview = new google.visualization.DataView(data);
		numfiles_currentusers = %(JScurrentusers)s;
		numfiles_pastusers = %(JSpastusers)s;
		numfiles_allusers = %(JSallusers)s;
		numfiles_nousers = %(JSnousers)s;
		numfiles_numpoints = %(numpoints)s;
		numfiles_filecounts = %(currentSumFilecount)s;
		numfiles_filecountHeadings = %(sumFilecountHeadings)s;
		numfiles_title = "Title";
		numfiles_seriesformatall = %(seriesformat)s;
		numfiles_seriesformatpast = %(seriesformatpast)s;
		numfiles_seriesformatcurrent = %(seriesformatcurrent)s; 
		numfiles_seriesformat = numfiles_seriesformatall; 
		set_numfilesRows(0);
		set_numfilesColumns(true, true);
	}
	function set_numfilesRows(userdirindex)
	{
		numfiles_title = 'Number of files in ' + numfiles_filecountHeadings[userdirindex] + ' (current = ' + numfiles_filecounts[userdirindex] + ')'
		startindex = userdirindex * numfiles_numpoints;
		numfiles_dataview.setRows(startindex, startindex + (numfiles_numpoints - 1));
		draw_numfiles();
	}
	function draw_numfiles()
	{
		settitle = numfiles_title;
		numfiles_chart.draw(numfiles_dataview, {title: settitle, hAxis:{slantedText:true,slantedTextAngle:60}, backgroundColor:{strokeWidth:3}, pointSize:2, vAxis:{title:'%(yAxisTitle)s', minValue:%(minValue)d}, lineWidth: 2, series: numfiles_seriesformat, width: 1200, height: 640});

	}
	function set_numfilesColumns(current, past)
	{
		// choose the columns
		if (current && past)
		{
			numfiles_dataview.setColumns(numfiles_allusers)
			numfiles_seriesformat = numfiles_seriesformatall;
		}
		else if (current)
		{
			numfiles_dataview.setColumns(numfiles_currentusers)
			numfiles_seriesformat = numfiles_seriesformatcurrent;
		}
		else if (past)
		{
			numfiles_dataview.setColumns(numfiles_pastusers)
			numfiles_seriesformat = numfiles_seriesformatpast;
		}
		else
		{
			numfiles_dataview.setColumns(numfiles_nousers)
		}
		draw_numfiles();
	}
	</script>
		''' % vars())
		
		fnname = "drawSpaceUsageNumfilesTotals"
		chartsfns.append(fnname)
		html.append('''
	<script type="text/javascript">
	var numfilestotals_chart;
	function %(fnname)s() {
	// Create our data table.
	var data = new google.visualization.DataTable();
	data.addColumn('string', 'Date');
	data.addColumn('number', 'home + data');''' % vars())
	
		for userdir in userdirs:
			html.append('''data.addColumn('number', '%(userdir)s');''' % vars())
		html.append('''data.addRows(%d);''' % len(sumFilecount))
		
		i = 0
		for daysCount in sumFilecount:
			html.append('''data.setValue(%d, 0, '%s');''' % (i, daysCount[0]))
			for j in range(1, len(daysCount)):
				html.append('''data.setValue(%d, %d, %d);''' % (i, j, daysCount[j]))
			i += 1
		
		totalscolorlist = [('red', 2), ('blue', 2), ('yellow', 2), ('green', 2), ('orange', 2)]
		seriesformattotals = ["%d:{color: '%s', lineWidth: %d}" % (i, totalscolorlist[i][0], totalscolorlist[i][1]) for i in range(len(totalscolorlist))]
		seriesformattotals = join(seriesformattotals,", ")
		seriesformattotals = "series:{%s}" % seriesformattotals 
		html.append('''

		numfilestotals_chart = new google.visualization.LineChart(document.getElementById('SpaceUsageChartNumfilesTotals'));
		numfilestotals_dataview = new google.visualization.DataView(data);
		numfilestotals_chart.draw(numfilestotals_dataview, {title: "Total number of files", hAxis:{slantedText:true,slantedTextAngle:60}, backgroundColor:{strokeWidth:3}, pointSize:2, vAxis:{title:'%(yAxisTitle)s'}, lineWidth: 2, %(seriesformattotals)s, width: 1200, height: 400});

	}
	</script>''' % vars())
		

	for userdir in userdirs:
		sortedUsers = getSortedUsers(usagetbl, latestdate, users, userdir)
		yAxisTitle = "Usage in GB"
		fnname = "drawSpaceUsage%s" % string.capwords(userdir)
		chartsfns.append(fnname)
		totalInGB = []
			
		html.append('''
	<script type="text/javascript">
	var %(userdir)s_chart;
	var %(userdir)s_dataview;
	var %(userdir)s_currentusers;
	var %(userdir)s_pastusers;
	var %(userdir)s_allusers;
	var %(userdir)s_nousers;
		  
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
			html.append(''' data.addColumn('number', 'Used');''') # Add used datapoint

		else:
			html.append(''' data.addColumn('number', 'Quota');''')
			html.append(''' data.addColumn('number', 'Alumni quota');''')
		startindex = 3
		
		# Add user datapoints
		for user in sortedUsers:
			html.append('''data.addColumn('number', '%s');''' % user)	
		
		html.append('''data.addRows(%d);''' % len(dailyquotas))
		
		minValue = 0 # Prefer zero-based graphs
		maxValue = 0
		#if userdir == "archive":
		#	startindex += 1

		for i in range(len(dailyquotas)):
			# Date, Quotas, DriveUsage, OtherData, GroupUsage
			quota = dailyquotas[i]
			Quotas = pickle.loads(quota[1])
			OtherData = None
			if quota[3]:
				OtherData = pickle.loads(quota[3])

			dt = quota[0]
			
			quotaValue = 0
			alumniQuotaValue = 0
			if Quotas.get(userdir):
				if Quotas[userdir].get(CurrentMembers):
					quotaValue = Quotas[userdir][CurrentMembers]
				if Quotas[userdir].get(LabAlumni):
					alumniQuotaValue = Quotas[userdir][LabAlumni]
				elif Quotas[userdir].get(PastRotationStudents):
					alumniQuotaValue = Quotas[userdir][PastRotationStudents]
			if userdir == "archive" and OtherData and OtherData.get("ArchiveHogThresholdInGB"):
				quotaInGB = OtherData["ArchiveHogThresholdInGB"]
			else:
				quotaInGB = quotaValue / 1024
				alumniQuotaInGB = alumniQuotaValue / 1024
			
			# Add quota
			html.append('''data.setValue(%d, 0, '%s');''' % (i, dt))
			html.append('''data.setValue(%d, 1, %d);''' % (i, quotaInGB))
			html.append('''data.setValue(%d, 2, %d);''' % (i, alumniQuotaInGB))
			
			# Add user datapoints
			sumUsageInGB = 0
			
			for j in range(len(sortedUsers)):
				username = sortedUsers[j]
				UsageInGB = 0
				if usagetbl[dt].get(username):
					UsageInGB = float(usagetbl[dt][username][userdir]["SizeInMB"]) / float(1024)
				sumUsageInGB += UsageInGB
				maxValue = max(maxValue, UsageInGB)
				minValue = min(maxValue, UsageInGB)
				html.append('''data.setValue(%d, %d, %0.3f);''' % (i, j + startindex, UsageInGB))
		
			totalInGB.append(sumUsageInGB)
			if userdir == "archive":
				html.append('''data.setValue(%d, 2, %d);''' % (i, sumUsageInGB))
		
		# Maintain lists of the user indices to enable us to hide different sets
		# todo: also add the list of colors here to keep them consistent when you switch sets
		JScurrentusers = range(0, startindex)
		JSpastusers = range(0, startindex) 
		if userdir != "archive":
			# Remove the quota for the other group
			JScurrentusers.remove(2) 
			JSpastusers.remove(1)
		JSallusers = range(0, startindex + len(sortedUsers))
		JSnousers = range(0, startindex)
		for j in range(len(sortedUsers)):
			username = sortedUsers[j]
			if userstatus[username] == CurrentMembers or username in limbousers:
				JScurrentusers.append(j + startindex)
			else:
				JSpastusers.append(j + startindex)
					
		maxValue *= 1.05
		
		if userdir == "archive":
			usages = pickle.loads(quotas[-1][2])
			tuserdir = "/%s usage (current : %s)" % (userdir, usages["zin"]["Use%"])
		else:
			sumUsageInTB = sumUsageInGB / 1024
			tuserdir = '/%(userdir)s usage (current = %(sumUsageInTB).2fTB)' % vars()
			
		if userdir == "archive":
			colorlist = [('black', 4), ('red', 4)]
		else:
			colorlist = [('black', 4), ('#333', 3)]
		
		global userColors
		for i in range(len(sortedUsers)):
			colorlist.append((userColors[sortedUsers[i]], 2))
		
		seriesformat = ["%d:{color: '%s', lineWidth: %d}" % (i, colorlist[i][0], colorlist[i][1]) for i in range(len(colorlist))]
		seriesformat = "series:{%s}" % join(seriesformat,", ") 
		if userdir != "archive":
			groupcolors = [colorlist[0]]
			for i in range(len(sortedUsers)):
				u = sortedUsers[i]
				if userstatus[u] == CurrentMembers or u in limbousers:
					groupcolors.append((userColors[u], 2))
			seriesformatcurrent = ["%d:{color: '%s', lineWidth: %d}" % (i, groupcolors[i][0], groupcolors[i][1]) for i in range(len(groupcolors))]
			seriesformatcurrent = "series:{%s}" % join(seriesformatcurrent,", ") 
			
			groupcolors = [colorlist[1]]
			for i in range(len(sortedUsers)):
				u = sortedUsers[i]
				if not(userstatus[u] == CurrentMembers or u in limbousers):
					groupcolors.append((userColors[u], 2))
			seriesformatpast = ["%d:{color: '%s', lineWidth: %d}" % (i, groupcolors[i][0], groupcolors[i][1]) for i in range(len(groupcolors))]
			seriesformatpast = "series:{%s}" % join(seriesformatpast,", ") 
			
		else:
			seriesformatcurrent = seriesformat
			seriesformatpast = seriesformat
			
		
		html.append('''
		  // Instantiate and draw our chart, passing in some options.
		  %(userdir)s_chart = new google.visualization.LineChart(document.getElementById('SpaceUsageChart%(userdir)s'));
		  %(userdir)s_dataview = new google.visualization.DataView(data); 
		  %(userdir)s_currentusers = %(JScurrentusers)s;
		  %(userdir)s_pastusers = %(JSpastusers)s;
		  %(userdir)s_allusers = %(JSallusers)s;
		  %(userdir)s_nousers = %(JSnousers)s;
		  
		  draw_%(userdir)s(true, true);
		}
		function draw_%(userdir)s(current, past)
		  {
			  if (current && past)
			  {
				  %(userdir)s_dataview.setColumns(%(userdir)s_allusers)
				  %(userdir)s_chart.draw(%(userdir)s_dataview, {hAxis:{slantedText:true,slantedTextAngle:60}, backgroundColor:{strokeWidth:3}, pointSize:2, vAxis:{title:'%(yAxisTitle)s', minValue:%(minValue)d}, lineWidth: 2, %(seriesformat)s, width: 1200, height: 640, title: '%(tuserdir)s'});
			  }
			  else if (current)
			  {
				  %(userdir)s_dataview.setColumns(%(userdir)s_currentusers)
				  %(userdir)s_chart.draw(%(userdir)s_dataview, {hAxis:{slantedText:true,slantedTextAngle:60}, backgroundColor:{strokeWidth:3}, pointSize:2, vAxis:{title:'%(yAxisTitle)s', minValue:%(minValue)d}, lineWidth: 2, %(seriesformatcurrent)s, width: 1200, height: 640, title: '%(tuserdir)s'});
			  }
			  else if (past)
			  {
				  %(userdir)s_dataview.setColumns(%(userdir)s_pastusers)
				  %(userdir)s_chart.draw(%(userdir)s_dataview, {hAxis:{slantedText:true,slantedTextAngle:60}, backgroundColor:{strokeWidth:3}, pointSize:2, vAxis:{title:'%(yAxisTitle)s', minValue:%(minValue)d}, lineWidth: 2, %(seriesformatpast)s, width: 1200, height: 640, title: '%(tuserdir)s'});
			  }
			  else
			  {
				  %(userdir)s_dataview.setColumns(%(userdir)s_nousers)
			  }
		  }

		</script>
		''' % vars())
		

		if userdir != 'archive':
			fnname = "drawSpaceUsageTotals%s" % string.capwords(userdir)
			chartsfns.append(fnname)
			numpoints=len(dailyquotas)
			html.append('''
<script type="text/javascript">
function %(fnname)s() {
// Create our data table.
var totalsdata = new google.visualization.DataTable();
totalsdata.addColumn('string', 'Date');
totalsdata.addColumn('number', 'Total');
totalsdata.addColumn('number', 'Max asssuming quota reached by all');
totalsdata.addRows(%(numpoints)d);
''' % vars())
		
			for i in range(len(dailyquotas)):
				html.append('''totalsdata.setValue(%d, 0, '%s');\n''' % (i, dt))
				html.append('''totalsdata.setValue(%d, 1, %d);\n''' % (i, totalInGB[i]))
				html.append('''totalsdata.setValue(%d, 2, %d);\n''' % (i, quotaInGB * len(users)))
			
			html.append('''
// Instantiate and draw our chart, passing in some options.
%(userdir)s_totalschart = new google.visualization.LineChart(document.getElementById('SpaceUsageChartTotals%(userdir)s'));
%(userdir)s_totalschart.draw(totalsdata, {backgroundColor:{strokeWidth:3}, pointSize:2, vAxis:{title:'%(yAxisTitle)s'}, lineWidth: 2, series:{0:{color: 'black', lineWidth: 4}, 1:{color: 'blue', lineWidth: 2}}, width: 1200, height: 200, title: '/%(userdir)s total usage'});
}
</script>''' % vars())
		
	html.append('''<span style="text-align:center; font-size:15pt"><A NAME="%(title)s"></A>%(title)s</span><br><br>''' % vars())

	#html.append("<table>")
	subtitles = []
	for userdir in userdirs:
		subtitle = "/%s usage" % userdir
		subtitles.append(subtitle)
		html.append('''<A NAME="%(subtitle)s"></A><div id="SpaceUsageChart%(userdir)s"></div>
		<div align="center">
		<form action="">
<input type="radio" name="%(userdir)s_radio" value="0" onclick="draw_%(userdir)s(true, true);" CHECKED /> All
<input type="radio" name="%(userdir)s_radio" value="1" onclick="draw_%(userdir)s(true, false);"/> Current members
<input type="radio" name="%(userdir)s_radio" value="2" onclick="draw_%(userdir)s(false, true);"/> Past members
</form></div>
		<br><br>''' % vars())
		subtitle = "/%s usage totals" % userdir
		subtitles.append(subtitle)
		html.append('''<A NAME="%(subtitle)s"></A><div id="SpaceUsageChartTotals%(userdir)s"></div><br><br>''' % vars())

	for userdir in ["numfiles"]:
		subtitle = "Number of files"
		subtitles.append(subtitle)
		html.append('''
		<A NAME="%(subtitle)s"></A><div id="SpaceUsageChartnumfiles"></div>
		<div align="center">
		<form action="">
			<input type="radio" name="numfiles_columnSelector" value="0" onclick="set_numfilesColumns(true, true);" CHECKED /> All
			<input type="radio" name="numfiles_columnSelector" value="1" onclick="set_numfilesColumns(true, false);"/> Current members
			<input type="radio" name="numfiles_columnSelector" value="2" onclick="set_numfilesColumns(false, true);"/> Past members
		</form>
		</div>
		<div align="center">
		<form action="">
			<input type="radio" name="numfiles_rowSelector" value="0" onclick="set_numfilesRows(this.value);" CHECKED /> data + home
			<input type="radio" name="numfiles_rowSelector" value="1" onclick="set_numfilesRows(this.value);"/> home
			<input type="radio" name="numfiles_rowSelector" value="2" onclick="set_numfilesRows(this.value);"/> data
			<input type="radio" name="numfiles_rowSelector" value="3" onclick="set_numfilesRows(this.value);"/> archive
		</form>
		</div>''' % vars())
		
		subtitle = "Number of files (totals)" 
		subtitles.append(subtitle)
		html.append('''<A NAME="%(subtitle)s"></A><div id="SpaceUsageChartNumfilesTotals"></div><br><br>''' % vars())
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
	# get ip addr hostname
	import os
	IP = os.environ['REMOTE_ADDR']
	hostname = IP
	try:
		hostname = socket.gethostbyaddr(IP)[0]
	except:
		pass

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
		if not hostname in DEVELOPMENT_HOSTS:
			html.append('''<button disabled="disabled">restart</button>''')
			html.append('''<button disabled="disabled">kill</button>''')
			html.append('''<button disabled="disabled">%s</button>''' % expiredcmd)
			html.append('''<button disabled="disabled">clear</button>''')
		else:
			if status == 2 or status == 4:
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
		
	
	# Set generate to False to hide pages for quicker testing
	subpages = [
		{"name" : "diskstats",	"desc" : "Disk stats",			"fn" : generateDiskStatsSubpage,	"generate" :True,	"params" : [quotas, usage, users]},
		{"name" : "jobadmin",	"desc" : "Job administration",	"fn" : generateJobAdminSubpage,		"generate" :True,	"params" : []},
		{"name" : "webusers",	"desc" : "Website users",		"fn" : generateWebUsersSubpage,		"generate" :True,	"params" : []},
		{"name" : "labusers",	"desc" : "Lab users",			"fn" : generateLabUsersSubpage,		"generate" :True,	"params" : []},
		]
# Create menu
	html = []
	html.append("<td align=center>")
	html.append('''<FORM name="adminform" method="post">''')
	
	for subpage in subpages:
		if subpage["generate"]:
			html.append('''<input type="button" value="%(desc)s" onClick="showPage('%(name)s');">''' % subpage)
	
	html.append('''<input type="button" value="Refresh" onClick="document.adminform.query.value='admin'; document.adminform.submit();">''')
	html.append('''<input type="hidden" NAME="AdminPage" VALUE="%s">''' % adminpage)
	html.append('''<input type="hidden" NAME="query" VALUE="">''')
	html.append('''</FORM>''')
	html.append("</td></tr><tr>")
	
	html.append("<td align=left>")
	
	# Disk stats
	for subpage in subpages:
		html.append('<div style="display:none" id="%s">' % subpage["name"])
		if subpage["generate"]:
			html.extend(subpage["fn"](*subpage["params"]))
		html.append("</div>")
		
	html.append("</td>")
	html.append('''<script src="/backrub/frontend/admin.js" type="text/javascript"></script>''')

	return html