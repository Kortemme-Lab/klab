#!/usr/bin/python
#This file was edited/added to by Shane O'Connor from files developed and written by Roland A. Pache, Ph.D., Copyright (C) 2011, 2012.
#Analyses the KIC scientific benchmark and creates a pdf report of the results.

import re
import os
import math
import statsfns
import rosettahelper
from benchmark_kic.analysis import BenchmarkAnalyzer
from string import join

class ComparisonReport(BenchmarkAnalyzer):
	'''Evaluates KIC scientific benchmark runs to test for significant improvement.'''

	def __init__(self, outdir, reportSettings, benchmark1RunSettings, benchmark2RunSettings, quiet = False, html = False):
		super(ComparisonReport, self).__init__(quiet, html)
		self.outdir = outdir
		self.reportSettings = reportSettings
		self.benchmark1RunSettings = benchmark1RunSettings
		self.benchmark2RunSettings = benchmark2RunSettings
		self.benchmarkname1 = benchmark1RunSettings["Description"]
		self.benchmarkname2 = benchmark2RunSettings["Description"]
		
		assert(benchmark1RunSettings['Options']['NumberOfModelsPerPDB'] == benchmark2RunSettings['Options']['NumberOfModelsPerPDB'])
		self.num_models_per_run = benchmark1RunSettings['Options']['NumberOfModelsPerPDB']
		
		self.PDFReport = None # todo remove
		
		self.model_start_index = 1
		self.model_end_index = self.num_models_per_run
		self.num_models_per_run = self.num_models_per_run
		self.num_bins = reportSettings['NumberOfBins']
		self.top_X = reportSettings['TopX']
		self.quiet = quiet

		self.models = {1: self.parseModels(benchmark1RunSettings["FlatfileLines"]), 2: self.parseModels(benchmark2RunSettings["FlatfileLines"])}
		
		assert(sorted(self.models[1].keys()) == sorted(self.models[2].keys()))
		self.sorted_benchmark_pdbs = sorted(self.models[1].keys())
		keys = ["NumberOfModels", "TopXBestModel"]
		self.resultsByPDB = dict.fromkeys(self.sorted_benchmark_pdbs, None)
		for pdbID in self.sorted_benchmark_pdbs:
			self.resultsByPDB[pdbID] = {}
			self.resultsByPDB[pdbID][1] = dict.fromkeys(keys, None)
			self.resultsByPDB[pdbID][2] = dict.fromkeys(keys, None)
		
		
	def parseModels(self, filelines):
		'Parse models.'
		pdb_runtimes = {}
		models = {}
		total_runtime = 0
		for line in filelines:
			if not line.startswith('#'):
				data = line.strip('\n').split('\t')
				if len(data) > 3:
					pdb = data[0]
					if pdb not in models:
						 models[pdb] = []
					#-
					if pdb not in pdb_runtimes:
						pdb_runtimes[pdb] = []
					#-
					model_index = int(data[1])
					if model_index >= self.model_start_index and model_index <= self.model_end_index:
						model = statsfns.Model(data[0], data[1], float(data[2]), float(data[3]), None)
						models[pdb].append(model)
						if len(data) > 4:
							total_runtime += int(data[4])
							pdb_runtimes[pdb].append(int(data[4]))
	
		if total_runtime != 0:
			self.log('total runtime [hours]:', int(total_runtime/float(3600)))
	
		return models


	def computeBestModelRmsds(self, benchmarkNumber, start_index, end_index):
		models_map = self.models[benchmarkNumber]
		best_model_rmsds = []
		rmsds = []
		for pdb in self.sorted_benchmark_pdbs:
			all_models = models_map[pdb]
			models = []
			for model in all_models:
				model_index = int(model.runID)
				if model_index >= start_index and model_index <= end_index:
					models.append(model)
		
			#determine best model of this run for the given pdb
			sorted_energy_models = sorted(models, lambda x, y: cmp(x.total_energy, y.total_energy))
			lowest_energy_model = sorted_energy_models[0]
			#when looking for the best model, consider the top X lowest energy models and pick the one with lowest rmsd
			for i in range(self.top_X):
				if i < len(sorted_energy_models):
					best_model_candidate = sorted_energy_models[i]
					if best_model_candidate.loop_rms < lowest_energy_model.loop_rms:
						lowest_energy_model = best_model_candidate
			
			self.log('best model (i.e. lowest rmsd of top %d lowest energy models):' % self.top_X, lowest_energy_model.id, lowest_energy_model.loop_rms, lowest_energy_model.total_energy)
			
			self.resultsByPDB[pdb][benchmarkNumber]["NumberOfModels"] = len(self.models[benchmarkNumber][pdb])
			self.resultsByPDB[pdb][benchmarkNumber]["TopXBestModel"] = lowest_energy_model
			
			best_model_rmsds.append(lowest_energy_model.loop_rms)
			#rmsds.append(lowest_energy_model.loop_rms)#for medians
		#--
		#best_model_rmsds.append(functions_lib.median(rmsds))#for medians
		return best_model_rmsds

		
	def computeBestModelEnergies(self, benchmarkNumber, start_index, end_index):
		return [self.resultsByPDB[pdb][benchmarkNumber]["TopXBestModel"].total_energy for pdb in self.sorted_benchmark_pdbs]
	
	def rmsdScatterplot(self, y_label, all_best_rmsds_models1, x_label, all_best_rmsds_models2, outfile_name):
		y_label = "Benchmark 1" # override
		x_label = "Benchmark 2" # override
		sorted_benchmark_pdbs = self.sorted_benchmark_pdbs
		top_X = self.top_X
		outfile = open(outfile_name, 'w')
		
		#write all datapoints
		outfile.write('#PDB\tLoop_rmsd_benchmark2\tLoop_rmsd_benchmark1\n')
		for i in range(len(sorted_benchmark_pdbs)):
			pdb = sorted_benchmark_pdbs[i]
			outfile.write('%s\t%s\t%s\n' % (pdb, str(all_best_rmsds_models2[i]), str(all_best_rmsds_models1[i])))
		#-
		outfile.write('\n\n')
		
		#highlight those datapoints that are subangstrom in only one of the datasets
		self.log('')
		self.log('PDB\t%(x_label)s\t%(y_label)s' % vars())
		for i in range(len(sorted_benchmark_pdbs)):
			pdb = sorted_benchmark_pdbs[i]
			rmsd1 = all_best_rmsds_models1[i]
			rmsd2 = all_best_rmsds_models2[i]
			if rmsd1 < 1 and rmsd2 >= 1:
				outstr = '%s\t%s\t%s\n'% (pdb, str(all_best_rmsds_models2[i]), str(all_best_rmsds_models1[i]))
				self.log(outstr)
				outfile.write(outstr)
		#--
		outfile.write('\n\n')
		self.log('')
		for i in range(len(sorted_benchmark_pdbs)):
			pdb = sorted_benchmark_pdbs[i]
			rmsd1 = all_best_rmsds_models1[i]
			rmsd2 = all_best_rmsds_models2[i]
			if rmsd2 < 1 and rmsd1 >= 1:
				outstr = '%s\t%s\t%s\n'% (pdb, str(all_best_rmsds_models2[i]), str(all_best_rmsds_models1[i]))
				self.log(outstr)
				outfile.write(outstr)
		
		outfile.close()
		eps_outfile_name = outfile_name.split('.')[0]+'.eps'
		x_label_gnu = x_label.replace('_',' ')
		y_label_gnu = y_label.replace('_',' ')
		gnuplot_commands='''
set autoscale
set border 31
set tics out
set terminal postscript eps enhanced color solid "Helvetica" 24
#set size 1,1.5
set size ratio 1
#set xtics ("default" 1, "default" 2, "H/Y" 3, "Y/H" 4, "default" 6, "default" 7, "H/Y" 8, "Y/H" 9) rotate by -45
set xtics autofreq
set xtics nomirror
set ytics autofreq
set ytics nomirror
set noy2tics
set nox2tics

set style line 1 lt rgb "dark-magenta" lw 2 ps 2 pt 13
set style line 2 lt rgb "blue" lw 2 ps 2 pt 13
set style line 3 lt rgb "forest-green" lw 2 ps 2 pt 13
set style line 4 lt rgb "gold" lw 2 ps 1 pt 7
set style line 5 lt rgb "red" lw 2 ps 2 pt 13
set style line 6 lt rgb "black" lw 2
set style line 7 lt rgb "dark-gray" lw 2
set style line 8 lt rgb "gray" lw 2
set style line 9 lt rgb "orange" lw 2 ps 2 pt 13
set style line 10 lt 0 lc rgb "black" lw 5 ps 1 pt 7

set boxwidth 0.75

#set logscale x
#set logscale y
set key top right
set xrange [0:6]
set yrange [0:6]
set title "Top %(top_X)d best loop rmsds"
set encoding iso_8859_1
set xlabel "%(x_label_gnu)s rmsd to crystal loop [{/E \305}]"
set ylabel "%(y_label_gnu)s rmsd to crystal loop [{/E \305}]"
set output "%(eps_outfile_name)s"
f(x)=x
g(x)=1
set arrow from 1,0 to 1,6 nohead ls 10
plot g(x) ls 10 notitle axes x1y1, "%(outfile_name)s" index 0 using ($2):($3) with points ls 3 notitle axes x1y1, "%(outfile_name)s" index 1 using ($2):($3) with points ls 1 notitle axes x1y1, "%(outfile_name)s" index 2 using ($2):($3) with points ls 9 notitle axes x1y1, f(x) ls 6 notitle axes x1y1
''' % vars()
		gnuplot_scriptname = '%s.gnu' % outfile_name.split('.')[0]
		rosettahelper.writeFile(gnuplot_scriptname, gnuplot_commands)
		error = statsfns.Popen(self.outdir, ['/usr/local/bin/gnuplot', gnuplot_scriptname]).getError() # Requires gnuplot 4.2
		if error:
			raise Exception(error)
		error = statsfns.Popen(self.outdir, ['bash', 'epstopdf','--nocompress', eps_outfile_name]).getError() # The bash is necessary as the epstopdf script does not have a valid shebang which confuses subprocess
		if error:
			raise Exception(error)


	def densityplot(self, title1, sorted_models1, title2, sorted_models2, outfile_name):
		title1 = "Benchmark 1" # override
		title2 = "Benchmark 2" # override
		outfile = open(outfile_name, 'w')
		outfile.write('#Loop_rmsd\tPercentage_of_models\n')
		values = [model.loop_rms for model in sorted_models1]
		#-
		histogram = statsfns.histogram(values, self.num_bins)
		for (bin, num_values) in histogram:
			outfile.write("%s\t%s\n" % (str(bin), str(100*num_values/float(len(values)))))
		
		outfile.write('\n\n')
		values = [model.loop_rms for model in sorted_models2]
		
		histogram = statsfns.histogram(values, self.num_bins)
		for (bin, num_values) in histogram:
			outfile.write("%s\t%s\n" % (str(bin), str(100*num_values/float(len(values)))))
		#-
		outfile.close()
		eps_outfile_name = outfile_name.split('.')[0] + '.eps'
		gnuplot_commands = '''
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

set style line 1 lt rgb "dark-magenta" lw 5
set style line 2 lt rgb "blue" lw 5 ps 1 pt 7
set style line 3 lt rgb "forest-green" lw 5 ps 2 pt 13
set style line 4 lt rgb "gold" lw 2 ps 1 pt 7
set style line 5 lt rgb "red" lw 2 ps 2 pt 13
set style line 6 lt rgb "black" lw 2
set style line 7 lt rgb "dark-gray" lw 2
set style line 8 lt rgb "gray" lw 2
set style line 9 lt rgb "orange" lw 5 ps 2 pt 13
set style line 10 lt 0 lc rgb "black" lw 5 ps 1 pt 7

set boxwidth 0.75

set key top right
set xrange [0:]
set title "''' + outfile_name.split('/')[-1].split('_')[0]+'''"
set encoding iso_8859_1
set xlabel "r.m.s. deviation to crystal loop [{/E \305}]"
set ylabel "Fraction of models [%]"
set output "'''+eps_outfile_name+'''"
set arrow from 1,graph 0 to 1,graph 1 nohead ls 10
plot "'''+outfile_name+'''" index 0 using ($1):($2) with lines smooth bezier ls 1 title "'''+title1.replace('_',' ')+'''" axes x1y1, "'''+outfile_name+'''" index 1 using ($1):($2) with lines smooth bezier ls 9 title "'''+title2.replace('_',' ')+'''" axes x1y1
'''
		gnuplot_scriptname = outfile_name.split('.')[0]+'.gnu'
		rosettahelper.writeFile(gnuplot_scriptname, gnuplot_commands)
		
		error = statsfns.Popen(self.outdir, ['/usr/local/bin/gnuplot', gnuplot_scriptname]).getError() # Requires gnuplot 4.2
		if error:
			raise Exception(error)
		error = statsfns.Popen(self.outdir, ['bash', 'epstopdf','--nocompress', eps_outfile_name]).getError() # The bash is necessary as the epstopdf script does not have a valid shebang which confuses subprocess
		if error:
			raise Exception(error)

	def generateBenchmarkDetailsTex(self, BenchmarkNumber, benchmarkRunSettings):
		benchmarkRunSettings['ReportDescription'] = ""
		if benchmarkRunSettings['Description'] != "Benchmark %d" % BenchmarkNumber:
			benchmarkRunSettings['ReportDescription'] = ' (%s)' % benchmarkRunSettings['Description'] 
		if benchmarkRunSettings['RosettaDBSVNRevision'] != benchmarkRunSettings['RosettaSVNRevision']:
			benchmarkRunSettings['DBDescription'] = ' (Rosetta database version %s)' % benchmarkRunSettings['RosettaDBSVNRevision']
		else:
			benchmarkRunSettings['DBDescription'] = ''
		
		commandLine = benchmarkRunSettings['RosettaCommandLine']
		for Option, d in benchmarkRunSettings['OptionReplacementPatterns'].iteritems():
			if benchmarkRunSettings['Options'].get(Option):	# todo: remove later - should not be necessary unless items missing from dict
				commandLine = re.sub("%%[(]%s[)]\w" % d['Pattern'], str(benchmarkRunSettings['Options'][Option]), commandLine)
		benchmarkRunSettings['RosettaSplitCommandLine'] = statsfns.breakCommandLine(commandLine) 
		benchmarkRunSettings['BenchmarkNumber'] = BenchmarkNumber
		
		return '''
\\paragraph{Benchmark %(BenchmarkNumber)d (run %(RunID)d) %(ReportDescription)s \\textnormal{Rosetta version %(RosettaSVNRevision)s%(DBDescription)s}}
\\begin{lstlisting}
%(RosettaSplitCommandLine)s
\\end{lstlisting}
		''' % benchmarkRunSettings
		
	def generateBenchmarkOptionsTex(self, benchmarkRunSettings):
		LaTeX = '''
\\paragraph{Options}
\\begin{tabular}{ll}
'''
		for option, value in benchmarkRunSettings['Options'].iteritems():
			if benchmarkRunSettings['OptionReplacementPatterns'][option]['ShowInReport']:
				LaTeX += "%s & %s \\\\\n" % (benchmarkRunSettings['OptionReplacementPatterns'][option]['Description'], value)	
		LaTeX += "\\end{tabular}\n"
		return LaTeX

	def run(self):
		top_X = self.top_X
		#plot density comparison
		self.log('\n')
		self.log('plotting sampling density comparisons...')
		for pdb in self.sorted_benchmark_pdbs:
			sorted_models1 = self.models[1][pdb]
			sorted_models2 = self.models[2][pdb]
			outfile_name = os.path.join(self.outdir, "%s_density_comparison.out" % pdb)
			self.densityplot(self.benchmarkname1, sorted_models1, self.benchmarkname2, sorted_models2, outfile_name)
		
		#put all density comparison figures into a tex table
		density_comparison_plots = []
		num_pdbs = len(self.sorted_benchmark_pdbs)
		num_rows = 4
		num_cols = 2
		num_plots_per_page = num_rows * num_cols
		num_pages = int(math.ceil(num_pdbs/float(num_plots_per_page)))
		self.log(num_pdbs, 'pdbs')
		self.log(num_pages, 'pages')
		index = 0
		for i in range(num_pages):
			outfile_name = os.path.join(self.outdir, 'density_comparison_%d.tex' % (i+1))
			outstring='''
\\begin{figure}[h]
\\resizebox{\\textwidth}{!}{
\\begin{tabular}{%s}
		''' % ('c' * num_cols)
		
			for j in range(num_rows):
				k = 0
				for k in range(num_cols):
					if index < num_pdbs:
						pdb = self.sorted_benchmark_pdbs[index]
						outstring += '\\includegraphics{%s} &' % (os.path.join(self.outdir, "%s_density_comparison.eps" % pdb))
					else:
						outstring += '\\includegraphics{%s} &' % BenchmarkAnalyzer.placeholder_image
					#-
					index += 1
				#-
				outstring = outstring.rstrip(' &')+'\\\\\n'
			#-
			outstring += '''
\\end{tabular}
}\\end{figure}
		'''
			rosettahelper.writeFile(outfile_name, outstring)
			density_comparison_plots.append(outfile_name)
			self.log('')
			self.log(outfile_name)
		#-
		#compute rmsds of best models
		self.log('\n')
		self.log('computing rmsds of best models,',self.num_models_per_run,'models per run')
		all_best_rmsds_models1 = []
		all_best_rmsds_models2 = []
		i = self.model_start_index
		while i < self.model_end_index:
			j = i + self.num_models_per_run - 1
			self.log('')
			self.log(i,'-',j)
			
			self.log('benchmark 1:')
			best_rmsds_models1 = self.computeBestModelRmsds(1, i, j)
			self.log('median rmsd:', round(statsfns.median(best_rmsds_models1), 2))
			all_best_rmsds_models1.extend(best_rmsds_models1)
			
			self.log('benchmark 2:')
			best_rmsds_models2 = self.computeBestModelRmsds(2, i, j)
			self.log('median rmsd:',round(statsfns.median(best_rmsds_models2), 2))
			all_best_rmsds_models2.extend(best_rmsds_models2)
			
			i += self.num_models_per_run
		
		best_model_energies1 = self.computeBestModelEnergies(1, i, j)
		best_model_energies2 = self.computeBestModelEnergies(2, i, j)
		MedianResult1 = statsfns.MedianResult(statsfns.median(best_rmsds_models1), statsfns.median(best_model_energies1))
		MedianResult2 = statsfns.MedianResult(statsfns.median(best_rmsds_models2), statsfns.median(best_model_energies2)) 
		self.log(MedianResult1)
		self.log(MedianResult2)
		
		# Print all_best_rmsds_models1
		num_cases = len(all_best_rmsds_models1)
		self.log(num_cases,'rmsds per benchmark in total')
		
		#calculate percentage of improved cases
		self.log('')
		self.log('calculating percentage of improved cases...')
		percent_improved_cases = 0
		for i in range(num_cases):
			rmsd1 = all_best_rmsds_models1[i]
			rmsd2 = all_best_rmsds_models2[i]
			if rmsd2 < rmsd1:
				percent_improved_cases += 1
		#--
		percent_improved_cases = round(100 * percent_improved_cases/float(num_cases), 2)
		self.log(percent_improved_cases,'% improved cases')
		if percent_improved_cases > 50:
			self.log('improvement in benchmark performance')
		
		#perform KS test to check for statistical significance of difference in rmsd distributions
		R_interface = statsfns.RInterface(self.outdir)
		self.log('')
		self.log('performing KS-test to check for statistical significance of difference in rmsd distributions...')
		KS_p_value = statsfns.KSTestPValue(R_interface, all_best_rmsds_models1, all_best_rmsds_models2, 'two.sided', False)
		self.log('p-value:', KS_p_value)
		self.log('performing Kruskal-Wallis test to check for statistical significance of difference in rmsd distributions...')
		KW_p_value = statsfns.KruskalWallisTestPValue(R_interface, all_best_rmsds_models1, all_best_rmsds_models2, 'two.sided', False)
		self.log('p-value:', KW_p_value)
		self.log('performing paired t-test (more statistical power) to check for statistical significance of difference in rmsd distributions...')
		pairedT_p_value = statsfns.pairedTTestPValue(R_interface, all_best_rmsds_models1, all_best_rmsds_models2, 'two.sided', False)
		self.log('p-value:', pairedT_p_value)
		
		#plot rmsd comparison
		self.log('')
		self.log('plotting rmsd comparison...')
		rmsd_comparison_outfile_name = os.path.join(self.outdir, 'rmsd_comparison.out')
		
		self.rmsdScatterplot(self.benchmarkname1, all_best_rmsds_models1, self.benchmarkname2, all_best_rmsds_models2, rmsd_comparison_outfile_name)
		self.log('')
		self.log(self.outdir)
		
		#create report pdf
		reportname = 'KIC_scientific_benchmark_changes_report_top%d' % top_X
		outfile_name = os.path.join(self.outdir, '%s.tex' % reportname)
		outstring = self.texHeader
		percent_improved_cases_text = 'Percentage of improved cases: %0.f\\%%' % percent_improved_cases
		if percent_improved_cases > 50:
			percent_improved_cases_text += ''' -- \\textcolor{OliveGreen}{Improvement in benchmark performance}'''
		elif percent_improved_cases < 50:
			percent_improved_cases_text += ''' -- \\textcolor{BrickRed}{Decrease in benchmark performance}'''
		percent_improved_cases_text += '.\\\\'
		
		rmsd_comparison_outfile_str = "%s.eps" % rmsd_comparison_outfile_name.split('.out')[0]
		KS_p_value_str = str(KS_p_value)
		KW_p_value_str = str(KW_p_value)
		pairedT_p_value_str = str(pairedT_p_value)
		
		outstring += '''
\\section{Benchmark details}'''

		outstring += self.generateBenchmarkDetailsTex(1, self.benchmark1RunSettings)
		outstring += self.generateBenchmarkOptionsTex(self.benchmark1RunSettings)
		outstring += self.generateBenchmarkDetailsTex(2, self.benchmark2RunSettings) 
		outstring += self.generateBenchmarkOptionsTex(self.benchmark2RunSettings)
		
		medianrmsd1 = MedianResult1.loop_rmsd
		medianrmsd2 = MedianResult2.loop_rmsd
		medianenergy1 = MedianResult1.energy
		medianenergy2 = MedianResult2.energy
		outstring += '''
\\pagebreak
\\section{Overall benchmark performance comparison}
\\begin{tabular}{lrr}
Top %(top_X)d best model &Median loop rmsd &Median energy\\\\\\hline
Benchmark 1 & %(medianrmsd1)f & %(medianenergy1)f\\\\
Benchmark 2 & %(medianrmsd2)f & %(medianenergy2)f\\\\
\\end{tabular}
\\begin{center}
\\includegraphics[width=10cm]{%(rmsd_comparison_outfile_str)s}
\\end{center}

%(percent_improved_cases_text)s

{\\bf Statistical significance of differences in RMSD distributions:}
\\begin{table}[ht]
\\begin{center}
\\begin{tabular}{rr}
Statistic &P-value\\\\\\hline
Kolmogorov-Smirnov test &%(KS_p_value_str)s\\\\
Kruskal-Wallis test &%(KW_p_value_str)s\\\\
Paired T-test &%(pairedT_p_value_str)s\\\\
\\end{tabular}
\\end{center}
\\end{table}''' % vars()

		outstring += '''
\\pagebreak
\\section{Individual results per input structure}
\\begin{table}[ht]
\\scalebox{0.85}{
\\begin{tabular}{r||r|rrr||r|rrr}
\\multicolumn{1}{c}{} & \\multicolumn{4}{c}{Benchmark 1} & \\multicolumn{4}{c}{Benchmark 2} \\\\ 
\\hline
PDB & \# models & Top %(top_X)d best model & Loop rmsd & Energy & \# models & Top %(top_X)d best model & Loop rmsd & Energy \\\\
\\hline''' % vars()

		for pdbID in self.sorted_benchmark_pdbs:
			vals = [pdbID]
			vals.append(self.resultsByPDB[pdbID][1]["NumberOfModels"])
			vals.append(self.resultsByPDB[pdbID][1]["TopXBestModel"].runID)
			vals.append(self.resultsByPDB[pdbID][1]["TopXBestModel"].loop_rms)
			vals.append(self.resultsByPDB[pdbID][1]["TopXBestModel"].total_energy)
			vals.append(self.resultsByPDB[pdbID][2]["NumberOfModels"])
			vals.append(self.resultsByPDB[pdbID][2]["TopXBestModel"].runID)
			vals.append(self.resultsByPDB[pdbID][2]["TopXBestModel"].loop_rms)
			vals.append(self.resultsByPDB[pdbID][2]["TopXBestModel"].total_energy)
			outstring += "%s\\\\\n" % join(map(str, vals), " & ")
		outstring += '''
\\end{tabular}
}
\\end{table}

The Top %(top_X)d best model is the model with the lowest rmsd out of the top %(top_X)d lowest energy models.''' % vars()


		outstring += '''
\\clearpage
%\\section{Individual comparisons per input structure}
'''
		for i in range(len(density_comparison_plots)):
			outstring+='\\input{%s}\n' % density_comparison_plots[i]
		#-
		outstring += '\\end{document}\n'
		rosettahelper.writeFile(outfile_name, outstring)
		for i in range(3):
			self.log(self.outdir)
			self.log(outfile_name)
			error = statsfns.Popen(self.outdir, ['latex', '-output-directory', self.outdir, outfile_name]).getError()
			if error:
				raise Exception(error)
			if not os.path.exists(os.path.join(self.outdir, '%s.dvi' % reportname)):
				raise Exception("DVI file could not be created.")
			
		error = statsfns.Popen(self.outdir, ['dvips', '-Ppdf', '%s.dvi' % reportname, '-o', '%s.ps' % reportname]).getError()
		if error:
			raise Exception(error)
		if not os.path.exists(os.path.join(self.outdir, '%s.ps' % reportname)):
			raise Exception("Postscript file could not be created.")
		
		error = statsfns.Popen(self.outdir, ['ps2pdf', '%s.ps' % reportname]).getError()
		if error:
			raise Exception(error)
		if not os.path.exists(os.path.join(self.outdir, '%s.pdf' % reportname)):
			raise Exception("PDF file could not be created.")
		#functions_lib.run('pdflatex -output-directory '+self.outdir+' '+outfile_name)
		#-
		self.log('')
		self.log('Final comparison report:')
		self.log(outfile_name.split('.tex')[0]+'.pdf')
		self.PDFReport = rosettahelper.readFile(outfile_name.split('.tex')[0]+'.pdf')
