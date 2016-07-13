#!/usr/bin/env python2
# encoding: utf-8

# The MIT License (MIT)
#
# Copyright (c) 2016 Kyle Barlow
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

# Renumbers PDBs to Rosetta numbering
import sys
import os

def renumber_pdb(pdb_path):
    new_lines = []
    new_resnum = long(0)
    last_resnum = None
    with open(pdb_path, 'r') as f:
        for line in f:
            if line.startswith('ATOM') or line.startswith('HETATM'):
                current_resnum = long( line[22:26].strip() )
                # print line[22:26]
                # print len(line[22:26])
                # print ('%d' % new_resnum).rjust(5) + '\\'
                # sys.exit()
                if last_resnum != current_resnum:
                    last_resnum = current_resnum
                    new_resnum += 1
                new_lines.append( line[:22] + ('%d' % new_resnum).rjust(4) + line[26:] )
            elif line.startswith('TER'):
                new_lines.append( line )
    with open(pdb_path + '.renumbered', 'w') as f:
        for line in new_lines:
            f.write(line.strip().ljust(80) + '\n')

if __name__ == '__main__':
    pdb_path = sys.argv[1]
    assert( os.path.isfile(pdb_path) )
    assert( '.pdb' in pdb_path )
    renumber_pdb(pdb_path)
