#!/usr/bin/python2.4
# -*- coding: iso-8859-15 -*-

########################################
# Constants for the daemon and cluster code
########################################

CLUSTER_debugmode = True
CLUSTER_UserAccount = "klabqb3backrub"

clusterRootDir = "/netapp/home/klabqb3backrub"
netappRoot = "%s/temp" % clusterRootDir

#todo:
cluster_dltest = "/home/oconchus/clustertest110428/rosettawebclustertest/backrub/downloads"
cluster_temp = "/home/oconchus/clustertest110428/rosettawebclustertest/backrub/temp/cluster"

CLUSTER_printstatusperiod = 5
CLUSTER_qstatpause = 60
if CLUSTER_debugmode:
    CLUSTER_qstatpause = 20
