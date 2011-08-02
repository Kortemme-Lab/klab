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


userColors = {}
showHistoryForDays = 31
settings = None

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

def getAlbanaConnection():
    return rosettadb.RosettaDB(settings)

def getJobs():
    userid='27'
    output = StringIO()
    output.write('<TD align="center">')
    
    results = []
    # Get all jobs on the live webserver which were submitted from this server and which have not expired
    KlabDBConnection = getKlabDBConnection()
    
    connections = [getKlabDBConnection(), getAlbanaConnection()]
    
    for connection in connections:
        sql = "SELECT ID, cryptID, Status, UserID, Date, Notes, Mini, EnsembleSize, Errors, task, BackrubServer, Expired FROM backrub ORDER BY backrub.ID DESC" 
        result = connection.execQuery(sql)
    
        for line in result:
            sql = "SELECT UserName FROM Users WHERE ID=%s" % line[3]
            result2 = KlabDBConnection.execQuery(sql)
            new_list = []
            new_list.extend(line)
            new_list[3] = result2[0][0]
            results.append(new_list)
        connection.close()
  
    # Sort the jobs by date
    results.sort(key = lambda x:x[6], reverse = True) 
        
    return results

def generateJobAdminSubpage():
    html = []
    job_list = getJobs()
    html.append("""<H1 class="title"> Job queue </H1> <br>
          <div id="queue_bg">
          <table border=0 cellpadding=2 cellspacing=0 width=700 >
           <colgroup>
             <col width="35">
             <col width="80">
             <col width="90">
             <col width="90">
             <col width="200">
             <col width="160">
             <col width="25">
           </colgroup>
          <tr align=center bgcolor="#828282" style="color:white;"> 
           <td > ID </td> 
           <td > Status </td> 
           <td > User Name </td>
           <td > Date (PST) </td>
           <td > Job Name </td>
           <td > Rosetta Application </td>
           <td > Structures </td>\n""")

    for line in job_list:
        jobIsLocal = True
        server = line[10]
        
        task = line[9]
        task_color = "#888888"
        
        bgcolor = "#EEEEEE"
        if not jobIsLocal:
            bgcolor = "#DDDDFF"
        
        html.append("""<tr align=center bgcolor="%s" onmouseover="this.style.background='#447DAE'; this.style.color='#FFFFFF';" onmouseout="this.style.background='%s'; this.style.color='#000000';" >""" % (bgcolor, bgcolor))
        link_to_job = ''
        
        # write ID
        html.append('<td class="lw" %s>%s </td>' % (link_to_job, str(line[0])))
        # write status 
        status = int(line[2])
        
        if status == 0:
            html.append('<td class="lw" %s><font color="orange">in queue</font></td>' % link_to_job)
        elif status == 1:
            html.append('<td class="lw" %s><font color="green">active</font></td>' % link_to_job)
        elif status == 2:
            html.append('<td class="lw" %s><font color="black">done</font></td>' % link_to_job) # <font color="darkblue" %s></font>
        elif status == 5:
            html.append('<td class="lw" style="background-color: #AFE2C2;" %s><font color="darkblue">sample</font></td>' % link_to_job)
        else:
          # write error
          if  str(line[8]) != '' and line[8] != None:
            # onclick="window.open('https://kortemmelab.ucsf.edu/backrub/wiki/Error#Errors_during_the_simulation','backrub_wiki')"
            #                        onmouseover="this.style.background='#447DAE'; this.style.color='#000000'"
            #                        onmouseout="this.style.background='#EEEEEE';"
            html.append('''<td class="lw">
                          <font color="FF0000">error</font>
                          (<a href="https://kortemmelab.ucsf.edu/backrub/wiki/Error#Errors_during_the_simulation" target="_blank"
                             onmouseover="this.style.color='#FFFFFF'" onmouseout="this.style.color='#365a79'">%s</a>)</td>''' % str(line[8]))
          else:
            html.append('<td class="lw"><font color="FF0000">error</font></td>')
            
        # write username
        html.append('<td class="lw" %s>%s</td>' % (link_to_job, str(line[3])))
        # write date
        html.append('<td class="lw" style="font-size:small;" %s>%s</td>' % (link_to_job, str(line[4])))
        # write jobname or "notes"
        if len(str(line[5])) < 26:
            html.append('<td class="lw" %s>%s</td>' % (link_to_job, str(line[5])))
        else:
            html.append('<td class="lw" %s>%s</td>' % (link_to_job, str(line[5])[0:23] + "..."))
        
        # Rosetta version
        # todo: the mini/classic distinction is somewhat deprecated with the new seqtol protocol
        miniVersion = line[6]
        html.append('<td class="lw" style="font-size:small;" bgcolor="%s" %s ><i>%s</i><br>%s</td>' % (task_color, link_to_job, miniVersion, task))
    
        # write size of ensemble
        html.append('<td class="lw" %s >%s</td></tr>\n' % (link_to_job, str(line[7])))
            
    html.append('</table> </div>')
    return html

def generateAdminPage(quotas, usage, users, settings_):
    
    global settings
    settings = settings_
    
    # Create menu
    html = ['''<script src="/backrub/frontend/admin.js" type="text/javascript"></script>''']
    html.append("<td align=center>")
    html.append('''<input type="button" value="Disk stats" onClick="showPage('diskstats');">''')
    html.append('''<input type="button" value="Job administration" onClick="showPage('jobadmin');">''')
    html.append("</td></tr><tr>")
    
    html.append("<td align=left>")
    
    # Disk stats
    html.append("<div id='diskstats'>")
    html.extend(generateDiskStatsSubpage(quotas, usage, users))
    html.append("</div>")

    # Job admin
    html.append('<div style="display:none" id="jobadmin">')
    html.extend(generateJobAdminSubpage())
    html.append("</div>")
    
    html.append("</td>")
    return html