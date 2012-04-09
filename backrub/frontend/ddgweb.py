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
from rosettahelper import DEVELOPMENT_HOSTS, DEVELOPER_USERNAMES, saturateHexColor, make755Directory, ROSETTAWEB_SK_AAinv
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
			ddGdb.close()			
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
			ddGdb.close()
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
	prothermfile = os.path.join("/backrub", "ddgpdbs", "ProTherm25616.dat")
	prothermindices = os.path.join("/backrub", "ddgpdbs", "ProTherm25616-indices.dat")
	html = []
	chartfns = []
	html.append('''<table width="900px">''')
	html.append('''<tr align="center">''')
	html.append('''<td colspan=1>''')

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
	</td></tr>
	''')

		if form.has_key("ddgProThermID"):
			ID = form["ddgProThermID"].value
			if ID.isdigit():
				ID = int(ID)
				ddGdb = common.ddgproject.ddGDatabase(passwd = settings["ddGPassword"])
				ptReader = protherm_api.ProThermReader(prothermfile, ddgDB = ddGdb, quiet = True, skipIndexStore = True)
				
				# Caching the indices speeds up the ptReader construction from @2s to 0.2s
				if not os.path.exists(prothermindices):
					ptReader.storeRecordIndices()
					ptReader.saveIndicesToFile(prothermindices)
				else:
					ptReader.loadIndicesFromFile(prothermindices)
				
				try:
					record = ptReader.readRecord(ID)
					if not record:
						raise Exception("")
					html.append("<tr><td>")
					html.extend(ptReader.getRecordHTML(ID))
					html.append("</td></tr>")
				except:
					html.append("<br><br>Could not find a record with ID #%s." % str(ID))
				scoreresults = ddGdb.execute('SELECT SourceID, ExperimentID, ExperimentScore.ID as ExperimentScoreID, ddG AS ddG_in_kcal, NumberOfMeasurements, Publication, Experiment.Source as Source, Experiment.Structure as Structure FROM ExperimentScore INNER JOIN Experiment ON ExperimentScore.ExperimentID=Experiment.ID WHERE SourceID=%s AND Source LIKE "ProTherm%%"', parameters=(ID,))
				assert(len(scoreresults) <= 1)
				if scoreresults:
					scoreresults = scoreresults[0]
					experimentID = scoreresults["ExperimentID"]
					mutation_results = ddGdb.execute('SELECT ExperimentMutation.* FROM ExperimentMutation INNER JOIN Experiment ON ExperimentMutation.ExperimentID=Experiment.ID WHERE Experiment.ID=%s', parameters=(experimentID,))
					experiment_rows = [
						"ExperimentID",
						"Source",
						"Structure",
					]
					experiment_score_rows = [
						"ExperimentScoreID",
						"SourceID",
						"ddG_in_kcal",
						"NumberOfMeasurements",
						"Publication",
					]
					mutation_rows = [
						"Chain",
						"ResidueID",
						"WildTypeAA",
						"MutantAA",
						"SecondaryStructurePosition",
					]
					
					html.append("<tr><td align='center'>")
					html.append("<br><br><b>Record as stored in our database</b><br>")
					html.append("<table align='center'>")
					html.append('<tr><td style="background-color:#bb8888; border:1px solid black;">Experiment</td></tr>')
					for r in experiment_rows:
						html.append("<tr><td></td><td style='background-color:#bbbbbb; border:1px solid black;'>%s</td><td style='background-color:#bbbbee; border:1px solid black;'>%s</td></tr>" % (r, str(scoreresults[r])))
					html.append('<tr><td style="background-color:#bb8888; border:1px solid black;">ExperimentScore</td></tr>')
					for r in experiment_score_rows:
						html.append("<tr><td></td><td style='background-color:#bbbbbb; border:1px solid black;'>%s</td><td style='background-color:#bbbbee; border:1px solid black;'>%s</td></tr>" % (r.replace("_", " "), str(scoreresults[r])))
					html.append('<tr><td style="background-color:#bb8888; border:1px solid black;">ExperimentMutation</td></tr>')
					count = 1
					for m in mutation_results:
						if m["SecondaryStructurePosition"]:
							m["SecondaryStructurePosition"] = "(%s)" % m["SecondaryStructurePosition"]
						else:
							m["SecondaryStructurePosition"] = ""
						html.append("<tr><td></td><td style='background-color:#bbbbbb; border:1px solid black;'>Mutation %d</td>" % count)
						html.append("<td style='background-color:#bbbbee; border:1px solid black;'>Chain %(Chain)s, %(WildTypeAA)s %(ResidueID)s %(MutantAA)s %(SecondaryStructurePosition)s</td></tr>" % (m))
						count += 1
					html.append("</table>")
					html.append("</td></tr>")
				ddGdb.close()
				
	html.append('''</td>''')
	html.append('''</tr>''')
	html.append('''</table>''')
	return html, chartfns

def getLinsData(PredictionSet):
	ddGdb = common.ddgproject.ddGDatabase(passwd = settings["ddGPassword"])
	
	FilePrefix = "%s_" % PredictionSet.split("-")[1]
	PDBID = "%s_lin" % PredictionSet.split("-")[1]
	
	numMissingResults = ddGdb.execute('''SELECT COUNT(ID) FROM `Prediction` WHERE PredictionSet= %s AND Status<>"done"''', parameters=(PredictionSet,), cursorClass=common.ddgproject.StdCursor)[0][0]
	
	dlpath = os.path.join(settings["DownloadDir"], "ddG", PredictionSet)
	if not os.path.exists(dlpath):
		make755Directory(dlpath)
	
	results = ddGdb.execute('''
	SELECT ID, Chain, ResidueID, WildTypeAA, MutantAA, ddG, TIME_TO_SEC(TIMEDIFF(EndDate,StartDate))/60 as TimeTakenInMinutes FROM  `Prediction` 
	INNER JOIN ExperimentMutation ON Prediction.ExperimentID = ExperimentMutation.ExperimentID
	WHERE PredictionSet= %s AND Status="done"''', parameters=(PredictionSet,))
	
	individual_results_by_position = {}
	results_grouped_by_position = {}
	wildtypes = {}
	for r in results:
		assert(r["Chain"] == "A")
		assert(r["WildTypeAA"] != r["MutantAA"])
		resid = r["ResidueID"]
		ddG = pickle.loads(r["ddG"])["data"]["ddG"]
		
		individual_results_by_position[resid] = individual_results_by_position.get(resid) or {}
		individual_results_by_position[resid][r["MutantAA"]] = (r["WildTypeAA"], ddG, r["TimeTakenInMinutes"])
		
		wildtypes[resid] = r["WildTypeAA"]
		
		#results_grouped_by_position[resid] = results_grouped_by_position.get(resid) or []
		#results_grouped_by_position[resid].append((ddG, r["MutantAA"]))
	
	F = open(os.path.join(dlpath, "%sPredictionsByMutation.csv" % FilePrefix), "w")
	F.write("Chain\tResidueID\tWildType\tMutant\tddG\tWallTimeInMinutes\n")
	# Warning: This sorting only works because there are no insertion codes (casting to int is okay)
	for position in sorted(individual_results_by_position.keys(), key=lambda pos : int(pos)):
		for mutant, values in individual_results_by_position[position].iteritems():
			F.write("A\t%s\t%s\t%s\t%s\t%s\n" % (position, values[0], mutant, values[1], values[2]))
	F.close()
	
	aas = ROSETTAWEB_SK_AAinv.keys()
	F = open(os.path.join(dlpath, "%sPredictionsByResidueID.csv" % FilePrefix), "w")
	F.write("Chain\tResidueID\tWildType\tBestMutant\tBestMutant_ddG\t%s\n" % join(sorted(aas),"\t"))
	
	# Warning: This sorting only works because there are no insertion codes (casting to int is okay)
	minimum_best_mutant = 900
	maximum_best_mutant = -900
	best_mutants = {}
	for position in sorted(individual_results_by_position.keys(), key=lambda pos : int(pos)):
		F.write("A\t%s\t%s\t" % (position, wildtypes[position]))
		
		results_grouped_by_position = [] 
		for mutant, values in individual_results_by_position[position].iteritems():
			results_grouped_by_position.append((values[1], mutant))
		
		best_mutant = sorted(results_grouped_by_position, key=lambda ddg_aa_pair : ddg_aa_pair[0])[0]
		best_mutants[position] = best_mutant[0] 
		minimum_best_mutant = min(minimum_best_mutant, best_mutant[0])
		maximum_best_mutant = max(maximum_best_mutant, best_mutant[0])
		F.write("%s\t%s\t" % (best_mutant[1], best_mutant[0]))
		
		results_grouped_by_position.append((0, wildtypes[position]))
		existingAAs = [r[1] for r in results_grouped_by_position]
		missingAAs = set(aas).difference(existingAAs)
		for missingAA in missingAAs:
			results_grouped_by_position.append(('N/A', missingAA))
		
		sorted_by_AA = sorted(results_grouped_by_position, key=lambda ddg_aa_pair : ddg_aa_pair[1])
		F.write(join([str(mtscore[0]) for mtscore in sorted_by_AA], "\t")) 
		F.write("\n")
	F.close()
	
	scaling_factor = min(50/abs(minimum_best_mutant), 50/abs(maximum_best_mutant)) - 0.05 # For scaling numbers from 0-100
	if numMissingResults == 0:
		F = open(os.path.join(dlpath, "%sbfactors.pdb" % FilePrefix), "w")
		pdbcontents = ddGdb.execute('''SELECT Content FROM Structure WHERE PDB_ID=%s''', parameters = (PDBID,))[0]["Content"].split("\n")
		for line in pdbcontents:
			if line.startswith("ATOM  "):
				assert(line[21] == "A")
				assert(line[26] == " ")
				position = line[22:27].strip()
				newbfactor = "%.4f" % ((50.0 + (best_mutants[position] * scaling_factor))/100.0)
				assert(0 <= float(newbfactor) <= 1.0)
				assert(len(newbfactor) == 6)
				F.write("%s%s%s\n" % (line[0:60], newbfactor, line[66:]))
			else:
				F.write("%s\n" % line)
		F.close()
	
	
def generateStatusPage(form):
	html = []
	html.append('''<table width="900px">''')
	html.append('''<tr align="center">''')
	html.append('''<td colspan=2>''')
	
	# Create chart
	title = "Job status"
	fnname = "drawDDGJobProgress"
	chartfns = [fnname]
	
	ddGdb = common.ddgproject.ddGDatabase(passwd = settings["ddGPassword"])
	results = ddGdb.execute('''SELECT PredictionSet, Status, COUNT(*) AS Count FROM Prediction WHERE PredictionSet <> "testrun" GROUP BY PredictionSet, Status;''')
	predictionSets =  {}
	
	statusOrder = ["done", "active", "queued", "failed"]
	statusColors = {
		"done" : "#404040", #00bb00",
		"active" : "#00bb00", #00FFFF",
		"queued" : "#FFFF44", #8888ff",
		"failed" : "#ff0000",
	}
	for r in results:
		if not predictionSets.get(r["PredictionSet"]):
			newtbl = {}
			for color in statusColors:
				newtbl[color] = 0
			predictionSets[r["PredictionSet"]] = newtbl
		assert(r["Status"] in statusColors.keys())
		predictionSets[r["PredictionSet"]][r["Status"]] = r["Count"]
	ddGdb.close()
	
	for predictionSet in predictionSets.keys(): 
		if predictionSet.startswith("lin-"):
			getLinsData(predictionSet)
	
	ddG_dlpath = "http://albana.ucsf.edu/backrub/downloads/ddG/"
	html.append('''
	<script type="text/javascript">
	ddG_dlpath = "%(ddG_dlpath)s"; 
	function %(fnname)s() {''' % vars())
	if results:
		html.append('''
		// Create our data table.
		var data = new google.visualization.DataTable();
		data.addColumn('string', 'Prediction set');''')
		for status in statusOrder:
			html.append('''data.addColumn('number', '%s');\n''' % status)
		html.append('''data.addRows([\n''')
		for predictionSet, data in sorted(predictionSets.iteritems()):
			html.append('''["%s", ''' % predictionSet)
			html.append(join(map(str, [data[status] for status in statusOrder]), ","))
			html.append('''],''')
		html.append(''']);
		
		// Instantiate and draw our chart, passing in some options.
		var chart = new google.visualization.BarChart(document.getElementById('ddgJobStatusChart'));
		seriesstyle = {''')
		count = 0
		for status in statusOrder:
			html.append('''%d:{color: '%s'},''' % (count, statusColors[status]))
			count += 1
		html.append('''}
		chart.draw(data, {width: 800, height: 360, isStacked:true, series:seriesstyle, backgroundColor:'#f2f2ff'});
		google.visualization.events.addListener(chart, 'select', ddGStatusSelectHandler);
		
		function ddGStatusSelectHandler() {
			var selection = chart.getSelection();
			var message = '';
			var predictionSet = null;
			for (var i = 0; i < selection.length; i++) {
				var item = selection[i];
				if (item.row != null)
				{
					predictionSet = data.getFormattedValue(item.row, 0);
					if ((predictionSet.length > 4) && (predictionSet.substring(0, 4) == "lin-"))
					{
						window.open(ddG_dlpath + predictionSet, "ddGresults");
					}
				}
			}
		}
		''')
	html.append('''
	}
	</script>
	''')
	html.append('''<span style="text-align:center; font-size:15pt"><A NAME="%(title)s"></A>%(title)s<br><br></span>''' % vars())
	html.append('''<div id="ddgJobStatusChart"></div>''')
	
	for predictionSet, data in sorted(predictionSets.iteritems()):
		if data["active"]:
			html.append('''<div><br><b>%s has %d active jobs.</b><div>''' % (predictionSet, data["active"]))

	#if form.has_key("ddgJmolPDB"):
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
		{"name" : "status",		"desc" : "Job status",			"fn" : generateStatusPage,			"generate" :True,	"params" : [form]},
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