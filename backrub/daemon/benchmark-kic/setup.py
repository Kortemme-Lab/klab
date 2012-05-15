#!/usr/bin/python
#This file was developed and written by Roland A. Pache, Ph.D., Copyright (C) 2012.

#import libraries
import re
import os
import time
import sys
import functions_lib


print '\nPrepares the run directories for the KIC scientific benchmark on the cluster (assuming a qsub system).\n'


#constants
run_test_cycles=False #set to True for testing
use_constant_seed=False #set to True for benchmarking only (all models will be the same)
memory_requirement='2G'
runtime_limit='6:00:00'
max_kic_build_attempts=1000000

#patterns

#define classes

#define functions
            
start_time=time.time()


#parse input parameters
if len(sys.argv)!=2:
    print
    print 'Usage: ./setup_KIC_scientific_benchmark.py PARAMETER_FILE'
    print
    sys.exit()
#-
parameter_file=sys.argv[1]
parameters=functions_lib.parseParameterFile(parameter_file)
structures_indir=parameters['minimized_starting_structures']
loops_indir=parameters['loop_definitions']
num_models_offset=int(parameters['num_models_offset'])
num_models_per_PDB=int(parameters['num_models_per_PDB'])
cluster_queue=parameters['cluster_queue']
cluster_architecture=parameters['cluster_architecture']
rosetta_executable=parameters['Rosetta_executable']
rosetta_database=parameters['Rosetta_database']
extra_rosetta_flags=parameters['extra_Rosetta_flags']
outdir=parameters['models_outdir']

print
print 'extra Rosetta flags:',extra_rosetta_flags


#for all input structures
structures_indir_contents=os.listdir(structures_indir)
for item in structures_indir_contents:
    if item.endswith('.pdb'):
        input_pdb=structures_indir+item
        pdb_prefix=item.split('.pdb')[0].split('_')[0]
        pdb_outdir=outdir+pdb_prefix+'/'

        #check for existence of corresponding loop file
        loop_file=loops_indir+pdb_prefix+'.loop'
        if not os.path.isfile(loop_file):
            print 'ERROR: loop file of '+item+' not found in '+loops_indir
            sys.exit()
        #-

        #create model subdirs for parallel runs on the cluster (to ensure that models from different runs don't overwrite each other)
        for i in range(num_models_offset+1,num_models_offset+num_models_per_PDB+1):
            model_outdir=pdb_outdir+str(i)+'/'
            if not os.path.isdir(model_outdir):
                os.makedirs(model_outdir)
        #--

        #write grid engine script
        qs_script_name=pdb_outdir+'KIC_scientific_benchmark-'+pdb_prefix+'.qs'
        qs_script_string='\
        \n#!/bin/csh\
        \n#$ -N KIC_scientific_benchmark\
        \n#$ -o '+pdb_outdir+'\
        \n#$ -e '+pdb_outdir+'\
        \n#$ -cwd\
        \n#$ -q '+cluster_queue+'\
        \n#$ -r y\
        \n#$ -l mem_free='+memory_requirement+'\
        \n#$ -l arch='+cluster_architecture+'\
        \n#$ -l h_rt='+runtime_limit+'\
        \n#$ -t '+str(num_models_offset+1)+'-'+str(num_models_offset+num_models_per_PDB)+'\
        \n\
        \necho start_date:\
        \ndate\
        \nhostname\
        \necho $SGE_TASK_ID\
        \necho\
        \n\
        \ncd '+pdb_outdir+'$SGE_TASK_ID/\
        \n\
        \n'+rosetta_executable+' -database '+rosetta_database+' -loops:input_pdb '+input_pdb+' -in:file:fullatom -loops:loop_file '+loop_file+' -loops:remodel perturb_kic -loops:refine refine_kic -in:file:native '+input_pdb+' -out:prefix '+pdb_prefix+' -overwrite -out:path '+pdb_outdir+'$SGE_TASK_ID/ -ex1 -ex2 -nstruct 1 -out:pdb_gz -loops:max_kic_build_attempts '+str(max_kic_build_attempts)+' '+extra_rosetta_flags
        if run_test_cycles:
            qs_script_string+=' -run:test_cycles'
        #-
        if use_constant_seed:
            qs_script_string+=' -constant_seed'
        #-
        qs_script_string+='\
        \n\
        \necho\
        \necho moving .e and .o files to task subdir...\
        \nmv ../*.e$JOB_ID.$SGE_TASK_ID .\
        \nmv ../*.o$JOB_ID.$SGE_TASK_ID .\
        \necho\
        \necho $SGE_TASK_ID\
        \necho end_date:\
        \ndate\
        \n\n'
        functions_lib.newFile(qs_script_string,qs_script_name)
        print qs_script_name
#--


end_time=time.time()
print "\ntime consumed: "+str(end_time-start_time)
