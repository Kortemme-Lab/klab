#!/usr/bin/python
# Concat a list of pdb files together, separated by MODEL X & ENDMDL records. X is set to 10
# for the 10th pdb file read in and the file name is stored in 'REMARK 99'.
# If run multiple times with the same output file, the pdbs are appended to the end
# and the model number is incremented from the previous last model number. This is
# especially useful for using long list of files with xargs

# Usage: concat-mult-pdbs.py <file to output models to> <pdb files or pdb.lst files>



import sys, os.path
from util import *

set_verbose(0)
out_pdb_fn, fns = sys.argv[1], sys.argv[2:]

# start numbering the models at 1 or 1 plus the current last model
model_num = 0
if os.path.exists(out_pdb_fn):
    model_num = int(run("awk '/^MODEL/ {print $2}' %s | tail -1" % out_pdb_fn).split()[1])

print "Starting model num: %s" % model_num

print "Combining files:"
pdb_fns = []
for fn in fns:
    print "   ", fn
    if fn.endswith(".lst"): 
        pdb_fns += readlines([fn])
    else:
	pdb_fns += [fn]

print

out_fh = open(out_pdb_fn, "a")
sys.stdout = out_fh

for pdb_fn in pdb_fns:
    model_num += 1

    print "MODEL %d" % model_num
    print "REMARK  99 FILE %s" % pdb_fn

    if pdb_fn.endswith(".pdb.gz"):
	cat_cmd = "zcat"
    else:
	cat_cmd = "cat"

    print run("%s %s | egrep '^(ATOM|HETATM|REMARK) '" % (cat_cmd, pdb_fn))
    print "ENDMDL"

out_fh.close()
