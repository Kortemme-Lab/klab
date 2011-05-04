#!/usr/bin/env python

# Set up array jobs for QB3 cluster.
import sys
import os
import time
import traceback
import pprint
sys.path.insert(0, "../")
sys.path.insert(0, "../../common/")

import RosettaTasks
from rosettahelper import make755Directory, makeTemp755Directory
from conf_daemon import *
from rosettahelper import *

if not os.path.exists(netappRoot):
    make755Directory(netappRoot)
if not os.path.exists(resultsRoot):
    make755Directory(resultsRoot)
    
if __name__ == "__main__":
    qstatpause = 20
    
    test = "1KI1"
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
                "numchains"         : 1,
                "Partners"          : ["A"],
                "Weights"           : [0.4, 0.4],
                "Premutated"        : {"A" : {102 : "A"}},
                "Designed"          : {"A" : [103, 104]}
                }
            clusterjob = RosettaTasks.SequenceToleranceJobSK(params, netappRoot, resultsRoot)            
        
        if test == "1KI1":
            mini = "seqtolJMB"
            ID = 1234
            pdb_filename = "1KI1.pdb"
            output_handle = open(os.path.join(inputDirectory, pdb_filename),'r')
            pdb_info = output_handle.read()
            output_handle.close()
            nstruct = 2
            allAAsExceptCysteine = ROSETTAWEB_SK_AAinv.keys()
            allAAsExceptCysteine.sort()
            allAAsExceptCysteine.remove('C')
    
            params = {
                "binary"            : mini,
                "ID"                : ID,
                "pdb_filename"      : pdb_filename,
                "pdb_info"          : pdb_info,
                "nstruct"           : nstruct,
                "radius"            : 10,
                "kT"                : 0.228 + 0.021,
                "numchains"         : 2,
                "Partners"          : ["A", "B"],
                "Weights"           : [0.4, 0.4, 0.4, 1.0],
                "Premutated"        : {"A" : {56 : allAAsExceptCysteine}},
                "Designed"          : {"B" : [1369, 1373, 1376, 1380]}
                }
            clusterjob = RosettaTasks.SequenceToleranceMultiJobSK(params, netappRoot, resultsRoot)            
                
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
            
            clusterjob = RosettaTasks.SequenceToleranceJobHK(params, netappRoot, resultsRoot)            
        
        if clusterjob:
            #todo: testing clusterjob._analyze()
            
            clusterjob.start()
            
            try:
                while not(clusterjob.isCompleted()):
                    time.sleep(qstatpause)
            except Exception, e:
                print("The scheduler failed at some point: %s." % str(e))
                print(traceback.print_exc())
                
            clusterjob.analyze()
            clusterjob.cleanup()
            jobprofile = clusterjob.getprofile()
            
            print("<profile>")
            print(clusterjob.getprofileXML())
            print("</profile>")
    
    except Exception, e:
        print(traceback.print_exc())
        print(e)
        

