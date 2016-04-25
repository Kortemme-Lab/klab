#!/usr/bin/python
# encoding: utf-8
"""
fsio.py
For common file I/O functions

Created by Shane O'Connor 2013
"""
import os
import tempfile
import gzip
import stat
import StringIO

# Note: I should use the same convention for all methods here but read_file differs. We should really support the whole fopen cstdio spec.

permissions755SGID = stat.S_ISGID | stat.S_IRUSR | stat.S_IWUSR | stat.S_IXUSR | stat.S_IRGRP | stat.S_IXGRP | stat.S_IROTH | stat.S_IXOTH

def read_file(filepath, binary = False):
    if binary:
        with open(filepath, 'rb') as f: contents = f.read()
    elif filepath.endswith('.gz'):
        f = gzip.open(filepath, 'r') # with...as fails for gzip.open in older versions of Python (e.g. v2.6.6)
        contents = f.read()
        f.close()
    else:
        with open(filepath, 'r') as f: contents = f.read()
    return contents


def get_file_lines(filepath):
    return read_file(filepath, binary = False).splitlines()


def read_file_lines(filepath, binary = False):
    # todo: deprecated. Replace this with get_file_lines
    return read_file(filepath, binary = binary).split('\n')


def write_file(filepath, contents, ftype = 'w'):
    output_handle = open(filepath, ftype)
    output_handle.write(contents)
    output_handle.close()


def open_temp_file(path, ftype = 'w', suffix = '', prefix = ''):
    F, fname = tempfile.mkstemp(dir = path, suffix = suffix, prefix = prefix)
    output_handle = os.fdopen(F, ftype)
    return output_handle, fname


def write_temp_file(path, contents, ftype = 'w', suffix = '', prefix = ''):
    output_handle, fname = open_temp_file(path, ftype = ftype, suffix = suffix, prefix = prefix)
    if contents:
        output_handle.write(contents)
    output_handle.close()
    return fname


def create_temp_755_path(temproot, suffix = None):
    if suffix:
        path = tempfile.mkdtemp("_%s" % suffix, dir = temproot)
    else:
        path = tempfile.mkdtemp(dir = temproot)
    if not os.path.isdir(path):
        raise os.error
    global permissions755SGID
    os.chmod(path, permissions755SGID)
    return path


def create_scratch_path():
    return create_temp_755_path('/scratch')


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


def read_gzip_in_memory(gzip_contents):
    cf = StringIO.StringIO()
    cf.write(gzip_contents)
    cf.seek(0)
    df = gzip.GzipFile(fileobj = cf, mode='rb')
    contents = df.read()
    df.close()
    return contents
