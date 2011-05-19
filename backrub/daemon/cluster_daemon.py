#!/usr/bin/python2.4

import os
import sys
sys.path.insert(0, "../common/")
sys.path.insert(1, "cluster")
import pdb
import time
import string
import pickle
import shutil
import zipfile
import traceback
import rosettadb
from daemon import Daemon
from datetime import datetime
from rosettahelper import * #RosettaError, get_files, grep, make755Directory, makeTemp755Directory
from RosettaProtocols import *
from rbutils import *
import RosettaTasks
from rosetta_daemon import RosettaDaemon
from conf_daemon import *
from sge import SGEConnection, SGEXMLPrinter

cwd = str(os.getcwd())

class ClusterDaemon(RosettaDaemon):
    
    MaxClusterJobs    = 3
    logfname          = "ClusterDaemon.log"
    pidfile           = '/tmp/rosettaweb-clusterdaemon.pid'
    
    def __init__(self, stdout, stderr):
        super(ClusterDaemon, self).__init__(stdout, stderr)        
        self.logfile = os.path.join(self.rosetta_tmp, self.logfname)
        self.beProtocols = ClusterProtocols(self)
        self.protocolGroups, self.protocols = self.beProtocols.getProtocols()
        self.setupSQL()
        self.sgec = SGEConnection()
        self._clusterjobjuststarted = None
        
        # Maintain a list of recent DB jobs started. This is to avoid any logical errors which 
        # would repeatedly start a job and spam the cluster. This should never happen but let's be cautious. 
        self.recentDBJobs = []                  
        
        if not os.path.exists(netappRoot):
            make755Directory(netappRoot)
        if not os.path.exists(cluster_temp):
            make755Directory(cluster_temp)
    
    def recordSuccessfulJob(self, clusterjob):
        self.runSQL('UPDATE %s SET Status=2, EndDate=NOW() WHERE ID=%s' % ( self.db_table, clusterjob.jobID ))

    def recordErrorInJob(self, clusterjob, errormsg, _traceback = None, _exception = None):
        jobID = clusterjob.jobID
        clusterjob.error = errormsg
        clusterjob.failed = True
        
        if _traceback and _exception:
            self.runSQL(('''UPDATE %s''' % self.db_table) + ''' SET Status=4, Errors=%s, AdminErrors=%s, EndDate=NOW() WHERE ID=%s''', parameters = (errormsg, "%s. %s." % (str(_traceback), str(_exception)), jobID))
        else:
            self.runSQL(('''UPDATE %s''' % self.db_table) + ''' SET Status=4, Errors=%s, EndDate=NOW() WHERE ID=%s''', parameters = (errormsg, jobID))
        self.log("Error: The %s job %d failed at some point:" % (clusterjob.suffix, jobID))
        self.log(errormsg)
        
    def run(self):
        """The main loop and job controller of the daemon."""
        
        print("Starting daemon.")
        self.log("%s\tStarted\n" % datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        self.runningJobs = []           # list of running processes
        self.killPreviouslyRunningJobs()
        sgec = self.sgec
        self.statusprinter = SGEXMLPrinter(sgec)
        self.diffcounter = CLUSTER_printstatusperiod
        
        counter = 1#upgradetodo
        
        while True:
            print("$$$ counter is %d $$$\n" % counter) #upgradetodo
            counter +=1#upgradetodo
            self.writepid()
            self.checkRunningJobs()
            self.startNewJobs()
            sgec.qstat(waitForFresh = True) # This should sleep until qstat can be called again
            self.printStatus()            
    
    def killPreviouslyRunningJobs(self):
        # If there were jobs running when the daemon crashed, see if they are still running, kill them and restart them
        # todo: used to be SELECT ID, status, pid
        results = self.runSQL("SELECT ID, Status FROM %s WHERE Status=1 and (%s) ORDER BY Date" % (self.db_table, self.SQLJobSelectString))
        for simulation in results:
            sgec = self.sgec
            sgec.qstat(force = True) # use of unnecessary force
            #todo: Check using qstat whether the job is running (check all children? log all qstat results to file. clear that file here and update it at the end of every run loop) and either kill it or email the admin and tell them (seeing as jobs take a while and the daemon may have failed rather than the job)              
            #if os.path.exists("/proc/%s" % simulation[2]): # checks if process is running
            #    if self.kill_process(simulation[2]): # checks if process was killed
            #        self.runSQL("UPDATE %s SET status=0 WHERE ID=%s" % (self.db_table, simulation[0]))
            #    else:
            #        self.log("%s\t process not killed: ID %s PID %s\n" % (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), simulation[0], simulation[2]) )
            #else:
            #    self.runSQL("UPDATE %s SET status=0 WHERE ID=%s" % (self.db_table, simulation[0]))
            self.log("Job possibly still running in the cluster since we crashed: %s" % str(simulation))
        

    def checkRunningJobs(self):
        completedJobs = []
        failedjobs = []
        
        # Remove failed jobs from the list
        # Any errors should already have been logged in the database
        for clusterjob in self.runningJobs:
            if clusterjob.failed:
                failedjobs.append(clusterjob)
                self.recordErrorInJob(clusterjob, clusterjob.error)
        for clusterjob in failedjobs:
            self.runningJobs.remove(clusterjob)
                    
        # Check if jobs are finished
        for clusterjob in self.runningJobs:
            jobID = clusterjob.jobID
            try:
                if clusterjob.isCompleted():
                    completedJobs.append(clusterjob)               

                    clusterjob.analyze()
                    clusterjob.saveProfile()
                    
                    self.end_job(clusterjob)
                    
                    print("<profile>")
                    print(clusterjob.getprofileXML())
                    print("</profile>")
                                                                           
            except Exception, e:
                self.recordErrorInJob(clusterjob, "Failed.", traceback.format_exc(), e)
                self.end_job(clusterjob)
                            
        # Remove completed jobs from the list
        for cj in completedJobs:
            self.runningJobs.remove(cj)
            
    def startNewJobs(self):
        # Start more jobs
        print("**startNewJobs**")
        newclusterjob = None
        if len(self.runningJobs) < self.MaxClusterJobs:            
            # get all jobs in queue
            data = self.runSQL("SELECT ID,Date,Status,PDBComplex,PDBComplexFile,Mini,EnsembleSize,task,ProtocolParameters,cryptID FROM %s WHERE Status=0 AND (%s) ORDER BY Date" % (self.db_table, self.SQLJobSelectString))
            try:
                if len(data) != 0:
                    jobID = None
                    for i in range(0, len(data)):
                        # Set up the parameters. We assume ProtocolParameters keys do not overlap with params.
                        jobID = data[i][0]
                        task = data[i][7]                            
                        params = {
                            "binary"            : data[i][5],
                            "cryptID"           : data[i][9],
                            "ID"                : jobID,
                            "pdb_filename"      : data[i][4],
                            "pdb_info"          : data[i][3],
                            "nstruct"           : data[i][6],
                            "task"              : task
                        }
                        ProtocolParameters = pickle.loads(data[i][8])
                        params.update(ProtocolParameters)                            
                        
                        # Remember that we are about to start this job to avoid repeatedly submitting the same job to the cluster
                        # This should not happen but just in case.
                        # Also, never let the list grow too large as the daemon should be able to run a long time                        
                        if jobID in self.recentDBJobs:
                            print("Error: Trying to run database job %d multiple times." % jobID) 
                            self.log("%s\t Error: Trying to run database job %d multiple times.\n" % (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), jobID))
                            raise
                        self.recentDBJobs.append(jobID)
                        if len(self.recentDBJobs) > 400:
                            self.recentDBJobs = self.recentDBJobs[200:]
                        
                        # Start the job
                        newclusterjob = self.start_job(task, params)
                        if newclusterjob:
                            #change status and write start time to DB
                            self.runningJobs.append(newclusterjob)
                            self.runSQL("UPDATE %s SET Status=1, StartDate=NOW() WHERE ID=%s" % ( self.db_table, jobID ))
                                                            
                        if len(self.runningJobs) >= self.MaxClusterJobs:
                            break
                        
            except Exception, e:
                newclusterjob = newclusterjob or self._clusterjobjuststarted
                self._clusterjobjuststarted = None
                print("%s\t error: self.run()\n%s\n\n" % (datetime.now().strftime("%Y-%m-%d %H:%M:%S"),traceback.format_exc()) )
                if newclusterjob:
                    newclusterjob.kill()
                    self.recordErrorInJob(newclusterjob, "Error starting job.", traceback.format_exc(), e)
                    if newclusterjob in self.runningJobs:
                        self.runningJobs.remove(newclusterjob)
                else:
                    self.runSQL('UPDATE %s SET Errors="Start.\n%s\n%s", Status=4 WHERE ID=%s' % ( self.db_table, traceback.format_exc(), e, str(jobID) ))                                      
                self.log("%s\t error: self.run()\n%s\n\n" % (datetime.now().strftime("%Y-%m-%d %H:%M:%S"),traceback.format_exc()) )
            self._clusterjobjuststarted = None

    def start_job(self, task, params):

        clusterjob = None
        jobID = params["ID"]
        
        self.log("%s\t start new job ID = %s, mini = %s, %s \n" % ( datetime.now().strftime("%Y-%m-%d %H:%M:%S"), jobID, params["binary"], task) )
        if task == "sequence_tolerance":
            params["radius"] = 5.0
            clusterjob = RosettaTasks.SequenceToleranceJobHK(self.sgec, params, netappRoot, cluster_temp)   
        elif task == "sequence_tolerance_SK":
            params["radius"] = 10.0
            clusterjob = RosettaTasks.ParallelSequenceToleranceJobSK(self.sgec, params, netappRoot, cluster_temp)     
        elif task == "multi_sequence_tolerance":
            params["radius"] = 10.0
            clusterjob = RosettaTasks.SequenceToleranceMultiJobSK(self.sgec, params, netappRoot, cluster_temp)            
        else:
            raise
        
        # Start the job
        self._clusterjobjuststarted = clusterjob        # clusterjob will not be returned on exception and the reference will be lost
        clusterjob.start()
        return clusterjob
    
    def printStatus(self):
        '''Print the status of all jobs.'''
        statusprinter = self.statusprinter
        
        if self.runningJobs:
            someoutput = False
            diff = statusprinter.qdiff()
            
            if False: # For debugging
                sys.stdout.write("\n")
                if self.sgec.CachedList:
                    print(self.sgec.CachedList)
                
            if diff:
                sys.stdout.write("\n")
                self.diffcounter += 1
                if self.diffcounter >= CLUSTER_printstatusperiod:
                    # Every x diffs, print a full summary
                    summary = statusprinter.summary()
                    statusList = statusprinter.statusList()
                    if summary:
                        print(summary)
                    if statusList:
                        print(statusList)
                    self.diffcounter = 0
                print(diff)
            else:
                # Indicate tick
                sys.stdout.write(".")
        else:
            sys.stdout.write(".")
        sys.stdout.flush()
            
            
    def end_job(self, clusterjob):
        
        try:
            self.copyAndZipOutputFiles(clusterjob, clusterjob.parameters["task"])
        except Exception, e:
            self.recordErrorInJob(clusterjob, "Error archiving files.", traceback.format_exc(), e)
        
        try:
            self.removeClusterTempDir(clusterjob)
        except Exception, e:
            self.recordErrorInJob(clusterjob, "Error removing temporary directory on the cluster", traceback.format_exc(), e)
            
        if not clusterjob.error:
            self.recordSuccessfulJob(clusterjob)

        ID = clusterjob.jobID                        
        data = self.runSQL("SELECT u.Email,u.FirstName,b.KeepOutput,b.cryptID,b.task,b.PDBComplexFile,b.EnsembleSize,b.Mini FROM Users AS u JOIN %s AS b on (u.ID=b.UserID) WHERE b.ID=%s" % ( self.db_table, str(ID) ), "Users AS u READ, %s AS b WRITE" % self.db_table)
        cryptID      = data[0][3]
        task         = data[0][4]
        keep_output  = int(data[0][2])
        status = 2        
        self.notifyUserOfCompletedJob(data, ID, cryptID, clusterjob.error)

    def moveFilesOnJobCompletion(self, clusterjob):
        try:
            return clusterjob.moveFilesTo(cluster_dltest)
        except Exception, e:
            print("moveFilesOnJobCompletion failure")
            self.log("Error moving files to the download directory.\n")
            self.log("%s\n%s" % (str(e), traceback.print_exc()))        
    
    def copyAndZipOutputFiles(self, clusterjob, task):
            
        ID = clusterjob.jobID                        
        
        # move the data to a webserver accessible directory 
        result_dir = self.moveFilesOnJobCompletion(clusterjob)
        
        # remember directory
        current_dir = os.getcwd()
        os.chdir(result_dir)
        
        # let's remove all empty files to not confuse the user
        self.exec_cmd('find . -size 0 -exec rm {} \";\"', result_dir)
        
        # store all files also in a zip file, to make it easier accessible
        if False and task == 'sequence_tolerance': #upgradetodo fix
            flist = []
            flist.append()
            flist.append("minimization/*.resfile backrub/*.resfile sequence_tolerance/*.pdb")
            flist.append("minimization/*.resfile backrub/*.resfile sequence_tolerance/*.resfile")
            self.exec_cmd("zip data_%s *.pdb  stdout*.txt freq_*.txt tolerance* specificity*" % (ID), result_dir)
        #todo: Which files go into a zipfile?
        else:            
            filename_zip = "data_%s.zip" % ( ID )
            all_output = zipfile.ZipFile(filename_zip, 'w', zipfile.ZIP_DEFLATED)
            abs_files = get_files('./')
            
            # Do not include the timing profile in the zip
            timingprofile = os.path.join(result_dir, "timing_profile.txt")
            if timingprofile in abs_files:
                abs_files.remove(timingprofile)
                
            os.chdir(result_dir)
            filenames_for_zip = [ string.replace(fn, os.getcwd()+'/','') for fn in abs_files ] # os.listdir(result_dir)
                                    
            for file in filenames_for_zip:
                if file != filename_zip:
                    all_output.write( file )
                    
            all_output.close()
        
        # go back to our working dir 
        os.chdir(current_dir)
    
    def removeClusterTempDir(self, clusterjob):
        try:
            clusterjob.removeClusterTempDir()
        except Exception, e:
            self.log("Error removing the temporary directory on the cluster.\n")
            self.log("%s\n%s" % (str(e), traceback.print_exc()))        

    #todo: Add these to the scheduler
    def EndSequenceToleranceHK(self, rosetta_object, pdb_id, ensembleSize, state, ID):
        state["keep_output"] = True
        self.running_S -= 1
        
        # remove files that we don't need
        if os.path.exists(rosetta_object.workingdir + '/' + 'error.txt') and os.path.getsize(rosetta_object.workingdir + '/' + 'error.txt') > 0:
            handle = open(rosetta_object.workingdir + '/' + 'error.txt', 'r')
            state["error"] = "Plasticity classic fail (%s out of %s crashed)" % (len(handle), ensembleSize)
            state["status"] = 4
            raise RosettaError( "sequence_tolerance", ID )
        
        if os.path.exists(rosetta_object.workingdir + '/backrub_0_stderr.txt'):
            os.remove(rosetta_object.workingdir + '/backrub_0_stderr.txt') # backrub error output, shoudl be empty
        if os.path.exists(rosetta_object.workingdir + '/entities.Rda'):
            os.remove(rosetta_object.workingdir + '/entities.Rda') # R temp file
        if os.path.exists(rosetta_object.workingdir + '/specificity_boxplot_NA.png'):
            os.remove(rosetta_object.workingdir + '/specificity_boxplot_NA.png') # boxplot tempfile I guess

        if os.path.exists(rosetta_object.workingdir + '/failed_minimization.txt'):
            ID = rosetta_object.get_ID()
            self.log("%s\t error: ID %s SEQTOL MINIMIZATION FAILED\n*******************************\n" % ( datetime.now().strftime("%Y-%m-%d %H:%M:%S"), ID ) )
            self.runSQL('UPDATE %s SET Errors="Terminated" Status=4 WHERE ID=%s' % ( self.db_table, ID ))
                            
        elif os.path.exists(rosetta_object.workingdir + '/failed_backrub.txt'):
            failed_handle = open(rosetta_object.workingdir + '/backrub_failed.txt','r')
            ID = rosetta_object.get_ID()
            if len(failed_handle.readlines()) == 2:
                self.log("%s\t error: ID %s SEQTOL BACKRUB TERMINATED\n*******************************\n" % ( datetime.now().strftime("%Y-%m-%d %H:%M:%S"), ID ) )
                self.runSQL('UPDATE %s SET Errors="Terminated" Status=4 WHERE ID=%s' % ( self.db_table, ID ))    
            else: # individual files missing
                no_failed = len(failed_handle.readlines()) - 2
                self.log("%s\t error: ID %s SEQTOL BACKRUB FAILED %s\n*******************************\n" % ( datetime.now().strftime("%Y-%m-%d %H:%M:%S"), ID, no_failed ) )
                self.runSQL('UPDATE %s SET Errors="backrub failed" Status=4 WHERE ID=%s' % ( self.db_table, ID ))
        
        elif os.path.exists(rosetta_object.workingdir + '/failed_jobs.txt'):
            failed_handle = open(rosetta_object.workingdir + '/failed_jobs.txt','r')
            no_failed = len(failed_handle.readlines())
            failed_handle.close()  
            ID = rosetta_object.get_ID()
            self.log("%s\t warning: ID %s SEQTOL RUNS TERMINATED %s\n*******************************\n" % ( datetime.now().strftime("%Y-%m-%d %H:%M:%S"), ID, no_failed ) )
            self.runSQL('UPDATE %s SET Errors="Terminated" Status=4 WHERE ID=%s' % ( self.db_table, ID ))

    def CheckSequenceTolerance(self, r_object, ensembleSize, pdb_id, job_id, task, binaryName):
        #todo: fix this up       
        handle = open(r_object.workingdir_file_path(r_object.filename_stdout),'r')
        if len(grep("Running Postprocessing and Analysis.", handle.readlines())) < 1:
            # AAAAAAAHHHH MESSY CODE!
            ID = r_object.get_ID()
            self.log("%s\t error: end_job() ID %s - error during simulation\n" % ( datetime.now().strftime("%Y-%m-%d %H:%M:%S"), ID ) )
            self.runSQL('UPDATE %s SET Errors="Terminated", Status=4 WHERE ID=%s' % ( self.db_table, ID ))
        
            handle.close()
            return True # to not raise the RosettaError and trigger additional error handling. Yikes!
        
        if len(grep("Success!", handle.readlines())) < 1:
            handle.close()
            return True
        handle.close()
        return True

    def EndSequenceToleranceSK(self, rosetta_object, pdb_id, ensembleSize, state, ID):
        state["keep_output"] = True
        self.running_S -= 1
        
        if False:
            #todo: This code was disabled - see if we should use it
            if not os.path.exists(rosetta_object.workingdir + '/'+pdb_id+'_0_0001_last.pdb') and not os.path.exists(rosetta_object.workingdir + '/'+pdb_id+'_0_0001_low.ga.entities.gz'):
                state["error"] = "Plasticity fail"
                state["status"] = 4
                raise RosettaError( "sequence_tolerance_SK", ID )
            else:
                for i in range(ensembleSize): # delete individual seqtol output
                    if os.path.exists( rosetta_object.workingdir + '/seqtol_%s_stderr.txt' % i ):
                        os.remove( rosetta_object.workingdir + '/seqtol_%s_stderr.txt' % i )
                    if os.path.exists( rosetta_object.workingdir + '/seqtol_%s_stdout.txt' % i ):
                        os.remove( rosetta_object.workingdir + '/seqtol_%s_stdout.txt' % i )
            
            if os.path.exists(rosetta_object.workingdir + '/backrub_0_stderr.txt'):
                os.remove(rosetta_object.workingdir + '/backrub_0_stderr.txt') # backrub error output, shoudl be empty
            if os.path.exists(rosetta_object.workingdir + '/entities.Rda'):
                os.remove(rosetta_object.workingdir + '/entities.Rda') # R temp file
            if os.path.exists(rosetta_object.workingdir + '/specificity_boxplot_NA.png'):
                os.remove(rosetta_object.workingdir + '/specificity_boxplot_NA.png') # boxplot tempfile I guess

class ClusterProtocols(WebserverProtocols):
      
    def __init__(self, clusterDaemon):
        super(ClusterProtocols, self).__init__()
        
        protocolGroups = self.protocolGroups
        protocols = self.protocols
        
        # Add backend specific information
        removelist = []
        for p in protocols:
            if p.dbname == "sequence_tolerance":
                p.setBackendFunctions(None, clusterDaemon.CheckSequenceTolerance, clusterDaemon.EndSequenceToleranceHK)
            elif p.dbname == "sequence_tolerance_SK":
                p.setBackendFunctions(None, clusterDaemon.CheckSequenceTolerance, clusterDaemon.EndSequenceToleranceSK)
            else:
                removelist.append(p)
        
        # Prune the protocols list
        for rp in removelist:
            protocols.remove(rp)
                