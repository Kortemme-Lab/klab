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
	
	def getProfile(self):
		if not self.stopped:
			return False
		s = []
		for stage in self.stages:
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
	
	allDesignIDs = set([r['ID'] for r in gen9db.execute_select('SELECT ID FROM Design')]) 
	
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
				allEntityRatedDesignIDs = set([r['ID'] for r in gen9db.execute_select("SELECT Design.ID FROM Design INNER JOIN UserDesignRating ON UserDesignRating.DesignID=Design.ID WHERE UserID=%s", parameters=(rating_entity_id,))])
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
				UserRatedDesignIDs = set([r['ID'] for r in gen9db.execute_select("SELECT Design.ID FROM Design INNER JOIN UserDesignRating ON UserDesignRating.DesignID=Design.ID WHERE UserID='%s' AND %s" % (rating_entity_id, disjunction))])
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
				allEntityRatedScaffoldIDs = set([r['ID'] for r in gen9db.execute_select("SELECT Design.ID FROM Design INNER JOIN PDBBiologicalUnit ON PDBBiologicalUnit.PDBFileID=WildtypeScaffoldPDBFileID AND PDBBiologicalUnit.BiologicalUnit=WildtypeScaffoldBiologicalUnit INNER JOIN UserScaffoldRating ON UserScaffoldRating.ComplexID=PDBBiologicalUnit.ComplexID WHERE UserID=%s", parameters=(rating_entity_id,))])
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
				UserRatedScaffoldIDs = set([r['ID'] for r in gen9db.execute_select("SELECT Design.ID FROM Design INNER JOIN PDBBiologicalUnit ON PDBBiologicalUnit.PDBFileID=WildtypeScaffoldPDBFileID AND PDBBiologicalUnit.BiologicalUnit=WildtypeScaffoldBiologicalUnit INNER JOIN UserScaffoldRating ON UserScaffoldRating.ComplexID=PDBBiologicalUnit.ComplexID WHERE UserID='%s' AND %s" % (rating_entity_id, disjunction))])
				if form['FilterType'].value == 'Intersection':
					filteredIDs = filteredIDs.intersection(UserRatedScaffoldIDs)
				else:
					filteredIDs = filteredIDs.union(UserRatedScaffoldIDs)
	
	if form.has_key('FilterMeetingSelection'):
		
		# This gets the list of designs not rated in ANY meeting
		elem = 'Filter_Design_Meeting_Unrated' % vars()
		if form.has_key(elem):
			allMeetingRatedDesignIDs = set([r['ID'] for r in gen9db.execute_select("SELECT Design.ID FROM Design INNER JOIN MeetingDesignRating ON MeetingDesignRating.DesignID=Design.ID")])
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
			MeetingRatedDesignIDs = set([r['ID'] for r in gen9db.execute_select("SELECT Design.ID FROM Design INNER JOIN MeetingDesignRating ON MeetingDesignRating.DesignID=Design.ID WHERE DATE(MeetingDate)='%s' AND %s" % (form['FilterMeetingSelection'].value, disjunction))])
			if form['FilterType'].value == 'Intersection':
				filteredIDs = filteredIDs.intersection(MeetingRatedDesignIDs)
			else:
				filteredIDs = filteredIDs.union(MeetingRatedDesignIDs)
				
				
	return filteredIDs
	
def generateHidingCheckboxes():
	html = []
	html.append("<div style='text-align:left'>")
	html.append('''<span class='gen9-hiding-button'><button style="width:155px" type='button' onClick="toggleNewDesigns(this);">Only recent designs</button></span>''')
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
	
	def __init__(self, filtered_DesignIDs):
		self.html = []
		self._initialize_css_members()
		self._initialize_data()
		self.filtered_DesignIDs = filtered_DesignIDs
	
	def _initialize_css_members(self):
		self.darker_blue = '#b2cecf'
		self.lighter_blue = '#e3eae9'
		self.alt_lighter_blue = '#d3dad9'
		
		self.bad_design_red = '#d0101d'
		self.bad_scaffold_red = '#c0101d'
		self.maybe_design_orange = '#e8c800'
		self.maybe_scaffold_orange = '#e0c000'
		self.good_design_green  = '#50f07d'
		self.good_scaffold_green  = '#40e06d'
		self.wildtype_mutation_green  = '#50d07d'
		self.title_bold_text = '#5225d0'
		self.YesNoMap = {0: 'No', 1: 'Yes'}
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
		# motif_residues
		motif_residues = {}
		results = gen9db.execute_select("SELECT * FROM SmallMoleculeMotifResidue ORDER BY ResidueID")
		for r in results:
			motif_residues[r["SmallMoleculeMotifID"]] = motif_residues.get(r["SmallMoleculeMotifID"], [r['PDBFileID'], []])
			motif_residues[r["SmallMoleculeMotifID"]][1].append("%(WildTypeAA)s%(ResidueID)s" % r)
		self.motif_residues = motif_residues
		
		# best_ranked
		best_ranked = {}
		results = gen9db.execute_select("SELECT * FROM RankedScore WHERE MarkedAsBest=1")
		for r in results:
			best_ranked[r['DesignID']] = best_ranked.get(r['DesignID'], [])
			best_ranked[r['DesignID']].append(r)
		self.best_ranked = best_ranked
		
		# HasSequenceLogo
		HasSequenceLogo = {}	
		results = gen9db.execute_select("SELECT * FROM DesignMutatedChain WHERE SequenceLogo IS NOT NULL")
		for r in results:
			HasSequenceLogo[r['DesignID']] = HasSequenceLogo.get(r['DesignID'], set())
			HasSequenceLogo[r['DesignID']].add(r['Chain'])
		self.HasSequenceLogo = HasSequenceLogo
		
		# DesignMatchtypes
		DesignMatchtypes = {}
		results = gen9db.execute_select('SELECT DesignID, WildtypeScaffoldChain, Matchtype FROM DesignSequenceMatch')
		for r in results:
			DesignMatchtypes[r['DesignID']] = DesignMatchtypes.get(r['DesignID'], {})
			DesignMatchtypes[r['DesignID']][r['WildtypeScaffoldChain']] = r['Matchtype']
		self.DesignMatchtypes = DesignMatchtypes
		
		# AllWildtypeSequences
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
		rank_components = {}
		results = gen9db.execute_select("SELECT DISTINCT RankingSchemeID, Component FROM RankedScoreComponent")
		for r in results:
			rank_components[r['RankingSchemeID']] = rank_components.get(r['RankingSchemeID'], [])
			rank_components[r['RankingSchemeID']].append(r['Component'])
		for rank_scheme in rank_components.keys():
			rank_components[rank_scheme] = sorted(rank_components[rank_scheme])
		self.rank_components = rank_components
		
		# rank_component_scores
		rank_component_scores = {}
		results = gen9db.execute_select("SELECT * FROM RankedScoreComponent ORDER BY Component")
		for r in results:
			rank_component_scores[r['DesignID']] = rank_component_scores.get(r['DesignID'], {})
			rank_component_scores[r['DesignID']][r['RankingSchemeID']] = rank_component_scores[r['DesignID']].get(r['RankingSchemeID'], {})
			rank_component_scores[r['DesignID']][r['RankingSchemeID']][r['Component']] = (r['CumulativeProbability'], r['IncludedInScheme'])
		self.rank_component_scores = rank_component_scores
		
		# chain_molecule_info
		chain_molecule_info = {}
		results = gen9db.execute_select('SELECT PDBMolecule.PDBFileID, PDBMoleculeChain.Chain, PDBMolecule.Name, PDBMolecule.Synonym FROM PDBMoleculeChain INNER JOIN PDBMolecule ON PDBMoleculeChain.PDBFileID=PDBMolecule.PDBFileID AND PDBMoleculeChain.MoleculeID=PDBMolecule.MoleculeID')
		for r in results:
			chain_molecule_info[r['PDBFileID']] = chain_molecule_info.get(r['PDBFileID'], {})
			chain_molecule_info[r['PDBFileID']][r['Chain']] = '<span title="%s">%s</span>' % (r['Synonym'], r['Name'])
		self.chain_molecule_info = chain_molecule_info
		
		# design_mutations, design_residue_data 
		self.residue_stats_headers = ['RSNL_', 'RSWL_', 'RANL_']
		design_residue_data = {}
		design_mutations = {}
		results = gen9db.execute_select('SELECT * FROM DesignMutation ORDER BY DesignID, Chain, ResidueID')
		for r in results:
			design_mutations[r['DesignID']] = design_mutations.get(r['DesignID'], {})
			design_mutations[r['DesignID']][r['Chain']] = design_mutations[r['DesignID']].get(r['Chain'], [])
			design_mutations[r['DesignID']][r['Chain']].append((r['WildTypeAA'], r['ResidueID'], r['MutantAA'], r['fa_dun']))
			
			design_residue_data[r['DesignID']] = design_residue_data.get(r['DesignID'], {})
			design_residue_data[r['DesignID']][r['Chain']] = design_residue_data[r['DesignID']].get(r['Chain'], {})
			design_residue_data[r['DesignID']][r['Chain']][r['ResidueID']] = {
				'WildTypeAA'	: r['WildTypeAA'],
				'MutantAA'		: r['MutantAA'],
				'fa_dun'		: r['fa_dun'],
			}
		results = gen9db.execute_select('SELECT * FROM DesignResidue ORDER BY DesignID, Chain, ResidueID')
		for r in results:
			design_residue_data[r['DesignID']] = design_residue_data.get(r['DesignID'], {})
			design_residue_data[r['DesignID']][r['Chain']] = design_residue_data[r['DesignID']].get(r['Chain'], {})
			d = design_residue_data[r['DesignID']][r['Chain']].get(r['ResidueID'], {
					'WildTypeAA'					: r['DesignedAA'],
					'MutantAA'						: '',
				})
			for prefix in self.residue_stats_headers:
				d['%sSignificantChiChange' % prefix]		= r['%sSignificantChiChange' % prefix]
				d['%sChi1Delta' % prefix]					= r['%sChi1Delta' % prefix]
				d['%sChi2Delta' % prefix]					= r['%sChi2Delta' % prefix]
				d['%sAllSideChainHeavyAtomsRMSD' % prefix]	= r['%sAllSideChainHeavyAtomsRMSD' % prefix]
			design_residue_data[r['DesignID']][r['Chain']][r['ResidueID']] = d
		self.design_residue_data = design_residue_data
		self.design_mutations = design_mutations
		
		# design_motif_residues
		design_motif_residues = {}
		results = gen9db.execute_select('SELECT * FROM DesignMotifResidue ORDER BY DesignID, Chain, ResidueID')
		for r in results:
			design_motif_residues[r['DesignID']] = design_motif_residues.get(r['DesignID'], {})
			design_motif_residues[r['DesignID']][r['Chain']] = design_motif_residues[r['DesignID']].get(r['Chain'], [])
			design_motif_residues[r['DesignID']][r['Chain']].append((r['ResidueAA'], r['ResidueID'], r['PositionWithinChain'], r['RMSD']))
		self.design_motif_residues = design_motif_residues
		
		# meeting_comments
		meeting_comments = {}
		results = gen9db.execute_select('SELECT * FROM MeetingDesignRating ORDER BY CommentDate')
		for r in results:
			meeting_comments[r['DesignID']] = meeting_comments.get(r['DesignID'], [])
			meeting_comments[r['DesignID']].append(r)
		self.meeting_comments = meeting_comments
		
		# MeetingDesignRatings
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
		ScaffoldReferences = {} 
		results = gen9db.execute_select("""SELECT * FROM ScaffoldReference INNER JOIN Publication ON PublicationID = Publication.ID ORDER BY PublicationDate""")
		for r in results:
			key = r['ComplexID']
			ScaffoldReferences[key] = ScaffoldReferences.get(key, [])
			ScaffoldReferences[key].append(r)
		self.ScaffoldReferences = ScaffoldReferences
		
		# SmallMoleculeReferences
		SmallMoleculeReferences = {} 
		results = gen9db.execute_select("""SELECT * FROM SmallMoleculeReference INNER JOIN Publication ON PublicationID = Publication.ID ORDER BY PublicationDate""")
		for r in results:
			key = r['SmallMoleculeID']
			SmallMoleculeReferences[key] = SmallMoleculeReferences.get(key, [])
			SmallMoleculeReferences[key].append(r)
		self.SmallMoleculeReferences = SmallMoleculeReferences
		
		# ReferenceAuthors
		ReferenceAuthors = {} 
		results = gen9db.execute_select("""SELECT * FROM PublicationAuthor ORDER BY PublicationID, AuthorOrder""")
		for r in results:
			key = r['PublicationID']
			ReferenceAuthors[key] = ReferenceAuthors.get(key, [])
			ReferenceAuthors[key].append(r)
		self.ReferenceAuthors = ReferenceAuthors

	def get_Design_HTML(self, design):
		'''design should be the result of a database query having:
		   - all fields in Design;
		   - PDBBiologicalUnit.ComplexID;
		   - SmallMolecule.Name AS SmallMoleculeName;
		   - SmallMolecule.ID AS SmallMoleculeID;
		   - SmallMoleculeMotif.Name AS TargetMotifName.'''
		
		html = []
		DesignID = design['DesignID']
		if (self.filtered_DesignIDs != None) and (DesignID not in self.filtered_DesignIDs):
			return html
		
		pdbID = design['WildtypeScaffoldPDBFileID']
		ComplexID = design['ComplexID']
		best_ranked_for_this_design = self.best_ranked.get(design['DesignID'], [])
		
		#UserDesignRatings = gen9db.execute_select("SELECT * FROM UserDesignRating INNER JOIN User ON UserID=User.ID WHERE DesignID=%s ORDER BY FirstName, Date", parameters=(design['DesignID'],))
		UserDesignRatings = gen9db.execute_select("""
SELECT FirstName, UserDesignRating.*
FROM UserDesignRating 
INNER JOIN (
SELECT UserID,DesignID,MAX(Date) AS MaxDate
FROM UserDesignRating GROUP BY UserID, DesignID) udr
ON udr.UserID=UserDesignRating.UserID AND udr.DesignID=UserDesignRating.DesignID AND udr.MaxDate=UserDesignRating.Date
INNER JOIN User ON UserDesignRating.UserID=User.ID
WHERE UserDesignRating.DesignID=%s ORDER BY FirstName
""", parameters=(design['DesignID'],))
		
		# Determine main row color based on ratings
		design_tr_class = 'unrated_design'
		scaffold_tr_class = 'unrated_scaffold'
		
		meeting_approval = None
		if MeetingDesignRatings.get(DesignID):
			# Latest meeting rating trumps all
			meeting_approval = MeetingDesignRatings[DesignID][sorted(MeetingDesignRatings[DesignID].keys(), reverse = True)[0]]['Approved']
		
		if meeting_approval:
			design_tr_class = meeting_rating_css_classes[meeting_approval] 
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
			scaffold_tr_class = meeting_scaffold_rating_css_classes[meeting_approval] 
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
		html.append('''<div id='d%d' class='%s-cl %s-cl general-design-cl'>''' % (design['DesignID'], design_tr_class, scaffold_tr_class))
		html.append('''<div class='new-genbrowser-row %s'>''' % design_tr_class)
		html.append('''<span class='new-genbrowser-header'>%(Type)s</span><span><a class='gen9' href='#d%(DesignID)d'>#%(DesignID)d</a></span></div>\n''' % design)
		html.append('''<div class='new-genbrowser-row %s'>''' % scaffold_tr_class)
		
		html.append('''<span class='new-genbrowser-header'>Wildtype scaffold</span><span style='display: inline-block; width: 50px;'>#%(ComplexID)d</span>'''  % design)
		if len(pdbID) == 4:
			html.append('''<span>(<a class='gen9' target='_new' href='http://www.rcsb.org/pdb/explore.do?structureId=%(WildtypeScaffoldPDBFileID)s'>%(WildtypeScaffoldPDBFileID)s</a>, %(WildtypeScaffoldBiologicalUnit)s)</span>'''  % design)
			#html.append('''<div class='new-genbrowser-row'><span class='new-genbrowser-header'>Scaffold</span><span><a class='newgen9' href='http://www.rcsb.org/pdb/explore.do?structureId=%(WildtypeScaffoldPDBFileID)s'>%(WildtypeScaffoldPDBFileID)s</a>, %(WildtypeScaffoldBiologicalUnit)s</span></div>\n''' % design)
		else:
			html.append('''<span>(%(WildtypeScaffoldPDBFileID)s, %(WildtypeScaffoldBiologicalUnit)s)</span>'''  % design)
		html.append('''</div>\n''')

		html.append('''<div class='new-genbrowser-row'><span class='new-genbrowser-header'>Mutant complex</span><span>#%(MutantComplexID)d</span></div>\n''' % design)
		
		html.append('''<div class='new-genbrowser-row'><span class='new-genbrowser-header'>Design PDB.gz</span><span><a class='newgen9' href='?query=Gen9File&amp;DesignID=%(DesignID)d&amp;download=PDB'>Download</a></span></div>\n'''  % design)
		#html.append('''<div class='new-genbrowser-row file-links-div-%(DesignID)d' style='display:none;'><span class='new-genbrowser-header'></span><span class='gen9-filelink'>%(FilePath)s</span></div>\n''' % design)
		
		html.append('''<div class='new-genbrowser-row file-links-div-%(DesignID)d' style='display:none;'><span class='new-genbrowser-header'></span><span class='gen9-betterfilelink'>%(FilePath)s</span></div>\n''' % design)
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
		
		best_ranked_for_this_design = self.best_ranked.get(design['DesignID'], [])
		if best_ranked_for_this_design:
			for i in range(0, len(best_ranked_for_this_design), 2):
					
				### First line starts
				if i == 0:
					html.append('''<br><div class='new-genbrowser-row'><span class='new-genbrowser-header'>Scores</span>''')
				else:
					html.append('''<br><br><div class='new-genbrowser-row'><span class='new-genbrowser-header'></span>''')

				row_type = 1 + (i % 2)
				
				rank = best_ranked_for_this_design[i]
				next_rank = None
				if i+1 < len(best_ranked_for_this_design):
					next_rank = best_ranked_for_this_design[i+1] 
				
				html.append('''<span class='gen9-firstscore'>''')
				html.append('''<span class='new-genbrowser-fake-button'>Scheme %(RankingSchemeID)s, ranked #%(Rank)d</span>''' % rank)
				
				if rank['PyMOLSessionFile']:
					html.append('''<span class='Gen9PyMOL-link'><a href='?query=Gen9File&amp;DesignID=%(DesignID)d&amp;RankingSchemeID=%(RankingSchemeID)s&amp;download=PSE'><img width="18" height="18" src='../images/filesaveas128.png' alt='pdf'></a></span>''' % rank)
				html.append('''</span>''')
				
				if next_rank:
					html.append('''<span class='new-genbrowser-fake-button'>Scheme %(RankingSchemeID)s, ranked #%(Rank)d</span>''' % next_rank)
				
				if next_rank and next_rank['PyMOLSessionFile']:
					html.append('''<span class='Gen9PyMOL-link'><a href='?query=Gen9File&amp;DesignID=%(DesignID)d&amp;RankingSchemeID=%(RankingSchemeID)s&amp;download=PSE'><img width="18" height="18" src='../images/filesaveas128.png' alt='pdf'></a></span></div>\n''' % next_rank)
				else:
					html.append('''</div>\n''')
				### First line ends
				
				html.append("<div class='new-genbrowser-row'><span class='new-genbrowser-header'></span>")
				html.append("<span class='gen9-firstscore'><span><b>Total score: %f</b></span></span>" % rank['TotalScore'])
				if next_rank:
					html.append("<span><b>Total score: %f</b></span>" % next_rank['TotalScore'])
				html.append('</div>\n')
				
				html.append("<table class='new-genbrowser-score-1'><tr class='new-genbrowser-score-1'><th class='new-genbrowser-score-1'>Component</th><th class='new-genbrowser-score-1'>Score</th><th class='new-genbrowser-score-1'>C. Prob.</th></tr>")
				design_rank_components = set(rank_components[rank['RankingSchemeID']])
				score_components = gen9db.execute_select('SELECT * FROM ScoreComponent WHERE DesignID=%s ORDER BY Component', parameters=(design['DesignID'],))
				for score_component in score_components:
					CumulativeProbability = ""
					IncludedInScheme = False
					if rank_component_scores.get(DesignID, {}).get(rank['RankingSchemeID'], {}).get(score_component['Component'], {}):
						rcs = rank_component_scores[DesignID][rank['RankingSchemeID']][score_component['Component']]
						CumulativeProbability = rcs[0]
						IncludedInScheme = rcs[1]
						
					if IncludedInScheme:
						html.append("<tr style='background-color:#c9d8d5'>")
						html.append("<td><b>%(Component)s</b></td><td>%(RawScore)s</td>" % score_component)
						html.append("<td><b>%s</b></td>" % str(CumulativeProbability))
						html.append("</tr>")
					else:
						html.append("<tr style='background-color:#888888'>")
						html.append("<td>%(Component)s</td><td>%(RawScore)s</td>" % score_component)
						if CumulativeProbability:
							html.append("<td>%s</td>" % str(CumulativeProbability))
						html.append("</tr>")
				html.append("</table>\n")
				
				if next_rank:
					html.append("<table class='new-genbrowser-score-2'><tr class='new-genbrowser-score-2'><th class='new-genbrowser-score-2'>Component</th><th class='new-genbrowser-score-2'>Score</th><th class='new-genbrowser-score-2'>C. Prob.</th></tr>")
					design_rank_components = set(rank_components[next_rank['RankingSchemeID']])
					score_components = gen9db.execute_select('SELECT * FROM ScoreComponent WHERE DesignID=%s ORDER BY Component', parameters=(design['DesignID'],))
					for score_component in score_components:
						CumulativeProbability = ""
						IncludedInScheme = False
						if rank_component_scores.get(DesignID, {}).get(next_rank['RankingSchemeID'], {}).get(score_component['Component'], {}):
							rcs = rank_component_scores[DesignID][next_rank['RankingSchemeID']][score_component['Component']]
							CumulativeProbability = rcs[0]
							IncludedInScheme = rcs[1]
							
						if IncludedInScheme:
							html.append("<tr style='background-color:#c9d8d5'>")
							html.append("<td><b>%(Component)s</b></td><td>%(RawScore)s</td>" % score_component)
							html.append("<td><b>%s</b></td>" % str(CumulativeProbability))
							html.append("</tr>")
						else:
							html.append("<tr style='background-color:#888888'>")
							html.append("<td>%(Component)s</td><td>%(RawScore)s</td>" % score_component)
							if CumulativeProbability:
								html.append("<td>%s</td>" % str(CumulativeProbability))
							html.append("</tr>")
					html.append("</table>\n")
				
				if rank['PyMOLSessionFile']:
					html.append('''<div class='new-genbrowser-row file-links-div-%(DesignID)d' style='display:none;'><span class='gen9-filelink'>%(PyMOLSessionFile)s</span></div>\n''' % rank)
				if next_rank and next_rank['PyMOLSessionFile']:
					html.append('''<div class='new-genbrowser-row file-links-div-%(DesignID)d' style='display:none;'><span class='gen9-filelink'>%(PyMOLSessionFile)s</span></div>\n''' % next_rank)
					
		html.append('''<div class='new-genbrowser-row'><span class='new-genbrowser-inline-header'>Scaffold sequences</span>''')
		html.append('''</div>''')
		
		sequence_pairs = {}
		mutant_sequences = gen9db.execute_select('SELECT Chain, ProteinChain.Sequence, WildTypeChain FROM DesignMutatedChain INNER JOIN ComplexChain ON DesignMutatedChain.MutantComplexChainID=ComplexChain.ID INNER JOIN ProteinChain ON ComplexChain.ProteinChainID=ProteinChain.ID WHERE DesignID=%s', parameters=(design['DesignID'],))
		
		mutant_chain_to_wildtype_chain = {}
		wildtype_chain_to_mutant_chain = {}
		for ms in mutant_sequences:
			sequence_pairs[ms['Chain']] = [None, None, ms['Sequence']]
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
		
		design_residue_id = 1
		residue_offset = 0
		for chainID, s_pair in sorted(sequence_pairs.iteritems()):
			sub_html = []
			sub_html.append("<table class='new-gen9browser-sequences'>")
			
			motif_positions = set()
			if design_motif_residues[DesignID].get(chainID):
				motif_positions = [m[2] for m in design_motif_residues[DesignID].get(chainID)]
			if len(s_pair[0]) == len(s_pair[2]):
				
				wt_sequence = s_pair[0]
				mutant_sequence = s_pair[2]
				n = 100
				wt_subsequences = [s for s in get_subsequence(wt_sequence, n)]
				mutant_subsequences = [s for s in get_subsequence(mutant_sequence, n)]
				
				counter = '1234567890' * (len(s_pair[0])/10) + ('1234567890')[0:len(s_pair[0])%10]
				ncount = 0
				for x in range(len(wt_subsequences)):
					wt_subsequence = wt_subsequences[x]
					mutant_subsequence = mutant_subsequences[x]
					#html.append("<tr><td>        </td><td style='font-family:monospace;'>%s</td></tr>" % counter[ncount:ncount+n])
					#html.append("<tr><td>Wildtype</td><td style='font-family:monospace;'>%s</td></tr>" % wt_subsequence)
					seq1 = []
					seq2 = []
					for x in range(len(mutant_subsequence)):
						
						if wt_subsequence[x] == mutant_subsequence[x]:
							seq1.append("<span title='%s %d'>%s</span>" % (ROSETTAWEB_SK_AAinv[wt_subsequence[x]], design_residue_id, wt_subsequence[x]))
							if (ncount+x+1) in motif_positions:
								seq2.append("<span title='%s %d' class='new-genbrowser-sequence-motif-residue'>%s</span>" % (ROSETTAWEB_SK_AAinv[mutant_subsequence[x]], design_residue_id, mutant_subsequence[x]))
							else:
								seq2.append("<span title='%s %d'>%s</span>" % (ROSETTAWEB_SK_AAinv[mutant_subsequence[x]], design_residue_id, mutant_subsequence[x]))
						else:
							seq1.append("<span title='%s %d' class='new-genbrowser-sequence-wildtype-mutated'>%s</span>" % (ROSETTAWEB_SK_AAinv[wt_subsequence[x]], design_residue_id, wt_subsequence[x]))
							if (ncount+x+1) in motif_positions:
								seq2.append("<span title='%s %d' class='new-genbrowser-sequence-motif-residue'>%s</span>" % (ROSETTAWEB_SK_AAinv[mutant_subsequence[x]], design_residue_id, mutant_subsequence[x]))
							else:
								seq2.append("<span title='%s %d' class='new-genbrowser-sequence-mutant-mutated'>%s</span>" % (ROSETTAWEB_SK_AAinv[mutant_subsequence[x]], design_residue_id, mutant_subsequence[x]))
						design_residue_id += 1
					sub_html.append("<tr><td>Wildtype</td><td style='font-family:monospace;'>%s</td></tr>" % "".join(seq1))
					sub_html.append("<tr><td>Mutant</td><td style='font-family:monospace;'>%s</td></tr>" % "".join(seq2))
					ncount += n
				residue_offset += len(wt_sequence)
			
			else:
				sub_html.append("<tr><td>Mutant</td><td>Error: The length of the wildtype chain does not match what the database describes as the corresponding mutant chain.</td></tr>")
			sub_html.append("</table>")
			
			html.append('''<div class='new-genbrowser-sequence-block'>''')
			db_mutations = []
			if design_mutations.get(DesignID) and design_mutations[DesignID].get(chainID):
				db_mutations = design_mutations[DesignID][chainID]
				
				if HasSequenceLogo.get(DesignID) and chainID in HasSequenceLogo.get(DesignID):
					first_cell = '''Chain %s <a class='gen9' target="_new" href='?query=Gen9File&amp;DesignID=%d&amp;download=WebLogo&amp;Chain=%s'> <img width="42" height="18" src='../images/weblogo.png' alt='WebLogo'></a>:''' % (chainID, DesignID, chainID)
				else:
					first_cell = 'Chain %s:' % chainID
				
				html.append('''<div class='new-genbrowser-row'><span class='new-genbrowser-sequence-chain'>%s</span>''' % first_cell)
				if chain_molecule_info.get(pdbID) and chain_molecule_info[pdbID].get(mutant_chain_to_wildtype_chain[chainID]):
					html.append('''<span class="new-genbrowser-sequence-motif-residues">%s</span></div>''' % chain_molecule_info[pdbID][mutant_chain_to_wildtype_chain[chainID]])
				else:
					html.append('''<span class="new-genbrowser-sequence-motif-residues"></span></div>''')

				
				if design_motif_residues[DesignID].get(chainID):
					html.append('''<div class='new-genbrowser-row'><span class='new-genbrowser-sequence-chain'></span><span class="new-genbrowser-sequence-motif-residues">Motif residues %s</span></div>''' % (", ".join(['''<span class='new-genbrowser-sequence-motif-residue'>%s</span>''' % "".join(map(str, m[0:2])) for m in design_motif_residues[DesignID].get(chainID)])))
				#html.append('''<span title="%s" class="new-genbrowser-sequence-motif-residues">Mutations %s (%d mutations in total)</span></div>''' % (", ".join(["".join(map(str,m[0:3])) for m in db_mutations]), len(db_mutations)))
				html.append('''<div class='new-genbrowser-row'><span class='new-genbrowser-sequence-chain'></span><span title="%s" class="new-genbrowser-sequence-motif-residues">Mutations ''')
				mutations_text = ['<span title="fa_dun: %s">%s</span>' % (m[3], "".join(map(str,m[0:3]))) for m in db_mutations]
				html.append('''%s (%d mutations in total)</span></div>''' % (", ".join(mutations_text), len(db_mutations)))
			else:
				html.append('''<div class='new-genbrowser-row'><span class='new-genbrowser-sequence-chain'>Chain %s</span>''' % chainID)
				if chain_molecule_info.get(pdbID) and chain_molecule_info[pdbID].get(mutant_chain_to_wildtype_chain[chainID]):
					html.append('''<span class="new-genbrowser-sequence-motif-residues">%s</span></div>''' % chain_molecule_info[pdbID][mutant_chain_to_wildtype_chain[chainID]])
				else:
					html.append('''<span class="new-genbrowser-sequence-motif-residues"></span></div>''')
				if design_motif_residues[DesignID].get(chainID):
					html.append('''<div class='new-genbrowser-row'><span class='new-genbrowser-sequence-chain'></span><span class="new-genbrowser-sequence-motif-residues">Motif residues %s</span></div>''' % (", ".join(['''<span class='new-genbrowser-sequence-motif-residue'>%s</span>''' % "".join(map(str, m[0:2])) for m in design_motif_residues[DesignID].get(chainID)])))
				#html.append('''<span title="%s" class="new-genbrowser-sequence-motif-residues">Mutations %s (%d mutations in total)</span></div>''' % (", ".join(["".join(map(str,m[0:3])) for m in db_mutations]), len(db_mutations)))
				html.append('''<div class='new-genbrowser-row'><span class='new-genbrowser-sequence-chain'></span><span title="%s" class="new-genbrowser-sequence-motif-residues">Mutations ''')
				mutations_text = ['<span title="fa_dun: %s">%s</span>' % (m[3], "".join(map(str,m[0:3]))) for m in db_mutations]
				html.append('''%s (%d mutations in total)</span></div>''' % (", ".join(mutations_text), len(db_mutations)))
				
			html.extend(sub_html)
			html.append('''</div>''')
		
		if design_residue_data.get(DesignID):
			html.append("<div style='padding-top:10px;padding-bottom:10px;' class='new-genbrowser-row'><span class='new-genbrowser-inline-header'>Dunbrack energies, &#x3C7; angle deviations, and side-chain RMSDs upon repacking after ligand removal</span>")
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
					html.append("<td>%(WildTypeAA)s%(ResidueID)d%(MutantAA)s</td>" % residue_detail)
					if residue_detail.get('fa_dun') != None:
						html.append("<td>%(fa_dun)f</td>" % residue_detail)
					else:
						html.append("<td></td>")
					for prefix in residue_stats_headers:
						if residue_detail.get('%sSignificantChiChange' % prefix) == 0:
							html.append("<td>No</td>")
						elif residue_detail.get('%sSignificantChiChange' % prefix) == 1:
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
					html.append('''<td style='text-align:center; width:50px; font-weight:bold; color:#fff; background:%s' class='new-genbrowser-comments'>%s</td>''' % (bad_design_red, comment[2]))
				else:
					html.append('''<td style='text-align:center; width:50px; background:%s' class='new-genbrowser-comments'>%s</td>''' % (maybe_design_orange, comment[2]))
				html.append('''<td style='width:600px' class='new-genbrowser-comments'>%s</td>''' % comment[3])
				html.append('''</tr>\n''')
			html.append('''</table></div>''')
				
				#<span><a class='newgen9' href='?query=Gen9File&amp;DesignID=%(DesignID)d&amp;download=PDB'>Download</a></span></div>\n'''  % design)
		
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
					html.append('''<td style='text-align:center; width:50px; font-weight:bold; color:#fff; background:%s' class='new-genbrowser-comments'>%s</td>''' % (bad_scaffold_red, comment[2]))
				else:
					html.append('''<td style='text-align:center; width:50px; background:%s' class='new-genbrowser-comments'>%s</td>''' % (maybe_scaffold_orange, comment[2]))

				html.append('''<td style='width:600px' class='new-genbrowser-comments'>%s</td>''' % comment[3])
				html.append('''</tr>\n''')
			html.append('''</table></div>''')
		# ROW 4
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
		'MutantComplex'	: ('Design.MutantComplexID',),
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

def get_sorting_controls_html(form):
	html = []
	html.append('''<div align="left">''')
	html.append('''Order records by:''')
	html.append('''<select id='ordering1' name='new-ordering1'>
		<option value='Complex'>Complex</option>
		<option value='ID'>ID</option>
		<option value='MutantComplex'>Mutant complex</option>
		<option value='Target'>Target</option>
		<option value='Scaffold'>Scaffold</option>
		</select>''')
	html.append('''<select id='ordering2' name='new-ordering2'>
		<option value='Complex'>Complex</option>
		<option value='ID'>ID</option>
		<option value='MutantComplex'>Mutant complex</option>
		<option value='Target'>Target</option>
		<option value='Scaffold'>Scaffold</option>
		</select>''')
	html.append("""<button type='button' name='new-resort-designs' onClick='reopen_page_with_sorting();'>Sort</button>""")
	html.append('''</div>''')
	return html

def generateTablelessBrowsePage(form, filtered_DesignIDs):
	global username
	html = []
	chartfns = []
	
	profile_timer = ProfileTimer()
	profile_timer_row3 = ProfileTimer()
	
	profile_timer.start('Preamble')
	
	function_start_time = time.time()
	
	html.append('''<center><div>''')
	
	html.extend(getTablelessBrowsePageNotes())
	sorting_criteria = determine_sorting_criteria(form)
	
	# Run database queries in the iterator
	profile_timer.start('DB queries')
	designs = gen9db.execute_select("SELECT Design.ID AS DesignID, PDBBiologicalUnit.ComplexID, Design.*, SmallMolecule.Name AS SmallMoleculeName, SmallMolecule.ID AS SmallMoleculeID, SmallMoleculeMotif.Name AS TargetMotifName FROM Design INNER JOIN SmallMoleculeMotif ON TargetSmallMoleculeMotifID=SmallMoleculeMotif.ID INNER JOIN SmallMolecule ON SmallMoleculeID=SmallMolecule.ID INNER JOIN PDBBiologicalUnit ON PDBBiologicalUnit.PDBFileID=WildtypeScaffoldPDBFileID AND PDBBiologicalUnit.BiologicalUnit=WildtypeScaffoldBiologicalUnit WHERE Design.ID <> 173 ORDER BY %s" % sorting_criteria)
	hidden_designs = [173]
	designs = [design for design in designs if design["ID"] not in hidden_designs] 
	design_iterator = DesignIterator(filtered_DesignIDs)
	profile_timer.start('Postamble')
	
	html.append(generateFilterCheckboxes(username))
	
	html.append('''<H1 align="left">Designs (%s)</H1><div align="right">
</div>''' % len([design for design in designs if ((None == filtered_DesignIDs) or (filtered_DesignIDs and (design['DesignID'] in filtered_DesignIDs)))]))

	#<table style="border-style:solid; border-width:1px;">
	#<tr><td>Download PyMOL session</td><td><img width="18" height="18" src='../images/filesaveas128.png' alt='pdf'></td></tr>
	#</table>
	html.extend(get_sorting_controls_html())
	
	html.append('''<br><br>''')
	html.append(generateHidingCheckboxes())
	html.append('''<br>''')
	
	html.append('''<div class='gen9floater'>Jump to design:<input style='background:#e3eae9' onKeyPress="goToDesign(this, event)" type=text size=4 maxlength=4 name='floating-goto' value=""></div>''')
	
	profile_timer.start('For-loop start')
	
	html.append('''<div class='new-genbrowser'>''')
	
	#designs, filtered_DesignIDs
	for design in designs:
		html.extend(design_iterator.get_Design_HTML(design))
		
	profile_timer.stop()
	
	if showprofile:
		debug_log(username, "Function time: %f" % (time.time() - function_start_time))
	
	if showprofile:
		debug_log(username, "** PROFILE **")
		debug_log(username, profile_timer.getProfile())
		debug_log(username, "<br>** SUB-PROFILE ROW 3 **")
		debug_log(username, profile_timer_row3.getProfile())
		
		
	html.append('''</div>''')
	
	html.append('''<input type="hidden" NAME="query" VALUE="">''')
	html.append('''</div></center>''')

	return html, chartfns

def generateRankMappingPage(form):
	global gen9db
	
	html = []
	chartfns = []
	
	html.append('''<div>''')
	results = gen9db.execute("SELECT Design.ID AS DesignID, WildtypeScaffoldPDBFileID, WildtypeScaffoldBiologicalUnit, SmallMoleculeID, RankingSchemeID, Rank FROM Design INNER JOIN SmallMoleculeMotif ON Design.TargetSmallMoleculeMotifID=SmallMoleculeMotif.ID INNER JOIN RankedScore ON Design.ID=RankedScore.DesignID ORDER BY Design.ID")
	if results:
		html.append('''<div class="rankmapping_header"><span>Design ID#</span><span>Ranking scheme ID</span><span>Wildtype scaffold</span></div>''')
		for r in results: 
			html.append('''<div class="rankmapping">''')
			html.append('''<span onmouseover='style="cursor: pointer;"' onClick="jumpToDesign(%(DesignID)d)">%(DesignID)d</span>''' % r)
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
	
	use_security = False # This should always be True except for initial testing
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
	
	subpages = [
	{"name" : "browse",		"desc" : "Browse designs",	"fn" : generateTablelessBrowsePage,	"generate" :True,	"params" : [form, filtered_DesignIDs]},
	]
	
	subpages.append(
		{"name" : "rankmapping",		"desc" : "Rank/Design ID mapping",	"fn" : generateRankMappingPage,			"generate" :True,	"params" : [form]},
	)
	
	
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
	html.extend(initGoogleCharts(gchartfns))
#<script src="/jmol/Jmol.js" type="text/javascript"></script>
	html.append('''
<script src="/backrub/frontend/gen9.js" type="text/javascript"></script>
<script src="/javascripts/sorttable.js" type="text/javascript"></script>''')

	gen9db.close()
	rosettaweb.close()
	
	return html