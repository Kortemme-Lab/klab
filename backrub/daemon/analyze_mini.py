#!/usr/bin/env python2.4
# encoding: utf-8
"""
analyze_mini.py

Created by Florian Lauck on 2009-10-21.
Copyright (c) 2009 __UCSF__. All rights reserved.

This class analyzes the raw output of a mini run. It parses the output file and reads out the energies.

"""

import os
import sys
if __name__ == "__main__":
    sys.path.insert(0, "../common/")
import re
import time
import string
from string import join
import subprocess
import rosettahelper
import constants
		
class StructureScores(object):
	def __init__(self, filename, shortname, scores):
		self.filename = filename
		self.shortname = shortname
		self.scores = scores
				
class ComponentScore(object):
	def __init__(self, weight, rawscore, weighted_score):
		self.weight = weight
		self.rawscore = rawscore
		self.weighted_score = weighted_score
	
class AnalyzeMini(object):
	prefix = "# All scores below are weighted scores, not raw scores.\n"
	score_keys = [ 'total',
			'fa_atr', 'fa_rep', 'fa_sol', 'fa_intra_rep', 'mm_bend', 'pro_close', 
			'fa_pair', 'hbond_sr_bb', 'hbond_lr_bb', 'hbond_bb_sc', 'hbond_sc', 
			'dslf_ss_dst', 'dslf_cs_ang', 'dslf_ss_dih', 'dslf_ca_dih', 
			'rama', 'omega', 'fa_dun', 'p_aa_pp', 'ref']

	def __init__(self, filename, nstruct):
		self.nstruct = nstruct
		self.scores = []
		self._parse_file(filename)

	def _parse_file(self, filename):
		handle_in = open(filename,'r')
		
		firstline = handle_in.readline().strip()
		if firstline.startswith("core.init: command: "):
			self._parse_command(firstline)
		else:
			raise Exception("Expected core.init at the start of stdout.")
		 
		i = 1
		pdbroot = os.path.splitext(self.pdbname)[0]
		for line in handle_in:
			# if the line indicates the start of the table AND the table is for one of the LOW structures
			# then: call _read_score_table
			if line.strip() == 'apps.backrub: Score After PDB Load:':
				self.scores.append(StructureScores(self.pdbname, 'input', self._read_score_table(handle_in)))
			elif line.strip() == 'apps.backrub: Low Score:':
				id = '%04.i' % i
				lowfilename = '%s_%s_low.pdb' % (pdbroot, id) 
				self.scores.append(StructureScores(lowfilename, id, self._read_score_table(handle_in)))
				i+=1
		
		if len(self.scores) != self.nstruct + 1:
			raise Exception("Expected %d low structures but found %d scores in the stdout." % (self.nstruct, len(self.dict_scores.keys())))
		handle_in.close()
		
		self._make_totals_table()
		self._make_detailed_scores_table()
		self._make_weights_table()
		
	def _parse_command(self, firstline):
		mtchs = re.match("^.*?\s+-s\s+(.*?)\s+.*$", firstline)
		if not mtchs:
			raise Exception("Could not determine the PDB root name from stdout.")
		pdbname = os.path.split(mtchs.group(1))[1]
		self.pdbname = pdbname
		
		mtchs = re.match("^.*?\s+-nstruct\s+(\d+)\s+.*$", firstline)
		if not mtchs:
			raise Exception("Could not determine the number of structures from stdout.")
		nstruct = int(mtchs.group(1))
		if not self.nstruct == nstruct:
			raise Exception("Expected %d structures but stdout indicates that %d structures exist." % (self.nstruct, nstruct))
			
	def _read_score_table(self, handle):
		"""reads exactly one table from the buffer and returns a dictionary with the values"""
		scores = {}
		for line in handle:
			line = line.strip()
			tokens = line.split()
			if line.startswith('Total weighted score:'):
				scores['total'] = ComponentScore(1, tokens[-1], tokens[-1])
				break # the table ends after the total score and we can break
			else:
				if tokens[0] != 'Scores' and tokens[0] != 'apps.backrub:' and tokens[0][0] != '-' and tokens[0] != 'core.io.database:':
					scores[tokens[0]] = ComponentScore(tokens[1], tokens[2], tokens[3])
		return scores
	
	def analyze(self, detailed_scores_file, overall_scores_file):
		try:
			prefix = "# All scores below are weighted scores, not raw scores.\n"
			detailed_score_table = self._detailed_scores_to_string()
			overall_score_table = self._total_scores_to_string()
			if detailed_scores_file == None:
				print("")
				print(detailed_score_table)
			else:
				rosettahelper.writeFile(detailed_scores_file, detailed_score_table)
			if overall_scores_file == None:
				print("")
				print(overall_score_table)
			else:
				rosettahelper.writeFile(overall_scores_file, overall_score_table)
			print(self.total_scores_to_html(headertrstyle = "font-weight:bold"))
			
		except Exception, e:
			import traceback
			print(str(e))
			print(traceback.format_exc())
			return False
		return True

	def _make_totals_table(self):
		self.totals_table = [('Filename', 'Score')] # , 'Structure'
		for score in self.scores:
			self.totals_table.append((score.filename, score.scores['total'].weighted_score))# , score.shortname

	def _make_detailed_scores_table(self):
		self.detailed_scores_table = [['structure'] + ['%s' % key for key in self.score_keys]]
		for score in self.scores:
			self.detailed_scores_table.append([score.shortname] + ['%s' % score.scores[key].weighted_score for key in self.score_keys])

	def _make_weights_table(self):
		"""format a dict with scores into a line"""
		assert(self.score_keys[0] == "total")
		self.weights_table = [['%s' % key for key in self.score_keys[1:]]]
		self.weights_table.append(['%s' % self.scores[0].scores[key].weight for key in self.score_keys[1:]])
		
	def _table_to_string(self, tbl, field_separator = "\t", line_separator = "\n"):
		return join([join(line, field_separator) for line in tbl], line_separator)

	def _table_to_html(self, headers, data, headertitles = None, tableclass = "", tablestyle = "", headertrclass = "", headertrstyle = "", headerthclass = "", headerthstyle = "",  tdclass = "", tdstyle = "", trclass = "", trstyle = ""):
		
		if tablestyle:
			tablestyle = ' style="%s"' % tablestyle
		tableclass = ' class="sortable %s"' % (tableclass or "")
		if tdstyle:
			tdstyle = ' style="%s"' % tdstyle
		if tdclass:
			tdclass = ' class="%s"' % tdclass
		if trstyle:
			trstyle = ' style="%s"' % trstyle
		if trclass:
			trclass = ' class="%s"' % trclass
		if headertrclass:
			headertrclass = ' class="%s"' % headertrclass
		if headertrstyle:
			headertrstyle = ' style="%s"' % headertrstyle
		if headerthclass:
			headerthclass = ' class="%s"' % headerthclass
		if headerthstyle:
			headerthstyle = ' style="%s"' % headerthstyle
		html = ['''<script src="/javascripts/sorttable.js"></script>''']
		html = ["<table%(tableclass)s%(tablestyle)s>\n" % vars()]
		if headertitles:
			assert(len(headertitles) == len(headers))
			html.append("<tr%(headertrclass)s%(headertrstyle)s>" % vars())
			for x in range(len(headers)):
				if headertitles[x]:
					html.append('''<th%s%s title="%s">%s</th>''' % (headerthclass, headerthstyle, headertitles[x], headers[x]))
				else:
					html.append('''<th%s%s>%s</th>''' % (headerthclass, headerthstyle, headers[x]))
			html.append("</tr>")
		else:
			headertxt = join(headers, "</th><th%(headerthclass)s%(headerthstyle)s>" % vars())
			html.append("<tr%(headertrclass)s%(headertrstyle)s><th%(headerthclass)s%(headerthstyle)s>%(headertxt)s</th></tr>" % vars())
		if len(data) >= 1:
			contentstxt = join([join(line, "</td><td%(tdclass)s%(tdstyle)s>" % vars()) for line in data], "</td></tr>\n<tr%(trclass)s%(trstyle)s><td%(tdclass)s%(tdstyle)s>" % vars())
			html.append("<tr%(trclass)s%(trstyle)s><td%(tdclass)s%(tdstyle)s>%(contentstxt)s</td></tr>" % vars())
		html.append("\n</table>")
		return join(html)
		
	def total_scores_to_html(self, tableclass = "", tablestyle = "", headertrclass = "", headertrstyle = "", headerthclass = "", headerthstyle = "",  tdclass = "", tdstyle = "", trclass = "", trstyle = ""):
		return "%s<br><br>%s" % (self.prefix[1:].strip(), self._table_to_html(self.totals_table[0], self.totals_table[1:], tableclass = tableclass, tablestyle = tablestyle, headertrclass = headertrclass, headertrstyle = headertrstyle, headerthclass = headerthclass, headerthstyle = headerthstyle,  tdclass = tdclass, tdstyle = tdstyle, trclass = trclass, trstyle = trstyle))
	
	def _get_table_headers_for_scores(self, headers):
		titles = []
		for x in range(len(headers)):
			h = headers[x]
			if constants.rosetta_weights.get(h):
				if constants.rosetta_weights[h][0]:
					titles.append(constants.rosetta_weights[h][0])
				else:
					titles.append(None)
			else:
				titles.append(h)
		return titles
	
	def residues_scores_to_html(self, contents, tableclass = "", tablestyle = "", headertrclass = "", headertrstyle = "", headerthclass = "", headerthstyle = "",  tdclass = "", tdstyle = "", trclass = "", trstyle = ""):
		mtchs = re.findall("BEGIN_POSE_ENERGIES_TABLE(.*?)END_POSE_ENERGIES_TABLE", contents, re.DOTALL)
		html = []
		if mtchs:
			lines = mtchs[0].split("\n")
			weightsline = lines[2].split()[1:]
			headers = lines[1].split()[1:]
			if len(headers) == len(weightsline):
				titles = self._get_table_headers_for_scores(headers)
				html.append("<b>Weights</b>")
				html.append(self._table_to_html(headers, [weightsline], headertitles=titles, tableclass = tableclass, tablestyle = tablestyle, headertrclass = headertrclass, headertrstyle = headertrstyle, headerthclass = headerthclass, headerthstyle = headerthstyle,  tdclass = tdclass, tdstyle = tdstyle, trclass = trclass, trstyle = trstyle))
				html.append("<br>")
		for tbl in mtchs:
			tbl = tbl.split("\n")
			filename = tbl[0]
			weightsline = tbl[2]
			poseline = tbl[3]
			headers = ["ID"] + tbl[1].split()
			titles = self._get_table_headers_for_scores(headers)
			residues = [[line.strip().split()[0].split("_")[-1]] + line.strip().split() for line in tbl[4:] if line.strip() != "#"]
			html.append("<b>%s</b>" % filename)
			html.append(self._table_to_html(headers, residues, headertitles=titles, tableclass = tableclass, tablestyle = tablestyle, headertrclass = headertrclass, headertrstyle = headertrstyle, headerthclass = headerthclass, headerthstyle = headerthstyle,  tdclass = tdclass, tdstyle = tdstyle, trclass = trclass, trstyle = trstyle))
			html.append("<br><br>")
		return join(html, "\n")
		
	def detailed_scores_to_html(self, tableclass = "", tablestyle = "", headertrclass = "", headertrstyle = "", headerthclass = "", headerthstyle = "",  tdclass = "", tdstyle = "", trclass = "", trstyle = ""):
		html = ["<b>%s<b><br><br>" % self.prefix[1:].strip()]
		
		headers = self.detailed_scores_table[0]
		headers[0] = headers[0].title()
		headers[1] = headers[1].title()
		titles = self._get_table_headers_for_scores(headers)
		html.append(self._table_to_html(headers, self.detailed_scores_table[1:], headertitles=titles, tableclass = tableclass, tablestyle = tablestyle, headertrclass = headertrclass, headertrstyle = headertrstyle, headerthclass = headerthclass, headerthstyle = headerthstyle,  tdclass = tdclass, tdstyle = tdstyle, trclass = trclass, trstyle = trstyle))
		
		headers = self.weights_table[0]
		titles = self._get_table_headers_for_scores(headers)
		html.append('<br><b>Weights<b><br><br>')
		html.append(self._table_to_html(self.weights_table[0], self.weights_table[1:], headertitles=titles, tableclass = tableclass, tablestyle = tablestyle, headertrclass = headertrclass, headertrstyle = headertrstyle, headerthclass = headerthclass, headerthstyle = headerthstyle,  tdclass = tdclass, tdstyle = tdstyle, trclass = trclass, trstyle = trstyle))
		return join(html, "\n")

	def _total_scores_to_string(self):
		return self.prefix + self._table_to_string(self.totals_table)
	
	def _detailed_scores_to_string(self):
		tbl = [self.prefix]
		tbl.append(self._table_to_string(self.detailed_scores_table, field_separator = " "))
		tbl.append('\nWeights')
		tbl.append(self._table_to_string(self.weights_table, field_separator = " "))
		return join(tbl, "\n")
					
	# the following functions are unique to mini and n/a for classic
	# Run the score analysis on residue level, extract the scores from the pdb files and write them in individual files
	def calculate_residue_scores(self, base_dir, postprocessingBinary, databaseDir, workingdir, scores_out_fn):
		if workingdir[-1] != '/' : workingdir = workingdir+'/'
		try:
			# open scores file, this file will contain all scores for all structures
			handle = open(scores_out_fn,'w')
			handle.write("# All scores below are weighted scores, not raw scores.\n")
		
			# get files:
			files = os.listdir( workingdir )
			files.sort()
			# print files
			for fn in files:
				if re.match ('.*low.*(pdb|PDB)', fn):
					# add pairwise energies to the pdb file
					args = [ postprocessingBinary,
						 '-database', databaseDir,
						 '-s', workingdir + fn,
						 '-no_optH',
						 '-score:weights', base_dir + "data/scores.txt" ]
					print([str(arg) for arg in args], subprocess.PIPE, subprocess.PIPE, workingdir )
					
					subp = subprocess.Popen([str(arg) for arg in args], stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=workingdir )
				
					while subp.poll() == None:
						time.sleep(1)
					# # overwrite the old pdb file with the resulting pdb file that contains the scores 
					#print workingdir + fn[:-4] + '_0001' + fn[-4:], '->', workingdir+fn 
					os.rename( workingdir + fn[:-4] + '_0001' + fn[-4:], workingdir+fn )
					# extract the scores and add them to a file
					handle.write( self._extract_scores_from_PDB( workingdir+fn ) )
				
			handle.close()
		except:
			return False
			
		return True
	
	def _extract_scores_from_PDB(self, fn_in):
		'''this extracts the residue scores from the PDB file'''
		handle = open(fn_in,'r')
		read = False
		score_lines = ''
		for line in handle:
			value = line.split()
			if value[0] == '#BEGIN_POSE_ENERGIES_TABLE':
				read = True
				score_lines += value[0] + ' %s\n' % fn_in.split('/')[-1]
			elif value[0] == '#END_POSE_ENERGIES_TABLE':
				score_lines += value[0] + ' %s\n' % fn_in.split('/')[-1]
				break
			elif read:
				score_lines += line
		
		handle.close()
		return score_lines
		
 
def printUsage():
	print('usage: %s <mini Rosetta stdout file> <num_structures> <energy matrix output file> <simple score list>' % sys.argv[0])
		
if __name__ == "__main__":
	"""test"""
	energy_matrix_output_file = None
	simple_score_list = None
	nstruct = None
	if len(sys.argv) > 2:
		if not sys.argv[2].isdigit():
			printUsage()
			sys.exit(1)
		nstruct = int(sys.argv[2])
	if len(sys.argv) > 3:
		energy_matrix_output_file = sys.argv[3]
	if len(sys.argv) > 4:
		simple_score_list = sys.argv[4]
	if len(sys.argv) < 3 or len(sys.argv) > 5:
		printUsage()
		sys.exit(1)
	
	try:
		obj = AnalyzeMini(sys.argv[1], nstruct)
		if obj.analyze(energy_matrix_output_file, simple_score_list):
			print("Success!")
		else:
			print("Failure.")
		
		base_dir = "/var/www/html/rosettaweb/backrub/"
		databaseDir = os.path.join(base_dir, "data", "minirosetta_database")
		postprocessingBinary = os.path.join(base_dir, "bin", "score_jd2_r32532")
				
		if obj.calculate_residue_scores( base_dir, postprocessingBinary, databaseDir, ".", os.path.join("scores_residues.txt" ) ):
			print("Success!")
		else:
			print("Failure.")
			
				
	except Exception, e: 
		print("Failure.")
		print(str(e))
		import traceback
		print(traceback.format_exc())
		
  # obj2 = AnalyzeMini()
  # obj2.calculate_residue_scores( '/opt/rosettabackend/', 
  #                                '/opt/rosettabackend/data/minirosetta_database/', 
  #                                '/opt/lampp/htdocs/rosettaweb/backrub/downloads/a4327fe4878a9445831062d735f162d5/', 
  #                                '/opt/lampp/htdocs/rosettaweb/backrub/downloads/a4327fe4878a9445831062d735f162d5/scores_residues.txt' )
