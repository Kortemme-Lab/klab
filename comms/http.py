#!/usr/bin/python
# encoding: utf-8
"""
http.py
http wrappers

Created by Shane O'Connor 2012
"""

import os
from httplib import HTTPConnection

def get(url):
    url = url.strip()
    if url[:7].lower()==("http://"):
        url = url[7:]
    idx = url.find('/')

    root = url[:idx]
    resource = url[idx:]
    c = HTTPConnection(root)
    c.request("GET", resource)
    response = c.getresponse()
    contents = response.read()
    c.close()
    return contents

def get_resource(url, resource):
    c = HTTPConnection(url)
    c.request("GET", resource)
    response = c.getresponse()
    contents = response.read()
    c.close()
    if contents[0:6] == "<html>":
        raise Exception("Error retrieving %s." % os.path.split(url)[1])
    return contents
