#This file was developed and written by Roland A. Pache, Ph.D., Copyright (C) 2011, 2012.

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

#Kruskal-Wallis nonparametric test p-value
#input: two lists of values (float/int), one of {'two.sided','greater','less'}
#output: one or two-sided p-value (float), depending on the given alternative
def KruskalWallisTestPValue(list1,list2,alternative,printout=True):
	R_commands='library(stats)\n\
	x<-c('+str(list1).strip('[]')+')\n\
	x\n\
	y<-c('+str(list2).strip('[]')+')\n\
	y\n\
	result=kruskal.test(list(x,y),workspace=2e8,paired=TRUE,alternative="'+alternative+'")\n\
	result\n'
	#cat("p-value: ",result$p.value,"\n")'
	output=Parameters.runR(R_commands)
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
def pairedTTestPValue(list1,list2,alternative,printout=True):
	R_commands='library(stats)\n\
	x<-c('+str(list1).strip('[]')+')\n\
	x\n\
	y<-c('+str(list2).strip('[]')+')\n\
	y\n\
	result=t.test(x,y,workspace=2e8,paired=TRUE,alternative="'+alternative+'")\n\
	result\n'
	#cat("p-value: ",result$p.value,"\n")'
	output=Parameters.runR(R_commands)
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
def KSTestPValue(list1,list2,alternative,printout=True):
	R_commands='library(stats)\n\
	x<-c('+str(list1).strip('[]')+')\n\
	x\n\
	y<-c('+str(list2).strip('[]')+')\n\
	y\n\
	result=ks.test(x,y,workspace=2e8,alternative="'+alternative+'")\n\
	result\n'
	#cat("p-value: ",result$p.value,"\n")'
	output=Parameters.runR(R_commands)
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