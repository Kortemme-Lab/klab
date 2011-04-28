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
import distutils.dir_util

import sge
import ClusterTask  
import SimpleProfiler

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
        self.debug = True
        self.tasks = {ClusterTask.INITIAL_TASK: [],
                      ClusterTask.ACTIVE_TASK: [],
                      ClusterTask.RETIRED_TASK: [],
                      ClusterTask.COMPLETED_TASK: []}
        
        self.pendingtasks = {}
        self.initialFiles = files # todo: Unused at present
        self.workingdir = workingdir
        self.failed = False
        self.started = False
        self.tasks_in_order = []
        self.statechanged = False
    
    #todo: Use multiple inheritance for this and task    
    def _status(self, message, plain = False):
        if self.debug:
            if plain:
                print(message)
            else:
                print('<debug type="task">%s</debug>' % message)
            
    def _movequeue(self, task, oldqueue, newqueue):
        self._status("[Moving %s from %d to %d]" % (task.getName(), oldqueue, newqueue))
        self.tasks[oldqueue].remove(task)
        self.tasks[newqueue].append(task)
        self.statechanged = True
        
    def _getAllTasks(self):
        tasks = []
        tasks.extend(self.tasks[ClusterTask.INITIAL_TASK])
        tasks.extend(self.tasks[ClusterTask.ACTIVE_TASK])
        tasks.extend(self.tasks[ClusterTask.RETIRED_TASK])
        tasks.extend(self.tasks[ClusterTask.COMPLETED_TASK])
        return tasks        
        
    def getprofile(self):
        profile = []
        count = 1
        ts = self._getAllTasks()
        
        for task in self.tasks_in_order:
            status = ClusterTask.status.get(task.getState(allowToRetire = False))
            profile.append(('task id="%d" name="%s" status="%s"' % (count, task.getName(), status), task.getprofile()))
            ts.remove(task)
            count += 1
        
        if ts:
            profile.append(("Logical error in getprofile! (%s)" % str(ts), 0))
            
        for task in ts:
            profile.append(("%s@%d" % (task.getName(), count), task.getprofile()))
            count += 1
        
        return profile
        
    # API
    
    def addInitialTasks(self, *tasks):
        if self.started:
            raise SchedulerTaskAddedAfterStartException(self.pendingtasks, self.tasks[ClusterTask.RETIRED_TASK], self.tasks[ClusterTask.COMPLETED_TASK], msg = "Exception adding initial task: %s" % task.getName())
        for task in tasks:
            self.tasks[ClusterTask.INITIAL_TASK].append(task)

    def raiseFailure(self, exception = None):
        self.failed = True
        if exception:
            raise exception
                       
    def start(self):
        # todo: Check the reachability and acylicity of the graph here
        checkGraphReachability(self.tasks[ClusterTask.INITIAL_TASK])
            
        for task in self.tasks[ClusterTask.INITIAL_TASK]:
            #todo: pass in files?
            started = task.start()
            tstate = task.getState()
            self._status("Started %s %d " % (task.getName(), tstate))
            if started and tstate != ClusterTask.FAILED_TASK:
                self.tasks_in_order.append(task)
                self._movequeue(task, ClusterTask.INITIAL_TASK, tstate)
            else:
                self.raiseFailure(SchedulerStartException(self.pendingtasks, self.tasks[ClusterTask.RETIRED_TASK], self.tasks[ClusterTask.COMPLETED_TASK], msg = "Exception starting: %s" % task.getName()))
                return False
        
        return True
        
    def isAlive(self):
        return self.failed == False
    
    def hasFailed(self):
        return self.failed
    
    def step(self):
        '''This determines whether the system state changes by checking the 
           state of the individual tasks.
           We return True iff all tasks are completed.'''
        
        # I told you I was sick. Don't step a broken scheduler.
        if self.failed:
             raise BadSchedulerException(self.pendingtasks, self.tasks[ClusterTask.RETIRED_TASK], self.tasks[ClusterTask.COMPLETED_TASK], msg = "The scheduler has failed.") 
        
        activeTasksOnCluster = []
        self.statechanged = False    
        alljobs = sge.qstat()
                      
        # Retire tasks
        activeTasks = self.tasks[ClusterTask.ACTIVE_TASK][:]
        for task in activeTasks:
            tstate = task.getState(alljobs)
            activeTasksOnCluster.append(task.getClusterStatus(alljobs))
            if tstate == ClusterTask.RETIRED_TASK:
                self._movequeue(task, ClusterTask.ACTIVE_TASK, ClusterTask.RETIRED_TASK)
            elif tstate == ClusterTask.FAILED_TASK:
                self._movequeue(task, ClusterTask.ACTIVE_TASK, ClusterTask.RETIRED_TASK)
                self.raiseFailure(TaskCompletionException(self.pendingtasks, self.tasks[ClusterTask.RETIRED_TASK], self.tasks[ClusterTask.COMPLETED_TASK], msg = "The task %s failed." % task.getName()))
                return False
        
        # Complete tasks
        retiredTasks = self.tasks[ClusterTask.RETIRED_TASK][:]
        for task in retiredTasks:
            dependents = task.getDependents()
            completed = True
            for dependent in dependents:
                if dependent.getState(alljobs) != ClusterTask.COMPLETED_TASK:
                    completed = False
                    break
            if completed:
                completed = task.complete()
                if completed:
                    self._movequeue(task, ClusterTask.RETIRED_TASK, ClusterTask.COMPLETED_TASK)
                else:
                    self.raiseFailure(TaskCompletionException(self.pendingtasks, self.tasks[ClusterTask.RETIRED_TASK], self.tasks[ClusterTask.COMPLETED_TASK], msg = "The task %s failed." % task.getName()))
            
            # Try to start any dependents if we can
            # A dependent *should* fire once all its prerequisite tasks have finished
            dependents = task.getDependents()
            for dependent in dependents:
                if dependent.getState(alljobs) == ClusterTask.INACTIVE_TASK:
                    self.pendingtasks[dependent] = True
                    self._status("Starting %s." % dependent.getName())
                    started = dependent.start()
                    if started:
                        self.tasks_in_order.append(dependent)
                        del self.pendingtasks[dependent]
                        self.statechanged = True
                        self.tasks[ClusterTask.ACTIVE_TASK].append(dependent)

        
        # Bad scheduler. No biscuit.
        if self.tasks[ClusterTask.INITIAL_TASK]:
            raise BadSchedulerException 
        
        # If we have no more tasks which will trigger other tasks to start i.e. active tasks
        # and we have pending tasks which have not been started, they never will be started.
        # John Hodgman - "Halting problem - solved. You're welcome."
        if self.pendingtasks and not (self.tasks[ClusterTask.ACTIVE_TASK]):
             raise SchedulerDeadlockException(self.pendingtasks, self.tasks[ClusterTask.RETIRED_TASK], self.tasks[ClusterTask.COMPLETED_TASK])
        
        self._status("<cluster>" % task, plain = True)
        for task in activeTasksOnCluster:
            if task:
                self._status("<task>%s</task>" % task, plain = True)
        self._status("</cluster>", plain = True)
                    
        if self.statechanged:
            for task in activeTasks:
                self._status("%s %d " % (task.getName(), tstate))
            if self.tasks[ClusterTask.ACTIVE_TASK]:
                self._status("<active>%s</active>" % self.tasks[ClusterTask.ACTIVE_TASK])
            if self.tasks[ClusterTask.RETIRED_TASK]:
                self._status("<retired>%s</retired>" % self.tasks[ClusterTask.RETIRED_TASK])
        
        # We are finished when there are no active or retired tasks
        return not(self.tasks[ClusterTask.ACTIVE_TASK] or self.tasks[ClusterTask.RETIRED_TASK]) 
    
    def cleanup(self):
        tasks = self._getAllTasks()
        for task in tasks:
            task.cleanup()

import pprint
class RosettaClusterJob(object):
    
    suffix = "job"
    
    def __init__(self, parameters, tempdir, targetroot):
        self.parameters = parameters
        self.debug = True
        self.tempdir = tempdir
        self.targetroot = targetroot
        self._make_workingdir() #todo: This will need to be done on chef itself from the server
        self._make_targetdir() #todo: This will need to be done on chef itself from the server
        self.jobID = self.parameters.get("ID") or 0
        self.filename_stdout = "stdout_%s_%d.txt" % (self.suffix, self.jobID)
        self.filename_stderr = "stderr_%s_%d.txt" % (self.suffix, self.jobID)
        self.profiler = SimpleProfiler.SimpleProfiler("%s-%d" % (self.suffix, self.jobID))
        self.profiler.PROFILE_START("Initialization")
        self._initialize()
        self.profiler.PROFILE_STOP("Initialization")
        
    def _initialize(self):
        '''Override this function.'''
        raise Exception
    
    def _status(self, message):
        if self.debug:
            print('<debug type="job">%s</debug>' % message)
            
    def start(self):
        try:
            self.scheduler.start()
        except TaskSchedulerException, e:
            print(e)
    
    def cleanup(self):
        self.scheduler.cleanup()
    
    def isCompleted(self):
        if self.scheduler.step():
            self.scheduler.cleanup()
            #self._status('distutils.dir_util.copy_tree(%s, %s)' % (self.workingdir, self.targetdirectory))
            return True
        else:
            return False

    def _analyze(self):
        '''Override this function.'''
        raise Exception
    
    def getprofileXML(self):
        return SimpleProfiler.listsOfTuplesToXML(self.getprofile())

    def getprofile(self):
        stats = self.profiler.PROFILE_STATS()
        stats.insert(-1, ("scheduler", self.scheduler.getprofile()))
        
        attr = None
        if self.scheduler.hasFailed():
            attr = 'succeeded = "false"' 
        else:    
            attr = 'succeeded = "true"' 
        
        stats = [("%s %s" % (self.suffix, attr), stats)]
        SimpleProfiler.sumTuples(stats)
        return stats
        
    def analyze(self):
        '''Any final output can be generated here. We assume here that all necessary files have been copied in place.'''
        self.profiler.PROFILE_START("Analysis")
        self._analyze()
        self.profiler.PROFILE_STOP("Analysis")
        return True
        
    def _make_workingdir(self):
        """Make a single used working directory inside the temporary directory"""
        # make a tempdir on the host
        self.workingdir = tempfile.mkdtemp("_%s" % self.suffix, dir = self.tempdir)
        if not os.path.isdir(self.workingdir):
            raise os.error
        return self.workingdir

    def _targetdir_file_path(self, filename):
        """Get the path for a file within the working directory"""
        return os.path.join(self.targetdirectory, filename)   

    def _make_targetdir(self):
        """Make a single used target directory inside the target directory"""
        # make a tempdir on the host
        self.targetdirectory = tempfile.mkdtemp("_%s" % self.suffix, dir = self.targetroot)
        if not os.path.isdir(self.targetdirectory):
            raise os.error
        return self.targetdirectory
    
    def _taskresultsdir_file_path(self, taskdir, filename):
        return os.path.join(self.targetdirectory, taskdir, filename)
    
    def _make_taskdir(self, dirname, files = []):
        """ Make a subdirectory dirname in the working directory and copy all files into it.
            Filenames should be relative to the working directory."""
        taskdir = "%s/%s" % (self.workingdir, dirname)
        if not os.path.isdir(taskdir):
            os.mkdir(taskdir)
        if not os.path.isdir(taskdir):
            raise os.error
        for file in files:
            #todo: This will copy the files from the webserver to chef
            shutil.copyfile("%s/%s" % (self.workingdir, file), "%s/%s" % (taskdir, file))
        return taskdir

    def _workingdir_file_path(self, filename):
        """Get the path for a file within the working directory"""
        return os.path.join(self.workingdir, filename)
    

