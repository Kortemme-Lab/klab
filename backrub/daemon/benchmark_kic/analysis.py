#!/usr/bin/python
#This file was developed and written by Roland A. Pache, Ph.D., Copyright (C) 2011, 2012.
#Analyses the KIC scientific benchmark and creates a pdf report of the results.

#import libraries
import re
import os
import time
import sys
import math
import statsfns
import rosettahelper

def getEnergyStats(models):
	energies=[]
	for model in models:
		if model.id!=None:
			energies.append(model.total_energy)
	return (min(energies),statsfns.median(energies),max(energies))

def getRmsdStats(models):
	rmsds=[]
	for model in models:
		if model.id!=None:
			rmsds.append(model.loop_rms)
	return (min(rmsds),statsfns.median(rmsds),max(rmsds))

def scatterplot(outdir, sorted_models, best_model, outfile_name, top_X):
	outfile = open(outfile_name, 'w')
	outfile.write('#Model\tLoop_rmsd\tTotal_energy\n')
	energies = []
	for model in sorted_models:
		outfile.write('%s\n' % str(model))
		energies.append(model.total_energy)
	#-
	outfile.write('\n\n')
	for i in range(min(len(sorted_models), 5)):
		model = sorted_models[i]
		outfile.write('%s\n' % str(model))
		
	outfile.write('\n\n')
	outfile.write('%s\n' % str(best_model))
	outfile.close()
	eps_outfile_name = "%s_all.eps" % outfile_name.split('.')[0]
	
	title = outfile_name.split('/')[-1].split('_')[0]
	top_X_str = str(top_X)
	
	gnuplot_commands='''
set autoscale
set border 31
set tics out
set terminal postscript eps enhanced color solid "Helvetica" 24
#set size 1,1.5
#set size ratio 1
#set xtics ("default" 1, "default" 2, "H/Y" 3, "Y/H" 4, "default" 6, "default" 7, "H/Y" 8, "Y/H" 9) rotate by -45
set xtics autofreq
set xtics nomirror
set ytics autofreq
set ytics nomirror
set noy2tics
set nox2tics

set style line 1 lt rgb "dark-magenta" lw 2
set style line 2 lt rgb "blue" lw 2 ps 1 pt 7
set style line 3 lt rgb "forest-green" lw 2 ps 2 pt 13
set style line 4 lt rgb "gold" lw 2 ps 1 pt 7
set style line 5 lt rgb "red" lw 2 ps 2 pt 13
set style line 6 lt rgb "black" lw 2
set style line 7 lt rgb "dark-gray" lw 2
set style line 8 lt rgb "gray" lw 2

set boxwidth 0.75

set key top right
set xrange [0:]
set title "%(title)s"
set encoding iso_8859_1
set xlabel "r.m.s. deviation to crystal loop [{/E \305}]"
set ylabel "Rosetta all-atom score"
set output "%(eps_outfile_name)s"
plot "%(outfile_name)s" index 0 using ($2):($3) with points ls 2 title "KIC protocol (all models)" axes x1y1, "%(outfile_name)s" index 1 using ($2):($3) with points ls 4 title "KIC protocol (5 lowest energy models)" axes x1y1, "%(outfile_name)s" index 2 using ($2):($3) with points ls 5 title "KIC protocol (top %(top_X_str)s best model)" axes x1y1
''' % vars()
	
	gnuplot_scriptname = outfile_name.split('.')[0] + '.gnu'
	rosettahelper.writeFile(gnuplot_scriptname, gnuplot_commands)
	error = statsfns.Popen(outdir, ['/usr/local/bin/gnuplot', gnuplot_scriptname]).getError() # Requires gnuplot 4.2
	if error:
		raise Exception(error)
	error = statsfns.Popen(outdir, ['bash', 'epstopdf','--nocompress', eps_outfile_name]).getError() # The bash is necessary as the epstopdf script does not have a valid shebang which confuses subprocess
	if error:
		raise Exception(error)

def densityplot(outdir, sorted_models, outfile_name, num_bins):
	outfile = open(outfile_name, 'w')
	outfile.write('#Loop_rmsd\tPercentage_of_models\n')
	values = [model.loop_rms for model in sorted_models]
	histogram = statsfns.histogram(values, num_bins)
	for (bin, num_values) in histogram:
		outfile.write("%s\t%s\n" % (str(bin), str(100 * num_values/float(len(values)))))
	outfile.close()
	
	eps_outfile_name = "%s.eps" % outfile_name.split('.')[0]
	title = outfile_name.split('/')[-1].split('_')[0]
	gnuplot_commands='''
set autoscale
set border 31
set tics out
set terminal postscript eps enhanced color solid "Helvetica" 24
#set size 1,1.5
#set size ratio 1
#set xtics ("default" 1, "default" 2, "H/Y" 3, "Y/H" 4, "default" 6, "default" 7, "H/Y" 8, "Y/H" 9) rotate by -45
set xtics autofreq
set xtics nomirror
set ytics autofreq
set ytics nomirror
set noy2tics
set nox2tics

set style line 1 lt rgb "dark-magenta" lw 2
set style line 2 lt rgb "blue" lw 5 ps 1 pt 7
set style line 3 lt rgb "forest-green" lw 5 ps 2 pt 13
set style line 4 lt rgb "gold" lw 2 ps 1 pt 7
set style line 5 lt rgb "red" lw 2 ps 2 pt 13
set style line 6 lt rgb "black" lw 2
set style line 7 lt rgb "dark-gray" lw 2
set style line 8 lt rgb "gray" lw 2
set style line 9 lt 0 lc rgb "black" lw 5 ps 1 pt 7
\
set boxwidth 0.75
\
set key top right
set xrange [0:]
set title "%(title)s"
set encoding iso_8859_1
set xlabel "r.m.s. deviation to crystal loop [{/E \305}]"
set ylabel "Fraction of models [%%]"
set output "%(eps_outfile_name)s"
set arrow from 1,graph 0 to 1,graph 1 nohead ls 9
plot "%(outfile_name)s" index 0 using ($1):($2) with lines smooth bezier ls 2 title "KIC protocol (all models)" axes x1y1
''' % vars()

	gnuplot_scriptname = outfile_name.split('.')[0]+'.gnu'
	rosettahelper.writeFile(gnuplot_scriptname, gnuplot_commands)
	error = statsfns.Popen(outdir, ['/usr/local/bin/gnuplot', gnuplot_scriptname]).getError() # Requires gnuplot 4.2
	if error:
		raise Exception(error)
	error = statsfns.Popen(outdir, ['bash', 'epstopdf','--nocompress', eps_outfile_name]).getError() # The bash is necessary as the epstopdf script does not have a valid shebang which confuses subprocess
	if error:
		raise Exception(error)

		

def boxplot(outdir, models, outfile_name):
	boxplot_data = {}
	boxplot_data[1] = []
	for model in models:
		boxplot_data[1].append(model.loop_rms)
	#-
	tuples = statsfns.boxAndWhisker(boxplot_data)
	outfile = open(outfile_name, 'w')
	outfile.write('#x\tmin\tfirst_quartile\tmedian\tthird_quartile\tmax\n')
	for tuple in tuples:
		for item in tuple:
			outfile.write(str(item) + '\t')
		outfile.write('\n\n\n')
	outfile.close()
	eps_outfile_name = outfile_name.split('.')[0] + '.eps'
	gnuplot_commands ='''
set autoscale
set border 31
set tics out
set terminal postscript eps enhanced color solid "Helvetica" 24
set size ratio 1
set xtics ("KIC" 1)
set xrange [0.5:1.5]
set nox2tics
set ytics autofreq
set ytics nomirror
set noy2tics

set style line 1 lt rgb "dark-magenta" lw 2
set style line 2 lt rgb "blue" lw 5 pt 7
set style line 3 lt rgb "forest-green" lw 2
set style line 4 lt rgb "gold" lw 2
set style line 5 lt rgb "red" lw 5 pt 7
set style line 6 lt rgb "black" lw 5
set style line 7 lt rgb "dark-gray" lw 2
set style line 8 lt rgb "gray" lw 2

set boxwidth 0.25

set key tmargin
set title "Best models performance distribution"
set noxlabel
set style fill solid
set encoding iso_8859_1
set ylabel "r.m.s. deviation to crystal loop [{/E \305}]"
set output "%(eps_outfile_name)s"
plot "%(outfile_name)s" index 0 using 1:3:2:6:5 with candlesticks whiskerbars ls 2 notitle axes x1y1, "%(outfile_name)s"index 0 using 1:4:4:4:4 with candlesticks ls 6 notitle
''' % vars()
	gnuplot_scriptname=outfile_name.split('.')[0]+'.gnu'
	rosettahelper.writeFile(gnuplot_scriptname, gnuplot_commands)
	error = statsfns.Popen(outdir, ['/usr/local/bin/gnuplot', gnuplot_scriptname]).getError() # Requires gnuplot 4.2
	if error:
		raise Exception(error)
	error = statsfns.Popen(outdir, ['bash', 'epstopdf','--nocompress', eps_outfile_name]).getError()  # The bash is necessary as the epstopdf script does not have a valid shebang which confuses subprocess
	if error:
		raise Exception(error)
	

def texHeader():
	header='''
\\documentclass[a4paper,10pt]{article}
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
\\end{center}'''
	return header
