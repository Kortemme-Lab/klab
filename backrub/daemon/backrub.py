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

from rosetta_daemon import RosettaDaemon
from cluster_daemon import ClusterDaemon

def _removejob(daemon, UserID, jobID):
    try: 
        print("Removing job %s:" % jobID)
        sql = "SELECT ID, Notes FROM %s WHERE ID=%d AND UserID=%d" % (daemon.db_table, jobID, UserID)
        results = daemon.runSQL(sql)
        if not results:
            print("Job not found.")
            return False
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
        return False
    return True

def _add(daemon, UserID, job):
    try:
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
        if 'sk' == job:
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
        elif 'hk' == job:
            print("Adding a new sequence tolerance (HK) job:")
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
        else:
            return False
        ProtocolParameters = pickle.dumps(ProtocolParameters)
    except Exception, e:
        #daemon.runSQL("UNLOCK TABLES")
        print("\tError: %s\n%s" % (str(e), traceback.print_exc())) 
        print("Failed.")
        return False

    try: 
        import random
        import md5
        print(UserID)
        #daemon.runSQL("LOCK TABLES %s WRITE, Users READ" % daemon.db_table)
        daemon.runSQL("""INSERT INTO %s ( Date,hashkey,BackrubServer,Email,UserID,Notes, PDBComplex,PDBComplexFile,IPAddress,Host,Mini,EnsembleSize,KeepOutput,task, ProtocolParameters) 
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
        
        #livejobs = daemon.runSQL("SELECT Date,hashkey,Email,UserID,Notes, PDBComplex,PDBComplexFile,IPAddress,Host,Mini,EnsembleSize,KeepOutput,task, ProtocolParameters FROM %s WHERE UserID=%d and (%s) ORDER BY Date" % (daemon.db_table, UserID, daemon.SQLJobSelectString))
        livejobs = daemon.runSQL("SELECT ID, Status, Notes FROM %s WHERE UserID=%d and (%s) ORDER BY Date" % (daemon.db_table, UserID, daemon.SQLJobSelectString))
        #daemon.runSQL("UNLOCK TABLES")
        print(livejobs)
        print("Success.")
    except Exception, e:
        #daemon.runSQL("UNLOCK TABLES")
        print("\tError: %s\n%s" % (str(e), traceback.print_exc())) 
        print("Failed.")
        return False
    return True

def printUsage():
    print "\n* Usage *\n"
    print "Backend daemon: %s [ backend start | backend stop | backend restart  ]" % sys.argv[0]
    print "Cluster daemon: %s [ cluster start | cluster stop | cluster restart  ]" % sys.argv[0]
    print "Database tools: %s [ db check      | db rehash    | db convert       ]" % sys.argv[0]
    print "Test functions: %s [ test add sk   | test add hk  | test remove <id> ]" % sys.argv[0]
    print("")
   
def db(argv):
    #todo: separate out the db functions from RosettaDaemon
    daemon = RosettaDaemon(os.path.join(temppath, 'dbrunning.log'), os.path.join(temppath, 'dbrunning.log'))
    if 'rehash' == argv[0]:
        daemon.dbrehash()
    elif 'convert' == argv[0]:
        daemon.dbconvert()
    elif 'check' == argv[0]:
        daemon.dbcheck()
    elif ('dumppdb' == argv[0]) and argv[1]:
        daemon.dbdumpPDB(int(argv[1]))
    else:
        return False
    return True

def test(argv):
    UserID = 106
    daemon = ClusterDaemon(os.path.join(temppath, 'testrunning.log'), os.path.join(temppath, 'testrunning.log'))    
    if len(argv > 1):
        if 'remove' == argv[0]:
            return _remove(daemon, UserID, int(argv[1]))
        elif 'add' == argv[0]:
            return _add(daemon, UserID, argv[1]) 
    return False

def backend(argv):
    daemon = RosettaDaemon(os.path.join(temppath, 'running.log'), os.path.join(temppath, 'running.log'))
    if 'start' == argv[0]:
        daemon.start()
    elif 'stop' == argv[0]:
        daemon.stop()
    elif 'restart' == argv[0]:
        daemon.restart()
    else:
        return False
    return True

def cluster(argv):
    #upgradetodo daemon = ClusterDaemon(os.path.join(temppath, 'qb3running.log'), os.path.join(temppath, 'qb3running.log'))
    daemon = ClusterDaemon('/dev/stdout','/dev/stderr')
    if 'start' == argv[0]:
        daemon.start()
    elif 'stop' == argv[0]:
        daemon.stop()
    elif 'restart' == argv[0]:
        daemon.restart()
    else:
        return False
    return True

def parse(argv):
    if len(argv) > 2:
        if 'backend' == argv[1]:
            return backend(argv[2:])
        elif 'db' == argv[1]:
            return db(argv[2:])
        elif 'cluster' == argv[1]:
            return cluster(argv[2:])
        elif 'test' == sys.argv[1]:
            return test(argv[2:])
    return False

temppath = os.path.join(server_root, 'temp')
if not parse(sys.argv):
    printUsage()
    sys.exit(1)

