Instructions on running the daemons.

To start/restart/stop the webserver daemon, run:
  sudo python rosetta_daemon.py start
  sudo python rosetta_daemon.py restart
  sudo python rosetta_daemon.py stop

To restart/stop the cluster daemon, run:
  sudo -u klabqb3backrub ./start cluster
  sudo -u klabqb3backrub ./stop cluster

To run a test job on the cluster using cluster/clusterrun.py, run:
  cd cluster
  sudo -u klabqb3backrub admin/testCluster
