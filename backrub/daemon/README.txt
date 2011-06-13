Instructions on running the daemons.

To start/restart/stop the webserver daemon, run:
  sudo -u klabqb3backrub python rosetta_daemon.py start
  sudo -u klabqb3backrub python rosetta_daemon.py restart
  sudo -u klabqb3backrub python rosetta_daemon.py stop

To restart/stop the cluster daemon, run:
  sudo -u klabqb3backrub ./qbstart
  sudo -u klabqb3backrub ./qbstop

To run a test job on the cluster using cluster/cluster.py, run:
  cd cluster
  sudo -u klabqb3backrub admin/testCluster
