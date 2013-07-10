#!/usr/bin/python
# encoding: utf-8
"""
io.py
For common file I/O functions
"""
import os
import tempfile

def read_file(filepath, binary = False):
    if binary:
        output_handle = open(filepath,'rb')
    else:
        output_handle = open(filepath,'r')
    contents = output_handle.read()
    output_handle.close()
    return contents

def get_file_lines(filepath):
    return read_file(filepath, binary = False).splitlines()

def write_file(filepath, contents):
    output_handle = open(filepath,'w')
    output_handle.write(contents)
    output_handle.close()

def open_temp_file(path):
    F, fname = tempfile.mkstemp(dir = path)
    output_handle = os.fdopen(F, "w")
    return output_handle, fname

def write_temp_file(path, contents):
    output_handle, fname = open_temp_file(path)
    output_handle.write(contents)
    output_handle.close()
    return fname