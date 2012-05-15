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