#!/usr/bin/python
# encoding: utf-8
"""
SGE.py
Fragment generation submission module for the Sun Grid Engine.

Created by Shane O'Connor 2013

Use this as a basis for your cluster system module. The following functionality should be provided:
    - A SingleTask class for single job runs;
    - A MultipleTask class for parallel/multiple/array job runs;
    - a query function which takes a job ID and returns information about the job via the cluster scheduler;
    - a submit function
"""

import sys
import os
import re
import subprocess

from ClusterTask import ClusterTask

sys.path.insert(0, "..")
from utils import colorprinter

class SingleTask(ClusterTask):

    # The command line used to call the fragment generating script. Add -noporter into cmd below to skip running Porter
    cmd = 'make_fragments_RAP_cluster.pl -verbose -id %(pdbid)s%(chain)s %(no_homologs)s %(fasta)s'

    script_header ='''
#!/usr/bin/python
#$ -N %(jobname)s
#$ -o %(outpath)s
#$ -e %(outpath)s
#$ -cwd
#$ -r y
#$ -l mem_free=1G
#$ -l arch=lx24-amd64
#$ -l h_rt=6:00:00
'''
    job_header = '''
from time import strftime
import socket
import os
import platform
import subprocess

print("<make_fragments>")

print("<start_time>")
print(strftime("%%Y-%%m-%%d %%H:%%M:%%S"))
print("</start_time>")

print("<host>")
print(socket.gethostname())
print("</host>")

print("<arch>")
print(platform.machine() + ', ' + platform.processor() + ', ' + platform.platform()))
print("</arch>")

'''

    job_cmd = '''
workingdir = %(outpath)s
print("<cwd>")
print(workingdir)
print("</cwd>")

print("<cmd>")
print(' '.join(%(cmd_list)s))
print("</cmd>")

print("<output>")
subp = subprocess.Popen(%(cmd_list)s, stdout=file_stdout, stderr=file_stdout, cwd=workingdir)
print("</output>")

'''

    job_footer = '''
print("<end_time>")
print(strftime("%%Y-%%m-%%d %%H:%%M:%%S"))
print("</end_time>")

subp = subprocess.Popen(['qstat', '-xml', '-j', os.environ['JOB_ID'], stdout=file_stdout, stderr=file_stdout, cwd=workingdir)

print("</make_fragments>")
'''

    def __init__(self):
        self.script = '%s%s%s%s' %(self.__class__.script_header, self.__class__.job_header, self.__class__.job_cmd, self.__class__.job_footer)

    def get_script(self, cmd_list, outpath, jobname, NumTasks = 1):
        assert(NumTasks == 1)
        return self.script % locals()

class MultipleTask(SingleTask):

    job_header = SingleTask.script_header + '''
#$ -t 1-%(NumTasks)s

array_job_input_ids = %(input_ids)s
task_input_id = array_job_input_ids[int(os.environ['SGE_TASK_ID']) - 1]

'''
    job_cmd = '''
working_dir = os.path.join("%(outpath)s", task_input_id)
os.mkdir(working_dir)
print("<cwd>")
print(workingdir)
print("</cwd>")

print("<output>")
subp = subprocess.Popen(%(cmd_list)s, stdout=file_stdout, stderr=file_stdout, cwd=working_dir)
print("</output>")
'''

    def get_script(self, cmd_list, outpath, jobname, NumTasks):
        if NumTasks == 1:
            return super(MultipleTask, self).get_script(cmd_list, outpath, jobname, NumTasks)
        return self.script % locals()



def submit(command_filename, workingdir, hold_jobid = None, showstdout = False):
    '''Submit the given command filename to the queue. Adapted from the qb3 example.'''

    # Open streams
    command_filename = command_filename
    outfile = command_filename + ".out"
    file_stdout = open(outfile, 'w')

    # Form command
    command = ['qsub']
    if hold_jobid:
        command.append('-hold_jid')
        command.append('%d' % hold_jobid)
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
    print(output)

    os.remove(outfile)
    os.remove(command_filename)

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


def check(logfile, job_id):
    joblist = logfile.readFromLogfile()
    jobIsRunning = query(logfile, job_id)
    if not joblist.get(job_id):
        if not jobIsRunning:
            errors.append("Job %d is not running but also has no entry in the logfile %s." % (job_id, logfile.getName()))
        else:
            errors.append("Job %d is running but has no entry in the logfile %s." % (job_id, logfile.getName()))
    else:
        global clusterJobName
        cname = clusterJobName
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
