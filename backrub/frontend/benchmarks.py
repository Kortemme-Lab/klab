#!/usr/bin/python2.4
# -*- coding: iso-8859-15 -*-

########################################
# Code for the benchmarks page
########################################

import os, re
import datetime
from datetime import date
from string import join
import pickle
import string
import rosettadb
from rosettahelper import DEVELOPMENT_HOSTS, DEVELOPER_USERNAMES
import locale
locale.setlocale(locale.LC_ALL, 'en_US')

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

def generateSubmissionPage(benchmark_options):
	html = []
	html.append('''''')
	
	benchmarks = benchmark_options['benchmarks']
	benchmark_names = sorted(benchmarks.keys())
	benchmarks['KIC']['revisions'] = [48255, 48528] #todo: hardcoded
	benchmarks['KIC']['dbrevisions'] = [48255, 48528] #todo: hardcoded
	
	benchmarkselector_html = ['<select name="BenchmarkType">']
	for benchmark in benchmark_names:
		benchmarkselector_html.append('<option value="%(benchmark)s">%(benchmark)s</option>' % vars())
	benchmarkselector_html.append('</select>')

	runlengths = benchmark_options['runlengths']
	runlengthselector_html = ['<select name="BenchmarkRunLength">']
	for runlength in runlengths:
		runlengthselector_html.append('<option value="%(runlength)s">%(runlength)s</option>' % vars())
	runlengthselector_html.append('</select>')

	rosettarevisionselector_html = ['<select name="BenchmarkRosettaRevision">']
	for rosettarevision in benchmarks['KIC']['revisions']: # Should be determined using JS
		rosettarevisionselector_html.append('<option value="%(rosettarevision)s">%(rosettarevision)s</option>' % vars())
	rosettarevisionselector_html.append('</select>')
	
	rosettadbrevisionselector_html = ['<select name="BenchmarkRosettaDBRevision">']
	for rosettadbrevision in benchmarks['KIC']['revisions']:
		rosettadbrevisionselector_html.append('<option value="%(rosettadbrevision)s">%(rosettadbrevision)s</option>' % vars())
	rosettadbrevisionselector_html.append('</select>')
	
	clusterqueues = benchmark_options['ClusterQueues']
	clusterqueueselector_html = ['<select name="BenchmarkClusterQueue">']
	for clusterqueue in clusterqueues:
		clusterqueueselector_html.append('<option value="%(clusterqueue)s">%(clusterqueue)s</option>' % vars())
	clusterqueueselector_html.append('</select>')

	clusterarchitectures = benchmark_options['ClusterArchitectures']
	clusterarchitectureselector_html = ['<select name="BenchmarkClusterArchitecture">']
	for clusterarchitecture in clusterarchitectures:
		clusterarchitectureselector_html.append('<option value="%(clusterarchitecture)s">%(clusterarchitecture)s</option>' % vars())
	clusterarchitectureselector_html.append('</select>')

	#Ideally we'd use the JSON module here but we need to upgrade to 2.6
	#import json
	#json.dumps(benchmarks) # use default=longhandler?
	for b in benchmark_names:
		for option in benchmarks[b]['options']:
			for k,v in option.iteritems():
				if v == None:
					option[k] = 'null'
				elif type(v) == type(1L):
					if v < 2^31:
						option[k] = int(v)
					else:
						raise Exception("Need to reformat longs for JSON.")
	
	html.append('''<script type="text/javascript">benchmarks=%(benchmarks)s;</script>''' % vars())
	
	benchmark_alternate_flags_selector_html = []
	for benchmark in benchmark_names:
		benchmark_alternate_flags = benchmarks[benchmark]['alternate_flags']
		benchmark_alternate_flags_selector_html.append('<select style="display:none;" name="BenchmarkAlternateFlags%(benchmark)s">' % vars())
		for alternate_flags in benchmark_alternate_flags:
			benchmark_alternate_flags_selector_html.append('<option value="%(alternate_flags)s">%(alternate_flags)s</option>' % vars())
		benchmark_alternate_flags_selector_html.append('</select>')

	tablewidth = 200
	
	html.append('''<style type="text/css">
table.benchmarks {}
td.benchmarks {border: 0}
tr.benchmarks {border: 0}
</style>''')
	html.append('''<center><div>''')
	html.append('''<H1 align=left> Submit a new benchmark run</H1><br>''')
	html.append('''<FORM name="benchmarkoptionsform" method="post">''')
	html.append('''<table style="width:800px;">''')
	html.append('''<tr><td>''')
	html.append('''<table style="text-align:left">''')
	html.append('''<tr><td><div style="width:%(tablewidth)dpx">Benchmark</div></td>''' % vars())
	html.append('''<td>%s</td></tr>''' % join(benchmarkselector_html,""))
	html.append('''<tr><td><div style="width:%(tablewidth)dpx">Run length</div></td>''' % vars())
	html.append('''<td>%s</td></tr>''' % join(runlengthselector_html,""))
	html.append('''<tr><td><div style="width:%(tablewidth)dpx">Rosetta revision</div></td>''' % vars())
	html.append('''<td>%s</td></tr>''' % join(rosettarevisionselector_html,""))
	html.append('''<tr><td><div style="width:%(tablewidth)dpx">Rosetta database revision</div></td>''' % vars())
	html.append('''<td>%s</td></tr>''' % join(rosettadbrevisionselector_html,""))
	html.append('''</table>''')
	html.append('''</td></tr>''')
	
	html.append('''<tr><td>''')
	html.append('''<br><b><i>Benchmark settings</i></b><br>''')
	html.append('''<table class="benchmarks"  style="text-align:left; table-layout: fixed;">''')
	html.append('''<tr><td><div style="width:%(tablewidth)dpx">Command line flags</div></td><td>
	<input type="radio" onchange='editCommandLine()' name="BenchmarkCommandLineType" checked="true" value="Standard">Standard
	<input type="radio" onchange='editCommandLine()' name="BenchmarkCommandLineType" value="ExtraFlags">Extra flags
	<input type="radio" onchange='editCommandLine()' name="BenchmarkCommandLineType" value="Custom">Custom
	</td></tr>''' % vars())
	html.append('''<tr><td></td><td>%s</td></tr>''' % join(benchmark_alternate_flags_selector_html,""))
	html.append('''<tr><td></td><td><input type="text" style="display:none; width:500px" maxlength=1024 readonly="true" name="BenchmarkCommandLine_1" value="%s"></input></td></tr>''' % benchmarks[benchmark_names[0]]['ParameterizedFlags'])
	html.append('''<tr><td></td><td><input type="text" style="display:none; width:500px" maxlength=1024 name="BenchmarkCommandLine_2" value="%s"></input></td></tr>''' % benchmarks[benchmark_names[0]]['SimpleFlags'])
	for benchmark in benchmark_names:
		for option in benchmarks[benchmark]['options']:
			if option["Type"] == 'int':
				html.append('''<tr><td><div style="width:%(tablewidth)dpx">''' % vars())
				html.append('''%(Description)s</div></td><td><input type="text" style="width:75px" maxlength=8 name="Benchmark%(BenchmarkID)sOption%(OptionName)s" value="%(DefaultValue)s"></input></td></tr>''' % option)
	html.append('''</table>''')
	html.append('''</td></tr>''')
	
	html.append('''<tr><td>''')
	html.append('''<br><b><i>Cluster settings</i></b><br>''')
	
	
	html.append('''<table style="text-align:left; table-layout: fixed;">''')
	html.append('''<tr><td><div style="width:%(tablewidth)dpx">Cluster queue</div></td>''' % vars())
	html.append('''<td>%s</td></tr>''' % join(clusterqueueselector_html,""))
	html.append('''<tr><td><div style="width:%(tablewidth)dpx">Cluster architecture</div></td>''' % vars())
	html.append('''<td>%s</td></tr>''' % join(clusterarchitectureselector_html,""))
	html.append('''<tr><td><div style="width:%(tablewidth)dpx">Memory requirement (GB)</div></td>''' % vars())
	html.append('''<td><input type="text" style="width:75px" maxlength=8 name="BenchmarkMemoryRequirement" value="2"></input></td></tr>''' % option) # todo: use default here
	html.append('''<tr><td><div style="width:%(tablewidth)dpx">Wall-time limit (mins)</div></td>''' % vars())
	html.append('''<td><input type="text" style="width:75px" maxlength=8 name="BenchmarkWalltimeLimit" value="360"></input></td></tr>''' % option) # todo: use default here
	html.append('''<tr><td><div style="width:%(tablewidth)dpx">Email notification list (comma separated)</div></td>''' % vars())
	html.append('''<td><input type="text" style="width:75px" maxlength=8 name="BenchmarkNotificationEmailAddresses" value=""></input></td></tr>''' % option)
	html.append('''</td></tr>''')
	html.append('''</table>''')
	html.append('''</td></tr>''')
	
	html.append('''<tr><td><INPUT TYPE="Submit" VALUE="Submit" disabled=true></td></tr>''')
	
	if False:
		bm_parameters = {}
		for option in benchmarks[selected_benchmark]['options']:
			if option["Type"] == 'int':
				bm_parameters[options['OptionName']] = int(valueof("Benchmark%sOption%s" %(selected_benchmark, options['OptionName'])))
			else:
				raise Exception("Handle more option datatypes here.")
		result = getBenchmarksConnection().execInnoDBQuery("UPDATE BenchmarkRun SET BenchmarkOptions=%s WHERE ID=1", parameters = (pickle.dumps(bm_parameters),))
			
	
	html.append('''</table>''')
	html.append('''</FORM>''')
	html.append('''</div></center>''')
	return html, []

def generateReportPage():
	html = []
	
	html.append("""<center><div><i>...</i></div></center>""")
	html.append("""<H1 align=left > ... </H1><br>""")
	return html, []

def generateBenchmarksPage(settings_, rosettahtml, form, benchmark_options):

	global settings
	settings = settings_
	
	benchmarkspage = ""
	if form.has_key("BenchmarksPage"):
		benchmarkspage = form["BenchmarksPage"].value
		
	
	# Set generate to False to hide pages for quicker testing
	subpages = [
		{"name" : "submission",	"desc" : "Submit",			"fn" : generateSubmissionPage,	"generate" :True,	"params" : [benchmark_options]},
		{"name" : "report",		"desc" : "View reports",	"fn" : generateReportPage,		"generate" :True,	"params" : []},
		]
	
	# Create menu
	html = []
	html.append("<td align=center>")
	html.append('''<FORM name="benchmarksform" method="post">''')
	
	for subpage in subpages:
		if subpage["generate"]:
			html.append('''<input type="button" value="%(desc)s" onClick="showPage('%(name)s');">''' % subpage)
	
	html.append('''<input type="button" value="Refresh" onClick="document.benchmarksform.query.value='benchmarks'; document.benchmarksform.submit();">''')
	html.append('''<input type="hidden" NAME="BenchmarksPage" VALUE="%s">''' % benchmarkspage)
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
<script src="/backrub/frontend/benchmarks.js" type="text/javascript"></script>
<script src="/javascripts/sorttable.js"></script>''')

	return html