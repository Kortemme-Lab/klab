#!/usr/bin/python
#$ -S /usr/bin/python
#$ -cwd
#$ -r yes
#$ -l h_rt=24:00:00
#$ -t 1-995
#$ -l arch=linux-x64
#$ -l mem_free=2G
#$ -l scratch=1G

# Make sure you set task number above to be correct!!!

import socket
import sys

print "Python version:", sys.version
print "Hostname:", socket.gethostname()

from datetime import *
import os
import subprocess
import time
import sys
import shutil
import inspect
import gzip
import tempfile

try:
    import cPickle as pickle
except:
    print 'cPickle not available, using regular pickle module'
    import pickle

# This first method of setting name doesn't work on SGE
# script_name=os.path.basename(inspect.getfile(inspect.currentframe()))
script_name = 'run_mix.py' # Change me!

print "Script:",script_name

# Constants
cluster_rosetta_bin='/netapp/home/kbarlow/rosetta/designmixer/source/bin/'
cluster_rosetta_db='/netapp/home/kbarlow/rosetta/designmixer/database'

local_rosetta_bin='/home/kyleb/rosetta/working_branches/designmixer/source/bin'
local_rosetta_db='/home/kyleb/rosetta/working_branches/designmixer/database'
local_scratch_dir='/tmp'

job_pickle_file='data/job_dict.pickle'

app_name='designmixer.mysql.linuxgccrelease'

zip_rosetta_output=True

generic_rosetta_args=[
    '-mute core.conformation',
    '-mute protocols.jd2.PDBJobInputter',
    '-mute protocols.loops.loops_main',
    '-mute core.optimization.LineMinimizer',
    # '-unmute devel.fragment_mixer.FragMixMover',
    # '-out:levels devel.fragment_mixer.FragMixMover:debug',
    '-fragmix:num_fragment_applies 1050',
    '-fragmix:num_final_applies 50',
    '-fragmix:pdbs_to_load 50',
    '-out:use_database',
    '-inout:dbms:mode mysql',
    '-inout:dbms:database_name kyleb',
    '-inout:dbms:user kyleb',
    '-inout:dbms:port 3306',
    '-inout:dbms:password RN6RyLpUDF9tUbJx',
    '-inout:dbms:host guybrush-pi.compbio.ucsf.edu',
]

# Used when there is no job_dict.pickle file
job_dict={}
master_dict={}

# for i in xrange(0,3000):
#     job_dict[i]=master_dict

sge_task_id=0
run_locally=True
run_on_sge=False
if os.environ.has_key("SGE_TASK_ID"):
    sge_task_id = long(os.environ["SGE_TASK_ID"])
    run_locally=False
    run_on_sge=True

job_id=0
if os.environ.has_key("JOB_ID"):
    job_id=long(os.environ["JOB_ID"])

def roundTime(dt=None, roundTo=1):
    """Round a datetime object to any time period (in seconds)
    dt : datetime.datetime object, default now.
    roundTo : Closest number of seconds to round to, default 1 second.
    Author: Thierry Husson 2012 - Use it as you want but don't blame me.
    http://stackoverflow.com/questions/3463930/how-to-round-the-minute-of-a-datetime-object-python/10854034#10854034
    """
    if dt == None : dt = datetime.now()
    seconds = total_seconds(dt - dt.min)
    # // is a floor division, not a comment on following line:
    rounding = (seconds+roundTo/2) // roundTo * roundTo
    return dt + timedelta(0,rounding-seconds,-dt.microsecond)

def total_seconds(td):
    '''
    Included in python 2.7 but here for backwards-compatibility
    '''
    return (td.microseconds + (td.seconds + td.days * 24 * 3600) * 10**6) / 10**6

# Simple class to print out progress of each calculation
class Reporter:
    def __init__(self,task,report_interval=1):
        self.start=time.time()
        self.lastreport=self.start
        self.task=task
        self.report_interval=report_interval
        print 'Starting '+task
    def report(self,n):
        t=time.time()
        if self.lastreport<(t-self.report_interval):
            self.lastreport=t
            sys.stdout.write("  Processed: "+str(n)+"\r" )
            sys.stdout.flush()
    def done(self):
        print 'Done %s, took %.3f seconds\n' % (self.task,time.time()-self.start)

def run_single(task_id,rosetta_bin,rosetta_db,scratch_dir=local_scratch_dir,verbosity=1):
    global job_dict

    time_start = roundTime()

    if verbosity>=1:
        print 'Starting time:',time_start
        print 'Task id:',task_id

    if os.path.isfile(job_pickle_file):
        p=open(job_pickle_file,'r')
        job_dict=pickle.load(p)
        p.close()

    job_dirs=sorted(job_dict.keys())
    
    job_dir=job_dirs[task_id]

    if verbosity>=1:
        print 'Job dir:',job_dir

    # Make temporary directories
    if not os.path.isdir(scratch_dir):
        os.mkdir(scratch_dir)
    tmp_data_dir=tempfile.mkdtemp(prefix='%d.%d_data_'%(job_id,task_id),dir=scratch_dir)
    tmp_output_dir=tempfile.mkdtemp(prefix='%d.%d_output_'%(job_id,task_id),dir=scratch_dir)

    args=[
        os.path.join(rosetta_bin,app_name),
        '-database',
        rosetta_db,
        ]

    flags_dict=job_dict[job_dir]
    for flag in flags_dict:
        # Add only the key if NOAPPEND
        if not flag.startswith('NOAPPEND'):
            args.append(flag)

        # Check if argument is a file or directory
        # If so, copy to temporary data directory
        value = str(flags_dict[flag])
        if os.path.isfile(value):
            original_file=os.path.abspath(value)
            new_file=os.path.join(tmp_data_dir,os.path.basename(original_file))
            shutil.copy(original_file,new_file)
            value=os.path.relpath(new_file,tmp_output_dir)
            if verbosity>=1:
                print 'Copied file to local scratch:',os.path.basename(original_file)
        elif os.path.isdir(value):
            original_dir=os.path.abspath(value)
            new_dir=os.path.join(tmp_data_dir,os.path.basename(original_dir))
            shutil.copytree(original_dir,new_dir)
            value=os.path.relpath(new_dir,tmp_output_dir)
            if verbosity>=1:
                print 'Copied dir to local scratch:',os.path.basename(original_dir)

        args.append(value)

    args.extend(generic_rosetta_args)

    job_dir_path=os.path.join(os.getcwd(),str(job_dir))
    outfile_path=os.path.join(tmp_output_dir,'rosetta.out')
    
    if verbosity>=1:
        print 'Args:'
        print args
        print ''

    # Run Rosetta
    rosetta_outfile=open(outfile_path,'w')

    rosetta_env = os.environ.copy()
    if "LD_LIBRARY_PATH" in rosetta_env:
        rosetta_env["LD_LIBRARY_PATH"] = "/netapp/home/kbarlow/lib/mysql-connector-c-6.1.2-linux-glibc2.5-x86_64/lib:" + rosetta_env["LD_LIBRARY_PATH"]
    else:
        rosetta_env["LD_LIBRARY_PATH"] = "/netapp/home/kbarlow/lib/mysql-connector-c-6.1.2-linux-glibc2.5-x86_64/lib"

    rosetta_process=subprocess.Popen(args, stdout=rosetta_outfile, stderr=subprocess.STDOUT, close_fds = True, cwd=tmp_output_dir, env=rosetta_env )
    return_code=rosetta_process.wait()

    rosetta_outfile.close()

    if verbosity>=1:
        print 'Rosetta return code:',return_code

    if zip_rosetta_output and os.path.isfile(outfile_path):
        zip_file(outfile_path)

    if not os.path.isdir(job_dir_path):
        print 'Making jobdir: ',job_dir_path
        os.makedirs(job_dir_path)

    # Move files to job_dir from scratch dir
    for x in os.listdir(tmp_output_dir):
        x=os.path.abspath(os.path.join(tmp_output_dir,x))
        if x.endswith('.pdb'):
            x=zip_file(x)
        shutil.copy(x,job_dir_path)
        os.remove(x)
            

    # Delete temporary directories
    os.rmdir(tmp_output_dir)
    shutil.rmtree(tmp_data_dir)
        
    # Check if on SGE to move special output files
    if run_on_sge:
        shutil.move("%s.o%d.%d"%(script_name,job_id,sge_task_id),job_dir_path)
        shutil.move("%s.e%d.%d"%(script_name,job_id,sge_task_id),job_dir_path)

    time_end = roundTime()
    if verbosity>=1:
        print 'Ending time:',time_end
        print "Elapsed time:", time_end-time_start

    return time_end

def run_local():
    global job_dict

    from multiprocessing import Pool
    import multiprocessing

    class MultiWorker:
        def __init__(self,task,func):
            self.reporter=Reporter(task)
            self.func=func
            self.pool=Pool()
            self.number_finished=0
        def cb(self,time_return):
            self.number_finished+=1
            self.reporter.report(self.number_finished)
        def addJob(self,argsTuple):
            self.pool.apply_async(self.func,argsTuple,callback=self.cb)
        def finishJobs(self):
            self.pool.close()
            self.pool.join()
            self.reporter.done()

    worker=MultiWorker('running script locally',run_single)

    if os.path.isfile(job_pickle_file):
        p=open(job_pickle_file,'r')
        job_dict=pickle.load(p)
        p.close()

    num_jobs=len(job_dict.keys())

    for i in xrange(0,num_jobs+1):
        worker.addJob((i,local_rosetta_bin,local_rosetta_db,local_scratch_dir,1))

    worker.finishJobs()

def zip_file(file_path):
    if os.path.isfile(file_path):
        f_in=open(file_path,'rb')
        f_out_name=file_path+'.gz'
        f_out=gzip.open(f_out_name,'wb')
        f_out.writelines(f_in)
        f_out.close()
        f_in.close()
        os.remove(file_path)
        return f_out_name

if __name__=='__main__':
    if run_locally:
        #run_single(0,local_rosetta_bin,local_rosetta_db,scratch_dir=local_scratch_dir)
        #sys.exit(0)
        run_local()
    else:
        run_single(int(sge_task_id)-1,cluster_rosetta_bin,cluster_rosetta_db,scratch_dir='/scratch')
