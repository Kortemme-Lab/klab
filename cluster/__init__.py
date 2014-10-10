#!/usr/bin/env python2

def is_this_chef():
    from socket import gethostname
    return gethostname() == 'chef.compbio.ucsf.edu'

def require_chef():
    if not is_this_chef():
        raise SystemExit("This script must be run on chef.")

