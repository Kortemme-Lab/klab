#!/usr/bin/python
# encoding: utf-8
"""
info.py
Functions to query the operating system.

Created by Shane O'Connor 2013
"""

import socket

def get_hostname():
    hostname = socket.gethostname().split('.')[0]
    assert(hostname.isalnum())
    return hostname