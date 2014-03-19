#!/usr/bin/python
# encoding: utf-8
"""
SGE.py
Fragment generation submission module for the Sun Grid Engine.

Created by Shane O'Connor 2013

Use this as a basis for your cluster system module. The following functionality should be provided:
    - A SingleTask class for single job runs;
    - A MultipleTask class for parallel/multiple/array job runs;
    - a submit function which takes a command_filename e.g. cluster script and a working directory in which to run the script;
    - a query function which takes a logfile path and an optional job ID and returns information, via the cluster scheduler, about all jobs (if job ID is not specified) or else the specified job;
    - a check function which takes a logfile path and an optional job ID. This is similar to the query function but describes whether the job has finished or not.

"""

import sys
import os
import re
import subprocess

from ClusterTask import ClusterTask

sys.path.insert(0, "..")
from utils import colorprinter, JobInitializationException

# todo: move these into a common file e.g. utils.py
ERRCODE_ARGUMENTS = 1
ERRCODE_CLUSTER = 2
ERRCODE_OLDRESULTS = 3
ERRCODE_CONFIG = 4
ERRCODE_NOOUTPUT = 5
ERRCODE_JOBFAILED = 6
ERRCODE_MISSING_FILES = 1


class SingleTask(ClusterTask):

    submission_script ='''
#!/usr/bin/bash
#$ -N %(jobname)s
#$ -o %(outpath)s
#$ -e %(outpath)s
#$ -cwd
#$ -r y
#$ -l mem_free=1G
#$ -l arch=linux-x64
'''

    python_script_preamble = '''
import sys
from time import strftime
import socket
import os
import platform
import subprocess

class ProcessOutput(object):

    def __init__(self, stdout, stderr, errorcode):
        self.stdout = stdout
        self.stderr = stderr
        self.errorcode = errorcode
    
    def getError(self):
        if self.errorcode != 0:
            return("Errorcode: %%d\\n%%s" %% (self.errorcode, self.stderr))
        return None

def Popen(outdir, args):
    subp = subprocess.Popen([str(arg) for arg in args], stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=outdir, env={'SPARKSXDIR' : '/netapp/home/klabqb3backrub/tools/sparks-x'})
    output = subp.communicate()
    return ProcessOutput(output[0], output[1], subp.returncode) # 0 is stdout, 1 is stderr

print("<make_fragments>")

print("<start_time>")
print(strftime("%%Y-%%m-%%d %%H:%%M:%%S"))
print("</start_time>")

print("<host>")
print(socket.gethostname())
print("</host>")

print("<arch>")
print(platform.machine() + ', ' + platform.processor() + ', ' + platform.platform())
print("</arch>")

task_id = os.environ.get('SGE_TASK_ID')
'''

    python_script_postamble = '''
print("<end_time>")
print(strftime("%%Y-%%m-%%d %%H:%%M:%%S"))
print("</end_time>")

print("</make_fragments>")

if subp.errorcode != 0:
    sys.stderr.write(subp.stderr)
    sys.exit(subp.errorcode)
'''

    def __init__(self, make_fragments_perl_script, options, test_mode = False):
        '''options must contain jobname, outpath, no_homologs, NumTasks, [pdb_ids], [chains], and [fasta_files].'''
        super(SingleTask, self).__init__(make_fragments_perl_script, options)

        # NOTE: This if/elif block is specific to the QB3 cluster system and is only included for the benefit of QB3 users. Delete this line or alter it to fit your SGE cluster queue names.
        if options['queue'] not in ['long.q', 'lab.q', 'short.q']: 
            raise JobInitializationException("The queue you specified (%s) is invalid. Please use either long.q, lab.q, or short.q." % options['queue'])
        elif options['queue'] == 'short.q':
            test_mode = True

        self.test_mode = test_mode
        self.submission_script = self.__class__.submission_script
        self.set_run_length_and_queue()
        self.submission_script += '\npython python_script.py\n\n'

    def set_run_length_and_queue(self):
        if self.test_mode:
            self.submission_script += '#$ -l h_rt=0:29:00\n'
        else:
            self.submission_script += '#$ -l h_rt=6:00:00\n'
        self.submission_script += '#$ -q %s\n' % self.options['queue']

    def get_scripts(self):
        options = self.options

        assert(1 == len(options['job_inputs']))
        jobname = options['jobname']
        outpath = options['outpath']
        make_fragments_perl_script = self.make_fragments_perl_script

        pdb_id = options['job_inputs'][0].pdb_id
        chain = options['job_inputs'][0].chain
        fasta_file = options['job_inputs'][0].fasta_file

        fasta_file_dir = os.path.split(fasta_file)[0]
        no_homologs = options['no_homologs']

        python_script = '''
job_root_dir = "%(fasta_file_dir)s"
print("<cwd>")
print(job_root_dir)
print("</cwd>")

print("<cmd>")
cmd_args = [c for c in ['%(make_fragments_perl_script)s', '-verbose', '-id', '%(pdb_id)s%(chain)s', '%(no_homologs)s', '%(fasta_file)s'] if c]
print(' '.join(cmd_args))
print("</cmd>")

print("<output>")
subp = Popen(job_root_dir, cmd_args)
sys.stdout.write(subp.stdout)
print("</output>")
''' % locals()

        return 'submission_script.sh', {
            'submission_script.sh' : self.submission_script % locals(),
            'python_script.py' : '\n'.join([self.__class__.python_script_preamble, python_script, self.__class__.python_script_postamble]) % locals()
        }


class MultipleTask(SingleTask):

    # The command line used to call the fragment generating script. Add -noporter into cmd below to skip running Porter
    cmd = 'make_fragments_RAP_cluster.pl -verbose -id %(pdbid)s%(chain)s %(no_homologs)s %(fasta)s'

    submission_script = SingleTask.submission_script + '#$ -t 1-%(num_tasks)d\n'

    def get_scripts(self):
        options = self.options

        jobname = options['jobname']
        outpath = options['outpath']
        make_fragments_perl_script = self.make_fragments_perl_script

        job_inputs = options['job_inputs']
        num_tasks = len(options['job_inputs'])


        no_homologs = options['no_homologs']

        job_arrays = []
        job_arrays.append('chains = %s' % str([ji.chain for ji in job_inputs]))
        job_arrays.append('pdb_ids = %s' % str([ji.pdb_id for ji in job_inputs]))
        job_arrays.append('fasta_files = %s' % str([ji.fasta_file for ji in job_inputs]))
        job_arrays = '\n'.join(job_arrays)

        python_script = '''

idx = int(task_id) - 1
chain = chains[idx]
pdb_id = pdb_ids[idx]
fasta_file = fasta_files[idx]

job_root_dir = os.path.split(fasta_file)[0]
print("<cwd>")
print(job_root_dir)
print("</cwd>")

print("<cmd>")
cmd_args = [c for c in ['%(make_fragments_perl_script)s', '-verbose', '-id', pdb_id + chain, '%(no_homologs)s', fasta_file] if c]
print(' '.join(cmd_args))
print("</cmd>")

print("<output>")
subp = Popen(job_root_dir, cmd_args)
sys.stdout.write(subp.stdout)
print("</output>")
''' % locals()

        return 'submission_script.sh', {
            'submission_script.sh' : self.submission_script % locals(),
            'python_script.py' : '\n'.join([self.__class__.python_script_preamble, job_arrays, python_script, self.__class__.python_script_postamble]) % locals()
        }


def submit(command_filename, workingdir):
    '''Submit the given command filename to the queue. Adapted from the qb3 example.'''

    # Open streams
    command_filename = command_filename
    outfile = command_filename + ".out"
    file_stdout = open(outfile, 'w')

    # Form command
    command = ['qsub']
    command.append(command_filename)

    # Submit the job and capture output.
    try:
        subp = subprocess.Popen(command, stdout=file_stdout, stderr=file_stdout, cwd=workingdir)
    except Exception, e:
        colorprinter.error('Failed running qsub command: %s in cwd %s.' % (command, workingdir))
        raise

    waitfor = 0
    errorcode = subp.wait()
    file_stdout.close()

    file_stdout = open(outfile, 'r')
    output = file_stdout.read().strip()
    file_stdout.close()

    if errorcode != 0:
        colorprinter.error('Failed running qsub command: %s in cwd %s.' % (command, workingdir))
        if output.find("unable to contact qmaster") != -1:
            raise Exception("qsub failed: unable to contact qmaster")
        else:
            raise Exception(output)

    # Match job id
    # This part of the script may be error-prone as it depends on the server message.
    matches = re.match('Your job-array (\d+).(\d+)-(\d+):(\d+)', output)
    if not matches:
        matches = re.match('Your job (\d+) \(".*"\) has been submitted.*', output)

    if matches:
        jobid = int(matches.group(1))
    else:
        jobid = -1

    output = output.replace('"', "'")
    if output.startswith("qsub: ERROR"):
        raise Exception(output)

    os.remove(outfile)
    #os.remove(command_filename)

    return jobid, output


def query(logfile, jobID = None):
    """If jobID is an integer then return False if the job has finished and True if it is still running.
       Otherwise, returns a table of jobs run by the user."""
    
    joblist = logfile.readFromLogfile()
    if jobID and type(jobID) == type(1):
        command = ['qstat', '-j', str(jobID)]
    else:
        command = ['qstat']

    processoutput = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()
    output = processoutput[0]
    serror = processoutput[1]
    # Form command
    jobs = {}
    if type(jobID) == type(1):
        if serror.find("Following jobs do not exist") != -1:
            return False
        else:
            return True

    if not output.strip():
        colorprinter.message("No jobs running at present.")
    output = output.strip().split("\n")
    if len(output) > 2:
        for line in output[2:]:
            # We assume that our script names contain no spaces for the parsing below to work (this should be ensured by ClusterTask)
            tokens = line.split()
            jid = int(tokens[0])
            jobstate = tokens[4]

            details = {  "jobid" : jid,
                         "prior" : tokens[1],
                         "name" : tokens[2],
                         "user" : tokens[3],
                         "state" : jobstate,
                         "submit/start at" : "%s %s" % (tokens[5], tokens[6])
                         }
            jataskID = 0
            if jobstate == "r":
                details["queue"] = tokens[7]
                details["slots"] = tokens[8]
            elif jobstate == "qw":
                details["slots"] = tokens[7]
                if len(tokens) >= 9:
                    jataskID = tokens[8]
                    details["ja-task-ID"] = jataskID

            if len(tokens) > 9:
                jataskID = tokens[9]
                details["ja-task-ID"] = jataskID

            jobs[jid] = jobs.get(jid) or {}
            jobs[jid][jataskID] = details
            if joblist.get(jid):
                jobdir = joblist[jid]["Directory"]
                jobtime = joblist[jid]["TimeInSeconds"]
                colorprinter.message("Job %d submitted %d minutes ago. Status: '%s'. Destination directory: %s." % (jid, jobtime / 60, jobstate, jobdir))
            else:
                colorprinter.message("Job %d submitted at %s %s. Status: '%s'. Destination directory unknown." % (jid, tokens[5], tokens[6], jobstate))
        return True


def check(logfile, job_id, cluster_job_name):
    # todo: this needs to be updated for array jobs
    errors = []
    joblist = logfile.readFromLogfile()
    jobIsRunning = query(logfile, job_id)
    if not joblist.get(job_id):
        if not jobIsRunning:
            errors.append("Job %d is not running but also has no entry in the logfile %s." % (job_id, logfile.getName()))
        else:
            errors.append("Job %d is running but has no entry in the logfile %s." % (job_id, logfile.getName()))
    else:
        cname = cluster_job_name
        dir = joblist[job_id]["Directory"]
        if not jobIsRunning:
            outputfile = os.path.join(dir, "%(cname)s.o%(job_id)d" % vars())
            if os.path.exists(outputfile):
                F = open(outputfile, "r")
                contents = F.read()
                F.close()
                success = re.compile('''Done!\s*</output>\s*<enddate>(.*?)</enddate>\s*</make_fragments>\s*$''', re.DOTALL)
                match = success.search(contents)
                if match:
                    colorprinter.message("Job %d finished successfully on %s. Results are in %s." % (job_id, match.groups(1)[0].strip(), dir))
                else:
                    errors.append("Job %d has finished running but was not successful. Results are in %s." % (job_id, dir))
                    errcode = ERRCODE_JOBFAILED
            else:
                    errors.append("The output file %s associated with job %d could not be found. Searched in %s." % (outputfile, job_id, dir))
                    errcode = ERRCODE_NOOUTPUT
        else:
            colorprinter.warning("Job %d is still running. Results are being stored in %s." % (job_id, dir))
    return errors
