#!/usr/bin/env python2

def is_this_chef():
    from socket import gethostname
    return gethostname() == 'chef.compbio.ucsf.edu'

def require_chef():
    if not is_this_chef():
        raise SystemExit("This script must be run on chef.")

def require_qsub():
    import os, subprocess

    try:
        command = 'qsub', '-help'
        devnull = open(os.devnull)
        subprocess.Popen(command, stdout=devnull, stderr=devnull).communicate()
    except OSError as e:
        if e.errno == os.errno.ENOENT:
            print "'qsub' not found.  Are you logged onto the cluster?"
            raise SystemExit

    
