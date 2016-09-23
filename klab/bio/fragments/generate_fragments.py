#!/usr/bin/python
# -*- coding: utf-8 -*-
# Created 2011-10-13 by Shane O'Connor, Kortemme Lab
# Updated 2014-03-18 by Shane O'Connor, Kortemme Lab

import sys
import os
import re
from string import join, strip
import shutil
import subprocess
import traceback
import time
from datetime import datetime
from optparse import OptionParser, OptionGroup, Option
from fnmatch import fnmatch
import glob
import getpass
import json
from utils import LogFile, colorprinter
from klab.cluster.cluster_interface import JobInitializationException

from klab import colortext
from klab.rosetta.input_files import LoopsFile, SecondaryStructureDefinition
from klab.fs.fsio import read_file, write_temp_file
from klab.bio.pdb import PDB
from klab.bio.rcsb import retrieve_pdb
from klab.general.strutil import parse_range_pairs

#################
#  Configuration

# Choose the Python classes for your type of cluster system
import hpc.SGE as ClusterEngine
#
#################


#################
#  Constants
ERRCODE_ARGUMENTS = 1
ERRCODE_CLUSTER = 2
ERRCODE_OLDRESULTS = 3
ERRCODE_CONFIG = 4
ERRCODE_NOOUTPUT = 5
ERRCODE_JOBFAILED = 6
ERRCODE_MISSING_FILES = 1
errcode = 0
#
#################


#################
#  Fragment generation pipeline configuration
make_fragments_script = "make_fragments_RAP_cluster.pl"
test_mode = False # set this to true for running quick tests on your cluster system (you will need to adapt the cluster/[engine].py code to use this argument
logfile = LogFile("make_fragments_destinations.txt") # the logfile used for querying jobs
cluster_job_name = "fragment_generation" # optional: set this to identify your jobs on the cluster
fasta_file_wildcards = '*.fasta', '*.fasta.txt', '*.fa' # optional: set this to your preferred FASTA file extensions. This is used for finding FASTA files when specifying a directory.
pdb_file_wildcards = '*.pdb', '*.pdb.gz', '*.ent' # optional: set this to your preferred PDB file extensions. This is used for finding PDB files when specifying a directory. The .ent files are contained in mirrored versions of the PDB.
input_file_wildcards = fasta_file_wildcards + pdb_file_wildcards
#
# The location of the text file containing the names of the configuration scripts
configurationFilesLocation = "make_fragments_confs.txt" # "/netapp/home/klabqb3backrub/make_fragments/make_fragments_confs.txt"
#################


class FastaException(Exception): pass

class OptionParserWithNewlines(OptionParser):
    '''Override the help section with a function which does not strip the newline characters.'''
    def format_epilog(self, formatter):
        return self.epilog


class MultiOption(Option):
    '''From http://docs.python.org/2/library/optparse.html'''
    ACTIONS = Option.ACTIONS + ("extend",)
    STORE_ACTIONS = Option.STORE_ACTIONS + ("extend",)
    TYPED_ACTIONS = Option.TYPED_ACTIONS + ("extend",)
    ALWAYS_TYPED_ACTIONS = Option.ALWAYS_TYPED_ACTIONS + ("extend",)

    def take_action(self, action, dest, opt, value, values, parser):
        if action == "extend":
            lvalue = value.split(",")
            values.ensure_value(dest, []).extend(lvalue)
        else:
            Option.take_action(self, action, dest, opt, value, values, parser)


class JobInput(object):

    def __init__(self, fasta_file, pdb_id, chain):
        self.fasta_file = fasta_file
        self.pdb_id = pdb_id
        self.chain = chain



def get_username():
    return getpass.getuser()

def write_file(filepath, contents, ftype = 'w'):
    output_handle = open(filepath, ftype)
    output_handle.write(contents)
    output_handle.close()

def parse_args():
    global errcode
    errors = []
    pdbpattern = re.compile("^\w{4}$")
    logfile_name = logfile.getName()
    script_name = os.path.split(sys.argv[0])[1]
    description = '\n' + """\
*** Help ***

The output of the computation will be saved in the output directory, along with 
the input FASTA file which is generated from the supplied FASTA file.  To admit 
queries, a log of the output directories for cluster jobs is saved in
{logfile_name} in the current directory.

The FASTA description lines must begin with '>protein_id|chain_letter'.  This 
information may optionally be followed by a '|' and more text.

There are a few caveats:

1. The underlying Perl script requires a 5-character ID for the sequence 
   identifier which is typically a PDB ID followed by a chain ID e.g. "1a2pA".  
   For this reason, our script expects FASTA record headers to have a form like
   ">xxxx|y" where xxxx is a 4-letter identifier e.g. PDB ID and y is a chain
   identifier. protein_id identifier may be longer than 4 characters and 
   chain_letter must be a single character. However, only the first 4 characters 
   of the identifier are used by the script. Any information after the chain 
   identifier must be preceded by a '|' character.

   For example, ">1A2P_001|A|some information" is a valid header but the 
   generated ID will be "1a2pA" (we convert PDB IDs to lowercase).

2. If you are submitting a batch job, the list of 5-character IDs generated 
   from the FASTA files using the method above must be unique.  For example, if 
   you have two records ">1A2P_001|A|" and "">1A2P_002|A|" then the job will 
   fail.  On the other hand, ">1A2P_001|A|" and "">1A2P_001|B|" is perfectly 
   fine and the script will output fragments for 1a2pA and 1a2pB.

3. By design, residue ID ranges are capped at chain boundaries. For example, if a
   PDB has chains A (residues 1-50), B (residues 51-100), and chain C (residues 101-
   150) and the user selects 9mers for the ranges 35-48 and 101-110 then, since none
   of the ranges overlap with chain B - even though they will when 9mers are considered -
   we will not generate any fragments for chain B. This behavior is chosen as it
   seems the most intuitive/expected.

*** Examples ***

Single-sequence fragment generation:
1: {script_name} -d results /path/to/1CYO.fasta.txt

Multi-sequence fragment generation (batch job):
2: {script_name} -d results /some/path/*.fa??? /some/other/path/

Fragment generation for a specific chain:
3: {script_name} -d results /path/to/1CYO.fasta.txt -cA

Fragment generation using a loops file applied to: a) a FASTA file; b) a PDB identifier; c) a directory of FASTA/PDB files and a PDB ID, using the short/test queue:
4a: {script_name} -d results -l input/loops_file input/fragments/0001.fasta
4b: {script_name} -d results -l input/loops_file 4un3
4c: {script_name} -d results -l input/loops_file -q short.q input/fragments 4un3

*** Example secondary structure definition file***

# Comments are allowed. A line has two columns: the first specifies the residue(s),
# the second specifies the expected secondary structure using H(elix), E(xtended/sheet),
# or L(oop). The second column is case-insensitive.
#
# A single residue, any structure
1339 HEL
# An expected helix
1354-1359 H
# A helical or sheet structure
1360,1370-1380 HE

""".format(**locals())

    parser = OptionParserWithNewlines(usage="usage: %prog [options] <inputs>...", version="%prog 1.1A", option_class=MultiOption)
    parser.epilog = description

    group = OptionGroup(parser, "Fragment generation options")
    group.add_option("-N", "--nohoms", dest="nohoms", action="store_true", help="Optional. If this option is set then homologs are omitted from the search.")
    group.add_option("-s", "--frag_sizes", dest="frag_sizes", help="Optional. A list of fragment sizes e.g. -s 3,6,9 specifies that 3-mer, 6-mer, and 9-mer fragments are to be generated. The default is for 3-mer and 9-mer fragments to be generated.")
    group.add_option("-c", "--chain", dest="chain", help="Chain used for the fragment. This is optional so long as the FASTA file only contains one chain.", metavar="CHAIN")
    group.add_option("-l", "--loops_file", dest="loops_file", help="Optional but recommended. A Rosetta loops file which will be used to select sections of the FASTA sequences from which fragments will be generated. This saves a lot of time on large sequences.")
    group.add_option("-i", "--indices", dest="indices", help="Optional. A comma-separated list of ranges. A range can be a single index or a hyphenated range. For example, '10-30,66,90-93' is a valid set of indices. The indices are used to pick out parts of the supplied sequences for fragment generation and start at 1 (1-indexed). Similarly to the loops_file option, this restriction may save a lot of computational resources. If this option is used in addition to the loops_file option then the sections defined by the indices are combined with those in the loops file.")
    group.add_option("--ss", dest="secondary_structure_file", help="Optional. A secondary structure definition file. This is used in postprocessing to filter out fragments which do not match the requested secondary structure.")
    group.add_option("--n_frags", dest="n_frags", help="Optional. The number of fragments to generate. This must be less than the number of candidates. The default value is 200.")
    group.add_option("--n_candidates", dest="n_candidates", help="Optional. The number of candidates to generate. The default value is 1000.")
    group.add_option("--add_vall_files", dest="add_vall_files", help="Optional and untested. This option allows extra Vall files to be added to the run. The files must be comma-separated.")
    group.add_option("--use_vall_files", dest="use_vall_files", help="Optional and untested. This option specifies that the run should use only the following Vall files. The files must be comma-separated.")
    group.add_option("--add_pdbs_to_vall", dest="add_pdbs_to_vall", help="Optional and untested. This option adds extra pdb Vall files to the run. The files must be comma-separated.")
    parser.add_option_group(group)

    group = OptionGroup(parser, "General options")
    group.add_option("-d", "--outdir", dest="outdir", help="Optional. Output directory relative to user space on netapp. Defaults to the current directory so long as that is within the user's netapp space.", metavar="OUTPUT_DIRECTORY")
    group.add_option("-V", "--overwrite", dest="overwrite", action="store_true", help="Optional. If the output directory <PDBID><CHAIN> for the fragment job(s) exists, delete the current contents.")
    group.add_option("-F", "--force", dest="force", action="store_true", help="Optional. Create the output directory without prompting.")
    group.add_option("-M", "--email", dest="sendmail", action="store_true", help="Optional. If this option is set, an email is sent when the job finishes or fails (cluster-dependent). WARNING: On an SGE cluster, an email will be sent for each FASTA file i.e. for each task in the job array.")
    group.add_option("-Z", "--nozip", dest="nozip", action="store_true", help="Optional, false by default. If this is option is set then the resulting fragments are not compressed with gzip. We compress output by default as this can reduce the output size by 90% and the resulting zipped files can be passed directly to Rosetta.")
    parser.add_option_group(group)

    group = OptionGroup(parser, "Cluster options")
    group.add_option("-q", "--queue", dest="queue", help="Optional. Specify which cluster queue to use. Whether this option works and what this value should be will depend on your cluster architecture. Valid arguments for the QB3 SGE cluster are long.q, lab.q, and short.q. By default, no queue is specified. This may be a single value or a comma-separated list of queues. The short.q is only allowed on its own for test runs.", metavar="QUEUE_NAME")
    group.add_option("-x", "--scratch", type="int", dest="scratch", help="Optional. Specifies the amount of /scratch space in GB to reserve for the job.")
    group.add_option("-m", "--memfree", type="int", dest="memfree", help="Optional. Specifies the amount of RAM in GB that the job will require on the cluster. This must be at least 2GB.")
    group.add_option("-r", "--runtime", type="int", dest="runtime", help="Optional. Specifies the runtime in hours that the job will require on the cluster.")
    parser.add_option_group(group)

    group = OptionGroup(parser, "Querying options")
    group.add_option("-K", "--check", dest="check", help="Optional, needs to be fixed for batch mode. Query whether or not a job is running. It if has finished, query %s and print whether the job was successful." % logfile.getName(), metavar="JOBID")
    group.add_option("-Q", "--query", dest="query", action="store_true", help="Optional, needs to be fixed for batch mode. Query the progress of the cluster job against %s and then quit." % logfile.getName())
    parser.add_option_group(group)

    parser.set_defaults(outdir = os.getcwd())
    parser.set_defaults(overwrite = False)
    parser.set_defaults(nohoms = False)
    parser.set_defaults(force = False)
    parser.set_defaults(query = False)
    parser.set_defaults(sendmail = False)
    parser.set_defaults(queue = [])
    parser.set_defaults(nozip = False)
    parser.set_defaults(scratch = 1)
    parser.set_defaults(memfree = 40)
    parser.set_defaults(runtime = 6)
    parser.set_defaults(frag_sizes = '3,9')
    parser.set_defaults(n_frags = '200')
    parser.set_defaults(n_candidates = '1000')
    parser.set_defaults(add_vall_files = '')
    parser.set_defaults(use_vall_files = '')
    parser.set_defaults(add_pdbs_to_vall = '')

    (options, args) = parser.parse_args()

    username = get_username()

    # QUERY
    if options.query:
        ClusterEngine.query(logfile)
    # CHECK
    elif options.check:
        if not(options.check.isdigit()):
            errors.append("Please enter a valid job identifier.")
        else:
            # The job has finished. Check the output file.
            jobID = int(options.check)
            errors.extend(ClusterEngine.check(logfile, jobID, cluster_job_name))

    validOptions = options.query or options.check

    # Queue
    if options.queue:
        options.queue = sorted(set(options.queue.split(',')))

    # RAM / scratch
    if options.scratch < 1:
        errors.append("The amount of scratch space requested must be at least 1 (GB).")
    if options.memfree < 2:
        errors.append("The amount of RAM requested must be at least 2 (GB).")
    if options.runtime < 6:
        errors.append("The requested runtime must be at least 6 (hours).")

    # CHAIN
    if options.chain and not (len(options.chain) == 1):
        errors.append("Chain must only be one character.")

    # OUTDIR
    outpath = options.outdir
    if outpath[0] != "/":
        outpath = os.path.abspath(outpath)
    outpath = os.path.normpath(outpath)

    # Loops file
    if options.loops_file:
        if not os.path.isabs(options.loops_file):
            options.loops_file = os.path.realpath(options.loops_file)
        if not(os.path.exists(options.loops_file)):
            errors.append('The loops file %s does not exist.' % options.loops_file)

    if options.indices:
        try:
            options.indices = parse_range_pairs(options.indices, range_separator = '-')
        except Exception, e:
            errors.append('The indices argument must be a list of valid indices into the sequences for which fragments are to be generated.')

    # Secondary structure file
    if options.secondary_structure_file:
        if not os.path.isabs(options.secondary_structure_file):
            options.secondary_structure_file = os.path.realpath(options.secondary_structure_file)
        if not(os.path.exists(options.secondary_structure_file)):
            errors.append('The secondary structure definition file %s does not exist.' % options.secondary_structure_file)

    # Fragment sizes
    if options.frag_sizes:
        sizes = []
        try:
            sizes = [s.strip() for s in options.frag_sizes.split(',') if s.strip()]
            for s in sizes:
                assert(s.isdigit() and (3 <= int(s) <= 20))
            sizes = sorted(map(int, sizes))
        except Exception, e:
            errors.append('The frag_size argument must be a comma-separated list of integers between 3 and 20.')
        if not sizes:
            errors.append('The frag_sizes argument was not successfully parsed.')
        if len(sizes) != len(set(sizes)):
            errors.append('The frag_sizes argument contains duplicate values.')
        else:
            options.frag_sizes = sizes

    # n_frags and n_candidates
    if options.n_frags:
        try:
            assert(options.n_frags.isdigit())
            options.n_frags = int(options.n_frags)
        except Exception, e:
            print(traceback.format_exc())
            errors.append('The n_frags argument must be an integer.')
    if options.n_frags < 10:
        errors.append('The n_frags argument is set to 200 by default; %d seems like a very low number.' % options.n_frags)
    if options.n_candidates:
        try:
            assert(options.n_candidates.isdigit())
            options.n_candidates = int(options.n_candidates)
        except Exception, e:
            print(traceback.format_exc())
            errors.append('The n_candidates argument must be an integer.')
    if options.n_candidates < 100:
        errors.append('The n_candidates argument is set to 1000 by default; %d seems like a very low number.' % options.n_candidates)
    if options.n_frags > options.n_candidates:
        errors.append('The value of n_candidates argument must be greater than the value of n_frags.')

    if 'netapp' in os.getcwd():
        userdir = os.path.join("/netapp/home", username)
        if os.path.commonprefix([userdir, outpath]) != userdir:
            errors.append("Please enter an output directory inside your netapp space (-d option).")
    else:
        if not os.path.exists(outpath):
            createDir = options.force
            if not createDir:
                answer = ""
                colorprinter.prompt("Output path '%(outpath)s' does not exist. Create it now with 755 permissions (y/n)?" % vars())
                while answer not in ['Y', 'N']:
                    colorprinter.prompt()
                    answer = sys.stdin.readline().upper().strip()
                if answer == 'Y':
                    createDir = True
                else:
                    errors.append("Output directory '%s' does not exist." % outpath)
            if createDir:
                try:
                    os.makedirs(outpath, 0755)
                except Exception, e:
                    errors.append(str(e))
                    errors.append(traceback.format_exc())

    # ARGUMENTS
    batch_files = []
    missing_files = []
    temp_files = []

    if len(args) == 0:
        errors.append('No input files were specified.')
    else:
        for batch_file_selector in args:
            if '*' in batch_file_selector or '?' in batch_file_selector:
                batch_files += map(os.path.abspath, glob.glob(batch_file_selector))
            elif os.path.isdir(batch_file_selector):
                for input_file_wildcard in input_file_wildcards:
                    batch_files += map(os.path.abspath, glob.glob(os.path.join(batch_file_selector, input_file_wildcard)))
            elif not os.path.exists(batch_file_selector):
                if len(batch_file_selector) == 4 and batch_file_selector.isalnum():
                    batch_file_selector = batch_file_selector.lower() # the files are named in lowercase on the cluster
                    if not os.path.exists('/netapp/database'):
                        # This script is not being run on the cluster - try to retrieve the file from the RCSB
                        colortext.message('No file %s exists - assuming that this is a PDB ID and trying to retrieve the associated file from the RCSB.' % batch_file_selector)
                        try:
                            fname = write_temp_file('/tmp', retrieve_pdb(batch_file_selector), suffix = '.pdb', prefix = batch_file_selector)
                            batch_files.append(os.path.abspath(fname))
                            temp_files.append(os.path.abspath(fname))
                        except:
                            errors.append('An error occurred retrieving the PDB file "%s".' % batch_file_selector)
                    else:
                        # We are on the cluster so try to retrieve the stored file
                        colortext.message('No file %s exists - assuming that this is a PDB ID and trying to retrieve the associated file from the cluster mirror of the PDB database.' % batch_file_selector)
                        if os.path.exists('/netapp/database/pdb/remediated/uncompressed_files/pdb%s.ent' % batch_file_selector):
                            batch_files.append('/netapp/database/pdb/remediated/uncompressed_files/pdb%s.ent' % batch_file_selector)
                        elif os.path.exists('/netapp/database/pdb/pre-remediated/uncompressed_files/pdb%s.ent' % batch_file_selector):
                            batch_files.append('/netapp/database/pdb/pre-remediated/uncompressed_files/pdb%s.ent' % batch_file_selector)
                        else:
                            errors.append('Could not find a PDB file for argument "%s".' % batch_file_selector)
                            missing_files.append(batch_file_selector)
            else:
                batch_files.append(os.path.abspath(batch_file_selector))

        batch_files = list(set(batch_files))
        if len(missing_files) == 1:
            errors.append("Input file %s does not exist." % missing_files[0])
        elif len(missing_files) > -0:
            errors.append("Input files %s do not exist." % ', '.join(missing_files))
        if len(batch_files) == 0:
            errors.append('No input files could be found matching the arguments "%s".' % ', '.join(args))

    if errors:
        print_errors_and_exit(parser, errors, ERRCODE_ARGUMENTS)

    job_inputs = []
    job_inputs, has_segment_mapping, errors = setup_jobs(outpath, options, batch_files)

    # Remove any temporary files created
    for tf in temp_files:
        if os.path.exists(tf):
            os.remove(tf)

    if errors:
        print_errors_and_exit(parser, errors, ERRCODE_ARGUMENTS, not errcode)

    no_homologs = ""
    if options.nohoms:
        no_homologs = "-nohoms"

    return dict(
        queue            = options.queue,
        sendmail         = options.sendmail,
        no_homologs      = no_homologs,
        user             = username,
        outpath          = outpath,
        jobname          = cluster_job_name,
        job_inputs       = job_inputs,
        no_zip           = options.nozip,
        scratch          = options.scratch,
        memfree          = options.memfree,
        runtime          = options.runtime,
        frag_sizes       = options.frag_sizes,
        n_frags          = options.n_frags,
        n_candidates     = options.n_candidates,
        add_vall_files   = options.add_vall_files,
        use_vall_files   = options.use_vall_files,
        add_pdbs_to_vall = options.add_pdbs_to_vall,
        has_segment_mapping = has_segment_mapping,
    )

def print_errors_and_exit(parser, errors, errcode, print_help = True):
    if print_help:
        parser.print_help()
    errors.insert(0, '')
    errors.append('')
    for e in errors:
        colorprinter.error(e.replace('  ', ' '))

    if errcode:
        sys.exit(errcode)
    else:
        sys.exit(ERRCODE_ARGUMENTS)

def setup_jobs(outpath, options, input_files):
    ''' This function sets up the jobs by creating the necessary input files as expected.
          - outpath is where the output is to be stored.
          - options is the optparse options object.
          - input_files is a list of paths to input files.
    '''

    job_inputs = None
    reverse_mapping = None
    fasta_file_contents = {}

    # Generate FASTA files for PDB inputs
    # fasta_file_contents is a mapping from a file path to a pair (FASTA contents, file type). We remember the file type
    # since we offset residue IDs depending on file type i.e. for FASTA files, we treat each sequence separately and do
    # not renumber the fragments in postprocessing. For PDB files, however, we need to respect the order and length of
    # sequences so that we renumber the fragments appropriately in postprocessing - we assume that if a PDB file is passed in
    # then all chains (protein, RNA, or DNA) will be used in a Rosetta run.
    for input_file in input_files:
        assert(not(fasta_file_contents.get(input_file)))
        if any(fnmatch(input_file, x) for x in pdb_file_wildcards):
            pdb = PDB.from_filepath(input_file, strict=True)
            pdb.pdb_id = os.path.basename(input_file).split('.')[0]            
            if pdb.pdb_id.startswith('pdb') and len(pdb.pdb_id) >= 7:
                # Hack to rename FASTA identifiers for pdb*.ent files which are present in mirrors of the PDB
                pdb.pdb_id = pdb.pdb_id.replace('pdb', '')    
            fasta_file_contents[input_file] = (pdb.create_fasta(prefer_seqres_order = False), 'PDB')
        else:
            fasta_file_contents[input_file] = (read_file(input_file), 'FASTA')

    # Extract sequences from the input FASTA files.
    found_sequences, reverse_mapping, errors = get_sequences(options, fasta_file_contents)
    if found_sequences:
        reformat(found_sequences)
    if errors:
        return None, False, errors

    # Discard sequences that are the wrong chain.
    desired_sequences = {}
    for key, sequence in found_sequences.iteritems():
        pdb_id, chain, file_name = key
        if options.chain is None or chain == options.chain:
            desired_sequences[key] = sequence

    # Create the input FASTA and script files.
    job_inputs, errors = create_inputs(options, outpath, desired_sequences)

    # Create the reverse mapping file
    if reverse_mapping:
        segment_mapping_file = os.path.join(outpath, "segment_map.json")
        colorprinter.message("Creating a reverse mapping file %s." % segment_mapping_file)
        write_file(segment_mapping_file, json.dumps(reverse_mapping))

    # Create the post-processing script file
    post_processing_script = read_file(os.path.join(os.path.split(os.path.realpath(__file__))[0], 'post_processing.py'))
    write_file(os.path.join(outpath, 'post_processing.py'), post_processing_script, 'w')

    # Create the secondary structure filter file
    if options.secondary_structure_file:
        write_file(os.path.join(outpath, 'ss_filter.json'), json.dumps({'secondary_structure_filter' : SecondaryStructureDefinition.from_filepath(options.secondary_structure_file).data}), 'w')

    return job_inputs, reverse_mapping != None, errors


def get_sequences(options, fasta_file_contents):
    ''' This function returns a dict mapping (pdbid, chain, file_name) tuples to sequences:
          - options is the OptionParser member;
          - fasta_file_contents is a map from input filenames to the associated FASTA file contents.
    '''
    errors = []
    fasta_files_str = ", ".join(fasta_file_contents.keys())
    fasta_records = None
    reverse_mapping = {}

    try:
        fasta_records, reverse_mapping = parse_FASTA_files(options, fasta_file_contents)
        if not fasta_records:
            errors.append("No protein sequences found in the FASTA file(s) %s." % fasta_files_str)
    except Exception, e:
        e = '\n'.join([l for l in traceback.format_exc(), str('e') if l.strip()])
        errors.append("Error parsing FASTA file(s) %s:\n%s" % (fasta_files_str, str(e)))

    if not fasta_records:
        return None, {}, errors

    colorprinter.message('Found %d protein sequence(s).' % len(fasta_records))
    return fasta_records, reverse_mapping, errors

def parse_FASTA_files(options, fasta_file_contents):
    ''' This function iterates through each filepath in fasta_file_contents and returns a dict mapping (pdbid, chain, file_name) tuples to sequences:
          - options is the OptionParser member;
          - fasta_file_contents is a map from input filenames to the associated FASTA file contents.
    '''
    records = {}
    reverse_mapping = {}
    original_segment_list = []
    key_location = {}
    sequenceLine = re.compile("^[A-Z]+\n?$")
    sequence_offsets = {}

    for fasta_file_name, tagged_fasta in sorted(fasta_file_contents.iteritems()):

        # Check the tagged pair
        fasta = tagged_fasta[0].strip().split('\n')
        file_type = tagged_fasta[1]
        assert(file_type == 'PDB' or file_type == 'FASTA')
        if not fasta:
            raise Exception("Empty FASTA file.")

        first_line = [line for line in fasta if line.strip()][0]
        if first_line[0] != '>':
            raise Exception("The FASTA file %s is not formatted properly - the first non-blank line is not a description line (does not start with '>')." % fasta_file_name)

        key = None
        line_count = 0
        record_count = 0
        file_keys = []
        unique_keys = {}
        for line in fasta:
            line_count += 1
            line = line.strip()
            if line:
                if line[0] == '>':
                    record_count += 1
                    tokens = [t.strip() for t in line[1:].split('|') if t.strip()]
                    if len(tokens) < 2:
                        raise Exception("The description line ('%s') of record %d of %s is invalid. It must contain both a protein description and a chain identifier, separated by a pipe ('|') symbol." % (line, record_count, fasta_file_name))
                    if len(tokens[0]) < 4:
                        raise Exception("The protein description in the description line ('%s') of record %d of %s is too short. It must be at least four characters long." % (line, record_count, fasta_file_name))
                    if len(tokens[1]) != 1:
                        raise Exception("The chain identifier in the description line ('%s') of record %d of %s is the wrong length. It must be exactky one character long." % (line, record_count, fasta_file_name))

                    # Note: We store the PDB ID as lower-case so that the user does not have to worry about case-sensitivity here (we convert the user's PDB ID argument to lower-case as well)
                    key = (tokens[0][0:4].lower(), tokens[1], fasta_file_name)
                    sub_key = (key[0], key[1]) # this is the part of the key that we expect to be unique (the actual key)
                    key_location[key] = fasta_file_name
                    if sub_key in unique_keys:
                        # todo: we include the fasta_file_name in the key - should we not be checking for uniqueness w.r.t. just tokens[0][0:4].lower() and tokens[1] i.e. omitting the fasta_file_name as part of the check for a more stringent check?
                        raise Exception("Duplicate protein/chain identifier pair. The key %s was generated from both %s and %s. Remember that the first four characters of the protein description are concatenated with the chain letter to generate a 5-character ID which must be unique." % (key, key_location[key], fasta_file_name))
                    records[key] = [line]
                    unique_keys[sub_key] = True
                    file_keys.append(key)
                else:
                    mtchs = sequenceLine.match(line)
                    if not mtchs:
                        raise FastaException("Expected a record header or sequence line at line %d." % line_count)
                    records[key].append(line)

        offset = 0
        if file_type == 'PDB':
            for key in file_keys:
                sequence_length = len(''.join(records[key][1:]))
                sequence_offsets[key[0] + key[1]] = (offset, offset + 1, offset + sequence_length) # storing the sequence start and end residue IDs here is redundant but simplifies code later on
                offset += sequence_length

    # We remove non-protein chains from fragment generation although we did consider them above when determining the offsets
    # as we expect them to be used in predictions
    non_protein_records = []
    set_of_rna_dna_codes = set(('A', 'C', 'G', 'T', 'U', 'X', 'Z'))
    for key, content_lines in records.iteritems():
        mm_sequence = ''.join(content_lines[1:])
        assert(re.match('^[A-Z]+$', mm_sequence)) # Allow X or Z because these may exist (X from the RCSB, Z from our input files)
        if set(mm_sequence).union(set_of_rna_dna_codes) == set_of_rna_dna_codes:
            non_protein_records.append(key)
    for non_protein_record in non_protein_records:
        del records[non_protein_record]

    # If a loops file was passed in, use that to cut up the sequences and concatenate these subsequences to generate a
    # shorter sequence to process. This should save a lot of time when the total length of the subsequences is considerably
    # shorter than the length of the total sequence e.g. in cases where the protein has @1000 residues but we only care about
    # 100 residues in particular loop regions.

    # We need to sample all sequences around a loop i.e. if a sequence segment is 7 residues long at positions 13-19 and we
    # require 9-mers, we must consider the segment from positions 5-27 so that all possible 9-mers are considered.
    residue_offset = max(options.frag_sizes)

    if options.loops_file or options.indices:
        loops_definition = None
        if options.loops_file:
            loops_definition = LoopsFile.from_filepath(options.loops_file, ignore_whitespace = True, ignore_errors = False)

        # If the user supplied more ranges of residues, use those as well
        if options.indices:
            if not loops_definition:
                loops_definition = LoopsFile('')
            for p in options.indices:
                if loops_definition:
                    loops_definition.add(p[0], p[1])

        segment_list = loops_definition.get_distinct_segments(residue_offset, residue_offset)
        original_segment_list = loops_definition.get_distinct_segments(1, 1) # We are looking for 1-mers so the offset is 1 rather than 0

        # Sanity checks
        assert(sorted(segment_list) == segment_list) # sanity check
        for x in range(len(segment_list)):
            segment = segment_list[x]
            if x < len(segment_list) - 1:
                assert(segment[1] < segment_list[x+1][0]) # sanity check

        # Create the generic reverse_mapping from the indices in the sequences defined by the segment_list to the indices in the original sequences.
        # This will be used in FASTA sequences to rewrite the fragments files to make them compatible with the original sequences.
        # Note that this mapping ignores the length of the sequences (which may vary in length) so it may be mapping residues indices
        # which are outside of the length of some of the sequences.
        # Create a sorted list of residues of the chain that we will be including in the sequence for fragment generation
        # then turn that into a 1-indexed mapping from the order of the residue in the sequence to the original residue ID in the PDB
        residues_for_generation = []
        for s in segment_list:
            residues_for_generation += range(s[0], s[1] + 1)
        reverse_mapping['FASTA'] = dict((key, value) for (key, value) in zip(range(1, len(residues_for_generation) + 1), residues_for_generation))

        # Create the reverse_mappings from the indices in the PDB sequences defined by the segment_list to the indices in the original sequences.
        # Membership in sequence_offsets implies a PDB sequence.
        for k, v in sorted(sequence_offsets.iteritems()):
            # For each PDB chain, we consider the set of segments (ignoring extra residues due to nmerage for now so that
            # we do not include chains by accident e.g. if the user specified the first residues of chain C but none in chain B,
            # they probably do not wish to generate fragments for chain B)
            chain_residues = range(v[1], v[2] + 1)
            residues_for_generation = []
            for s in original_segment_list:
                # If the original segment lists lie inside the chain residues then we extend the range w.r.t. the nmers
                if (chain_residues[0] <= s[0] <= chain_residues[-1]) or (chain_residues[0] <= s[1] <= chain_residues[-1]):
                    residues_for_generation += range(s[0] - residue_offset + 1, s[1] + residue_offset - 1 + 1)

            # Create a sorted list of residues of the chain that we will be including in the sequence for fragment generation
            # then turn that into a 1-indexed mapping from the order of the residue in the sequence to the original residue ID in the PDB
            chain_residues_for_generation = sorted(set(chain_residues).intersection(set(residues_for_generation)))
            reverse_mapping[k] = dict((key, value) for (key, value) in zip(range(1, len(chain_residues_for_generation) + 1), chain_residues_for_generation))

        found_at_least_one_sequence = False
        for k, v in sorted(records.iteritems()):
            assert(v[0].startswith('>'))
            subkey = k[0] + k[1]
            sequence = ''.join([s.strip() for s in v[1:]])
            assert(sequenceLine.match(sequence) != None) # sanity check
            cropped_sequence = None
            if sequence_offsets.get(subkey):
                # PDB chain case
                first_residue_id = sequence_offsets[subkey][1]
                cropped_sequence = ''.join([sequence[rmv - first_residue_id] for rmk, rmv in sorted(reverse_mapping[subkey].iteritems())])
                # Sanity check - check that the remapping from the cropped sequence to the original sequence will work in postprocessing
                for x in range(0, len(cropped_sequence)):
                    assert(cropped_sequence[x] == sequence[reverse_mapping[subkey][x + 1] - sequence_offsets[subkey][0] - 1])
                records[k] = [v[0]] + [cropped_sequence[i:i+60] for i in range(0, len(cropped_sequence), 60)] # update the record to only use the truncated sequence
            else:
                # FASTA chain case
                cropped_sequence = ''.join([sequence[rmv - 1] for rmk, rmv in sorted(reverse_mapping['FASTA'].iteritems()) if rmv <= len(sequence)])
                # Sanity check - check that the remapping from the cropped sequence to the original sequence will work in postprocessing
                for x in range(0, len(cropped_sequence)):
                    assert(cropped_sequence[x] == sequence[reverse_mapping['FASTA'][x + 1] - 1])

            found_at_least_one_sequence = found_at_least_one_sequence or (not not cropped_sequence)
            if cropped_sequence:
                records[k] = [v[0]] + [cropped_sequence[i:i+60] for i in range(0, len(cropped_sequence), 60)]
            else:
                del records[k] # delete the chain. todo: test that this works

        if not found_at_least_one_sequence:
            raise Exception('No sequences were created from the loops/indices and the input sequences. This may be an input error so the job is being terminated.')

    if reverse_mapping:
        return records, dict(reverse_mapping = reverse_mapping, segment_list = original_segment_list, sequence_offsets = sequence_offsets)
    else:
        return records, None

def reformat(found_sequences):
    '''Truncate the FASTA headers so that the first field is a 4-character ID.'''
    for (pdb_id, chain, file_name), sequence in sorted(found_sequences.iteritems()):
        header = sequence[0]
        assert(header[0] == '>')
        tokens = header.split('|')
        tokens[0] = tokens[0][:5]
        assert(len(tokens[0]) == 5)
        sequence[0] = "|".join(tokens)

def create_inputs(options, outpath, found_sequences):
    errors = []

    # Create subdirectories
    job_inputs = []
    for (pdb_id, chain, file_name), sequence in sorted(found_sequences.iteritems()):
        created_new_subdirectory = False
        subdir_path = os.path.join(outpath, "%s%s" % (pdb_id, chain))
        try:
            if os.path.exists(subdir_path):
                if options.overwrite:
                    colorprinter.warning("Path %s exists. Removing all files in that path as per the override option." % subdir_path)
                    shutil.rmtree(subdir_path)
                    created_new_subdirectory = True
                else:
                    errors.append('The directory %s already exists.' % subdir_path) # uncomment this if we want to turn on the _001, _002, etc. directories
                    count = 1
                    while count < 1000:
                        subdir_path = os.path.join(outpath, "%s%s_%.3i" % (pdb_id, chain, count))
                        if not os.path.exists(subdir_path):
                            break
                        count += 1
                    if count == 1000:
                        errors.append("The directory %s contains too many previous results. Please clean up the old results or choose a new output directory." % outpath)
                        sys.exit(ERRCODE_OLDRESULTS)
            os.makedirs(subdir_path, 0755)

            # Create a FASTA file for the sequence in the output directory
            fasta_file = os.path.join(subdir_path, "%s%s.fasta" % (pdb_id, chain))
            colorprinter.message("Creating a new FASTA file %s." % fasta_file)

            assert(not(os.path.exists(fasta_file)))
            write_file(fasta_file, '\n'.join(sequence) + '\n', 'w') # The file must terminate in a newline for the Perl script to work
            job_inputs.append(JobInput(fasta_file, pdb_id, chain))
        except:
            if created_new_subdirectory and os.path.exists(subdir_path):
                shutil.rmtree(subdir_path)
            errors.append('An error occurred creating the input for %s%s.' % (pdb_id, chain))
            job_inputs = []
            break

    return job_inputs, errors

def search_configuration_files(findstr, replacestr = None):
    '''This function could be used to find and replace paths in the configuration files.
        At present, it only finds phrases.'''

    F = open(configurationFilesLocation, "r")
    lines = F.readlines()
    F.close()
    allerrors = {}
    alloutput = {}

    for line in lines:
        line = line.strip()
        if line:
            if line.endswith("generate_fragments.py"):
                # Do not parse the Python script but check that it exists
                if not(os.path.exists(line)):
                    allerrors[line] = "File/directory %s does not exist." % line
            else:
                cmd = ["grep", "-n", "-i",  findstr, line]
                output = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()
                errors = output[1]
                output = output[0]
                if errors:
                    errors = errors.strip()
                    allerrors[line] = errors
                if output:
                    output = output.strip()
                    alloutput[line] = output.split("\n")
    return alloutput, allerrors

def check_configuration_paths():
    pathregex1 = re.compile('.*"(/netapp.*?)".*')
    pathregex2 = re.compile('.*".*(/netapp.*?)\\\\".*')
    alloutput, allerrors = search_configuration_files("netapp")
    errors = []
    if allerrors:
        for flname, errs in sorted(allerrors.iteritems()):
            errors.append((flname, [errs]))
    for flname, output in sorted(alloutput.iteritems()):
        m_errors = []
        for line in output:
            mtchs = pathregex1.match(line) or pathregex2.match(line)
            if not mtchs:
                m_errors.append("Regex could not match line: %s." % line)
            else:
                dir = mtchs.group(1).split()[0]
                if not os.path.exists(dir):
                    m_errors.append("File/directory %s does not exist." % dir)
        if m_errors:
            errors.append((flname, m_errors))

    return errors


def main():
    this_dir = os.path.dirname(os.path.realpath(__file__))
    make_fragments_script_path = os.path.join(this_dir, make_fragments_script)

    errors = [] #check_configuration_paths()
    if errors:
        colorprinter.error("There is an error in the configuration files:")
        for e in errors:
            print("")
            flname = e[0]
            es = e[1]
            colorprinter.warning(flname)
            for e in es:
                colorprinter.error(e)
        sys.exit(ERRCODE_CONFIG)

    options = parse_args()
    if options["outpath"] and options['job_inputs']:
        job_script = None
        try:
            cluster_job = ClusterEngine.FragmentsJob(make_fragments_script_path, options, test_mode = test_mode)
            job_script = cluster_job.script
        except JobInitializationException, e:
            colorprinter.error(str(e))
            sys.exit(ERRCODE_ARGUMENTS)

        submission_script = os.path.join(options["outpath"], 'submission_script.py')
        write_file(submission_script, job_script, 'w')

        try:
            send_mail = options['sendmail']
            username = None
            if send_mail:
                username = get_username()
            (jobid, output) = ClusterEngine.submit(submission_script, options["outpath"], send_mail = send_mail, username = username )
        except Exception, e:
            colorprinter.error("An exception occurred during submission to the cluster.")
            colorprinter.error(str(e))
            colorprinter.error(traceback.format_exc())
            sys.exit(ERRCODE_CLUSTER)

        colorprinter.message("\nFragment generation jobs started with job ID %d. Results will be saved in %s." % (jobid, options["outpath"]))
        if options['no_homologs']:
            print("The --nohoms option was selected.")
        if options['no_zip']:
            print("The --nozip option was selected.")
        if ClusterEngine.ClusterType == "SGE":
            print("The jobs have been submitted using the %s queue(s)." % (', '.join(sorted(options['queue'])) or 'default'))
        print('')
        logfile.writeToLogfile(datetime.now(), jobid, options["outpath"])

if __name__ == "__main__":
    main()
