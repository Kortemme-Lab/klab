####!/usr/bin/python2.4
#### -*- coding: iso-8859-15 -*-

# The "Mean Cα difference distance values" pdb is generated with the following:

import sys
from optparse import OptionParser
import os.path, numpy
import util, pool, PDBlite
import traceback
import time
# Added 05/19/11
starting_pdb_file = sys.argv[1]
#experimental_list = sys.argv[1]
ensemble_list = sys.argv[2]
prefix = sys.argv[3] 

if len(sys.argv) > 4 and sys.argv[4] == '-d':
	util.DEBUGMODE = True
else: 
	util.DEBUGMODE = False

F = open(util.logfile, "w")
F.close()   

starttime = time.time()

#starting_pdb_file = "1A8G.pdb"
util.MSG("\nStarting PDB is: %s" % (starting_pdb_file))
util.MSG("Ensemble list is: %s" % (ensemble_list))
util.MSG("Prefix is: %s" % (prefix))

CA_DIST_DIFF_MATRIX_FILE = "ca_dist_difference_matrix-%s.dat" % (prefix)
CA_DIST_DIFF_BFACT_PDB_FILE = "ca_dist_difference_bfactors-%s.pdb" % (prefix)
RMSD_PLOT_FILE = "rmsd_plot-%s.png" % (prefix)
CA_DIST_DIFF_2D_PLOT_FILE = "ca_dist_difference_2D_plot-%s.png" % (prefix)
CA_DIST_DIFF_1D_PLOT_FILE = "ca_dist_difference_1D_plot-%s.png" % (prefix)

util.PRINTHEAP("before loading starting pdb")

starting_pdb = PDBlite.PDB(open(starting_pdb_file).readlines())

util.PRINTHEAP("after loading starting pdb")

br_traj = PDBlite.PDBTrajectory(ensemble_list)

open(CA_DIST_DIFF_MATRIX_FILE, "w").write(br_traj.get_diff_dist_matrix_str())

util.PRINTHEAP("after computing ca dist diff matrix")
# calculate the RMSDs at each residue
# 05/19/11: What datatype is rmsds? rmsds is an array of size ? --Rocco
rmsds = None
try:
    # 06/26/11: Added the call to Shane's new function that should fix the memory issue.
    rmsds2 = br_traj.calc_CA_rmsd_over_sequence_lessmem(starting_pdb)
    util.PRINTHEAP("after computing ca dist diff matrix")
    rmsds = rmsds2

except Exception, e:
    util.ERROR("Exception computing calc_rmsd_over_sequence")
    util.PRINTHEAP("Heap:")
    util.ERROR(e)
    util.ERROR(traceback.format_exc())
    sys.exit(1)

#print "length of rmsds",len(rmsds),"\n"

util.PRINTHEAP("after calc_rmsd_over_sequence")

# load the CA distance difference results
A = numpy.loadtxt(CA_DIST_DIFF_MATRIX_FILE)

util.PRINTHEAP("after loadtxt(CA_DIST_DIFF_MATRIX_FILE")

vals_str = util.run("grep MEAN %(CA_DIST_DIFF_MATRIX_FILE)s | tr ' ' '\t' | cut -f4-" % vars()).replace("\t",",")

util.PRINTHEAP("after grep MEAN %(CA_DIST_DIFF_MATRIX_FILE)")

ca_dist_diff_means = numpy.array(map(float, vals_str.split(",")))

util.PRINTHEAP("after ca_dist_diff_means")

#print "length of ca_dist_diff_means: %d" % (len(ca_dist_diff_means))
#sys.exit()

# add CA-distance difference values into bfactor of a new pdb file
open(CA_DIST_DIFF_BFACT_PDB_FILE, 'w').write(starting_pdb.get_pdb_set_bfactor_str(list(ca_dist_diff_means)))

util.PRINTHEAP("CA_DIST_DIFF_BFACT_PDB_FILE")

# The "Pairwise Cα difference distance values" graph is generated with the following:
# (The variable A is created above)

res_nums = [int(res.res_num) for res in starting_pdb.iter_residues()]
nres = len(res_nums)
res_num_strs = map(str, res_nums)

util.PRINTHEAP("STARTING MATPLOT")

import matplotlib
matplotlib.use('Agg') # so plots aren't made interactively
import pylab
matplotlib.rcParams['xtick.direction'] = 'out'
matplotlib.rcParams['ytick.direction'] = 'out'

# now plot 2D
pylab.figure()
ax = pylab.subplot(111)
plot2D = pylab.imshow(A, cmap=pylab.cm.hot, origin='lower')
pylab.xticks(numpy.arange(nres), res_num_strs) # add ticks for all residues
pylab.yticks(numpy.arange(nres), res_num_strs) # add ticks for all residues

pylab.xlabel('Residue')
pylab.ylabel('Residue')
cb = pylab.colorbar(plot2D)
cb.set_label('C-alpha distance difference value')
xlabels, ylabels = ax.get_xticklabels(), ax.get_yticklabels()
pylab.setp(xlabels, rotation=-90, fontsize=5)
pylab.setp(ylabels, fontsize=5)
pylab.savefig(CA_DIST_DIFF_2D_PLOT_FILE, dpi=300)

# The "Mean Cα difference distance values" graph is generated with the following:

# plot 1D
pylab.figure()
ax = pylab.subplot(111)
plot1D = pylab.plot(ca_dist_diff_means)
pylab.xticks(numpy.arange(nres), res_num_strs) # add ticks for all residues
pylab.xlabel('Residue')
pylab.ylabel('C-alpha distance difference mean value')
xlabels = ax.get_xticklabels()
pylab.setp(xlabels, rotation=-90, fontsize=5)
pylab.savefig(CA_DIST_DIFF_1D_PLOT_FILE, dpi=300)

# The "Mean RMSD of Cα atoms for individual residues" graph is generated with the following:

# plot rmsds
pylab.figure()
ax = pylab.subplot(111)
plot = pylab.plot(rmsds)
pylab.xticks(numpy.arange(nres), res_num_strs) # add ticks for all residues
pylab.xlabel('Residue')
pylab.ylabel('RMSD (Angstroms)')
xlabels = ax.get_xticklabels()
pylab.setp(xlabels, rotation=-90, fontsize=5)
pylab.savefig(RMSD_PLOT_FILE, dpi=300)

util.PRINTHEAP("Before exit")
print("Total time: %.2fs" % (time.time() - starttime))
