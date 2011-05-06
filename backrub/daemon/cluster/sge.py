#!/usr/bin/env python

# Set up array jobs for QB3 cluster.
import sys
sys.path.insert(0, "../")
import commands
import re
import subprocess
import time
from string import join, strip
from conf_daemon import *

print(clusterRootDir)
DEBUG = False
clusterUserAccount = "klabqb3backrub"
qstatLastCalled = None
qstatWaitingPeriod = float(CLUSTER_qstatpause) - 0.2
emptyDict = {}

#scp tempdir/* shaneoconner@chef.compbio.ucsf.edu:/netapp/home/shaneoconner/temp/tempdir
#publickey = /netapp/home/shaneoconner/.ssh/id_rsa.pub

#todo: This logic may be flawed - check that qstat displays all pending jobs
def isRunning(jobid):
    jobs = qstat()
    for job in jobs:
        if job[job-ID] == "%s" % str(jobid):
            return True
    return False

class qjob(object):
    
    def __init__(self, data, separator = ", "):
        self.data = data
        self.separator = separator
        
    def __str__(self):
        if self.data:
            jobs = []
            s = ""
            for details in self.data:
                s += "Job %s" % details["jobid"]
                if details.get("ja-task-ID"):
                    s += ", subtask %s" % details["ja-task-ID"]
                s += " (%s): " % details["user"]    
                if details["state"] == "r":
                    s += "active"
                elif details["state"] == "qw":
                    s += "pending"
                elif details["state"] == "t":
                    s += "transferring"
                else:
                    s += "status logic for '%s' missing in python script!" % details["state"]
                jobs.append(s)
                s = ""
            return join(jobs, self.separator)
        else:
            return "Job does not exist."
            
def qstat(jobid = None, jobs = None, user = clusterUserAccount):
    """ Returns a table of jobs run by the current user."""
    
    #debug: for testing without submission - 
    if DEBUG:
        if jobid:
            return None, {}
        else:
            return {}
    
    global qstatLastCalled
    global qstatWaitingPeriod
 
    if type(jobs) != type(emptyDict):
        if qstatLastCalled > 0 and ((time.time() - qstatLastCalled) < qstatWaitingPeriod):
            print("<warning>QSTAT is being called more regularly than %fs.</warning>" % qstatWaitingPeriod)
        
        qstatLastCalled = time.time()
        #print("QSTAT: %f" % qstatLastCalled)
        command = 'qstat -u "%s"' % user  #"shaneoconner"' # jlmaccal qstat -u "kortemme-pi"  ,    qstat -u "*"
        output = commands.getoutput(command)
        output = output.split("\n")
        jobs = {}
        if len(output) > 2:
            for line in output[2:]:
                # We must ensure our task names contain no spaces for the parsing below to work 
                tokens = line.split()
                jid = int(tokens[0])
                jobstate = tokens[4]
                            
                details = {   #"line" : line, # for debugging
                             #"tokens" : tokens, # for debugging
                             "jobid" : jid,
                             "prior" : tokens[1],
                             "name" : tokens[2],
                             "user" : tokens[3],
                             "state" : jobstate,
                             "submit/start at" : "%s %s" % (tokens[5], tokens[6])}
                
                if jobstate == "r":
                    details["queue"] = tokens[7]
                    details["slots"] = tokens[8]
                elif jobstate == "qw":
                    details["slots"] = tokens[7]
                if len(tokens) > 9:
                    details["ja-task-ID"] = tokens[9]
                    
                jobs[jid] = jobs.get(jid) or []
                jobs[jid].append(details)
    
    if jobid:
        if jobs.get(jobid):
            return qjob(jobs[jobid]), jobs
        else:
            return None, jobs
    else:
        return jobs

def qsub_submit(command_filename, workingdir, hold_jobid = None, name = None, showstdout = False):
    """Submit the given command filename to the queue.
    
    ARGUMENTS
        command_filename (string) - the name of the command file to submit
    
    OPTIONAL ARGUMENTS
        hold_jobid (int) - job id to hold on as a prerequisite for execution
    
    RETURNS
        jobid (integer) - the jobid
    """
    
    #debug: for testing without submission - 
    if DEBUG:
        return 1

    # Open streams
    file_stdout = open(command_filename + ".temp.out", 'w')
    file_stderr = open(command_filename + ".temp.out", 'w')
        
    # Form command
    command = ['qsub']
    if name:
        command.append('-N')
        command.append('%s' % name)
    if hold_jobid:
        command.append('-hold_jid')
        command.append('%d' % hold_jobid)
    command.append('%s' % command_filename)
    
    # Submit the job and capture output.
    subp = subprocess.Popen(command, stdout=file_stdout, stderr=file_stderr, cwd=workingdir)
    waitfor = 0
    errorcode = subp.wait()
    file_stdout.close()
    file_stdout = open(command_filename + ".temp.out", 'r')
    output = strip(file_stdout.read())
    file_stdout.close()
    file_stderr.close()
        
    # Match job id
    # This part of the script is probably error-prone as it depends on the server message.
    matches = re.match('Your job-array (\d+).(\d+)-(\d+):(\d+)', output)
    if not matches:
        matches = re.match('Your job (\d+) \(".*"\) has been submitted.*', output)
    
    if matches:
        return int(matches.group(1)), output
    else:
        return -1, output

if __name__ == "__main__":
    thisjob, jobs = qstat(1)
    print(thisjob)