#!/usr/bin/python2.4

# Updated 1/14/09 (gfriedla): to add plotting functionality for CA dist diff matrices.
# Updated 1/21/09 (gfriedla): to add RMSD calc
# Updated 1/26/09 (gfriedla): process jobs using the condor cluster
# Updated 01/06/09 (flolauck): modified for the server environment

# Make backrub structures and run design on them, then analyze the results with sequence logos and CA difference distance matrices.
# It's recommended that flexible termini are truncated because otherwise they will dominate the CA-difference distance flexibility analysis.

# This script should be run in a new uniquely named directory.

# USAGE: ensdes2.py --help
# REQUIRES: python packages (numpy, matplotlib, weblogo+patch code.google.com/p/weblogo/, corebio code.google.com/p/corebio/, util+PDBlite gfriedla-custom)

# OUTPUT:
#   Core residues file:                                core.txt
#   Ensemble pdb file:                                 ensemble.pdb
#   CA distance diff values mapped onto the png file:  ca_dist_difference_bfactors.pdb
#   CA distance diff matrix and mean value plots:      ca_dist_difference_1D_plot.png, ca_dist_difference_2D_plot.png
#   RMSD plot:                                         rmsd_plot.png
#   All and core only sequences:                       designs.fasta, designs_core.fasta
#   All and core only sequence profile logo plot:      logo.png, logo_core.png
#   All and core only sequence populations tables:     seq_pop.txt, seq_pop_core.txt

import sys

sys.path.insert(0, "../../common/")
from RosettaProtocols import RosettaBinaries


CORERES_CBETA_NB_CUTOFF = 18
AAS = list("ACDEFGHIKLMNPQRSTVWY")

BACKRUB_DIR = "backrubs"
DESIGN_DIR = "designs"


# needed files
#ROSETTA_BIN = "/kortemmelab/home/gfriedla/bin/ros_090907.gcc"

# output files
DESIGNS_FASTA_FILE = "designs.fasta"
DESIGNS_CORERES_FASTA_FILE = "designs_core.fasta"
DESIGNS_SEQ_POP_FILE = "seq_pop.txt"
DESIGNS_CORERES_SEQ_POP_FILE = "seq_pop_core.txt"
DESIGNED_PDBS_LIST_FILE = "designed_pdbs.lst" # the file containing the list of designed pdb files
BR_PDBS_LIST_FILE = "ensemble.lst"            # the file containing the list of backrub files
BR_PDBS_FILE = "ensemble.pdb"                 # the file containing the pdbs in NMR pdb format
LOGO_FILE = "logo.png"
LOGO_CORERES_FILE = "logo_core.png"
CA_DIST_DIFF_MATRIX_FILE = "ca_dist_difference_matrix.dat"
RMSD_PLOT_FILE = "rmsd_plot.png"
CA_DIST_DIFF_2D_PLOT_FILE = "ca_dist_difference_2D_plot.png"
CA_DIST_DIFF_1D_PLOT_FILE = "ca_dist_difference_1D_plot.png"
CA_DIST_DIFF_BFACT_PDB_FILE = "ca_dist_difference_bfactors.pdb"
CORERES_FILE = "core.txt"

from optparse import OptionParser
import os.path, numpy
#todo: Argh! Get rid of this!
sys.path.append("/kortemmelab/home/gfriedla/scripts/python")

import util, pool, PDBlite

# takes a list of sequence strings and retunrs an array of populations of each AA over the sequence (nres x 20)
def calc_seq_populations(sequences):
    nseq = len(sequences)
    nres = len(sequences[0])
    for seq in sequences: assert(len(seq) == nres)

    assert(len(AAS) == 20)
    aa_map = {}
    for aa in AAS: aa_map[aa] = AAS.index(aa)
    
    pop_mat = numpy.zeros((nres, 20))
    for res_num in range(nres):
        for seq_num in range(nseq):
            aa_ind = aa_map[sequences[seq_num][res_num]]
            pop_mat[res_num, aa_ind] += 1
    pop_mat /= nseq
    return pop_mat
    
# parse and initialize parameters
try:
    usage = "usage: %prog bin_directory starting_pdb_file num_structs max_segment_length num_steps temp num_designs_per_struct [options]"
    parser = OptionParser(usage)
    parser.add_option("--verbose", type="int", default=0, help="verbose level")
    parser.add_option("--debug", action="store_true", default=False, help="Don't run the long operations; assume they've run already")
    parser.add_option("--cluster", action="store_true", default=False, help="Use the Kortemme Lab condor cluster")
    (options, args) = parser.parse_args()
    
    DEBUG = options.debug
    bin_directory, starting_pdb_file, num_structs, maxres, num_steps, kt, num_designs_per_bb = args
    
    BIN_DIR = bin_directory
    SCRIPT_DIR = sys.path[0]
    sys.path.append(BIN_DIR)
    ROSETTA_BIN = "%s/%s" % (BIN_DIR, RosettaBinaries["ensemble"]["backrub"])
    PATHS_FILE = "%s/paths.txt" % BIN_DIR
    MAKE_RESFILE_SCRIPT = "%s/makeResfile.pl" % SCRIPT_DIR
    PDBLITE_SCRIPT = "%s/PDBlite.py" % SCRIPT_DIR
    CONCAT_PDB_SCRIPT = "%s/concat-mult-pdbs.py" % SCRIPT_DIR
    PARSE_NEIGHBOR_SCRIPT = "%s/parse_neighbors.py" % SCRIPT_DIR
    
    starting_pdb_file = os.path.abspath(starting_pdb_file)
    ens_name = util.parse_pdbname(starting_pdb_file)
    num_structs, maxres, num_steps, kt, num_designs_per_bb = int(num_structs), int(maxres), int(num_steps), float(kt), int(num_designs_per_bb)
    num_designs = num_structs * num_designs_per_bb
    
    # get the residue numbers
    starting_pdb = PDBlite.PDB(open(starting_pdb_file).readlines()) # hier gehts schief
    res_nums = [int(res.res_num) for res in starting_pdb.iter_residues()]
    nres = len(res_nums)
    res_num_strs = map(str, res_nums)
    print "Res nums: ", res_nums
    
    if options.cluster:
        cmdPool = pool.Pool("ensdes_pool", mem_required = 2000)
except Exception:
    if options.verbose >=1: util.print_last_exception()
    parser.error("Invalid number or type of arguments: %s")

# find the core residues
try:
    util.mkdir_cd("repack")
    util.run("rm -f *pdb; %(ROSETTA_BIN)s xx %(ens_name)s _ -design -onlypack -s %(starting_pdb_file)s -read_all_chains -paths %(PATHS_FILE)s > repack.log" % vars()).split()
    repacked_pdb_files = util.run("find $PWD -noleaf  -name '*pdb'" % vars()).split()
    assert(len(repacked_pdb_files) == 1)
    repacked_pdb_file = repacked_pdb_files[0]
    num_neighbors = map(int, util.run("%(PARSE_NEIGHBOR_SCRIPT)s %(repacked_pdb_file)s" % vars()).strip().split())
    assert(len(res_nums) == len(num_neighbors))
    coreres = []
    for res_num, neighbors in zip(res_nums, num_neighbors):
        if neighbors >= 18: coreres.append(res_num)
    coreres_str = ":".join(map(str, coreres))
    if options.verbose >=1: print "Found core residues: ", coreres
    util.cd("..")
    util.run("echo %s > %s" % (" ".join(map(str, coreres)), CORERES_FILE))
except Exception, e:
    if options.verbose >=1: util.print_last_exception()
    raise Exception("Error finding core residues: %s" % e)
    
# generate backrub ensemble and check if they were created correctly
try:
    # make backrub resfile
    br_resfile = os.path.abspath(ens_name + "_br.res")
    util.run("%(MAKE_RESFILE_SCRIPT)s -pdb %(starting_pdb_file)s | sed 's/NATRO /NATAAB/' > %(br_resfile)s" % vars())
        
    backrub_log = os.path.abspath("backrub.log")
    util.mkdir_cd(BACKRUB_DIR)
    
    if not DEBUG:
        if options.cluster:
            for pdb_num in range(num_structs):
                util.mkdir_cd(str(pdb_num))
                cmd_one = "%(ROSETTA_BIN)s br 0001 _ -paths %(PATHS_FILE)s -pose1 -backrub_mc -fa_input -find_disulf -norepack_disulf -s %(starting_pdb_file)s -resfile %(br_resfile)s -ex1 -ex2 -extrachi_cutoff 0 -ntrials %(num_steps)d -max_res %(maxres)d -only_bb .5 -only_rot .5 -nstruct 1 -mc_temp %(kt)f -bond_angle_params bond_angle_amber_rosetta -read_all_chains -use_pdb_numbering >& %(backrub_log)s" % vars()
                cmdPool.queue(cmd_one)
                util.cd("..")
            cmdPool.run()
        else:
            cmd_mult = "%(ROSETTA_BIN)s br 0001 _ -paths %(PATHS_FILE)s -pose1 -backrub_mc -fa_input -find_disulf -norepack_disulf -s %(starting_pdb_file)s -resfile %(br_resfile)s -ex1 -ex2 -extrachi_cutoff 0 -ntrials %(num_steps)d -max_res %(maxres)d -only_bb .5 -only_rot .5 -nstruct %(num_structs)d -mc_temp %(kt)f -bond_angle_params bond_angle_amber_rosetta -read_all_chains -use_pdb_numbering >& %(backrub_log)s" % vars()
            util.run(cmd_mult)
    util.run("find $PWD -noleaf -name 'br*.pdb' | grep -v last | xargs rm -f") # remove low and initial backrub output files
    util.run("find $PWD -noleaf -name 'br*last*.pdb' | xargs gzip -f") # compress the pdb files for storage
    util.cd("..")

    util.run("find $PWD/%(BACKRUB_DIR)s -noleaf -name 'br*last*.pdb.gz' | sort > %(BR_PDBS_LIST_FILE)s; %(CONCAT_PDB_SCRIPT)s %(BR_PDBS_FILE)s %(BR_PDBS_LIST_FILE)s" % vars())
    br_files = util.run("cat %(BR_PDBS_LIST_FILE)s" % vars()).split()
    if options.verbose >= 2: print "Backrub files:\n  " + "\n  ".join(br_files) + "\n"
    assert(len(br_files) == num_structs)
except Exception, e:
    if options.verbose >=1: util.print_last_exception()
    raise Exception("Error creating Backrub structures: %s" % e)

# design on the resulting ensemble
try:
    # make design resfile
    des_resfile = os.path.abspath(ens_name + "_des.res")
    util.run("%(MAKE_RESFILE_SCRIPT)s -pdb %(starting_pdb_file)s | sed 's/NATRO/ALLAA/' > %(des_resfile)s" % vars())

    util.mkdir_cd(DESIGN_DIR)
    for br_file_num, br_file in zip(range(num_structs), br_files):
        br_file = br_file.replace(".gz", "") # rosetta stupidly tries to add another .pdb onto the end if the filename ends in .gz...
        br_file_name = util.parse_pdbname(br_file)
        br_logfile = os.path.abspath(br_file_name + "_" + str(br_file_num) + ".log")
        if not DEBUG:
            util.mkdir_cd(str(br_file_num))
            cmd = "%(ROSETTA_BIN)s -design -fixbb -read_all_chains -fa_input -ex2 -ex1aro -ex1 -try_both_his_tautomers -ndruns %(num_designs_per_bb)d -resfile %(des_resfile)s -s %(br_file)s -paths %(PATHS_FILE)s -output_pdb %(br_file_name)s -output_pdb_gz -use_pdb_numbering > %(br_logfile)s" % vars()
            if options.cluster: cmdPool.queue(cmd)
            else: util.run(cmd)
            util.cd("..")
    if options.cluster: cmdPool.run()
    design_pdb_files = util.run("find $PWD/ -noleaf -name '*.pdb.gz'" % vars()).split()
    util.cd("..")
    if options.verbose >= 2: print "Design files:\n  " + "\n  ".join(design_pdb_files) + "\n"
    assert(len(design_pdb_files) == num_designs)
    open(DESIGNED_PDBS_LIST_FILE, "w").write("\n".join(design_pdb_files)+"\n")

    # output the sequences to fasta files and reformat the sequence names to something user-intelligible
    designs_traj = PDBlite.PDBTrajectory(DESIGNED_PDBS_LIST_FILE)
    open(DESIGNS_FASTA_FILE, 'w').write(designs_traj.get_fasta_str().replace("br0001last_","Structure-").replace("_","; Sequence-").replace(".pdb.gz",""))
    open(DESIGNS_CORERES_FASTA_FILE, 'w').write(designs_traj.get_fasta_str(coreres).replace("br0001last_","Structure-").replace("_","; Sequence-").replace(".pdb.gz",""))

    sequences = util.run("cat %(DESIGNS_FASTA_FILE)s | grep -v \>" % vars()).split("\n")
    sequences_core = util.run("cat %(DESIGNS_CORERES_FASTA_FILE)s | grep -v \>" % vars()).split("\n")
    open(DESIGNS_SEQ_POP_FILE, 'w').write(util.arr2str2(calc_seq_populations(sequences), precision=2, length=4, col_names=AAS, row_names=map(str, res_nums)))
    try:
      open(DESIGNS_CORERES_SEQ_POP_FILE, 'w').write(util.arr2str2(calc_seq_populations(sequences_core), precision=2, length=4, col_names=AAS, row_names=map(str, coreres)))
    except:
      pass
except Exception, e:
    if options.verbose >=1: util.print_last_exception()
    raise Exception("Error creating design files: %s" % e)

# make the ca-distance difference matrix, plot and output in pdb file format
try:
    br_traj = PDBlite.PDBTrajectory(BR_PDBS_LIST_FILE)
    open(CA_DIST_DIFF_MATRIX_FILE, "w").write(br_traj.get_diff_dist_matrix_str())
    #util.run("python %(PDBLITE_SCRIPT)s -t %(BR_PDBS_LIST_FILE)s --diff_dist_matrix > %(CA_DIST_DIFF_MATRIX_FILE)s" % vars())

    # calcualte the RMSDs at each residue
    #pdb_traj = PDBlite.PDBTrajectory(BR_PDBS_LIST_FILE)
    rmsds = br_traj.calc_rmsd_over_sequence(starting_pdb, ["CA"])

    # load the CA distance difference results
    A = numpy.loadtxt(CA_DIST_DIFF_MATRIX_FILE)
    vals_str = util.run("grep MEAN %(CA_DIST_DIFF_MATRIX_FILE)s | tr ' ' '\t' | cut -f4-" % vars()).replace("\t",",")
    ca_dist_diff_means = numpy.array(map(float, vals_str.split(",")))

    # add CA-distance difference values into bfactor of a new pdb file
    open(CA_DIST_DIFF_BFACT_PDB_FILE, 'w').write(starting_pdb.get_pdb_set_bfactor_str(list(ca_dist_diff_means)))
                                
    #starting_pdb_list_file = "starting_pdb.lst"
    #open(starting_pdb_list_file, "w").write(starting_pdb_file)
    #util.run("python %(PDBLITE_SCRIPT)s -t %(starting_pdb_list_file)s --set_bfactors='%(vals_str)s' > %(CA_DIST_DIFF_BFACT_PDB_FILE)s" % vars())

    # init plotting
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

except Exception, e:
    if options.verbose >=1: util.print_last_exception()
    raise Exception("Error running CA distance difference analysis: %s" % e)

# make the sequence logos using the berkeley weblogo library
try:
    from weblogolib import *
    seqs = read_seq_data(open(DESIGNS_FASTA_FILE))
    logo_data = LogoData.from_seqs(seqs)
    logo_options = LogoOptions()
    logo_options.title = "Sequence profile for %(num_designs)s designs on %(num_structs)s Backrub backbones of '%(ens_name)s'" % vars()
    logo_options.number_interval = 1
    logo_options.color_scheme = std_color_schemes["chemistry"]
    logo_options.annotate = res_nums
    logo_format = LogoFormat(logo_data, logo_options)
    png_print_formatter(logo_data, logo_format, open(LOGO_FILE, 'w'))

    seqs = read_seq_data(open(DESIGNS_CORERES_FASTA_FILE))
    logo_data = LogoData.from_seqs(seqs)
    logo_options = LogoOptions()
    logo_options.number_interval = 1
    logo_options.color_scheme = std_color_schemes["chemistry"]
    logo_options.annotate = coreres
    logo_options.title = "Core residue sequence profile for %(num_designs)s designs on %(num_structs)s Backrub backbones of '%(ens_name)s'" % vars()
    logo_format = LogoFormat(logo_data, logo_options)
    png_print_formatter(logo_data, logo_format, open(LOGO_CORERES_FILE, 'w'))

except Exception, e:
    if options.verbose >=1: util.print_last_exception()
    raise Exception("Error creating logo plot: %s" % e)

