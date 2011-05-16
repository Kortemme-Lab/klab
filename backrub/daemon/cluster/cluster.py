#!/usr/bin/python2.4
# encoding: utf-8
"""
cluster.py

Created by Shane O'Connor 2011.
Copyright (c) 2011 __UCSF__. All rights reserved.
"""


import sys
import os
import time
import traceback
import pprint
sys.path.insert(0, "../../common/")
sys.path.insert(0, "../")

from conf_daemon import *
from rosettahelper import *
import RosettaTasks
from sge import SGEConnection, SGEXMLPrinter

if not os.path.exists(netappRoot):
    make755Directory(netappRoot)
if not os.path.exists(cluster_dltest):
    make755Directory(cluster_dltest)

inputDirectory = "/home/oconchus/clustertest110428/rosettawebclustertest/backrub/test/"

# copied from rosetta_daemon
def printStatus(sgec, statusprinter, diffcounter):
    '''Print the status of all jobs.'''
    someoutput = False
    diff = statusprinter.qdiff()
    
    if False: #todo True: # todo self.diffcounter >= CLUSTER_printstatusperiod:
        sys.stdout.write("\n")
        if sgec.CachedList:
            print(sgec.CachedList)
        
    if diff:
        sys.stdout.write("\n")
        diffcounter += 1
        if diffcounter >= CLUSTER_printstatusperiod:
            # Every x diffs, print a full summary
            summary = statusprinter.summary()
            statusList = statusprinter.statusList()
            if summary:
                print(summary)
            if statusList:
                print(statusList)
            diffcounter = 0
        print(diff)
    else:
        # Indicate tick
        sys.stdout.write(".")
    sys.stdout.flush()
    return diffcounter
    
if __name__ == "__main__":
    test = "PSK"
    sgec = SGEConnection()
    try:
        clusterjob = None
        
        if test == "SK":
            mini = "seqtolJMB"
            ID = 1234
            pdb_filename = "1MDY_mod.pdb"    
            output_handle = open(os.path.join(inputDirectory, pdb_filename),'r')
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
                "Partners"          : ["A", "B"],
                "Weights"           : [0.4, 0.4, 0.4, 1.0],
                "Premutated"        : {"A" : {102 : "A"}},
                "Designed"          : {"A" : [103, 104]}
                }
            clusterjob = RosettaTasks.SequenceToleranceJobSK(sgec, params, netappRoot, cluster_dltest)
        
        if test == "PSK":
            mini = "seqtolJMB"
            ID = 1234
            pdb_filename = "1MDY_mod.pdb"    
            output_handle = open(os.path.join(inputDirectory, pdb_filename),'r')
            pdb_info = output_handle.read()
            output_handle.close()
            nstruct = 2
            
            params = {
                "cryptID"           : "cryptic",
                "binary"            : mini,
                "ID"                : ID,
                "pdb_filename"      : pdb_filename,
                "pdb_info"          : pdb_info,
                "nstruct"           : nstruct,
                "radius"            : 10,
                "kT"                : 0.228,
                "Partners"          : ["A", "B"],
                "Weights"           : [0.4, 0.4, 0.4, 1.0],
                "Premutated"        : {"A" : {102 : "A"}},
                "Designed"          : {"A" : [103, 104]}
                }
            clusterjob = RosettaTasks.ParallelSequenceToleranceJobSK(sgec, params, netappRoot, cluster_dltest)
        
        if test == "1KI1analysis":
            mini = "seqtolJMB"
            ID = 1234
            pdb_filename = "1ki1.pdb"
            output_handle = open(os.path.join(inputDirectory, pdb_filename),'r')
            pdb_info = output_handle.read()
            output_handle.close()
            nstruct = 100
            allAAsExceptCysteine = ROSETTAWEB_SK_AAinv.keys()
            allAAsExceptCysteine.sort()
            allAAsExceptCysteine.remove('C')
            
            if CLUSTER_debugmode:
                nstruct = 2
                allAAsExceptCysteine = ["A", "D"]
            
            params = {
                "binary"            : mini,
                "ID"                : ID,
                "pdb_filename"      : pdb_filename,
                "pdb_info"          : pdb_info,
                "nstruct"           : nstruct,
                "radius"            : 10,
                "kT"                : 0.228 + 0.021,
                "Partners"          : ["A", "B"],
                "Weights"           : [0.4, 0.4, 0.4, 1.0],
                "Premutated"        : {"A" : {56 : allAAsExceptCysteine}},
                "Designed"          : {"B" : [1369, 1373, 1376, 1380]}
                }
            clusterjob = RosettaTasks.SequenceToleranceSKAnalyzer(sgec, params, netappRoot, cluster_dltest) 
            clusterjob._analyze()
            sys.exit(0)

        if test == "3QDORtest":            
            mini = "seqtolJMB"
            ID = 1234
            pdb_filename = "3QDO.pdb"    
            output_handle = open(os.path.join(inputDirectory, pdb_filename),'r')
            pdb_info = output_handle.read()
            output_handle.close()
            nstruct = 10
            
            params = {
                "binary"            : mini,
                "ID"                : ID,
                "pdb_filename"      : pdb_filename,
                "pdb_info"          : pdb_info,
                "nstruct"           : nstruct,
                "radius"            : 10,
                "kT"                : 0.228,
                "Partners"          : ["A", "B"],
                "Weights"           : [0.4, 0.4, 0.4, 1.0],
                "Premutated"        : {},
                "Designed"          : {"B" : [203, 204, 205, 206, 207, 208]}
                }
            clusterjob = RosettaTasks.SequenceToleranceJobSK(sgec, params, netappRoot, "/home/oconchus/1KI1test")
            clusterjob.targetdirectory = "/home/oconchus/1KI1test"
            clusterjob._analyze()
            sys.exit(0)
            
        if test == "1KI1":
            mini = "seqtolJMB"
            ID = 1234
            pdb_filename = "1ki1.pdb"
            output_handle = open(os.path.join(inputDirectory, pdb_filename),'r')
            pdb_info = output_handle.read()
            output_handle.close()
            nstruct = 100
            allAAsExceptCysteine = ROSETTAWEB_SK_AAinv.keys()
            allAAsExceptCysteine.sort()
            allAAsExceptCysteine.remove('C')
            
            if CLUSTER_debugmode:
                nstruct = 2
                allAAsExceptCysteine = ["A", "D"]
            
            params = {
                "binary"            : mini,
                "ID"                : ID,
                "pdb_filename"      : pdb_filename,
                "pdb_info"          : pdb_info,
                "nstruct"           : nstruct,
                "radius"            : 10,
                "kT"                : 0.228 + 0.021,
                "Partners"          : ["A", "B"],
                "Weights"           : [0.4, 0.4, 0.4, 1.0],
                "Premutated"        : {"A" : {56 : allAAsExceptCysteine}},
                "Designed"          : {"B" : [1369, 1373, 1376, 1380]}
                }
            clusterjob = RosettaTasks.SequenceToleranceMultiJobSK(sgec, params, netappRoot, cluster_dltest)
            print(clusterjob.scheduler.getAllJIDs())
            sys.exit(0)            
                
        elif test == "HK":
            mini = "seqtolHK"
            ID = 1234
            pdb_filename = "hktest.pdb"    
            output_handle = open(os.path.join(inputDirectory, pdb_filename),'r')
            pdb_info = output_handle.read()
            output_handle.close()
            nstruct = 2
            radius = 5.0 #todo: Set this in the constants file instead
            
            params = {
                "binary"            : mini,
                "ID"                : ID,
                "pdb_filename"      : pdb_filename,
                "pdb_info"          : pdb_info,
                "nstruct"           : nstruct,
                "radius"            : radius,
                "Partners"          : ["A", "B"],
                "Designed"          : {"A" : [], "B" : [145, 147, 148, 150, 152, 153]} # todo: Test when "A" not defined
                }
            
            clusterjob = RosettaTasks.SequenceToleranceJobHK(sgec, params, netappRoot, cluster_dltest)            
        
        if clusterjob:
            #todo: testing clusterjob._analyze()

            statusprinter = SGEXMLPrinter(sgec)
            diffcounter = CLUSTER_printstatusperiod

            clusterjob.start()
            sgec.qstat(waitForFresh = True) # This should sleep until qstat can be called again
            
            try:
                while not(clusterjob.isCompleted()):
                    sgec.qstat(waitForFresh = True)
                    diffcounter = printStatus(sgec, statusprinter, diffcounter)

            except Exception, e:
                print("The scheduler failed at some point: %s." % str(e))
                print(traceback.print_exc())
                
            clusterjob.analyze()
            
            print("<profile>")
            print(clusterjob.getprofileXML())
            print("</profile>")
    
    except Exception, e:
        print(traceback.print_exc())
        print(e)
        

