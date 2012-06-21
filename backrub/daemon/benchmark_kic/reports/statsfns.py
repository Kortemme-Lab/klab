import subprocess
import os
import math
import rosettahelper
from string import join

#This file was edited/added to by Shane O'Connor from files developed and written by Roland A. Pache, Ph.D., Copyright (C) 2011, 2012.

class ProcessOutput(object):
	
	def __init__(self, stdout, stderr, errorcode):
		self.stdout = stdout
		self.stderr = stderr
		self.errorcode = errorcode
	
	def getError(self):
		if self.errorcode != 0:
			return("Errorcode: %d\n%s" % (self.errorcode, self.stderr))
		return None

class Model:
	def __init__(self, pdbID, runID, loop_rms, total_energy, runtime):
		self.pdbID = pdbID
		self.runID = runID
		self.id = "%s_%s" % (pdbID, runID)
		self.loop_rms = loop_rms
		self.total_energy = total_energy
		self.runtime = runtime
		
	def __repr__(self):
		return "%s\t%f\t%f" % (self.id, self.loop_rms, self.total_energy)

class MedianResult:
	
	def __init__(self, loop_rmsd, energy):
		self.loop_rmsd = loop_rmsd
		self.energy = energy
		
	def __repr__(self):
		return "Median of loop rmsds: %s\nMedian of energies: %s" % (self.loop_rmsd, self.energy)

def Popen(outdir, args):
	subp = subprocess.Popen([str(arg) for arg in args], stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=outdir)
	output = subp.communicate()
	return ProcessOutput(output[0], output[1], subp.returncode) # 0 is stdout, 1 is stderr
	#process = subprocess.Popen(args,shell=True)
	#status = os.waitpid(process.pid, 0)
	#return status[1]

def breakCommandLine(commandLine, length = 80):
	commandLine = commandLine.replace("%(", "[").replace(")s", "]").replace(")d", "]").replace('{', '(').replace('}', ')')
	tokens = commandLine.split(" ")
	commandLine = []
	currentLine = ''
	for token in tokens:
		if len(currentLine) + len(token) > length:
			commandLine.append(currentLine)
			currentLine = token
		else:
			currentLine += ' %s' % token
	commandLine.append(currentLine)
	commandLine = join(commandLine, "\n")
	return commandLine

#Quantile
#input: list of values (floats/ints), p in [0,1)
#output: p-Quantile, 'n/a' if not applicable
def quantile(values, p):
	quantile='n/a'
	if values!=[]:
		dummy_values=[]
		for value in values:
			if value!='n/a':
				dummy_values.append(value)
		if not dummy_values:
			raise Exception("The list of values did not contain any valid entries.")
		dummy_values.sort()
		num_values=len(dummy_values)
		index=int(float(num_values)*p)
		quantile=dummy_values[index]
	return quantile

#Median
#input: list of values (floats/ints)
#output: median, 'n/a' if not applicable
def median(values):
	median=quantile(values,0.5)
	return median

#Box-and-Whisker plot with median bars
#input: map x (float/int) -> list of y (float/int)
#output: list of (x,min,1st_quartile,median,3rd_quartile,max) tuples ready for gnuplot
def boxAndWhisker(data):
	tuples=[]
	for x in data:
		y_values=data[x]
		if y_values!=[]:
			minimum=min(y_values)
			maximum=max(y_values)
			median_value=median(y_values)
			first_quartile=quantile(y_values,0.25)
			third_quartile=quantile(y_values,0.75)
			tuples.append([x,minimum,first_quartile,median_value,third_quartile,maximum])
	return tuples

#cumulative probabilities
#input: list of values (float/int)), sort reverse (boolean)
#output: map: value -> cumulative probability
def cumulativeProbabilitiesMap(values,sort_reverse):
	cumulative_probabilities_map={}
	num_values=len(values)
	values_map={}
	for value in values:
		if value not in values_map:
			values_map[value]=1
		else:
			values_map[value]+=1
	#--
	sorted_values=sorted(values_map.keys(),reverse=sort_reverse)
	count=0
	for value in sorted_values:
		count+=values_map[value]
		cumulative_probabilities_map[value]=count/float(num_values)
	#-
	return cumulative_probabilities_map

#Histogram
#input: list of values (floats/ints), number of bins (int)
#output: list of pairs (bin,abundance) ready for gnuplot
def histogram(values, num_bins):
	cleaned_values = [value for value in values if value != 'n/a']

	bins_list = []
	maximum = max(cleaned_values)
	minimum = min(cleaned_values)
	#check if minimum unequal to maximum
	if maximum != minimum:
		bin_size = float(maximum - minimum)/(num_bins - 0.000001)#subtract small epsilon value to get the maximum also into a bin
		
		#init bins
		bins = dict.fromkeys(range(num_bins), 0)
		#-
		#fill bins
		for value in cleaned_values:
			bin_number = math.floor(float(value - minimum)/float(bin_size))
			bins[bin_number] += 1
		#-
		#convert map of bin_numbers into list of bin representatives
		for bin_number in bins:
			bin = (bin_number * bin_size) + minimum
			bins_list.append((bin, bins[bin_number]))
	#--
	else:
		#create only one bin
		bins_list.append((minimum, len(values)))
	#-
	return bins_list

#converts raw values into ranks for rank correlation coefficients
#input: list of values (int/float)
#output: map: value -> rank 
def getRanks(values):
	ranks={}
	sorted_values=sorted(values)
	for i in range(len(sorted_values)):
		value=sorted_values[i]
		if value not in ranks:
			ranks[value]=i+1
	#--
	return ranks

#Goodman and Kruskal's gamma correlation coefficient
#input: 2 lists of ranks (ints) of same length with corresponding entries
#output: Gamma correlation coefficient (rank correlation ignoring ties)
def gamma(ranks_list1,ranks_list2):
	num_concordant_pairs=0
	num_discordant_pairs=0
	num_tied_x=0
	num_tied_y=0
	num_tied_xy=0
	num_items=len(ranks_list1)
	for i in range(num_items):
		rank_1=ranks_list1[i]
		rank_2=ranks_list2[i]
		for j in range(i+1,num_items):
			diff1=ranks_list1[j]-rank_1
			diff2=ranks_list2[j]-rank_2
			if (diff1>0 and diff2>0) or (diff1<0 and diff2<0):
				num_concordant_pairs+=1
			elif (diff1>0 and diff2<0) or (diff1<0 and diff2>0):
				num_discordant_pairs+=1
			elif diff1==0 and diff2==0:
				num_tied_xy+=1
			elif diff1==0:
				num_tied_x+=1
			elif diff2==0:
				num_tied_y+=1
	#---
	try:
		gamma_corr_coeff=float(num_concordant_pairs-num_discordant_pairs)/float(num_concordant_pairs+num_discordant_pairs)
	except:
		gamma_corr_coeff='n/a'
	#-
	return [num_tied_x,num_tied_y,num_tied_xy,gamma_corr_coeff]

#Goodman and Kruskal's gamma correlation coefficient wrapper
#input: 2 lists of values of same length with corresponding entries
#output: Gamma correlation coefficient (rank correlation ignoring ties)
def gammaCC(values_list1,values_list2):
	ranks1=getRanks(values_list1)
	ranks_list1=[]
	for value in values_list1:
		rank=ranks1[value]
		ranks_list1.append(rank)
	#-
	ranks2=getRanks(values_list2)
	ranks_list2=[]
	for value in values_list2:
		rank=ranks2[value]
		ranks_list2.append(rank)
	#-
	gcc=round(gamma(ranks_list1,ranks_list2)[3],2)
	return gcc

class RInterface(object):
	def __init__(self, outdir):
		self.outdir = outdir
		
	def run(self, R_commands):
		outfile_name = 'R_commands.dat'
		outfile_path = os.path.join(self.outdir, outfile_name)
		rosettahelper.writeFile(outfile_path, R_commands)
		error = Popen(self.outdir, ['R', 'CMD', 'BATCH', outfile_name]).getError()
		if error:
			raise Exception(error)
		return rosettahelper.readFile(os.path.join(self.outdir, '%s.Rout' % outfile_name))

#Kruskal-Wallis nonparametric test p-value
#input: two lists of values (float/int), one of {'two.sided','greater','less'}
#output: one or two-sided p-value (float), depending on the given alternative
def KruskalWallisTestPValue(R_interface, list1, list2, alternative, printout = True):
	R_commands='library(stats)\n\
	x<-c('+str(list1).strip('[]')+')\n\
	x\n\
	y<-c('+str(list2).strip('[]')+')\n\
	y\n\
	result=kruskal.test(list(x,y),workspace=2e8,paired=TRUE,alternative="'+alternative+'")\n\
	result\n'
	#cat("p-value: ",result$p.value,"\n")'
	output=R_interface.run(R_commands)
	if printout:
		print output
	#-
	p_value='n/a'
	lines=output.split('\n')
	for line in lines:
		if 'p-value' in line:
			p_value=line.split('p-value =')[1].strip(' ')
			break
	#--
	return p_value

#Paired t-test p-value
#input: two lists of values (float/int), one of {'two.sided','greater','less'}
#output: one or two-sided p-value (float), depending on the given alternative
def pairedTTestPValue(R_interface, list1, list2, alternative, printout = True):
	R_commands='library(stats)\n\
	x<-c('+str(list1).strip('[]')+')\n\
	x\n\
	y<-c('+str(list2).strip('[]')+')\n\
	y\n\
	result=t.test(x,y,workspace=2e8,paired=TRUE,alternative="'+alternative+'")\n\
	result\n'
	#cat("p-value: ",result$p.value,"\n")'
	output = R_interface.run(R_commands)
	if printout:
		print output
	#-
	p_value='n/a'
	lines=output.split('\n')
	for line in lines:
		if 'p-value' in line:
			p_value=line.split('p-value =')[1].strip(' ')
			break
	#--
	return p_value


#Kolmogorov-Smirnov test (KS test) p-value
#input: two lists of values (float/int), one of {'two.sided','greater','less'}
#output: one or two-sided p-value (float), depending on the given alternative
def KSTestPValue(R_interface, list1, list2, alternative, printout = True):
	R_commands='library(stats)\n\
	x<-c('+str(list1).strip('[]')+')\n\
	x\n\
	y<-c('+str(list2).strip('[]')+')\n\
	y\n\
	result=ks.test(x,y,workspace=2e8,alternative="'+alternative+'")\n\
	result\n'
	#cat("p-value: ",result$p.value,"\n")'
	
	output = R_interface.run(R_commands)
	if printout:
		print output
	#-
	p_value='n/a'
	lines=output.split('\n')
	
	for line in lines:
		if 'p-value' in line and 'cannot compute correct p-values with ties' not in line:
			p_value=line.split('p-value =')[1].strip(' ')
			break
	#--
	return p_value


