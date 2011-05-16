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
import subprocess
import rosetta_rdc
import rosettaplusplus
import pprint
from daemon import Daemon
from datetime import datetime
from analyze_mini import AnalyzeMini
from analyze_classic import AnalyzeClassic
from rosettahelper import * #RosettaError, get_files, grep, make755Directory, makeTemp755Directory
from RosettaProtocols import *
from rbutils import *
import RosettaTasks
from conf_daemon import *
from sge import SGEConnection, SGEXMLPrinter

cwd = str(os.getcwd())

class RosettaDaemon(Daemon):
    """This class controls the rosetta simulation"""
    
    # those are set by configure(self, filename_config)
    email_admin       = ''  # server administrators email adderss
    db_table          = ''
    server_name       = ''
    base_dir          = ''
    rosetta_tmp       = ''  
    rosetta_ens_tmp   = ''
    rosetta_dl        = ''  # webserver accessible directory
    rosetta_error_dir = ''  # directory were failed runs should be stored
    store_time        = ''  # how long are we going to store the data
    store_time_guest  = '30'  # how long are we going to store the data for guest users
    ntrials           = 10000 # THIS SHOULD BE 10000
    logSQL            = False
    logfname          = "RosettaDaemon.log"
    pidfile           = '/tmp/rosettaweb-rosettadaemon.pid'
    email_text_error  = """Dear %s,
    
An error occurred during your simulation. Please check 
http://%s/backrub/cgi-bin/rosettaweb.py?query=jobinfo&jobnumber=%s 
for more information.

The Kortemme Lab Server Daemon
"""

    email_text_success = """Dear %s,

Your simulation finished successfully. You can download the results as a zipped file or as individual files. Additional information can be found on our webserver.

- Job Information:  https://%s/backrub/cgi-bin/rosettaweb.py?query=jobinfo&jobnumber=%s
- Zip file:  https://%s/backrub/downloads/%s/data_%s.zip
- Individual output files:  https://%s/backrub/cgi-bin/rosettaweb.py?query=datadir&job=%s


Your data will be stored for %s days. Thank you for using Backrub.

Have a nice day!

The Kortemme Lab Server Daemon

"""

    def __init__(self, stdout, stderr):
        super(RosettaDaemon, self).__init__(self.pidfile, stdout = stdout, stderr = stderr)
        self.configure()
        self.logfile = os.path.join(self.rosetta_tmp, self.logfname)
        self.beProtocols = BackendProtocols(self)
        self.protocolGroups, self.protocols = self.beProtocols.getProtocols()
        self.max_processes     = 0  # maximal number of processes that can be run at a time
        self.setupSQL()
    
    def setupSQL(self):
        dbnames = self.beProtocols.getProtocolDBNames()
        SQLJobSelectString = []
        for dbn in dbnames:
            SQLJobSelectString.append('task="%s"' % dbn)
        if SQLJobSelectString:
            self.SQLJobSelectString = string.join(SQLJobSelectString, " OR ")
        else:
            raise
    
    def kill_process (self, pid):
        try:
            os.kill(int(pid), 0)
            return True
        except:
            return False
    
    def log(self, str):
        log = open(self.logfile, 'a+')
        log.write(str)
        log.close()
        
    def run(self):
        """runs the daemon, sets the maximal number of parallel simulations"""
        
        self.list_RosettaPP = [] # list of running processes
        self.running_P = 0 # total no of jobs
        self.running_S = 0 # sequence tolerance
        
        # logfile
        self.log("%s\tstarted\n" % datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        
        # if there were jobs running when the daemon crashed, see if they are still running, kill them and restart them
        #self.runSQL("LOCK TABLES %s WRITE, Users READ" % self.db_table)
        try:
            results = self.runSQL("SELECT ID, Status, pid FROM %s WHERE Status=1 ORDER BY Date" % self.db_table)
            for simulation in results:
                if os.path.exists("/proc/%s" % simulation[2]): # checks if process is running
                    if self.kill_process(simulation[2]): # checks if process was killed
                        self.runSQL("UPDATE %s SET Status=0 WHERE ID=%s" % (self.db_table, simulation[0]))
                    else:
                        self.log("%s\t process not killed: ID %s PID %s\n" % (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), simulation[0], simulation[2]) )
                else:
                    self.runSQL("UPDATE %s SET Status=0 WHERE ID=%s" % (self.db_table, simulation[0]))
        except TypeError: # iteration over non-sequence, i.e. results is empty
            pass
        #self.runSQL("UNLOCK TABLES")
                        
        while True:
            # this is executed every 30 seconds if the maximum number of jobs is running
            self.writepid()
            if self.running_P != len(self.list_RosettaPP):
                self.running_P = len(self.list_RosettaPP)
                # only write this on change so the actual file doesn't get too big.
                print "%s\trunning processes:" % (datetime.now().strftime("%Y-%m-%d %H:%M:%S")), self.running_P
            
            # make sure this is written to the disk            
            sys.stdout.flush()
            sys.stderr.flush()
            os.fsync(sys.stdout)
            os.fsync(sys.stderr)
            # check if a simulation is finished
            
            completedJobs = []
            for rosetta_object in self.list_RosettaPP:
                ID = rosetta_object.get_ID()
                pid = rosetta_object.get_pid()
                error = ""
                if rosetta_object.is_done():
                    if rosetta_object.exit == "terminated":
                        self.log("%s\t error: ID %s PROCESS TERMINATED\n" % (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), ID) )
                        error = "Terminated"
                    else:
                        # call clean up function
                        try:
                            (status, error, ID) = self.end_job(rosetta_object)
                            error = '' # since error should already be set by end_job
                        except IndexError:
                            self.log("%s\t error: ID %s end_job failed, job terminated externally\n" % (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), ID) )
                            error = "Terminated"
                    
                    # remove object
                    completedJobs.append(rosetta_object)
                    #self.runSQL("LOCK TABLES %s WRITE, Users READ" % self.db_table)
                    res = self.runSQL('SELECT Errors FROM %s WHERE ID=%s' % (self.db_table, ID))
                    if res[0][0] != '' and res[0][0] != None:
                        self.runSQL('UPDATE %s SET Status=4, EndDate=NOW() WHERE ID=%s' % ( self.db_table, ID ))
                    elif error != '':
                        self.runSQL('UPDATE %s SET Status=4, Errors=%s, EndDate=NOW() WHERE ID=%s' % ( self.db_table,error,ID ))
                    else:
                        self.runSQL('UPDATE %s SET Status=2, EndDate=NOW() WHERE ID=%s' % ( self.db_table, ID ))
                    #self.runSQL("UNLOCK TABLES")
                    
            # Remove completed jobs
            for cj in completedJobs:
                self.list_RosettaPP.remove(cj)
                            
            # check whether data of simulations need to be deleted, and delete them from the database as well as from the harddrive
            try:
                self.delete_data()
            except Exception, e:
                self.log("%s\t error: self.delete()\n%s\n\n" % (datetime.now().strftime("%Y-%m-%d %H:%M:%S"),traceback.format_exc()) )
                #sys.exit(2)

            if len(self.list_RosettaPP) < self.max_processes:
                #print "check for new job"
                # get job from db
                # first lock tables, no surprises!
                #self.runSQL("LOCK TABLES %s WRITE, Users READ" % self.db_table)
                                    
                # get all jobs in queue                            vvv 0
                try:
                    data = self.runSQL("SELECT ID,Date,Status,task FROM %s WHERE Status=0 ORDER BY Date" % self.db_table)
                    if len(data) == 0:
                        #self.runSQL("UNLOCK TABLES")
                        time.sleep(10) # wait 10 seconds if there's no job in queue
                        continue
                    else:
                        ID = None
                        for i in range(0,len(data)):
                            # if this is a sequence_tolerance job, but the limit is already being processed
                            if (data[i][3] == 'sequence_tolerance' or data[i][3] == 'sequence_tolerance_SK'): 
                                continue # skip it
                            else:
                                # get first job
                                ID = data[i][0]
                                                                               
                                # get pdb file
                                job_data = self.runSQL("SELECT PDBComplex,PDBComplexFile,Mini,EnsembleSize,task, ProtocolParameters FROM %s WHERE ID=%s" % ( self.db_table, ID ))
                            
                                #start the job
                                pid = self.start_job(ID,job_data[0][0],job_data[0][1],job_data[0][2],job_data[0][3],job_data[0][4],job_data[0][5])
                                #change status and write starttime to DB
                                if pid:
                                    self.runSQL("UPDATE %s SET Status=1, StartDate=NOW(), pid=%s WHERE ID=%s" % ( self.db_table, pid, ID ))
                                    break

                        # don't forget to unlock the tables!
                        #self.runSQL("UNLOCK TABLES")
                        
                        time.sleep(3) # wait 3 seconds after a job was started
                except Exception, e:
                    self.log("%s\t error: self.run()\n%s\n\n" % (datetime.now().strftime("%Y-%m-%d %H:%M:%S"),traceback.format_exc()) )
                    self.runSQL('UPDATE %s SET Errors="Start", Status=4 WHERE ID=%s' % ( self.db_table, ID ))                  
                    #self.runSQL("UNLOCK TABLES")
                    time.sleep(10)

            else:
                time.sleep(30)  # wait 5 seconds if max number of jobs is running

        
    # split this one up in individual functions at some point
    def start_job(self, ID, pdb_info, pdb_filename, mini, ensemble_size, task, ProtocolParameters):
        
        pid = None
        try:
            self.log("%s\t start new job ID = %s, mini = %s, %s \n" % ( datetime.now().strftime("%Y-%m-%d %H:%M:%S"), ID, mini, task) )
            
            # todo: The "task" dict entry is a hack for the mutations protocols. Remove when their functions are separated out            
            params = pickle.loads(ProtocolParameters)
            params["task"] = task 
            
            for p in self.protocols:
                if p.dbname == task:
                    return p.startFunction(ID, pdb_info, pdb_filename, mini, ensemble_size, params)
          
        except Exception, e: 
            self.log("%s\t error: start_job() ID = %s\n%s\n\n" % ( datetime.now().strftime("%Y-%m-%d %H:%M:%S"), ID, traceback.format_exc() ) )
            
        return pid

    def check_files(self, r_object, ensembleSize, pdb_id, job_id, task, binaryName):
        """checks whether all pdb files were created
           sometimes Rosetta classic crashes at the end, but the results are ok
        """
        # This function takes the last-files into account... and deletes them! We don't need them!        
        for p in self.protocols:
            if p.dbname == task:
                if p.checkFunction(r_object, ensembleSize, pdb_id, job_id, task, binaryName):
                    self.log("%s\t\t check_files() ID = %s, task = %s : all files successfully created\n" % ( datetime.now().strftime("%Y-%m-%d %H:%M:%S"), job_id, task ) )
                    return True
        return False
    
            
    def runSQL(self, query, alternateLocks = "", parameters = None):
        """ This function should be the only place in this class which executes SQL.
            Previously, bugs were introduced by copy and pasting and executing the wrong SQL commands (stored as strings in copy and pasted variables).
            Using this function and passing the string in reduces the likelihood of these errors.
            It also allows us to log all executed SQL here if we wish.
            
            We are lock-happy here but SQL performance is not currently an issue daemon-side. 
            """ 
        if self.logSQL:
            self.log("SQL: %s\n" % query)
        results = []
        try:
            lockstr = alternateLocks or "%s WRITE, Users READ" % self.db_table         
            self.DBConnection.execQuery("LOCK TABLES %s" % lockstr)
            results = self.DBConnection.execQuery(query, parameters)
        except Exception, e:
            self.DBConnection.execQuery("UNLOCK TABLES")
            raise e
        self.DBConnection.execQuery("UNLOCK TABLES")
        return results

    
    def end_job(self, rosetta_object):
        
        ID       = int( rosetta_object.get_ID() )
                        
        data = self.runSQL("SELECT u.Email,u.FirstName,b.KeepOutput,b.cryptID,b.task,b.PDBComplexFile,b.EnsembleSize,b.Mini FROM Users AS u JOIN %s AS b on (u.ID=b.UserID) WHERE b.ID=%s" % ( self.db_table, ID ), "Users AS u READ, %s AS b WRITE" % self.db_table)
        cryptID      = data[0][3]
        task         = data[0][4]
        pdb_id       = data[0][5].split('.')[0]
        ensembleSize = data[0][6]
        binaryName   = data[0][7]
        state = {
                 "status" : 2,       # 2 means everything went well
                 "error" : "",
                 "keep_output" : int(data[0][2])
        }
        
        try:               
            # open error messages
            # todo: This doesn't seem to generalise e.g. seqtol has many possible stderr files    
            error_handle = open( rosetta_object.workingdir + "/" + rosetta_object.filename_stderr, 'r')
            error_file = error_handle.read()
            error_handle.close()
                        
            # check whether an error occured i.e. the error file is empty
            # default movemap error! if len(error_file) > 1 # lets ignore the error file as long as all files are there
            # I naively assume that Gregs ensembles are always created correctly
            if not self.check_files(rosetta_object, ensembleSize, pdb_id, ID, task, binaryName):
                state["error"] = "Rosetta Error"
                state["status"] = 4
                raise RosettaError( task, ID )
    
            else: 
                # if no error occured move results directory to the download directory 
                #try:
                if os.path.exists(rosetta_object.workingdir + "/paths.txt"):
                    os.remove( rosetta_object.workingdir + "/paths.txt" )
                if os.path.exists( rosetta_object.workingdir + "/molprobity_err_0.dat" ):
                    os.remove( rosetta_object.workingdir + "/molprobity_err_0.dat" )
                
                #todo: Which temp files should be deleted? 
                
                # remove error file, it should be empty anyway
                #os.remove( rosetta_object.workingdir + "/stderr_%s.dat" % ( ID ) )

                for p in self.protocols:
                    if p.dbname == task:
                        p.endFunction(rosetta_object, pdb_id, ensembleSize, state, ID)

                # remove the resfile, and rosetta raw output if the user doesn't want to keep it
                if not state["keep_output"]:
                    os.remove( rosetta_object.workingdir + "/" + rosetta_object.name_resfile )
                    os.remove( rosetta_object.workingdir + "/stdout_%s.dat" % ( ID ) )

        except Exception, e:
            ID = rosetta_object.get_ID()
            XX = "%s\t error: end_job() ID %s - postprocessing error\n*******************************\n" % ( datetime.now().strftime("%Y-%m-%d %H:%M:%S"), ID )
            self.log("%s\n%s*******************************\n" % (XX, traceback.format_exc()) )
            self.runSQL('UPDATE %s SET Errors="Postprocessing", Status=4 WHERE ID=%s' % ( self.db_table, ID ))
            state["error"] = "Postprocessing"
            
            #try:
            #  handle = open(rosetta_object.filename_stdout,'r')
            #  if handle.readlines()[-1].strip() == '*****ERROR TOO MANY CYSTEINES COUNTED*****':
            #    XX = "%s\t error: end_job() ID %s - postprocessing error- TOO MANY CYSTEINS\n*******************************\n" % ( datetime.now().strftime("%Y-%m-%d %H:%M:%S"), ID )
            #    sql = 'UPDATE %s SET Errors="Too many Cysteines", Status=4 WHERE ID=%s' % ( self.db_table, ID )
            #  handle.close()
            #except:
        #  pass            
        
        error = state["error"]
        status = state["status"]
        
        try:
            if error == "Postprocessing":
                raise RosettaError( "postprocessing", ID )
            self.copyAndZipOutputFiles(rosetta_object, ID, task, cryptID)    
        except Exception, e:
            ID = rosetta_object.get_ID()
            self.log("%s\t error: end_job() ID = %s - error moving files\n*******************************\n%s*******************************\n" % ( datetime.now().strftime("%Y-%m-%d %H:%M:%S"), ID, traceback.format_exc() ) )
            self.runSQL('UPDATE %s SET Errors="Terminated", Status=4 WHERE ID=%s' % ( self.db_table, ID ))
            error = "error moving files"
            
            # # if this error occurs we store the output in the error directory so that the user cannot access it
            # if os.path.exists( self.rosetta_error_dir + "%s/" % ID ):
            #   shutil.rmtree( self.rosetta_error_dir + "%s/" % ID )
            # if os.path.exists( rosetta_object.workingdir ):
            #   shutil.move( rosetta_object.workingdir, self.rosetta_error_dir + "%s/" % ID ) ## does NOT overwrite destination
               
            ########################################################################################  
            # let's move the errors to the webserver too so that someone can more easily debug it. #
            ########################################################################################
            # same code as above therefore no comments
            result_dir = "%s%s" % (self.rosetta_dl, cryptID)
            if os.path.exists( result_dir ):
                shutil.rmtree( result_dir )
            shutil.move( rosetta_object.workingdir, result_dir ) ## does NOT overwrite destination
            os.chmod( result_dir, 0775 )
            current_dir = os.getcwd()
            os.chdir(result_dir)
            self.exec_cmd('find . -size 0 -exec rm {} \";\"', result_dir)
            os.chdir(current_dir)
        
        self.notifyUserOfCompletedJob(data, ID, cryptID, error)
        return (status, error, ID)
    
    def copyAndZipOutputFiles(self, rosetta_object, ID, task, cryptID):
            
        # copy files to web accessible directory
        result_dir = "%s%s" % (self.rosetta_dl, cryptID)
        # move the data to a webserver accessible directory 
        if os.path.exists( result_dir ):
            shutil.rmtree( result_dir )
        shutil.move( rosetta_object.workingdir, result_dir ) ## does NOT overwrite destination
        #shutil.rename( rosetta_object.workingdir, result_dir )
        # make it readable
        os.chmod( result_dir, 0777 )
        # remember directory
        current_dir = os.getcwd()
        os.chdir(result_dir)
        # let's remove all empty files to not confuse the user
        self.exec_cmd('find . -size 0 -exec rm {} \";\"', result_dir)
        # store all files also in a zip file, to make it easier accessible

        filename_zip = "data_%s.zip" % ( ID )
        all_output = zipfile.ZipFile(filename_zip, 'w', zipfile.ZIP_DEFLATED)
        abs_files = get_files('./')
        os.chdir(result_dir)
        filenames_for_zip = [ string.replace(fn, os.getcwd()+'/','') for fn in abs_files ] # os.listdir(result_dir)
                                
        for file in filenames_for_zip:
            if file != filename_zip:
                all_output.write( file )
                
        all_output.close()
        
        # go back to our working dir 
        os.chdir(current_dir)
            
    def notifyUserOfCompletedJob(self, data, ID, cryptID, error):
        user_email   = data[0][0]
        user_name    = data[0][1]              
        subject  = "Kortemme Lab Backrub Server - Your Job #%s" % (ID)
        mailTXT = ''
        adminTXT = ''
        
        if not error:
            mailTXT = self.email_text_success % (user_name, self.server_name, cryptID, self.server_name, cryptID, ID, self.server_name, cryptID, self.store_time) 
        else:
            mailTXT = self.email_text_error % (user_name, self.server_name, cryptID)
            if user_name == "Shane": #todo
                mailTXT = "%s\nerror='%s'" % (mailTXT, str(error))
            if self.server_name == 'albana.ucsf.edu':
                subject = 'Albana test job %d failed.' % ID
                adminTXT = 'An error occured during TEST server simulation #%s.' % ID
            else:
                adminTXT = 'An error occured during simulation #%s.' % ID

        if mailTXT != '' and user_name != "guest":
            if not self.sendMail(user_email, self.email_admin, subject, mailTXT):
                self.log("%s\t error: sendMail() ID = %s" % ( datetime.now().strftime("%Y-%m-%d %H:%M:%S"), ID ) )                
                self.runSQL('UPDATE %s SET Errors="no email sent" WHERE ID=%s' % ( self.db_table, ID ))
        
        if adminTXT != '':
            if not self.sendMail(self.email_admin, self.email_admin, subject, adminTXT):
                self.log("%s\t error: sendMail() ID = %s" % ( datetime.now().strftime("%Y-%m-%d %H:%M:%S"), ID ) )                
                self.runSQL('UPDATE %s SET Errors="no email sent" WHERE ID=%s' % ( self.db_table, ID ))
                
    def exec_cmd(self, cmd, run_dir):
        subp = subprocess.Popen(cmd,
                              stdout=subprocess.PIPE,
                              stderr=subprocess.PIPE,
                              cwd=run_dir,
                              shell=True,
                              executable='/bin/bash' )
        while subp.poll() == None:
            time.sleep(0.1)
        return True
        
    def _get_score_from_pdb_file(self, filename):
        handle = open(filename, 'r')
        handle.readline() # discard first line, 2nd is interesting to us
        score = handle.readline().split()[-1]
        handle.close()
        return score
        
    def delete_data(self):
        # Delete jobs whose time has expired
        
        # get due runs for guest user        
        data = self.runSQL('SELECT br.ID, br.cryptID, br.EndDate, br.Status FROM %s br, Users u WHERE u.UserName="guest" AND br.UserID=u.ID AND DATE_ADD(EndDate, INTERVAL %s DAY) < NOW() AND br.Status!="5"' % ( self.db_table, self.store_time_guest ))
        
        #get due runs for all others
        sqlquery = 'SELECT br.ID, br.cryptID, br.EndDate, br.Status FROM %s br, Users u WHERE u.UserName!="guest" AND br.UserID=u.ID AND DATE_ADD(EndDate, INTERVAL %s DAY) < NOW() AND br.Status!="5"' % ( self.db_table, self.store_time )
        if data == None:
            data = self.runSQL(sqlquery)
        else:
            data += self.runSQL(sqlquery)
        if len(data) > 0:
            for x in data:
              
                del_ID  = x[0]
                cryptID = x[1]
                # START DELETE
                # query   = 'DELETE FROM %s WHERE ID=%s' % ( self.db_table, del_ID )
                # self.DBConnection.execQuery(query)
                # 
                # log.write("%s\t job %s: deleted from database" % ( datetime.now().strftime("%Y-%m-%d %H:%M:%S"), del_ID ) )
                # 
                # if x[3] in [2,4]:
                #     shutil.rmtree( "%s%s" % (self.rosetta_dl, cryptID) )
                #     rmdir = "%s%s" % (self.rosetta_dl, del_ID)
                # #else:
                # #    shutil.rmtree( "%s../error/%s" % (self.rosetta_dl, del_ID) )
                # #    rmdir = "%s../error/%s" % (self.rosetta_dl, del_ID)
                # #print "delete: %s" % (rmdir)
                # log.write("%s\t job %s: directory %s%s deleted \n" % ( datetime.now().strftime("%Y-%m-%d %H:%M:%S"), del_ID, self.rosetta_dl, cryptID ) )
                # log.close() # END DELETE
                
                # instead of deleting, we now copy everything into the archive directory... another hack :(                
                data = self.runSQL('SELECT * FROM %s WHERE ID=%s' % ( self.db_table, del_ID ))
                columns_raw = self.runSQL('SHOW COLUMNS FROM %s' % ( self.db_table ))
                columns = [col[0] for col in columns_raw]
                
                if x[3] in [2,4]: # done and error
                    dir_from = "%s%s" % (self.rosetta_dl, cryptID)
                    dir_to   = "%sarchive/%s" % (self.rosetta_tmp[:-5], del_ID)
                    try:
                        handle_param = open("%s/DB.txt" % (dir_from), 'w')
                        for i in range(len(data)-1):
                            handle_param.write('%s\t%s\n' % (columns[i],str(data[0][i])))
                        handle_param.close()
                        
                        os.rename( dir_from, dir_to ) # copy directory
                        self.log("%s\t job %s: directory moved: %s -> %s\n" % ( datetime.now().strftime("%Y-%m-%d %H:%M:%S"), del_ID, dir_from, dir_to ) )
                        
                        # let's delete the zip file to save space:
                        # todo: why not keep *just* the zip file if it has everything else?
                        try:
                            os.remove( '%s/data_%s.zip' % (dir_to,del_ID) )
                        except:
                            pass
                    except Exception, e:
                        self.log("%s\n%s\t job %s: couldn't move directory: %s -> %s\n" % (traceback.format_exc(), datetime.now().strftime("%Y-%m-%d %H:%M:%S"), del_ID, dir_from, dir_to ) )
                        break
                 
                # Keep the data in the database but mark it as expired
                self.runSQL('UPDATE %s SET Expired=1 WHERE ID=%s' % (self.db_table, del_ID))
                self.log("%s\t job %s: marked as expired in database\n" % ( datetime.now().strftime("%Y-%m-%d %H:%M:%S"), del_ID ) )

    def configure(self):
        parameter = read_config_file()
                
        self.email_admin            = parameter["email_admin"]
        self.max_processes          = int(parameter["max_processes"])
        self.db_table               = parameter["db_table"]
        self.server_name            = parameter["server_name"]
        self.base_dir               = parameter["base_dir"]
        self.binDir                 = "%sbin" % self.base_dir
        self.dataDir                = "%sdata" % self.base_dir
        self.rosetta_tmp            = parameter["rosetta_tmp"]
        self.rosetta_ens_tmp        = parameter["rosetta_ens_tmp"]
        self.rosetta_dl             = parameter["rosetta_dl"]
        self.rosetta_error_dir      = parameter["rosetta_error_dir"]
        self.store_time             = parameter["store_time"]
        
        db_host                = parameter["db_host"]
        db_name                = parameter["db_name"]
        db_user                = parameter["db_user"]
        db_pw                  = parameter["db_pw"]
        db_port                = int(parameter["db_port"])
        db_socket              = parameter["db_socket"]
        db_numTries            = 32
        self.DBConnection      = rosettadb.RosettaDB(db_host, db_name, db_user, db_pw, db_port, db_socket, self.store_time, db_numTries)

        if self.server_name == 'albana.ucsf.edu':
            self.ntrials = 10        
            
    #############################################################################################
    # sendMail()                                                                                #
    # sendmail wrapper                                                                          #
    #############################################################################################
    
    def sendMail(self, mailTO, mailFROM, mailSUBJECT, mailTXT):
        MAIL = "/usr/sbin/sendmail"
    
        mssg = "To: %s\nFrom: %s\nReply-To: %s\nSubject: %s\n\n%s" % (mailTO, mailFROM, mailFROM, mailSUBJECT, mailTXT)
        # open a pipe to the mail program and
        # write the data to the pipe
        p = os.popen("%s -t" % MAIL, 'w')
        p.write(mssg)
        exitcode = p.close()
        if exitcode:
            return exitcode
        else:
            return 1

###############################################################################################
# Server maintenance functions
###############################################################################################      
        
    def dbrehash(self):
        # open connection to MySQL
        dbconnection = self.DBConnection
        
        results = self.runSQL("SELECT ID, hashkey FROM %s" % self.db_table)
                
        hashkeys = {}
        for simulation in results:
            hashkeys[simulation[0]] = simulation[1]
            newhash = dbconnection.generateHash(simulation[0], debug = True) # Change debug to False to enable updating 
            #Used for testing when the update query in turned off
            #if hashkeys[simulation[0]] == newhash:
            #    print("unchanged: %d changed from %s to %s." % (simulation[0], hashkeys[simulation[0]], simulation[1]))
            
        results = self.runSQL("SELECT ID, hashkey FROM %s" % self.db_table)
        
        for simulation in results:
            if hashkeys[simulation[0]] == simulation[1]:
                print("unchanged: Simulation %d hash remains as %s." % (simulation[0], simulation[1]))
            else:
                print("Key for simulation %d changed from %s to %s." % (simulation[0], hashkeys[simulation[0]], simulation[1]))
         
        
    
    def dbcheck(self):
        results = self.runSQL("SELECT ID, ProtocolParameters, task FROM %s" % self.db_table)
        for simulation in results:
            protoparams = pickle.loads((simulation[1]))
            task = simulation[2]
            if len(str(protoparams)) == 2 and task != "no_mutation":
                print("Job number %d (%s) is missing parameters." % (simulation[0], task))
    
    def dbdumpPDB(self, jobID):
        results = self.runSQL("SELECT PDBComplex, PDBComplexFile FROM %s WHERE ID = %d" % (self.db_table, jobID))
        if results:
            contents = results[0][0]
            filename = results[0][1]
            filename = os.path.join(os.getcwd(), filename)
            print(contents)
            print(filename)            
            self.pdb = pdb.PDB(contents.split('\n'))
            if not os.path.exists(filename):
                print("Writing file %s:" % filename)
                self.pdb.write(filename)
            else:
                print("The file %s already exists. The PDB in the database was not dumped out." % filename)
        else:
            print("Job %d could not be found." % jobID)

    
    
    def dbconvert(self):
        # if there were jobs running when the daemon crashed, see if they are still running, kill them and restart them
        results = self.runSQL("SELECT ID, task, PM_chain, PM_resid, PM_newres, PM_radius, ENS_temperature, ENS_num_designs_per_struct, ENS_segment_length, seqtol_parameter, ProtocolParameters FROM %s" % self.db_table)
        
        sqlupdates = []
        try:
            errors = []
            for simulation in results:
                id = simulation[0]
                update = False
                ProtocolParameters = {}
                Mutations = []
                
                task = simulation[1]
                #print("%d: %s" % (id, task))
                
                # Point Mutation / Multiple Point Mutations
                chain = simulation[2]
                resid = simulation[3]
                newres = simulation[4]
                radius = simulation[5]
                if chain and resid and newres and radius:
                    if task == "point_mutation" or task == "multiple_mutation":
                        list_chains = [ str(x.strip('\'')) for x in chain.split('-') ]
                        list_resids = [ int(x.strip('\'')) for x in resid.split('-') ]
                        list_newres = [ x.strip('\'') for x in newres.split('-') ]
                        list_radius = [ float(x.strip('\'')) for x in radius.split('-') ]
                        if len(list_chains) < 1 or not(len(list_chains) == len(list_resids) and len(list_chains) == len(list_newres) and len(list_chains) == len(list_radius)):
                            errors.append("This simulation is missing data: %s\n" % simulation)
                        for i in range(len(list_chains)):
                            Mutations.append((list_chains[i], list_resids[i], list_newres[i], list_radius[i]))
                        ProtocolParameters["Mutations"] = Mutations
                        update = True
                    else:
                        errors.append("This simulation has bad data set: %s\n" % simulation)
                
                # Ensemble design
                temperature = simulation[6]
                designsPerStruct = simulation[7]
                segmentLength = simulation[8]
                if temperature and designsPerStruct and segmentLength:
                    if task == "ensemble":
                        ProtocolParameters["Temperature"] = float(temperature)
                        ProtocolParameters["NumDesignsPerStruct"] = int(designsPerStruct)
                        ProtocolParameters["SegmentLength"] = int(segmentLength)
                        update = True
                    else:
                        errors.append("This simulation has bad data set: %s\n" % str(simulation))
                
                # Sequence tolerance
                seqtol_parameter = simulation[9]
                
                if seqtol_parameter:
                    if task == "sequence_tolerance":
                        seqtol_parameter = pickle.loads(seqtol_parameter)
                        
                        Designed = {}
                        chain1 = seqtol_parameter["seqtol_chain1"]
                        chain2 = seqtol_parameter["seqtol_chain2"]
                        Designed[chain1] = seqtol_parameter["seqtol_list_1"]
                        Designed[chain2] = seqtol_parameter["seqtol_list_2"]
                        for i in range(len(Designed[chain1])):
                            Designed[chain1][i] = int(Designed[chain1][i])
                        for i in range(len(Designed[chain2])):
                            Designed[chain2][i] = int(Designed[chain2][i])
                        if not Designed[chain1] and not Designed[chain2]:
                            errors.append("%d: There must be at least one designed residue." % id)
    
                        ProtocolParameters = {
                            "Partners"      :   [chain1, chain2],
                            "Designed"      :   Designed,
                            "Weights"       :   [float(seqtol_parameter["seqtol_weight_chain1"]), float(seqtol_parameter["seqtol_weight_chain2"]), float(seqtol_parameter["seqtol_weight_interface"])],
                        }
                        update = True
                        
                    elif task == "sequence_tolerance_SK":
                        seqtol_parameter = pickle.loads(seqtol_parameter)
                        if len(str(seqtol_parameter)) != 2:
                            errors.append("%d: Found seqtol data unexpectedly." % id)
                        #protoparams = pickle.loads(simulation[10])
                        #if len(str(protoparams)) == 2:
                        #    errors.append("%d: This simulation has no data. %s\n" % (id, protoparams))
                        #ProtocolParameters = protoparams
                        #update = True
                    else:
                        seqtol_parameter = pickle.loads(seqtol_parameter)
                        if len(str(seqtol_parameter)) != 2:
                            errors.append("%d: This simulation has bad data set: seqtol data exists %s, %d\n" % (id, str(seqtol_parameter), d))
                
                if task != "no_mutation" and task != "sequence_tolerance_SK" and not update:
                    protoparams = pickle.loads(simulation[10])
                    if len(str(seqtol_parameter)) == 2:
                        errors.append("%d: This simulation %s has no data. %s\n" % (id, task, protoparams))
                
                if update and len(str(pickle.loads(simulation[10]))) ==2:
                    ProtocolParameters = pickle.dumps(ProtocolParameters)
                    updatesql = 'UPDATE %s SET ProtocolParameters="%s" WHERE ID=%s' % (self.db_table, ProtocolParameters, simulation[0])
                    sqlupdates.append(updatesql)
                    if self.runSQL(updatesql) == None:
                        print("Update failed on record %d" % id)
                    
            #print(string.join(sqlupdates,"\n"))
            print(string.join(errors,"\n"))
                    
        except: # iteration over non-sequence, i.e. results is empty
            traceback.print_exc()
            pass

###############################################################################################
# Protocol-specific functions - start job, check files, end job                                                                                            #
###############################################################################################

    def StartMutations(self, ID, pdb_info, pdb_filename, mini, ensemble_size, params):                       
        # create rosetta run
        #todo: get binaries from RosettaBinaries
        binary = RosettaBinaries[mini]
        usingMini = binary["mini"]
        executable = "%s/%s" % (self.binDir, binary["backrub"])
        databaseDir = "%s/%s" % (self.dataDir, binary["database"])
        object_rosetta = rosettaplusplus.RosettaPlusPlus( ID, executable, databaseDir, self.rosetta_tmp, mini = usingMini)
        
        # store Rosetta object to list; this is not a copy since Python uses references
        self.list_RosettaPP.append(object_rosetta)
        
        # create working directory
        w_dir = object_rosetta.make_workingdir()
        self.log("%s\t mutation job preprocessing started in directory %s\n" % ( datetime.now().strftime("%Y-%m-%d %H:%M:%S"), w_dir) )
        
        # copy pdb data in object and get filename
        fn_pdb = object_rosetta.set_pdb(pdb_filename, pdb_info)
        # create mutations and define backrub residues
        dict_residues = {}   # contains the residues and their modes according to rosetta: { (chain, resID):["PIKAA","PHKL"] }
        backbone      = []   # residues to which backrub should be applied: [ (chain,resid), ... ]
        default       = ""
        rand_chain    = "A"
        # chains for classic
        chain_parameter = [] # ["-read_all_chains"]
        resid2type = object_rosetta.pdb.aa_resid2type()
        
        self.log("%s\t start_job_preprocessing() ID = %s\n" % ( datetime.now().strftime("%Y-%m-%d %H:%M:%S"), ID ) )
        
        task = params["task"] # hack (see above)
        
        if task == 'no_mutation': # no mutation, apply backrub to all residues
            default = "NATAA"
            residue_ids = object_rosetta.pdb.aa_resids()
                            
            # chains for classic
            chain_parameter.append("-read_all_chains")
            for chain in object_rosetta.pdb.chain_ids():
              chain_parameter.append("-chain")
              chain_parameter.append(str(chain))
            
            for res in residue_ids:
                x = [ res[0], res[1:].strip() ]
                if len(x) == 1:
                    backbone.append( ( "_", int(x[0].lstrip())) )
                else:
                  try:
                    if resid2type[res] != "C": # no backrub for cysteins to prevent S=S breaking
                      backbone.append( ( x[0], int(x[1].lstrip())) )
                  except KeyError: # this happens if "residue" is nucleotide
                    pass
                        
        elif task == 'point_mutation': # point mutation
                
            # oh this hurts a lot ... refactor theses classes and come up with a more elegant way here
            # example: 12 -> 'A  12' -> 'A   8' -> 8
            # get the neighbors one residues
            try:
                PM_chain = params["Mutations"][0][0]
                PM_resid = params["Mutations"][0][1]
                PM_newres = params["Mutations"][0][2]
                PM_radius = params["Mutations"][0][3]
            except:
                self.log("params='%s'\n%s" % (str(params), traceback.format_exc()))
                
            neighbor_list = object_rosetta.pdb.neighbors2( float(PM_radius), "%s%4.i" % (PM_chain, int(PM_resid)) )
            # set default: don't move other residues
            default = "NATRO"
                            
            # let surrounding residues move and apply backrub
            for residue in neighbor_list:
                pair_res = ( residue[0], int(residue[1:].lstrip()) )
                dict_residues[ pair_res ] = ["NATAA", ' ']
                try:
                  if resid2type[residue] != "C": # no backrub for cysteins to prevent S=S breaking
                    backbone.append( pair_res )
                except KeyError: # this happens if "residue" is nucleotide
                  pass
            
            # overwrite position where the mutation is
            dict_residues[ (PM_chain, int(PM_resid)) ] = [ "PIKAA", PM_newres ]
            if (PM_chain, int(PM_resid)) not in backbone:
                backbone.append((PM_chain, int(PM_resid)))    
            
            # chains for classic
            chain_parameter.append("-read_all_chains")
            if PM_chain in object_rosetta.pdb.chain_ids():
              chain_parameter.append("-chain")
              chain_parameter.append(str(PM_chain))
                
        elif task == 'multiple_mutation': # multiple point mutations    
            list_chains = [ m[0] for m in params["Mutations"] ]
            list_resids = [ m[1] for m in params["Mutations"] ]
            list_newres = [ m[2] for m in params["Mutations"] ]
            list_radius = [ m[3] for m in params["Mutations"] ]
            
            list_new_resid = []
            
            # chains for classic
            chains = list(set(list_chains))
                            
            chain_parameter.append("-read_all_chains") # makes sure backrub is applied to all chains
            for chain in chains:
              chain_parameter.append("-chain")
              chain_parameter.append(str(chain))
        
            for x in range(len(list_resids)):
                entry_list_resid = str(list_resids[x])
                list_new_resid.append( entry_list_resid )
            
                neighbor_list = object_rosetta.pdb.neighbors2( float(list_radius[x]), "%s%4.i" % (list_chains[x], list_resids[x]) ) ## this is not nice accessing pdb from outside the class tztztz!
                # set default: don't move other residues
                default = "NATRO"
                
                # let surrounding residues move and apply backrub
                for residue in neighbor_list:
                    pair_res = ( residue[0], int(residue[1:].lstrip()) )
                    dict_residues[ pair_res ] = ["NATAA", ' ']
                    # add residues to backrub list
                    if pair_res not in backbone: # (check to avoid double entries) 
                      try:
                        if resid2type[residue] != "C": # and (no backrub for cysteins to prevent S=S breaking)
                          backbone.append( pair_res )
                      except KeyError: # this occurs when the "residue" is a nucleotide
                        pass
                
                
            for y in range(len(list_resids)):
                # overwrite position where the mutation is
                dict_residues[ (list_chains[y], int(list_resids[y])) ] = [ "PIKAA", list_newres[y] ]
                if (list_chains[y], int(list_resids[y])) not in backbone:
                    backbone.append((list_chains[y], int(entry_list_resid)))
        
        # create resfile and get filename
        fn_resfile = object_rosetta.write_resfile( default, dict_residues, backbone, None)
        # run rosetta
        r_command = ''
        
        if usingMini:
            object_rosetta.run_args( [ "-database", databaseDir, 
                                       "-s", fn_pdb, 
                                       "-ignore_unrecognized_res", 
                                       "-resfile", fn_resfile, 
                                       "-nstruct",  ensemble_size, 
                                       "-backrub:ntrials", str(self.ntrials),
                                       "-pivot_atoms", "CA" ] )
            time.sleep(1)
            
            r_command = object_rosetta.command
        else:
            object_rosetta.run_args( ["-paths","paths.txt",
                                      "-pose1","-backrub_mc",
                                      "-s", fn_pdb ] + chain_parameter + ["-series","BR",
                                      "-protein", fn_pdb.split('.')[0],
                                      "-resfile", fn_resfile, 
                                      "-bond_angle_params","bond_angle_amber",
                                      "-use_pdb_numbering", 
                                      "-ex1","-ex2",
                                      "-extrachi_cutoff","0",
                                      "-nstruct",  ensemble_size,
                                      "-ntrials", str(self.ntrials),
                                      "-norepack_disulf", "-find_disulf", ] )
            time.sleep(1)
            r_command = object_rosetta.command
        
        pid = object_rosetta.get_pid()
        self.log("%s %s: mutation job started with pid: %s\n" % ( datetime.now().strftime("%Y-%m-%d %H:%M:%S"), ID, pid ) )
        self.log("%s %s: %s\n" % ( datetime.now().strftime("%Y-%m-%d %H:%M:%S"), ID, r_command ) )
        return pid
        
    def CheckMutations(self, r_object, ensembleSize, pdb_id, job_id, task, binaryName):
        initial_score = 'xxx'
        low_scores  = []
        last_scores = []
        
        binary = RosettaBinaries[binaryName]
        workingdir = r_object.workingdir
        usingMini = r_object.mini
        try:
            if usingMini:
                databaseDir = "%s/%s" % (self.dataDir, binary["database"])              
                postprocessingBinary = "%s/%s" % (self.binDir, binary["postprocessing"])              
                analysis = AnalyzeMini(filename="%s/stdout_%s.dat" % ( workingdir, job_id) )
                if not analysis.analyze(outfile="%s/scores_detailed.txt" % workingdir, outfile2="%s/scores_overall.txt" % workingdir):
                    self.log("%s\t\t check_files() ID = %s : individual scores could not be created\n" % ( datetime.now().strftime("%Y-%m-%d %H:%M:%S"), job_id ) )
                if not analysis.calculate_residue_scores( self.base_dir, postprocessingBinary, databaseDir, workingdir, "%s/scores_residues.txt" % workingdir ):
                    self.log("%s\t\t check_files() ID = %s : residue energies could not be calculated\n" % ( datetime.now().strftime("%Y-%m-%d %H:%M:%S"), job_id ) )
                        
                x = 1
                while x <= ensembleSize:
                    last_file = '%s/%s_%04.i_last.pdb' % (workingdir, pdb_id, x )
                    low_file  = '%s/%s_%04.i_low.pdb'  % (workingdir, pdb_id, x )
                    if os.path.exists( last_file ): 
                        os.remove( last_file )
                    if not os.path.exists( low_file ):
                        return False
                
                    # last_scores.append(self._get_score_from_pdb_file(last_file))
                    # low_scores.append( self._get_score_from_pdb_file(low_file))
                     
                    x += 1 # IMPORTANT because of while loop
                
            else:
                initial_file = '%s/BR%s_initial.pdb' % ( workingdir, pdb_id )
                cmd_stdout = os.popen("tail -n 1 %s" % initial_file).readline().split()
                if cmd_stdout[0] == 'SCORE':
                    initial_score = cmd_stdout[1]
              
                analysis = AnalyzeClassic(filename="%s/stdout_%s.dat" % ( workingdir, job_id) )
                if not analysis.analyze(outfile="%s/scores_detailed.txt" % workingdir, outfile2="%s/scores_overall.txt" % workingdir):
                    self.log("%s\t\t check_files() ID = %s : individual scores could not be created\n" % ( datetime.now().strftime("%Y-%m-%d %H:%M:%S"), job_id ) )
                
                x = 1
                while x <= ensembleSize:
                    last_file = '%s/BR%slast_%04.i.pdb' % (workingdir, pdb_id, x )
                    low_file  = '%s/BR%slow_%04.i.pdb' % (workingdir, pdb_id, x ) 
                    if os.path.exists( last_file ): 
                        os.remove( last_file )
                    if not os.path.exists( low_file ): 
                        return False
                                    
                    # last_scores.append(self._get_score_from_pdb_file(last_file))
                    # low_scores.append(self._get_score_from_pdb_file(low_file))
                    
                    x += 1 # very important!!!!! :-/
                
                # output scores
                # handle_out = open( '%s/scores_overall.txt' % workingdir , 'w')
                # handle_out.write( 'structure\tscore\n' )
                # handle_out.write( '#initial:\t%s\n' % initial_score )
                # i = 0
                # while i < len(low_scores):
                #     a = i + 1
                #     handle_out.write( '%04.i\t%s\n' % ( a , low_scores[i]) ) #last_scores[i]
                #     i += 1
                # handle_out.write('\n')
                # handle_out.close()
                
        except:
            self.log("%s\t\t check_files() ID = %s, task = %s : failed\n" % ( datetime.now().strftime("%Y-%m-%d %H:%M:%S"), job_id, task ) )
            self.log("Exception: %s\n" % traceback.format_exc())
            return False
        
        return True
    
    def EndMutations(self, rosetta_object, pdb_id, ensembleSize, state, ID):
        pass

    def StartEnsemble(self, ID, pdb_info, pdb_filename, mini, ensemble_size, params):                
                
        ENS_obj = rosetta_rdc.Rosetta_RDC( ID=ID, tempdir = self.rosetta_ens_tmp )
        ENS_obj.make_workingdir()
        ENS_obj.set_pdb(pdb_filename, pdb_info)
        
        # Parameters
        ENS_segment_length = params["SegmentLength"]
        ENS_temperature = params["Temperature"]
        ENS_num_designs_per_struct = params["NumDesignsPerStruct"]
        
        # starting_pdb_file, backrub_num_structs, backrub_max_segment_length, backrub_num_steps, backrub_temp, num_designs_per_struct
        cmd_args = [ self.base_dir + "daemon/ensemble_design/ensemble_design.py", self.base_dir + "bin", pdb_filename, ensemble_size, ENS_segment_length, self.ntrials, ENS_temperature, ENS_num_designs_per_struct, '--verbose', '2' ] 
                        
        ENS_obj.run_args(cmd_args)
        time.sleep(1)
        pid = ENS_obj.get_pid()
        
        # store rosetta object to list; this is not a copy !
        self.list_RosettaPP.append(ENS_obj)
    
        return pid
    
    def CheckEnsemble(self, r_object, ensembleSize, pdb_id, job_id, task, binaryName):
        return True

    def EndEnsemble(self, rosetta_object, pdb_id, ensembleSize, state, ID):
        state["keep_output"] = True
        # remove directories
        #shutil.rmtree( rosetta_object.workingdir + "/designs" )
        #shutil.rmtree( rosetta_object.workingdir + "/backrubs" )
        shutil.rmtree( rosetta_object.workingdir + "/repack" )
        # # remove individual files
        # os.remove( rosetta_object.workingdir + "/stdout_%s.dat" % ( ID ) )
        os.remove( rosetta_object.workingdir + "/%s_br.res" % ( pdb_id ) )
        os.remove( rosetta_object.workingdir + "/%s_des.res" % ( pdb_id ) )
        os.remove( rosetta_object.workingdir + "/backrub.log" )
        # os.remove( rosetta_object.workingdir + "/core.txt" )
        os.remove( rosetta_object.workingdir + "/designed_pdbs.lst" )
        os.remove( rosetta_object.workingdir + "/ensemble.lst" )
        #os.remove( rosetta_object.workingdir + "/starting_pdb.lst" )
        
    ##################################### end of sendMail() ######################################


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

    def recordErrorInJob(self, clusterjob, errormsg):
        jobID = clusterjob.jobID
        clusterjob.error = errormsg
        clusterjob.failed = True
        
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
        
        while True:
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
                tracebackstr = "%s\n%s" % (str(e), traceback.print_exc()) 
                self.recordErrorInJob(clusterjob, "Failed. %s" % tracebackstr)
                self.end_job(clusterjob)
                            
        # Remove completed jobs from the list
        for cj in completedJobs:
            self.runningJobs.remove(cj)
            
    def startNewJobs(self):
        # Start more jobs
        newclusterjob = None
        if len(self.runningJobs) < self.MaxClusterJobs:            
            # get all jobs in queue
            #todo change seqtol_parameter to ProtocolParameters after webserver update
            data = self.runSQL("SELECT ID,Date,Status,PDBComplex,PDBComplexFile,Mini,EnsembleSize,task,seqtol_parameter,cryptID FROM %s WHERE Status=0 AND (%s) ORDER BY Date" % (self.db_table, self.SQLJobSelectString))
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
                    self.recordErrorInJob(newclusterjob, "Error starting job.\n%s\n%s" % (traceback.format_exc(), e))
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
            
            if False: #todo True: # todo self.diffcounter >= CLUSTER_printstatusperiod:
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
        except:
            self.recordErrorInJob(clusterjob, "Error archiving files")
        
        try:
            self.removeClusterTempDir(clusterjob)
        except:
            self.recordErrorInJob(clusterjob, "Error removing temporary directory on the cluster")
            
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
            
        try:
            ID = clusterjob.jobID                        
            
            # move the data to a webserver accessible directory 
            result_dir = self.moveFilesOnJobCompletion(clusterjob)
            
            # remember directory
            current_dir = os.getcwd()
            os.chdir(result_dir)
            
            # let's remove all empty files to not confuse the user
            self.exec_cmd('find . -size 0 -exec rm {} \";\"', result_dir)
            
            # store all files also in a zip file, to make it easier accessible
            if task == 'sequence_tolerance':
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
        except Exception, e:
            self.log("%s\t error: end_job() ID = %s - error moving files\n*******************************\n%s*******************************\n" % ( datetime.now().strftime("%Y-%m-%d %H:%M:%S"), ID, traceback.format_exc() ) )
            self.runSQL('UPDATE %s SET Errors="Error archiving data", Status=4 WHERE ID=%s' % ( self.db_table, ID ))
            status = 4
            clusterjob.error = "Error archiving data"
    
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



class BackendProtocols(WebserverProtocols):
      
    def __init__(self, rosettaDaemon):
        super(BackendProtocols, self).__init__()
        
        protocolGroups = self.protocolGroups
        protocols = self.protocols
        
        # Add backend specific information
        removelist = []
        for p in protocols:
            if p.dbname == "point_mutation":
                p.setBackendFunctions(rosettaDaemon.StartMutations, rosettaDaemon.CheckMutations, rosettaDaemon.EndMutations)
            elif p.dbname == "multiple_mutation":
                p.setBackendFunctions(rosettaDaemon.StartMutations, rosettaDaemon.CheckMutations, rosettaDaemon.EndMutations)
            elif p.dbname == "no_mutation":
                p.setBackendFunctions(rosettaDaemon.StartMutations, rosettaDaemon.CheckMutations, rosettaDaemon.EndMutations)
            elif p.dbname == "ensemble":
                p.setBackendFunctions(rosettaDaemon.StartEnsemble, rosettaDaemon.CheckEnsemble, rosettaDaemon.EndEnsemble)
            else:
                removelist.append(p)
        
        # Prune the protocols list
        for rp in removelist:
            protocols.remove(rp)

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
                
if __name__ == "__main__":
    temppath = os.path.join(server_root, 'temp')
             
    if len(sys.argv) > 1:
        if len(sys.argv) == 2:
            daemon = RosettaDaemon(os.path.join(temppath, 'running.log'), os.path.join(temppath, 'running.log'))
            if 'start' == sys.argv[1]:
                daemon.start()
            elif 'stop' == sys.argv[1]:
                daemon.stop()
            elif 'restart' == sys.argv[1]:
                daemon.restart()
        elif 'db' == sys.argv[1]:
            #todo: separate out the db functions from RosettaDaemon
            daemon = RosettaDaemon(os.path.join(temppath, 'dbrunning.log'), os.path.join(temppath, 'dbrunning.log'))
            if 'rehash' == sys.argv[2]:
                daemon.dbrehash()
            elif 'convert' == sys.argv[2]:
                daemon.dbconvert()
            elif 'check' == sys.argv[2]:
                daemon.dbcheck()
            elif ('dumppdb' == sys.argv[2]) and sys.argv[3]:
                daemon.dbdumpPDB(int(sys.argv[3]))
            else:
                print "Unknown command to db"
                sys.exit(2)
            sys.exit(0)
        elif 'cluster' == sys.argv[1]:
            #daemon = ClusterDaemon(os.path.join(temppath, 'qb3running.log'), os.path.join(temppath, 'qb3running.log'))
            daemon = ClusterDaemon('/dev/stdout','/dev/stderr')
            if 'start' == sys.argv[2]:
                daemon.start()
            elif 'stop' == sys.argv[2]:
                daemon.stop()
            elif 'restart' == sys.argv[2]:
                daemon.restart()
            else:
                print "Unknown command to cluster"
                sys.exit(2)
            sys.exit(0)
        elif 'test' == sys.argv[1]:
            UserID = 106
            if 'db' == sys.argv[2] and sys.argv[3]:
                UserID = 25
                Email = "test@bob.co"
                ProtocolParameters = {}
                inputDirectory = '/home/oconchus/'
                pdb_filename = '3QDO.pdb'
                output_handle = open(os.path.join(inputDirectory, pdb_filename), 'r')
                pdbfile = output_handle.read()
                output_handle.close()
                IP = '127.0.0.1'
                hostname = 'albana'
                nos = '10'
                keep_output = 1
                
                print("Adding a new sequence tolerance (SK) job:")
                JobName = "3QDO (Job 1957)"
                mini = 'seqtolJMB'
                modus = "sequence_tolerance_SK"
                ProtocolParameters = {
                    "kT"                : 0.228,
                    "Partners"          : ["A", "B"],
                    "Weights"           : [0.4, 0.4, 0.4, 1.0],
                    "Premutated"        : {"A": {}, "B" : {}},
                    "Designed"          : {"A": {}, "B" : {203 : True, 204 : True, 205 : True, 206 : True, 207 : True, 208 : True}}
                }
                ProtocolParameters = pickle.dumps(ProtocolParameters)
                
                try: 
                    import random
                    import md5
                    #daemon.runSQL("LOCK TABLES %s WRITE, Users READ" % daemon.db_table)
                    #todo change seqtol_parameter to ProtocolParameters after webserver update

                    db_host                = "localhost"
                    db_name                = "rosettaweb"
                    db_user                = "rosettaweb"
                    db_pw                  = sys.argv[3]
                    db_port                = 3306
                    db_socket              = "/var/lib/mysql/mysql.sock"
                    db_numTries            = 32
                    DBConnection = rosettadb.RosettaDB(db_host, db_name, db_user, db_pw, db_port, db_socket, 60, db_numTries)
                    
                    lockstr = "backrub WRITE, Users READ"         
                    DBConnection.execQuery("LOCK TABLES %s" % lockstr)
                    try:
                        query = """INSERT INTO backrub ( Status, cryptID, Date,hashkey,BackrubServer,Email,UserID,Notes, PDBComplex,PDBComplexFile,IPAddress,Host,Mini,EnsembleSize,KeepOutput,task, ProtocolParameters) 
                                    VALUES (2, "shanetest", NOW(), "0", "albana", "shaneoconnor@ucsf.edu","%d","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s")""" % (UserID, JobName, pdbfile, pdb_filename, IP, hostname, mini, nos, keep_output, modus, ProtocolParameters)           
                        result = DBConnection.execQuery(query)
                        query = """SELECT ID FROM backrub WHERE UserID="%s" AND Notes="%s" ORDER BY Date DESC""" % (UserID , JobName)
                        result = DBConnection.execQuery(query)
                        ID = result[0][0]
                        print("\tTest job created with PDB %s and ID #%s" % (pdb_filename, str(ID)))
                    except Exception, e: 
                        print("Error.\n%s\n%s" % (e, traceback.format_exc()))
                        DBConnection.execQuery("UNLOCK TABLES")
                        sys.exit(1)
                    DBConnection.execQuery("UNLOCK TABLES")

                except Exception, e:
                    print("Error.\n%s" % e)
                    sys.exit(1)
                print("Success")
                sys.exit(0)
                    # success
            
            daemon = ClusterDaemon(os.path.join(temppath, 'testrunning.log'), os.path.join(temppath, 'testrunning.log'))    
            if 'remove' == sys.argv[2] and sys.argv[3]: 
                try: 
                    print("Removing job %s:" % sys.argv[3])
                    jobID = int(sys.argv[3])
                    sql = "SELECT ID, Notes FROM %s WHERE ID=%d AND UserID=%d" % (daemon.db_table, jobID, UserID)
                    results = daemon.runSQL(sql)
                    if not results:
                        print("Job not found.")
                        sys.exit(2)
                    print("Deleting jobs: %s" % results)
                    time.sleep(5)    
                    sql = "DELETE FROM %s WHERE ID=%d AND UserID=%d" % (daemon.db_table, jobID, UserID)    
                    results = daemon.runSQL(sql)
                    if results:
                        print(results)
                    print("\tSuccessful removal.")
                except Exception, e:
                    print("\tError: %s\n%s" % (str(e), traceback.print_exc())) 
                    print("\tFailed.")
                    sys.exit(2)
            
            if 'add' == sys.argv[2]:
                JobName = "Cluster test"
                inputDirectory = '/home/oconchus/clustertest110428/rosettawebclustertest/backrub/daemon/cluster/input'
                pdb_filename = '1MDY_mod.pdb'
                output_handle = open(os.path.join(inputDirectory, pdb_filename), 'r')
                pdbfile = output_handle.read()
                output_handle.close()
                IP = '127.0.0.1'
                hostname = 'albana'
                keep_output = 1
                nos = None
                
                ProtocolParameters = {}
                if 'cm1' == sys.argv[3]:
                    pdb_filename = '3QDO.pdb'
                    output_handle = open(os.path.join(inputDirectory, pdb_filename), 'r')
                    pdbfile = output_handle.read()
                    output_handle.close()
                    nos = '100'
                
                    print("Adding a new sequence tolerance (SK) job:")
                    JobName = "3QDO (Job 1957)"
                    mini = 'seqtolJMB'
                    modus = "sequence_tolerance_SK"
                    ProtocolParameters = {
                        "kT"                : 0.228,
                        "Partners"          : ["A", "B"],
                        "Weights"           : [0.4, 0.4, 0.4, 1.0],
                        "Premutated"        : {},
                        "Designed"          : {"B" : [203, 204, 205, 206, 207, 208]}
                    }
                if 'cm2' == sys.argv[3]:
                    pdb_filename = '3QE1.pdb'
                    output_handle = open(os.path.join(inputDirectory, pdb_filename), 'r')
                    pdbfile = output_handle.read()
                    output_handle.close()
                    nos = '100'
                
                    print("Adding a new sequence tolerance (SK) job:")
                    JobName = "3QE1 (Job 1958)"
                    mini = 'seqtolJMB'
                    modus = "sequence_tolerance_SK"
                    ProtocolParameters = {
                        "kT"                : 0.228,
                        "Partners"          : ["A", "B"],
                        "Weights"           : [0.4, 0.4, 0.4, 1.0],
                        "Premutated"        : {},
                        "Designed"          : {"B" : [201, 202, 203, 204, 205, 206]}
                    }
                if 'sk' == sys.argv[3]:
                    print("Adding a new sequence tolerance (SK) job:")
                    mini = 'seqtolJMB'
                    modus = "sequence_tolerance_SK"
                    nos = '2'
                    ProtocolParameters = {
                        "kT"                : 0.228,
                        "Partners"          : ["A", "B"],
                        "Weights"           : [0.4, 0.4, 0.4, 1.0],
                        "Premutated"        : {"A" : {102 : "A"}},
                        "Designed"          : {"A" : [103, 104]}
                    }
                elif 'hk' == sys.argv[3]:
                    pdb_filename = 'hktest.pdb'
                    output_handle = open(os.path.join(inputDirectory, pdb_filename), 'r')
                    pdbfile = output_handle.read()
                    output_handle.close()
                    nos = '2'
                    
                    print("Adding a new sequence tolerance (HK) job:")
                    mini = 'seqtolHK'
                    modus = "sequence_tolerance"
                    ProtocolParameters = {
                        "Partners"          : ["A", "B"],
                        "Designed"          : {"A" : [], "B" : [145, 147, 148, 150, 152, 153]}, # todo: Test when "A" not defined
                    }
                ProtocolParameters = pickle.dumps(ProtocolParameters)
                
                try: 
                    import random
                    import md5
                    print(UserID)
                    #daemon.runSQL("LOCK TABLES %s WRITE, Users READ" % daemon.db_table)
                    #todo change seqtol_parameter to ProtocolParameters after webserver update
                    daemon.runSQL("""INSERT INTO %s ( Date,hashkey,BackrubServer,Email,UserID,Notes, PDBComplex,PDBComplexFile,IPAddress,Host,Mini,EnsembleSize,KeepOutput,task, seqtol_parameter) 
                                VALUES (NOW(), "0", "albana", "shaneoconnor@ucsf.edu","%d","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s")""" % (daemon.db_table, UserID, JobName, pdbfile, pdb_filename, IP, hostname, mini, nos, keep_output, modus, ProtocolParameters))           
                    result = daemon.runSQL("""SELECT ID FROM backrub WHERE UserID="%s" AND Notes="%s" ORDER BY Date DESC""" % (UserID , JobName))
                    ID = result[0][0]
                    print("\tTest job created with PDB %s and ID #%s" % (pdb_filename, str(ID)))
                    # create a unique key as name for directories from the ID, for the case we need to hide the results
                    # do not just use the ID but also a random sequence
                    tgb = str(ID) + 'flo' + string.join(random.sample('0123456789abcdefghijklmnopqrstuvwxyz0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789', 6), '') #feel free to subsitute your own name here ;)
                    cryptID = md5.new(tgb.encode('utf-8')).hexdigest()
                    return_vals = (cryptID, "new")
                    sql = 'UPDATE backrub SET cryptID="%s" WHERE ID="%s"' % (cryptID, ID)
                    result = daemon.runSQL(sql)
                    # success
                    
                    #livejobs = daemon.runSQL("SELECT Date,hashkey,Email,UserID,Notes, PDBComplex,PDBComplexFile,IPAddress,Host,Mini,EnsembleSize,KeepOutput,task, seqtol_parameter FROM %s WHERE UserID=%d and (%s) ORDER BY Date" % (daemon.db_table, UserID, daemon.SQLJobSelectString))
                    livejobs = daemon.runSQL("SELECT ID, Status, Notes FROM %s WHERE UserID=%d and (%s) ORDER BY Date" % (daemon.db_table, UserID, daemon.SQLJobSelectString))
                    #daemon.runSQL("UNLOCK TABLES")
                    print(livejobs)
                
                    print("Success.")
                except Exception, e:
                    #daemon.runSQL("UNLOCK TABLES")
                    print("\tError: %s\n%s" % (str(e), traceback.print_exc())) 
                    print("Failed.")
                    sys.exit(2)
            sys.exit(0)
        
    print "usage: %s start|stop|restart|cluster start|cluster stop|cluster restart|db check|db rehash|db convert|test add [sk|hk]|test remove <id>" % sys.argv[0]
    sys.exit(2)

