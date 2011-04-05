#!/usr/bin/python2.4

import os
import sys
sys.path.insert(0, "../common/")
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
from daemon import Daemon
from datetime import datetime
from analyze_mini import AnalyzeMini
from analyze_classic import AnalyzeClassic
from rosettahelper import RosettaError
from rosettahelper import get_files
from rosettahelper import grep
from RosettaProtocols import *
from rbutils import *

cwd = str(os.getcwd())


class RosettaDaemon(Daemon):
    """This class controls the rosetta simulation"""
    
    # those are set by configure(self, filename_config)
    email_admin       = ''  # server administrators email adderss
    max_processes     = ''  # maximal number of processes that can be run at a time
    db_table          = ''
    server_name       = ''
    base_dir          = ''
    rosetta_tmp       = ''  
    rosetta_ens_tmp   = ''
    rosetta_dl        = ''  # webserver accessible directory
    rosetta_error_dir = ''  # directory were failed runs should be stored
    store_time        = ''  # how long are we going to store the data
    store_time_guest  = '30'  # how long are we going to store the data for guest users
    logfile           = ''
    ntrials           = 10000 # THIS SHOULD BE 10000
    logSQL            = True
    email_text_error = """Dear %s,

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

    protocolGroups = None
    protocols = None

    def __init__(self, pid, stdout, stderr):
        super(RosettaDaemon, self).__init__(pid, stdout = stdout, stderr = stderr)
        beProtocols = BackendProtocols(self)
        self.protocolGroups, self.protocols = beProtocols.getProtocols()


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
        self.configure()
        
        # logfile
        self.logfile = self.rosetta_tmp + "RosettaDaemon.log"
        self.log("%s\tstarted\n" % datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        
        # if there were jobs running when the daemon crashed, see if they are still running, kill them and restart them
        results = self.runSQL("SELECT ID, status, pid FROM %s WHERE status=1 ORDER BY Date" % self.db_table)
        try:
            for simulation in results:
                if os.path.exists("/proc/%s" % simulation[2]): # checks if process is running
                    if self.kill_process(simulation[2]): # checks if process was killed
                        self.runSQL("UPDATE %s SET status=0 WHERE ID=%s" % (self.db_table, simulation[0]))
                    else:
                        self.log("%s\t process not killed: ID %s PID %s\n" % (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), simulation[0], simulation[2]) )
                else:
                    self.runSQL("UPDATE %s SET status=0 WHERE ID=%s" % (self.db_table, simulation[0]))
        except TypeError: # iteration over non-sequence, i.e. results is empty
            pass
        
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
                    self.list_RosettaPP.remove(rosetta_object)
                    res = self.runSQL('SELECT Errors FROM %s WHERE ID=%s' % (self.db_table, ID))
                    if res[0][0] != '' and res[0][0] != None:
                        self.runSQL('UPDATE %s SET status=4, EndDate=NOW() WHERE ID=%s' % ( self.db_table, ID ))
                    elif error != '':
                        self.runSQL('UPDATE %s SET status=4, Errors=%s, EndDate=NOW() WHERE ID=%s' % ( self.db_table,error,ID ))
                    else:
                        self.runSQL('UPDATE %s SET status=2, EndDate=NOW() WHERE ID=%s' % ( self.db_table, ID ))
                    
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
                self.runSQL("LOCK TABLES %s WRITE, Users READ" % self.db_table)
                
                # get all jobs in queue                            vvv 0
                data = self.runSQL("SELECT ID,Date,status,task FROM %s WHERE status=0 ORDER BY Date" % self.db_table)
                try:
                    if len(data) == 0:
                        self.runSQL("UNLOCK TABLES")
                        time.sleep(10) # wait 10 seconds if there's no job in queue
                        continue
                    else:
                        ID = None
                        for i in range(0,len(data)):
                            # if this is a sequence_tolerance job, but the limit is already being processed
                            if (data[i][3] == 'sequence_tolerance' or data[i][3] == 'sequence_tolerance_SK') and self.running_S >= self.MaxSeqTolJobsRunning: 
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
                                    self.runSQL("UPDATE %s SET status=1, StartDate=NOW(), pid=%s WHERE ID=%s" % ( self.db_table, pid, ID ))
                                    break

                        # don't forget to unlock the tables!
                        self.runSQL("UNLOCK TABLES")
                        
                        time.sleep(3) # wait 3 seconds after a job was started
                except Exception, e:
                    self.log("%s\t error: self.run()\n%s\n\n" % (datetime.now().strftime("%Y-%m-%d %H:%M:%S"),traceback.format_exc()) )
                    self.runSQL('UPDATE %s SET Errors="Start", Status=4 WHERE ID=%s' % ( self.db_table, ID ))                  
                    time.sleep(10)
            else:
                time.sleep(30)  # wait 5 seconds if max number of jobs is running


    # split this one up in individual functions at some point
    def start_job(self, ID, pdb_info, pdb_filename, mini, ensemble_size, task, ProtocolParameters):
        
        pid = None
        try:
            self.log("%s\t start new job ID = %s, mini = %s, %s \n" % ( datetime.now().strftime("%Y-%m-%d %H:%M:%S"), ID, mini, task) )
            params = pickle.loads(ProtocolParameters)            
            params["task"] = task # This is a hack for the mutations protocols. Remove when their functions are separated out            
            for p in self.protocols:
                if p.dbname == task:
                    return p.startFunction(ID, pdb_info, pdb_filename, mini, ensemble_size, params)
          
        except Exception, e: 
            self.log("%s\t error: start_job() ID = %s\n%s\n\n" % ( datetime.now().strftime("%Y-%m-%d %H:%M:%S"), ID, traceback.format_exc() ) )
            
        return pid

    def check_files(self, r_object, ensembleSize, pdb_id, job_id, task):
        """checks whether all pdb files were created
           sometimes Rosetta classic crashes at the end, but the results are ok
        """
        # This function takes the last-files into account... and deletes them! We don't need them!        
        for p in self.protocols:
            if p.dbname == task:
                return p.checkFunction(r_object, ensembleSize, pdb_id, job_id, task)
        
        if retval:
            self.log("%s\t\t check_files() ID = %s, task = %s : all files successfully created\n" % ( datetime.now().strftime("%Y-%m-%d %H:%M:%S"), job_id, task ) )
            return True
            
    def runSQL(self, query):
        """ This function should be the only place in this class which executes SQL.
            Previously, bugs were introduced by copy and pasting and executing the wrong SQL commands (stored as strings in copy and pasted variables).
            Using this function and passing the string in reduces the likelihood of these errors.
            It also allows us to log all executed SQL here if we wish.""" 
        if self.logSQL:
            self.log("SQL: %s\n" % query)
        return self.DBConnection.execQuery(query)
        
    def end_job(self, rosetta_object):
        
        ID       = int( rosetta_object.get_ID() )
                        
        data = self.runSQL("SELECT u.Email,u.FirstName,b.KeepOutput,b.cryptID,b.task,b.PDBComplexFile,b.EnsembleSize FROM Users AS u JOIN %s AS b on (u.ID=b.UserID) WHERE b.ID=%s" % ( self.db_table, ID ))
        cryptID      = data[0][3]
        task         = data[0][4]
        pdb_id       = data[0][5].split('.')[0]
        ensembleSize = data[0][6]
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
            if not self.check_files(rosetta_object, ensembleSize, pdb_id, ID, task):
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
        if task == 'sequence_tolerance':
            self.exec_cmd("zip data_%s *.pdb seqtol_*_stdout.txt freq_*.txt *.resfiles tolerance* specificity*" % (ID), result_dir)
        #todo: Which files go into a zipfile?
        else:            
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
        
        if error == '':
            mailTXT = self.email_text_success % (user_name, self.server_name, cryptID, self.server_name, cryptID, ID, self.server_name, cryptID, self.store_time) 
        else:
            mailTXT = self.email_text_error % (user_name, self.server_name, cryptID)
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
        self.MaxSeqTolJobsRunning   = 3
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
        self.configure()
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
        self.configure()

        results = self.runSQL("SELECT ID, ProtocolParameters, task FROM %s" % self.db_table)
        for simulation in results:
            protoparams = pickle.loads((simulation[1]))
            task = simulation[2]
            if len(str(protoparams)) == 2 and task != "no_mutation":
                print("Job number %d (%s) is missing parameters." % (simulation[0], task))
    
    def dbconvert(self):
        # if there were jobs running when the daemon crashed, see if they are still running, kill them and restart them
        self.configure()
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
        fn_resfile = object_rosetta.write_resfile( default, dict_residues, backbone )
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
        
    def CheckMutations(self, r_object, ensembleSize, pdb_id, job_id, task):
        initial_score = 'xxx'
        low_scores  = []
        last_scores = []
        
        workingdir = r_object.workingdir
        mini = r_object.mini
        
        try:
            if mini:
                databaseDir = "%s/%s" % (self.dataDir, binary["mini"]["database"])              
                postprocessingBinary = "%s/%s" % (self.binDir, binary["mini"]["postprocessing"])              
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
    
    def CheckEnsemble(self, r_object, ensembleSize, pdb_id, job_id, task):
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
                    
    def StartSequenceToleranceHK(self, ID, pdb_info, pdb_filename, mini, ensemble_size, params):
    
        # let's use RosettaRDC since it can run an external script
        SEQTOL_obj = rosetta_rdc.Rosetta_RDC( ID=ID, tempdir = self.rosetta_ens_tmp )
        SEQTOL_obj.make_workingdir()
        SEQTOL_obj.set_pdb(pdb_filename, pdb_info)
    
        scriptname = 'daemon/rosettaseqtol_classic2.py'
        radius = 5.0 #todo: Set this in the constants file instead
        
    
        cmd_args = [ self.base_dir + scriptname, 
                     ID, pdb_filename, ensemble_size, 
                     radius, ]
                                
        chain1 = params["Partners"][0]
        chain2 = params["Partners"][1]
        cmd_args.append(chain1)
        cmd_args.extend(params["Designed"][chain1])
        cmd_args.append(chain2)
        cmd_args.extend(params["Designed"][chain2])
        
        print string.join([str(arg) for arg in cmd_args])
        
        SEQTOL_obj.run_args(cmd_args)
        time.sleep(1)
        pid = SEQTOL_obj.get_pid()
        # store rosetta object to list; this is not a copy !
        self.list_RosettaPP.append(SEQTOL_obj)
        
        self.running_S += 1
        
        return pid

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

    def CheckSequenceTolerance(self, r_object, ensembleSize, pdb_id, job_id, task):
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
                
    def StartSequenceToleranceSK(self, ID, pdb_info, pdb_filename, mini, ensemble_size, params):
    
        # let's use RosettaRDC since it can run an external script
        SEQTOL_obj = rosetta_rdc.Rosetta_RDC( ID=ID, tempdir = self.rosetta_ens_tmp )
        SEQTOL_obj.make_workingdir()
        SEQTOL_obj.set_pdb(pdb_filename, pdb_info)
        
        scriptname = 'daemon/rosettaseqtol.py'
        radius = 10.0  #todo: Set this in the constants file instead
        
        cmd_args = [ self.base_dir + scriptname, 
                     ID, pdb_filename, ensemble_size, 
                     radius, ]
    
        # See rosettaseqtol.py for a description of the command-line format.
        
        # todo: We deserialize the parameter here and then turn it into a command line only to read it back into a structure again on the other side
        #       instead, we could just save the serialized parameters and load it back in which would save a lot of trouble
        #       The downside to this is that it would still be handy to have a command line interface to test the script - we could write a textual input function based on the webform (which would need to be updated).
                                
        cmd_args.append( params["kT"] )
    
        premutatedResidues = []
        designedResidues = []
        partners = params["Partners"]
        cmd_args.append(len(partners))            # for convenience with the command-line parsing logic
        cmd_args.extend(partners)
        
        # Add the partners and build up the residue lists
        for partner in partners:                    
            premutatedResidues.append(partner)
            premlist = params["Premutated"][partner]
            for indx in premlist:
                premutatedResidues.append(str(indx)+str(premlist[indx]))
            
            designedResidues.append(partner)
            designedlist = params["Designed"][partner]
            for indx in designedlist:
                designedResidues.append(str(indx))
                                                      
        cmd_args.extend(params["Weights"])
        cmd_args.extend(premutatedResidues)
        cmd_args.extend(designedResidues)
        
        print string.join([str(arg) for arg in cmd_args])
        
        SEQTOL_obj.run_args(cmd_args)
        time.sleep(1)
        pid = SEQTOL_obj.get_pid()
        # store rosetta object to list; this is not a copy !
        self.list_RosettaPP.append(SEQTOL_obj)
        
        self.running_S += 1
        
        return pid

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

        
    ##################################### end of sendMail() ######################################

class BackendProtocols(WebserverProtocols):
      
    def __init__(self, rosettaDaemon):
        super(BackendProtocols, self).__init__()
        
        protocolGroups = self.protocolGroups
        protocols = self.protocols
        
        # Add backend specific information
        for p in protocols:
            if p.dbname == "point_mutation":
                p.setBackendFunctions(rosettaDaemon.StartMutations, rosettaDaemon.CheckMutations, rosettaDaemon.EndMutations)
            elif p.dbname == "multiple_mutation":
                p.setBackendFunctions(rosettaDaemon.StartMutations, rosettaDaemon.CheckMutations, rosettaDaemon.EndMutations)
            elif p.dbname == "no_mutation":
                p.setBackendFunctions(rosettaDaemon.StartMutations, rosettaDaemon.CheckMutations, rosettaDaemon.EndMutations)
            elif p.dbname == "ensemble":
                p.setBackendFunctions(rosettaDaemon.StartEnsemble, rosettaDaemon.CheckEnsemble, rosettaDaemon.EndEnsemble)
            elif p.dbname == "sequence_tolerance":
                p.setBackendFunctions(rosettaDaemon.StartSequenceToleranceHK, rosettaDaemon.CheckSequenceTolerance, rosettaDaemon.EndSequenceToleranceHK)
            elif p.dbname == "sequence_tolerance_SK":
                p.setBackendFunctions(rosettaDaemon.StartSequenceToleranceSK, rosettaDaemon.CheckSequenceTolerance, rosettaDaemon.EndSequenceToleranceSK)
                
if __name__ == "__main__":

    daemon = RosettaDaemon('/tmp/daemon-example.pid', stdout='/var/www/html/rosettaweb/backrub/temp/running.log', stderr='/var/www/html/rosettaweb/backrub/temp/running.log')
    if len(sys.argv) > 1 and len(sys.argv) <= 3:
        if 'start' == sys.argv[1]:
            daemon.start()
        elif 'stop' == sys.argv[1]:
            daemon.stop()
        elif 'restart' == sys.argv[1]:
            daemon.restart()
        elif 'dbrehash' == sys.argv[1]:
            daemon.dbrehash()
        elif 'dbconvert' == sys.argv[1]:
            daemon.dbconvert()
        elif 'dbcheck' == sys.argv[1]:
            daemon.dbcheck()
        else:
            print "Unknown command"
            sys.exit(2)
        sys.exit(0)
    else:
        print "usage: %s start|stop|restart|dbcheck|dbrehash|dbconvert" % sys.argv[0]
        sys.exit(2)

