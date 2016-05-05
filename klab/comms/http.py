#!/usr/bin/python
# encoding: utf-8
"""
http.py
http wrappers

Created by Shane O'Connor 2012
"""

import os
import time
import traceback
from httplib import HTTPConnection

def get(url, timeout = None):
    url = url.strip()
    if url[:7].lower()==("http://"):
        url = url[7:]
    idx = url.find('/')

    root = url[:idx]
    resource = url[idx:]
    c = HTTPConnection(root, timeout = timeout)
    c.request("GET", resource)
    response = c.getresponse()
    contents = response.read()
    c.close()
    return contents


def get_resource(url, resource, timeout = None):
    c = HTTPConnection(url, timeout = timeout)
    c.request("GET", resource)
    response = c.getresponse()
    contents = response.read()
    c.close()
    if contents[0:6] == "<html>":
        raise Exception("Error retrieving %s." % os.path.split(url)[1])
    return contents



class Connection(object):
    '''A class to keep a HTTPConnection open for multiple requests.'''

    def __init__(self, url, timeout = None, attempts = 3):
        self.timeout = timeout
        self.attempts = attempts
        self.url = url
        self.connection = None


    def _get_connection(self):
        if self.connection:
            return self.connection
        else:
            if self.timeout:
                self.connection = HTTPConnection(self.url, timeout = self.timeout)
            else:
                self.connection = HTTPConnection(self.url)


    def __del__(self):
        if self.connection:
            self.connection.close()


    def _close(self):
        if self.connection: self.connection.close()


    def get(self, resource):
        attempts_left = self.attempts
        while attempts_left > 0:
            try:
                self._get_connection()
                self.connection.request("GET", resource)
                response = self.connection.getresponse()
                contents = response.read()
                if contents[0:6] == "<html>":
                    raise Exception("Error retrieving %s." % os.path.split(self.url)[1])
                if attempts_left != self.attempts:
                    print('Success.')
                return contents
            except Exception, e:
                print('Error retrieving {0} {1}.'.format(os.path.split(self.url)[1], resource))
                print(str(e))
                print(traceback.format_exc())
                attempts_left -= 1
                if attempts_left > 0:
                    print('Retrying.')
                    self._close()
                    time.sleep(2)
        raise Exception('get {0} failed'.format(resource))


    @classmethod
    def get_resource(cls, url, resource):
        c = cls(url)
        return c.get(resource)
