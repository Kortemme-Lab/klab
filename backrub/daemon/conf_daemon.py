#!/usr/bin/python2.4
# -*- coding: iso-8859-15 -*-

########################################
# Constants for the daemon and cluster code
########################################
import sys
import os
from rosettahelper import WebsiteSettings

# Local directories
if os.environ.get('PWD'):
    settings = WebsiteSettings(sys.argv, os.environ['PWD'])
else:
    settings = WebsiteSettings(sys.argv, os.environ['SCRIPT_NAME'])
    
server_root = settings["BaseDir"]
cluster_dldir = settings["ClusterDownloadDir"]
cluster_remotedldir = settings["ClusterRemoteDownloadDir"]
cluster_temp = settings["ClusterTemp"]

# Cluster debug mode. Sets jobs to use short iterations for quick testing
CLUSTER_debugmode = settings["ClusterDebugMode"]

# Cluster netapp directories
clusterRootDir = "/netapp/home/klabqb3backrub"
netappRoot = "%s/temp" % clusterRootDir

# Cluster constants
CLUSTER_UserAccount = "klabqb3backrub"
CLUSTER_printstatusperiod = 5
CLUSTER_qstatpause = 60
CLUSTER_maxhoursforjob = 335
CLUSTER_maxminsforjob = 59

if CLUSTER_debugmode:
    CLUSTER_qstatpause = 20
    CLUSTER_maxhoursforjob = 0
    CLUSTER_maxminsforjob = 29
