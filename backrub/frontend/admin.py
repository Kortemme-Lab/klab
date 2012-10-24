#!/usr/bin/python2.4
# -*- coding: iso-8859-15 -*-

########################################
# Code for the admin page
########################################

import os, re
import datetime
from datetime import date
from string import join
import pickle
import string
from sys import maxint
import rosettadb
import calendar
import socket
from rosettahelper import DEVELOPMENT_HOSTS, DEVELOPER_USERNAMES, saturateHexColor
import locale
locale.setlocale(locale.LC_ALL, 'en_US')
import retrospect
from RosettaProtocols import WebserverProtocols
#from cStringIO import StringIO
	
userColors = {}
showHistoryForDays = 31

settings = None
protocols = None
script_filename = None

CurrentMembers = "Current Members"
LabAlumni = "Lab Alumni"
PastRotationStudents = "Past Rotation Students"

#todo: Change the database records to use the enum in Users as below in UCurrentMembers 
UCurrentMembers = "current"

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
            google.load('visualization', '1', {'packages':['corechart', 'gauge', 'geochart']});
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

def webstatsSuccessFailure(stats):
	# Return values
	title = "Success/Failure rate"
	html = []
	fnname = "drawStatsSuccessFailure"
	chartsfns = [fnname]
		
	mkeys = sorted(stats.keys())[:]
	c = len(mkeys)
	html.append('''
	<script type="text/javascript">
	function %(fnname)s() {''' % vars())
	
	if c:
		html.append('''
		// Create our data table.
		var data = new google.visualization.DataTable();
		data.addColumn('string', 'Month');
		data.addColumn('number', 'Failure');
		data.addColumn('number', 'Success');
		data.addRows([''' % vars())
		
		for k in mkeys:
			v = stats[k]
			key = map(int, k.split("-"))
			dt = ("%s %d" % (calendar.month_abbr[key[1]], key[0]))
			html.append('''["%s", %d, %d],''' % (dt, v.get("failed", 0), v.get("successful", 0))) 
		html.append(''']);
		
		// Instantiate and draw our chart, passing in some options.
		var chart = new google.visualization.ColumnChart(document.getElementById('webstatsSuccessFailureChart'));
		seriesstyle = {0:{color: 'red'}, 1:{color: 'green'}}
		chart.draw(data, {width: 800, height: 360, isStacked:true, series:seriesstyle, hAxis:{slantedText:true,slantedTextAngle:60}});
		''')
	html.append('''
	}
	</script>
	''')
	html.append('''<span style="text-align:center; font-size:15pt"><A NAME="%(title)s"></A>%(title)s</span>''' % vars())
	html.append('''<div id="webstatsSuccessFailureChart"></div>''')
	
	return title, html, chartsfns

def webstatsJobsByProtocol(stats):
	# Return values
	title = "Jobs by protocol"
	html = []
	fnname = "drawStatsJobsByProtocol"
	chartsfns = [fnname]
	protocols = ["Point/multiple mutation", "Backrub Ensemble", "Backrub Ensemble Design", "Sequence Tolerance (Elisabeth)", "Sequence Tolerance (Colin)"]
	
	protocolGroups = WebserverProtocols().getProtocols()[0]
	seriesColors = [
		saturateHexColor(protocolGroups[0].color, 2),
		saturateHexColor(protocolGroups[1].color, 1.5),
		saturateHexColor(protocolGroups[1].color, 3.5),
		saturateHexColor(protocolGroups[2].color, 2),
		saturateHexColor(protocolGroups[2].color, 3.5)
	]
	mkeys = sorted(stats.keys())[:]
	c = len(mkeys)
	html.append('''
	<script type="text/javascript">
	function %(fnname)s() {''' % vars())
	
	if c:
		html.append('''
		// Create our data table.
		var data = new google.visualization.DataTable();
		data.addColumn('string', 'Month');''')
		
		for p in protocols:
			html.append('''		data.addColumn('number', '%s');\n''' % p)
		
		html.append('''		data.addRows([''')
		
		for k in mkeys:
			v = stats[k]
			key = map(int, k.split("-"))
			dt = ("%s %d" % (calendar.month_abbr[key[1]], key[0]))
			html.append('''["%s", ''' % dt)
			for p in protocols:
				html.append('''%d,''' % v.get(p, 0))
			html.append('''],''')
		html.append(''']);
		
		// Instantiate and draw our chart, passing in some options.
		var chart = new google.visualization.ColumnChart(document.getElementById('webstatsJobsByProtocolChart'));
		seriesstyle = {''')
		
		for i in range(len(seriesColors)):
			html.append('''%d:{color: '%s'}, ''' % (i, seriesColors[i]))
		html.append('''}
		chart.draw(data, {width: 800, height: 360, isStacked:true, series:seriesstyle, hAxis:{slantedText:true,slantedTextAngle:60}});''')
	html.append('''
	}
	</script>
	''')
	html.append('''<span style="text-align:center; font-size:15pt"><A NAME="%(title)s"></A>%(title)s</span>''' % vars())
	html.append('''<div id="webstatsJobsByProtocolChart"></div>''')
	
	return title, html, chartsfns

def webstatsJobsByProtocolCumulative(stats):
	# Return values
	title = "Jobs by protocol (cumulative)"
	html = []
	fnname = "drawStatsJobsByProtocolCumulative"
	chartsfns = [fnname]
	protocols = ["Point/multiple mutation", "Backrub Ensemble", "Backrub Ensemble Design", "Sequence Tolerance (Elisabeth)", "Sequence Tolerance (Colin)"]
	protocolGroups = WebserverProtocols().getProtocols()[0]
	seriesColors = [
		saturateHexColor(protocolGroups[0].color, 2),
		saturateHexColor(protocolGroups[1].color, 1.5),
		saturateHexColor(protocolGroups[1].color, 3.5),
		saturateHexColor(protocolGroups[2].color, 2),
		saturateHexColor(protocolGroups[2].color, 3.5)
	]
	# mkeys are the months of the years
	mkeys = sorted(stats.keys())[:]
	c = len(mkeys)
	html.append('''
	<script type="text/javascript">
	function %(fnname)s() {''' % vars())
	
	if c:
		html.append('''
		// Create our data table.
		var data = new google.visualization.DataTable();
		data.addColumn('string', 'Month');''')
		
		for p in protocols:
			html.append('''		data.addColumn('number', '%s');\n''' % p)
		
		html.append('''		data.addRows([''')
		
		cumulative = {}
		for p in protocols:
			cumulative[p] = 0
			
		for k in mkeys:
			v = stats[k]
			key = map(int, k.split("-"))
			dt = ("%s %d" % (calendar.month_name[key[1]], key[0]))
			html.append('''["%s", ''' % dt)
			for p in protocols:
				cumulative[p] += v.get(p, 0)
				html.append('''%d,''' % cumulative[p])
			html.append('''],''')
		html.append(''']);
		
		// Instantiate and draw our chart, passing in some options.
		var chart = new google.visualization.ColumnChart(document.getElementById('webstatsJobsByProtocolCumulativeChart'));
		seriesstyle = {''')
		
		for i in range(len(seriesColors)):
			html.append('''%d:{color: '%s'}, ''' % (i, seriesColors[i]))
		html.append('''}
		chart.draw(data, {width: 1200, height: 600, isStacked:true, series:seriesstyle});''')
	html.append('''
	}
	</script>
	''')
	html.append('''<span style="text-align:center; font-size:15pt"><A NAME="%(title)s"></A>%(title)s</span>''' % vars())
	html.append('''<div id="webstatsJobsByProtocolCumulativeChart"></div>''')
	
	return title, html, chartsfns

def websiteUserGeoChart(userGeoFreqCount):
	# Return values
	title = "Users by country"
	html = []
	fnname = "drawStatsUserGeoChart"
	chartsfns = [fnname]
	
	#userGeoFreqCount
	html.append('''
	<script type='text/javascript'>
	var userGeoChart;
	var userGeoData;
	function %(fnname)s() {''' % vars())
	if userGeoFreqCount:
		html.append('''
		userGeoData = new google.visualization.DataTable();
		userGeoData.addRows(%d);
		userGeoData.addColumn('string', 'Country');
		userGeoData.addColumn('number', 'Popularity');\n''' % len(userGeoFreqCount))
	
		c = 0
		for k, v in sorted(userGeoFreqCount.iteritems()):
			html.append('''		userGeoData.setValue(%d, 0, '%s');\n''' % (c, k))
			html.append('''		userGeoData.setValue(%d, 1, %s);\n''' % (c, v))
			c += 1

		width = 800
		height = width / 1.6
		html.append('''
		userGeoChart = new google.visualization.GeoChart(document.getElementById('webstatsUserGeoChart'));
		userGeoChart.draw(userGeoData, {width: %d, height: %d, colors:['yellow', 'orange', 'red']});''' % (width, height))
	html.append('''
	}
	</script>
	''')
	
	html.append('''<span style="text-align:center; font-size:15pt"><A NAME="%(title)s"></A>%(title)s</span>''' % vars())
	html.append('''<div id="webstatsUserGeoChart"></div>''')
	
	return title, html, chartsfns

def addDriveUsageChart(DriveUsage):
    # Return values
    title = "Drive usage"
    html = []
    chartsfns = []
 
    drives = ["ganon", "link", "zelda", "hyrule", "Webserver", "Test webserver"] # "zin
    #colors = {CurrentMembers : "#ADA", LabAlumni : "#AAD", PastRotationStudents : "#D8A9DE", Unaccounted : "#EFEFEF"}
    for drive in drives:
        nospdrive = drive.replace(" ", "")
        if DriveUsage.get(drive):
            data = DriveUsage[drive]
            fnname = "drawDriveUsage%s" % string.capwords(drive.replace(" ",""))
            chartsfns.append(fnname)
            usepercentage = int(data["Use%"][0:-1])
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
        ['%s', %d],''' % (drive, usepercentage))
            html.append('''
              ]);
        
              // Instantiate and draw our chart, passing in some options.
              var chart = new google.visualization.Gauge(document.getElementById('DriveUsageChart%(nospdrive)s'));
               
              options = {width: 300, height: 180, greenColor: '#ff0', greenFrom: 70, greenTo: 80, yellowFrom: 80, yellowTo: 90, redFrom: 90, redTo: 100,}
              chart.draw(data, options);
              
              setInterval(function() {
				data.setValue(0, 1, Math.round(%(usepercentage)s + 3 * (0.5 - Math.random())));
				chart.draw(data, options);
			  }, 300);
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
        if counter >= 4:
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
			if userstatus[username] == UCurrentMembers or username in limbousers:
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
			if userstatus[u] == UCurrentMembers or u in limbousers:
				groupcolors.append((userColors[u], 2))
		seriesformatcurrent = ["%d:{color: '%s', lineWidth: %d}" % (i, groupcolors[i][0], groupcolors[i][1]) for i in range(len(groupcolors))]
		seriesformatcurrent = "{%s}" % join(seriesformatcurrent,", ") 
		
		groupcolors = colorlist[0:4]
		for i in range(len(sortedUsers)):
			u = sortedUsers[i]
			if not(userstatus[u] == UCurrentMembers or u in limbousers):
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
			if userstatus[username] == UCurrentMembers or username in limbousers:
				JScurrentusers.append(j + startindex)
			else:
				JSpastusers.append(j + startindex)
					
		maxValue *= 1.05
		
		if userdir == "archive":
			usages = pickle.loads(quotas[-1][2])
			tuserdir = "/%s usage (current : %s)" % (userdir, usages["ganon"]["Use%"])
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
				if userstatus[u] == UCurrentMembers or u in limbousers:
					groupcolors.append((userColors[u], 2))
			seriesformatcurrent = ["%d:{color: '%s', lineWidth: %d}" % (i, groupcolors[i][0], groupcolors[i][1]) for i in range(len(groupcolors))]
			seriesformatcurrent = "series:{%s}" % join(seriesformatcurrent,", ") 
			
			groupcolors = [colorlist[1]]
			for i in range(len(sortedUsers)):
				u = sortedUsers[i]
				if not(userstatus[u] == UCurrentMembers or u in limbousers):
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
    
    html.extend(charthtml)
    return html, chartfns

def getKlabDBConnection():
	return rosettadb.RosettaDB(settings, host = "kortemmelab.ucsf.edu")

def getKortemmelabUsersConnection():
	return rosettadb.RosettaDB(settings, host = "kortemmelab.ucsf.edu", db = "KortemmeLab")

def getAlbanaConnection():
	return rosettadb.RosettaDB(settings)

def getWebsiteUsers():
	# Get all jobs on the live webserver which were submitted from this server and which have not expired
	connection = getKlabDBConnection()
	sql = '''SELECT ID, UserName, Concat(FirstName, ' ', LastName) AS Name, Email, Institution, Address1, Address2, City, State, Zip, Country, Phone, Date, LastLoginDate, Priority, Jobs, EmailList FROM Users ORDER BY UserName''' 
	result = connection.execQuery(sql, cursorClass = rosettadb.DictCursor)
	return result

def getInventory():
	# Get all jobs on the live webserver which were submitted from this server and which have not expired
	connection = getKortemmelabUsersConnection()
	sql = '''SELECT PCInventory.*, Users.FirstName, IPAddresses.IPv4Address FROM PCInventory LEFT JOIN Users ON PrimaryUser=Username LEFT JOIN IPAddresses ON PCInventory.Hostname=IPAddresses.Hostname  ORDER BY IPAddresses.IPv4Address, Hostname''' 
	result = list(connection.execQuery(sql, cursorClass = rosettadb.DictCursor))
	return result

def getIPAddresses():
	# Get all jobs on the live webserver which were submitted from this server and which have not expired
	connection = getKortemmelabUsersConnection()
	sql = '''SELECT * FROM IPAddresses''' 
	result = list(connection.execQuery(sql, cursorClass = rosettadb.DictCursor))
	hostToIP = {}
	unassignedAddresses = []
	for address in result:
		hostname = address["Hostname"]
		if hostname:
			hostToIP[hostname] = hostToIP.get(hostname, [])
			hostToIP[hostname].append(address["IPv4Address"])
	return hostToIP

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

def generateITInventory():
	html = []
	inventory = getInventory()
	hostToIP = getIPAddresses()
	fieldnames = ["Hostname", "Label", "Location", "InUse", "PrimaryUser", "Model", "OS", "CPU",
			"CPUSpeedGHz", "NumCoresThreads", "RamInGB", "RAMType", "HDSizes"]
	
	rowcols = {
		"Computational lab"			: ("#5566cc", "#FFFFFF"),
		"Experimental lab"			: ("#cc4444", "#000000"),
		"Tanja's office"			: ("#5566cc", "#FFFFFF"),
		"Server room 101"			: ("#ffcc33", "#000000"),
		"Dogpatch Network Centre"	: ("#66ff66", "#000000"),
		"None"						: ("#cc9999", "#000000"),
	}
	
	IPRanges = {
		"Computational lab"			: "169.230.84.",
		"Experimental lab"			: "169.230.86.",
		"Server room 101"			: "169.230.81.",
		"Dogpatch Network Centre"	: "64.54.136.",
	}
	# Get all IP addresses  which either have no corresponding PC Inventory entry or which have one but the PC is unused 
	machineNames = set([machine["Hostname"] for machine in inventory])
	unusedMachineNames = set([machine["Hostname"] for machine in inventory if not(machine["InUse"])])
	unusedHostnames = list(set(hostToIP.keys()).difference(machineNames).union(set(hostToIP.keys()).intersection(unusedMachineNames)))
	unusedIPAddresses = []
	for h in unusedHostnames:
		if len(hostToIP[h]) > 1:
			print("Unhandled case in PC Inventory : %s, %s" % (h, hostToIP[h]))
			continue
		else:
			IPaddress = hostToIP[h][0]
		location = None
		for loc, r in IPRanges.iteritems():
			if IPaddress.startswith(r):
				location = loc
		unusedIPAddresses.append((IPaddress, h, location or "Unhanded location"))
	
	html.append("""<center><div><i>All machines must have unique labels.</i></div></center>""")
		
	if unusedIPAddresses:
		html.append("""<H1 align=left > Unused IP addresses </H1><br>
			<div>""")
		html.append("""<table border=1 cellpadding=2 cellspacing=0>
			<tr style="font-weight:normal;font-size:10pt"><th>IP address</th><th>DNS name</th><th>Location</th></tr>""")
		for machine in unusedIPAddresses:
			html.append("		<tr><td>%s</td><td>%s</td><td>%s</td></tr>" % machine)
		html.append("</table><br><br></div>")
	else:
		html.append("""<H1 align=left > All IP addresses are used </H1><br>""")
		
	html.append("""<H1 align=left > IT inventory </H1><br>
		<div>""")
	
	columns = [
		("IP", [80], [""]),
		("Hostname", [80], [""]),
		("Location", [160], [""]),
		("In use", [50], [""]),
		("Primary user", [100], [""]),
		("Model", [150], [""]),
		("OS", [200], [""]),
		("CPU type, speed, #cores / threads", [190, 70, 40], ["Chip", "Speed", "Cores/threads"]),
		("RAM", [40, 40, 70, 40, 40], ["Total", "Sticks", "Speed", "Type", "Slots"]),
		("HDs", [150], [""])
	]
	
	count = 0
	for c in columns:
		count += sum(c[1])
	html.append("""		<table class="sortable" border=1 cellpadding=4 cellspacing=0  width="%dpx">""" % (count + 100))
			
	html.append('''
		<tr bgcolor="#828282" style="text-align:center;color:white;">''')
	for c in columns:
		html.append('''			<th style="font-weight:normal;font-size:10pt" colspan=%d> %s </th>''' % (len(c[1]), c[0]))
	html.append('''		</tr>''')

	html.append('''<tr bgcolor="#828282">''')
	for c in columns:
		assert(len(c[1]) == len(c[2]))
		for i in range(len(c[1])):
			w = c[1][i]
			hdr = c[2][i]
			html.append('''<td width="%dpx">%s</td>''' % (w, hdr))
	html.append('''</tr>''')
		
	alreadyPrinted = {}
	
	machinestrings = []
	for machine in inventory:
		machinestring = []
		if alreadyPrinted.get(machine["Hostname"]):
			continue
		alreadyPrinted[machine["Hostname"]] = True
		
		colors = rowcols.get(machine["Location"], rowcols["None"])
		
		if not machine["InUse"]:
			IPAddress = "None"
			colors = rowcols["None"]
		elif hostToIP.get(machine["Hostname"]):
			IPAddress = join(hostToIP.get(machine["Hostname"]), ", ")
		else:
			if IPRanges.get(machine["Location"]):
				IPAddress = IPRanges[machine["Location"]] + "*"
			else:
				IPAddress = "Dynamic"
		
		machinestring.append("<tr style='background-color:%s;color:%s'>" % colors)
		if machine["InUse"] == 1:
			machine["InUse"] = "Yes"
		else:
			machine["InUse"] = "No"
		machinestring.append("<td>%s</td>" % IPAddress)
		machinestring.append("<td>%(Hostname)s</td>" % machine)
		machinestring.append("<td>%(Location)s</td>" % machine)
		machinestring.append("<td>%(InUse)s</td>" % machine)
		machinestring.append("<td>%s</td>" % (machine["FirstName"] or machine["PrimaryUse"]))
		
		if machine.get("Model"):
			machinestring.append("<td>%s</td>" % machine.get("Model", ""))
		else:
			machinestring.append("<td></td>")
		
		if machine.get("OS"):
			machinestring.append("<td>%s</td>" % machine.get("OS", ""))
		else:
			machinestring.append("<td></td>")
		
		if machine.get("CPU"):
			machinestring.append("<td>%s</td>" % machine.get("CPU", ""))
		else:
			machinestring.append("<td></td>")
		
		if machine.get("CPUSpeedGHz"):
			machinestring.append("<td>%s GHz</td>" % machine.get("CPUSpeedGHz"))
		else:
			machinestring.append("<td></td>")
		
		if machine.get("NumCores"):
			if machine.get("NumThreads"):
				machinestring.append("<td>%(NumCores)d/%(NumThreads)d</td>" % machine)
			else:
				machinestring.append("<td>%s</td>" % machine.get("NumCores"))
		else:
			machinestring.append("<td></td>")
		
		if machine.get("RAMInGB"):
			machinestring.append("<td>%d GB</td>" % machine.get("RAMInGB"))
		else:
			machinestring.append("<td></td>")
		if machine.get("RAMSticks"):
			machinestring.append("<td>%s</td>" % machine.get("RAMSticks"))
		else:
			machinestring.append("<td></td>")
		if machine.get("RAMSpeedInMHz"):
			machinestring.append("<td>%s MHz</td>" % machine.get("RAMSpeedInMHz"))
		else:
			machinestring.append("<td></td>")
		if machine.get("RAMType"):
			machinestring.append("<td>%s</td>" % machine.get("RAMType"))
		else:
			machinestring.append("<td></td>")
		if machine.get("RAMNumberOfSlots"):
			machinestring.append("<td>%s slots</td>" % machine.get("RAMNumberOfSlots"))
		else:
			machinestring.append("<td></td>")
		
		if machine.get("HDSizes"):
			machinestring.append("<td>%s</td>" % machine.get("HDSizes", ""))
		else:
			machinestring.append("<td></td>")
		
		machinestring.append("</tr>")
		machinestrings.append((IPAddress, machinestring))
	
	for ms in sorted(machinestrings):
		html.extend(ms[1])
	
	html.append('</table> </div>')
	return html, []

def generateWebUsersSubpage():
	html = []
	userlist = getWebsiteUsers()
	html.append("""<H1 align=left > Kortemme Lab users </H1> <br>
		<div >
		<table border=1 cellpadding=2 cellspacing=0 width=1200 >
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
	return html, []

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
	return html, []

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
	IP = os.environ['REMOTE_ADDR']
	hostname = IP
	try:
		hostname = socket.gethostbyaddr(IP)[0]
	except Exception, e:
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
	return html, []

# Add this style (for word-wrap inside the pre tag) to your CSS page
#pre.Retrospect {
#	white-space: pre-wrap;
#	white-space: -moz-pre-wrap !important;
#	white-space: -pre-wrap;
#	white-space: -o-pre-wrap;
#	word-wrap: break-word;
#}
def generateRetrospectLogPage():
	'''This function returns a HTML containing a table of the most recent runs of the expected scripts,
		printed logs for all records read from the log file, and an index to traverse the records by date. 
		The return value is a list of HTML strings.
		todo: remove second return before posting.
	'''
	
	html = []
	logfile = "/retrospect/operations_log.utx"
		
	# Read the default amount (retrospect.DEFAULT_LOG_SIZE) from the log file
	retrospectLog = retrospect.LogReader(logfile, retrospect.expectedScripts)
	log = retrospectLog.getLog()
	
	# Create a date-descending list of dates from the extracted log entries
	# This is used to generate an hyperlinked index for quick navigation
	logdates = {}
	for dt in log.keys():
		logdates["%s-%s-%s" % (dt.year, dt.month, dt.day)] = True
	logdates = reversed(sorted(logdates.keys()))
	
	# Retrospect header
	html.append('<div style="color:white;background-color:#00b5f9;text-align:center"><hr><hr><h1>Retrospect</h1><hr><hr></div>')	
	
	# The summary table
	html.append("<div>")
	html.append("	<table style='margin-left: auto;margin-right: auto;'>")
	html.append("		<tr><td>")
	html.append("			<div style='text-align:center'><b>Summary since %s</b></div>" % retrospectLog.getEarliestEntry())
	html.extend(retrospectLog.generateSummaryHTMLTable(1.5))	# Allow 1.5 days before considering a job to have stopped. Edit this value to suit
	html.append("			</td>")
	html.append("			<td width='200px'></td>")
	html.append("<td style='vertical-align:top;' ><div style='text-align:center'><b>Dates shown</b></div>") #
	# The 'dates shown' index
	html.append("<table style='text-align:center;border:1px solid black;margin-left: auto;margin-right: auto;'>")
	tablestyle = ['background-color:#d0ffd0;', 'background-color:white;']
	count = 0
	for dt in logdates:
		html.append('<tr><td style="%s"><a href="#%s">%s</a><br></td></tr>' % (tablestyle[count % 2], dt, dt))
		count += 1
	html.append("</table></td></tr></table></div><br><br>")
	
	# Add the records from the log, delimited by date
	oldKey = None
	for dt, record in reversed(sorted(log.iteritems())):
		newKey = "%s-%s-%s" % (dt.year, dt.month, dt.day)
		if newKey != oldKey:
			# Add an anchor for the last record of the day to be linked by the 'dates shown' index table 
			html.append('<A NAME="%s"></A><div style="color:white;background-color:#00b5f9;text-align:center"><hr><hr><h1>%s</h1><hr><hr></div>' % (newKey, newKey))
			oldKey = newKey
		
		# Create an anchor for the record so it can be linked to from the summary table
		anchorID = retrospectLog.createAnchorID(record["script"], dt)
		html.append("<!--RECORD-->")
		html.append('<A NAME="%s"></A>' % anchorID)
		
		# Record header
		html.append('<div style="text-align:center;"><b>%s: %s</b></div>'% (record["script"], dt))
		
		# Determine the color for the record 'block' 
		color = ""
		if record["status"] & retrospect.RETROSPECT_FAIL == retrospect.RETROSPECT_FAIL:
			color = "background-color:#ffbbbb" # Pink
		elif record["status"] & retrospect.RETROSPECT_WARNING == retrospect.RETROSPECT_WARNING:
			color = "background-color:#f5b767" # Orange
		elif record["status"] & retrospect.RETROSPECT_EVENT:
			color = "background-color:#bbbbff" # Lavender
		
		# Add the actual record. Lines are formatted depending on their types:
		#   Bold green for headers, italics for subheaders ('events'), orange for warnings,
		#	bold red for errors, blue for possible errors that are not yet recognised by the log reader. 
		# Note that the <pre> block has the class Retrospect. The CSS snippet above should be added
		# to the CSS section/file of your webpage or else word wrapping may not function.
		
		while True:
			if record["lines"] and not(record["lines"][-1][1].strip()):
				record["lines"] = record["lines"][:-1]
				continue
			break
		
		html.append('<pre style="width:900px;%s" class="Retrospect">' % color)
		for line in record["lines"]:
			if line[0] == retrospect.RETROSPECT_HEADER:
				html.append('<b><font color="green">%s</font></b>\n' % line[1].strip())
			elif line[0] == retrospect.RETROSPECT_SUBHEADER:
				html.append('<i>%s</i>' % line[1])
			elif line[0] == retrospect.RETROSPECT_WARNING:
				html.append('<font color="#E56717">%s</font>' % line[1])
			elif line[0] == retrospect.RETROSPECT_FAIL:
				html.append('<b><font color="red">%s</font></b>' % line[1])
			elif line[0] == retrospect.RETROSPECT_UNHANDLED_ERROR:
				html.append('<b><font color="blue">%s</font></b>' % line[1])
			else:
				html.append(line[1])
		html.append('</pre>\n')
		
	return html, []

def generateWebserverStatsSubpage():
	html = []
	errors = []
	
	db = getKlabDBConnection()
	stats = {}
	# 2011 stats starting in June
	for m in range(6,13):
		k = "2011-%.2d" % m
		stats[k] = {}
	# Later stats
	tdy = date.today()
	for y in range(2012, tdy.year + 1):
		if y == tdy.year:
			for m in range(1,tdy.month + 1):
				k = "%d-%.2d" % (y, m)
				stats[k] = {}
		else:
			for m in range(1,13):
				k = "%d-%.2d" % (y, m)
				stats[k] = {}
	
	excludestr = "BackrubServer = 'kortemmelab' AND UserID <> 84 AND UserID <> 106 AND UserID <> 120"
	results = db.execQuery("SELECT MONTH(Date), YEAR(Date), COUNT(id) FROM backrub WHERE %s AND STATUS=0 or STATUS=1 or STATUS=2 GROUP BY YEAR(Date), MONTH(Date)" % excludestr)
	for r in results:
		k = "%d-%.2d" % (r[1], r[0])
		if stats.get(k) != None:
			stats[k]["successful"] = r[2]
	
	results = db.execQuery("SELECT MONTH(Date), YEAR(Date), COUNT(id) FROM backrub WHERE %s AND STATUS=4 GROUP BY YEAR(Date), MONTH(Date)" % excludestr)
	for r in results:
		k = "%d-%.2d" % (r[1], r[0])
		if stats.get(k) != None:
			stats[k]["failed"] = r[2]
	
	results = db.execQuery("SELECT MONTH(Date), YEAR(Date), COUNT(id) FROM backrub WHERE %s AND Task='multiple_mutation' OR Task='point_mutation' GROUP BY YEAR(Date), MONTH(Date)" % excludestr)
	for r in results:
		k = "%d-%.2d" % (r[1], r[0])
		if stats.get(k) != None:
			stats[k]["Point/multiple mutation"] = r[2]

	results = db.execQuery("SELECT MONTH(Date), YEAR(Date), COUNT(id) FROM backrub WHERE %s AND Task='no_mutation' GROUP BY YEAR(Date), MONTH(Date)" % excludestr)
	for r in results:
		k = "%d-%.2d" % (r[1], r[0])
		if stats.get(k) != None:
			stats[k]["Backrub Ensemble"] = r[2]

	results = db.execQuery("SELECT MONTH(Date), YEAR(Date), COUNT(id) FROM backrub WHERE %s AND Task='ensemble' GROUP BY YEAR(Date), MONTH(Date)" % excludestr)
	for r in results:
		k = "%d-%.2d" % (r[1], r[0])
		if stats.get(k) != None:
			stats[k]["Backrub Ensemble Design"] = r[2]
	
	results = db.execQuery("SELECT MONTH(Date), YEAR(Date), COUNT(id) FROM backrub WHERE %s AND Task='sequence_tolerance' GROUP BY YEAR(Date), MONTH(Date)" % excludestr)
	for r in results:
		k = "%d-%.2d" % (r[1], r[0])
		if stats.get(k) != None:
			stats[k]["Sequence Tolerance (Elisabeth)"] = r[2]

	results = db.execQuery("SELECT MONTH(Date), YEAR(Date), COUNT(id) FROM backrub WHERE %s AND Task='sequence_tolerance_SK' GROUP BY YEAR(Date), MONTH(Date)" % excludestr)
	for r in results:
		k = "%d-%.2d" % (r[1], r[0])
		if stats.get(k) != None:
			stats[k]["Sequence Tolerance (Colin)"] = r[2]
	
	results = db.execQuery("SELECT * FROM Users ORDER BY ID", cursorClass = rosettadb.DictCursor)
	fields = ["Address1", "Address2", "City", "State", "Zip", "Country"]
	userGeoFreqCount = {}
	
	GoogleCountries = {"east timor": "TP", "samoa": "WS", "japan": "JP", "french southern territories": "TF", 
					"tokelau": "TK", "cayman islands": "KY", "azerbaijan": "AZ", "north korea": "KP", 
					"djibouti": "DJ", "french guiana": "GF", "malta": "MT", "guinea-bissau": "GW", 
					"hungary": "HU", "taiwan": "TW", "cyprus": "CY", "haiti": "HT", "barbados": "BB", 
					"eastern asia": "UN030", "bhutan": "BT", "yugoslavia": "YU", "lithuania": "LT", 
					"congo - kinshasa": "CD", "micronesia": "UN057", "andorra": "AD", 
					"union of soviet socialist republics": "SU", "rwanda": "RW", "aruba": "AW", 
					"liberia": "LR", "argentina": "AR", "norway": "NO", "sierra leone": "SL", 
					"somalia": "SO", "ghana": "GH", "falkland islands": "FK", "belarus": "BY", 
					"saint helena": "SH", "cuba": "CU", "middle africa": "UN017", "central asia": "UN143", 
					"french polynesia": "PF", "southern europe": "UN039", "guatemala": "GT", "isle of man": "IM",
					"belgium": "BE", "world": "UN001", "congo - brazzaville": "CG", "southern asia": "UN034", 
					"kazakhstan": "KZ", "burkina faso": "BF", "aland islands": "AX", "kyrgyzstan": "KG", "netherlands": "NL", "portugal": "PT", "central america": "UN013", "denmark": "DK", "philippines": "PH", "montserrat": "MS", "senegal": "SN", "moldova": "MD", "latvia": "LV", "croatia": "HR", "bosnia and herzegovina": "BA", "chad": "TD", "switzerland": "CH", "western europe": "UN155", "mali": "ML", "bulgaria": "BG", "jamaica": "JM", "albania": "AL", "angola": "AO", "colombia": "CO", "serbia and montenegro": "CS", "northern america": "UN021", "palestinian territory": "PS", "lebanon": "LB", "malaysia": "MY", "christmas island": "CX", "mozambique": "MZ", "greece": "GR", "zaire": "ZR", "nicaragua": "NI", "new zealand": "NZ", "southern africa": "UN018", "canada": "CA", "afghanistan": "AF", "qatar": "QA", "oceania": "UN009", "palau": "PW", "turkmenistan": "TM", "equatorial guinea": "GQ", "pitcairn": "PN", "guinea": "GN", "panama": "PA", "nepal": "NP", "central african republic": "CF", "luxembourg": "LU", "solomon islands": "SB", "south america": "UN005", "swaziland": "SZ", "cook islands": "CK", "tuvalu": "TV", "netherlands antilles": "AN", "namibia": "NA", "nauru": "NR", "venezuela": "VE", "australia and new zealand": "UN053", "outlying oceania": "QO", "europe": "UN150", "brunei": "BN", "iran": "IR", "british indian ocean territory": "IO", "united arab emirates": "AE", "south georgia and the south sandwich islands": "GS", "saint kitts and nevis": "KN", "sri lanka": "LK", "paraguay": "PY", "china": "CN", "armenia": "AM", "western asia": "UN145", "kiribati": "KI", "belize": "BZ", "tunisia": "TN", "ukraine": "UA", "melanesia": "UN054", "yemen": "YE", "northern mariana islands": "MP", "libya": "LY", "trinidad and tobago": "TT", "mayotte": "YT", "gambia": "GM", "finland": "FI", "macedonia": "MK", "americas": "UN019", "mauritius": "MU", "antigua and barbuda": "AG", "niue": "NU", "syria": "SY", "dominican republic": "DO", "people's democratic republic of yemen": "YD", "jersey": "JE", "burma": "BU", "pakistan": "PK", "romania": "RO", "seychelles": "SC", "metropolitan france": "FX", "czech republic": "CZ", "myanmar": "MM", "el salvador": "SV", "egypt": "EG", "neutral zone": "NT", "guam": "GU", "africa": "UN002", "papua new guinea": "PG", "wallis and futuna": "WF", "united states": "US", "austria": "AT", "greenland": "GL", "mongolia": "MN", "ivory coast": "CI", "thailand": "TH", "honduras": "HN", "niger": "NE", "fiji": "FJ", "comoros": "KM", "turkey": "TR", "united kingdom": "GB", "madagascar": "MG", "iraq": "IQ", "bangladesh": "BD", "mauritania": "MR", "eastern europe": "UN151", "bolivia": "BO", "uruguay": "UY", "france": "FR", "bahamas": "BS", "vatican": "VA", "slovakia": "SK", "gibraltar": "GI", "ireland": "IE", "laos": "LA", "british virgin islands": "VG", "south korea": "KR", "anguilla": "AI", "malawi": "MW", "ecuador": "EC", "israel": "IL", "peru": "PE", "algeria": "DZ", "serbia": "RS", "tanzania": "TZ", "puerto rico": "PR", "montenegro": "ME", "tajikistan": "TJ", "svalbard and jan mayen": "SJ", "togo": "TG", "jordan": "JO", "chile": "CL", "martinique": "MQ", "oman": "OM", "turks and caicos islands": "TC", "nigeria": "NG", "spain": "ES", "sao tome and principe": "ST", "georgia": "GE", "eastern africa": "UN014", "bouvet island": "BV", "asia": "UN142", "northern europe": "UN154", "american samoa": "AS", "polynesia": "UN061", "morocco": "MA", "sweden": "SE", "heard island and mcdonald islands": "HM", "gabon": "GA", "guyana": "GY", "western africa": "UN011", "grenada": "GD", "guadeloupe": "GP", "hong kong": "HK", "russia": "RU", "u.s. virgin islands": "VI", "cocos islands": "CC", "bahrain": "BH", "zimbabwe": "ZW", "estonia": "EE", "mexico": "MX", "reunion": "RE", "india": "IN", "new caledonia": "NC", "lesotho": "LS", "antarctica": "AQ", "australia": "AU", "saint vincent and the grenadines": "VC", "saint pierre and miquelon": "PM", "uganda": "UG", "burundi": "BI", "kenya": "KE", "macao": "MO", "botswana": "BW", "italy": "IT", "western sahara": "EH", "south africa": "ZA", "east germany": "DD", "cambodia": "KH", "ethiopia": "ET", "bermuda": "BM", "vanuatu": "VU", "marshall islands": "MH", "cameroon": "CM", "zambia": "ZM", "benin": "BJ", "brazil": "BR", "saudi arabia": "SA", "singapore": "SG", "faroe islands": "FO", "iceland": "IS", "saint lucia": "LC", "monaco": "MC", "costa rica": "CR", "united states minor outlying islands": "UM", "slovenia": "SI", "germany": "DE", "caribbean": "UN029", "san marino": "SM", "dominica": "DM", "suriname": "SR", "eritrea": "ER", "tonga": "TO", "maldives": "MV", "south-eastern asia": "UN035", "uzbekistan": "UZ", "northern africa": "UN015", "norfolk island": "NF", "poland": "PL", "indonesia": "ID", "cape verde": "CV", "sudan": "SD", "liechtenstein": "LI", "vietnam": "VN", "guernsey": "GG", "kuwait": "KW"};

	countryRemap = {
		"Iran (Islamic Republic of)" : "Iran",
		"Russian Federation" : "Russia",
		"Taiwan, Province of China" : "Taiwan",
		"Korea, Republic of" : "South Korea",
	}
	
	for r in results:
		if r["UserName"] != "guest":
			country = r["Country"]
			if country:
				country = countryRemap.get(country, country)
				if not GoogleCountries.get(country.lower()):
					print("Cannot find mapping for country %(Country)s of user %(UserName)s.<br>" % r)
				userGeoFreqCount[country] = userGeoFreqCount.get(country, 0) + 1
			else:
				pass
			
	generators = [
		[webstatsSuccessFailure, stats],
		[webstatsJobsByProtocol, stats],
		[webstatsJobsByProtocolCumulative, stats],
		[websiteUserGeoChart, userGeoFreqCount]
	]
	
	chartfns = []
	charthtml = []
	titles = []
	for g in generators:
		if len(g) > 1:
			gtitles, ghtml, gchartfns = g[0](*g[1:])
			titles.append(gtitles)
			charthtml.extend(ghtml)
			charthtml.append("<br><br>")
			chartfns.extend(gchartfns)
		else:
			charthtml.extend(g[0]())
	
	tabtitle = "Tabular data"
	titles.append(tabtitle)
	
	# Titles
	html.append('''<table><tr><td style="text-align:left"><div style="font-size:15pt">Web site statistics:</div><ol>''')
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
	
	html.extend(charthtml)
	
	html.append('''<span style="text-align:center; font-size:15pt"><A NAME="%(tabtitle)s"></A>%(tabtitle)s</span>''' % vars())
	html.append("<table style='margin-left: auto; margin-right: auto;'>")
	
	html.append("<tr><td><i>Contact Shane if you want these in another format e.g. CSV.</i><br><br></td></tr>")
	
	html.append("<tr><td><div style='text-align:left;'><b>Success/Failure rate</b></div></td></tr>")
	html.append("<tr><td><table border=1 cellpadding=2 cellspacing=0 width=260 ><tr style='background-color:#DDDDDD'>")
	html.append("<td width='130'>Month</td><td>Success</td><td>Failure</td></tr>")
	found = False
	for k, v in sorted(stats.iteritems()):
		if v.get("successful") or v.get("failed"):
			found = True
		if found:
			key = map(int, k.split("-"))
			if key[0] < 2011:
				continue
			elif key[0] == 2011 and key[1] <=5:
				continue
			dt = ("%s %d" % (calendar.month_name[key[1]], key[0]))
			html.append("<tr><td>%s</td><td>%d</td><td>%d</td></tr>" % (dt, v.get("successful", 0), v.get("failed", 0)))
	html.append("</table>")
	html.append("</td></tr>")
	
	html.append("<tr><td><br><br></td></tr>")
	
	html.append("<tr><td><div style='text-align:left;'><b>Jobs run by protocol</b></div></td></tr>")
	html.append("<tr><td><table border=1 cellpadding=2 cellspacing=0 width=760 ><tr style='background-color:#DDDDDD'>")
	html.append("<td width='130'>Month</td><td>Point/multiple Mutation</td><td>Backrub Ensemble</td><td>Backrub Ensemble Design</td><td>Sequence Tolerance (Elisabeth)</td><td>Sequence Tolerance (Colin)</td></tr>")
	found = False
	for k, v in sorted(stats.iteritems()):
		key = map(int, k.split("-"))
		if key[0] < 2011:
			continue
		elif key[0] == 2011 and key[1] <=5:
			continue
		dt = ("%s %d" % (calendar.month_name[key[1]], key[0]))
		html.append("<tr><td>%s</td><td>%d</td><td>%d</td><td>%d</td><td>%d</td><td>%d</td></tr>" % (dt, v.get("Point/multiple mutation", 0), v.get("Backrub Ensemble", 0), v.get("Backrub Ensemble Design", 0), v.get("Sequence Tolerance (Elisabeth)", 0), v.get("Sequence Tolerance (Colin)", 0)))
	html.append("</table>")
	html.append("</td></tr>")
	
	html.append("<tr><td><br><br></td></tr>")
	
	html.append("<tr><td><div style='text-align:left;'><b>Users by country</b></div></td></tr>")
	html.append("<tr><td><table border=1 cellpadding=2 cellspacing=0 width=200 ><tr style='background-color:#DDDDDD'>")
	html.append("<td width='130'>Country</td><td>#Users</td></tr>")
	for k, v in sorted(userGeoFreqCount.items(), key=lambda x:x[1], reverse=True):
		html.append("<tr><td>%s</td><td>%d</td></tr>" % (k, v))
	html.append("</table>")
	html.append("</td></tr>")

	html.append("</table>")
	
	return html, chartfns

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
		{"name" : "retrospect",	"desc" : "Backups",				"fn" : generateRetrospectLogPage,	"generate" :True,	"params" : []},
		{"name" : "diskstats",	"desc" : "Disk stats",			"fn" : generateDiskStatsSubpage,	"generate" :True,	"params" : [quotas, usage, users]},
		{"name" : "inventory",	"desc" : "IT inventory",		"fn" : generateITInventory,			"generate" :True,	"params" : []},
		{"name" : "jobadmin",	"desc" : "Job administration",	"fn" : generateJobAdminSubpage,		"generate" :True,	"params" : []},
		{"name" : "webusers",	"desc" : "Website users",		"fn" : generateWebUsersSubpage,		"generate" :True,	"params" : []},
		{"name" : "sitestats",	"desc" : "Website stats",		"fn" : generateWebserverStatsSubpage,"generate" :True,	"params" : []},
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
	gchartfns = []
	for subpage in subpages:
		html.append('<div style="display:none" id="%s">' % subpage["name"])
		if subpage["generate"]:
			h, gcf = subpage["fn"](*subpage["params"])
			html.extend(h)
			gchartfns.extend(gcf)
		html.append("</div>")
	
	# Prepare javascript calls
	for i in range(len(gchartfns)):
		gchartfns[i] += "();"


	html.append("</td>")
	html.extend(initGoogleCharts(gchartfns))
	html.append('''
<script src="/backrub/frontend/admin.js" type="text/javascript"></script>
<script src="/javascripts/sorttable.js"></script>''')

	return html