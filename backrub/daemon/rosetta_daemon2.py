#!/usr/bin/python2.4

import os
import sys
import pdb
import time
import string
import shutil
import zipfile
import MySQLdb
import traceback
import rosetta_rdc
import rosettaplusplus
from daemon import Daemon
from datetime import datetime

cwd = str(os.getcwd())

class RosettaDaemon(Daemon):
    """This class controls the rosetta simulation"""
    
    
    def run(self):
        """runs the daemon, sets the maximal number of parallel simulations"""
        
        self.list_RosettaPP = []
        
        filename_config = cwd + "/../parameter.cfg"
        try:
            self.read_config_file(filename_config)
        except IOError:
            print filename_config, "could not be found."
            sys.exit(2)
        
        # logfile
        self.logfile = self.rosetta_tmp + "RosettaDaemon.log"
        log = open(self.logfile, 'a+')
        log.write("%s\tstarted\n" % datetime.now().strftime("%Y-%m-%d %H:%M:%S") )
        log.close()
        
        while True:
            print "running processes:", len(self.list_RosettaPP)
            # check if a simulation is finished
            for rosetta_object in self.list_RosettaPP:
                if rosetta_object.is_done():
                    # call clean up function
                    (status, error, ID) = self.end_job(rosetta_object)
                    # remove object
                    self.list_RosettaPP.remove(rosetta_object)
                    # update database     
                    query = 'UPDATE %s SET status=%s, Errors="%s", EndDate=NOW() WHERE ID=%s' % ( self.db_table, status, error, ID )
                    self.execQuery(query)
            
            # check whether data of simulations need to be deleted, and delete them from the database as well as from the harddrive
            try:
                self.delete_data()
            except Exception, e:
                log = open(self.logfile, 'a+')
                log.write("%s\t error: self.delete()\n" % datetime.now().strftime("%Y-%m-%d %H:%M:%S") )
                traceback.print_exc(file=log)
                log.write("\n\n")
                log.close()
                #sys.exit(2)

            if len(self.list_RosettaPP) < self.max_processes:
                #print "check for new job"
                # get job from db
                # first lock tables, no surprises!
                query = "LOCK TABLES %s WRITE, Users READ" % self.db_table
                self.execQuery(query)
                # get all jobs in queue                            vvv 0
                query = "SELECT ID,Date,status FROM %s WHERE status=0 ORDER BY Date" % self.db_table
                data = self.execQuery(query)
                try:
                    if len(data) == 0:
                        sql = "UNLOCK TABLES"
                        self.execQuery(query)
                        time.sleep(10) # wait 10 seconds if there's no job in queue
                        continue
                    else:
                        # get first job
                        ID = data[0][0]
                        
                        # get pdb file
                        sql_query = "SELECT PDBComplex,PDBComplexFile,Mini,Mutations,EnsembleSize,task,PM_chain,PM_resid,PM_newres,PM_radius, RDC_temperature, RDC_num_designs_per_struct, RDC_segment_length FROM %s WHERE ID=%s" % ( self.db_table, ID )
                        data = self.execQuery(sql_query)
                        
                        #start the job
                        self.start_job(ID,data[0][0],data[0][1],data[0][2],data[0][3],data[0][4],data[0][5],data[0][6],data[0][7],data[0][8],data[0][9],data[0][10],data[0][11],data[0][12])
                        
                        #change status and write starttime to DB
                        sql_query = "UPDATE %s SET status=1, StartDate=NOW() WHERE ID=%s" % ( self.db_table, ID )
                        self.execQuery(sql_query)
                        
                        # don't forget to unlock the tables!
                        sql = "UNLOCK TABLES"
                        self.execQuery(query)
                        
                        time.sleep(3) # wait 3 seconds after a job was started
                except Exception, e:
                    log = open(self.logfile, 'a+')
                    log.write("%s\t error: self.run()\n" % datetime.now().strftime("%Y-%m-%d %H:%M:%S") )
                    traceback.print_exc(file=log)
                    log.write("\n\n")
                    log.close()
                    time.sleep(10)
            else:
                time.sleep(5)  # wait 5 seconds if max number of jobs is running


    def start_job(self, ID, pdb_info, pdb_filename, mini, mutations, ensemble_size, task, PM_chain, PM_resid, PM_newres, PM_radius, RDC_temperature, RDC_num_designs_per_struct, RDC_segment_length):
        try:
            # this is hacked in so that Greg's script can be run... honestly... this is bad and I'm going to change this ASAP 
            if task == 4: # Gregs ensemble
                
                log = open(self.logfile, 'a+')
                log.write("%s\t start new job ID = %s RDC \n" % ( datetime.now().strftime("%Y-%m-%d %H:%M:%S"), ID) )
                log.close()
                
                rdc_obj = rosetta_rdc.Rosetta_RDC( ID=ID, tempdir = self.rosetta_ens_tmp )
                
                rdc_obj.make_workingdir()
                
                rdc_obj.set_pdb(pdb_filename, pdb_info)
                
                # starting_pdb_file, backrub_num_structs, backrub_max_segment_length, backrub_num_steps, backrub_temp, num_designs_per_struct
                cmd_args = [ self.rosetta_ens_bin, pdb_filename, ensemble_size, RDC_segment_length, 10000, RDC_temperature, RDC_num_designs_per_struct ]
                
                rdc_obj.run_args(cmd_args)
                
                # store rosetta object to list; this is not a copy !
                self.list_RosettaPP.append(rdc_obj)
                # get position in list
                index = self.list_RosettaPP.index(rdc_obj)

                return
                     
            # create rosetta run
            if mini:
                object_rosetta = rosettaplusplus.RosettaPlusPlus( ID = ID, mini = True, executable = self.rosetta_mini_bin, datadir = self.rosetta_mini_db, tempdir = self.rosetta_tmp, auto_cleanup = False)
            else:
                object_rosetta = rosettaplusplus.RosettaPlusPlus( ID = ID, executable = self.rosetta_bin, datadir = self.rosetta_db, tempdir = self.rosetta_tmp, auto_cleanup = False)

            log = open(self.logfile, 'a+')
            log.write("%s\t start new job ID = %s mini = %s\n" % ( datetime.now().strftime("%Y-%m-%d %H:%M:%S"), ID, mini) )
            log.close()
            # store rosetta object to list; this is not a copy !
            self.list_RosettaPP.append(object_rosetta)
            # get position in list
            index = self.list_RosettaPP.index(object_rosetta)
            # create working directory
            object_rosetta.make_workingdir()
            # copy pdb data in object and get filename
            fn_pdb = object_rosetta.set_pdb(pdb_filename, pdb_info)
            
            # create mutations and define backrub residues
            dict_mutation = {}   # name is misleading should be changed at some point. 
                                 # it contains the residues and their modes according to rosetta: { (chain, resID):["PIKAA","PHKL"] }
            backbone      = []   # residues to which backrub should be applied: [ (chain,resid), ... ]
            default       = ""
            rand_chain    = "A"
            
            task = int(task)
            
            if task == 0: # no mutation, apply backrub to all residues
                default = "NATAA"
                if not mini:
                    residue_ids = object_rosetta.pdb.aa_resids()
                    for res in residue_ids:
                        x = res.split()
                        if len(x) == 1:
                            backbone.append( ( "_", int(x[0].lstrip())) )
                        else:
                            backbone.append( ( x[0], int(x[1].lstrip())) )
                            
            elif task == 1: # point mutation
                # oh this hurts a lot ... refactor theses classes and come up with a more elegant way here
                # example: 12 -> 'A  12' -> 'A   8' -> 8
#if not mini:
    #PM_resid = object_rosetta.map_res_id[PM_chain + '%4.i' % int(PM_resid)][1:].lstrip()
    #sql_query = "UPDATE %s SET PM_resid=%s WHERE ID=%s" % ( self.db_table, PM_resid, ID )
    #self.execQuery(sql_query)
                # get the neighbors of all residues
                neighbor_list = object_rosetta.pdb.neighbors( float(PM_radius), PM_resid )
                # set default: don't move other residues
                default = "NATRO"
                
                # let surrounding residues move and apply backrub
                for residue in neighbor_list:
                    pair_res = ( residue[0], int(residue[1:].lstrip()) )
                    dict_mutation[ pair_res ] = ["NATAA", ' ']
                    backbone.append( pair_res )
                
                # overwrite position where the mutation is
                dict_mutation[ (PM_chain, int(PM_resid)) ] = [ "PIKAA", PM_newres ]
                if (PM_chain, int(PM_resid)) not in backbone:
                    backbone.append((PM_chain, int(PM_resid)))    
                    
            elif task == 3: # multiple point mutations
                list_chains = PM_chain.split('-')
                list_resids = [ int(x.strip("\'")) for x in PM_resid.split('-') ]
                list_newres = [ x.strip("\'") for x in PM_newres.split('-') ]
                list_radius = [ float(x.strip("\'")) for x in PM_radius.split('-') ]
                list_new_resid = []
                
                for x in range(len(list_chains)):
## get the neighbors of all residues
#if not mini:
    #entry_list_resid = object_rosetta.map_res_id[list_chains[x].strip("'") + '%4.i' % int(list_resids[x])][1:].lstrip() # not nice
#else:
                    entry_list_resid = str(list_resids[x])

                    list_new_resid.append( entry_list_resid )
                    
                    neighbor_list = object_rosetta.pdb.neighbors( float(list_radius[x]), entry_list_resid ) ## this is not nice accessing pdb from outside the class tztztz!
                    # set default: don't move other residues
                    default = "NATRO"
                    
                    # let surrounding residues move and apply backrub
                    for residue in neighbor_list:
                        pair_res = ( residue[0], int(residue[1:].lstrip()) )
                        dict_mutation[ pair_res ] = ["NATAA", ' ']
                        # add residues to backrub list
                        if pair_res not in backbone:    # check to avoid double entries
                            backbone.append( pair_res )
                   
#sql_query = "update %s set pm_resid=\"%s\" where id=%s" % ( self.db_table, str(list_new_resid).strip('[]').replace(', ','-'), id )
#print sql_query
#self.execquery(sql_query)

                for y in range(len(list_chains)):
#if not mini:
    #entry_list_resid = object_rosetta.map_res_id[list_chains[x].strip('\'') + '%4.i' % int(list_resids[y])][1:].lstrip() # not nice, FIX IT!
#else:
                    entry_list_resid = list_resids[x]
                        
                    # overwrite position where the mutation is
                    dict_mutation[ (list_chains[y].strip('\''), int(entry_list_resid)) ] = [ "PIKAA", list_newres[y] ]
                    if (list_chains[y], int(entry_list_resid)) not in backbone:
                        backbone.append((list_chains[y], int(entry_list_resid)))
                
                ##debug
                #print
                #print dict_mutation
                #print
                #print backbone
                                     
            elif task == 2: # complex mutation (file)
                default = "NATRO"
                new_mutations = '' # used to recreate the file ... but why? ok let's keep it for now (03/05/09) 
                for line in mutations.split('\n'):
                    word = line.split(' ')          # chain id, res id, backrub, residues for mutation
#if not mini:
    #word[1] = object_rosetta.map_res_id[PM_chain + '%4.i' % int(word[1])][1:].lstrip()
                    if len(word) >= 3:
                        if word[2] == 'B':          # for the case backrub should be applied to this residue
                            backbone.append( ( word[0], int(word[1]) ) )
                            dict_mutation[ (word[0], int(word[1])) ] = ["NATAA", ' ']  # allow the residue to move (is overwritten by a mutation) 
                        if len(word) == 4:
                            dict_mutation[ (word[0], int(word[1])) ] = ["PIKAA", word[3]]
                    new_mutations += string.join(word,' ') + '\n'
                
                sql_query = "UPDATE %s SET Mutations=%s WHERE ID=%s" % ( self.db_table, new_mutations, ID )
                self.execQuery(sql_query)
                    
            # create resfile and get filename
            fn_resfile = object_rosetta.write_resfile( default, dict_mutation, backbone )
            # run rosetta
            if mini:
                object_rosetta.run_args( [ "-database", self.rosetta_mini_db, "-s", fn_pdb, "-ignore_unrecognized_res", "-resfile", fn_resfile, "-nstruct",  ensemble_size, "-backrub:ntrials", "10000", "-pivot_atoms", "CA" ] )
            else:
                object_rosetta.run_args( ["-paths","paths.txt","-pose1","-backrub_mc","-s", fn_pdb,"-read_all_chains","-chain","A","-series","BR","-protein", fn_pdb.split('.')[0],"-resfile", fn_resfile, "-use_pdb_numbering", "-ex1aro","-ex2", "-try_both_his_tautomers","-extrachi_cutoff","0","-nstruct",  ensemble_size,"-ntrials","10000"] ) #
                
        except Exception, e:
            log = open(self.logfile, 'a+')
            log.write("%s\t error: start_job() ID = %s" % ( datetime.now().strftime("%Y-%m-%d %H:%M:%S"), ID ) )
            traceback.print_exc(file=log)
            log.write("\n\n")
            log.close()
    
    def end_job(self, rosetta_object):
        
        status  = 2      # 2 means everything went well
        error   = "" 
        ID      = int( rosetta_object.get_ID() )
        mini    = rosetta_object.mini
        subject = "Kortemme Lab Backrub Server - Your Job #%s" % (ID)
        
        sql_query = "SELECT u.Email,u.FirstName,b.KeepOutput,b.cryptID,b.task,b.PDBComplexFile,b.EnsembleSize FROM Users u JOIN %s b on (u.ID=b.UserID) WHERE b.ID=%s" % ( self.db_table, ID )
        data = self.execQuery(sql_query)
        user_email   = data[0][0]
        user_name    = data[0][1]
        keep_output  = int(data[0][2])
        cryptID      = data[0][3]
        task         = int(data[0][4])
        pdb_id       = data[0][5]
        ensembleSize = data[0][6]
        
        try:               
            # open error messages
            error_handle = open( rosetta_object.workingdir + "/" + rosetta_object.filename_stderr, 'r')
            error_file = error_handle.read()
            error_handle.close()
            
            # check whether an error occured i.e. the error file is empty
            if len(error_file) >= 1 and ( task == 4 or (not self.check_files(rosetta_object.workingdir, mini, ensembleSize, pdb_id)) ):
                error = "Rosetta Error"
                status = 4
                # if an error occurs we store the output in the error directory so that the user cannot access it
                shutil.move( rosetta_object.workingdir, rosetta_object.workingdir + "/../../../error/%s/" % ID ) ## does NOT overwrite destination
                #shutil.rename( rosetta_object.workingdir, rosetta_object.workingdir + "/../../../error/%s/" % ID )
                
                mailTXT = """Dear %s,
                
An error occured during your simulation. Please check 
http://albana.ucsf.edu/backrub/cgi-bin/rosettaweb.py?query=jobinfo&jobnumber=%s 
for more information.

The Kortemme Lab Server Daemon
    """ % (user_name, cryptID) 
    
            else: 
                # if no error occured move results directory to the download directory 
                #try:
                if os.path.exists(rosetta_object.workingdir + "/paths.txt"):
                    os.remove( rosetta_object.workingdir + "/paths.txt" )
                # remove error file, it should be empty anyway
                os.remove( rosetta_object.workingdir + "/stderr_%s.dat" % ( ID ) )
                if task == 4:
                    keep_output = True
                    shutil.rmtree( rosetta_object.workingdir + "/designs" )
                    shutil.rmtree( rosetta_object.workingdir + "/backrubs" )
                    shutil.rmtree( rosetta_object.workingdir + "/repack" )
                    
                    os.remove( rosetta_object.workingdir + "/stdout_%s.dat" % ( ID ) )
                    os.remove( rosetta_object.workingdir + "/%s_br.res" % ( pdb_id.split('.')[0] ) )
                    os.remove( rosetta_object.workingdir + "/%s_des.res" % ( pdb_id.split('.')[0] ) )
                    os.remove( rosetta_object.workingdir + "/backrub.log" )
                    os.remove( rosetta_object.workingdir + "/core.txt" )
                    os.remove( rosetta_object.workingdir + "/designed_pdbs.lst" )
                    os.remove( rosetta_object.workingdir + "/ensemble.lst" )
                    #os.remove( rosetta_object.workingdir + "/starting_pdb.lst" )
                    
                    
                # remove the resfile, and rosetta raw output if the user doesn't want to keep it
                if not keep_output:
                    os.remove( rosetta_object.workingdir + "/" + rosetta_object.name_resfile )
                    os.remove( rosetta_object.workingdir + "/stdout_%s.dat" % ( ID ) )
                
                result_dir = "%s%s" % (self.rosetta_dl, cryptID)
                # move the data to a webserver accessible directory 
                shutil.move( rosetta_object.workingdir, result_dir ) ## does NOT overwrite destination
                #shutil.rename( rosetta_object.workingdir, result_dir )
                # make it readable
                os.chmod( result_dir, 0755 )
                # remember directory
                current_dir = os.getcwd()
                os.chdir(result_dir)
                # store all files also in a zip file, to make it easier accessible     
                filename_zip = "data_%s.zip" % ( ID )
                all_output = zipfile.ZipFile(filename_zip, 'w', zipfile.ZIP_DEFLATED)
                
                for file in os.listdir(result_dir):
                    if file != filename_zip:
                        all_output.write( file )
                all_output.close()
                
                # go back to our working dir
                os.chdir(current_dir)
    
                mailTXT = """Dear %s,
    
Your simulation finished successfully. You can download the results as a zipped file or as individual files. Additional information can be found on our webserver.
    
 - Zip file:  http://albana.ucsf.edu/backrub/downloads/%s/data_%s.zip
 - Individual output files:  http://albana.ucsf.edu/backrub/downloads/%s/
 - Job Information:  http://albana.ucsf.edu/backrub/cgi-bin/rosettaweb.py?query=jobinfo&jobnumber=%s
    
Your data will be store for %s days. Thank you for using Backrub.

Have a nice day!

The Kortemme Lab Server Daemon

    """ % (user_name, cryptID, ID, cryptID, cryptID, self.store_time) 
                #except:
                    #status = 5
                    ##error += "\ncould not move directory: %s -> %s%s" % ( rosetta_object.workingdir, self.rosetta_dl, ID )
                    #error = "Server Error"
                    ##mailTXT = str(e.value)
                    
            if not self.sendMail(user_email, self.admin_email, subject, mailTXT):
                log = open(self.logfile, 'a+')
                log.write("%s\t error: sendMail() ID = %s" % ( datetime.now().strftime("%Y-%m-%d %H:%M:%S"), ID ) )
                log.close()
                sql = 'UPDATE %s SET Errors="no email sent" WHERE ID=%s' % ( self.db_table, ID )
                self.execQuery(sql_query)
                
        except Exception, e:
            ID = rosetta_object.get_ID()
            log = open(self.logfile, 'a+')
            log.write("%s\t error: end_job() ID = %s \n*******************************\n" % ( datetime.now().strftime("%Y-%m-%d %H:%M:%S"), ID ) )
            traceback.print_exc(file=log)
            log.write("*******************************\n")
            log.close()
            sql = 'UPDATE %s SET Errors="postprocessing error" Status=4 WHERE ID=%s' % ( self.db_table, ID )
            self.execQuery(sql_query)
            
            mailTXT = """Dear %s,
                
An error occured during your simulation. Please check 
http://albana.ucsf.edu/backrub/cgi-bin/rosettaweb.py?query=jobinfo&jobnumber=%s 
for more information.

The Kortemme Lab Server Daemon
    """ % (user_name, cryptID) 
            
            self.sendMail(user_email, self.admin_email, subject, mailTXT)
            
        
        return (status, error, ID)
   
    def check_files(self, workingdir, mini, ensembleSize, pdb_id):
        """checks whether all pdb files were created
           sometimes Rosetta classic crashes at the end, but the ersults are ok
        """
        
        if mini:
            x = 1
            while x <= ensembleSize:
                if not os.path.exists( '%s/%s_%4.i_last.pdb' + (workingdir, pdb_id, x ) ): return False
                if not os.path.exists( '%s/%s_%4.i_low.pdb' + (workingdir, pdb_id, x ) ): return False
        else:
            x = 1
            while x <= ensembleSize:
                if not os.path.exists( '%s/BR%slast_%4.i.pdb' + (workingdir, pdb_id, x ) ): return False
                if not os.path.exists( '%s/BR%slow_%4.i.pdb' + (workingdir, pdb_id, x ) ): return False
                
        return True
        
        
        
    def delete_data(self):
        query = 'SELECT ID, EndDate, Status FROM %s WHERE DATE_ADD(EndDate, INTERVAL %s DAY) < NOW()' % ( self.db_table, self.store_time )
        data = self.execQuery(query)
        if len(data) > 0:
            for x in data:
                del_ID = x[0]
                query  = 'DELETE FROM %s WHERE ID=%s' % ( self.db_table, del_ID )
                self.execQuery(query)
                if x[2] == 2:
                    shutil.rmtree( "%s%s" % (self.rosetta_dl, del_ID) )
                    rmdir = "%s%s" % (self.rosetta_dl, del_ID)
                #else:
                #    shutil.rmtree( "%s../error/%s" % (self.rosetta_dl, del_ID) )
                #    rmdir = "%s../error/%s" % (self.rosetta_dl, del_ID)
                #print "delete: %s" % (rmdir)
   

    def read_config_file(self,filename_config):
        handle = open(filename_config, 'r')
        lines  = handle.readlines()
        handle.close()
        parameter = {}
        for line in lines:
            if line[0] != '#' and len(line) > 1  : # skip comments and empty lines
                # format is: "parameter = value"
                list_data = line.split()
                parameter[list_data[0]] = list_data[2]
        
        self.admin_email       = parameter["admin_email"]
        self.max_processes     = int(parameter["max_processes"])
        self.db_host           = parameter["db_host"]
        self.db_name           = parameter["db_name"]
        self.db_user           = parameter["db_user"]
        self.db_pw             = parameter["db_pw"]
        self.db_port           = int(parameter["db_port"])
        self.db_socket         = parameter["db_socket"]
        self.db_table          = parameter["db_table"]
        self.rosetta_ens_bin   = parameter["rosetta_ens_bin"]
        self.rosetta_bin       = parameter["rosetta_bin"]
        self.rosetta_db        = parameter["rosetta_db"]
        self.rosetta_mini_bin  = parameter["rosetta_mini_bin"]
        self.rosetta_mini_db   = parameter["rosetta_mini_db"]
        self.rosetta_tmp       = parameter["rosetta_tmp"]
        self.rosetta_ens_tmp   = parameter["rosetta_ens_tmp"]
        self.rosetta_dl        = parameter["rosetta_dl"]
        self.store_time        = parameter["store_time"]
        

    def execQuery(self,sql):
        """execute SQL query"""
        i = 1
        while i <= 32:
            try:
                connection = MySQLdb.Connection( host=self.db_host, db=self.db_name, user=self.db_user, passwd=self.db_pw, port=self.db_port, unix_socket=self.db_socket )
                cursor = connection.cursor()
                cursor.execute(sql)
                results = cursor.fetchall()
                cursor.close()
                return results
            except:
                time.sleep(i)
                i += i
                break        
        return None
            
    #############################################################################################
    # sendMail()                                                                                #
    # sendmail wrapper                                                                          #
    #############################################################################################
    
    def sendMail(self, mailTO, mailFROM, mailSUBJECT, mailTXT):
        MAIL = "/usr/sbin/sendmail"
    
        mssg = "To: %s\nFrom: %s\nReply-To: %s\nSubject: %s\n\n%s" % (mailTO, mailFROM, 'lauck@cgl.ucsf.edu', mailSUBJECT, mailTXT)
        # open a pipe to the mail program and
        # write the data to the pipe
        p = os.popen("%s -t" % MAIL, 'w')
        p.write(mssg)
        exitcode = p.close()
        if exitcode:
            return exitcode
        else:
            return 1
    
    ##################################### end of sendMail() ######################################

if __name__ == "__main__":

    daemon = RosettaDaemon('/tmp/daemon-example.pid')
    if len(sys.argv) == 2:
        if 'start' == sys.argv[1]:
            daemon.start()
        elif 'stop' == sys.argv[1]:
            daemon.stop()
        elif 'restart' == sys.argv[1]:
            daemon.restart()
        else:
            print "Unknown command"
            sys.exit(2)
        sys.exit(0)
    else:
        print "usage: %s start|stop|restart" % sys.argv[0]
        sys.exit(2)

