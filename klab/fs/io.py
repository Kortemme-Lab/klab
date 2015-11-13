#!/usr/bin/python
# encoding: utf-8
"""
io.py
For common file I/O functions
"""
import os
import tempfile
import gzip

# Note: I should use the same convention for all methods here but read_file differs. We should really support the whole fopen cstdio spec.

def sanitize_filename(filename):
    valid_chars = '-_.abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
    return ''.join(c for c in filename if c in valid_chars)

def read_file(filepath, binary = False):
    print filepath
    if binary:
        output_handle = open(filepath,'rb')
    elif filepath.endswith('.gz'):
        output_handle = gzip.open(filepath,'r')
    else:
        output_handle = open(filepath,'r')
    contents = output_handle.read()
    output_handle.close()
    return contents

def get_file_lines(filepath):
    return read_file(filepath, binary = False).splitlines()

def write_file(filepath, contents, ftype = 'w'):
    output_handle = open(filepath, ftype)
    output_handle.write(contents)
    output_handle.close()

def open_temp_file(path, ftype = 'w'):
    F, fname = tempfile.mkstemp(dir = path)
    output_handle = os.fdopen(F, ftype)
    return output_handle, fname

def write_temp_file(path, contents, ftype = 'w'):
    output_handle, fname = open_temp_file(path, ftype = ftype)
    output_handle.write(contents)
    output_handle.close()
    return fname

def safe_gz_unzip(contents):
    ''' Takes a file's contents passed as a string (contents) and either gz-unzips the contents and returns the uncompressed data or else returns the original contents.
        This function raises an exception if passed what appears to be gz-zipped data (from the magic number) but if gzip fails to decompress the contents.
        A cleaner method would use zlib directly rather than writing a temporary file but zlib.decompress(contents, 16+zlib.MAX_WBITS) fix did not work for me immediately and I had things to get done!'''
    if len(contents) > 1 and ord(contents[0]) == 31 and ord(contents[1]) == 139:
        #contents = zlib.decompress(contents, 16+zlib.MAX_WBITS)
        fname = write_temp_file('/tmp', contents)
        try:
            f = gzip.open(fname, 'rb')
            contents = f.read()
            f.close()
        except:
            os.remove(fname)
            raise
        return contents
    else:
        return contents
