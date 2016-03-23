#!/bin/python 
# -*- coding: utf-8 -*-

"""
parse_unicorn_method_files.py
Parsing function for reading the METHOD section of GE Healthcare Life Sciences Unicorn 5.31 binary files. This can be useful in case it is difficult to restore the method files in the correct manner.
 
Created by Shane O'Connor 2016.
Copyright (c) 2016 Shane O'Connor. All rights reserved.
"""

import os
import unicodedata
import re
import sys

printable = set(['Lu','Ll','Lm','Lo','Lt'])
white_space = ['\t', ' ', '\n', '\r', '\f']

def filter_non_printable(sblock):
  s = ''
  for c in sblock:
    try:
      #if c in white_space:
      s += c
      #elif unicodedata.category(unicode(c)) == 'Cc':
      #   continue
      #else:
      #  s += c
    except Exception, e: 
      try:
        if unicodedata.category(c.decode('windows-1252')) in printable:
          s += c
      except: raise     
  return re.sub(r'[\n]+', '\n', s)


method_start = [0x00, 0x4d, 0x45, 0x54, 0x48, 0x4f, 0x44, 0x0a] # the string "METHOD" (without quotes), with a null prefix and newline suffix
method_end = [0x0a, 0x45, 0x4e, 0x44, 0x5f, 0x4d, 0x45, 0x54, 0x48, 0x4f, 0x44, 0x0a] # the string "END_METHOD" (without quotes), with newline prefix and suffix


def scan_directory(dirname):
  for root, dirs, files in os.walk(dirname):
    for filename in files:
      if os.path.splitext(filename)[1] == '.m01' or os.path.splitext(filename)[1] == '.m02':
        print('\n\n** {0} **\n'.format(os.path.relpath(os.path.join(root, filename), dirname)))
        filepath = os.path.join(root, filename)        

        with open(filepath, 'rb') as fp:
            bytes = map(ord, fp.read())
    
        start_index, end_index = [], []
        for x in xrange(len(bytes) - len(method_start) + 1):
            if bytes[x:x+len(method_start)] == method_start:
                start_index.append(x)
            elif bytes[x:x+len(method_end)] == method_end:
                end_index.append(x)
        if len(start_index) == 1 and len(end_index) == 1:
            block = bytes[start_index[0] + 1 : end_index[0] + len(method_end)]
            block = ''.join(map(chr, block))
            print(block.strip())
        else:
            print('FAILED TO PARSE.')
            sys.exit(1)

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print('\n\nUsage: {0} <path_to_Local/Fil/Default/Method_directory>.\n'.format(sys.argv[0]))
    else:
        dirpath = sys.argv[1]
        assert(os.path.exists(dirpath))
        assert(os.path.split(dirpath)[1] == 'Method')
        scan_directory(dirpath)


