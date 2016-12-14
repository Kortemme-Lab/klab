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

import string
import sys
import os

def renumber_atoms(lines):
    '''
    Takes in a list of PDB lines and renumbers the atoms appropriately
    '''
    new_lines = []
    current_number = 1
    for line in lines:
        if line.startswith('ATOM') or line.startswith('HETATM'):
            new_lines.append(
                line[:6] + string.rjust('%d' % current_number, 5) + line[11:]
            )
            current_number += 1
        else:
            if line.startswith('TER'):
                current_number += 1
            new_lines.append(line)
    return new_lines

def clean_alternate_location_indicators(lines):
    '''
    Keeps only the first atom, if alternated location identifiers are being used
    Removes alternate location ID charactor
    '''
    new_lines = []
    previously_seen_alt_atoms = set()
    for line in lines:
        if line.startswith('ATOM'):
            alt_loc_id = line[16]
            if alt_loc_id != ' ':
                atom_name = line[12:16].strip()
                res_name = line[17:20].strip()
                chain = line[21]
                resnum = long( line[22:26].strip() )
                loc_tup = (atom_name, res_name, chain, resnum)
                if loc_tup in previously_seen_alt_atoms:
                    # Continue main for loop
                    continue
                else:
                    previously_seen_alt_atoms.add( loc_tup )
                    line = line[:16] + ' ' + line[17:]
        new_lines.append(line)
    return new_lines

if __name__ == '__main__':
    assert( len(sys.argv) >= 2 )
    pdb_path = sys.argv[1]
    assert os.path.isfile(pdb_path)
    with open(pdb_path, 'r') as f:
        lines = f.readlines()

    for arg in sys.argv[2:]:
        if arg == 'clean_alternate_location':
            lines = clean_alternate_location_indicators(lines)
        elif arg == 'renumber_atoms':
            lines = renumber_atoms(lines)
        else:
            raise Exception('Unrecognized argument: ' + arg)

    new_pdb_path = os.path.join(
        os.path.dirname(pdb_path),
        'cleaned-' + os.path.basename(pdb_path)
    )

    with open(new_pdb_path, 'w') as f:
        for line in lines:
            f.write(line)
