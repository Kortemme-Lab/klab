#!/usr/bin/python2.4
# -*- coding: iso-8859-15 -*-

########################################
# Constants for the daemon and cluster code
########################################
import sys
import os
from rosettahelper import server_root

# Cluster debug mode. Sets jobs to use short iterations for quick testing
CLUSTER_debugmode = False

# Local directories
cluster_dldir = os.path.join(server_root, "downloads")
cluster_remotedldir = os.path.join(server_root, "remotedownloads")
cluster_remotedldir = "/var/www/html/rosettaweb/backrub/remotedownloads"
cluster_temp = os.path.join(server_root, "temp/cluster")

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
