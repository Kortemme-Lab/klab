#!/usr/bin/python2.4
# -*- coding: iso-8859-15 -*-

########################################
# Code for the Gen9 page
########################################

import os, re
import datetime
from datetime import date
from string import join
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

settings = None
script_filename = None
gen9db = None
userid = None

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

def generateBrowsePage(form):
	global username
	html = []
	chartfns = []
	html.append('''<center><div>''')
	html.append('''<H1 align="center">To be done: <br>-fix residue numbering<br>-add filtering<br>-add motif images</H1><br>''')
	html.append('''<H1 align="left" style='color:#005500;'>
The scaffold column is colored depending on the scaffold rating which may differ from the design rating.
<br>
Colors are based on the *worst* user rating.
<br>''')

	html.append('''<H1 align="left" style='color:#550000;'>
Mutation residue IDs use Rosetta numbering, not PDB numbering. HOWEVER, this is computed dumbly on the page<br> using sequences of strings ordered by chain ID. This is usually correct but when the PDB file contains chain B before<br> chain A, this numbering is incorrect e.g. see Design 131. This will be fixed by using Roland's script to extract the mutated<br>residues IDs and store them in the database explicitly.
</H1><br>''')
	html.append('''<H1 align="left">Designs</H1><br>''')
	
	if True:
		html.append('''
<div align="right">
<table style="border-style:solid; border-width:1px;">
<tr><td>Download PyMOL session</td><td><img width="18" height="18" src='../images/filesaveas128.png' alt='pdf'></td></tr>
</table>
</div>''')

	if False:
		a='''
	<tr><td>Show progress</td><td><img width="20" height="10" src='../images/progress-active82x30.png' alt='progress'></td></tr>
<tr><td>View stored PDF</td><td><img width="20" height="20" src='../images/pdf48.png' alt='pdf'></td></tr>
<tr><td>Regenerate PDF</td><td><img width="20" height="20" src='../images/regenerate32.png' alt='pdf'></td></tr>'''
	
	sorting_criteria = ['PDBBiologicalUnit.ComplexID', '', 'Design.ID']
	if form.has_key('gen9sort1'):
		if form['gen9sort1'].value == 'Complex':
			sorting_criteria[0] = 'PDBBiologicalUnit.ComplexID'
		elif form['gen9sort1'].value == 'ID':
			sorting_criteria[0] = 'Design.ID'
		elif form['gen9sort1'].value == 'Target':
			sorting_criteria[0] = 'SmallMoleculeID'
		elif form['gen9sort1'].value == 'Scaffold':
			sorting_criteria[0] = 'Design.WildtypeScaffoldPDBFileID'
			sorting_criteria[1] = 'Design.WildtypeScaffoldBiologicalUnit'
	if form.has_key('gen9sort2'):
		if form.has_key('gen9sort1') and (form['gen9sort1'].value == form['gen9sort2'].value):
			sorting_criteria[2] = 'PDBBiologicalUnit.ComplexID'
		else:
			if form['gen9sort2'].value == 'Complex':
				sorting_criteria[2] = 'PDBBiologicalUnit.ComplexID'
			elif form['gen9sort2'].value == 'ID':
				sorting_criteria[2] = 'Design.ID'
			elif form['gen9sort2'].value == 'Target':
				sorting_criteria[2] = 'SmallMoleculeID'
			elif form['gen9sort2'].value == 'Scaffold':
				sorting_criteria[1] = 'Design.WildtypeScaffoldPDBFileID'
				sorting_criteria[2] = 'Design.WildtypeScaffoldBiologicalUnit'
	sorting_criteria = [s for s in sorting_criteria if s]
	if sorting_criteria[0] == sorting_criteria [1]:
		sorting_criteria = sorting_criteria[1:]
	sorting_criteria = ",".join(sorting_criteria)
	
	html.append('''<div align="left">''')
	html.append('''Order records by:''')
	html.append('''<select id='ordering1' name='ordering1'>
		<option value='Complex'>Complex</option>
		<option value='ID'>ID</option>
		<option value='Target'>Target</option>
		<option value='Scaffold'>Scaffold</option>
		</select>''')
	html.append('''<select id='ordering2' name='ordering2'>
		<option value='Complex'>Complex</option>
		<option value='ID'>ID</option>
		<option value='Target'>Target</option>
		<option value='Scaffold'>Scaffold</option>
		</select>''')
	html.append("""<button type='button' name='resort-designs' onClick='reopen_page_with_sorting();'>Sort</button>""")
	html.append('''</div>''')
	
	
	html.append('''<table style="width:800px;">''')
	html.append('''<tr><td>''')
	html.append('''<table   border=1 cellpadding=4 cellspacing=0  width="1100px" style="font-size:12px;text-align:left">''')
	
	html.append("<tr style='background-color:#dddddd'>")
	#style='width:100px;'
	html.append("<th>ID</th><th>Complex</th><th style='width:50px;'>Type</th><th style='width:50px;'>File</th><th>Target</th><th style='width:50px;'>Scaffold</th><th style='width:250px;'>List of best designs resp. best relaxed designs (enzdes weights)</th><th style='width:50px;'>Comments</th>")
	html.append("</tr>")
	
	#benchmark_details['BenchmarkRuns'] = gen9db.execute("SELECT ID, BenchmarkID, RunLength, RosettaSVNRevision, RosettaDBSVNRevision, RunType, CommandLine, BenchmarkOptions, ClusterQueue, ClusterArchitecture, ClusterMemoryRequirementInGB, ClusterWalltimeLimitInMinutes, NotificationEmailAddress, EntryDate, StartDate, EndDate, Status, AdminCommand, Errors FROM BenchmarkRun ORDER BY ID")
	motif_residues = {}
	results = gen9db.execute("SELECT * FROM SmallMoleculeMotifResidue ORDER BY ResidueID")
	for r in results:
		motif_residues[r["SmallMoleculeMotifID"]] = motif_residues.get(r["SmallMoleculeMotifID"], (r['PDBFileID'], []))
		motif_residues[r["SmallMoleculeMotifID"]][1].append("%(Chain)s:%(ResidueID)s" % r)
	
	best_ranked = {}
	results = gen9db.execute("SELECT * FROM RankedScore WHERE MarkedAsBest=1")
	for r in results:
		best_ranked[r['DesignID']] = best_ranked.get(r['DesignID'], [])
		best_ranked[r['DesignID']].append(r)

	sequence_matches = {}
	results = gen9db.execute("SELECT * FROM DesignSequenceMatch")
	for r in results:
		sequence_matches[r['DesignID']] = sequence_matches.get(r['DesignID'], {})
		sequence_matches[r['DesignID']][r['WildtypeScaffoldChain']] = sequence_matches[r['DesignID']].get(r['WildtypeScaffoldChain'], {})
		sequence_matches[r['DesignID']][r['WildtypeScaffoldChain']] = r['Matchtype']
	
	rank_components = {}
	results = gen9db.execute("SELECT DISTINCT RankingSchemeID, Component FROM RankedScoreComponent")
	for r in results:
		rank_components[r['RankingSchemeID']] = rank_components.get(r['RankingSchemeID'], [])
		rank_components[r['RankingSchemeID']].append(r['Component'])
	
	for rank_scheme in rank_components.keys():
		rank_components[rank_scheme] = sorted(rank_components[rank_scheme])
	
	designs = gen9db.execute("SELECT Design.ID AS DesignID, PDBBiologicalUnit.ComplexID, Design.*, SmallMolecule.Name AS SmallMoleculeName, SmallMolecule.ID AS SmallMoleculeID, SmallMoleculeMotif.Name AS TargetMotifName FROM Design INNER JOIN SmallMoleculeMotif ON TargetSmallMoleculeMotifID=SmallMoleculeMotif.ID INNER JOIN SmallMolecule ON SmallMoleculeID=SmallMolecule.ID INNER JOIN PDBBiologicalUnit ON PDBBiologicalUnit.PDBFileID=WildtypeScaffoldPDBFileID AND PDBBiologicalUnit.BiologicalUnit=WildtypeScaffoldBiologicalUnit ORDER BY %s" % sorting_criteria)
	
	UserScaffoldRatings = {}
	UserScaffoldTerminiOkay = {}
	results = gen9db.execute("SELECT UserScaffoldRating.*, User.FirstName FROM UserScaffoldRating INNER JOIN User ON UserID=User.ID")
	for r in results:
		key = r['ComplexID']
		UserScaffoldRatings[key] = UserScaffoldRatings.get(key, {})
		UserScaffoldRatings[key][r['UserID']] = r
		if r['TerminiAreOkay']:
			UserScaffoldTerminiOkay[key] = r['TerminiAreOkay']
	
	for design in designs:
		UserDesignRatings = gen9db.execute("SELECT * FROM UserDesignRating INNER JOIN User ON UserID=User.ID WHERE DesignID=%s ORDER BY FirstName", parameters=(design['DesignID'],))
		
		# Determine main row color based on ratings
		design_color = '#cccccc'
		bad_design = False
		okay_design = False
		good_design = False
		for r in UserDesignRatings:
			if r['Rating'] == 'Bad':
				bad_design = True
			elif r['Rating'] == 'Good':
				good_design = True
			elif r['Rating'] == 'Maybe':
				okay_design = True
			else:
				# if no rating is given, assume a good rating
				good_design = True
		if bad_design:
			design_color = '#FF4D4D'
		elif okay_design:
			design_color = '#FFCC00'
		elif good_design:
			design_color = '#00CC00'
		
		# Determine scaffold color based on ratings
		scaffold_color = '#cccccc'
		bad_scaffold = False
		okay_scaffold = False
		good_scaffold = False
		no_rating = False
		if UserScaffoldRatings.get(design['ComplexID']):
			for user_id, scaffold_rating in UserScaffoldRatings[design['ComplexID']].iteritems():
				if scaffold_rating['Rating'] == 'Bad':
					bad_scaffold = True
				elif scaffold_rating['Rating'] == 'Good':
					good_scaffold = True
				elif scaffold_rating['Rating'] == 'Maybe':
					okay_scaffold = True
				elif user_id == 'huangy2':
					no_rating = True
				else:
					# if no rating is given, assume a good rating
					good_design = True
			if bad_scaffold:
				scaffold_color = '#FF4D4D'
			elif okay_scaffold:
				scaffold_color = '#FFCC00'
			elif good_scaffold:
				scaffold_color = '#00CC00'
			
		# Create an anchor to the row
		html.append("<tr id='%d' style='background-color:%s'>" % (design['DesignID'], design_color))
		
		html.append("<td>%(DesignID)d</td>" % design)
		html.append("<td>%(ComplexID)d</td>" % design)
		html.append("<td>%(Type)s</td>" % design)
		
		# File links
		if design['FilePath']:
			html.append("<td><a href='?query=Gen9File&amp;DesignID=%(DesignID)d&amp;download=PDB'>link</a></td>" % design)
		else:
			html.append("<td></td>")
		
		motif_info = motif_residues[design['TargetSmallMoleculeMotifID']]
		motif_info = "%s<br>%s" % (motif_info[0], ",".join(motif_info[1]))
		design['motif_info'] = motif_info
					
		html.append("<td>%(SmallMoleculeName)s<br>%(SmallMoleculeID)s<br>%(TargetMotifName)s<br>%(motif_info)s</td>" % design)
		
		html.append("<td style='background-color:%s'>" % scaffold_color)
		html.append("%(WildtypeScaffoldPDBFileID)s<br>%(WildtypeScaffoldBiologicalUnit)s</td>" % design)
		
		# Scores
		colors = ['#eeeeee', '#dddddd']
		html.append("<td><table style='border-collapse: collapse;'>")
		colorcode = 0
		for rank in best_ranked.get(design['DesignID'], []):
			href_html = ""
			if rank['PyMOLSessionFile']:
				href_html = '''<a href='?query=Gen9File&amp;DesignID=%(DesignID)d&amp;RankingSchemeID=%(RankingSchemeID)s&amp;download=PSE'><img width="18" height="18" src='../images/filesaveas128.png' alt='pdf'></a>''' % rank
			
			html.append("<tr style='background-color:%s'>" % colors[colorcode])
			html.append("<td style='border: 1px solid black;'>%s_%s_%s &nbsp;&nbsp; %s</td>" % (design['SmallMoleculeID'], rank['RankingSchemeID'], rank['Rank'], href_html))
			html.append("</tr>")
			
			html.append("<tr style='background-color:%s'>" % colors[colorcode])
			html.append("<td style='border: 1px solid black;'>Total score</td><td style='border: 1px solid black;'>%f</td>" % rank['TotalScore'])
			html.append("</tr>")
			
			design_rank_components = rank_components[rank['RankingSchemeID']]
			if len(design_rank_components) == 1:
				score_components = gen9db.execute('SELECT * FROM ScoreComponent WHERE DesignID=%d AND Component IN ("%s") ORDER BY Component' % (design['DesignID'], design_rank_components[0]))
			else:
				score_components = gen9db.execute('SELECT * FROM ScoreComponent WHERE DesignID=%d AND Component IN %s ORDER BY Component' % (design['DesignID'], str(tuple(design_rank_components))))
			
			for score_component in score_components:
				html.append("<tr style='background-color:%s'>" % colors[colorcode])
				html.append("<td style='border: 1px solid black;'>%(Component)s</td><td style='border: 1px solid black;'>%(RawScore)s</td>" % score_component)
				html.append("</tr>")
			
			colorcode = (colorcode + 1) % 2
			
		html.append("</table></td>")
		
		html.append("<td style='vertical-align:top;'><b>Design comments</b><br><div style='width:20px;'></div>")
		if UserDesignRatings:
			html.append("<table style='border-collapse: collapse;'>")
			for user_rating in UserDesignRatings:
				# Hide empty ratings
				if user_rating['Rating'] or user_rating['RatingNotes']:
					html.append("<tr style='background-color:%s'>" % colors[1])
					if user_rating['FirstName'] == 'Yao-ming':
						html.append("<td style='width:65px;border: 1px solid black;'>Ming</td>")
					else:
						html.append("<td style='width:65px;border: 1px solid black;'>%s</td>" % user_rating['FirstName'])
					html.append("<td style='border: 1px solid black;'>%s</td>" % user_rating['Rating'])
					html.append("<td style='border: 1px solid black;'>%s</td>" % user_rating['RatingNotes'])
					html.append("</tr>")
			html.append("</table>")
		html.append("</td>")
		
		html.append("</tr>")
		
		html.append("<tr style='background-color:#CCE0F5'><td>%(DesignID)s</td>" % design)
		html.append("<td>%(ComplexID)d</td>" % design)
		html.append("<td COLSPAN='5'>")
		html.append("<b>Scaffold sequences<br><br></b>")
		
		#if design['SequenceMatches'] == 'ATOM':
		#	html.append('<b style="color:#885500">Note: The ATOM records of the PDB file are missing residues listed in the SEQRES records.</b><br><br>')
		
		sequence_pairs = {}
		mutant_sequences = gen9db.execute('SELECT Chain, ProteinChain.Sequence FROM DesignMutatedChain INNER JOIN ComplexChain ON DesignMutatedChain.MutantComplexChainID=ComplexChain.ID INNER JOIN ProteinChain ON ComplexChain.ProteinChainID=ProteinChain.ID WHERE DesignID=%s', parameters=(design['DesignID'],))
		for ms in mutant_sequences:
			sequence_pairs[ms['Chain']] = [None, None, ms['Sequence']]
			matchtype = gen9db.execute('SELECT Matchtype FROM DesignSequenceMatch WHERE DesignID=%s AND WildtypeScaffoldChain=%s', parameters=(design['DesignID'], ms['Chain']))
			assert(len(matchtype) == 1)
			matchtype = matchtype[0]['Matchtype']
			sequence_pairs[ms['Chain']][1] = matchtype
		
		wildtype_sequences = gen9db.execute('SELECT PDBBiologicalUnit.PDBFileID, PDBBiologicalUnitChain.Chain AS Chain, ProteinChain.Sequence AS Sequence FROM PDBBiologicalUnit INNER JOIN PDBBiologicalUnitChain ON PDBBiologicalUnit.PDBFileID=PDBBiologicalUnitChain.PDBFileID AND PDBBiologicalUnit.BiologicalUnit=PDBBiologicalUnitChain.BiologicalUnit INNER JOIN PDBChain ON PDBBiologicalUnitChain.PDBFileID=PDBChain.PDBFileID AND PDBBiologicalUnitChain.Chain=PDBChain.Chain INNER JOIN ProteinChain ON PDBChain.ProteinChainID=ProteinChain.ID WHERE PDBBiologicalUnit.PDBFileID=%s AND PDBBiologicalUnit.BiologicalUnit=%s', parameters=(design['WildtypeScaffoldPDBFileID'], design['WildtypeScaffoldBiologicalUnit']))
		
		seqres_wildtype_sequences = gen9db.execute('SELECT PDBBiologicalUnit.PDBFileID, PDBBiologicalUnitChain.Chain AS Chain, ProteinChain.Sequence AS Sequence FROM PDBBiologicalUnit INNER JOIN PDBBiologicalUnitChain ON PDBBiologicalUnit.PDBFileID=PDBBiologicalUnitChain.PDBFileID AND PDBBiologicalUnit.BiologicalUnit=PDBBiologicalUnitChain.BiologicalUnit INNER JOIN PDBChain ON PDBBiologicalUnitChain.PDBFileID=PDBChain.PDBFileID AND PDBBiologicalUnitChain.Chain=PDBChain.Chain INNER JOIN ProteinChain ON PDBChain.ProteinChainID=ProteinChain.ID WHERE PDBBiologicalUnit.PDBFileID=%s AND PDBBiologicalUnit.BiologicalUnit=%s', parameters=(design['WildtypeScaffoldPDBFileID'], design['WildtypeScaffoldBiologicalUnit']))
		atom_wildtype_sequences   = gen9db.execute('SELECT PDBBiologicalUnit.PDBFileID, PDBBiologicalUnitChain.Chain AS Chain, ProteinChain.Sequence AS Sequence FROM PDBBiologicalUnit INNER JOIN PDBBiologicalUnitChain ON PDBBiologicalUnit.PDBFileID=PDBBiologicalUnitChain.PDBFileID AND PDBBiologicalUnit.BiologicalUnit=PDBBiologicalUnitChain.BiologicalUnit INNER JOIN PDBChain ON PDBBiologicalUnitChain.PDBFileID=PDBChain.PDBFileID AND PDBBiologicalUnitChain.Chain=PDBChain.Chain INNER JOIN ProteinChain ON PDBChain.EffectiveProteinChainID=ProteinChain.ID WHERE PDBBiologicalUnit.PDBFileID=%s AND PDBBiologicalUnit.BiologicalUnit=%s', parameters=(design['WildtypeScaffoldPDBFileID'], design['WildtypeScaffoldBiologicalUnit']))
		
		for wtsequence in seqres_wildtype_sequences:
			if sequence_pairs.get(wtsequence['Chain']) and sequence_pairs[wtsequence['Chain']][1] == 'SEQRES':
				sequence_pairs[wtsequence['Chain']][0] = wtsequence['Sequence']
		for wtsequence in atom_wildtype_sequences:
			if sequence_pairs.get(wtsequence['Chain']) and sequence_pairs[wtsequence['Chain']][1] == 'ATOM':
				sequence_pairs[wtsequence['Chain']][0] = wtsequence['Sequence']
		
		for chainID, sp in sequence_pairs.iteritems():
			assert(sp[0])
			assert(sp[1])
			assert(sp[2])
		
		residue_offset = 0
		for chainID, s_pair in sorted(sequence_pairs.iteritems()):
			mutation_residueIDs = []
			sub_html = []
			sub_html.append("<table>")
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
							seq1.append(wt_subsequence[x])
							seq2.append(mutant_subsequence[x])
						else:
							mutation_residueIDs.append({'Chain' : chainID, 'ResidueID' : residue_offset + ncount + x + 1, 'WildTypeAA' : wt_subsequence[x], 'MutantAA' : mutant_subsequence[x]})
							seq1.append("<span style='background-color:#00dd00;'><font color='#003300'>%s</font></span>" % wt_subsequence[x])
							seq2.append("<span style='background-color:#ffff00;'><font color='#990099'>%s</font></span>" % mutant_subsequence[x])
					sub_html.append("<tr><td>Wildtype</td><td style='font-family:monospace;'>%s</td></tr>" % "".join(seq1))
					sub_html.append("<tr><td>Mutant</td><td style='font-family:monospace;'>%s</td></tr>" % "".join(seq2))
					ncount += n
				residue_offset += len(wt_sequence)
			
			else:
				sub_html.append("<tr><td>Mutant</td><td>Error: The length of the wildtype chain does not match what the database describes as the corresponding mutant chain.</td></tr>")
			sub_html.append("</table>")

			if mutation_residueIDs:
				html.append('<b>Chain %s: Mutations %s (%d mutations in total)</b><br>' % (chainID, ", ".join(["%(WildTypeAA)s%(ResidueID)s%(MutantAA)s" % m for m in mutation_residueIDs]), len(mutation_residueIDs)))
			else:
				html.append('<b>Chain %s</b><br>' % chainID)
			html.extend(sub_html)
			
		html.append("</td>")
		html.append("<td style='vertical-align:top;' >")
		html.append("<b>Scaffold comments<br></b>")
		
		key = design['ComplexID']
		if UserScaffoldRatings.get(key) or UserScaffoldTerminiOkay.get(key):
			html.append("<table style='border-collapse: collapse;'>")
			for user, user_rating in sorted(UserScaffoldRatings[key].iteritems()):
				if user_rating['Rating']:
					html.append("<tr style='background-color:%s'>" % colors[1])
					if user_rating['FirstName'] == 'Yao-ming':
						html.append("<td style='width:65px;border: 1px solid black;'>Ming</td>")
					else:
						html.append("<td style='width:65px;border: 1px solid black;'>%s</td>" % user_rating['FirstName'])
					html.append("<td style='border: 1px solid black;'>%s</td>" % user_rating['Rating'])
					html.append("<td style='border: 1px solid black;'>%s</td>" % user_rating['RatingNotes'])
					html.append("</tr>")
			if UserScaffoldTerminiOkay.get(key):
				html.append("<tr style='background-color:%s'><td style='width:65px;border: 1px solid black;'>TerminiOkay?</td><td style='border: 1px solid black;'>%s</td></tr>" % (colors[1], UserScaffoldTerminiOkay[key]))
				
			html.append("</table>")
		
		
		html.append("</td>")
		html.append("</tr>")
		
		if username:
			html.append("<tr><td>%(DesignID)s</td>" % design)
			html.append("<td>%(ComplexID)d</td>" % design)
			html.append("<td COLSPAN='6'>")
			html.append('''<FORM name="gen9form-%(DesignID)d" method="post">''' % design)
			html.append('''<input type="hidden" NAME="DesignID" VALUE="%(DesignID)d">''' % design)
			html.append('''<input type="hidden" NAME="Username" VALUE="%s">''' % username)
			html.append('''<input type="hidden" NAME="Gen9Page" VALUE="">''')
			html.append('''<input type="hidden" NAME="query" VALUE="">''')
			html.append('''<input type="hidden" NAME="gen9sort1" VALUE="">''')
			html.append('''<input type="hidden" NAME="gen9sort2" VALUE="">''')
	
			html.append("<table>")
			
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
			
			html.append("<tr><td>Design rating:</td><td><select name='user-design-rating-%d'>" % design['DesignID'])
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
			html.append("</select></td></tr>")
			if user_design_comments:
				html.append("""<tr><td>Comments on the design:</td><td><input type=text size=100 maxlength=300 name='user-design-comments-%d' value="%s"></td></tr>""" % (design['DesignID'], user_design_comments.replace('"',"'")))
			else:
				html.append("""<tr><td>Comments on the design:</td><td><input type=text size=100 maxlength=300 name='user-design-comments-%d' value=""></td></tr>""" % (design['DesignID']))
			
			html.append("""<tr><td></td></tr>""")
			##
			
			html.append("<tr><td>Scaffold rating:</td><td><select name='user-scaffold-rating-%d'>" % design['DesignID'])
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
			html.append("</select></td></tr>")
			
			if user_scaffold_comments:
				html.append("""<tr><td>Comments on the scaffold:</td><td><input type=text size=100 maxlength=300 name='user-scaffold-comments-%d' value="%s"></td></tr>""" % (design['DesignID'], user_scaffold_comments.replace('"',"'")))
			else:
				html.append("""<tr><td>Comments on the scaffold:</td><td><input type=text size=100 maxlength=300 name='user-scaffold-comments-%d' value=""></td></tr>""" % (design['DesignID']))
			
			
			html.append("""<tr><td><button type='submit' name='user-comments-submit-%d' onClick='copyPageFormValues(this);'>Submit comments</button></td></tr>""" % design['DesignID'])
			html.append("</table>")
			html.append('''</FORM>''') 
			html.append("</td>")
			
			html.append("</tr>")
		
	html.append('''</table>''')
	html.append('''</td></tr>''')
	html.append('''</table>''')
	html.append('''<input type="hidden" NAME="benchmarkrunID" VALUE="">''')
	html.append('''<input type="hidden" NAME="query" VALUE="">''')
	html.append('''<input type="hidden" NAME="BenchmarksPage" VALUE="">''')
	html.append('''<input type="hidden" NAME="BenchmarksType" VALUE="">''')
	html.append('''<input type="hidden" NAME="Benchmark1Name" VALUE="">''')
	html.append('''<input type="hidden" NAME="Benchmark2Name" VALUE="">''')
	html.append('''<input type="hidden" NAME="Benchmark1ID" VALUE="">''')
	html.append('''<input type="hidden" NAME="Benchmark2ID" VALUE="">''')
	html.append('''</div></center>''')
	
	return html, chartfns


def generateGen9Page(settings_, rosettahtml, form, userid_, Gen9Error):
	global gen9db
	gen9db = rosettadb.DatabaseInterface(settings_, host = "kortemmelab.ucsf.edu", db = "Gen9Design")
	rosettaweb = rosettadb.DatabaseInterface(settings_, host = "localhost", db = "rosettaweb")

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
		results = rosettaweb.execute('SELECT UserName FROM Users WHERE ID=%s', parameters= (userid_,))
		if len(results) == 1:
			username = results[0]['UserName']
		if username in ['oconchus', 'kortemme', 'rpache', 'kyleb', 'huangy2', 'noah', 'amelie']:
			has_access = True
		else:
			username = None
	if use_security and not has_access:
		html.append('Guests do not have access to this page. Please log in.</tr>')
		return html
	
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
		{"name" : "browse",		"desc" : "Browse designs",				"fn" : generateBrowsePage,			"generate" :True,	"params" : [form]},
		]
	
	# Create menu
	
	html.append("<td align=center>")
	html.append('''<FORM name="gen9form" method="post">''')
	
	for subpage in subpages:
		if subpage["generate"]:
			html.append('''<input type="button" value="%(desc)s" onClick="showPage('%(name)s');">''' % subpage)
	
	html.append('''<input type="button" value="Refresh" onClick="document.gen9form.query.value='Gen9'; document.gen9form.submit();">''')
	html.append('''<input type="hidden" NAME="Gen9Page" VALUE="%s">''' % Gen9Page)
	html.append('''<input type="hidden" NAME="query" VALUE="">''')
	html.append('''<input type="hidden" NAME="gen9sort1" VALUE="%s">''' % gen9sort1)
	html.append('''<input type="hidden" NAME="gen9sort2" VALUE="%s">''' % gen9sort2)
	
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

	return html