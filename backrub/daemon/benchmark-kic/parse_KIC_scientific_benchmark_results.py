#!/usr/bin/python
#This file was developed and written by Roland A. Pache, Ph.D., Copyright (C) 2012.

#import libraries
import re
import os
import time
import sys
import functions_lib
import datetime


print '\nParses the KIC scientific benchmark results into a flatfile.\n'


#constants
output_time_format="%s"

#patterns

#define classes

#define functions

            
start_time=time.time()


#parse input parameters
if len(sys.argv)!=2:
    print
    print 'Usage: ./parse_KIC_scientific_benchmark_results.py PARAMETER_FILE'
    print
    sys.exit()
#-
parameter_file=sys.argv[1]
parameters=functions_lib.parseParameterFile(parameter_file)
num_models_offset=int(parameters['num_models_offset'])
num_models_per_PDB=int(parameters['num_models_per_PDB'])
indir=parameters['models_outdir']
input_time_format=parameters['input_time_format']
outfile_name=parameters['results_flatfile']


#prepare outfile
outfile=open(outfile_name,'w')
outfile.write('#PDB\tModel\tLoop_rmsd\tTotal_energy\tRuntime\n')


#parse benchmark results
print indir
start_index=num_models_offset+1
end_index=num_models_offset+num_models_per_PDB
sorted_indir_contents=sorted(os.listdir(indir))
for pdb in sorted_indir_contents:
    print
    print pdb
    pdb_runtimes=[]
    num_models=0
    pdb_dir=indir+pdb+'/'
    pdb_dir_contents=os.listdir(pdb_dir)
    #copy output and error files to model subdirs
    for item in pdb_dir_contents:
        if '.o' in item or '.e' in item:
            model_subdir=item.split('.')[-1]
            functions_lib.run('cp '+pdb_dir+item+' '+pdb_dir+model_subdir+'/')
    #--
    #parse output files to collect energies, rmsds and runtimes
    for item in pdb_dir_contents:
        if os.path.isdir(pdb_dir+item) and int(item)>=start_index and int(item)<=end_index:
            model_subdir=pdb_dir+item+'/'
            model_subdir_contents=os.listdir(model_subdir)
            for item2 in model_subdir_contents:
                if '.o' in item2:
                    stats=[]
                    text=functions_lib.run_return('head -n 4 '+model_subdir+item2)
                    text+=functions_lib.run_return('tail -n 9 '+model_subdir+item2)
                    lines=text.split('\n')
                    if len(lines)>11 and lines[-3]=='end_date:':
                        #calculate runtime
                        start_time=int(datetime.datetime.strftime(datetime.datetime.strptime(lines[3],input_time_format),output_time_format))
                        end_time=int(datetime.datetime.strftime(datetime.datetime.strptime(lines[-2],input_time_format),output_time_format))
                        runtime=end_time-start_time
                        total_energy=None
                        loop_rms=None
                        #determine loop rmsd and total energy of the pose
                        for line in lines:
                            if 'total_energy' in line:
                                total_energy=float(line.split('total_energy:')[1].strip(' '))
                            elif 'loop_rms' in line:
                                loop_rms=float(line.split('loop_rms:')[1].strip(' '))
                        #--
                        if total_energy!=None and loop_rms!=None:
                            num_models+=1
                            #write to outfile
                            outfile.write(pdb+'\t'+item+'\t'+str(loop_rms)+'\t'+str(total_energy)+'\t'+str(runtime)+'\n')
                            pdb_runtimes.append(runtime)
    #------
    print num_models,'models created successfully'
#-
outfile.close()
print
print outfile_name                


end_time=time.time()
print "\ntime consumed: "+str(end_time-start_time)
