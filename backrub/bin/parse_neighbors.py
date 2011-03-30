#!/usr/bin/python

# parse the number of neighbors from the pdb output of a rosetta run

import sys

fn = sys.argv[1]

# e.g.
#  1      MET 15
#  5   A  LYS  7  
look_for_neighbor = False
for line in open(fn):
    if line.startswith("res chain aa nb"):
        look_for_neighbor = True
        continue
    elif line.startswith("avgtot "): break

    if look_for_neighbor: print line[13:15],
print
    
