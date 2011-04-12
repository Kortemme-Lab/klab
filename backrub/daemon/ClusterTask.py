#!/usr/bin/env python

# Set up array jobs for QB3 cluster.
import sys
import os
sys.path.insert(0, "../common/")
import time
import shutil
import tempfile
import re
from string import join

import pdb
from analyze_mini import AnalyzeMini
from rosettaseqtol import make_seqtol_resfile


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
        self.rootdir = "/netapp/home/shaneoconner"
        self.revision = RosettaBinaries[binary]["clusterrev"]
        self.bindir = "%s/%s" % (self.rootdir, self.revision)
        self.workingdir = workingdir
        self.script = None
            
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

if False:
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
            "-database %s" % ct.getDatabaseDir(), 
            "-s $pdbFile",
            "-packing:resfile %s/%s" % (ct.getDataDir(), seqtolParameters["resfile"]),
            "-ex1 -ex2 -extrachi_cutoff 0",
            "-score:ref_offsets TRP 0.9",
            "-ms:generations 5",
            "-ms:pop_size %d" % parameters["pop_size"],
            "-ms:pop_from_ss 1",
            "-ms:checkpoint:prefix $prefixFile",
            "-ms:checkpoint:interval 200",
            "-ms:checkpoint:gz",
            "-out:prefix $outPrefix",
            "-seq_tol:fitness_master_weights %s" % seqtolParameters["weights"] ]))
    
    print(ct.createScript(commandlines, type="SequenceTolerance"))


INITIAL_TASK = 0
INACTIVE_TASK = 1
ACTIVE_TASK = 2
RETIRED_TASK = 3
COMPLETED_TASK = 4
FAILED_TASK = 5

dsger='''
    We allow directed acylic graphs, not necessarily strongly connected.

    This needs to be fixed.
    Logic is wrong at present as there are multiple paths to a node
    Instead, try labelling the nodes with distance from the initial nodes where 
    distance is the maximum number of connections to an initial node.
    Break if the distance exceeds the number of nodes as this implies a cycle.
    After labelling, if there is a path from a node of distance d to a node of distance c, c < d, then error
    Better still, just use Tarjan's algorithm.
    http://en.wikipedia.org/wiki/Tarjan%E2%80%99s_strongly_connected_components_algorithm
    
    CyclicDependencyException
    IncompleteGraphException
    
    def traverseDependents(self, availabletasks, task):
        del availabletasks[task]
        for d in task.getDependents():
            if not allowedtasks[d]:
                # We have either encountered a task previously removed or else one which
                # was never in the list to begin with. 
                # todo: Distinguish these cases
                raise CyclicDependencyException 
            traverseDependents(d)

    def checkGraphReachability(tasks, initialtasks):
        check initial in tasks
        
        for task in initialtasks:
            if not tasks[task]:
                raise IncompleteGraphException
            traverseDependents(tasks, task)
'''
def checkGraphReachability(initialtasks):
    pass

# Scheduler exceptions
class TaskSchedulerException(Exception):
    def __init__(self, pending, retired, completed, msg = ""):
        self.message = msg
        self.pending = pending
        self.retired = retired
        self.completed = completed
    def __str__(self):
        s = ""
        # todo: List the remaining tasks and the completed ones
        print('<SchedulerException message="%s">' % self.message)
        for p in self.pending:
            print("<pending>%s</pending>" % p.getName())
        print("</SchedulerException>")
        # etc.
        return s

class SchedulerTaskAddedAfterStartException(TaskSchedulerException): pass
class BadSchedulerException(TaskSchedulerException): pass
class TaskCompletionException(TaskSchedulerException): pass
class SchedulerDeadlockException(TaskSchedulerException): pass
class SchedulerStartException(TaskSchedulerException): pass

class TaskScheduler(object):

    def __init__(self, workingdir, files = []):
        self.tasks = {INITIAL_TASK: [],
                      ACTIVE_TASK: [],
                      RETIRED_TASK: [],
                      COMPLETED_TASK: []}
        
        self.pendingtasks = {}
        self.initialFiles = files
        self.workingdir = workingdir
        self.failed = False
        self.started = False
    
    def _movequeue(self, task, oldqueue, newqueue):
        print("[Moving %s from %d to %d]" % (task.getName(), oldqueue, newqueue))
        self.tasks[oldqueue].remove(task)
        self.tasks[newqueue].append(task)
    
    def _getAllTasks(self):
        tasks = []
        tasks.extend(self.tasks[INITIAL_TASK])
        tasks.extend(self.tasks[ACTIVE_TASK])
        tasks.extend(self.tasks[RETIRED_TASK])
        tasks.extend(self.tasks[COMPLETED_TASK])
        return tasks

    # API
    
    def addInitialTask(self, task):
        if self.started:
            raise SchedulerTaskAddedAfterStartException(pendingtasks, self.tasks[RETIRED_TASK], self.tasks[COMPLETED_TASK], msg = "Exception adding initial task: %s" % task.getName())
        self.tasks[INITIAL_TASK].append(task)
               
    def start(self):
        # todo: Check the reachability and acylicity of the graph here
        checkGraphReachability(self.tasks[INITIAL_TASK])
            
        for task in self.tasks[INITIAL_TASK]:
            #todo: pass in files?
            started = task.start()
            print("Started %s %d " % (task.getName(), task.getState()))
            if started:
                self._movequeue(task, INITIAL_TASK, task.getState())
            else:
                raise SchedulerStartException(pendingtasks, self.tasks[RETIRED_TASK], self.tasks[COMPLETED_TASK], msg = "Exception starting: %s" % task.getName())
                self.failed = True
                return False
        
        return True
        
    def isAlive(self):
        return self.failed == False
    
    def step(self):
        '''This determines whether the system state changes by checking the 
           state of the individual tasks.
           We return True iff all tasks are completed.'''
        
        # I told you I was sick. Don't step a broken scheduler.
        if self.failed:
             raise BadSchedulerException(pendingtasks, self.tasks[RETIRED_TASK], self.tasks[COMPLETED_TASK], msg = "Exception stepping the scheduler.") 
            
        # Retire tasks
        activeTasks = self.tasks[ACTIVE_TASK][:]
        for task in activeTasks:
            print("%s %d " % (task.getName(), task.getState()))
            if task.getState() == RETIRED_TASK:
                self._movequeue(task, ACTIVE_TASK, RETIRED_TASK)
                if task.getState() == FAILED_TASK:
                    self.failed = True
                    return False
        
        # Complete tasks
        retiredTasks = self.tasks[RETIRED_TASK][:]
        for task in retiredTasks:
            dependents = task.getDependents()
            completed = True
            for dependent in dependents:
                if dependent.getState() != COMPLETED_TASK:
                    completed = False
                    break
            if completed:
                completed = task.complete()
                if completed:
                    self._movequeue(task, RETIRED_TASK, COMPLETED_TASK)
                else:
                    raise TaskCompletionException(pendingtasks, self.tasks[RETIRED_TASK], self.tasks[COMPLETED_TASK])
            
            # Try to start any dependents if we can
            # A dependent *should* fire once all its prerequisite tasks have finished
            dependents = task.getDependents()
            for dependent in dependents:
                if dependent.getState() == INACTIVE_TASK:
                    self.pendingtasks[dependent] = True
                    print("Starting %s." % dependent.getName())
                    started = dependent.start()
                    if started:
                        del self.pendingtasks[dependent]
                        self.tasks[ACTIVE_TASK].append(dependent)


        
        # Bad scheduler. No biscuit.
        if self.tasks[INITIAL_TASK]:
            raise BadSchedulerException 
        
        # If we have no more tasks which will trigger other tasks to start i.e. active tasks
        # and we have pending tasks which have not been started, they never will be started.
        # John Hodgman - "Halting problem - solved. You're welcome."
        if self.pendingtasks and not (self.tasks[ACTIVE_TASK]):
             raise SchedulerDeadlockException(pendingtasks, self.tasks[RETIRED_TASK], self.tasks[COMPLETED_TASK])
        
        # We are finished when there are no active or retired tasks
        print("STEP")
        print(self.tasks[ACTIVE_TASK])
        print(self.tasks[RETIRED_TASK])
        return not(self.tasks[ACTIVE_TASK] or self.tasks[RETIRED_TASK]) 
    
    def cleanup(self):
        tasks = self._getAllTasks()
        for task in tasks:
            task.cleanup()

class ClusterTask(object):
     
    def __init__(self, workingdir, scriptfilename, parameters = {}, name = ""):
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
        if parameters.get("pdb_filename"):
            parameters["pdbRootname"] = parameters["pdb_filename"][:-4]

    def getName(self):
        return self.name
        
    def start(self):
        # Our job submission engine is sequential at present so we use one filename
        # todo: use a safe equivalent of tempname
        if self.script:
            
            # Copy files from prerequisites
            for prereq, files in self.prerequisites.iteritems():
                prereq.copyFiles(self.workingdir, files)
                
            write_file(self.filename, self.script)
            #print(self.script)
            self.jobid = 1
            #self.jobid = qsub_submit(filename, name = 'backrubtest')
            if self.jobid != 0:
                self.state = ACTIVE_TASK
                return self.jobid
        else:
            return 0
        #print "Submitted. jobid = %d" % jobid
        # Write jobid to a file.
        #import subprocess
        #p = subprocess.call("echo %d >> jobids" % jobid, shell=True)
    
    def copyFiles(self, targetDirectory, filemasks = ["*"]):
        for mask in filemasks:
            print('os.system("cp %s/%s %s")' % (self.workingdir, mask, targetDirectory))
        
    def retire(self):
        return True
    
    def complete(self):
        self.state = COMPLETED_TASK
        return True

    def cleanup(self):
        if not self.cleanedup:
            pass
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
            if True or qstatblah: # todo
                "Retiring %s." % self.getName()
                self.state = RETIRED_TASK
                self.retire()
                # look at stderr
                # determine scratch dir
                # copy files back to dir with jobid
        return self.state     

def getOutputFilename(pdbname, index, suffix):
    return '%s_%04.i_%s.pdb'  % (pdbname, index, suffix)          
    
class BackrubClusterTask(ClusterTask):

    # additional attributes
    default       = ""   # resfile default for amino acids
    residues      = {}   # contains the residues and their modes according to rosetta: { (chain, resID):["PIKAA","PHKL"] }
    backrub       = []   # residues to which backrub should be applied: [ (chain,resid), ... ]
    pivot_res     = []   # list of pivot residues, consecutively numbered from 1 [1,...]
    map_res_id    = {}   # contains the mapping from (chain,resid) to pivot_res
    
    def workingdir_file_path(self, filename):
        """Get the path for a file within the working directory"""
        return os.path.join(self.workingdir, filename)

    def __init__(self, workingdir, parameters, resfile=None, name=""):
        super(BackrubClusterTask, self).__init__(workingdir, 'backrub.cmd', parameters, name)          
        self.resfile = resfile
        self.prepare_backrub()
        
        self.parameters["ntrials"] = 10000 # todo: should be 10000 on the live webserver
        if True: #read_config_file()["server_name"] == 'albana.ucsf.edu':
            self.parameters["ntrials"] = 10   
    
        # Setup backrub
        ct = ClusterScript(self.workingdir, parameters["binary"])
        args = [ct.getBinary("backrub"),  
                "-database %s" % ct.getDatabaseDir(), 
                "-s %s/%s" % (ct.getWorkingDir(), parameters["pdb_filename"]),
                "-ignore_unrecognized_res", 
                "-nstruct %d" % parameters["nstruct"],
                "-backrub:ntrials %d" % parameters["ntrials"], 
                "-pivot_atoms CA"]
        if self.resfile:
            args.append("-resfile %s/%s" % (ct.getWorkingDir(), resfile))
        if len(self.pivot_res) > 0:
            args.append("-pivot_residues")
            self.pivot_res.sort()
            args.extend([str(resid) for resid in self.pivot_res])

        commandline = join(args, " ")
        self.script = ct.createScript([commandline], type="Backrub")

    
    def write_resfile( self ):
        """function for resfile creation"""
        
        default_mode = 'NATAA'
        # store filename
        self.resfile = self.workingdir_file_path("backrub_%s.resfile" % self.parameters["ID"])
        output_handle = open(self.resfile,'w')
        output_handle.write('%s\nstart\n' % default_mode)
        output_handle.write( "\n" )
        
        #todo: Ask Florian - residues never seem to be used in old rosettabackrub.py?
        
        # translate resid to absolute mini rosetta res ids
        for residue in self.backrub:
            self.pivot_res.append( self.map_res_id[ '%s%4.i' % residue  ] )
        
        output_handle.close()
        
        # final check if file was created
        return os.path.exists( self.resfile )

    def prepare_backrub( self ):
        """prepare data for a full backbone backrub run"""
        
        self.pdb = pdb.PDB(self.parameters["pdb_info"].split('\n'))
        self.map_res_id = self.parameters["map_res_id"] 
        residue_ids = self.pdb.aa_resids()
        
        # backrub is applied to all residues: append all residues to the backrub list
        for res in residue_ids:
            x = [ res[0], res[1:].strip() ] # 0: chain ID, 1..: resid
            if len(x) == 1:
                self.backrub.append( ( "_", int(x[0].lstrip())) )
            else:
                self.backrub.append( ( x[0], int(x[1].lstrip())) )
        
        if not self.resfile:
            self.write_resfile()
    
    def retire(self):
        sr = super(BackrubClusterTask, self).retire()
        if not sr:
            return False
        return True #todo
        error = ''
        # check whether files were created (and write the total scores to a file)
        for x in range(1, self.parameter['ensemble_size']+1):
            low_file   = self.workingdir_file_path(getOutputFilename(self.parameters["pdbRootname"], x, "low"))          
            last_file  = self.workingdir_file_path(getOutputFilename(self.parameters["pdbRootname"], x, "last"))          

            if not os.path.exists( low_file ): 
                error += ' %s missing, ' % low_file # return False            
            if not os.path.exists( last_file ):
                error += ' %s missing, ' % ( last_file ) # return False
                  
        Analysis = AnalyzeMini(filename=self.workingdir_file_path( self.filename_stdout ))
        Analysis.analyze(outfile=self.workingdir_file_path('backrub_scores.dat'))
            
        if result_dir != None:
            self.copy_working_dir(result_dir)
        
        if error != '':
            print error
            return False
        
        return True
        
        
    def complete(self):
        """this is the place to implement the postprocessing protocol for your application
            e.g.: -check if all files were created
                  -execute analysis
                  -get rid of files the user doesn't need to see
                  -copy he directory over to the webserver\n"""
        sc = super(BackrubClusterTask, self).complete()
        if not sc:
            return False
        return True
            
class SequenceToleranceClusterTask(ClusterTask):
   
    def workingdir_file_path(self, filename):
        """Get the path for a file within the working directory"""
        return os.path.join(self.workingdir, filename)

    def __init__(self, workingdir, parameters, resfile, name=""):
        super(SequenceToleranceClusterTask, self).__init__(workingdir, 'seqtol.cmd', parameters, name)          
        self.resfile = resfile
        self.parameters = parameters
        
        low_files = []
        prefixes = []
        for i in range(1, parameters["nstruct"] + 1):
            lfilename = getOutputFilename(parameters["pdbRootname"], i, "low")
            lowfilepath = self.workingdir_file_path(lfilename)
            low_files.append(lowfilepath)          
            prefixes.append(lfilename[:-4])          
        self.lowfiles = low_files  
        
        parameters["pop_size"] = 2000 # todo: should be 2000 on the live webserver
        if True: #read_config_file()["server_name"] == 'albana.ucsf.edu':
            self.parameters["pop_size"] = 20
        
        # Setup backrub
        ct = ClusterScript(self.workingdir, parameters["binary"], numtasks = 2, dataarrays = {"lowfiles" : low_files, "prefixes" : prefixes})
        commandlines = ['"# Run sequence tolerance', '',
            join(
                [ct.getBinary("sequence_tolerance"),  
                "-database %s" % ct.getDatabaseDir(), 
                "-s $lowfilesvar",
                "-packing:resfile %s/%s" % (self.workingdir, resfile),
                "-ex1 -ex2 -extrachi_cutoff 0",
                "-score:ref_offsets TRP 0.9",  # todo: Ask Colin
                "-ms:generations 5",
                "-ms:pop_size %d" % parameters["pop_size"],
                "-ms:pop_from_ss 1",
                "-ms:checkpoint:prefix $prefixesvar",
                "-ms:checkpoint:interval 200",
                "-ms:checkpoint:gz",
                "-out:prefix $prefixesvar",
                "-seq_tol:fitness_master_weights %s" % join(map(str,parameters["weights"]), " ") ])]
        self.script = ct.createScript(commandlines, type="SequenceTolerance")

    def retire(self):
        sr = super(SequenceToleranceClusterTask, self).retire()
        if not sr:
            return False
        
        
        print("Postprocessing")
        return True #todo
        # run Colin's analysis script: filtering and profiles/motifs
        thresh_or_temp = self.parameter['kT']
        
        weights = self.parameter['weights']
        fitness_coef = 'c(%s' % weights[0]
        for i in range(1, len(weights)):
            fitness_coef += ', %s' % weights[i]
        fitness_coef += ')'
        
        type_st = '\\"boltzmann\\"'
        prefix  = '\\"tolerance\\"'
        percentile = '.5'
        
        self.workingdir = os.path.abspath('./') #todo: delete
        cmd = '''/bin/echo "process_seqtol(\'%s\', %s, %s, %s, %s, %s);\" \\
                  | /bin/cat %sdaemon/specificity.R - \\
                  | /usr/bin/R --vanilla''' % ( self.workingdir, fitness_coef, thresh_or_temp, type_st, percentile, prefix, server_root)
        
                 
        # open files for stderr and stdout 
        self.file_stdout = open(self.workingdir_file_path( self.filename_stdout ), 'a+')
        self.file_stderr = open(self.workingdir_file_path( self.filename_stderr ), 'a+')
        self.file_stdout.write("*********************** R output ***********************\n")
        print(cmd)
        subp = subprocess.Popen(cmd, 
                                stdout=self.file_stdout,
                                stderr=self.file_stderr,
                                cwd=self.workingdir,
                                shell=True,
                                executable='/bin/bash' )
                
        while True:
            returncode = subp.poll()
            if returncode != None:
                if returncode != 0:
                    sys.stderr.write("An error occurred during the postprocessing script. The errorcode is %d." % returncode)
                    raise PostProcessingException
                break;
            time.sleep(2)
        
        subp.returncode
        
        self.file_stdout.close()
        self.file_stderr.close()
        count = 0
        if not os.path.exists( self.workingdir_file_path("tolerance_sequences.fasta") ) and count < 10 :
            time.sleep(1) # make sure the fasta file gets written
            count += 1
        
        #todo: should fail gracefully here if the fasta file still isn't written
          
        # create weblogo from the created fasta file
        seqs = read_seq_data(open(self.workingdir_file_path("tolerance_sequences.fasta")))
        logo_data = LogoData.from_seqs(seqs)
        logo_data.alphabet = std_alphabets['protein'] # this seems to affect the coloring, but not the actual motif
        logo_options = LogoOptions()
        logo_options.title = "Sequence profile"
        logo_options.number_interval = 1
        logo_options.color_scheme = std_color_schemes["chemistry"]
        
        ann = getResIDs(self.parameter)
        logo_options.annotate = ann
        
        logo_format = LogoFormat(logo_data, logo_options)
        png_print_formatter(logo_data, logo_format, open(self.workingdir_file_path( "tolerance_motif.png" ), 'w'))
        
        # let's just quickly delete the *last.pdb and generation files:
        list_files = os.listdir(self.workingdir)
        list_files.sort()
        for pdb_fn in rosettahelper.grep('%s_[0-9]_[0-9]{4}_last\.pdb' % (self.parameter['pdb_id']), list_files):
            os.remove( self.workingdir_file_path(pdb_fn) )
        for pdb_fn in rosettahelper.grep('%s_[0-9]_[0-9]{4}_low\.ga\.generations\.gz' % (self.parameter['pdb_id']), list_files):
            os.remove( self.workingdir_file_path(pdb_fn) )
        
        return True
        
        
    def complete(self):
        """this is the place to implement the postprocessing protocol for your application
            e.g.: -check if all files were created
                  -execute analysis
                  -get rid of files the user doesn't need to see
                  -copy he directory over to the webserver\n"""
        sc = super(SequenceToleranceClusterTask, self).complete()
        if not sc:
            return False
        return True
            
class RosettaSequenceToleranceSK(object):

    map_res_id = {}
    name_pdb = ""

    def __init__(self, parameters, tempdir):
        
        self.parameters = parameters
        self.tempdir = tempdir
        print "Creating RosettaSeqTol object."
    
        # Create input files        
        self.make_workingdir() #todo: This will need to be done on chef itself from the server
        self.import_pdb(parameters["pdb_filename"], parameters["pdb_info"])
        self.write_backrub_resfile()
        self.write_seqtol_resfile()

        scheduler = TaskScheduler(self.workingdir, files = [self.name_pdb, self.seqtol_resfile, self.backrub_resfile])
        
        taskdir = self.make_taskdir("backrub", [self.name_pdb, self.backrub_resfile])
        brTask = BackrubClusterTask(taskdir, parameters, self.backrub_resfile, name="Backrub step for sequence tolerance protocol")
            
        taskdir = self.make_taskdir("sequence_tolerance", [self.name_pdb, self.seqtol_resfile])
        stTask = SequenceToleranceClusterTask(taskdir, parameters, self.seqtol_resfile, name="Sequence tolerance step for sequence tolerance protocol")
        if not stTask:
            raise Exception
        stTask.addPrerequisite(brTask, ["*_low.pdb"])
        
        scheduler.addInitialTask(brTask)
        self.scheduler = scheduler

        #obj.run()
        #obj.postprocessing()
        
    def make_workingdir(self):
        """Make a single used working directory inside the temporary directory"""
        #todo: let this make a tempdir
        self.workingdir = "%s/test" % self.tempdir
        return self.workingdir
        
        self.workingdir = tempfile.mkdtemp("seqtol_", dir = self.tempdir)
        if not os.path.isdir(self.workingdir):
            raise os.error
        return self.workingdir
    
    def make_taskdir(self, dirname, files = []):
        """ Make a subdirectory dirname in the working directory and copy all files into it.
            Filenames should be relative to the working directory."""
        taskdir = "%s/%s" % (self.workingdir, dirname)
        if not os.path.isdir(taskdir):
            os.mkdir(taskdir)
        if not os.path.isdir(taskdir):
            raise os.error
        for file in files:
            shutil.copyfile("%s/%s" % (self.workingdir, file), "%s/%s" % (taskdir, file))
        return taskdir

    def workingdir_file_path(self, filename):
        """Get the path for a file within the working directory"""
        return os.path.join(self.workingdir, filename)

    def import_pdb(self, filename, contents):
        """Import a pdb file from the database and write it to the temporary directory"""
        
        self.pdb = pdb.PDB(contents.split('\n'))
      
        # remove everything but the chosen chains or keep all chains if the list is empty
        # pdb_content is passed directly to backrub so remove the pruned chain lines before the backrub
        self.pdb.pruneChains(self.parameters['Partners'])
        self.pdb.remove_hetatm()  # rosetta doesn't like heteroatoms so let's remove them
        self.parameters['pdb_content'] = join(self.pdb.lines, '\n')        
        
        # internal mini resids don't correspond to the pdb file resids
        # the pivot residues need to be numbered consecuively from 1 up
        self.map_res_id = self.pdb.get_residue_mapping()
        self.parameters["map_res_id"] = self.map_res_id 
        self.pdb.write(self.workingdir_file_path(filename))
        self.name_pdb = filename
        return self.name_pdb
            
    def write_backrub_resfile( self ):
        """create a resfile of premutations for the backrub"""
               
        # Write out the premutated residues
        s = ""
        params = self.parameters
        for partner in params['Partners']:
            if params['Premutated'].get(partner):
                pm = params['Premutated'][partner]
                for residue in pm:
                    #todo: check that residue exists -  # get all residues:  residue_ids     = self.pdb.aa_resids()
                    s += ("%d %s PIKAA %s\n" % (residue, partner, pm[residue]))
        
        # Only create a file if there are any premutations
        if s != "":
            self.backrub_resfile = "backrub_%s.resfile" % self.parameters["ID"]
            output_handle = open( self.workingdir_file_path(self.backrub_resfile), 'w')
            output_handle.write('NATAA\nstart\n')
            output_handle.write(s)  
            output_handle.write( "\n" )
            output_handle.close()
        
    def write_seqtol_resfile( self ):
        """create a resfile for the chains
            residues in interface: NATAA (conformation can be changed)
            residues mutation: PIKAA ADEFGHIKLMNPQRSTVWY (design sequence)"""
        
        resfileHasContents, contents = make_seqtol_resfile( self.pdb, self.parameters, self.parameters['radius'], self.pdb.aa_resids())
        
        if resfileHasContents:
            self.seqtol_resfile = "seqtol_%s.resfile" % self.parameters["ID"]
            output_handle = open( self.workingdir_file_path(self.seqtol_resfile), 'w')
            output_handle.write(contents)
            output_handle.write( "\n" )
            output_handle.close()
        else:
            sys.stderr.write("An error occurred during the sequence tolerance execution. The chosen designed residues resulting in an empty resfile and so could not be used.")
            raise SequenceToleranceException          
        
    def start(self):
        try:
            self.scheduler.start()
        except TaskSchedulerException, e:
            print(e)
            
    
    def isCompleted(self):
        if self.scheduler.step():
            return True
        else:
            return False


if __name__ == "__main__":
    mini = "seqtolJMB"
    ID = 1234
    pdb_filename = "2I0L_A_C_V2006.pdb"    
    output_handle = open(pdb_filename,'r')
    pdb_info = output_handle.read()
    output_handle.close()
    nstruct = 2
    
    params = {
        "binary"            : mini,
        "ID"                : ID,
        "pdb_filename"      : pdb_filename,
        "pdb_info"          : pdb_info,
        "nstruct"           : nstruct,
        "radius"            : 10,
        "kT"                : 0.228,
        "numchains"         : 1,
        "Partners"          : ["A"],
        "weights"           : [0.4, 0.4],
        "Premutated"        : {"A" : {319 : "A"}},
        "Designed"          : {"A" : [318]}
        }
    seqtol = RosettaSequenceToleranceSK(params, "/netapp/home/shaneoconner/temp")
    seqtol.start()
    
    while not(seqtol.isCompleted()):
        time.sleep(1)
    
                      
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

