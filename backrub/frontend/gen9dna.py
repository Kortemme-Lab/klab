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
from gen9api.gen9api import Gen9Interface, DesignInformation

settings = None
script_filename = None
gen9db = None
userid = None

showprofile = True

def getSmallMoleculeColors():
	SmallMoleculeIDs = sorted([r['ID'] for r in gen9db.execute("SELECT ID FROM SmallMolecule")])
	spaced_colors = ggplotColorWheel(len(SmallMoleculeIDs), start=15, saturation_adjustment=0.5)
	mol_colors = {}
	for x in range(len(SmallMoleculeIDs)):
		mol_colors[SmallMoleculeIDs[x]] = spaced_colors[x]
	mol_colors['_WT'] = '888'
	return mol_colors

def generateDNATranslator(form):
	html = []
	chartfns = []
	
	html.append("""<div><span>Enter DNA sequence and hit enter</span></div>""")
	html.append("""<div><span><textarea cols=120 rows=8 id='dna_translator' name='dna_translator'></textarea></span></div>""")
	html.append("""<div><span>Protein sequence</span></div>""")
	html.append("""<div><span><textarea cols=120 rows=3 disabled id='dna_translator_results' name='dna_translator_results'></textarea></span></div>""")
			
	return html, chartfns

def generateChildPlatePage(form):
	html = []
	chartfns = []
	
	profile_timer = ProfileTimer()
	
	profile_timer.start('init')
	
	#html.append("<div><select id='motif_selector' name='motif_selector'>")
	#html.append("<option value=''>Choose a motif</option>")
	#for r in gen9db.execute_select("SELECT * FROM SmallMoleculeMotif ORDER BY SmallMoleculeID, PDBFileID, Name"):
	#	html.append("<option value='%s'>%(SmallMoleculeID)s, %(PDBFileID)s, %(Name)s</option>" % r)
	#html.append('''</select></div>''')
	
	#html.append('''<div><span id='motif_interaction_diagrams'></span></div>''')
	#html.append('''<div><img src='../images/placeholder.png' style='height:100px' id='motif_interaction_diagram'></img></div>''')
	#html.append('''<div id='input_structure'></div>''')
	small_molecule_colors = getSmallMoleculeColors()
	lookup_plate_id = 'plate10089'
	
	html.append('''<div style='margin-bottom:10px;'>Click on the *center* of a well location to bring up more information in a pop-up dialog (clicking on the top-right of a well does not work). The DNA sequence for the corresponding design chain is shown in color in the pop-up dialog. If the DNA construct contains another DNA chain, this second chain is greyed out.</div>''')
	
	html.append('''<div>
	<b>View legend</b> 
	<span style='cursor:pointer' onclick='show_gen9well_legend(true);' id='gen9well_legend-show'><img width="11" height="11" src='../images/plusbutton32.png' alt='pdf'></span>
	<span style='cursor:pointer; display:none' onclick='show_gen9well_legend(false);' id='gen9well_legend-hide'><img width="11" height="11" src='../images/minusbutton32.png' alt='pdf'></span>
	<div id='gen9well_legend'></div></div>''')
	
	ListOfSmallMoleculesOnPage = set()
	for PlateChain in [1, 2]:
	
		profile_timer.start('body header')
	
		plate_id = 'Child%d' % PlateChain 
		
		html.append("""<div id="dialog" title="Basic dialog">
  <p>This is the default dialog which is useful for displaying information. The dialog window can be moved, resized and closed with the 'x' icon.</p>
</div>""")
		html.append("<div class='gen9well_container_title'>Child plate %d (Chain%d)</div>" % (PlateChain, PlateChain))
		html.append("<div class='gen9well_container_header'>")
		html.append("<div class='gen9well_container_row'>")
		html.append('''<span style='width:15px' class="gen9well_rowlabel_block"></span>''')
		for x in range(1, 13):
			html.append('''<span class="gen9well_header_block">%02d</span>''' % x)
		html.append("</div>")
		html.append("</div>")
		
		html.append("<div class='gen9well_container'>")
		for y in ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H']:
			html.append("<div id='row_%s_%s' class='gen9well_container_row'>" % (plate_id, y))
			html.append('''<span class="gen9well_rowlabel_block">%s</span>''' % y)
			for x in range(1, 13):
				#%s%02d (y, x)
				html.append('''<span id="%s_%s_%02d_well" class="gen9well_block"><img src='../images/gen9well.png' width='100' alt='%s%02d'></span>''' % (plate_id, y, x, y, x))
			html.append("</div>")
		html.append("</div>")
		
		profile_timer.start('getManualDesignsForDNAPlate')
		ManualDesigns, errors, warnings = gen9Interface.getManualDesignsForDNAPlate(lookup_plate_id)
		
		profile_timer.start('body remainder')
		designs_in_order, wildtype_designs_in_order = DesignInformation.sort(ManualDesigns, 'TargetSmallMoleculeID', 'WellLocation', extra = {'LookupPlateID' : lookup_plate_id, 'SortChain' : 'Chain1'}, separate_wildtype_sequences = True)
		
		for d in designs_in_order + wildtype_designs_in_order:
			ListOfSmallMoleculesOnPage.add(d.TargetSmallMolecule.ID)
		
		for wildtype_design in wildtype_designs_in_order:
			design_index = 0
			wildtype_index = 0
			for y in ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H']:
				for x in range(1, 13):
					if design_index < len(designs_in_order): 
						#designs_in_order[index]
						design = designs_in_order[design_index]
						for chain_info in design.getSummaryInformationForAssembly(lookup_plate_id):
							cloning_type = chain_info['DNAChain'].CloningType
							assert(cloning_type == 'Chain1' or cloning_type == 'Chain2')
							if chain_info['DNAChain'].CloningType == "Chain%d" % PlateChain:
								StorageLocation = chain_info['StorageLocation']
								
								tooltip = []
								tooltip.append("%s, Design #%d" % (design.TargetSmallMolecule.ID, design.ID))
								tooltip.append('Wildtype scaffold: %s.%s' % (design.WildtypeScaffold.PDBFileID, design.WildtypeScaffold.BiologicalUnit))
								tooltip.append("Location of Chain%d in master(%s): %s%02d" % (PlateChain, StorageLocation.DNAPlateID, StorageLocation.PlateRow, StorageLocation.PlateColumn))
								tooltip.append("Master plate BP: %d" % StorageLocation.NumberOfBasePairs)
								tooltip.append("Master plate concentration: %0.2f ng/&#x3BC;l" % StorageLocation.Concentration)
								tooltip.append("Master plate volume: %0.2f &#x3BC;l" % StorageLocation.Volume)
								tooltip.append("Master plate total yield: %0.2f ng" % StorageLocation.TotalYield)
								tooltip = "\n".join(tooltip)
								
								html.append('''<span title='%s' id="%s_%s_%02d_info" style='cursor:pointer; background:#%s; display:none;' class="gen9well_block">''' % (tooltip, plate_id, y, x, small_molecule_colors[design.TargetSmallMolecule.ID]))
								#html.append('''<span class='Gen9DNAWell_%d'>''' % design.ID)
								html.append('''<span class='Gen9DNAWell_%d'>''' % design.ID)
								html.append("%s, #%d<br>" % (design.TargetSmallMolecule.ID, design.ID))
								html.append("BP: %d<br>" % StorageLocation.NumberOfBasePairs)
								html.append("%0.2f ng/&#x3BC;l<br>" % StorageLocation.Concentration)

								html.append("<center><font size='10'><b>%s%02d</b></font></center>" % (StorageLocation.PlateRow, StorageLocation.PlateColumn))
								html.append('''</span>''')
								html.append("</span>")
						design_index += 1
					elif wildtype_index < len(wildtype_designs_in_order):
						design = wildtype_designs_in_order[wildtype_index]
						for chain_info in design.getSummaryInformationForAssembly(lookup_plate_id):
							cloning_type = chain_info['DNAChain'].CloningType
							assert(cloning_type == 'Chain1' or cloning_type == 'Chain2')
							if chain_info['DNAChain'].CloningType == "Chain%d" % PlateChain:
								StorageLocation = chain_info['StorageLocation']
								
								tooltip = []
								tooltip.append('%s.%s, Design #%d' % (design.WildtypeScaffold.PDBFileID, design.WildtypeScaffold.BiologicalUnit, design.ID))
								tooltip.append("Location of Chain%d in master(%s): %s%02d" % (PlateChain, StorageLocation.DNAPlateID, StorageLocation.PlateRow, StorageLocation.PlateColumn))
								tooltip.append("Master plate BP: %d" % StorageLocation.NumberOfBasePairs)
								tooltip.append("Master plate concentration: %0.2f ng/&#x3BC;l" % StorageLocation.Concentration)
								tooltip.append("Master plate volume: %0.2f &#x3BC;l" % StorageLocation.Volume)
								tooltip.append("Master plate total yield: %0.2f ng" % StorageLocation.TotalYield)
								tooltip = "\n".join(tooltip)
								
								html.append('''<span title='%s' id="%s_%s_%02d_info" style='cursor:pointer; background:#%s; display:none;' class="gen9well_block">''' % (tooltip, plate_id, y, x, small_molecule_colors['_WT']))
								html.append('''<span class='Gen9DNAWell_%d'>''' % design.ID)
								html.append("<span style='font-size:80%%'>%s.%s,#%d</span><br>" % (design.WildtypeScaffold.PDBFileID, design.WildtypeScaffold.BiologicalUnit, design.ID))
								html.append("BP: %d<br>" % StorageLocation.NumberOfBasePairs)
								html.append("%0.2f ng/&#x3BC;l<br>" % StorageLocation.Concentration)
								html.append("<center><font size='10'><b>%s%02d</b></font></center>" % (StorageLocation.PlateRow, StorageLocation.PlateColumn))
								html.append('''</span>''')
								html.append("</span>")
						wildtype_index += 1

	profile_timer.start('postamble')
	
	profile_timer.stop()
	if showprofile and username=='oconchus':
		debug_log(username, "** DesignIterator constructor **")
		debug_log(username, profile_timer.getProfile())


	html.append('''<div style='display:none; border:1px solid black; width:100px; margin-top: 3px; margin-left: 20px;' id='gen9well_legend_contents'>''')
	for small_molecule_id, small_mol_color in sorted(small_molecule_colors.iteritems()):
		if small_molecule_id in ListOfSmallMoleculesOnPage or small_molecule_id == '_WT':
			html.append('''<span class='gen9well_legend_text'>%s</span><span style='background:#%s' class='gen9well_legend_box'></span></br>''' % (small_molecule_id.replace("_WT", "Wildtype"), small_mol_color))
	html.append('''</div>''')
	
	
	html.append("<div style='padding-top: 40px;' class='gen9well_container_title'>Manual designs we cannot make</div>")
	html.append("<div class='gen9well_errors'>")
	for e in errors:
		html.append("%s<br>" % e)
	html.append("</div>")
	html.append("<div style='margin-top:10px' class='gen9well_warnings'>")
	for w in warnings:
		html.append("%s<br>" % w)
	html.append("</div>")
	
		
	return html, chartfns


def debug_log(username, msg, br=True, color=None):
	if username == 'oconchus':
		if br:
			print("%s<br>" % msg)
		else:
			print(msg)

class ProfileTimer(object):
	def __init__(self):
		self.stages = []
		self.stage_times = {}
		self.current_stage = None
		self.last_start_time = None
		self.stopped = True
		
	def start(self, stage):
		time_now = time.time()
		self.stopped = False
		
		if stage not in self.stage_times.keys():
			self.stages.append(stage)
		
		if self.current_stage:
			self.stage_times[self.current_stage] = self.stage_times.get(self.current_stage, 0)
			self.stage_times[self.current_stage] += time_now - self.last_start_time
			self.last_start_time = time_now
			self.current_stage = stage
		else:
			self.current_stage = stage
			self.last_start_time = time_now
			self.stage_times[stage] = 0
			
	def stop(self):
		time_now = time.time()
		if self.current_stage:
			self.stage_times[self.current_stage] = self.stage_times.get(self.current_stage, 0)
			self.stage_times[self.current_stage] += time_now - self.last_start_time
			self.last_start_time = None
			self.current_stage = None
		self.stopped = True
	
	def getTotalTime(self):
		if not self.stopped:
			return None
		t = 0
		for stage in self.stages:
			t += self.stage_times[stage]
		return t

	def getProfile(self):
		if not self.stopped:
			return False
		s = ['<b>Total time: %fs</b>' % self.getTotalTime()]
		
		stage_times = sorted([self.stage_times[stage] for stage in self.stages])
		if len(stage_times) < 10:
			top_time_cutoff = stage_times[-2]
		else:
			top_time_cutoff = stage_times[-(len(stage_times) / 5)]
		
		for stage in self.stages:
			if self.stage_times[stage] == stage_times[-1]:
				s.append("<b><font color='#550000'>%s: %fs</font></b>" % (stage, self.stage_times[stage]))
			elif self.stage_times[stage] >= top_time_cutoff:
				s.append("<b><font color='red'>%s: %fs</font></b>" % (stage, self.stage_times[stage]))
			else:
				s.append("%s: %fs" % (stage, self.stage_times[stage]))
		return "<br>".join(s)
	
def generateGenericPage(form):
	html = []
	chartfns = []
	html.append('''<table width="1200px">''')
	html.append('''<tr align="center">''')
	html.append('''<td colspan=2>''')
	
	#if form.has_key("ddgJmolPDB"):
	html.append('''</td>''')
	html.append('''</tr>''')
	html.append('''</table>''')
	return html, chartfns
	
def generateGen9DNAPage(settings_, rosettahtml, form, userid_):
	global gen9db
	global gen9Interface
	gen9Interface = Gen9Interface(username = 'oconchus', password = settings_['SQLPassword'])
	gen9db = gen9Interface.gen9db
	#rosettadb.ReusableDatabaseInterface(settings_, host = "kortemmelab.ucsf.edu", db = "Gen9Design")
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
	global showprofile
	subpages =[
		{"name" : "ChildPlates",		"desc" : "Child plates",	"fn" : generateChildPlatePage,	"generate" :True,	"params" : [form]},
		{"name" : "DNATranslation",		"desc" : "DNA translator",	"fn" : generateDNATranslator,	"generate" :True,	"params" : [form]}
	]
	
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
		html.append('<div style="display:none; " id="%s">' % subpage["name"])
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