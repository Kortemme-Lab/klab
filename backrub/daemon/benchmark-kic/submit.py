#!/usr/bin/python
#This file was developed and written by Roland A. Pache, Ph.D., Copyright (C) 2012.

#import libraries
import re
import os
import time
import sys
import functions_lib


print '\nSubmits the KIC scientific benchmark on the cluster, using qsub.\n'


#constants

#patterns

#define classes

#define functions
            
start_time=time.time()


#parse input parameters
if len(sys.argv)!=2:
    print
    print 'Usage: ./submit_KIC_scientific_benchmark.py PARAMETER_FILE'
    print
    sys.exit()
#-
parameter_file=sys.argv[1]
parameters=functions_lib.parseParameterFile(parameter_file)
structures_indir=parameters['minimized_starting_structures']
outdir=parameters['models_outdir']


#submit grid engine scripts
print
print 'submitting KIC scientific benchmark...'
structures_indir_contents=os.listdir(structures_indir)
for item in structures_indir_contents:
    if item.endswith('.pdb'):
        pdb_prefix=item.split('.pdb')[0].split('_')[0]
        pdb_outdir=outdir+pdb_prefix+'/'
        functions_lib.run('for i in '+pdb_outdir+'*.qs; do ls $i; qsub $i; done')
#--

end_time=time.time()
print "\ntime consumed: "+str(end_time-start_time)
