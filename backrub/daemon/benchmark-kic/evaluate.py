#!/usr/bin/python
#This file was developed and written by Roland A. Pache, Copyright (C) 2011, 2012.

#import libraries
import re
import os
import time
import sys
import math
from subprocess import *
#from optparse import OptionParser
import Parameters
import Statistics
#import Proteins


print '\nEvaluates KIC scientific benchmark runs to test for significant improvement.\n'


#constants
id1='Dun02'
id2='Dun02_bicubic'
infile1_name='/home/rpache/postdoc/projects/KIC_analysis/results/benchmark_paper_bumpfix/KIC_scientific_benchmark_score12prime_merged_datasets.results'
infile2_name='/home/rpache/postdoc/projects/KIC_analysis/results/benchmark_paper_bumpfix/KIC_scientific_benchmark_score12prime_bicubic_merged_datasets.results'
model_start_index=1
model_end_index=2500
num_models_per_run=2500
outdir='/home/rpache/postdoc/projects/KIC_analysis/results/benchmark_paper_bumpfix/evaluation_score12prime_vs_score12prime_bicubic_merged_datasets/'
top_X=5

#patterns

#define classes
class Model:
    def __init__(self):
        self.id=None
        self.loop_rms=float('inf')
        self.total_energy=float('inf')
        self.runtime=None

#define functions
def parseModels(infile_name):
    pdb_runtimes={}
    models={}
    print
    print infile_name
    total_runtime=0
    infile=open(infile_name)
    for line in infile:
        if not line.startswith('#'):
            data=line.strip('\n').split('\t')
            if len(data)>3:
                pdb=data[0]
                if pdb not in models:
                     models[pdb]=[]
                #-
                if pdb not in pdb_runtimes:
                    pdb_runtimes[pdb]=[]
                #-
                model_index=int(data[1])
                if model_index>=model_start_index and model_index<=model_end_index:
                    model=Model()
                    model.id=data[0]+'_'+data[1]
                    model.loop_rms=float(data[2])
                    model.total_energy=float(data[3])
                    models[pdb].append(model)
                    if len(data)>4:
                        total_runtime+=int(data[4])
                        pdb_runtimes[pdb].append(int(data[4]))
    #-----
    infile.close()
    if total_runtime!=0:
        print 'total runtime [hours]:',int(total_runtime/float(3600))
    #-
    ## for pdb in pdb_runtimes:
    ##     print
    ##     print pdb
    ##     count=0
    ##     for runtime in pdb_runtimes[pdb]:
    ##         if runtime/float(3600)>6:
    ##             print runtime
    ##             count+=1
    ##     #--
    ##     print count
    ## #-
    ## pdbs=models['dataset_2/']['-default']
    ## for pdb in pdbs:
    ##     print
    ##     print pdb,len(pdbs[pdb])
    ## #-
    return models


def computeBestModelRmsds(models_map,benchmark_pdbs,start_index,end_index):
    best_model_rmsds=[]
    rmsds=[]
    sorted_pdb_ids=sorted(models_map.keys())
    for pdb in sorted_pdb_ids:
        if pdb in benchmark_pdbs:
            #print pdb
            all_models=models_map[pdb]
            #print len(all_models),'successful models in total'
            models=[]
            for model in all_models:
                model_index=int(model.id.split('_')[1])
                if model_index>=start_index and model_index<=end_index:
                    models.append(model)
            #--
            #print len(models),'successful models in this run'
            #determine best model of this run for the given pdb
            sorted_energy_models=sorted(models,lambda x, y: cmp(x.total_energy,y.total_energy))
            lowest_energy_model=sorted_energy_models[0]
            #when looking for the best model, consider the top X lowest energy models and pick the one with lowest rmsd
            for i in range(top_X):
                best_model_candidate=sorted_energy_models[i]
                if best_model_candidate.loop_rms<lowest_energy_model.loop_rms:
                    lowest_energy_model=best_model_candidate
            #--
            print 'best model (i.e. lowest rmsd of top '+str(top_X)+' lowest energy models):',lowest_energy_model.id,lowest_energy_model.loop_rms,lowest_energy_model.total_energy
            best_model_rmsds.append(lowest_energy_model.loop_rms)
            #rmsds.append(lowest_energy_model.loop_rms)#for medians
    #--
    #best_model_rmsds.append(Statistics.median(rmsds))#for medians
    return best_model_rmsds


def rmsdScatterplot(sorted_benchmark_pdbs,y_label,all_best_rmsds_models1,x_label,all_best_rmsds_models2,outfile_name):
    outfile=open(outfile_name,'w')
    #write all datapoints
    outfile.write('#PDB\tLoop_rmsd_benchmark2\tLoop_rmsd_benchmark1\n')
    for i in range(len(benchmark_pdbs)):
        pdb=sorted_benchmark_pdbs[i]
        outfile.write(pdb+'\t'+str(all_best_rmsds_models2[i])+'\t'+str(all_best_rmsds_models1[i])+'\n')
    #-
    outfile.write('\n\n')
    #highlight those datapoints that are subangstrom in only one of the datasets
    print
    print 'PDB\t'+x_label+'\t'+y_label
    for i in range(len(benchmark_pdbs)):
        pdb=sorted_benchmark_pdbs[i]
        rmsd1=all_best_rmsds_models1[i]
        rmsd2=all_best_rmsds_models2[i]
        if rmsd1<1 and rmsd2>=1:
            print pdb+'\t'+str(all_best_rmsds_models2[i])+'\t'+str(all_best_rmsds_models1[i])
            outfile.write(pdb+'\t'+str(all_best_rmsds_models2[i])+'\t'+str(all_best_rmsds_models1[i])+'\n')
    #--
    outfile.write('\n\n')
    print
    for i in range(len(benchmark_pdbs)):
        pdb=sorted_benchmark_pdbs[i]
        rmsd1=all_best_rmsds_models1[i]
        rmsd2=all_best_rmsds_models2[i]
        if rmsd2<1 and rmsd1>=1:
            print pdb+'\t'+str(all_best_rmsds_models2[i])+'\t'+str(all_best_rmsds_models1[i])
            outfile.write(pdb+'\t'+str(all_best_rmsds_models2[i])+'\t'+str(all_best_rmsds_models1[i])+'\n')
    #--
    outfile.close()
    gnuplot_commands='\nset autoscale\
    \nset border 31\
    \nset tics out\
    \nset terminal postscript eps enhanced color solid "Helvetica" 24\
    \n#set size 1,1.5\
    \nset size ratio 1\
    \n#set xtics ("default" 1, "default" 2, "H/Y" 3, "Y/H" 4, "default" 6, "default" 7, "H/Y" 8, "Y/H" 9) rotate by -45\
    \nset xtics autofreq\
    \nset xtics nomirror\
    \nset ytics autofreq\
    \nset ytics nomirror\
    \nset noy2tics\
    \nset nox2tics\
    \n\
    \nset style line 1 lt rgb "dark-magenta" lw 2 ps 2 pt 13\
    \nset style line 2 lt rgb "blue" lw 2 ps 2 pt 13\
    \nset style line 3 lt rgb "forest-green" lw 2 ps 2 pt 13\
    \nset style line 4 lt rgb "gold" lw 2 ps 1 pt 7\
    \nset style line 5 lt rgb "red" lw 2 ps 2 pt 13\
    \nset style line 6 lt rgb "black" lw 2\
    \nset style line 7 lt rgb "dark-gray" lw 2\
    \nset style line 8 lt rgb "gray" lw 2\
    \nset style line 9 lt rgb "orange" lw 2 ps 2 pt 13\
    \nset style line 10 lt 0 lc rgb "black" lw 5 ps 1 pt 7\
    \n\
    \nset boxwidth 0.75\
    \n\
    \n#set logscale x\
    \n#set logscale y\
    \nset key top right\
    \nset xrange [0:6]\
    \nset yrange [0:6]\
    \nset title "Top '+str(top_X)+' best loop rmsds"\
    \nset encoding iso_8859_1\
    \nset xlabel "'+x_label.replace('_',' ')+' rmsd to crystal loop [{/E \305}]"\
    \nset ylabel "'+y_label.replace('_',' ')+' rmsd to crystal loop [{/E \305}]"\
    \nset output "'+outfile_name.split('.')[0]+'.eps"\
    \nf(x)=x\
    \ng(x)=1\
    \nset arrow from 1,0 to 1,6 nohead ls 10\
    \nplot g(x) ls 10 notitle axes x1y1,\
    "'+outfile_name+'" index 0 using ($2):($3) with points ls 3 notitle axes x1y1,\
    "'+outfile_name+'" index 1 using ($2):($3) with points ls 1 notitle axes x1y1,\
    "'+outfile_name+'" index 2 using ($2):($3) with points ls 9 notitle axes x1y1,\
    f(x) ls 6 notitle axes x1y1\
    \n'
    gnuplot_scriptname=outfile_name.split('.')[0]+'.gnu'
    Parameters.newFile(gnuplot_commands,gnuplot_scriptname)
    Parameters.run('gnuplot '+gnuplot_scriptname)
    Parameters.run('epstopdf --nocompress '+outfile_name.split('.')[0]+'.eps')
                    

start_time=time.time()

#parse models
print
print 'parsing models...'
models1=parseModels(infile1_name)
models2=parseModels(infile2_name)


#collect list of pdbs
print
print
print 'collecting list of benchmark pdbs...'
benchmark_pdbs=set(models1.keys())
sorted_benchmark_pdbs=sorted(benchmark_pdbs)
print sorted_benchmark_pdbs
print len(benchmark_pdbs),'pdbs'


#compute rmsds of best models
print
print
print 'computing rmsds of best models,',num_models_per_run,'models per run'
all_best_rmsds_models1=[]
all_best_rmsds_models2=[]
i=model_start_index
while i<model_end_index:
    j=i+num_models_per_run-1
    print
    print i,'-',j
    print 'benchmark 1:'
    best_rmsds_models1=computeBestModelRmsds(models1,benchmark_pdbs,i,j)
    print 'median rmsd:',round(Statistics.median(best_rmsds_models1),2)
    #print best_rmsds_models1
    all_best_rmsds_models1.extend(best_rmsds_models1)
    print 'benchmark 2:'
    best_rmsds_models2=computeBestModelRmsds(models2,benchmark_pdbs,i,j)
    print 'median rmsd:',round(Statistics.median(best_rmsds_models2),2)
    #print best_rmsds_models2
    all_best_rmsds_models2.extend(best_rmsds_models2)
    i+=num_models_per_run
#-
#print all_best_rmsds_models1
num_cases=len(all_best_rmsds_models1)
print num_cases,'rmsds per benchmark in total'


#calculate percentage of improved cases
print
print 'calculating percentage of improved cases...'
percent_improved_cases=0
for i in range(num_cases):
    rmsd1=all_best_rmsds_models1[i]
    rmsd2=all_best_rmsds_models2[i]
    if rmsd2<rmsd1:
        percent_improved_cases+=1
#--
percent_improved_cases=round(100*percent_improved_cases/float(num_cases),2)
print percent_improved_cases,'% improved cases'
if percent_improved_cases>50:
    print 'improvement in benchmark performance'
#-


#perform KS test to check for statistical significance of difference in rmsd distributions
print
print 'performing KS-test to check for statistical significance of difference in rmsd distributions...'
p_value=Statistics.KSTestPValue(all_best_rmsds_models1,all_best_rmsds_models2,'two.sided',False)
print 'p-value:',p_value
print 'performing Kruskal-Wallis test to check for statistical significance of difference in rmsd distributions...'
p_value=Statistics.KruskalWallisTestPValue(all_best_rmsds_models1,all_best_rmsds_models2,'two.sided',False)
print 'p-value:',p_value
print 'performing paired t-test (more statistical power) to check for statistical significance of difference in rmsd distributions...'
p_value=Statistics.pairedTTestPValue(all_best_rmsds_models1,all_best_rmsds_models2,'two.sided',False)
print 'p-value:',p_value


#plot rmsd comparison
print
print 'plotting rmsd comparison...'
outfile_name=outdir+'rmsd_comparison.out'
if not os.path.isdir(outdir):
    os.makedirs(outdir)
#-
rmsdScatterplot(sorted_benchmark_pdbs,id1,all_best_rmsds_models1,id2,all_best_rmsds_models2,outfile_name)
print
print outdir


end_time=time.time()
print
print "\ntime consumed: "+str(end_time-start_time)
