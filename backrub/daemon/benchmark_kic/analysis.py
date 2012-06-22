#!/usr/bin/python
#This file was developed and written by Shane O'Connor based on code from Roland A. Pache, Ph.D., Copyright (C) 2011, 2012.
#Analyses the KIC scientific benchmark and creates a pdf report of the results.

import os
import time
import sys
import math
import shutil
import reports.statsfns as statsfns
import rosettahelper
from string import join

class BenchmarkReport(object):
	def __init__(self, outdir, reportsettings, quiet = False, html = False):
		self.outdir = rosettahelper.makeTemp755Directory(outdir)
		self.reportsettings = reportsettings
		self.quiet = quiet
		self.html = html
		self.benchmarkRunSettings = []
		self.PDFReport = None
			
	def __del__(self):
		pass # shutil.rmtree(self.outdir)
	
	def addBenchmark(self, runID, description, flatfile, rosettaversion, rosettadbversion, commandline, benchmarkoptions, optionReplacementPatterns, passingFileContents = False):
		benchmarkRunSettings =	{
			"RunID"						: runID,
			"Description"				: description,
			"FlatfileLines"				: None,
			"RosettaSVNRevision"		: rosettaversion,
			"RosettaDBSVNRevision"		: rosettadbversion,
			"RosettaCommandLine"		: commandline,
			"Options"					: benchmarkoptions,
			"OptionReplacementPatterns" : optionReplacementPatterns,
		}
		benchmarkSettingsKeys = benchmarkRunSettings.keys()
		for k, v in benchmarkoptions.iteritems():
			assert(k not in benchmarkSettingsKeys)
			benchmarkRunSettings[k] = v
		if flatfile:
			if not passingFileContents:
				benchmarkRunSettings["FlatfileLines"] = rosettahelper.readFileLines(flatfile)
			else:
				benchmarkRunSettings["FlatfileLines"] = flatfile.split('\n')
		self.benchmarkRunSettings.append(benchmarkRunSettings)
		
	def run(self):
		if len(self.benchmarkRunSettings) == 1:
			analysis = SingleRunReport(self.outdir, self.reportsettings, self.benchmarkRunSettings[0], self.quiet, html = self.html)
		elif len(self.benchmarkRunSettings) == 2:
			analysis = ComparisonReport(self.outdir, self.reportsettings, self.benchmarkRunSettings[0], self.benchmarkRunSettings[1], quiet = self.quiet, html = self.html)
		else:
			raise Exception("Expected either one or two benchmark runs.")
		
		analysis.run()
		self.PDFReport = analysis.PDFReport
		return self.PDFReport 
		
class BenchmarkAnalyzer(object):
	placeholder_image ='/backrub/daemon/benchmark_kic/data/placeholder_image.eps'
	
	texHeader = '''
\\documentclass[a4paper,10pt]{article}

\\makeatletter
\\renewcommand\\paragraph{\\@startsection{paragraph}{4}{\\z@}%
  {-3.25ex\\@plus -1ex \\@minus -.2ex}%
  {1.5ex \\@plus .2ex}%
  {\\normalfont\\normalsize\\bfseries}}
\\makeatother

\\usepackage{a4wide}
\\usepackage[utf8]{inputenc}
\\usepackage[small,bf]{caption}
\\usepackage{times}
\\usepackage{amsmath,amsthm,amsfonts}
\\usepackage{graphicx}
\\usepackage{rotating}
\\usepackage[usenames,dvipsnames]{color}
\\usepackage{textcomp}
\\definecolor{deepblue}{rgb}{0,0,0.6}
\\usepackage[pdfpagemode=UseNone,pdfstartview=FitH,colorlinks=true,linkcolor=deepblue,urlcolor=deepblue,citecolor=black,pdftitle=KIC scientific benchmark]{hyperref} %for ideal pdf layout and hyperref
\\usepackage{booktabs}
\\usepackage{colortbl}
\\usepackage{multirow}
\\usepackage{listings}
\\usepackage[round]{natbib}
\\bibliographystyle{apalike}
\\renewcommand{\\thefootnote}{\\fnsymbol{footnote}}
\\begin{document}
\\setcounter{page}{1}
\\setcounter{footnote}{0}
\\renewcommand{\\thefootnote}{\\arabic{footnote}}

\\begin{center}
{\\huge KIC scientific benchmark}\\\\[0.5cm]
\\today
\\end{center}
'''
	
	def __init__(self, quiet, html = False):
		self.quiet = True
		if html:
			self.linebreak = "<br>"
		else:
			self.linebreak = ""
		self.PDFReport = None
		
	def log(self, *msg):
		if self.quiet:
			return
		if len(msg) == 1:
			print(msg[0])
		else:
			print(msg)
		print(self.linebreak)
	
	def gnuplot(self, gnuplot_commands, gnuplot_scriptname, eps_outfile_name):
		rosettahelper.writeFile(gnuplot_scriptname, gnuplot_commands)
		self.popen(['/usr/local/bin/gnuplot', gnuplot_scriptname])  # Requires gnuplot 4.2
		self.popen(['bash', 'epstopdf','--nocompress', eps_outfile_name]) # The bash is necessary as the epstopdf script does not have a valid shebang which confuses subprocess
		
	def popen(self, arglist, logstdout = False, logstderr = False):
		processOutput = statsfns.Popen(self.outdir, arglist)
		
		if logstdout:
			self.log("STDOUT START")
			self.log(processOutput.stdout)
			self.log("STDOUT END")
		if logstderr:
			self.log("STDERR START")
			self.log(processOutput.stderr)
			self.log("STDERR END")
		error = processOutput.getError()
		if error:
			raise Exception(error)

	def checkFileExists(self, filename):
		if not os.path.exists(os.path.join(self.outdir, filename)):
			raise Exception("%s does not exist." % filename)

from reports.SingleRun import SingleRunReport 
from reports.Comparison import ComparisonReport 


	

