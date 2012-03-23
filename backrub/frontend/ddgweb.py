#!/usr/bin/python2.4
# -*- coding: iso-8859-15 -*-

########################################
# Code for the ddg page
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
import sys
import common
from ddglib import ddgfilters, protherm_api

settings = None
script_filename = None

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

def viewStructure(StructureID, ExperimentID, PredictionID, mutations = []):
	"""This shows the Jmol applet for a structure"""
	
	html = []
	pdb_filepath = os.path.join("../ddgpdbs", StructureID + ".pdb")
	if os.path.exists(pdb_filepath):
		jmol_cmd = ' "load %s;  cpk off; cartoon on; wireframe off; backbone 0.2;" +\n' % (pdb_filepath)
		jmol_cmd += ' "cpk off; wireframe off; backbone 0.2;" +'
		jmol_cmd_highlighted = ''
		if mutations:
			for m in mutations:
				jmol_cmd_highlighted += 'select %s:%s; color backbone green; cartoon off; backbone on; wireframe 0.25; ' % ( m["ResidueID"], m["Chain"])		
	
		html.append('''
				<tr>
				<td width="150px" style="text-align:justify;vertical-align:top" bgcolor="#d8fcd8" style="min-width:200px">
				<div><b>Model: </b>%s</div>''' % StructureID)
		if ExperimentID:
			html.append('''
				<div><b>Experiment ID: </b>%s</div>''' % ExperimentID)
		if PredictionID:
			html.append('''
				<div><b>Prediction ID: </b>%s</div>''' % PredictionID)
		if mutations:
			html.append('''
				<div><b>Mutations:</b><br>''')
			for m in mutations:
				html.append('''
				Chain: %(Chain)s, %(WildTypeAA)s%(ResidueID)s &#8594; %(MutantAA)s<br>''' % m)
			html.append("</div>")
		html.append('''
				 <br>
				 </td>
				 <td bgcolor="#ffffff">
					 <table>
						 <tr>
							 <td> 
								<script type="text/javascript">
								  jmolInitialize("../../jmol");
								  jmolApplet(700, "set appendNew false;" + %s "%s frame all;" ); 
								</script>
								<br>
								<small>Jmol: an open-source Java viewer for chemical structures in 3D.</small><br><a href="http://www.jmol.org"><small>www.jmol.org</small></a>
							 </td>
						 </tr>
					 </table>
				 </td>
				</tr>
				''' % (jmol_cmd, jmol_cmd_highlighted))
	else:
		html.append("<tr><td align='center' colspan=2>Could not locate %s.pdb.</td></tr>" % StructureID)
	return html

def generateJmolPage(form):
	html = []
	chartfns = []
	html.append('''<table width="900px">''')
	html.append('''<tr align="center">''')
	html.append('''<td colspan=2>''')
	filename = None
	mutations = None
	ExperimentID = None
	PredictionID = None
	StructureID = None
	estring = None
	try:
		if form.has_key("ddgJmolPDB"):
			StructureID = form["ddgJmolPDB"].value
		elif form.has_key("ddgJmolExperimentID"):
			estring = "Could not retrieve results from experiment %s." % form["ddgJmolExperimentID"].value
			ExperimentID = form["ddgJmolExperimentID"].value
			ddGdb = common.ddgproject.ddGDatabase(passwd = settings["ddGPassword"])
			er = ddgfilters.ExperimentResultSet.fromIDs(ddGdb, [int(ExperimentID)])
			IDs = er.getStructures()[0].IDs
			assert(len(IDs) == 1)
			StructureID = IDs.pop()
			
			results = ddGdb.callproc("GetMutations", parameters = ExperimentID)
			mutations = results
			estring = None
		elif form.has_key("ddgJmolPredictionID"):
			estring = "Could not retrieve results from prediction %s." % form["ddgJmolPredictionID"].value
			PredictionID = form["ddgJmolPredictionID"].value
			ddGdb = common.ddgproject.ddGDatabase(passwd = settings["ddGPassword"])
			pr = ddgfilters.PredictionResultSet.fromIDs(ddGdb, [int(PredictionID)])
			IDs = pr.getStructures()[0].IDs
			assert(len(IDs) == 1)
			StructureID = IDs.pop()
			
			ExperimentID = pr.getFilteredResults()[0]["ExperimentID"]
			results = ddGdb.callproc("GetMutations", parameters = ExperimentID)
			mutations = results
			estring = None
	except Exception, e:
		if not estring:
			import traceback
			print(traceback.format_exc().replace("\n", "<br>"))
			print(str(e))		

#<form name="ddgJmolForm" method="post" action="%s">
#</form>
	html.append('''
<table style="background-color:#999999;margin-left: auto; margin-right: auto;">
	<tr style="text-align:center;">
		<td>PDB ID</td>
		<td>Experiment ID</td>
		<td>Prediction ID</td>
	</tr>
	<tr>
		<td><input type=text size=4 maxlength=4 name=ddgJmolPDB value=""
		 	onkeydown="if (event.keyCode == 13){document.ddgform.ddgJmolPDB.value = this.value;document.ddgform.query.value='ddg'; document.ddgform.submit();}"></td>
		<td><input type=text size=8 maxlength=8 name=ddgJmolExperimentID value=""
		 	onkeydown="if (event.keyCode == 13){document.ddgform.ddgJmolExperimentID.value = this.value;document.ddgform.query.value='ddg'; document.ddgform.submit();}"></td>
		<td><input type=text size=8 maxlength=8 name=ddgJmolPredictionID value=""
		 	onkeydown="if (event.keyCode == 13){document.ddgform.ddgJmolPredictionID.value = this.value;document.ddgform.query.value='ddg'; document.ddgform.submit();}"></td>
	</tr>
</table>
''')
	html.append('''</td>''')
	html.append('''</tr>''')
	if estring:
		html.append("<tr><td colspan=2 align=center>%s</td></tr>" % estring)
	elif StructureID:
		html.extend(viewStructure(StructureID, ExperimentID, PredictionID, mutations))
	
	html.append('''</table>''')
	return html, chartfns

def generateProThermPage(form):
	prothermfile = os.path.join("/backrub", "daemon" ,"ddglib", "ProTherm25616.dat")
	html = []
	chartfns = []
	html.append('''<table width="900px">''')
	html.append('''<tr align="center">''')
	html.append('''<td colspan=2>''')

	if not os.path.exists(prothermfile):
		html.append("Cannot locate ProTherm file %s" % prothermfile)
	else:
		html.append('''
	<table style="background-color:#999999;margin-left: auto; margin-right: auto;">
		<tr style="text-align:center;">
			<td>ProTherm ID</td>
		</tr>
		<tr>
			<td><input type=text size=7 maxlength=7 name=ddgProThermID value=""
			 	onkeydown="if (event.keyCode == 13){document.ddgform.ddgProThermID.value = this.value;document.ddgform.query.value='ddg'; document.ddgform.submit();}"></td>
		</tr>
	</table>
	''')

		if form.has_key("ddgProThermID"):
			ID = form["ddgProThermID"].value
			if ID.isdigit():
				ID = int(ID)
				ddGdb = common.ddgproject.ddGDatabase(passwd = settings["ddGPassword"])
				ptReader = protherm_api.ProThermReader(prothermfile, ddgDB = ddGdb, quiet = True)
				try:
					record = ptReader.readRecord(ID)
					if not record:
						raise Exception("")
					html.extend(ptReader.getRecordHTML(ID))
				except:
					html.append("<br><br>Could not find a record with ID #%s." % str(ID))
				ddGdb.close()
	
	html.append('''</td>''')
	html.append('''</tr>''')
	html.append('''</table>''')
	return html, chartfns

def generateGenericPage(form):
	html = []
	chartfns = []
	html.append('''<table width="900px">''')
	html.append('''<tr align="center">''')
	html.append('''<td colspan=2>''')
	
	#if form.has_key("ddgJmolPDB"):
	html.append('''</td>''')
	html.append('''</tr>''')
	html.append('''</table>''')
	return html, chartfns

def generateDDGPage(settings_, rosettahtml, form):

	global settings
	global protocols
	global script_filename
	settings = settings_
	script_filename = rosettahtml.script_filename 
	
	ddgpage = ""
	if form.has_key("DDGPage"):
		ddgpage = form["DDGPage"].value
	
	# Set generate to False to hide pages for quicker testing
	subpages = [
		{"name" : "jmol",		"desc" : "Jmol viewer",			"fn" : generateJmolPage,			"generate" :True,	"params" : [form]},
		{"name" : "protherm",	"desc" : "ProTherm viewer",		"fn" : generateProThermPage,		"generate" :True,	"params" : [form]},
		]
	
	# Create menu
	html = []
	html.append("<td align=center>")
	html.append('''<FORM name="ddgform" method="post">''')
	
	for subpage in subpages:
		if subpage["generate"]:
			html.append('''<input type="button" value="%(desc)s" onClick="showPage('%(name)s');">''' % subpage)
	
	html.append('''<input type="button" value="Refresh" onClick="document.ddgform.query.value='ddg'; document.ddgform.submit();">''')
	html.append('''<input type="hidden" NAME="DDGPage" VALUE="%s">''' % ddgpage)
	html.append('''<input type="hidden" NAME="query" VALUE="">''')
	html.append('''<input type="hidden" NAME="ddgJmolPDB" VALUE="">''')
	html.append('''<input type="hidden" NAME="ddgJmolExperimentID" VALUE="">''')
	html.append('''<input type="hidden" NAME="ddgJmolPredictionID" VALUE="">''')
	html.append('''<input type="hidden" NAME="ddgProThermID" VALUE="">''')
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
<script src="/backrub/frontend/ddgweb.js" type="text/javascript"></script>
<script src="/jmol/Jmol.js" type="text/javascript"></script>
<script src="/javascripts/sorttable.js" type="text/javascript"></script>''')

	return html