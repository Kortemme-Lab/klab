#!/usr/bin/env python

# Set up array jobs for QB3 cluster.
import sys
sys.path.insert(0, "../")
sys.path.insert(0, "../../common/")
import os
import time
import shutil
import tempfile
import re
import glob
from string import join

import SimpleProfiler
import sge
from rosettahelper import make755Directory, makeTemp755Directory, writeFile
from RosettaProtocols import *
from conf_daemon import *

INITIAL_TASK = 0
INACTIVE_TASK = 1
ACTIVE_TASK = 2
RETIRED_TASK = 3
COMPLETED_TASK = 4
FAILED_TASK = 5

status = {
    INITIAL_TASK    : "pending",
    INACTIVE_TASK   : "pending",
    ACTIVE_TASK     : "active",
    RETIRED_TASK    : "retired",
    COMPLETED_TASK  : "completed",
    FAILED_TASK     : "failed",
    }

def getClusterDatabasePath(binary, cluster_database_index = 0):
    if cluster_database_index in range(len(RosettaBinaries[binary]["cluster_databases"])):
        return "%s/%s/%s" % (clusterRootDir, RosettaBinaries[binary]["clusterrev"], RosettaBinaries[binary]["cluster_databases"][cluster_database_index])

class ClusterScript:
    
    def __init__(self, workingdir, binary, numtasks = 0, dataarrays = {}, maxhours = 335, maxmins = 59):
        self.contents = []
        self.tasks = []
        self.parameters = {"workingdir": workingdir, "taskline": "", "taskparam" : "", "taskvar" : "", "maxhours": maxhours, "maxmins": maxmins}
        if numtasks > 0:
            if dataarrays:
                for arrayname, contents in sorted(dataarrays.iteritems()):
                    self.parameters["taskline"] += "%s=( dummy %s )\n" % (arrayname, join(contents, " "))
                    self.parameters["taskvar"]  += '%svar=${%s[$SGE_TASK_ID]}\n' % (arrayname, arrayname)     
                #self.parameters["taskline"] = "tasks=( dummy %s )" % join(tasks, " ")
                #self.parameters["taskvar"] = 'taskvar=${tasks[$SGE_TASK_ID]}"'
            self.parameters["taskparam"] = "#$ -t 1-%d" % numtasks #len(tasks)
        self.revision = RosettaBinaries[binary]["clusterrev"]
        self.bindir = "%s/%s" % (clusterRootDir, self.revision)
        self.workingdir = workingdir
        self.script = None

        global _debugmode
        if _debugmode: 
            self.parameters["maxhours"] = 0
            self.parameters["maxmins"] = 10

    # todo: try #$ -l h_rt=40:00:00
    #       and #$ -l mem_free=2G
    

    def _addPreamble(self):

        self.contents.insert(0, """\
#!/bin/bash
#
#$ -S /bin/bash
#$ -o %(workingdir)s
#$ -e %(workingdir)s
#$ -cwd
#$ -r y
#$ -j n
#$ -l arch=lx24-amd64
#$ -l panqb3=1G,scratch=1G,mem_total=3G
#$ -l h_rt=%(maxhours)d:%(maxmins)d:00
%(taskparam)s
%(taskline)s
%(taskvar)s
echo off

echo "<startdate>"
date
echo "</startdate>"
echo "<host>"
hostname
echo "</host>"
echo "<cwd>"
pwd
echo "</cwd>"

echo "<arch>"
uname -i
echo "</arch>"

#setenv TMPDIR /scratch
#setenv MYTMP `mktemp -d`
#echo $MYTMP
#cd $MYTMP
""" % self.parameters)

    def _addTask(self, lines, type, attributes):
        attstring = ""
        if attributes:
            for k,v in attributes:
                attstring += '%s = "%s" ' % (k, v)
        if attstring:
            attstring = " " + attstring       
        if type:
            self.contents.append('echo -n "<%s%s"' % (type, attstring))
            self.contents.append('if [ -n "${SGE_TASK_ID+x}" ]; then')
            self.contents.append('echo -n " \\"subtask=$SGE_TASK_ID\\"" ')
            self.contents.append('fi')
            self.contents.append('echo ">"')
                        
        self.contents.append(join(lines, "\n"))
        
        if type:
            self.contents.append('echo "</%s>"\n' % type)
    
    def _addEpilogue(self):
        self.contents.append("""
echo "<enddate>"
date
echo "</enddate>"
""")

    def createScript(self, lines, type = "", attributes = {}):
        self._addPreamble()
        self._addTask(lines, type, attributes)
        self._addEpilogue()
        self.script = join(self.contents, "\n")
        return self.script
    
    def getBinary(self, binname):
        return "%s/%s_%s_static" % (self.bindir, binname, self.revision)
    
    def getDatabaseDir(self):
        return "%s/rosetta_database/" % self.bindir
    
    def getWorkingDir(self):
        return self.workingdir

class ClusterTask(object):
    prefix = "task"
    
    def __init__(self, workingdir, targetdirectory, scriptfilename, parameters = {}, name = ""):
        self.profiler = SimpleProfiler.SimpleProfiler(name)
        self.profiler.PROFILE_START("Initialization")
        self.parameters = parameters
        self.failOnStdErr = True
        self.debug = True
        self.targetdirectory = targetdirectory
        self.jobid = 0
        self.script = None
        self.state = INACTIVE_TASK
        self.dependents = []
        self.prerequisites = {}
        self.workingdir = workingdir
        self.scriptfilename = scriptfilename
        self.filename = os.path.join(workingdir, scriptfilename)
        self.cleanedup = False
        self.filename_stdout = None
        self.filename_stderr = None
        self.name = name or "unnamed"
        self.numtasks = 1
        self.outputstreams = []
        if parameters.get("pdb_filename"):
            parameters["pdbRootname"] = parameters["pdb_filename"][:-4]
        self._initialize()
        self.profiler.PROFILE_STOP("Initialization")
    
    def _initialize(self):
        '''Override this function.'''
        raise Exception
    
    def _workingdir_file_path(self, filename):
        """Get the path for a file within the working directory"""
        return os.path.join(self.workingdir, filename)   

    def _targetdir_file_path(self, filename):
        """Get the path for a file within the working directory"""
        return os.path.join(self.targetdirectory, filename)   
    
    def getOutputStreams(self):
        return self.outputstreams

    def getExpectedOutputFileNames(self):
        outputFilenames = []
        for i in range(1, self.numtasks + 1):
            outputFilenames.append("%s_%d.cmd.o%d.%d" % (self.prefix, self.parameters["ID"], self.jobid, i))
        return outputFilenames 

    def getName(self):
        return self.name
        
    def start(self):
        # Our job submission engine is sequential at present so we use one filename
        # todo: use a safe equivalent of tempname
        if self.script:
            self._status("Starting %s" % self.name)
            # Copy files from prerequisites
            for prereq, files in self.prerequisites.iteritems():
                self._status("Copying prerequisites for %s" % self.name)
                prereq.copyFiles(self.workingdir, files)
                
            writeFile(self.filename, self.script)
            #print(self.script)
            self.jobid, stdo = sge.qsub_submit(self.filename, self.workingdir, name = self.scriptfilename, showstdout = self.debug)
            self._status("<qsub>%s</qsub>" % stdo, plain = True)
            self._status("Job started with id %d." % self.jobid)
            if self.jobid != 0:
                self.profiler.PROFILE_START("Execution")
                self.state = ACTIVE_TASK
                return self.jobid
        else:
            return 0
        #print "Submitted. jobid = %d" % jobid
        # Write jobid to a file.
        #import subprocess
        #p = subprocess.call("echo %d >> jobids" % jobid, shell=True)
    
    def copyFiles(self, targetdirectory, filemasks = ["*"]):
        for mask in filemasks:
            #todo: This will copy the files to the dependent task's directory on chef
            self._status('os.system("cp %s/%s %s")' % (self.workingdir, mask, targetdirectory))
            for file in glob.glob(self._workingdir_file_path(mask)):
                self._status('copying %s' % file)
                shutil.copy(file, targetdirectory)
           
    
    def _copyFilesBackToHost(self, filemasks = ["*"]):
        if type(filemasks) == type(""):
            filemasks = [filemasks]
        for p in filemasks:
            for file in glob.glob(self._workingdir_file_path(p)):
                self._status('copying %s' % file)
                shutil.copy(file, self.targetdirectory)    
        
    def retire(self):
        """ This is the place to implement any interim postprocessing steps for your task to generate input the dependents require (Pay it forward).
            All necessary input files for dependents should be copied back to the originating host here. 
            e.g.  -check if all files were created
                  -execute analysis
                  -optionally get rid of unused files
                  -copy any files needed for dependent steps back to the originating host.
            By default, this function creates a target directory on the host and copies all stdout and stderr files to it.
            If any of the stderr files have non-zero size, the default behaviour is to mark the task as failed."""
        
        #todo: This will copy the output files from the cluster submission host back to the originating host
        self._status("Retiring %s" % self.name)
        
        if not os.path.isdir(self.targetdirectory):
            # The root of self.targetdirectory should exists - otherwise we should not
            # create the tree here as there is probably a bug in the code
            make755Directory(self.targetdirectory)
        
        clusterScript = self._workingdir_file_path(self.scriptfilename)
        if os.path.exists(clusterScript):
            shutil.copy(clusterScript, self.targetdirectory)
                    
        if self.scriptfilename:
            failedOutput = False
            for i in range(1, self.numtasks + 1):
            
                if self.numtasks == 1:
                    filename_stdout = "%s.o%s" % (self.scriptfilename, self.jobid)
                    filename_stderr = "%s.e%s" % (self.scriptfilename, self.jobid)
                else:
                    filename_stdout = "%s.o%s.%d" % (self.scriptfilename, self.jobid, i)
                    filename_stderr = "%s.e%s.%d" % (self.scriptfilename, self.jobid, i)
                
                stderrhasfailed = False
                    
                if os.path.exists(self._workingdir_file_path(filename_stdout)):
                    self.filename_stdout = filename_stdout
                    self._status('shutil.copy(%s %s")' % (self._workingdir_file_path(filename_stdout), self.targetdirectory))
                    shutil.copy(self._workingdir_file_path(filename_stdout), self.targetdirectory)
                else:
                    self._status("Failed on %s, subtask %d" % (self.name, i))
                    filename_stdout = None
                    failedOutput = True

                if os.path.exists(self._workingdir_file_path(filename_stderr )):                    
                    self.filename_stderr = filename_stderr
                    self._status('shutil.copy(%s %s")' % (self._workingdir_file_path(filename_stderr), self.targetdirectory))
                    shutil.copy(self._workingdir_file_path(filename_stderr), self.targetdirectory)
                    stderrHasFailed = os.path.getsize(self._workingdir_file_path(filename_stderr)) > 0
                    if self.failOnStdErr and stderrHasFailed:
                        self._status("Failed on %s, subtask %d" % (self.name, i))
                        self.state = FAILED_TASK
                        failedOutput = True
                else:
                    self._status("Failed on %s, subtask %d" % (self.name, i))
                    filename_stderr = None
                    failedOutput = True
    
                self.outputstreams.append({"stdout" : filename_stdout, "stderr" : filename_stderr, "failed" : stderrhasfailed})

            return not failedOutput
        else:
            self.state = FAILED_TASK
            return False
    
    def _complete(self):
        """This is the place to implement any final postprocessing steps for your task which prerequisites require (Pay it backward).
           All necessary input files for prerequisites should be copied back to the originating host here. 
           e.g.  -check if all files were created
                 -execute final analysis
                 -optionally get rid of unused files
                 -copy final output files back to the originating host\n"""
        return True
    
    def complete(self):
        """This function should not be overridden. Completion code should be written in the _complete function."""
        self.profiler.PROFILE_START("Completion")
        self._status("Completing %s" % self.name)
        result = self._complete()
        self.state = COMPLETED_TASK
        self.profiler.PROFILE_STOP("Completion")
        return result
    
    def getprofile(self):
        return self.profiler.PROFILE_STATS()

    def _status(self, message, plain = False):
        if self.debug:
            if plain:
                print(message)
            else:
                print('<debug type="task">%s</debug>' % message)
        
    def cleanup(self):
        """this is the place to remove any remaining files left by your application"""
        self._status("Cleaning up %s" % self.name)
        
        if not self.cleanedup:
            self._status("cleanup: os.remove(%s)" % self.workingdir)
            self.cleanedup = True
    
    def addPrerequisite(self, task, inputfiles = []):
        self.prerequisites[task] = inputfiles
        task.addDependent(self)
    
    def addDependent(self, task):
        self.dependents.append(task)
    
    def getDependents(self):
        return self.dependents
    
    def getClusterStatus(self, qstatjobs = None):
        if self.state == ACTIVE_TASK:
            thisjob, alljobs = sge.qstat(self.jobid, jobs = qstatjobs)
            if thisjob:
                return "%s - %s" % (self.scriptfilename, thisjob)
        return None

    def getState(self, qstatjobs = None, allowToRetire = True):
        # ping server
        if self.state == ACTIVE_TASK:
            # Query the submission host
            thisjob, alljobs = sge.qstat(self.jobid, jobs = qstatjobs)
                        
            if not thisjob and allowToRetire:
                self.state = RETIRED_TASK
                self.profiler.PROFILE_STOP("Execution")
                self.profiler.PROFILE_START("Retirement")
                if not self.retire():
                    self._status("Failed while retiring task %s." % self.name)
                    self.state = FAILED_TASK
                self.profiler.PROFILE_STOP("Retirement")
                # look at stderr
                # determine scratch dir
                # copy files back to dir with jobid
        return self.state
