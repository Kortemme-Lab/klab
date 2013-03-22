#!/usr/bin/python2.4
# -*- coding: iso-8859-15 -*-

########################################
# Code for the Gen9 DNA page
########################################

import os, re
import datetime
from datetime import date
from string import join
import time
import pickle
import string
import rosettadb
import calendar
import socket
from rosettahelper import DEVELOPMENT_HOSTS, DEVELOPER_USERNAMES, saturateHexColor, make755Directory, ROSETTAWEB_SK_AAinv
import locale
locale.setlocale(locale.LC_ALL, 'en_US')
import sys
import common
from rosettahelper import ggplotColorWheel

settings = None
script_filename = None
gen9db = None
userid = None

showprofile = False

def generateTestPage(form):
	html = []
	chartfns = []
	
	html.append("<div><select id='motif_selector' name='motif_selector'>")
	html.append("<option value=''>Choose a motif</option>")
	for r in gen9db.execute_select("SELECT * FROM SmallMoleculeMotif ORDER BY SmallMoleculeID, PDBFileID, Name"):
		html.append("<option value='%s'>%(SmallMoleculeID)s, %(PDBFileID)s, %(Name)s</option>" % r)
	html.append('''</select></div>''')
	
	html.append('''<div><span id='motif_interaction_diagrams'></span></div>''')
	html.append('''<div><img src='../images/placeholder.png' style='height:100px' id='motif_interaction_diagram'></img></div>''')
	
	
	
	
	html.append("<div>test div</div>")
	html.append('''
<script type="text/javascript">
	

</script>
<a href="">Link</a>
	
	
	
	
	''')
	
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
	
def generateGen9DNAPage(settings_, rosettahtml, form, userid_):
	global gen9db
	gen9db = rosettadb.ReusableDatabaseInterface(settings_, host = "kortemmelab.ucsf.edu", db = "Gen9Design")
	rosettaweb = rosettadb.ReusableDatabaseInterface(settings_, host = "localhost", db = "rosettaweb")

	global settings
	global protocols
	global script_filename
	global userid
	global username
	settings = settings_
	script_filename = rosettahtml.script_filename 
	userid = userid_
	
	use_security = True # This should always be True except for initial testing
	html = []
	username = None
	has_access = False
	
	if use_security and userid == '':
			html.append('Guests do not have access to this page. Please log in.</tr>')
			return html
	if userid != '':
		results = rosettaweb.execute_select('SELECT UserName FROM Users WHERE ID=%s', parameters= (userid_,))
		if len(results) == 1:
			username = results[0]['UserName']
		if username in ['oconchus', 'oconchus2', 'kortemme', 'rpache', 'kyleb', 'huangy2', 'noah', 'amelie']:
			has_access = True
		else:
			username = None
	if use_security and not has_access:
		html.append('Guests do not have access to this page. Please log in.</tr>')
		return html
	
	# Set generate to False to hide pages for quicker testing
	subpages = []
	
	global showprofile
	subpages.append({"name" : "test",		"desc" : "test",	"fn" : generateTestPage,	"generate" :True,	"params" : [form]})
	
	# Create menu
	
	html.append("<td align=center>")
	html.append('''<FORM name="gen9form" method="post" action="http://albana.ucsf.edu/backrub/cgi-bin/rosettaweb.py">''')
	
	for subpage in subpages:
		if subpage["generate"]:
			html.append('''<input type="button" value="%(desc)s" onClick="showPage('%(name)s');">''' % subpage)
	
	html.append('''<input type="hidden" NAME="Gen9DNAPage" VALUE="">''')
	html.append('''<input type="button" value="Refresh" onClick="document.gen9form.query.value='Gen9DNA'; document.gen9form.submit();">''')
	html.append('''<input type="hidden" NAME="query" VALUE="">''')
	html.append('''<input type="hidden" NAME="Username" VALUE="%s">''' % username)
			
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
	#html.extend(initGoogleCharts(gchartfns))
#<script src="/jmol/Jmol.js" type="text/javascript"></script>
#<script src="/jquery/jquery-1.9.0.min.js" type="text/javascript"></script>
#<script src="/javascripts/sorttable.js" type="text/javascript"></script>
	html.append('''
<script src="/backrub/frontend/gen9dna.js" type="text/javascript"></script>
''')

	gen9db.close()
	rosettaweb.close()
	
	return html