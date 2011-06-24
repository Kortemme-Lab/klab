import sys
from optparse import OptionParser
import os.path, numpy
import util, pool, PDBlite

# The "Mean Cα difference distance values" pdb is generated with the following:
   CA_DIST_DIFF_MATRIX_FILE = "ca_dist_difference_matrix.dat"
   CA_DIST_DIFF_BFACT_PDB_FILE = "ca_dist_difference_bfactors.pdb"
   starting_pdb = PDBlite.PDB(open(starting_pdb_file).readlines())
   <ensemble.lst = a file which is a list of PDBs>
   br_traj = PDBlite.PDBTrajectory("ensemble.lst")
   open(CA_DIST_DIFF_MATRIX_FILE, "w").write(br_traj.get_diff_dist_matrix_str())

   # calculate the RMSDs at each residue
   rmsds = br_traj.calc_rmsd_over_sequence(starting_pdb, ["CA"])

   # load the CA distance difference results
   A = numpy.loadtxt(CA_DIST_DIFF_MATRIX_FILE)
   vals_str = util.run("grep MEAN %(CA_DIST_DIFF_MATRIX_FILE)s | tr ' ' '\t' | cut -f4-" % vars()).replace("\t",",")
   ca_dist_diff_means = numpy.array(map(float, vals_str.split(",")))

   # add CA-distance difference values into bfactor of a new pdb file
   open(CA_DIST_DIFF_BFACT_PDB_FILE, 'w').write(starting_pdb.get_pdb_set_bfactor_str(list(ca_dist_diff_means)))

# The "Pairwise Cα difference distance values" graph is generated with the following:
# (The variable A is created above)

   res_nums = [int(res.res_num) for res in starting_pdb.iter_residues()]
   nres = len(res_nums)
   res_num_strs = map(str, res_nums)

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

