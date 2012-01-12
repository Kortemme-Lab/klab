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
sys.path.insert(1, "../")

from conf_daemon import *
from rosettahelper import *
import RosettaTasks
from sge import SGEConnection, SGEXMLPrinter
from Graph import JITGraph

dlDirectory = "/home/oconchus/clustertest110428/rosettawebclustertest/backrub/temp/clusterstandalone"
inputDirectory = "/home/oconchus/clustertest110428/rosettawebclustertest/backrub/test/"
sgec = SGEConnection()

if not os.path.exists(netappRoot):
    make755Directory(netappRoot)
if not os.path.exists(cluster_dldir):
    make755Directory(cluster_dldir)
if not os.path.exists(cluster_temp):
    make755Directory(cluster_temp)
if not os.path.exists(dlDirectory):
    make755Directory(dlDirectory)

# copied from rosetta_daemon
def printStatus(sgec, statusprinter, diffcounter):
    '''Print the status of all jobs.'''
    someoutput = False
    diff = statusprinter.qdiff()
        
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

def setupParameters(binary, ID, pdb_filename, nstruct, specificParameters):
    output_handle = open(os.path.join(inputDirectory, pdb_filename),'r')
    pdb_info = output_handle.read()
    output_handle.close()
    specificParameters["binary"] = binary
    specificParameters["ID"] = ID
    specificParameters["pdb_filename"] = pdb_filename
    specificParameters["pdb_info"] = pdb_info
    specificParameters["nstruct"] = nstruct
    specificParameters["cryptID"] = "cryptic"
  
def testSequenceToleranceSK(extraparams):
    params = {
                "radius"            : 10,
                "kT"                : 0.228,
                "Partners"          : ["A", "B"],
                "Weights"           : [0.4, 0.4, 0.4, 1.0],
                "Premutated"        : {"A" : {102 : "A"}},
                "Designed"          : {"A" : [103, 104]}
                }
    setupParameters(extraparams["binary"], 1234, "1MDY_mod.pdb", 2, params)            
    return RosettaTasks.SequenceToleranceSKJob(sgec, params, netappRoot, cluster_temp, dlDirectory)

def testSequenceToleranceSKNegativeIndices(extraparams):
    params = {
                "radius"            : 10,
                "kT"                : 0.228,
                "Partners"          : ["A", "B"],
                "Weights"           : [0.4, 0.4, 0.4, 1.0],
                "Premutated"        : {},
                "Designed"          : {"B" : [11, 13]}
                }
    setupParameters(extraparams["binary"], 1234, "negidx.pdb", 2, params)            
    return RosettaTasks.SequenceToleranceSKJob(sgec, params, netappRoot, cluster_temp, dlDirectory)
    
def testMultiSequenceToleranceSKCommon(extraparams):
    nstruct = 100
    allAAsExceptCysteine = ROSETTAWEB_SK_AAinv.keys()
    allAAsExceptCysteine.sort()
    allAAsExceptCysteine.remove('C')
    if CLUSTER_debugmode:
        nstruct = 2
        allAAsExceptCysteine = ["A", "D"]

    params = {
                "radius"            : 10,
                "kT"                : 0.228 + 0.021,
                "Partners"          : ["A", "B"],
                "Weights"           : [0.4, 0.4, 0.4, 1.0],
                "Premutated"        : {"A" : {56 : allAAsExceptCysteine}},
                "Designed"          : {"B" : [1369, 1373, 1376, 1380]}
                }
    setupParameters("multiseqtol", 1234, "1KI1.pdb", nstruct, params)
    return params  

def testSequenceToleranceHKAnalysis(extraparams):
    '''To use this to check the analysis functions, set the extraparams in the tests table below.'''
    params = {
                "radius"            : 5.0,  #todo: Set this in the constants file instead
                "Partners"          : ["B", "C"],
                "Designed"          : {"B" : [], "C" : [311]} # todo: Test when "A" not defined
                }
    setupParameters("seqtolHK", 2017, "1FRT.pdb", 10, params)            
    return RosettaTasks.SequenceToleranceHKJobAnalyzer(sgec, params, netappRoot, cluster_temp, dlDirectory, extraparams)

def testSequenceToleranceSKAnalysis(extraparams):
    params = {
                "radius"            : 10,
                "kT"                : 0.228,
                "Partners"          : ["C", "D"],
                "Weights"           : [0.4, 0.4, 0.4, 1.0],
                "Premutated"        : {},
                "Designed"          : {"D" : [434, 435, 436, 309, 310, 311, 314, 252, 253, 254]}
                }
    setupParameters(extraparams["binary"], 2016, "1FC2.pdb", 10, params)            
    return RosettaTasks.SequenceToleranceSKJobAnalyzer(sgec, params, netappRoot, cluster_temp, dlDirectory, extraparams["dldir"])
    

def testMultiSequenceToleranceSKCommon2541(extraparams):
    global inputDirectory
    inputDirectory = "/home/oconchus/temp/rescore2541"

    nstruct = 20
    allAAsExceptCysteine = ROSETTAWEB_SK_AAinv.keys()
    allAAsExceptCysteine.sort()
    allAAsExceptCysteine.remove('C')
    
    params = {
                "radius"            : 10,
                "kT"                : 0.249000,
                "Partners"          : ["A", "B"],
                "Weights"           : [0.4, 0.4, 0.4, 1.0],
                "Premutated"        : {"B" : {1109 : allAAsExceptCysteine}},
                "Designed"          : {"A" : [96, 146, 142]}
                }
    setupParameters("multiseqtol", 2541, "1QAV.pdb", nstruct, params)
    return params  

def testMultiSequenceToleranceSKCommon2565(extraparams):
    global inputDirectory
    inputDirectory = "/home/oconchus/temp/rescore2565"

    nstruct = 2
    allAAsExceptCysteine = ROSETTAWEB_SK_AAinv.keys()
    allAAsExceptCysteine.sort()
    allAAsExceptCysteine.remove('C')
    
    params = {
                "radius"            : 10,
                "kT"                : 0.249000,
                "Partners"          : ["A", "B"],
                "Weights"           : [0.4, 0.4, 0.4, 1.0],
                "Premutated"        : {"A" : {56 : ['A']}},
                "Designed"          : {"B" : [1369]}
                }
    setupParameters("multiseqtol", 2565, "1KI1.pdb", nstruct, params)
    return params  

def testMultiSequenceToleranceSKAnalysis(extraparams):
    params = testMultiSequenceToleranceSKCommon2565(extraparams) 
    return RosettaTasks.SequenceToleranceSKMultiJobAnalyzer(sgec, params, netappRoot, cluster_temp, dlDirectory, extraparams)

def testMultiSequenceToleranceSK(extraparams):
    params = testMultiSequenceToleranceSKCommon(extraparams) 
    return RosettaTasks.SequenceToleranceSKMultiJob(sgec, params, netappRoot, cluster_temp, dlDirectory)

def testMultiSequenceToleranceSKFixBB(extraparams):
    nstruct = 100
    if CLUSTER_debugmode:
        nstruct = 2
        allAAsExceptCysteine = ["A", "D"]

    params = {
                "radius"            : 10,
                "kT"                : 0.228 + 0.021,
                "Partners"          : ["A", "B"],
                "Weights"           : [0.4, 0.4, 0.4, 1.0],
                "Premutated"        : {"A" : {56 : 'R'}},
                "Designed"          : {"B" : [1369, 1373, 1376, 1380]}
                }
    setupParameters("multiseqtol", 1234, "1KI1_fixbb_out.pdb", nstruct, params)
    return RosettaTasks.SequenceToleranceSKMultiJobFixBB(sgec, params, netappRoot, cluster_temp, dlDirectory)

def testSequenceToleranceHK(extraparams):
    params = {
                "radius"            : 5.0,  #todo: Set this in the constants file instead
                "Partners"          : ["A", "B"],
                "Designed"          : {"A" : [], "B" : [3, 4, 5, 6]} # todo: Test when "A" not defined
                }
    setupParameters("seqtolHK", 1934, "2PDZ.pdb", 49, params)            
    return RosettaTasks.SequenceToleranceHKJob(sgec, params, netappRoot, cluster_temp, dlDirectory)

def run(test):
    tests = {
        "HK"           : {"testfn" : testSequenceToleranceHK,               "analysisOnly" : False, "extraparams" : None},
        "HKAnalysis"   : {"testfn" : testSequenceToleranceHKAnalysis,       "analysisOnly" : True,  "extraparams" : ("/home/oconchus/clustertest110428/rosettawebclustertest/backrub/downloads/testhk/tmphYbm4h_seqtolHK/", 6217160)},
        "SKJMB"        : {"testfn" : testSequenceToleranceSK,               "analysisOnly" : False, "extraparams" : {"binary" : "seqtolJMB"}},
        "SKJMBneg"     : {"testfn" : testSequenceToleranceSKNegativeIndices,"analysisOnly" : False, "extraparams" : {"binary" : "seqtolP1"}},
        "SKP1"         : {"testfn" : testSequenceToleranceSK,               "analysisOnly" : False, "extraparams" : {"binary" : "seqtolP1"}},
        "SKAnalysis"   : {"testfn" : testSequenceToleranceSKAnalysis,       "analysisOnly" : True,  "extraparams" : {"binary" : "seqtolP1", "dldir" : "/home/oconchus/clustertest110428/rosettawebclustertest/backrub/downloads/41f7141e75998737061a3cca2e1dd7b7"}},
        "1KI1"         : {"testfn" : testMultiSequenceToleranceSK,          "analysisOnly" : False, "extraparams" : None},
        "1KI1analysis" : {"testfn" : testMultiSequenceToleranceSKAnalysis,  "analysisOnly" : True,  "extraparams" : "/home/oconchus/temp/rescore2565"},
        "1KI1fixBB"    : {"testfn" : testMultiSequenceToleranceSKFixBB,     "analysisOnly" : False, "extraparams" : None},
     }
    if tests.get(test):
        test = tests[test]
        clusterjob = test["testfn"](test["extraparams"])
        if clusterjob:
            if test["analysisOnly"]:
                clusterjob._analyze()
                print("Analysis finished.")
            else:
                try:                                                                                       
                    statusprinter = SGEXMLPrinter(sgec)
                    diffcounter = CLUSTER_printstatusperiod
        
                    print("Starting job.")
                    clusterjob.start()
                    sgec.qstat(waitForFresh = True) # This should sleep until qstat can be called again
                    
                    destpath = os.path.join(cluster_dldir, clusterjob.parameters["cryptID"])
                    if os.path.exists(destpath):
                        shutil.rmtree(destpath)
        
                    try:
                        while not(clusterjob.isCompleted()):
                            sgec.qstat(waitForFresh = True)
                            diffcounter = printStatus(sgec, statusprinter, diffcounter)
                            clusterjob.dumpJITGraph()
                            
                        clusterjob.dumpJITGraph()
                        clusterjob.analyze()
                    
                    except Exception, e:
                        print("The scheduler failed at some point: %s." % str(e))
                        print(traceback.print_exc())
                        if clusterjob:
                            # This should delete the working and target directories so comment this line out for testing
                            #clusterjob.kill()
                            pass
                        print("Killed jobs")    
                    
                    print("<profile>")
                    print(clusterjob.getprofileXML())
                    print("</profile>")
    
                except Exception, e:
                    print(traceback.print_exc())
                    print(e)
    else:
    	print("Cannot find test '%s'." % test)

run("1KI1analysis")
