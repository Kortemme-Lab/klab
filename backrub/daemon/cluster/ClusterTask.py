#!/usr/bin/env python

# Set up array jobs for QB3 cluster.
import sys
import os
import time
import shutil
import tempfile
import re
import glob
from string import join
import SimpleProfiler

import sge

INITIAL_TASK = 0
INACTIVE_TASK = 1
ACTIVE_TASK = 2
RETIRED_TASK = 3
COMPLETED_TASK = 4
FAILED_TASK = 5

#todo: remove

RosettaBinaries = {        
    "classic"   :{  # 2.3.0 was released 2008-04-21, this revision dates 2008-12-27
                    "name"      : "Rosetta++ 2.32 (classic), as published",
                    "revision"  : 26316, 
                    "mini"      : False,
                    "backrub"   : "rosetta_20090109.gcc", 
                    "database"  : "rosetta_database"
                 },
    "mini"      :{  # Revision is clear here
                    "name" : "Rosetta 3.1 (mini)",
                    "revision" : 32532, 
                    "mini"      : True,
                    "backrub" : "backrub_r32532", 
                    "postprocessing" : "score_jd2_r32532", 
                    "database"  : "minirosetta_database"
                 },
    "ensemble"  :{  # based solely on the date, roughly between revisions 22709 - 22736
                    "name" : "Rosetta++ 2.30 (classic), as published",
                    "revision" : 22736, 
                    "mini"      : False,
                    "backrub" : "ros_052208.gcc",
                 },
    "seqtolHK"  :{  # based solely on the date, roughly between revisions 24967 - 24980
                    "name" : "Rosetta++ 2.30 (classic), as published",
                    "revision" : 24980, 
                    "mini"      : False,
                    "backrub" : "rosetta_classic_elisabeth_backrub.gcc", 
                    "sequence_tolerance" : "rosetta_1Oct08.gcc",
                    "minimize" : "rosetta_minimize_12_17_05.gcc",
                    "database" : "rosetta_database_elisabeth", #todo: Now defunct
                    "clusterrev" : "rElisabeth",
                    "cluster_databases" : ["rosetta_database_r15286", "rosetta_database_r17289"],
                 },
    "seqtolJMB" :{  # based solely on the date, roughly between revisions 24967 - 24980
                    "name" : "Rosetta 3.2 (mini), as published",
                    "revision" : 39284,
                    "mini"      : True,
                    "backrub" : "backrub_r39284",
                    "sequence_tolerance" : "sequence_tolerance_r39284",
                    "database"  : "minirosetta_database_r39284",
                    "clusterrev" : "r3.2.1"
                 },
    "seqtolP1"  :{  # based solely on the date, roughly between revisions 24967 - 24980
                    "name" : "Rosetta 3.2 (mini), as published",
                    "revision" : 0, 
                    "mini"      : True,
                    "backrub" : "backrub_r", 
                    "sequence_tolerance" : "sequence_tolerance_r",
                    "database"  : "minirosetta_database_r"
                 },
}


def write_file(filename, contents):
   file = open(filename, 'w')
   file.write(contents)
   file.close()
   return

rootdir = "/netapp/home/shaneoconner"

def getClusterDatabasePath(binary, cluster_database_index = 0):
    if cluster_database_index in range(len(RosettaBinaries[binary]["cluster_databases"])):
        return "%s/%s/%s" % (rootdir, RosettaBinaries[binary]["clusterrev"], RosettaBinaries[binary]["cluster_databases"][cluster_database_index])

class ClusterScript:
    
    def __init__(self, workingdir, binary, numtasks = 0, dataarrays = {}):
        self.contents = []
        self.tasks = []
        self.parameters = {"workingdir": workingdir, "taskline": "", "taskparam" : "", "taskvar" : ""}
        if numtasks > 0:
            if dataarrays:
                for arrayname, contents in sorted(dataarrays.iteritems()):
                    self.parameters["taskline"] += "%s=( dummy %s )\n" % (arrayname, join(contents, " "))
                    self.parameters["taskvar"]  += '%svar=${%s[$SGE_TASK_ID]}\n' % (arrayname, arrayname)     
                #self.parameters["taskline"] = "tasks=( dummy %s )" % join(tasks, " ")
                #self.parameters["taskvar"] = 'taskvar=${tasks[$SGE_TASK_ID]}"'
            self.parameters["taskparam"] = "#$ -t 1-%d" % numtasks #len(tasks)
        self.revision = RosettaBinaries[binary]["clusterrev"]
        self.bindir = "%s/%s" % (rootdir, self.revision)
        self.workingdir = workingdir
        self.script = None

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
#$ -l h_rt=11:59:00
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
     
    def __init__(self, workingdir, targetdirectory, scriptfilename, parameters = {}, name = ""):
        self.failOnStdErr = True
        self.debug = True
        self.targetdirectory = targetdirectory
        self.jobid = 0
        self.script = None
        self.state = INACTIVE_TASK
        self.dependents = []
        self.prerequisites = {}
        self.parameters = parameters
        self.workingdir = workingdir
        self.scriptfilename = scriptfilename
        self.filename = os.path.join(workingdir, scriptfilename)
        self.cleanedup = False
        self.filename_stdout = None
        self.filename_stderr = None
        self.name = name or "unnamed"
        self.numtasks = 1
        if parameters.get("pdb_filename"):
            parameters["pdbRootname"] = parameters["pdb_filename"][:-4]

    def _workingdir_file_path(self, filename):
        """Get the path for a file within the working directory"""
        return os.path.join(self.workingdir, filename)   

    def _targetdir_file_path(self, filename):
        """Get the path for a file within the working directory"""
        return os.path.join(self.targetdirectory, filename)   

    def getName(self):
        return self.name
        
    def start(self, profiler):
        # Our job submission engine is sequential at present so we use one filename
        # todo: use a safe equivalent of tempname
        if self.script:
            
            self._status("Starting %s" % self.name)
            # Copy files from prerequisites
            for prereq, files in self.prerequisites.iteritems():
                self._status("Copying prerequisites for %s" % self.name)
                prereq.copyFiles(self.workingdir, files)
                
            write_file(self.filename, self.script)
            #print(self.script)
            self._status("<qsub>", plain = True)
            self.jobid = sge.qsub_submit(self.filename, self.workingdir, name = self.scriptfilename, showstdout = self.debug)
            self._status("</qsub>", plain = True)
            self._status("Job started with id %d." % self.jobid)
            if self.jobid != 0:
                self.profiler = profiler
                profiler.PROFILE_START(self.getName())
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
           
    
    def _copyAllFilesBackToHost(self):
        #todo: This will copy the files from the cluster submission host back to the originating host
        for file in glob.glob(self._workingdir_file_path("*")):
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
            os.mkdir(self.targetdirectory)
            
        if self.scriptfilename:
            for i in range(1, self.numtasks + 1):
            
                if self.numtasks == 1:
                    filename_stdout = "%s.o%s" % (self.scriptfilename, self.jobid)
                    filename_stderr = "%s.e%s" % (self.scriptfilename, self.jobid)
                else:
                    filename_stdout = "%s.o%s.%d" % (self.scriptfilename, self.jobid, i)
                    filename_stderr = "%s.e%s.%d" % (self.scriptfilename, self.jobid, i)
                
                if os.path.exists(self._workingdir_file_path(filename_stdout)):
                    self.filename_stdout = filename_stdout
                    self._status('shutil.copy(%s/%s %s")' % (self.workingdir, filename_stdout, self.targetdirectory))
                    shutil.copy("%s/%s" % (self.workingdir, filename_stdout), self.targetdirectory)
                if os.path.exists(self._workingdir_file_path(filename_stderr )):                    
                    self.filename_stderr = filename_stderr
                    self._status('shutil.copy(%s/%s %s")' % (self.workingdir, filename_stderr, self.targetdirectory))
                    shutil.copy("%s/%s" % (self.workingdir, filename_stderr), self.targetdirectory)
                    if self.failOnStdErr and os.path.getsize(self._workingdir_file_path(filename_stderr)) > 0:
                        self._status("Failed on %s, subtask %d" % (self.name, i))
                        self.state = FAILED_TASK
                        return False

            return self.filename_stdout and self.filename_stderr
        else:
            self.state = FAILED_TASK
            return False
    
    def complete(self):
        """This is the place to implement any final postprocessing steps for your task which prerequisites require (Pay it backward).
           All necessary input files for prerequisites should be copied back to the originating host here. 
           e.g.  -check if all files were created
                 -execute final analysis
                 -optionally get rid of unused files
                 -copy final output files back to the originating host\n"""

        self._status("Completing %s" % self.name)
        self.state = COMPLETED_TASK
        return True
    
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
    
    def getState(self):
        # ping server
        if self.state == ACTIVE_TASK:
            # Query the submission host
            thisjob, alljobs = sge.qstat(self.jobid)
                        
            if not thisjob:
                self.state = RETIRED_TASK
                self.retire()
                # look at stderr
                # determine scratch dir
                # copy files back to dir with jobid
            else:
                self._status("%s - %s" % (self.scriptfilename, thisjob))
        return self.state   
