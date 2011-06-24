#!/usr/bin/python

# parse the number of neighbors from the pdb output of a rosetta run

import sys
import re

fn = sys.argv[1]

# e.g.
#  1      MET 15
#  5   A  LYS  7  
look_for_neighbor = False
neighbor_re = re.compile("^\s*\d+\s+[A-Z]\s+[A-Z]{3}\s+(\d+).*", re.IGNORECASE)
for line in open(fn):
    if line.startswith("res chain aa nb"):
        look_for_neighbor = True
        continue
    elif line.startswith("avgtot "):
        break

    if look_for_neighbor:
        n = neighbor_re.match(line)
        if n:
            print(n.group(1)),
print
    
