#!/usr/bin/python
#This file was edited/added to by Shane O'Connor from files developed and written by Roland A. Pache, Ph.D., Copyright (C) 2011, 2012.
#Analyses the KIC scientific benchmark and creates a pdf report of the results.

import re
import os
import time
import sys
import math
import shutil
import statsfns
import rosettahelper
from benchmark_kic.analysis import BenchmarkAnalyzer
from string import join

class SingleRunReport(BenchmarkAnalyzer):
	
	def __init__(self, outdir, reportSettings, benchmarkRunSettings, quiet = False, html = False):
				
		super(SingleRunReport, self).__init__(quiet, html)
		self.outdir = outdir
		self.reportSettings = reportSettings
		self.benchmarkRunSettings = benchmarkRunSettings
		self.num_models_per_run = benchmarkRunSettings['Options']['NumberOfModelsPerPDB']
		self.num_bins = reportSettings['NumberOfBins']
		self.top_X = reportSettings['TopX']
		self.quiet = quiet
		
	def getEnergyStats(self, models):
		energies=[]
		for model in models:
			if model.id!=None:
				energies.append(model.total_energy)
		return (min(energies),statsfns.median(energies),max(energies))
	
	def getRmsdStats(self, models):
		rmsds=[]
		for model in models:
			if model.id!=None:
				rmsds.append(model.loop_rms)
		return (min(rmsds),statsfns.median(rmsds),max(rmsds))
	
	def scatterplot(self, sorted_models, best_model, outfile_name, top_X):
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
		
		self.gnuplot(gnuplot_commands, outfile_name.split('.')[0] + '.gnu', eps_outfile_name)
	
	def densityplot(self, sorted_models, outfile_name):
		outfile = open(outfile_name, 'w')
		outfile.write('#Loop_rmsd\tPercentage_of_models\n')
		values = [model.loop_rms for model in sorted_models]
		histogram = statsfns.histogram(values, self.num_bins)
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
	
		self.gnuplot(gnuplot_commands, outfile_name.split('.')[0] + '.gnu', eps_outfile_name)

	def boxplot(self, models, outfile_name):
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
	
		self.gnuplot(gnuplot_commands, outfile_name.split('.')[0] + '.gnu', eps_outfile_name)

	def generateBenchmarkDetailsTex(self):
		if self.benchmarkRunSettings['RosettaDBSVNRevision'] != self.benchmarkRunSettings['RosettaSVNRevision']:
			self.benchmarkRunSettings['DBDescription'] = ' (Rosetta database version %s)' % self.benchmarkRunSettings['RosettaDBSVNRevision']
		else:
			self.benchmarkRunSettings['DBDescription'] = ''
		
		commandLine = self.benchmarkRunSettings['RosettaCommandLine']
		for Option, d in self.benchmarkRunSettings['OptionReplacementPatterns'].iteritems():
			commandLine = re.sub("%%[(]%s[)]\w" % d['Pattern'], str(self.benchmarkRunSettings['Options'][Option]), commandLine)
		self.benchmarkRunSettings['RosettaSplitCommandLine'] = statsfns.breakCommandLine(commandLine) 
		
		return '''
\\paragraph{Benchmark run %(RunID)d \\textnormal{Rosetta version %(RosettaSVNRevision)s%(DBDescription)s}}
\\begin{lstlisting}
%(RosettaSplitCommandLine)s
\\end{lstlisting}
		''' % self.benchmarkRunSettings

	def generateBenchmarkOptionsTex(self):
		LaTeX = '''
\\paragraph{Options}
\\begin{tabular}{ll}
'''
		for option, value in self.benchmarkRunSettings['Options'].iteritems():
			if self.benchmarkRunSettings['OptionReplacementPatterns'][option]['ShowInReport']:
				LaTeX += "%s & %s \\\\\n" % (self.benchmarkRunSettings['OptionReplacementPatterns'][option]['Description'], value)	
		LaTeX += "\\end{tabular}\n"
		return LaTeX
		
	def run(self):
		num_models_offset = self.benchmarkRunSettings['Options']["NumberOfModelsOffset"]
		num_models_per_PDB = self.benchmarkRunSettings['Options']["NumberOfModelsPerPDB"]
		top_X = self.top_X

		# Parse models
		pdb_models = {} # PDB ID -> List[Model] 
		start_index = num_models_offset + 1
		end_index = num_models_offset + num_models_per_PDB
		total_runtime = 0
		for line in self.benchmarkRunSettings['FlatfileLines']:
			#self.log(line)
			if not line.startswith('#'):
				data = line.strip('\n').split('\t')
				#self.log(data)
				if len(data) > 4:
					pdb = data[0]
					pdb_models[pdb] = pdb_models.get(pdb, [])
					model_index = int(data[1])
					if model_index >= start_index and model_index <= end_index:
						runtime = int(data[4])
						model = statsfns.Model(pdb, model_index, float(data[2]), float(data[3]), runtime)
						pdb_models[pdb].append(model)
						total_runtime += runtime
						#self.log(total_runtime)
				
		if total_runtime != 0:
			self.log('Total runtime [hours]: %d' % int(total_runtime/float(3600)))
		
		self.log("here")
		self.log(self.outdir)
		self.log("there")
		
		# Compute basic statistics and create RMSD vs. Rosetta score plots per PDB
		tex_tables = []
		best_models = []
		closest_models = []
		sorted_pdb_ids = sorted(pdb_models.keys())
		self.log("%d PDBs" % len(sorted_pdb_ids))
		
		# Init results tex table
		tex_table_string = ['''
\\begin{tabular}{rr|rrr|rrr}
PDB &\# models &Top %(top_X)d best model &Loop rmsd &Energy &Closest model &Loop rmsd &Energy\\\\\\hline
	''' % vars()]
		for pdb in sorted_pdb_ids:
			self.log(pdb)
			models = pdb_models[pdb]
			self.log('%d successful models' % len(models))
			#determine best and closest model for the given pdb
			models_sorted_by_energy = sorted(models, lambda x, y: cmp(x.total_energy, y.total_energy))
			models_sorted_by_rmsd = sorted(models, lambda x, y: cmp(x.loop_rms, y.loop_rms))
			best_model = models_sorted_by_energy[0]
			
			# When looking for the best model, consider the top X lowest energy models and pick the one with lowest rmsd
			for i in range(top_X):
				if i < len(models_sorted_by_energy):
					best_model_candidate = models_sorted_by_energy[i] # here
					if best_model_candidate.loop_rms < best_model.loop_rms:
						best_model = best_model_candidate
			#--
			closest_model = models_sorted_by_rmsd[0]
			self.log('Best model of the top %d (i.e. lowest RMSD of top %d lowest energy models): %s, %f, %f' % (top_X, top_X, best_model.id, best_model.loop_rms, best_model.total_energy))
			self.log('Closest model (i.e. lowest RMSD): %s, %f, %f' % (closest_model.id, closest_model.loop_rms, closest_model.total_energy))
			best_models.append(best_model)
			closest_models.append(closest_model)
			#create scatterplot for each pdb
	
			outfile_name = os.path.join(self.outdir, '%s_models.out' % pdb)
			self.scatterplot(models_sorted_by_energy, best_model, outfile_name, top_X)
			outfile_name = os.path.join(self.outdir, '%s_density.out' % pdb)
			self.densityplot(models_sorted_by_energy, outfile_name)
			
			# Store data in results tex table
			tex_table_string.append('%s ' % pdb)
			tex_table_string.append('&%d ' % len(models))
			tex_table_string.append('&%s ' % best_model.runID)
			tex_table_string.append('&%0.2f ' % best_model.loop_rms)
			tex_table_string.append('&%0.2f' % best_model.total_energy)
			tex_table_string.append('&%s ' % closest_model.runID)
			tex_table_string.append('&%0.2f ' % closest_model.loop_rms) 
			tex_table_string.append('&%0.2f\\\\\n' % closest_model.total_energy)
		
		#write results tex table
		tex_table_string.append('\\end{tabular}\n')
		tex_table_string = join(tex_table_string, "")
		tex_outfile_name = os.path.join(self.outdir, 'results.tex')
		tex_tables.append(tex_outfile_name)
		rosettahelper.writeFile(tex_outfile_name, tex_table_string)
		
		self.log(tex_outfile_name)
		
		#create rmsd boxplot for the best models
		boxplot_outfile_name = os.path.join(self.outdir, 'best_models_rmsd_dist.out')
		self.boxplot(best_models, boxplot_outfile_name)
		self.log(self.outdir)
		self.log(boxplot_outfile_name)
		
		#calculate global stats across all pdbs and write overall performance tex table
		self.log('Global statistics (median rmsd and energy):')
		outfile_name = os.path.join(self.outdir, 'global_results.tex')
		tex_tables.append(outfile_name)
		best_models_median_energy = round(self.getEnergyStats(best_models)[1], 2)
		best_models_median_rmsd = round(self.getRmsdStats(best_models)[1], 2)
		closest_models_median_energy = round(self.getEnergyStats(closest_models)[1], 2)
		closest_models_median_rmsd = round(self.getRmsdStats(closest_models)[1], 2)
		self.log('best models median rmsd and energy: %f\t%f' % (best_models_median_rmsd, best_models_median_energy))
		self.log('closest models median rmsd and energy: %f\t%f' % (closest_models_median_rmsd, closest_models_median_energy))
		outstring = '''
\\begin{tabular}{lrr}
Model selection &Median loop rmsd &Median energy\\\\\\hline
{\\bf Top %(top_X)d best model} &{\\bf %(best_models_median_rmsd)0.2f} &{\\bf %(best_models_median_energy)0.2f}\\\\
Closest model &%(closest_models_median_rmsd)0.2f &%(closest_models_median_energy)0.2f\\\\
\\end{tabular}
	''' % vars()
		rosettahelper.writeFile(outfile_name, outstring)
		
		self.log(outfile_name)
		
		#put all model output figures into a tex table
		score_vs_rmsd_plots = []
		num_pdbs = len(sorted_pdb_ids)
		num_rows = 4
		num_cols = 2
		num_plots_per_page = num_rows * num_cols
		num_pages = int(math.ceil(2 * num_pdbs/float(num_plots_per_page)))
		self.log('%d pdbs' % num_pdbs)
		self.log('%d pages' % num_pages)
		index = 0
		for i in range(num_pages):
			outfile_name=os.path.join(self.outdir, 'all_models_%d.tex' % (i+1))
			outstring = '''
\\begin{figure}
\\resizebox{\\textwidth}{!}{
\\begin{tabular}{%s}
	''' % ('c' * num_cols)
			#-
			for j in range(num_rows):
				
				k = 0
				while k < num_cols:
					if index < num_pdbs:
						pdb = sorted_pdb_ids[index]
						outstring += '\\includegraphics{%s} &' % os.path.join(self.outdir, "%s_models_all.eps" % pdb)
						outstring += '\\includegraphics{%s} &' % os.path.join(self.outdir, "%s_density.eps" % pdb)
					else:
						outstring += '\\includegraphics{%s} &' % BenchmarkAnalyzer.placeholder_image
						outstring += '\\includegraphics{%s} &' % BenchmarkAnalyzer.placeholder_image
					k += 2
					index += 1
				
				outstring = outstring.rstrip(' &') + '\\\\\n'
			#-	
			outstring += '''
\\end{tabular}
}\\end{figure}
	'''
			rosettahelper.writeFile(outfile_name, outstring)
			score_vs_rmsd_plots.append(outfile_name)
			self.log(outfile_name)
		
		#create report PDF
		tempx = num_models_offset + 1
		reportname = 'KIC_scientific_benchmark_report_top%(top_X)d_models_%(tempx)d-%(num_models_per_PDB)d' % vars()
		outfile_name = os.path.join(self.outdir, '%s.tex' % reportname)
		
		outstring = self.texHeader
		
		outstring += '''
\\section{Benchmark details}'''
		outstring += self.generateBenchmarkDetailsTex()
		outstring += self.generateBenchmarkOptionsTex()
	
		outstring += '''
	\\section{Overall benchmark performance}
	\\begin{center}
	\\input{%s}
	
	\\includegraphics[width=10cm]{%s}
	\\end{center}
	
	\\clearpage
	\\section{Individual results per input structure}
	\\begin{table}[ht]
	\\scalebox{0.9}{
	\\input{%s}
	}
	\\end{table}
	
	\\clearpage''' % (tex_tables[1], '%s.eps' % boxplot_outfile_name.split('.out')[0], tex_tables[0])
		
		for i in range(len(score_vs_rmsd_plots)):
			outstring += '''
	\\input{%s}''' % score_vs_rmsd_plots[i]
		#-
		outstring+='''
	\\end{document}'''
		
		rosettahelper.writeFile(outfile_name, outstring)
		for i in range(3):
			#error = statsfns.Popen(self.outdir, ['pdflatex', '-output-directory', self.outdir, outfile_name]).getError()
			#if error:
		#		raise Exception(error)
			
			self.popen(['latex', '-output-directory', self.outdir, outfile_name], logstdout = True, logstderr = True)
			self.checkFileExists('%s.dvi' % reportname)
			
		self.popen(['dvips', '-Ppdf', '%s.dvi' % reportname], logstdout = True, logstderr = True)
		self.checkFileExists('%s.ps' % reportname)
			
		self.popen(['ps2pdf', '%s.ps' % reportname])
		self.checkFileExists('%s.pdf' % reportname)
			
		reportFile = os.path.join(self.outdir, '%s.pdf' % reportname)
		self.PDFReport = rosettahelper.readFile(reportFile)
		self.log('Final report: %s' % reportFile)
		return self.PDFReport