#!/usr/bin/env python

# Set up array jobs for QB3 cluster.
import sys
import os
import re
from string import join

#todo: so your job must copy back any data it needs on completion.

#scp tempdir/* shaneoconner@chef.compbio.ucsf.edu:/netapp/home/shaneoconner/temp/tempdir
#publickey = /netapp/home/shaneoconner/.ssh/id_rsa.pub

################## SUBROUTINES
def write_file(filename, contents):
   file = open(filename, 'w')
   file.write(contents)
   file.close()
   return

def qsub_submit(command_filename, hold_jobid = None, name = None):
    """Submit the given command filename to the queue.
    
    ARGUMENTS
        command_filename (string) - the name of the command file to submit
    
    OPTIONAL ARGUMENTS
        hold_jobid (int) - job id to hold on as a prerequisite for execution
    
    RETURNS
        jobid (integer) - the jobid
    """
    
    # Form command
    command = 'qsub'
    if name:
        command += ' -N %s' % name
    if hold_jobid:
        command += ' -hold_jid %d' % hold_jobid
    command += ' %s' % command_filename
    
    # Submit the job and capture output.
    import commands
    print "> " + command
    output = commands.getoutput(command)
    print output
    
    # Match job id
    # This part of the script is probably error-prone as it depends on the server message.
    matches = re.match('Your job-array (\d+).(\d+)-(\d+):(\d+)', output)
    if not matches:
        matches = re.match('Your job (\d+) \(".*"\) has been submitted.*', output)
    
    if matches:
        return int(matches.group(1))
    else:
        return -1

################ MAIN BODY

# Write equilibration script.

if not os.path.exists("output"):
    os.mkdir("output")

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
                    "database" : "rosetta_database_elisabeth"
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

# All cluster binaries should have the same name format based on the clusterrev field in RosettaBinaries: 
#    i) they are stored in the subdirectory of home named <clusterrev>
#   ii) they are named <somename>_<clusterrev>_static
# Furthermore, the related database should be in a subdirectory of the bindir named "rosetta_database"
# The "static" in the name is a reminder that these binaries must be built statically.

class ClusterScript:
    
    def __init__(self, binary, numtasks = 0, tasks = []):
        self.contents = []
        self.tasks = []
        self.parameters = {"taskline": "", "taskparam" : "", "taskvar" : ""}
        if numtasks > 0:
            if tasks:
                self.parameters["taskline"] = "tasks=( dummy %s )" % string.join(tasks, " ")
                self.parameters["taskvar"] = 'taskvar=${tasks[$SGE_TASK_ID]}"'
            self.parameters["taskparam"] = "#$ -t 1-%d" % numtasks #len(tasks)
            
        self.rootdir = "/netapp/home/shaneoconner"
        self.revision = RosettaBinaries[binary]["clusterrev"]
        self.bindir = "%s/%s" % (self.rootdir, self.revision)
        self.datadir = "%s/control" % self.rootdir
        self.script = None
            
    def _addPreamble(self):
        self.contents.insert(0, """\
#!/bin/bash
#
#$ -S /bin/bash
#$ -o output
#$ -e output
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
                
        if type:
            self.contents.append('echo -n "<%s %s"' % (type, attstring))
            self.contents.append('if [ -n "${SGE_TASK_ID+x}" ]; then')
            self.contents.append('echo -n "\\"subtask=$SGE_TASK_ID\\"" ')
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

    def setScript(self, lines, type = "", attributes = {}):
        self._addPreamble()
        self._addTask(lines, type, attributes)
        self._addEpilogue()
        self.script = join(self.contents, "\n")
        return self.script
    
    def submit(self):
        # Our job submission engine is sequential at present so we use one filename
        # todo: use a safe equivalent of tempname
        filename = 'backrub.cmd'
        write_file(filename, self.script)
        self.jobid = qsub_submit(filename, name = 'backrubtest')
        return self.jobid
        #print "Submitted. jobid = %d" % jobid
        # Write jobid to a file.
        #import subprocess
        #p = subprocess.call("echo %d >> jobids" % jobid, shell=True)

    def getBinary(self, binname):
        return "%s/%s_%s_static" % (self.bindir, binname, self.revision)
    
    def getDatabaseDir(self):
        return "%s/rosetta_database/" % self.bindir
    
    def getDataDir(self):
        return self.datadir


pdbRootname = "2I0L_A_C_V2006"

# Backrub

backrubParameters = {
    "resfile"    : "", #"-resfile /netapp/home/shaneoconner/backrub_1789.resfile"
    "nstruct"           : 2,
    "pdbRootname"       : pdbRootname,
    "ntrials"           : 10,
}

ct = ClusterScript("seqtolJMB")

args = [ct.getBinary("backrub"),  
        "-database %s/rosetta_database/" % ct.getDatabaseDir(), 
        "-s %s/%s.pdb" % (ct.getDataDir(), backrubParameters["pdbRootname"]),
        "-ignore_unrecognized_res", 
        "-nstruct %d" % backrubParameters["nstruct"],
        "-backrub:ntrials %d" % backrubParameters["ntrials"], 
        "-pivot_atoms CA"]
if backrubParameters["resfile"]:
    args.append("-resfile %s/%s" % (ct.getDataDir, backrubParameters["resfile"]))
commandline = join(args, " ")

print(ct.setScript([commandline], type="Backrub"))

# seqtol

weights = [0.4, 0.4, 0.4, 1.0]
weights = [0.4, 0.4]
seqtolParameters = {
    "pdbRootname"       : pdbRootname,
    "popsize"           : 20,
    "weights"           : join(map(str, weights), " "),
    "resfile"           : "seqtol_1863.resfile",
}

ct = ClusterScript("seqtolJMB", numtasks = 2)

commandlines = [
        '"# Run sequence tolerance',
        'structureID=$(printf "%%04d" $SGE_TASK_ID)',
        '',
        'xmltag=$(printf "<seqtol runnumber=%%s>" $structureID)',
        'pdbFile=$(printf "%s/%s_%%s_low.pdb" $structureID)' % (ct.getDataDir(), seqtolParameters["pdbRootname"]),
        'prefixFile=$(printf "%s_%%s_low" $structureID)' % seqtolParameters["pdbRootname"], 
        'outPrefix=$(printf "%s_%%s_low" $structureID)' % seqtolParameters["pdbRootname"]]

commandlines.append(join(
        [ct.getBinary("sequence_tolerance"),  
        "-database %s/rosetta_database/" % ct.getDatabaseDir(), 
        "-s $pdbFile",
        "-packing:resfile %s/%s" % (ct.getDataDir(), seqtolParameters["resfile"]),
        "-ex1 -ex2 -extrachi_cutoff 0",
        "-score:ref_offsets TRP 0.9",
        "-ms:generations 5",
        "-ms:pop_size %d" % seqtolParameters["popsize"],
        "-ms:pop_from_ss 1",
        "-ms:checkpoint:prefix $prefixFile",
        "-ms:checkpoint:interval 200",
        "-ms:checkpoint:gz",
        "-out:prefix $outPrefix",
        "-seq_tol:fitness_master_weights %s" % seqtolParameters["weights"] ]))

print(ct.setScript(commandlines, type="SequenceTolerance"))


sys.exit(1)

class ClusterTask(self):
     
     def __init__(self):
         self.subtasks = []
         self.dependents = []
         self.parent = None
     
     def setParent(self, task):
         self.parent = task
         
     def addSubTask(self, task):
         subtasks.append(task)
              
     def addDependent(self, task):
         dependents.append(task)
         dependent.setParent(self)

     def preprocess(self):
         pass
     
     def submit(self):
         # create my ClusterScript
         self.clusterJobid
         self.workingDirectory
         pass
     
     def postprocess(self):
         pass 

     def setupForDependents(self):
         self.workingdir = 
         pass
     
     def isDone(self):
         
         done = True
         for subtask in self.subtasks:
             if not subtask.isDone():
                 done = False
                 break
             else:
                 subtask.postprocess()
                 subtasks.remove(subtask)
         # Check if this task is done
         return done
     
     def controller(self):
         if not self.state:
             self.preprocess()
             self.state = "subtasks"
         
         if self.state == "subtasks":
             if self.subtasks:
                 for subtask in self.subtasks:
                     subtask.controller()
                     if subtask.isDone():
                         subtasks.remove(subtask)
                     else:
                         return False
             self.state = "main"
             
         if self.state = "main":
             self.submit()
             self.state = "running"
             
         if self.state = "running":
             if self.isDone():
                 self.state = "setupForDependents"
             else:
                 return False
         
         if self.state = "setupForDependents":
             setupForDependents()
             self.state = "dependents"
         
         if self.state = "dependents":
             if self.dependents:
                 for dependent in self.dependents:
                     dependent.controller()
                     if dependent.isDone():
                         dependents.remove(dependent)
                     else:
                         return False
             self.state = "postprocess"

         if self.state = "postprocess":
             self.postprocess()
             return True
                      
                      
if False:
    seqtolBody = """\
# Run sequence tolerance
structureID=$(printf "%%04d" $SGE_TASK_ID)

xmltag=$(printf "<seqtol runnumber=%%s>" $structureID)
pdbFile=$(printf "%(datadir)s/%(pdbRootname)s_%%s_low.pdb" $structureID)
prefixFile=$(printf "%(pdbRootname)s_%%s_low" $structureID)
outPrefix=$(printf "%(pdbRootname)s_%%s_low" $structureID)

echo xmltag
%(bindir)s/sequence_tolerance_r%(revision)s_static -database %(bindir)s/minirosetta_database/ -s $pdbFile -packing:resfile %(datadir)s/%(resfile)s -ex1 -ex2 -extrachi_cutoff 0 -score:ref_offsets TRP 0.9 -ms:generations 5 -ms:pop_size %(popsize)d -ms:pop_from_ss 1 -ms:checkpoint:prefix $prefixFile -ms:checkpoint:interval 200 -ms:checkpoint:gz -out:prefix $outPrefix -seq_tol:fitness_master_weights %(weights)s
echo "</seqtol>""" % seqtolParameters

remainder = '''
# Write production extension script.
contents = """\
#!/bin/tcsh
#
#$ -l opt64=true
#$ -S /bin/tcsh
#$ -cwd
#$ -r y
#$ -j y
#$ -l panqb3=1G,scratch=1G,mem_total=3G
#$ -l h_rt=11:59:00
#$ -q medium.q
#$ -t 1-%(ndirectories)d

set echo on

date
hostname
pwd

uname -i

# Run equilibration
set workdir = `head -n $SGE_TASK_ID %(directory_filename)s | tail -n 1`
cd $workdir
tcsh ./equilibrate.sh

date
""" % vars()

# Submit extension jobs.
for extend_iteration in range(extend_iterations):
  hold_jobid = jobid
  filename = 'hyd%d-prod%d.cmd' % (replicate, extend_iteration)
  write_file(filename, contents)
  jobid = qsub_submit(filename, hold_jobid = hold_jobid, name = 'hyd%d-prod%d' % (replicate, extend_iteration))
  print "Submitted extension job waiting on jobid %d. jobid = %d" % (hold_jobid, jobid)
  
  # Write jobid to a file.
  import commands
  commands.getoutput('echo %d >> hyd%d.jobids' % (replicate, jobid))

print "Done."'''

