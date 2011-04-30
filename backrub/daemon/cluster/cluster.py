#!/usr/bin/env python

# Set up array jobs for QB3 cluster.
import sys
import os
import time
import traceback
import pprint
sys.path.insert(0, "../../common/")

import RosettaTasks
from rosettahelper import make755Directory, makeTemp755Directory

#todo: so your job must copy back any data it needs on completion.

#scp tempdir/* shaneoconner@chef.compbio.ucsf.edu:/netapp/home/shaneoconner/temp/tempdir
#publickey = /netapp/home/shaneoconner/.ssh/id_rsa.pub

# All cluster binaries should have the same name format based on the clusterrev field in RosettaBinaries: 
#    i) they are stored in the subdirectory of home named <clusterrev>
#   ii) they are named <somename>_<clusterrev>_static
# Furthermore, the related database should be in a subdirectory of the bindir named "rosetta_database"
# The "static" in the name is a reminder that these binaries must be built statically.


#todo: Load from rwebhelper.py
ROSETTAWEB_SK_AA = {"ALA": "A", "CYS": "C", "ASP": "D", "GLU": "E", "PHE": "F", "GLY": "G",
                    "HIS": "H", "ILE": "I", "LYS": "K", "LEU": "L", "MET": "M", "ASN": "N",
                    "PRO": "P", "GLN": "Q", "ARG": "R", "SER": "S", "THR": "T", "VAL": "V",
                    "TRP": "W", "TYR": "Y"}
ROSETTAWEB_SK_AAinv = {}
for k, v in ROSETTAWEB_SK_AA.items():
    ROSETTAWEB_SK_AAinv[v] = k


netappRoot = "/netapp/home/klabqb3backrub/temp"
resultsRoot = "/home/oconchus/clustertest110428/rosettawebclustertest/backrub/daemon/cluster/output"
inputDirectory = "/home/oconchus/clustertest110428/rosettawebclustertest/backrub/daemon/cluster/input/"


if not os.path.exists(netappRoot):
    make755Directory(netappRoot)
if not os.path.exists(resultsRoot):
    make755Directory(resultsRoot)
    
if __name__ == "__main__":
    qstatpause = 60
    
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
            nstruct = 100
            allAAsExceptCysteine = ROSETTAWEB_SK_AAinv.keys()
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
        

