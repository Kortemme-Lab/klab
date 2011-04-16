#!/usr/bin/env python

# Set up array jobs for QB3 cluster.
import sys
import os
import time
sys.path.insert(0, "../common/")

import RosettaTasks
 
#todo: so your job must copy back any data it needs on completion.

#scp tempdir/* shaneoconner@chef.compbio.ucsf.edu:/netapp/home/shaneoconner/temp/tempdir
#publickey = /netapp/home/shaneoconner/.ssh/id_rsa.pub

if not os.path.exists("output"):
    os.mkdir("output")

# All cluster binaries should have the same name format based on the clusterrev field in RosettaBinaries: 
#    i) they are stored in the subdirectory of home named <clusterrev>
#   ii) they are named <somename>_<clusterrev>_static
# Furthermore, the related database should be in a subdirectory of the bindir named "rosetta_database"
# The "static" in the name is a reminder that these binaries must be built statically.
      

if __name__ == "__main__":
    
    test = "HK"
    
    if test = "SK":
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
            "Weights"           : [0.4, 0.4],
            "Premutated"        : {"A" : {319 : "A"}},
            "Designed"          : {"A" : [318]}
            }
        seqtol = RosettaTasks.RosettaSequenceToleranceSK(params, "/netapp/home/shaneoconner/temp", "/netapp/home/shaneoconner/results")
        seqtol.start()
        
        while not(seqtol.isCompleted()):
            time.sleep(20)
        
        seqtol.cleanup()
        
    elif test = "HK":
        mini = "seqtolHK"
        ID = 1234
        pdb_filename = "hktest.pdb"    
        output_handle = open(pdb_filename,'r')
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
            "Designed"          : {"B" : [145, 147, 148, 150, 152, 153]}
            }
        
        seqtol = RosettaTasks.RosettaSequenceToleranceHK(params, "/netapp/home/shaneoconner/temp", "/netapp/home/shaneoconner/results")
        seqtol.start()
        
        while not(seqtol.isCompleted()):
            time.sleep(20)
        
        seqtol.analyze()
        seqtol.cleanup()
        
