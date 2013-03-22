#!/usr/bin/python2.4
# -*- coding: iso-8859-15 -*-

########################################
# Code for the Gen9 page
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
			top_time_cutoff = stage_times[-(len(stage_times)/5)]
		
		for stage in self.stages:
			if self.stage_times[stage] == stage_times[-1]:
				s.append("<b><font color='#550000'>%s: %fs</font></b>" % (stage, self.stage_times[stage]))
			elif self.stage_times[stage] >= top_time_cutoff:
				s.append("<b><font color='red'>%s: %fs</font></b>" % (stage, self.stage_times[stage]))
			else:
				s.append("%s: %fs" % (stage, self.stage_times[stage]))
		return "<br>".join(s)
					 
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

def get_subsequence(sequence, n):
	for i in xrange(0, len(sequence), n):
		yield sequence[i:i + n]

filter_types = ['Scaffold', 'Design']
filter_entities = ['Meeting', 'Tanja', 'Roland', 'Kyle', 'Ming', 'Noah', 'Amelie']
filter_entities_map = {'Tanja' : 'kortemme', 'Roland' : 'rpache', 'Kyle' : 'kyleb', 'Ming' : 'huangy2', 'Noah' : 'noah', 'Amelie' : 'amelie'}
filter_ratings = ['Good', 'Unrated', 'Maybe', 'Bad']
filter_rating_map = {'Good' : 'Yes', 'Maybe' : 'Maybe', 'Bad' : 'No'}

def generateFilterQuery(gen9db, username, form):
	'''Hacky - we should use proper SQL queries here but this was quick to write.'''
	
	allDesignIDs = set([r['ID'] for r in gen9db.execute_select("SELECT ID FROM Design WHERE Design.Type='Design' OR Design.Type='Relaxed design'")]) 
	
	assert(form.has_key('FilterType'))
	if form['FilterType'].value == 'Intersection':
		filteredIDs = allDesignIDs
	elif form['FilterType'].value == 'Union':
		filteredIDs = set()
	
	for rating_entity in filter_entities:
		if rating_entity != 'Meeting':
			rating_entity_id = filter_entities_map[rating_entity]
			# Add unrated IDs
			elem = 'Filter_Design_%(rating_entity)s_Unrated' % vars()
			if form.has_key(elem):
				allEntityRatedDesignIDs = set([r['ID'] for r in gen9db.execute_select("SELECT Design.ID FROM Design INNER JOIN UserDesignRating ON UserDesignRating.DesignID=Design.ID WHERE UserID=%s AND (Design.Type='Design' OR Design.Type='Relaxed design')", parameters=(rating_entity_id,))])
				allEntityUnratedDesignIDs = allDesignIDs.difference(allEntityRatedDesignIDs)
				if form['FilterType'].value == 'Intersection':
					filteredIDs = filteredIDs.intersection(allEntityUnratedDesignIDs)
				else:
					filteredIDs = filteredIDs.union(allEntityUnratedDesignIDs)
				
			allowed_ratings = []
			for rating_value in filter_ratings:
				if rating_value != 'Unrated':
					elem = 'Filter_Design_%(rating_entity)s_%(rating_value)s' % vars()
					if form.has_key(elem):
						allowed_ratings.append(rating_value)
					
			if allowed_ratings:
				disjunction = " OR ".join(["Rating='%s'"% a_rating for a_rating in allowed_ratings])
				UserRatedDesignIDs = set([r['ID'] for r in gen9db.execute_select("SELECT Design.ID FROM Design INNER JOIN UserDesignRating ON UserDesignRating.DesignID=Design.ID WHERE UserID='%s' AND (Design.Type='Design' OR Design.Type='Relaxed design') AND %s" % (rating_entity_id, disjunction))])
				if form['FilterType'].value == 'Intersection':
					filteredIDs = filteredIDs.intersection(UserRatedDesignIDs)
				else:
					filteredIDs = filteredIDs.union(UserRatedDesignIDs)

	for rating_entity in filter_entities:
		if rating_entity != 'Meeting':
			rating_entity_id = filter_entities_map[rating_entity]
			# Add unrated IDs
			elem = 'Filter_Scaffold_%(rating_entity)s_Unrated' % vars()
			if form.has_key(elem):
				allEntityRatedScaffoldIDs = set([r['ID'] for r in gen9db.execute_select("SELECT Design.ID FROM Design INNER JOIN PDBBiologicalUnit ON PDBBiologicalUnit.PDBFileID=WildtypeScaffoldPDBFileID AND PDBBiologicalUnit.BiologicalUnit=WildtypeScaffoldBiologicalUnit INNER JOIN UserScaffoldRating ON UserScaffoldRating.ComplexID=PDBBiologicalUnit.ComplexID WHERE UserID=%s AND (Design.Type='Design' OR Design.Type='Relaxed design')", parameters=(rating_entity_id,))])
				allEntityUnratedScaffoldIDs = allDesignIDs.difference(allEntityRatedScaffoldIDs)
				if form['FilterType'].value == 'Intersection':
					filteredIDs = filteredIDs.intersection(allEntityUnratedScaffoldIDs)
				else:
					filteredIDs = filteredIDs.union(allEntityUnratedScaffoldIDs)
				
			allowed_ratings = []
			for rating_value in filter_ratings:
				if rating_value != 'Unrated':
					elem = 'Filter_Scaffold_%(rating_entity)s_%(rating_value)s' % vars()
					if form.has_key(elem):
						allowed_ratings.append(rating_value)
					
			if allowed_ratings:
				disjunction = " OR ".join(["Rating='%s'"% a_rating for a_rating in allowed_ratings])
				UserRatedScaffoldIDs = set([r['ID'] for r in gen9db.execute_select("SELECT Design.ID FROM Design INNER JOIN PDBBiologicalUnit ON PDBBiologicalUnit.PDBFileID=WildtypeScaffoldPDBFileID AND PDBBiologicalUnit.BiologicalUnit=WildtypeScaffoldBiologicalUnit INNER JOIN UserScaffoldRating ON UserScaffoldRating.ComplexID=PDBBiologicalUnit.ComplexID WHERE UserID='%s' AND (Design.Type='Design' OR Design.Type='Relaxed design') AND %s" % (rating_entity_id, disjunction))])
				if form['FilterType'].value == 'Intersection':
					filteredIDs = filteredIDs.intersection(UserRatedScaffoldIDs)
				else:
					filteredIDs = filteredIDs.union(UserRatedScaffoldIDs)
	
	if form.has_key('FilterMeetingSelection'):
		
		# This gets the list of designs not rated in ANY meeting
		elem = 'Filter_Design_Meeting_Unrated' % vars()
		if form.has_key(elem):
			allMeetingRatedDesignIDs = set([r['ID'] for r in gen9db.execute_select("SELECT Design.ID FROM Design INNER JOIN MeetingDesignRating ON MeetingDesignRating.DesignID=Design.ID WHERE Design.Type='Design' OR Design.Type='Relaxed design'")])
			allMeetingUnratedDesignIDs = allDesignIDs.difference(allMeetingRatedDesignIDs)
			if form['FilterType'].value == 'Intersection':
				filteredIDs = filteredIDs.intersection(allMeetingUnratedDesignIDs)
			else:
				filteredIDs = filteredIDs.union(allMeetingUnratedDesignIDs)
		
		allowed_ratings = []
		for rating_value in filter_ratings:
			if rating_value != 'Unrated':
				elem = 'Filter_Design_Meeting_%(rating_value)s' % vars()
				if form.has_key(elem):
					allowed_ratings.append(rating_value)
					
		if allowed_ratings:
			disjunction = " OR ".join(["Approved='%s'"% filter_rating_map[a_rating] for a_rating in allowed_ratings])
			MeetingRatedDesignIDs = set([r['ID'] for r in gen9db.execute_select("SELECT Design.ID FROM Design INNER JOIN MeetingDesignRating ON MeetingDesignRating.DesignID=Design.ID WHERE DATE(MeetingDate)='%s' AND (Design.Type='Design' OR Design.Type='Relaxed design') AND %s" % (form['FilterMeetingSelection'].value, disjunction))])
			if form['FilterType'].value == 'Intersection':
				filteredIDs = filteredIDs.intersection(MeetingRatedDesignIDs)
			else:
				filteredIDs = filteredIDs.union(MeetingRatedDesignIDs)
				
				
	return filteredIDs
	
def generateHidingCheckboxes():
	html = []
	html.append("<div style='text-align:left'>")
	html.append('''<span class='gen9-hiding-button'><button style="width:155px" type='button' onClick="toggleNewDesigns(this);">Only recent designs</button></span>''')
	html.append('''<span class='gen9-hiding-button'><button style="width:155px" type='button' onClick="toggleManualDesigns(this);">Only manually designed</button></span>''')
	html.append("</div>")
	html.append("<div style='text-align:left'>")
	html.append('''<span class='gen9-hiding-button'><button style="width:155px" type='button' onClick="toggleDesigns('bad', this, 'design');">Hide bad designs</button></span>''')
	html.append('''<span class='gen9-hiding-button'><button style="width:155px" type='button' onClick="toggleDesigns('maybe', this, 'design');">Hide maybe designs</button></span>''')
	html.append('''<span class='gen9-hiding-button'><button style="width:155px" type='button' onClick="toggleDesigns('good', this, 'design');">Hide good designs</button></span>''')
	html.append('''<span class='gen9-hiding-button'><button style="width:155px" type='button' onClick="toggleDesigns('unrated', this, 'design');">Hide unrated designs</button></span>''')
	html.append("</div>")
	html.append("<div style='text-align:left'>")
	html.append('''<span class='gen9-hiding-button'><button style="width:155px" type='button' onClick="toggleDesigns('bad', this, 'scaffold');">Hide bad scaffolds</button></span>''')
	html.append('''<span class='gen9-hiding-button'><button style="width:155px" type='button' onClick="toggleDesigns('maybe', this, 'scaffold');">Hide maybe scaffolds</button></span>''')
	html.append('''<span class='gen9-hiding-button'><button style="width:155px" type='button' onClick="toggleDesigns('good', this, 'scaffold');">Hide good scaffolds</button></span>''')
	html.append('''<span class='gen9-hiding-button'><button style="width:155px" type='button' onClick="toggleDesigns('unrated', this, 'scaffold');">Hide unrated scaffolds</button></span>''')
	html.append("</div>")
	return "\n".join(html)

def generateFilterCheckboxes(username):
	
	
	html = []
	script_html = []
	html.append('''
<div align="left">
<FORM name="gen9filter" method="post" action="http://albana.ucsf.edu/backrub/cgi-bin/rosettaweb.py">
<input type="hidden" NAME="Username" VALUE="%s">
<input type="hidden" NAME="Gen9Page" VALUE="">
<input type="hidden" NAME="query" VALUE="">
<input type="hidden" NAME="gen9sort1" VALUE="">
<input type="hidden" NAME="gen9sort2" VALUE="">
''' % username)
	html.append('''
<button type='button' onClick='showFilters()'>Show filters</button>
<div id="filter_table" style='display:none;'>
<table class="box-table-a">
<thead>
<tr>
<th>Rating</th>
<th COLSPAN="5">By scaffold</th>
<th COLSPAN="5">By design</th>
</tr>
</thead>
<tbody>''')
		
	DatesOfMeetings = [r['MeetingDate'] for r in gen9db.execute_select('SELECT DISTINCT MeetingDate FROM MeetingDesignRating ORDER BY MeetingDate')]
	DatesOfMeetings = ['%d-%02d-%-2d' % (d.year, d.month, d.day) for d in DatesOfMeetings]
	
	rating_entity = 'All'
	html.append('''<tr>''')
	html.append('''<td>%s</td>''' % rating_entity)
	for rating_type in filter_types:
		html.append('''<td>All <input name="Filter_%(rating_type)s_%(rating_entity)s_All" id="Filter_%(rating_type)s_%(rating_entity)s_All" type="checkbox" checked="checked" onClick="Filter%(rating_type)s%(rating_entity)sAllHandler()"></td>''' % vars())
		
		script_html.append('''<script type="text/javascript">//<![CDATA[
function Filter%(rating_type)s%(rating_entity)sAllHandler()
{ 
\tvar toggle = document.getElementById("Filter_%(rating_type)s_%(rating_entity)s_All").checked;
\tvar elem;''' % vars())
		for rating_value in filter_ratings:
			script_html.append('''\telem = document.getElementById("Filter_%(rating_type)s_%(rating_entity)s_%(rating_value)s");
\telem.checked = toggle;
\telem.onclick();''' % vars())
		for rating_subentity in filter_entities:
			script_html.append('''\telem = document.getElementById("Filter_%(rating_type)s_%(rating_subentity)s_All");
\telem.checked = toggle;
\telem.onclick();''' % vars())
		script_html.append('''
}//]]></script>''')
		
		for rating_value in filter_ratings:
			html.append('''<td>%(rating_value)s <input id="Filter_%(rating_type)s_%(rating_entity)s_%(rating_value)s" name="Filter_%(rating_type)s_%(rating_entity)s_%(rating_value)s" type="checkbox" checked="checked" onClick="Filter%(rating_type)s%(rating_entity)s%(rating_value)sHandler()"></td>''' % vars())
			script_html.append('''<script type="text/javascript">//<![CDATA[
function Filter%(rating_type)s%(rating_entity)s%(rating_value)sHandler()
{ 
\tvar toggle = document.getElementById("Filter_%(rating_type)s_%(rating_entity)s_%(rating_value)s").checked;
''' % vars())
			for rating_subentity in filter_entities:
				script_html.append('''\tdocument.getElementById("Filter_%(rating_type)s_%(rating_subentity)s_%(rating_value)s").checked = toggle;
''' % vars())
			script_html.append('''
}//]]></script>''')
			
			
	html.append('''</tr>''')

	for rating_entity in filter_entities:
		html.append('''<tr>''')
		html.append('''<td>%s</td>''' % rating_entity)
		for rating_type in filter_types:
			html.append('''<td>All <input id="Filter_%(rating_type)s_%(rating_entity)s_All" name="Filter_%(rating_type)s_%(rating_entity)s_All" type="checkbox" checked="checked" onClick="Filter%(rating_type)s%(rating_entity)sAllHandler()"></td>''' % vars())
			script_html.append('''<script type="text/javascript">//<![CDATA[
function Filter%(rating_type)s%(rating_entity)sAllHandler()
{ 
\tvar toggle = document.getElementById("Filter_%(rating_type)s_%(rating_entity)s_All").checked;
''' % vars())
			for rating_value in filter_ratings:
				script_html.append('''\tdocument.getElementById("Filter_%(rating_type)s_%(rating_entity)s_%(rating_value)s").checked = toggle;
''' % vars())
			script_html.append('''
}//]]></script>''')
			for rating_value in filter_ratings:
				html.append('''<td>%(rating_value)s <input id="Filter_%(rating_type)s_%(rating_entity)s_%(rating_value)s" name="Filter_%(rating_type)s_%(rating_entity)s_%(rating_value)s" type="checkbox" checked="checked"></td>''' % vars())
		html.append('''</tr>''')
	
	html.append('''<tr><td>Meeting date</td><td><select id='FilterMeetingSelection' name='FilterMeetingSelection'>''')
	html.append("".join(["<option value='%s'>%s</option>" % (meeting, meeting) for meeting in DatesOfMeetings]))
	html.append('''</select></td></tr>''')
	
	html.append('''<tr><td>Filter type</td><td><select id='FilterType' name='FilterType'>''')
	html.append("<option value='Union' selected='selected'>OR (Union)</option>")
	html.append("<option value='Intersection'>AND (Intersection)</option>")
	html.append('''</select></td></tr>''')
			
	
	html.append('''
</tbody>
</table>
<button type="submit" onClick='copyPageFormValues(this); this.form.query.value = "Gen9Filter";'>Apply filters</button>''')
	remove_JS = ""
	for ft in filter_types:
		remove_JS += "var elem = document.getElementById('Filter_%(ft)s_All_All'); elem.checked = true; elem.onclick();" % vars()
	html.append('''		
<button type="button" onclick="%(remove_JS)s">Remove filters</button>
</div>
</FORM>
</div><br>''' % vars())
	return "%s%s" % ("\n".join(html), "\n".join(script_html))

def debug_log(username, msg, br = True, color = None):
	if username == 'oconchus':
		if br:
			print("%s<br>" % msg)
		else:
			print(msg)


class DesignIterator(object):
	'''This class does a slurp of data from the database and stores it. HTML for individual designs can then be extracted from it.''' 
	
	def __init__(self, filtered_DesignIDs = None):
		self.html = []
		self._initialize_css_members()
		self._initialize_data()
		self.filtered_DesignIDs = filtered_DesignIDs
	
	def _initialize_css_members(self):
		#self.darker_blue = '#b2cecf'
		#self.lighter_blue = '#e3eae9'
		#self.alt_lighter_blue = '#d3dad9'
		
		self.bad_design_red = '#d0101d'
		self.bad_scaffold_red = '#c0101d'
		self.maybe_design_orange = '#e8c800'
		self.maybe_scaffold_orange = '#e0c000'
		#self.good_design_green  = '#50f07d'
		#self.good_scaffold_green  = '#40e06d'
		#self.wildtype_mutation_green  = '#50d07d'
		#self.title_bold_text = '#5225d0'
		#self.YesNoMap = {0: 'No', 1: 'Yes'}
		self.meeting_rating_css_classes = {
			'No'		: 'bad_design',
			'Yes'		: 'good_design',
			'Maybe'		: 'maybe_design',
		}
		self.meeting_scaffold_rating_css_classes = {
			'No'		: 'bad_scaffold',
			'Yes'		: 'good_scaffold',
			'Maybe'		: 'maybe_scaffold',
		}
		
		# group_colors
		dbusers = ['Shane', 'Tanja', 'Roland', 'Kyle', 'Ming', 'Noah', 'Amelie', 'Meeting']
		spaced_colors = ggplotColorWheel(len(dbusers), start = 15, saturation_adjustment = 0.5)
		group_colors = {}
		for x in range(len(dbusers)):
			group_colors[dbusers[x]] = spaced_colors[x]
		group_colors['TerminiOkay?'] = '#999'
		self.group_colors = group_colors
		
	def _initialize_data(self):
		profile_timer = ProfileTimer()
				
		self.ScoreComponentsOrder = [
			'tot_pstat_pm',
			'SR_LIGAND_total_score',
			'SR_LIGAND_fa_rep',
			'SR_LIGAND_all_cst',
			'SR_LIGAND_total_dsasa',
			'SR_LIGAND_dsasa_diff',
			'SR_LIGAND_hbond_pm',
			'SR_LIGAND_burunsat_pm',
			'nlr_totrms',
		]
		self.manual_design_score_components_of_interest = [  
			'fa_dun',
			'fa_atr',
			'fa_rep',
			'fa_sol',
			'p_aa_pp',
			'hbond_sr_bb',
			'hbond_lr_bb',
			'hbond_bb_sc',
			'hbond_sc',
			'hack_elec',
			'rama',
			'total',
		]
		self.residue_stats_headers = ['RSNL_', 'RSWL_', 'RANL_']

		# motif_residues
		profile_timer.start('motif_residues')
		motif_residues = {}
		results = gen9db.execute_select("SELECT * FROM SmallMoleculeMotifResidue ORDER BY ResidueID")
		for r in results:
			motif_residues[r["SmallMoleculeMotifID"]] = motif_residues.get(r["SmallMoleculeMotifID"], [r['PDBFileID'], []])
			motif_residues[r["SmallMoleculeMotifID"]][1].append("%(WildTypeAA)s%(ResidueID)s" % r)
		self.motif_residues = motif_residues
		
		# best_ranked
		profile_timer.start('best_ranked')
		best_ranked = {}
		results = gen9db.execute_select("SELECT * FROM RankedScore WHERE MarkedAsBest=1")
		for r in results:
			best_ranked[r['DesignID']] = best_ranked.get(r['DesignID'], [])
			best_ranked[r['DesignID']].append(r)
		self.best_ranked = best_ranked
		
		# HasSequenceLogo
		profile_timer.start('HasSequenceLogo')
		HasSequenceLogo = {}	
		results = gen9db.execute_select("SELECT DesignID, Chain FROM DesignMutatedChain WHERE SequenceLogo IS NOT NULL")
		for r in results:
			HasSequenceLogo[r['DesignID']] = HasSequenceLogo.get(r['DesignID'], set())
			HasSequenceLogo[r['DesignID']].add(r['Chain'])
		self.HasSequenceLogo = HasSequenceLogo
		
		# ScaffoldHasSequenceLogo
		profile_timer.start('ScaffoldHasSequenceLogo')
		ScaffoldHasSequenceLogo = {}	
		results = gen9db.execute_select("SELECT * FROM  PDBBiologicalUnitChain WHERE SequenceLogo IS NOT NULL")
		for r in results:
			sckey = '%s.%s' % (r['PDBFileID'], r['BiologicalUnit'])
			ScaffoldHasSequenceLogo[sckey] = ScaffoldHasSequenceLogo.get(sckey, set())
			ScaffoldHasSequenceLogo[sckey].add(r['Chain'])
		self.ScaffoldHasSequenceLogo = ScaffoldHasSequenceLogo
		
		# DesignMatchtypes
		profile_timer.start('DesignMatchtypes')
		DesignMatchtypes = {}
		results = gen9db.execute_select('SELECT DesignID, WildtypeScaffoldChain, Matchtype FROM DesignSequenceMatch')
		for r in results:
			DesignMatchtypes[r['DesignID']] = DesignMatchtypes.get(r['DesignID'], {})
			DesignMatchtypes[r['DesignID']][r['WildtypeScaffoldChain']] = r['Matchtype']
		self.DesignMatchtypes = DesignMatchtypes
		
		# AllWildtypeSequences
		profile_timer.start('AllWildtypeSequences')
		AllWildtypeSequences = {}
		results = gen9db.execute_select('''
	SELECT PDBBiologicalUnitChain.PDBFileID, PDBBiologicalUnitChain.BiologicalUnit, PDBBiologicalUnitChain.Chain AS Chain, ProteinChain.Sequence AS Sequence 
	FROM PDBBiologicalUnitChain 
	INNER JOIN PDBChain ON PDBBiologicalUnitChain.PDBFileID=PDBChain.PDBFileID AND PDBBiologicalUnitChain.Chain=PDBChain.Chain 
	INNER JOIN ProteinChain ON PDBChain.ProteinChainID=ProteinChain.ID''')
		for r in results:
			wkey = '%s-%s' % (r['PDBFileID'], r['BiologicalUnit'])
			AllWildtypeSequences[wkey] = AllWildtypeSequences.get(wkey, [])
			AllWildtypeSequences[wkey].append(r)
		self.AllWildtypeSequences = AllWildtypeSequences
		
		# AllEffectiveWildtypeSequences
		profile_timer.start('AllEffectiveWildtypeSequences')
		AllEffectiveWildtypeSequences = {}
		results = gen9db.execute_select('''
	SELECT PDBBiologicalUnitChain.PDBFileID, PDBBiologicalUnitChain.BiologicalUnit, PDBBiologicalUnitChain.Chain AS Chain, ProteinChain.Sequence AS Sequence 
	FROM PDBBiologicalUnitChain 
	INNER JOIN PDBChain ON PDBBiologicalUnitChain.PDBFileID=PDBChain.PDBFileID AND PDBBiologicalUnitChain.Chain=PDBChain.Chain 
	INNER JOIN ProteinChain ON PDBChain.EffectiveProteinChainID=ProteinChain.ID''')
		for r in results:
			wkey = '%s-%s' % (r['PDBFileID'], r['BiologicalUnit'])
			AllEffectiveWildtypeSequences[wkey] = AllEffectiveWildtypeSequences.get(wkey, [])
			AllEffectiveWildtypeSequences[wkey].append(r)
		self.AllEffectiveWildtypeSequences = AllEffectiveWildtypeSequences
		
		# rank_components
		profile_timer.start('rank_components')
		rank_components = {}
		results = gen9db.execute_select("SELECT DISTINCT RankingSchemeID, Component FROM RankedScoreComponent")
		for r in results:
			rank_components[r['RankingSchemeID']] = rank_components.get(r['RankingSchemeID'], [])
			rank_components[r['RankingSchemeID']].append(r['Component'])
		for rank_scheme in rank_components.keys():
			rank_components[rank_scheme] = sorted(rank_components[rank_scheme])
		self.rank_components = rank_components
		
		# rank_component_scores
		profile_timer.start('rank_component_scores')
		rank_component_scores = {}
		results = gen9db.execute_select("SELECT * FROM RankedScoreComponent ORDER BY Component")
		for r in results:
			rank_component_scores[r['DesignID']] = rank_component_scores.get(r['DesignID'], {})
			rank_component_scores[r['DesignID']][r['RankingSchemeID']] = rank_component_scores[r['DesignID']].get(r['RankingSchemeID'], {})
			rank_component_scores[r['DesignID']][r['RankingSchemeID']][r['Component']] = (r['CumulativeProbability'], r['IncludedInScheme'])
		self.rank_component_scores = rank_component_scores
		
		# chain_molecule_info
		profile_timer.start('chain_molecule_info')
		chain_molecule_info = {}
		results = gen9db.execute_select('SELECT PDBMolecule.PDBFileID, PDBMoleculeChain.Chain, PDBMolecule.Name, PDBMolecule.Synonym FROM PDBMoleculeChain INNER JOIN PDBMolecule ON PDBMoleculeChain.PDBFileID=PDBMolecule.PDBFileID AND PDBMoleculeChain.MoleculeID=PDBMolecule.MoleculeID')
		for r in results:
			chain_molecule_info[r['PDBFileID']] = chain_molecule_info.get(r['PDBFileID'], {})
			chain_molecule_info[r['PDBFileID']][r['Chain']] = '<span title="%s">%s</span>' % (r['Synonym'], r['Name'])
		self.chain_molecule_info = chain_molecule_info
		
		# meeting_comments
		profile_timer.start('meeting_comments')
		meeting_comments = {}
		results = gen9db.execute_select('SELECT * FROM MeetingDesignRating ORDER BY CommentDate')
		for r in results:
			meeting_comments[r['DesignID']] = meeting_comments.get(r['DesignID'], [])
			meeting_comments[r['DesignID']].append(r)
		self.meeting_comments = meeting_comments
		
		# MeetingDesignRatings
		profile_timer.start('MeetingDesignRatings')
		MeetingDesignRatings = {}
		results = gen9db.execute_select("""
	SELECT MeetingDesignRating.*
	FROM MeetingDesignRating 
	INNER JOIN (
	SELECT MeetingDate, DesignID, MAX(CommentDate) AS MaxDate
	FROM MeetingDesignRating GROUP BY MeetingDate, DesignID) mdr
	ON mdr.MeetingDate=MeetingDesignRating.MeetingDate AND mdr.DesignID=MeetingDesignRating.DesignID AND mdr.MaxDate=MeetingDesignRating.CommentDate
	""")
		for r in results:
			key = r['DesignID']
			MeetingDesignRatings[key] = MeetingDesignRatings.get(key, {})
			MeetingDesignRatings[key][r['MeetingDate']] = r
		self.MeetingDesignRatings = MeetingDesignRatings
		
		# MeetingScaffoldRatings
		profile_timer.start('MeetingScaffoldRatings')
		MeetingScaffoldRatings = {}
		results = gen9db.execute_select("""
	SELECT MeetingScaffoldRating.*
	FROM MeetingScaffoldRating 
	INNER JOIN (
	SELECT MeetingDate, ComplexID, MAX(CommentDate) AS MaxDate
	FROM MeetingScaffoldRating GROUP BY MeetingDate, ComplexID) mdr
	ON mdr.MeetingDate=MeetingScaffoldRating.MeetingDate AND mdr.ComplexID=MeetingScaffoldRating.ComplexID AND mdr.MaxDate=MeetingScaffoldRating.CommentDate
	""")
		for r in results:
			key = r['ComplexID']
			MeetingScaffoldRatings[key] = MeetingScaffoldRatings.get(key, {})
			MeetingScaffoldRatings[key][r['MeetingDate']] = r
		self.MeetingScaffoldRatings = MeetingScaffoldRatings
		
		# UserScaffoldRatings, UserScaffoldTerminiOkay
		profile_timer.start('UserScaffoldRatings')
		UserScaffoldRatings = {}
		UserScaffoldTerminiOkay = {}
		#results = gen9db.execute_select("SELECT UserScaffoldRating.*, User.FirstName FROM UserScaffoldRating INNER JOIN User ON UserID=User.ID")
		results = gen9db.execute_select("""
	SELECT FirstName, UserScaffoldRating.*
	FROM UserScaffoldRating 
	INNER JOIN (
	SELECT UserID, ComplexID, MAX(Date) AS MaxDate
	FROM UserScaffoldRating GROUP BY UserID, ComplexID) udr
	ON udr.UserID=UserScaffoldRating.UserID AND udr.ComplexID=UserScaffoldRating.ComplexID AND udr.MaxDate=UserScaffoldRating.Date
	INNER JOIN User ON UserScaffoldRating.UserID=User.ID""")
		for r in results:
			key = r['ComplexID']
			UserScaffoldRatings[key] = UserScaffoldRatings.get(key, {})
			UserScaffoldRatings[key][r['UserID']] = r
			if r['TerminiAreOkay']:
				UserScaffoldTerminiOkay[key] = r['TerminiAreOkay']
		self.UserScaffoldRatings = UserScaffoldRatings
		self.UserScaffoldTerminiOkay = UserScaffoldTerminiOkay
		
		# ScaffoldReferences
		profile_timer.start('ScaffoldReferences')
		ScaffoldReferences = {} 
		results = gen9db.execute_select("""SELECT * FROM ScaffoldReference INNER JOIN Publication ON PublicationID = Publication.ID ORDER BY PublicationDate""")
		for r in results:
			key = r['ComplexID']
			ScaffoldReferences[key] = ScaffoldReferences.get(key, [])
			ScaffoldReferences[key].append(r)
		self.ScaffoldReferences = ScaffoldReferences
		
		# SmallMoleculeReferences
		profile_timer.start('SmallMoleculeReferences')
		SmallMoleculeReferences = {} 
		results = gen9db.execute_select("""SELECT * FROM SmallMoleculeReference INNER JOIN Publication ON PublicationID = Publication.ID ORDER BY PublicationDate""")
		for r in results:
			key = r['SmallMoleculeID']
			SmallMoleculeReferences[key] = SmallMoleculeReferences.get(key, [])
			SmallMoleculeReferences[key].append(r)
		self.SmallMoleculeReferences = SmallMoleculeReferences
		
		# ReferenceAuthors
		profile_timer.start('ReferenceAuthors')
		ReferenceAuthors = {} 
		results = gen9db.execute_select("""SELECT * FROM PublicationAuthor ORDER BY PublicationID, AuthorOrder""")
		for r in results:
			key = r['PublicationID']
			ReferenceAuthors[key] = ReferenceAuthors.get(key, [])
			ReferenceAuthors[key].append(r)
		self.ReferenceAuthors = ReferenceAuthors
		
		# RosettaScoreComponents
		profile_timer.start('RosettaScoreComponents')
		RosettaScoreComponents = {}
		results = gen9db.execute_select("""SELECT * FROM RosettaScoreComponent""")
		for r in results:
			RosettaScoreComponents[r['ComponentName']] = r['Description']
		self.RosettaScoreComponents = RosettaScoreComponents
		
		profile_timer.start('UserDesignRatings')
		UserDesignRatings = {}
		results = gen9db.execute_select("""
SELECT FirstName, UserDesignRating.*
FROM UserDesignRating 
INNER JOIN (
SELECT UserID,DesignID,MAX(Date) AS MaxDate
FROM UserDesignRating GROUP BY UserID, DesignID) udr
ON udr.UserID=UserDesignRating.UserID AND udr.DesignID=UserDesignRating.DesignID AND udr.MaxDate=UserDesignRating.Date
INNER JOIN User ON UserDesignRating.UserID=User.ID
ORDER BY DesignID, FirstName""")
		for r in results:
			dID = r['DesignID']
			UserDesignRatings[dID] = UserDesignRatings.get(dID, [])
			UserDesignRatings[dID].append(r)
		self.UserDesignRatings = UserDesignRatings
		
		# Manual design filepaths
		profile_timer.start('ManualDesignsFilePaths')
		ManualDesignsFilePaths = {}
		results = gen9db.execute_select("""SELECT ID, FilePath FROM Design WHERE Type="Manual" """)
		for r in results:
			ManualDesignsFilePaths[r['ID']] = r['FilePath']
		
		# ManualDesigns
		profile_timer.start('AllManualDesignsPerDesign')
		AllManualDesignsPerDesign = {}
		ManualDesignsPerDesign = {}
		results = gen9db.execute_select("""SELECT ManualDesign.DesignID AS ManualDesignID, ManualDesign.* FROM ManualDesign ORDER BY DesignID""")
		for r in results:
			dID = r['OriginalDesignID']
			AllManualDesignsPerDesign[dID] = AllManualDesignsPerDesign.get(dID, [])
			AllManualDesignsPerDesign[dID].append(r)
			if r['MutationDescription'].lower() != 'original design' and r['MutationDescription'] != 'AUTO Wildtype Sequence':
				r['FilePath'] = ManualDesignsFilePaths[r['ManualDesignID']]
				ManualDesignsPerDesign[dID] = ManualDesignsPerDesign.get(dID, [])
				ManualDesignsPerDesign[dID].append(r)
		self.ManualDesignsPerDesign = ManualDesignsPerDesign
		self.AllManualDesignsPerDesign = AllManualDesignsPerDesign
		
		# ScoreComponents
		profile_timer.start('ScoreComponents')
		ScoreComponents = {}
		results = gen9db.execute_select('SELECT * FROM ScoreComponent ORDER BY DesignID, Component')
		for r in results:
			dID = r['DesignID']
			ScoreComponents[dID] = ScoreComponents.get(dID, {})
			ScoreComponents[dID][r['Component']] = r['RawScore']
		self.ScoreComponents = ScoreComponents

		# ManualDesignToDesignMapping
		profile_timer.start('ManualDesignToDesignMapping')
		ManualDesignToDesignMapping = {}
		results = gen9db.execute_select("""SELECT DesignID AS ManualDesignID, OriginalDesignID FROM ManualDesign""")
		for r in results:
			ManualDesignToDesignMapping[r['ManualDesignID']] = r['OriginalDesignID']
		self.ManualDesignToDesignMapping = ManualDesignToDesignMapping
		
		
		# design_residue_data 
		profile_timer.start('design_residue_data_SELECT_1')
		design_residue_data = {}
		results = gen9db.execute_select('''SELECT 
			DesignID, Chain, OriginalAA, ResidueID, VariantAA, IsMotifResidue, IsMutation, PositionWithinChain,
			fa_dun, fa_atr,	fa_rep,	fa_sol,	p_aa_pp, hbond_sr_bb, hbond_lr_bb, hbond_bb_sc, hbond_sc, hack_elec, rama, total,
			RANL_SignificantChiChange, RANL_Chi1Delta, RANL_Chi2Delta, RANL_AllSideChainHeavyAtomsRMSD,
			RSNL_SignificantChiChange, RSNL_Chi1Delta, RSNL_Chi2Delta, RSNL_AllSideChainHeavyAtomsRMSD,
			RSWL_SignificantChiChange, RSWL_Chi1Delta, RSWL_Chi2Delta, RSWL_AllSideChainHeavyAtomsRMSD
			FROM DesignResidue ORDER BY DesignID, Chain, ResidueID''')
		
		profile_timer.start('design_residue_data_LOOP')
		for r in results:
			design_residue_data[r['DesignID']] = design_residue_data.get(r['DesignID'], {})
			design_residue_data[r['DesignID']][r['Chain']] = design_residue_data[r['DesignID']].get(r['Chain'], {})
			design_residue_data[r['DesignID']][r['Chain']][r['ResidueID']] = r
		self.design_residue_data = design_residue_data
		
		# MutantSequences
		profile_timer.start('MutantSequences')
		MutantSequences = {}
		results = gen9db.execute_select('SELECT DesignID, Chain, ProteinChain.Sequence, WildTypeChain, FirstResidueID FROM DesignMutatedChain INNER JOIN ComplexChain ON DesignMutatedChain.ATOMComplexChainID=ComplexChain.ID INNER JOIN ProteinChain ON ComplexChain.ProteinChainID=ProteinChain.ID')
		for r in results:
			dID = r['DesignID']
			MutantSequences[dID] = MutantSequences.get(dID, {})
			MutantSequences[dID][r['Chain']] = MutantSequences[dID].get(r['Chain'], {})
			MutantSequences[dID][r['Chain']] = r
		self.MutantSequences = MutantSequences

		profile_timer.stop()
		if showprofile:
			debug_log(username, "** DesignIterator constructor **")
			debug_log(username, profile_timer.getProfile())


	def get_Design_HTML(self, design, profile_timer):
		'''design should be the result of a database query having:
		   - all fields in Design;
		   - PDBBiologicalUnit.ComplexID;
		   - SmallMolecule.Name AS SmallMoleculeName;
		   - SmallMolecule.ID AS SmallMoleculeID;
		   - SmallMoleculeMotif.Name AS TargetMotifName.'''
		
		profile_timer.start('Design preamble')
		
		html = []
		DesignID = design['DesignID']
		if (self.filtered_DesignIDs != None) and (DesignID not in self.filtered_DesignIDs):
			return html
		
		motif_residues = self.motif_residues
		best_ranked = self.best_ranked
		HasSequenceLogo = self.HasSequenceLogo
		ScaffoldHasSequenceLogo = self.ScaffoldHasSequenceLogo
		DesignMatchtypes = self.DesignMatchtypes
		AllWildtypeSequences = self.AllWildtypeSequences
		AllEffectiveWildtypeSequences = self.AllEffectiveWildtypeSequences
		rank_components = self.rank_components
		rank_component_scores =self.rank_component_scores
		chain_molecule_info = self.chain_molecule_info
		design_residue_data = self.design_residue_data
		
		DesignChains = sorted(design_residue_data.get(DesignID).keys())

		DesignsMutations = {}
		for ChainID in DesignChains:
			DesignsMutations[ChainID] = []
			for residueID, residue_details in sorted(design_residue_data[DesignID][ChainID].iteritems()):
				if residue_details['IsMutation'] == 1:
					DesignsMutations[ChainID].append((residue_details['OriginalAA'], residue_details['ResidueID'], residue_details['VariantAA']))
		
		DesignsMotifResidues = {}
		for ChainID in DesignChains:
			DesignsMotifResidues[ChainID] = []
			for residueID, residue_details in sorted(design_residue_data[DesignID][ChainID].iteritems()):
				if residue_details['IsMotifResidue'] == 1:
					DesignsMotifResidues[ChainID].append((residue_details['VariantAA'], residue_details['ResidueID'], residue_details['PositionWithinChain']))
		
		meeting_comments = self.meeting_comments
		MeetingDesignRatings = self.MeetingDesignRatings
		MeetingScaffoldRatings = self.MeetingScaffoldRatings
		UserScaffoldRatings = self.UserScaffoldRatings
		UserScaffoldTerminiOkay = self.UserScaffoldTerminiOkay
		ScaffoldReferences = self.ScaffoldReferences
		SmallMoleculeReferences = self.SmallMoleculeReferences
		ReferenceAuthors = self.ReferenceAuthors
		residue_stats_headers = self.residue_stats_headers
		group_colors = self.group_colors 
		ManualDesignsPerDesign = self.ManualDesignsPerDesign
		AllManualDesignsPerDesign = self.AllManualDesignsPerDesign
		manual_design_score_components_of_interest = self.manual_design_score_components_of_interest
		ScoreComponentsOrder = self.ScoreComponentsOrder
		
		pdbID = design['WildtypeScaffoldPDBFileID']
		ComplexID = design['ComplexID']
		best_ranked_for_this_design = best_ranked.get(design['DesignID'], [])
		
		UserDesignRatings = self.UserDesignRatings.get(DesignID, [])
		ScoreComponents = self.ScoreComponents
		MutantSequences = self.MutantSequences

		profile_timer.start('Determine rating')
		
		# Determine main row color based on ratings
		design_tr_class = 'unrated_design'
		scaffold_tr_class = 'unrated_scaffold'
		
		meeting_approval = None
		if MeetingDesignRatings.get(DesignID):
			# Latest meeting rating trumps all
			meeting_approval = MeetingDesignRatings[DesignID][sorted(MeetingDesignRatings[DesignID].keys(), reverse = True)[0]]['Approved']
		
		if meeting_approval:
			design_tr_class = self.meeting_rating_css_classes[meeting_approval] 
		else:
			num_bad_ratings = 0
			num_good_ratings = 0
			num_maybe_ratings = 0
			for r in UserDesignRatings:
				if r['Rating'] == 'Bad':
					num_bad_ratings += 1
				elif r['Rating'] == 'Good':
					num_good_ratings += 1
				elif r['Rating'] == 'Maybe':
					num_maybe_ratings += 1
			if num_bad_ratings:
				if num_good_ratings or num_maybe_ratings:
					# Mixed reviews
					design_tr_class = 'maybe_design'
				else:
					design_tr_class = 'bad_design'
			elif num_maybe_ratings:
				design_tr_class = 'maybe_design'
			elif num_good_ratings:
				design_tr_class = 'good_design'

		# Determine scaffold color based on ratings
		meeting_approval = None
		if MeetingScaffoldRatings.get(ComplexID):
			# Latest meeting rating trumps all
			meeting_approval = MeetingScaffoldRatings[ComplexID][sorted(MeetingScaffoldRatings[ComplexID].keys(), reverse = True)[0]]['Approved']
		if meeting_approval:
			scaffold_tr_class = self.meeting_scaffold_rating_css_classes[meeting_approval] 
		else:
			num_bad_ratings = 0
			num_good_ratings = 0
			num_maybe_ratings = 0
			
			if UserScaffoldRatings.get(design['ComplexID']):
				for user_id, scaffold_rating in UserScaffoldRatings[design['ComplexID']].iteritems():
					if scaffold_rating['Rating'] == 'Bad':
						num_bad_ratings += 1
					elif scaffold_rating['Rating'] == 'Good':
						num_good_ratings += 1
					elif scaffold_rating['Rating'] == 'Maybe':
						num_maybe_ratings += 1
					
			
			if num_bad_ratings:
				if num_good_ratings or num_maybe_ratings:
					# Mixed reviews
					scaffold_tr_class = 'maybe_scaffold'
				else:
					scaffold_tr_class = 'bad_scaffold'
			elif num_maybe_ratings:
				scaffold_tr_class = 'maybe_scaffold'
			elif num_good_ratings:
				scaffold_tr_class = 'good_scaffold'
		
			
		# ROW 1
			
		# Create an anchor to the row
		
		#html.append("<th style='width:50px;'>Type</th><th style='width:50px;'>File</th><th style='width:80px;'>Target/template</th><th style='width:50px;'>Scaffold</th><th style='width:250px;'>List of best designs resp. best relaxed designs (enzdes weights)</th><th style='width:50px;'>Comments</th>")
		#
		
		profile_timer.start('Design Header')
		
		extra_class = ""
		has_manual_designs = ManualDesignsPerDesign.get(DesignID)
		if not has_manual_designs:
			extra_class = " no-manual-designs "
			
		html.append('''<div id='d%d' class='%s-cl %s-cl %s general-design-cl'>''' % (design['DesignID'], design_tr_class, scaffold_tr_class, extra_class))
		html.append('''<div class='new-genbrowser-row %s'>''' % design_tr_class)
		html.append('''<span class='new-genbrowser-header'>%(Type)s</span><span><a class='gen9' href='#d%(DesignID)d'>#%(DesignID)d</a>''' % design)
		if design['PyMOLSessionFile']:
			html.append('''<span class='Gen9PyMOL-link'><a href='?query=Gen9File&amp;DesignID=%(DesignID)d&amp;download=PSE'><img width="18" height="18" src='../images/pse32o.png' alt='pdf'></a></span>''' % design)
		if design['Description']:
			html.append('''<span style='margin-left:20px;'>(%(Description)s)</span>''' % design)
		html.append('</span></div>\n')

		html.append('''<div class='new-genbrowser-row %s'>''' % scaffold_tr_class)
		
		html.append('''<span class='new-genbrowser-header'>Wildtype scaffold</span><span style='display: inline-block; width: 50px;'>#%(ComplexID)d</span>'''  % design)
		if len(pdbID) == 4:
			html.append('''<span>(<a class='gen9' target='_new' href='http://www.rcsb.org/pdb/explore.do?structureId=%(WildtypeScaffoldPDBFileID)s'>%(WildtypeScaffoldPDBFileID)s</a>, %(WildtypeScaffoldBiologicalUnit)s)</span>'''  % design)
			#html.append('''<div class='new-genbrowser-row'><span class='new-genbrowser-header'>Scaffold</span><span><a class='newgen9' href='http://www.rcsb.org/pdb/explore.do?structureId=%(WildtypeScaffoldPDBFileID)s'>%(WildtypeScaffoldPDBFileID)s</a>, %(WildtypeScaffoldBiologicalUnit)s</span></div>\n''' % design)
		else:
			html.append('''<span>(%(WildtypeScaffoldPDBFileID)s, %(WildtypeScaffoldBiologicalUnit)s)</span>'''  % design)
		
		sckey = '%s.%s' % (design['WildtypeScaffoldPDBFileID'], design['WildtypeScaffoldBiologicalUnit'])	
		if ScaffoldHasSequenceLogo.get(sckey):
			for chainID in sorted(ScaffoldHasSequenceLogo[sckey]):
				html.append('''<span style='display:inline-block; margin-left:20px;'>Chain %s''' % chainID)
				html.append('''<a class='gen9' target="_new" href='?query=Gen9File&amp;ScaffoldPDBID=%s&amp;ScaffoldUnit=%s&amp;download=WebLogo&amp;Chain=%s'> <img width="42" height="18" src='../images/weblogo.png' alt='WebLogo'></a>''' % (design['WildtypeScaffoldPDBFileID'], design['WildtypeScaffoldBiologicalUnit'], chainID))
		html.append('''</div>\n''')

		html.append('''<div class='new-genbrowser-row'><span class='new-genbrowser-header'>Mutant complex</span><span>#%(ATOMComplexID)d</span></div>\n''' % design)
		
		html.append('''<div class='new-genbrowser-row'><span class='new-genbrowser-header'>Design PDB.gz</span><span><a class='newgen9' href='?query=Gen9File&amp;DesignID=%(DesignID)d&amp;download=PDB'>Download</a></span></div>\n'''  % design)
		
		for mx in range(len(ManualDesignsPerDesign.get(DesignID, []))):
			manual_design = ManualDesignsPerDesign[DesignID][mx]
			ManualDesignID = manual_design['ManualDesignID'] 
			html.append('''<div class='new-genbrowser-row' id='manuald%(ManualDesignID)d'>''' % manual_design)
			if mx == 0:
				html.append('''<span class='new-genbrowser-header'>Manual designs''')
				if design['ManualDesignsPyMOLSessionFile']:
					html.append('''<span class='Gen9PyMOL-link'><a href='?query=Gen9File&amp;DesignID=%(DesignID)d&amp;download=ManualDesignsPSE'><img width="18" height="18" src='../images/pse32o.png' alt='pdf'></a></span>''' % design)
				html.append('''</span>''')
			else:
				html.append('''<span class='new-genbrowser-header'></span>''')
			
			html.append('''<span><a class='gen9' href='#manuald%(ManualDesignID)d'>#%(ManualDesignID)d</a></span>''' % manual_design)
			html.append('''<span style='display:inline-block; margin-left:20px;'><a class='newgen9' href='?query=Gen9File&amp;DesignID=%(ManualDesignID)d&amp;download=PDB'>PDB</a></span>''' % manual_design)
				
			ManualDesignsMutations = []
			num_manual_design_mutations = 0
			description_join_str = ""
			for ChainID in DesignChains:
				ChainData = design_residue_data[ManualDesignID].get(ChainID)
				if ChainData:
					chainManualDesignsMutations = []
					for residueID, residue_details in sorted(ChainData.iteritems()):
						if residue_details['IsMutation'] == 1:
							chainManualDesignsMutations.append("%s%s%s" % (residue_details['OriginalAA'], residue_details['ResidueID'], residue_details['VariantAA']))
					if chainManualDesignsMutations:
						num_manual_design_mutations += len(chainManualDesignsMutations) 
						ManualDesignsMutations.append("Chain %s: %s\n" % (ChainID, " ".join(chainManualDesignsMutations)))
			if ManualDesignsMutations:
				ManualDesignsMutations = "".join(ManualDesignsMutations)
				description_join_str = ","
			else:
				ManualDesignsMutations = ""
				
			if manual_design['MutationDescription']:
				html.append('''<span style='margin-left:10px;'>%s%s</span>''' % (manual_design['MutationDescription'], description_join_str))
			
			if ManualDesignsMutations:
				html.append('''<span title='%s' style='background:#dddddd;'>%d mutations from design</span>''' % (ManualDesignsMutations, num_manual_design_mutations))
				
				
			if manual_design.get('Description'):
				html.append('''<span style='margin-left:10px;'>(%(Description)s)</span>''' % manual_design)
			html.append('</div>\n')
			ManualDesignID = None
			
		html.append('''<div class='new-genbrowser-row file-links-div-%(DesignID)d' style='display:none;'><span class='new-genbrowser-header'>Design PDB</span><span class='gen9-betterfilelink'>%(FilePath)s</span></div>\n''' % design)
		if design['PyMOLSessionFile']:
			html.append('''<div class='new-genbrowser-row file-links-div-%(DesignID)d' style='display:none;'><span class='new-genbrowser-header'>Design PSE</span><span class='gen9-betterfilelink'>%(PyMOLSessionFile)s</span></div>\n''' % design)
		if ManualDesignsPerDesign.get(DesignID):
			for manual_design in ManualDesignsPerDesign[DesignID]:
				html.append('''<div class='new-genbrowser-row file-links-div-%(OriginalDesignID)d' style='display:none;'><span class='new-genbrowser-header'>Manual design %(ManualDesignID)d PDB</span><span class='gen9-betterfilelink'>%(FilePath)s</span></div>\n''' % manual_design)
			html.append('''<div class='new-genbrowser-row file-links-div-%(DesignID)d' style='display:none;'><span class='new-genbrowser-header'>Manual designs PSE</span><span class='gen9-betterfilelink'>%(ManualDesignsPyMOLSessionFile)s</span></div>\n''' % design)
		html.append('''<div class='new-genbrowser-row'><span class='new-genbrowser-header'></span><span><button type='button' onClick='show_file_links_new(%(DesignID)d);'>Show paths</button></span></div>\n'''  % design)
		
		motif_info = motif_residues[design['TargetSmallMoleculeMotifID']]
		split_point=motif_info[0].find('_')
		if split_point != -1:
			motif_info[0] = "%s (non-RCSB)" % motif_info[0][split_point+1:]
		motif_pdb_filename = motif_info[0]
		motif_residue_list = "%s" % ",".join(motif_info[1])
		
		
		html.append('''<div class='new-genbrowser-row'><span class='new-genbrowser-header'>Target</span><span>%(SmallMoleculeName)s (%(SmallMoleculeID)s)''' % design)
		if SmallMoleculeReferences.get(design['SmallMoleculeID']):
			count = 1
			for ref in SmallMoleculeReferences[design['SmallMoleculeID']]:
				html.append('''<span class='genbrowser-smallmolecule-reference'>''')
				publication_year = ref['PublicationYear']
				authors = ReferenceAuthors[ref['PublicationID']]
				if len(authors) <= 2:
					authors = " & ".join([author['Surname'] for author in authors])
				else:
					authors = "%s et al." % authors[0]['Surname']
				
				html.append('''<a class='gen9new' target="_new" href='?query=Gen9File&amp;PublicationID=%(PublicationID)d&amp;download=RefPDF'>''' % ref)
				html.append('''%s''' % authors)
				if publication_year != None:
					html.append(''', %d''' % publication_year)
				html.append('''</a></span>''' % ref)
				count += 1
		html.append('''</span></div>\n''')
		
		html.append('''<div class='new-genbrowser-row'><span class='new-genbrowser-header'>Template</span><span>%s</span></div>\n''' % motif_pdb_filename)
		html.append('''<div class='new-genbrowser-row'><span class='new-genbrowser-header'></span><span>%s</span></div>\n''' % design['TargetMotifName'])
		html.append('''<div class='new-genbrowser-row'><span class='new-genbrowser-header'></span><span>%s</span></div>\n''' % motif_residue_list)
		
		profile_timer.start('Ranks')
		
		best_ranked_for_this_design = best_ranked.get(design['DesignID'], [])
		if best_ranked_for_this_design:
			DesignScoreComponents = self.ScoreComponents.get(DesignID, {})
			start_idx = 0
			if ManualDesignsPerDesign.get(DesignID):
				start_idx = 1
				html.append('''<br><div class='new-genbrowser-row'><span class='new-genbrowser-header'>Scores</span>''')
				rank = best_ranked_for_this_design[0]
				html.append('''<span class='gen9-firstscore'>''')
				html.append('''<span class='new-genbrowser-fake-button'>Scheme %(RankingSchemeID)s, ranked #%(Rank)d</span>''' % rank)
				html.append('''</span>''')
				html.append('''</div>\n''')
				### First line ends
				
				html.append("<div class='new-genbrowser-row'><span class='new-genbrowser-header'></span>")
				html.append("<span class='gen9-firstscore'><span><b>Total score: %f</b></span></span>" % rank['TotalScore'])
				html.append('</div>\n')
				
				html.append("<table class='new-genbrowser-score-1'><tr class='new-genbrowser-score-1'><th class='new-genbrowser-score-1'>Component</th><th class='new-genbrowser-score-1'>Score</th><th class='new-genbrowser-score-1'>C. Prob.</th>")
				for manual_design in ManualDesignsPerDesign.get(DesignID, []):
					html.append("<th class='new-genbrowser-score-1'>Manual design %d</th>" % manual_design['ManualDesignID'])
				html.append("</tr>")
				design_rank_components = set(rank_components[rank['RankingSchemeID']])
				
				for score_component in ScoreComponentsOrder:
					CumulativeProbability = ""
					IncludedInScheme = False
					if rank_component_scores.get(DesignID, {}).get(rank['RankingSchemeID'], {}).get(score_component, {}):
						rcs = rank_component_scores[DesignID][rank['RankingSchemeID']][score_component]
						CumulativeProbability = rcs[0]
						IncludedInScheme = rcs[1]
						
					if IncludedInScheme:
						html.append("<tr style='background-color:#c9d8d5'>")
						html.append("<td><b>%s</b></td><td>%0.2f</td>" % (score_component, DesignScoreComponents.get(score_component, "")))
						html.append("<td><b>%s</b></td>" % str(CumulativeProbability))
					else:
						html.append("<tr style='background-color:#888888'>")
						html.append("<td>%s</td><td>%0.2f</td>" % (score_component, DesignScoreComponents.get(score_component, "")))
						if CumulativeProbability:
							html.append("<td>%s</td>" % str(CumulativeProbability))
						else:
							html.append("<td></td>")
					for manual_design in ManualDesignsPerDesign.get(DesignID, []):
						ManualDesignID = manual_design['ManualDesignID']
						html.append("<td style='background-color:#c9d8d5'>%s</td>" % ScoreComponents.get(ManualDesignID, {}).get(score_component, ""))
					html.append("</tr>")
				html.append("</table>\n")
				
			for i in range(start_idx, len(best_ranked_for_this_design), 2):
				
				### First line starts
				html.append('''<br><br><div class='new-genbrowser-row'><span class='new-genbrowser-header'></span>''')

				rank = best_ranked_for_this_design[i]
				next_rank = None
				if i+1 < len(best_ranked_for_this_design):
					next_rank = best_ranked_for_this_design[i+1] 
				
				html.append('''<span class='gen9-firstscore'>''')
				html.append('''<span class='new-genbrowser-fake-button'>Scheme %(RankingSchemeID)s, ranked #%(Rank)d</span>''' % rank)
				
				#if rank['PyMOLSessionFile']:
				#	html.append('''<span class='Gen9PyMOL-link'><a href='?query=Gen9File&amp;DesignID=%(DesignID)d&amp;RankingSchemeID=%(RankingSchemeID)s&amp;download=PSE'><img width="18" height="18" src='../images/pse32o.png' alt='pdf'></a></span>''' % rank)
				html.append('''</span>''')
				
				if next_rank:
					html.append('''<span class='new-genbrowser-fake-button'>Scheme %(RankingSchemeID)s, ranked #%(Rank)d</span>''' % next_rank)
				
				#if next_rankand next_rank['PyMOLSessionFile']:
				#	html.append('''<span class='Gen9PyMOL-link'><a href='?query=Gen9File&amp;DesignID=%(DesignID)d&amp;RankingSchemeID=%(RankingSchemeID)s&amp;download=PSE'><img width="18" height="18" src='../images/pse32o.png' alt='pdf'></a></span></div>\n''' % next_rank)
				#else:
				html.append('''</div>\n''')
				### First line ends
				
				html.append("<div class='new-genbrowser-row'><span class='new-genbrowser-header'></span>")
				html.append("<span class='gen9-firstscore'><span><b>Total score: %f</b></span></span>" % rank['TotalScore'])
				if next_rank:
					html.append("<span><b>Total score: %f</b></span>" % next_rank['TotalScore'])
				html.append('</div>\n')
				
				html.append("<table class='new-genbrowser-score-1'><tr class='new-genbrowser-score-1'><th class='new-genbrowser-score-1'>Component</th><th class='new-genbrowser-score-1'>Score</th><th class='new-genbrowser-score-1'>C. Prob.</th>")
				html.append("</tr>")
				design_rank_components = set(rank_components[rank['RankingSchemeID']])
				
				DesignScoreComponents = self.ScoreComponents.get(DesignID, {})
				for score_component in ScoreComponentsOrder:
					CumulativeProbability = ""
					IncludedInScheme = False
					if rank_component_scores.get(DesignID, {}).get(rank['RankingSchemeID'], {}).get(score_component, {}):
						rcs = rank_component_scores[DesignID][rank['RankingSchemeID']][score_component]
						CumulativeProbability = rcs[0]
						IncludedInScheme = rcs[1]
						
					if IncludedInScheme:
						html.append("<tr style='background-color:#c9d8d5'>")
						html.append("<td><b>%s</b></td><td>%0.2f</td>" % (score_component, DesignScoreComponents.get(score_component, "")))
						html.append("<td><b>%s</b></td>" % str(CumulativeProbability))
					else:
						html.append("<tr style='background-color:#888888'>")
						html.append("<td>%s</td><td>%0.2f</td>" % (score_component, DesignScoreComponents.get(score_component, "")))
						if CumulativeProbability:
							html.append("<td>%s</td>" % str(CumulativeProbability))
						else:
							html.append("<td></td>")
					html.append("</tr>")
				html.append("</table>\n")
				
				if next_rank:
					html.append("<table class='new-genbrowser-score-2'><tr class='new-genbrowser-score-2'><th class='new-genbrowser-score-2'>Component</th><th class='new-genbrowser-score-2'>Score</th><th class='new-genbrowser-score-2'>C. Prob.</th></tr>")
					design_rank_components = set(rank_components[next_rank['RankingSchemeID']])
					for score_component in ScoreComponentsOrder:
						CumulativeProbability = ""
						IncludedInScheme = False
						if rank_component_scores.get(DesignID, {}).get(next_rank['RankingSchemeID'], {}).get(score_component, {}):
							rcs = rank_component_scores[DesignID][next_rank['RankingSchemeID']][score_component]
							CumulativeProbability = rcs[0]
							IncludedInScheme = rcs[1]
							
						if IncludedInScheme:
							html.append("<tr style='background-color:#c9d8d5'>")
							html.append("<td><b>%s</b></td><td>%0.2f</td>" % (score_component, DesignScoreComponents.get(score_component, "")))
							html.append("<td><b>%s</b></td>" % str(CumulativeProbability))
							html.append("</tr>")
						else:
							html.append("<tr style='background-color:#888888'>")
							html.append("<td>%s</td><td>%0.2f</td>" % (score_component, DesignScoreComponents.get(score_component, "")))
							if CumulativeProbability:
								html.append("<td>%s</td>" % str(CumulativeProbability))
							html.append("</tr>")
					html.append("</table>\n")
		else:
			pass
			
		html.append('''<div class='new-genbrowser-row'><span class='new-genbrowser-inline-header'>Scaffold sequences</span>''')
		html.append('''</div>''')
		
		profile_timer.start('Sequences')
		
		sequence_pairs = {}
		#mutant_sequences = gen9db.execute_select('SELECT Chain, ProteinChain.Sequence, WildTypeChain, FirstResidueID FROM DesignMutatedChain INNER JOIN ComplexChain ON DesignMutatedChain.ATOMComplexChainID=ComplexChain.ID INNER JOIN ProteinChain ON ComplexChain.ProteinChainID=ProteinChain.ID WHERE DesignID=%s', parameters=(design['DesignID'],))
		
		mutant_chain_to_wildtype_chain = {}
		wildtype_chain_to_mutant_chain = {}

		for ChainID, ms in MutantSequences[DesignID].iteritems():
			sequence_pairs[ms['Chain']] = [None, None, ms['Sequence'], ms['FirstResidueID']]
			matchtype = DesignMatchtypes[design['DesignID']][ms['WildTypeChain']]
			sequence_pairs[ms['Chain']][1] = matchtype
			mutant_chain_to_wildtype_chain[ms['Chain']] = ms['WildTypeChain']
			wildtype_chain_to_mutant_chain[ms['WildTypeChain']] = ms['Chain'] 
		
		seqres_wildtype_sequences = AllWildtypeSequences['%s-%s' % (design['WildtypeScaffoldPDBFileID'], design['WildtypeScaffoldBiologicalUnit'])]
		atom_wildtype_sequences = AllEffectiveWildtypeSequences['%s-%s' % (design['WildtypeScaffoldPDBFileID'], design['WildtypeScaffoldBiologicalUnit'])]
		
		for wtsequence in seqres_wildtype_sequences:
			if wildtype_chain_to_mutant_chain.get(wtsequence['Chain']):
				mutant_chain = wildtype_chain_to_mutant_chain[wtsequence['Chain']]
				if sequence_pairs.get(mutant_chain) and sequence_pairs[mutant_chain][1] == 'SEQRES':
					sequence_pairs[mutant_chain][0] = wtsequence['Sequence']
		for wtsequence in atom_wildtype_sequences:
			if wildtype_chain_to_mutant_chain.get(wtsequence['Chain']):
				mutant_chain = wildtype_chain_to_mutant_chain[wtsequence['Chain']]
				if sequence_pairs.get(mutant_chain) and sequence_pairs[mutant_chain][1] == 'ATOM':
					sequence_pairs[mutant_chain][0] = wtsequence['Sequence']
		
		for chainID, sp in sequence_pairs.iteritems():
			assert(sp[0])
			assert(sp[1])
			assert(sp[2])
		
		residue_offset = 0
		for chainID, s_pair in sorted(sequence_pairs.iteritems()):
			# Start counting from the correct number according to the order in the PDB file
			design_residue_id = s_pair[3]
			if design_residue_id == None:
				print("Warning: The FirstResidueID field is NULL for Design %d, chain %s." % (DesignID, chainID))
				design_residue_id = 1
			sub_html = []
			sub_html.append("<table class='new-gen9browser-sequences'>")
			
			motif_positions = set()
			if DesignsMotifResidues.get(chainID):
				motif_positions = [m[2] for m in DesignsMotifResidues.get(chainID)]
			if len(s_pair[0]) == len(s_pair[2]):
				
				n = 100
				
				wt_sequence = s_pair[0]
				mutant_sequence = s_pair[2]
				
				manual_sequences = []
				manual_subsequences = []
				for manual_design in ManualDesignsPerDesign.get(DesignID, []):
					ManualDesignID=manual_design['DesignID']
					manual_sequence = MutantSequences[ManualDesignID][chainID]['Sequence']
					manual_subsequences.append([s for s in get_subsequence(manual_sequence, n)])
					
				wt_subsequences = [s for s in get_subsequence(wt_sequence, n)]
				mutant_subsequences = [s for s in get_subsequence(mutant_sequence, n)]
				
				counter = '1234567890' * (len(s_pair[0])/10) + ('1234567890')[0:len(s_pair[0])%10]
				ncount = 0
				for x in range(len(wt_subsequences)):
					wt_subsequence = wt_subsequences[x]
					mutant_subsequence = mutant_subsequences[x]
					num_manual_sequences = len(ManualDesignsPerDesign.get(DesignID, []))
					list_of_manual_subsequences = []
					for xman in range(num_manual_sequences):
						list_of_manual_subsequences.append(manual_subsequences[xman][x])
					#html.append("<tr><td>        </td><td style='font-family:monospace;'>%s</td></tr>" % counter[ncount:ncount+n])
					#html.append("<tr><td>Wildtype</td><td style='font-family:monospace;'>%s</td></tr>" % wt_subsequence)
					seq1 = []
					seq2 = []
					manual_seqs = [[] for xman in range(num_manual_sequences)]
					for x in range(len(mutant_subsequence)):
						if wt_subsequence[x] == mutant_subsequence[x]:
							seq1.append("<span title='%s %d'>%s</span>" % (ROSETTAWEB_SK_AAinv[wt_subsequence[x]], design_residue_id, wt_subsequence[x]))
							if (ncount+x+1) in motif_positions:
								seq2.append("<span title='%s %d' class='new-genbrowser-sequence-motif-residue'>%s</span>" % (ROSETTAWEB_SK_AAinv[mutant_subsequence[x]], design_residue_id, mutant_subsequence[x]))
							else:
								seq2.append("<span title='%s %d'>-</span>" % (ROSETTAWEB_SK_AAinv[mutant_subsequence[x]], design_residue_id))
						else:
							seq1.append("<span title='%s %d' class='new-genbrowser-sequence-wildtype-mutated'>%s</span>" % (ROSETTAWEB_SK_AAinv[wt_subsequence[x]], design_residue_id, wt_subsequence[x]))
							if (ncount+x+1) in motif_positions:
								seq2.append("<span title='%s %d' class='new-genbrowser-sequence-motif-residue'>%s</span>" % (ROSETTAWEB_SK_AAinv[mutant_subsequence[x]], design_residue_id, mutant_subsequence[x]))
							else:
								seq2.append("<span title='%s %d' class='new-genbrowser-sequence-mutant-mutated'>%s</span>" % (ROSETTAWEB_SK_AAinv[mutant_subsequence[x]], design_residue_id, mutant_subsequence[x]))
						for xman in range(num_manual_sequences):
							manual_subsequence = list_of_manual_subsequences[xman]
							if wt_subsequence[x] == manual_subsequence[x]:
								if (ncount+x+1) in motif_positions:
									manual_seqs[xman].append("<span class='new-genbrowser-sequence-motif-residue'>-</span>")
								else:
									manual_seqs[xman].append("<span>-</span>")
							else:
								if (ncount+x+1) in motif_positions:
									manual_seqs[xman].append("<span class='new-genbrowser-sequence-motif-residue'>%s</span>" % (manual_subsequence[x]))
								else:
									manual_seqs[xman].append("<span class='new-genbrowser-sequence-mutant-mutated'>%s</span>" % (manual_subsequence[x]))
					
							
						design_residue_id += 1
					sub_html.append("<tr><td>Wildtype</td><td style='font-family:monospace;'>%s</td></tr>" % "".join(seq1))
					sub_html.append("<tr><td>Design</td><td style='font-family:monospace;'>%s</td></tr>" % "".join(seq2))
					for xman in range(num_manual_sequences):
						manual_design = ManualDesignsPerDesign[DesignID][xman]
						sub_html.append("<tr><td>Manual %d</td><td style='font-family:monospace;'>%s</td></tr>" % (manual_design['ManualDesignID'], "".join(manual_seqs[xman])))
						
					ncount += n
				residue_offset += len(wt_sequence)
			
			else:
				sub_html.append("<tr><td>Design</td><td>Error: The length of the wildtype chain does not match what the database describes as the corresponding mutant chain.</td></tr>")
			sub_html.append("</table>")
			
			html.append('''<div class='new-genbrowser-sequence-block'>''')
			db_mutations = []
			if DesignsMutations and DesignsMutations.get(chainID):
				db_mutations = DesignsMutations[chainID]
				
				if HasSequenceLogo.get(DesignID) and chainID in HasSequenceLogo.get(DesignID):
					first_cell = '''Chain %s <a class='gen9' target="_new" href='?query=Gen9File&amp;DesignID=%d&amp;download=WebLogo&amp;Chain=%s'> <img width="42" height="18" src='../images/weblogo.png' alt='WebLogo'></a>:''' % (chainID, DesignID, chainID)
				else:
					first_cell = 'Chain %s:' % chainID
				
				html.append('''<div class='new-genbrowser-row'><span class='new-genbrowser-sequence-chain'>%s</span>''' % first_cell)
				if chain_molecule_info.get(pdbID) and chain_molecule_info[pdbID].get(mutant_chain_to_wildtype_chain[chainID]):
					html.append('''<span class="new-genbrowser-sequence-motif-residues">%s</span></div>''' % chain_molecule_info[pdbID][mutant_chain_to_wildtype_chain[chainID]])
				else:
					html.append('''<span class="new-genbrowser-sequence-motif-residues"></span></div>''')

				if DesignsMotifResidues.get(chainID):
					html.append('''<div class='new-genbrowser-row'><span class='new-genbrowser-sequence-chain'></span><span class="new-genbrowser-sequence-motif-residues">Motif residues %s</span></div>''' % (", ".join(['''<span class='new-genbrowser-sequence-motif-residue'>%s</span>''' % "".join(map(str, m[0:2])) for m in DesignsMotifResidues.get(chainID)])))
				#html.append('''<span title="%s" class="new-genbrowser-sequence-motif-residues">Mutations %s (%d mutations in total)</span></div>''' % (", ".join(["".join(map(str,m[0:3])) for m in db_mutations]), len(db_mutations)))
				html.append('''<div class='new-genbrowser-row'><span class='new-genbrowser-sequence-chain'></span><span title="%s" class="new-genbrowser-sequence-motif-residues">Mutations ''')
				html.append(''' (%d mutations in total)</span></div>''' % len(db_mutations))
			else:
				html.append('''<div class='new-genbrowser-row'><span class='new-genbrowser-sequence-chain'>Chain %s</span>''' % chainID)
				if chain_molecule_info.get(pdbID) and chain_molecule_info[pdbID].get(mutant_chain_to_wildtype_chain[chainID]):
					html.append('''<span class="new-genbrowser-sequence-motif-residues">%s</span></div>''' % chain_molecule_info[pdbID][mutant_chain_to_wildtype_chain[chainID]])
				else:
					html.append('''<span class="new-genbrowser-sequence-motif-residues"></span></div>''')
				if DesignsMotifResidues.get(chainID):
					html.append('''<div class='new-genbrowser-row'><span class='new-genbrowser-sequence-chain'></span><span class="new-genbrowser-sequence-motif-residues">Motif residues %s</span></div>''' % (", ".join(['''<span class='new-genbrowser-sequence-motif-residue'>%s</span>''' % "".join(map(str, m[0:2])) for m in DesignsMotifResidues.get(chainID)])))
				#html.append('''<span title="%s" class="new-genbrowser-sequence-motif-residues">Mutations %s (%d mutations in total)</span></div>''' % (", ".join(["".join(map(str,m[0:3])) for m in db_mutations]), len(db_mutations)))
				html.append('''<div class='new-genbrowser-row'><span class='new-genbrowser-sequence-chain'></span><span title="%s" class="new-genbrowser-sequence-motif-residues">Mutations ''')
				html.append(''' (%d mutations in total)</span></div>''' % len(db_mutations))
				
			html.extend(sub_html)
			html.append('''</div>''')
		
		profile_timer.start('Dunbrack energies')
		
		if design_residue_data.get(DesignID):
			html.append("<div style='padding-top:10px;padding-bottom:5px;' class='new-genbrowser-row'><span class='new-genbrowser-inline-header'>Dunbrack energies, &#x3C7; angle deviations, and side-chain RMSDs upon repacking after ligand removal</span></div>")
			html.append("<div style='padding-top:5px;padding-bottom:5px;' class='new-genbrowser-row'><span style='margin-left:20px' class='new-genbrowser-inline-header'>Design:</span>")
			html.append('''<span class='gen9-scaffold-details' onclick='showScaffoldDetails(%(DesignID)d, true);'  id='scaffold-details-%(DesignID)d-show'><img width="11" height="11" src='../images/plusbutton32.png' alt='pdf'></span>''' % design)
			html.append('''<span class='gen9-scaffold-details' onclick='showScaffoldDetails(%(DesignID)d, false);' id='scaffold-details-%(DesignID)d-hide' style='display:none;'><img width="11" height="11" src='../images/minusbutton32.png' alt='pdf'></span>''' % design)
			html.append("</div>")
		html.append('''<div class='new-genbrowser-row' style='display:none;' id='scaffold-details-%(DesignID)d-div'>''' % design)
		if design_residue_data.get(DesignID):
			# &#x3B4; delta
			# &#x3C3; sigma
			
			html.append("<table style='padding-bottom:10px;' class='new-genbrowser-score-2'>")
			html.append("<tr style='text-align:center;' class='new-genbrowser-score-2'><th COLSPAN='3'></th><th style='text-align:center' class='new-genbrowser-score-2' COLSPAN='4'>Repack single, no ligand</th><th style='text-align:center' class='new-genbrowser-score-2' COLSPAN='4'>Repack single, with ligand</th><th style='text-align:center' class='new-genbrowser-score-2' COLSPAN='4'>Repack all, no ligand</th></tr>")
			html.append("<tr style='text-align:center;' class='new-genbrowser-score-2'><td class='new-genbrowser-score-2h'>Chain</td><td class='new-genbrowser-score-2h'>Mutation</td><td class='new-genbrowser-score-2h'>fa_dun</td>")
			for rowcount in range(3):
				html.append("<td title='We consider significant changes to be anything greater than 20&#176;.' class='new-genbrowser-score-2h'>Large &#x394;(&#x3C7;)</td><td class='new-genbrowser-score-2h'>&#x394;(&#x3C7;1)</td><td class='new-genbrowser-score-2h'>&#x394;(&#x3C7;2)</td><td title='RMSD is based on all sidechain heavy atoms' class='new-genbrowser-score-2h'>RMSD (&#197;)</td>")
			html.append("</tr>")
			for dm_chain, residue_ids in sorted(design_residue_data[DesignID].iteritems()):
				for residue_id, residue_detail in sorted(residue_ids.iteritems()):
					residue_detail['ResidueID'] = residue_id 
					#html.append("<tr style='background-color:#c9d8d5'><td><b>%s</b></td>" % dm_chain)
					html.append("<tr class='new-genbrowser-stats'><td><b>%s</b></td>" % dm_chain)
					if residue_detail['IsMotifResidue']:
						if residue_detail['IsMutation']:
							html.append("<td style='background:#FFFF00'>%(OriginalAA)s%(ResidueID)d%(VariantAA)s</td>" % residue_detail)
						else:
							html.append("<td style='background:#FFFF00'>%(VariantAA)s%(ResidueID)d</td>" % residue_detail)
					elif residue_detail['IsMutation']:
						html.append("<td style='background:#d07d50'>%(OriginalAA)s%(ResidueID)d%(VariantAA)s</td>" % residue_detail)
					else:
						html.append("<td>%(VariantAA)s%(ResidueID)d</td>" % residue_detail)
					if residue_detail.get('fa_dun') != None:
						html.append("<td>%(fa_dun)f</td>" % residue_detail)
					else:
						html.append("<td></td>")
					for prefix in residue_stats_headers:
						if residue_detail.get('%sSignificantChiChange' % prefix) != None:
							if residue_detail.get('%sSignificantChiChange' % prefix) == 0.0:
								html.append("<td>No</td>")
							elif residue_detail.get('%sSignificantChiChange' % prefix) < 1.0:
								html.append("<td style='font-weight:bold;color:#fff;background:#d0d01d;'>Somewhat</td>")
							elif residue_detail.get('%sSignificantChiChange' % prefix) == 1.0:
								html.append("<td style='font-weight:bold;color:#fff;background:#d0101d;'>Yes</td>")
						else:
							html.append("<td></td>")
						Chi1Delta = residue_detail.get('%sChi1Delta' % prefix)
						if Chi1Delta != None:
							if Chi1Delta < 20:
								html.append("<td>%0.2f&#176;</td>" % Chi1Delta)
							else:
								html.append("<td style='font-weight:bold;color:#fff;background:#d0101d;'>%0.2f&#176;</td>" % Chi1Delta)
						else:
							html.append("<td></td>")
						Chi2Delta = residue_detail.get('%sChi2Delta' % prefix)
						if Chi2Delta != None:
							if Chi2Delta < 20:
								html.append("<td>%0.2f&#176;</td>" % Chi2Delta)
							else:
								html.append("<td style='font-weight:bold;color:#fff;background:#d0101d;'>%0.2f&#176;</td>" % Chi2Delta)
						else:
							html.append("<td></td>")
						if residue_detail.get('%sAllSideChainHeavyAtomsRMSD' % prefix):
							html.append("<td>%0.3f</td>" % residue_detail.get('%sAllSideChainHeavyAtomsRMSD' % prefix))
						else:
							html.append("<td></td>")
					html.append("</tr>")
			html.append("</table>\n")
		html.append("</div>")	
		
		for manual_design in AllManualDesignsPerDesign.get(DesignID, []):
			if manual_design['MutationDescription'].lower() == 'original design' or manual_design['MutationDescription'] == 'AUTO Wildtype Sequence':
				continue
			ManualDesignID = manual_design['ManualDesignID'] 
			if design_residue_data.get(ManualDesignID):
				html.append("<div style='padding-top:5px;padding-bottom:5px;' class='new-genbrowser-row'><span style='margin-left:20px' class='new-genbrowser-inline-header'>Manual design #%d (%s):</span>" % (ManualDesignID, manual_design['MutationDescription']))

				html.append('''<span class='gen9-scaffold-details' onclick='showManualDesignDetails(%(ManualDesignID)d, true);'  id='scaffold-details-Manual%(ManualDesignID)d-show'><img width="11" height="11" src='../images/plusbutton32.png' alt='pdf'></span>''' % manual_design)
				html.append('''<span class='gen9-scaffold-details' onclick='showManualDesignDetails(%(ManualDesignID)d, false);' id='scaffold-details-Manual%(ManualDesignID)d-hide' style='display:none;'><img width="11" height="11" src='../images/minusbutton32.png' alt='pdf'></span>''' % manual_design)
				html.append("</div>")
			html.append('''<div class='new-genbrowser-row' style='display:none;' id='scaffold-details-Manual%(ManualDesignID)d-div'>''' % manual_design)
			#html.append('''<div class='new-genbrowser-row' id='scaffold-details-Manual%(ManualDesignID)d-div'>''' % manual_design)
			if design_residue_data.get(ManualDesignID):
				html.append("<table style='padding-bottom:10px;' class='new-genbrowser-score-2'>")
				html.append("<tr style='text-align:center;' class='new-genbrowser-score-2'><th COLSPAN='%d'></th><th style='text-align:center' class='new-genbrowser-score-2' COLSPAN='4'>Repack single, no ligand</th><th style='text-align:center' class='new-genbrowser-score-2' COLSPAN='4'>Repack single, with ligand</th><th style='text-align:center' class='new-genbrowser-score-2' COLSPAN='4'>Repack all, no ligand</th></tr>" % (2+len(manual_design_score_components_of_interest)))
				html.append("<tr style='text-align:center;' class='new-genbrowser-score-2'><td class='new-genbrowser-score-2h'>Chain</td><td class='new-genbrowser-score-2h'>Mutation</td>")
				for sc in manual_design_score_components_of_interest:
					html.append("<td class='new-genbrowser-score-2h'>%s</td>" % sc)
				for rowcount in range(3):
					html.append("<td title='We consider significant changes to be anything greater than 20&#176;.' class='new-genbrowser-score-2h'>Large &#x394;(&#x3C7;)</td><td class='new-genbrowser-score-2h'>&#x394;(&#x3C7;1)</td><td class='new-genbrowser-score-2h'>&#x394;(&#x3C7;2)</td><td title='RMSD is based on all sidechain heavy atoms' class='new-genbrowser-score-2h'>RMSD (&#197;)</td>")
				html.append("</tr>")
				for dm_chain, residue_ids in sorted(design_residue_data[ManualDesignID].iteritems()):
					for residue_id, residue_detail in sorted(residue_ids.iteritems()):
						residue_detail['ResidueID'] = residue_id 
						#html.append("<tr style='background-color:#c9d8d5'><td><b>%s</b></td>" % dm_chain)
						html.append("<tr class='new-genbrowser-manual-design-stats'><td><b>%s</b></td>" % dm_chain)
						if design_residue_data[DesignID][dm_chain].get(residue_id, {}).get('IsMotifResidue'):
							if residue_detail['IsMutation']:
								html.append("<td style='background:#FFFF00'>%(OriginalAA)s%(ResidueID)d%(VariantAA)s</td>" % residue_detail)
							else:
								html.append("<td style='background:#FFFF00'>%(VariantAA)s%(ResidueID)d</td>" % residue_detail)
						elif residue_detail['IsMutation']:
							html.append("<td style='background:#d07d50'>%(OriginalAA)s%(ResidueID)d%(VariantAA)s</td>" % residue_detail)
						else:
							html.append("<td>%(VariantAA)s%(ResidueID)d</td>" % residue_detail)
						for sc in manual_design_score_components_of_interest:
							if residue_detail.get(sc) != None:
								if residue_detail[sc] == 0:
									html.append("<td>0</td>")
								else:
									html.append("<td>%0.2f</td>" % residue_detail[sc])
							else:
								html.append("<td></td>")
						for prefix in residue_stats_headers:
							if residue_detail.get('%sSignificantChiChange' % prefix) != None:
								if residue_detail.get('%sSignificantChiChange' % prefix) == 0.0:
									html.append("<td>No</td>")
								elif residue_detail.get('%sSignificantChiChange' % prefix) < 1.0:
									html.append("<td style='font-weight:bold;color:#fff;background:#d0d01d;'>Somewhat</td>")
								elif residue_detail.get('%sSignificantChiChange' % prefix) == 1.0:
									html.append("<td style='font-weight:bold;color:#fff;background:#d0101d;'>Yes</td>")
							else:
								html.append("<td></td>")
							Chi1Delta = residue_detail.get('%sChi1Delta' % prefix)
							if Chi1Delta != None:
								if Chi1Delta < 20:
									html.append("<td>%0.2f&#176;</td>" % Chi1Delta)
								else:
									html.append("<td style='font-weight:bold;color:#fff;background:#d0101d;'>%0.2f&#176;</td>" % Chi1Delta)
							else:
								html.append("<td></td>")
							Chi2Delta = residue_detail.get('%sChi2Delta' % prefix)
							if Chi2Delta != None:
								if Chi2Delta < 20:
									html.append("<td>%0.2f&#176;</td>" % Chi2Delta)
								else:
									html.append("<td style='font-weight:bold;color:#fff;background:#d0101d;'>%0.2f&#176;</td>" % Chi2Delta)
							else:
								html.append("<td></td>")
							if residue_detail.get('%sAllSideChainHeavyAtomsRMSD' % prefix):
								html.append("<td>%0.3f</td>" % residue_detail.get('%sAllSideChainHeavyAtomsRMSD' % prefix))
							else:
								html.append("<td></td>")
						html.append("</tr>")
				html.append("</table>\n")	
			html.append("</div>")		
			
		profile_timer.start('Scaffold references')
		
		if ScaffoldReferences.get(ComplexID):
			html.append('''<div class='new-genbrowser-row'><span class='new-genbrowser-header'>Scaffold references</span></div>''')
			for ref in ScaffoldReferences[ComplexID]:
				publication_year = ref['PublicationYear']
				
				authors = ReferenceAuthors[ref['PublicationID']]
				if len(authors) <= 2:
					authors = " & ".join([author['Surname'] for author in authors])
				else:
					authors = "%s et al." % authors[0]['Surname']
				
				html.append('''<div class='new-genbrowser-row'><span class='new-genbrowser-sequence-reference'>
<a class='gen9new' target="_new" href='?query=Gen9File&amp;PublicationID=%(PublicationID)d&amp;download=RefPDF'>''' % ref)
				html.append('''%s''' % authors)
				if publication_year != None:
					html.append(''', %d''' % publication_year)
				html.append('''</a></span><span>%(Notes)s</span></div>''' % ref)
		
		comments = []
		if MeetingDesignRatings.get(DesignID):
			comments += [(comment['CommentDate'], 'Meeting', comment['Approved'], comment['ApprovalNotes']) for comment in MeetingDesignRatings[DesignID].values()]
		if UserDesignRatings:
			comments += [(comment['Date'], comment['FirstName'], comment['Rating'], comment['RatingNotes']) for comment in UserDesignRatings if comment['Rating'] or comment['RatingNotes']]
		if comments:
			html.append('''<div class='new-genbrowser-row'><span class='new-genbrowser-header'>Design comments</span><span></span></div>\n''' % design)
			comments = sorted(comments, reverse=True)
			html.append('''<div class='new-genbrowser-row'>''')
			html.append('''<table class='new-genbrowser-comments'>''')
			html.append('''<tr class='new-genbrowser-comments'><th class='new-genbrowser-comments'>Date</th><th class='new-genbrowser-comments'>User</th><th class='new-genbrowser-comments'>Rating</th><th class='new-genbrowser-comments'>Notes</th></tr>''')
				
			for comment in comments:
				
				#<span class='new-genbrowser-comment-header'></span>''')
				name = comment[1]
				if name == 'Yao-ming':
					name = 'Ming'
				html.append('''<tr style='background-color:%s' class='new-genbrowser-comments'>''' % group_colors[name])
				html.append('''<td style='width:160px' class='new-genbrowser-comments'>%s</td>''' % comment[0])
				html.append('''<td style='width:80px' class='new-genbrowser-comments'>%s</td>''' % name)
				if comment[2] == 'Yes' or comment[2] == 'Good':
					html.append('''<td style='text-align:center; width:50px; background:#19AC19' class='new-genbrowser-comments'>%s</td>''' % (comment[2]))
				elif comment[2] == 'No' or comment[2] == 'Bad':
					html.append('''<td style='text-align:center; width:50px; font-weight:bold; color:#fff; background:%s' class='new-genbrowser-comments'>%s</td>''' % (self.bad_design_red, comment[2]))
				else:
					html.append('''<td style='text-align:center; width:50px; background:%s' class='new-genbrowser-comments'>%s</td>''' % (self.maybe_design_orange, comment[2]))
				html.append('''<td style='width:600px' class='new-genbrowser-comments'>%s</td>''' % comment[3])
				html.append('''</tr>\n''')
			html.append('''</table></div>''')
				
				#<span><a class='newgen9' href='?query=Gen9File&amp;DesignID=%(DesignID)d&amp;download=PDB'>Download</a></span></div>\n'''  % design)
		
		profile_timer.start('Scaffold comments')
		
		html.append('''<div class='new-genbrowser-row'><span class='new-genbrowser-header'>Scaffold comments</span><span></span></div>\n''' % design)
		
		comments = []#
		key = design['ComplexID']
		if MeetingScaffoldRatings.get(key):
			comments += [(comment['CommentDate'], 'Meeting', comment['Approved'], comment['ApprovalNotes']) for comment in MeetingScaffoldRatings[key].values()]
		if UserScaffoldRatings.get(key):
			comments += [(comment['Date'], comment['FirstName'], comment['Rating'], comment['RatingNotes']) for comment in UserScaffoldRatings[key].values() if comment['Rating']]
					
		if comments:
			comments = sorted(comments, reverse=True)
			
			key = design['ComplexID']
			if UserScaffoldTerminiOkay.get(key):
				comments.append((None, 'TerminiOkay?', UserScaffoldTerminiOkay[key], ''))

			html.append('''<div class='new-genbrowser-row'>''')
			html.append('''<table class='new-genbrowser-comments'>''')
			html.append('''<tr class='new-genbrowser-comments'><th class='new-genbrowser-comments'>Date</th><th class='new-genbrowser-comments'>User</th><th class='new-genbrowser-comments'>Rating</th><th class='new-genbrowser-comments'>Notes</th></tr>''')
				
			for comment in comments:
				#<span class='new-genbrowser-comment-header'></span>''')
				name = comment[1]
				if name == 'Yao-ming':
					name = 'Ming'
				html.append('''<tr style='background-color:%s' class='new-genbrowser-comments'>''' % group_colors[name])
				html.append('''<td style='width:160px' class='new-genbrowser-comments'>%s</td>''' % comment[0])
				html.append('''<td style='width:80px' class='new-genbrowser-comments'>%s</td>''' % name)
				if comment[2] == 'Yes' or comment[2] == 'Good':
					html.append('''<td style='text-align:center; width:50px; background:#40c06d' class='new-genbrowser-comments'>%s</td>''' % (comment[2]))
				elif comment[2] == 'No' or comment[2] == 'Bad':
					html.append('''<td style='text-align:center; width:50px; font-weight:bold; color:#fff; background:%s' class='new-genbrowser-comments'>%s</td>''' % (self.bad_scaffold_red, comment[2]))
				else:
					html.append('''<td style='text-align:center; width:50px; background:%s' class='new-genbrowser-comments'>%s</td>''' % (self.maybe_scaffold_orange, comment[2]))

				html.append('''<td style='width:600px' class='new-genbrowser-comments'>%s</td>''' % comment[3])
				html.append('''</tr>\n''')
			html.append('''</table></div>''')
		# ROW 4
		profile_timer.start('User comments')
		
		if username:
			html.append('''<div class='new-genbrowser-row'><span class='new-genbrowser-inline-header'>Your comments</span>''')
			html.append('''<span class='gen9-scaffold-details' onclick='showUserComments(%(DesignID)d, true);'  id='user-comments-%(DesignID)d-show'><img width="11" height="11" src='../images/plusbutton32.png' alt='pdf'></span>''' % design)
			html.append('''<span class='gen9-scaffold-details' onclick='showUserComments(%(DesignID)d, false);' id='user-comments-%(DesignID)d-hide' style='display:none;'><img width="11" height="11" src='../images/minusbutton32.png' alt='pdf'></span>''' % design)
			html.append('''</div>''')
			
			# START user-comments-div
			html.append('''<div class='new-genbrowser-row' style='display:none;' id='user-comments-%(DesignID)d-div'>''' % design)
		
			html.append('''<FORM name="gen9form-new-%(DesignID)d" method="post" action="http://albana.ucsf.edu/backrub/cgi-bin/rosettaweb.py">''' % design)
			html.append('''<input type="hidden" NAME="DesignID" VALUE="%(DesignID)d">''' % design)
			html.append('''<input type="hidden" NAME="Username" VALUE="%s">''' % username)
			html.append('''<input type="hidden" NAME="Gen9Page" VALUE="">''')
			html.append('''<input type="hidden" NAME="query" VALUE="">''')
			html.append('''<input type="hidden" NAME="gen9sort1" VALUE="">''')
			html.append('''<input type="hidden" NAME="gen9sort2" VALUE="">''')
			
			# User design comments
			user_design_comments = ""
			user_design_rating = ""
			user_scaffold_comments = "" 
			user_scaffold_rating = ""
			
			for udr in UserDesignRatings:
				if udr['UserID'] == username:
					user_design_comments = udr['RatingNotes']
					user_design_rating = udr['Rating']
			
			key = design['ComplexID']
			if UserScaffoldRatings.get(key):
				if UserScaffoldRatings[key].get(username):
					user_scaffold_comments = UserScaffoldRatings[key][username]['RatingNotes']
					user_scaffold_rating = UserScaffoldRatings[key][username]['Rating']
			
			# START new-genbrowser-comments-form-block
			html.append('''<div class='new-genbrowser-comments-form-block'>''')
			
			# user design comments block
			html.append("<div><span class='new-genbrowser-comments-header'>Design:</span><span class='new-genbrowser-comments-rating'><select name='user-design-rating-%d'>" % design['DesignID'])
			if user_design_rating == "":
				html.append("<option value='None' selected='selected'>[none]</option>")
			else:
				html.append("<option value='None'>[none]</option>")
			
			if user_design_rating == "Bad":
				html.append("<option value='Bad' selected='selected'>Bad</option>")
			else:
				html.append("<option value='Bad'>Bad</option>")
			
			if user_design_rating == "Good":
				html.append("<option value='Good' selected='selected'>Good</option>")
			else:
				html.append("<option value='Good'>Good</option>")
			
			if user_design_rating == "Maybe":
				html.append("<option value='Maybe' selected='selected'>Maybe</option>")
			else:
				html.append("<option value='Maybe'>Maybe</option>")
			html.append("</select></span>")
			if user_design_comments:
				html.append("""<span><textarea class='new-genbrowser-comments-textarea' name='user-design-comments-%d'>%s</textarea></span></div>""" % (design['DesignID'], user_design_comments.replace('"',"'")))
			else:
				html.append("""<span><textarea class='new-genbrowser-comments-textarea' name='user-design-comments-%d'></textarea></span></div>""" % (design['DesignID']))
			
			# END new-genbrowser-comments-form-block
			html.append("""</div>""")
			
			# User scaffold comments
			
			# START new-genbrowser-comments-form-block
			html.append('''<div class='new-genbrowser-comments-form-block'>''')
			
			# user scaffold comments block
			html.append("<div><span class='new-genbrowser-comments-header'>Scaffold:</span><span class='new-genbrowser-comments-rating'><select name='user-scaffold-rating-%d'>" % design['DesignID'])
			if user_scaffold_rating == "":
				html.append("<option value='None' selected='selected'>[none]</option>")
			else:
				html.append("<option value='None'>[none]</option>")
			
			if user_scaffold_rating == "Bad":
				html.append("<option value='Bad' selected='selected'>Bad</option>")
			else:
				html.append("<option value='Bad'>Bad</option>")
			
			if user_scaffold_rating == "Good":
				html.append("<option value='Good' selected='selected'>Good</option>")
			else:
				html.append("<option value='Good'>Good</option>")
			
			if user_scaffold_rating == "Maybe":
				html.append("<option value='Maybe' selected='selected'>Maybe</option>")
			else:
				html.append("<option value='Maybe'>Maybe</option>")
			html.append("</select></span>")
			
			if user_scaffold_comments:
				html.append("""<span><textarea class='new-genbrowser-comments-textarea' name='user-scaffold-comments-%d'>%s</textarea></span></div>""" % (design['DesignID'], user_scaffold_comments.replace('"',"'")))
			else:
				html.append("""<span><textarea class='new-genbrowser-comments-textarea' name='user-scaffold-comments-%d'></textarea></span></div>""" % (design['DesignID']))
			
			# END new-genbrowser-comments-form-block
			html.append("""</div>""")
			
			html.append("""<div class='new-genbrowser-comments-form-block'><span><button type='submit' name='user-comments-submit-%d' onClick='copyPageFormValues(this);'>Submit comments</button></span></div>""" % design['DesignID'])
			html.append('''</FORM>''') 
		
		profile_timer.start('Meeting comments')
			
		if username and (username == 'oconchus' or username == 'kyleb' or username == 'rpache'):
			
			#html.append('''<div style='display:none;' id='meeting-comments-%(DesignID)d'>''')
			html.append('''<div class='new-genbrowser-row'><span class='new-genbrowser-header'>Meeting comments</span></div>'''  % design)
			
			html.append('''<FORM name="gen9form-meeting-%(DesignID)d" method="post" action="http://albana.ucsf.edu/backrub/cgi-bin/rosettaweb.py">''' % design)
			html.append('''<input type="hidden" NAME="DesignID" VALUE="%(DesignID)d">''' % design)
			html.append('''<input type="hidden" NAME="Username" VALUE="%s">''' % username)
			html.append('''<input type="hidden" NAME="Gen9Page" VALUE="">''')
			html.append('''<input type="hidden" NAME="query" VALUE="">''')
			html.append('''<input type="hidden" NAME="gen9sort1" VALUE="">''')
			html.append('''<input type="hidden" NAME="gen9sort2" VALUE="">''')
			
			# Meeting design comments
			meeting_design_comments = ""
			meeting_design_rating = ""
			meeting_scaffold_comments = "" 
			meeting_scaffold_rating = ""
			
			for dt, mdr in MeetingDesignRatings.get(DesignID, {}).iteritems():
				if dt == date.today():
					meeting_design_comments = mdr['ApprovalNotes']
					meeting_design_rating = mdr['Approved']
			
			key = design['ComplexID']
			for dt, mdr in MeetingScaffoldRatings.get(key, {}).iteritems():
				if dt == date.today():
					meeting_scaffold_comments = mdr['ApprovalNotes']
					meeting_scaffold_rating = mdr['Approved']
			
			
			# START new-genbrowser-comments-form-block
			html.append('''<div class='new-genbrowser-comments-form-block'>''')
			
			# meeting design comments block
			html.append("<div><span class='new-genbrowser-comments-header'>Design:</span><span class='new-genbrowser-comments-rating'><select name='meeting-design-rating-%d'>" % design['DesignID'])
			if meeting_design_rating == "":
				html.append("<option value='None' selected='selected'>[none]</option>")
			else:
				html.append("<option value='None'>[none]</option>")
			
			if meeting_design_rating == "No":
				html.append("<option value='No' selected='selected'>No</option>")
			else:
				html.append("<option value='No'>No</option>")
			
			if meeting_design_rating == "Yes":
				html.append("<option value='Yes' selected='selected'>Yes</option>")
			else:
				html.append("<option value='Yes'>Yes</option>")
			
			if meeting_design_rating == "Maybe":
				html.append("<option value='Maybe' selected='selected'>Maybe</option>")
			else:
				html.append("<option value='Maybe'>Maybe</option>")
			html.append("</select></span>")
			
			if meeting_design_comments:
				html.append("""<span><textarea class='new-genbrowser-comments-textarea' name='meeting-design-comments-%d'>%s</textarea></span></div>""" % (design['DesignID'], meeting_design_comments.replace('"',"'")))
			else:
				html.append("""<span><textarea class='new-genbrowser-comments-textarea' name='meeting-design-comments-%d'></textarea></span></div>""" % (design['DesignID']))
			
			# END new-genbrowser-comments-form-block
			html.append("""</div>""")
			
			# Meeting scaffold comments
			
			# START new-genbrowser-comments-form-block
			html.append('''<div class='new-genbrowser-comments-form-block'>''')
			
			# meeting scaffold comments block
			html.append("<div><span class='new-genbrowser-comments-header'>Scaffold:</span><span class='new-genbrowser-comments-rating'><select name='meeting-scaffold-rating-%d'>" % design['DesignID'])
			if meeting_scaffold_rating == "":
				html.append("<option value='None' selected='selected'>[none]</option>")
			else:
				html.append("<option value='None'>[none]</option>")
			
			if meeting_scaffold_rating == "No":
				html.append("<option value='No' selected='selected'>No</option>")
			else:
				html.append("<option value='No'>No</option>")
			
			if meeting_scaffold_rating == "Yes":
				html.append("<option value='Yes' selected='selected'>Yes</option>")
			else:
				html.append("<option value='Yes'>Yes</option>")
			
			if meeting_scaffold_rating == "Maybe":
				html.append("<option value='Maybe' selected='selected'>Maybe</option>")
			else:
				html.append("<option value='Maybe'>Maybe</option>")
			html.append("</select></span>")
			
			if meeting_scaffold_comments:
				html.append("""<span><textarea class='new-genbrowser-comments-textarea' name='meeting-scaffold-comments-%d'>%s</textarea></span></div>""" % (design['DesignID'], meeting_scaffold_comments.replace('"',"'")))
			else:
				html.append("""<span><textarea class='new-genbrowser-comments-textarea' name='meeting-scaffold-comments-%d'></textarea></span></div>""" % (design['DesignID']))
			
			# END new-genbrowser-comments-form-block
			html.append("""</div>""")
				
			html.append("""<div class='new-genbrowser-comments-form-block'><span><button type='submit' name='meeting-comments-submit-%d' onClick='copyPageFormValues(this); this.form.query.value = "Gen9MeetingComment";'>Submit comments</button></span></div>""" % design['DesignID'])
			html.append('''</FORM>''')
		
		if username:
			# END user-comments-div 
			html.append('''</div>''') 
				
		html.append('''<hr class='new-genbrowser-hr'><div style="padding-bottom:10px;"></div>''')
		html.append('</div>')
		return html

	def get_ManualDesign_HTML(self, design):
		'''design should be the result of a database query having:
		   *todo*
		   - all fields in ManualDesign;
		   - most fields in Design;
		   - PDBBiologicalUnit.ComplexID;
		   - SmallMolecule.Name AS SmallMoleculeName;
		   - SmallMolecule.ID AS SmallMoleculeID;
		   - SmallMoleculeMotif.Name AS TargetMotifName.'''
		
		html = []
		return html
		
		
		
def getTablelessBrowsePageNotes():
	html = []
	html.append('''<H1 align="center">To be done: <br>
-add target molecule assay references and target motif references<br>
-improve filtering - store user's filters so they are reloaded on page reload<br>
</H1><br>''')
	html.append('''<H1 class="gen9-new-instructions">
The scaffold column is colored depending on the scaffold rating which may differ from the design rating. Colors are based on consensus user rating - if opinions disagree then the column is colored as a maybe (orange). Ratings
from meetings, if they exist, trump all other ratings with the more recent meetings taking priority.</H1>''')
	html.append('''<H1 class="gen9-new-instructions">
Mutation residue IDs use Rosetta numbering, not PDB numbering.
</H1>''')
	html.append('''<H1 class="gen9-new-instructions">
All score components are shown. The components for the particular ranking scheme are shown in bold. The unused components for that scheme 
have a darker, gray background. Cumulative probabilities, when available, are given in the final column.
</H1>''')
	html.append('''<H1 class="gen9-new-instructions">
To jump to a particular design, enter the design ID number in the textfield on the bottom right.
</H1>''')
	html.append('''<H1 class="gen9-new-instructions">
The show/hide buttons do not combine their filtering e.g. if you hide all bad designs and then show all bad scaffolds, all designs with bad scaffolds are shown, even the bad designs you just hid. 
</H1>''')
	return html

def determine_sorting_criteria(form):
	sorting_criteria = ['PDBBiologicalUnit.ComplexID', '', 'Design.ID']
	order_mapping = {
		'Complex'		: ('PDBBiologicalUnit.ComplexID',),
		'ATOMComplex'	: ('Design.ATOMComplexID',),
		'ID'			: ('Design.ID',),
		'Target'		: ('SmallMoleculeID',),
		'Scaffold'		: ('Design.WildtypeScaffoldPDBFileID', 'Design.WildtypeScaffoldBiologicalUnit'),
	}
		
	if form.has_key('gen9sort1'):
		ordering = order_mapping.get(form['gen9sort1'].value)
		if ordering:
			sorting_criteria[0] = ordering[0]
		if len(ordering) > 1:
			sorting_criteria[1] = ordering[1]
	if form.has_key('gen9sort2'):
		ordering = order_mapping.get(form['gen9sort2'].value)
		if ordering:
			if len(ordering) == 1:
				sorting_criteria[2] = ordering[0]
			else:
				sorting_criteria[1] = ordering[0]
				sorting_criteria[2] = ordering[1]

	sorting_criteria = [s for s in sorting_criteria if s]
	if sorting_criteria[0] == sorting_criteria [1]:
		sorting_criteria = sorting_criteria[1:]
	sorting_criteria = ",".join(sorting_criteria)
	return sorting_criteria

def get_sorting_controls_html():
	html = []
	html.append('''<div align="left">''')
	html.append('''Order records by:''')
	html.append('''<select id='ordering1' name='new-ordering1'>
		<option value='Complex'>Complex</option>
		<option value='ID'>ID</option>
		<option value='ATOMComplex'>Mutant complex</option>
		<option value='Target'>Target</option>
		<option value='Scaffold'>Scaffold</option>
		</select>''')
	html.append('''<select id='ordering2' name='new-ordering2'>
		<option value='Complex'>Complex</option>
		<option value='ID'>ID</option>
		<option value='ATOMComplex'>Mutant complex</option>
		<option value='Target'>Target</option>
		<option value='Scaffold'>Scaffold</option>
		</select>''')
	html.append("""<button type='button' name='new-resort-designs' onClick='reopen_page_with_sorting();'>Sort</button>""")
	html.append('''</div>''')
	return html

def get_Top10_controls_html():
	html = []
	
	SmallMoleculeIDs = [r['SmallMoleculeID'] for r in gen9db.execute("SELECT DISTINCT SmallMoleculeID FROM TopDesign INNER JOIN TopDesignScheme WHERE Description LIKE 'Top 10%' ORDER BY SmallMoleculeID")]
	RankingSchemeIDs = [r['RankingSchemeID'] for r in gen9db.execute("SELECT DISTINCT RankingSchemeID FROM TopDesign INNER JOIN TopDesignScheme WHERE Description LIKE 'Top 10%' ORDER BY RankingSchemeID")]
	html.append('''<div align="left">''')
	html.append('''<span>View Top 10 designs <input name="Show_Top_10_Options" id="Show_Top_10_Options" type="checkbox" onClick="toggleTop10Options()"></span>''' % vars())
	html.append('''<span id='Top10Options' style='display:none'>''')

	html.append('''<select id='Top10SmallMolecules' name='Top10SmallMolecules'>
		<option value=''>All molecules</option>''')
	for SmallMoleculeID in SmallMoleculeIDs:
		html.append('''<option value='%s'>%s</option>''' % (SmallMoleculeID, SmallMoleculeID))
	html.append('''</select>''')
	
	html.append('''<select id='Top10RankingScheme' name='Top10RankingScheme'>''')
	for RankingSchemeID in RankingSchemeIDs:
		html.append('''<option value='%s'>Ranking scheme %s</option>''' % (RankingSchemeID, RankingSchemeID))
	html.append('''</select>''')
	
	html.append('''<select id='Top10DesignType' name='Top10DesignType'>
		<option value=''>All design types</option>
		<option value='Design'>Design</option>
		<option value='Relaxed_design'>Relaxed design</option>
		</select>''')
	html.append('''</span>''')
	html.append("""<button type='button' name='new-resort-designs' onClick='reopen_page_with_top10();'>Go</button>""")
	html.append('''</div>''')
	return html

def generateDesignBrowsePage(form, design_iterator, filtered_DesignIDs):
	global username
	html = []
	chartfns = []
	
	function_start_time = time.time()
	
	profile_timer = ProfileTimer()
	profile_timer.start('Design: Preamble')
	
	html.append('''<center><div>''')
	
	sorting_criteria = determine_sorting_criteria(form)
	
	Top10Mode = False
	if form.has_key('gen9mode') and form['gen9mode'].value == 'top10':
		Top10Mode = True
	
	if len(gen9db.execute_select("SELECT ID FROM Design WHERE FilePath IS NOT NULL")) != len(gen9db.execute_select("SELECT DISTINCT FilePath FROM Design WHERE FilePath IS NOT NULL")):
		html.append('''<h1 style='color:red'>Error in the database: Some designs appear to be stored more than once in the database i.e. multiple designs have the same filepath in the database.</h1>''') 
	
	if not Top10Mode:
		html.extend(getTablelessBrowsePageNotes())
	
	if Top10Mode:
		top10_query = "SELECT DISTINCT TopDesign.DesignID, TopDesign.SmallMoleculeID, TopDesign.RankingSchemeID, RankedScore.Rank, Design.Type FROM TopDesign INNER JOIN Design ON TopDesign.DesignID=Design.ID INNER JOIN RankedScore ON TopDesign.DesignID=RankedScore.DesignID AND TopDesign.RankingSchemeID=RankedScore.RankingSchemeID"
		where_clauses = []
		where_values = []
		rough_count = 400
		if form.has_key('top10mol'):
			s = form['top10mol'].value
			assert(len(s) == 3)
			assert(s.isalnum())
			where_clauses.append("SmallMoleculeID=%s")
			where_values.append(s)
			rough_count /= 5
		if form.has_key('top10scheme'):
			s = form['top10scheme'].value
			assert(s.isalnum())
			where_clauses.append("TopDesign.RankingSchemeID=%s")
			where_values.append(s)
			rough_count /= 4
		if form.has_key('top10type'):
			s = form['top10type'].value
			assert(s.isalpha())
			if s == 'RelaxedDesign':
				s = 'Relaxed design'
			where_clauses.append("Design.Type=%s")
			where_values.append(s)
			rough_count /= 2
		assert(len(where_clauses) == len(where_values))
		if where_clauses:
			where_clauses = ' WHERE %s' % " AND ".join(where_clauses)
			top10_query += where_clauses 
		top10_query += ' ORDER BY SmallMoleculeID, TopDesign.RankingSchemeID, Design.Type, Rank'
		Top10Designs = gen9db.execute_select(top10_query, parameters=tuple(where_values))
		assert(0.82 <= (float(rough_count)/float(len(Top10Designs))) <= 1.0)
		
		SortedTop10Designs = {}
		SortedTop10DesignsSet = set()
		for r in Top10Designs:
			SortedTop10Designs[r['SmallMoleculeID']] = SortedTop10Designs.get(r['SmallMoleculeID'], {})
			SortedTop10Designs[r['SmallMoleculeID']][r['RankingSchemeID']] = SortedTop10Designs[r['SmallMoleculeID']].get(r['RankingSchemeID'], {})
			SortedTop10Designs[r['SmallMoleculeID']][r['RankingSchemeID']][r['Type']] = SortedTop10Designs[r['SmallMoleculeID']][r['RankingSchemeID']].get(r['Type'], {})
			SortedTop10Designs[r['SmallMoleculeID']][r['RankingSchemeID']][r['Type']][r['Rank']] = r['DesignID']
			SortedTop10DesignsSet.add(r['DesignID'])
		
	hidden_designs = [173]
	
	if Top10Mode:
		all_designs = gen9db.execute_select("SELECT Design.ID AS DesignID, PDBBiologicalUnit.ComplexID, Design.*, SmallMolecule.Name AS SmallMoleculeName, SmallMolecule.ID AS SmallMoleculeID, SmallMoleculeMotif.Name AS TargetMotifName FROM Design INNER JOIN SmallMoleculeMotif ON TargetSmallMoleculeMotifID=SmallMoleculeMotif.ID INNER JOIN SmallMolecule ON SmallMoleculeID=SmallMolecule.ID INNER JOIN PDBBiologicalUnit ON PDBBiologicalUnit.PDBFileID=WildtypeScaffoldPDBFileID AND PDBBiologicalUnit.BiologicalUnit=WildtypeScaffoldBiologicalUnit WHERE Design.Type='Design' OR Design.Type='Relaxed design'")
		all_designs = [r for r in all_designs if r['DesignID'] in SortedTop10DesignsSet]
	else:
		all_designs = gen9db.execute_select("SELECT Design.ID AS DesignID, PDBBiologicalUnit.ComplexID, Design.*, SmallMolecule.Name AS SmallMoleculeName, SmallMolecule.ID AS SmallMoleculeID, SmallMoleculeMotif.Name AS TargetMotifName FROM Design INNER JOIN SmallMoleculeMotif ON TargetSmallMoleculeMotifID=SmallMoleculeMotif.ID INNER JOIN SmallMolecule ON SmallMoleculeID=SmallMolecule.ID INNER JOIN PDBBiologicalUnit ON PDBBiologicalUnit.PDBFileID=WildtypeScaffoldPDBFileID AND PDBBiologicalUnit.BiologicalUnit=WildtypeScaffoldBiologicalUnit WHERE Design.Type='Design' OR Design.Type='Relaxed design' ORDER BY %s" % sorting_criteria)
	shown_designs = [design for design in all_designs if design["ID"] not in hidden_designs] 
	
	profile_timer.start('Postamble')
	
	if not(Top10Mode):
		html.append(generateFilterCheckboxes(username))
	
	if Top10Mode:
		html.append('''<H1 align="left">Designs (%s)</H1><div align="right">
</div>''' % len([design for design in shown_designs if ((None == filtered_DesignIDs) or (filtered_DesignIDs and (design['DesignID'] in filtered_DesignIDs)))]))
	else:
		html.append('''<H1 align="left">Designs (%s)</H1><div align="right">
</div>''' % len([design for design in shown_designs if ((None == filtered_DesignIDs) or (filtered_DesignIDs and (design['DesignID'] in filtered_DesignIDs)))]))

	#<table style="border-style:solid; border-width:1px;">
	#<tr><td>Download PyMOL session</td><td><img width="18" height="18" src='../images/filesaveas128.png' alt='pdf'></td></tr>
	#</table>
	html.extend(get_Top10_controls_html())
	html.append('''<br>''')
	
	html.extend(get_sorting_controls_html())
	html.append('''<br><br>''')
	html.append(generateHidingCheckboxes())
	html.append('''<br>''')
	
	if Top10Mode:
		html.append('''<div class='gen9floater'>''')
		html.append('''<div>Jump to design:<input style='background:#e3eae9' onKeyPress="goToDesign(this, event)" type=text size=4 maxlength=4 name='floating-goto' value=""></div>''')
		for SmallMoleculeID in sorted(SortedTop10Designs.keys()):
			html.append('''<div style='text-align:left'><span style="cursor: pointer;"  onclick='goToSmallMolecule("%s");'>Jump to %s</span></div>''' % (SmallMoleculeID, SmallMoleculeID))
		html.append('''</div>''')
		
	else:
		html.append('''<div class='gen9floater'>Jump to design:<input style='background:#e3eae9' onKeyPress="goToDesign(this, event)" type=text size=4 maxlength=4 name='floating-goto' value=""></div>''')
	
	profile_timer.start('For-loop start')
	
	html.append('''<div class='new-genbrowser'>''')
	
	#designs, filtered_DesignIDs
	
	profile_timer.start('Design: HTML Generation')
	if Top10Mode:
		designs_table = {}
		for design in shown_designs:
			designs_table[design['DesignID']] = design
		for SmallMoleculeID, SmallMoleculeDetails in sorted(SortedTop10Designs.iteritems()):
			html.append("<a id='aSmallMolecule%s'></a>" % SmallMoleculeID)
			for RankingSchemeID, RankingSchemeDetails in sorted(SmallMoleculeDetails.iteritems()):
				html.append("<a id='a%sRankingScheme%s'></a>" % (SmallMoleculeID, RankingSchemeID))
				for TypeID, TypeDetails in sorted(RankingSchemeDetails.iteritems()):
					html.append("<a id='a%s_%s_%s'></a>" % (SmallMoleculeID, RankingSchemeID, TypeID))
					count = 1
					for Rank, DesignID in sorted(TypeDetails.iteritems()):
						html.append("<h1 class='Top10SmallMolecule'><a class='top10header' href='#aSmallMolecule%s'>%s</a></h1>" % (SmallMoleculeID, SmallMoleculeID))
						html.append("<h1 class='Top10RankingScheme'><a class='top10header' href='#a%sRankingScheme%s'>Ranking scheme %s</a></h1>" % (SmallMoleculeID, RankingSchemeID, RankingSchemeID))
						html.append("<h1 class='Top10DesignType'><a class='top10header' href='#a%s_%s_%s'>%ss</a></h1>" % (SmallMoleculeID, RankingSchemeID, TypeID, TypeID))
						html.append("<p class ='Top10DesignRank'><b>#%d (ranked %d in the scheme)<b/></p>" % (count, Rank))
						html.extend(design_iterator.get_Design_HTML(designs_table[DesignID]))
						count += 1
	else:		
		for design in shown_designs:
			#if username=='oconchus' and design['ID']!=100:
			#	continue
			html.extend(design_iterator.get_Design_HTML(design, profile_timer))
	profile_timer.stop()
	
	if showprofile:
		debug_log(username, "<br>Function time: %f" % (time.time() - function_start_time))
		debug_log(username, "** HTML generator time **")
		debug_log(username, profile_timer.getProfile())
		
		
	html.append('''</div>''')
	
	html.append('''<input type="hidden" NAME="query" VALUE="">''')
	html.append('''</div></center>''')

	return html, chartfns

def generateRankMappingPage(form):
	global gen9db
	
	html = []
	chartfns = []
	
	html.append('''<div>''')
	results = gen9db.execute("SELECT Design.ID AS DesignID, Design.Type AS Type, WildtypeScaffoldPDBFileID, WildtypeScaffoldBiologicalUnit, SmallMoleculeID, RankingSchemeID, Rank FROM Design INNER JOIN SmallMoleculeMotif ON Design.TargetSmallMoleculeMotifID=SmallMoleculeMotif.ID INNER JOIN RankedScore ON Design.ID=RankedScore.DesignID ORDER BY Design.ID")
	if results:
		html.append('''<div class="rankmapping_header"><span>Design ID#</span><span>Design Type</span><span>Ranking scheme ID</span><span>Wildtype scaffold</span></div>''')
		for r in results: 
			html.append('''<div class="rankmapping">''')
			html.append('''<span onmouseover='style="cursor: pointer;"' onClick="jumpToDesign(%(DesignID)d)">%(DesignID)d</span>''' % r)
			html.append('''<span>%(Type)s</span>''' % r)
			html.append('''<span>%(SmallMoleculeID)s_%(RankingSchemeID)s_%(Rank)d</span>''' % r)
			html.append('''<span>%(WildtypeScaffoldPDBFileID)s, %(WildtypeScaffoldBiologicalUnit)s</span>''' % r)
			html.append('''</div>''')
	html.append('''</div>''')
	
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
	
def generateGen9Page(settings_, rosettahtml, form, userid_, Gen9Error, filtered_DesignIDs):
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
	
	BrowserVersion = 1
	results = gen9db.execute("SELECT BrowserVersion FROM User WHERE ID=%s", parameters= (username,))
	if len(results) == 1:
		BrowserVersion = results[0]['BrowserVersion']
	
	qs_gen9mode = ""
	if form.has_key("gen9mode"):
		qs_gen9mode = form["gen9mode"].value
	qs_top10mol = ""
	if form.has_key("top10mol"):
		qs_top10mol = form["top10mol"].value
	qs_top10scheme = ""
	if form.has_key("top10scheme"):
		qs_top10scheme = form["top10scheme"].value
	qs_top10type = ""
	if form.has_key("top10type"):
		qs_top10type = form["top10type"].value
	
	Gen9Page = ""
	if form.has_key("Gen9Page"):
		Gen9Page = form["Gen9Page"].value
	gen9sort1 = ""
	if form.has_key("gen9sort1"):
		gen9sort1 = form["gen9sort1"].value
	gen9sort2 = ""
	if form.has_key("gen9sort2"):
		gen9sort2 = form["gen9sort2"].value
		
	# Set generate to False to hide pages for quicker testing
	subpages = []
	
	global showprofile
	if username=='oconchus':
		showprofile = False #True
	
	design_iterator = DesignIterator(filtered_DesignIDs)
	
	if username=='oconchus':
		#subpages.append({"name" : "browse",		"desc" : "Browse designs",	"fn" : generateGenericPage,	"generate" :True,	"params" : [form]})
		subpages.append({"name" : "browse",		"desc" : "Browse designs",	"fn" : generateDesignBrowsePage,	"generate" :True,	"params" : [form, design_iterator, filtered_DesignIDs]})
	else:
		subpages.append({"name" : "browse",		"desc" : "Browse designs",	"fn" : generateDesignBrowsePage,	"generate" :True,	"params" : [form, design_iterator, filtered_DesignIDs]})

	subpages.append({"name" : "rankmapping",		"desc" : "Rank/Design ID mapping",	"fn" : generateRankMappingPage,			"generate" :True,	"params" : [form]})
	
	
	# Create menu
	
	html.append("<td align=center>")
	html.append('''<FORM name="gen9form" method="post" action="http://albana.ucsf.edu/backrub/cgi-bin/rosettaweb.py">''')
	
	for subpage in subpages:
		if subpage["generate"]:
			html.append('''<input type="button" value="%(desc)s" onClick="showPage('%(name)s');">''' % subpage)
	
	html.append('''<input type="button" value="Refresh" onClick="document.gen9form.query.value='Gen9'; document.gen9form.submit();">''')
	html.append('''<input type="button" value="Switch view" onClick="document.gen9form.query.value='Gen9Switch'; document.gen9form.submit();">''')
	html.append('''<input type="hidden" NAME="Gen9Page" VALUE="%s">''' % Gen9Page)
	html.append('''<input type="hidden" NAME="query" VALUE="">''')
	html.append('''<input type="hidden" NAME="gen9sort1" VALUE="%s">''' % gen9sort1)
	html.append('''<input type="hidden" NAME="gen9sort2" VALUE="%s">''' % gen9sort2)
	html.append('''<input type="hidden" NAME="Username" VALUE="%s">''' % username)

	html.append('''<input type="hidden" NAME="gen9mode" VALUE="%s">''' % qs_gen9mode)
	html.append('''<input type="hidden" NAME="top10mol" VALUE="%s">''' % qs_top10mol)
	html.append('''<input type="hidden" NAME="top10scheme" VALUE="%s">''' % qs_top10scheme)
	html.append('''<input type="hidden" NAME="top10type" VALUE="%s">''' % qs_top10type)	
	
	if form.has_key('DesignID'):
		html.append('''<input type="hidden" NAME="DesignID" VALUE="%d">''' % int(form['DesignID'].value))
	else:
		html.append('''<input type="hidden" NAME="DesignID" VALUE="">''')
	if Gen9Error:			
		html.append('''<input type="hidden" NAME="Gen9Error" VALUE="%s">''' % Gen9Error)
	else:
		html.append('''<input type="hidden" NAME="Gen9Error" VALUE="">''')
			
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
	html.append('''
<script src="/backrub/frontend/gen9.js" type="text/javascript"></script>
<script src="/javascripts/sorttable.js" type="text/javascript"></script>''')

	gen9db.close()
	rosettaweb.close()
	
	return html