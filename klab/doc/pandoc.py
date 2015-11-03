#!/usr/bin/python
# encoding: utf-8
"""
pandoc.py
Very simple wrappers around pandoc.

Created by Shane O'Connor 2015.
"""

import sys
import os
import platform
import commands
import shlex

if __name__ == '__main__':
    sys.path.insert(0, '../..')

from klab import colortext
from klab.fs.fsio import open_temp_file, read_file
from klab.process import Popen as _Popen



### Check for the necessary pandoc software
missing_pandoc_message = '''\n\nThis module requires pandoc to be installed. This software appears to be missing on your machine. On Ubuntu, you
can install the software as follows:
  sudo apt-get install pandoc

Otherwise, please refer to the official website: http://johnmacfarlane.net/pandoc/.
'''
if os.name == 'posix' or 'Linux' in platform.uname():
    if commands.getstatusoutput('which pandoc')[0] != 0:
        raise colortext.Exception(missing_pandoc_message)
else:
    raise Exception("Please extend this check to work on your architecture. At present, it only works on Linux.")


### API


def rst_to_html(input_file):
    return pandoc(input_file, 'rst', 'html')


def pandoc(input_file, from_format, to_format):
    assert(os.path.exists(input_file))
    pandoc_output_handle, pandoc_output_filename = open_temp_file('/tmp')
    p = _Popen('.', shlex.split('pandoc %(input_file)s -f %(from_format)s -t %(to_format)s -o %(pandoc_output_filename)s' % locals()))
    if p.errorcode:
        raise Exception('An error occurred while calling pandoc:\n%s' % p.stderr)
    else:
        return read_file(pandoc_output_filename)

