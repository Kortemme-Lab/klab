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
import glob
import getpass
from utils import LogFile, colorprinter, JobInitializationException

#################
#  Configuration

# Choose the Python classes for your type of cluster system
import cluster.SGE as ClusterEngine
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
#  Globals

make_fragments_script = "make_fragments_RAP_cluster.pl"
test_mode = False # set this to true for running quick tests on your cluster system (you will need to adapt the cluster/[engine].py code to use this argument
logfile = LogFile("make_fragments_destinations.txt") # the logfile used for querying jobs
cluster_job_name = "fragment_generation" # optional: set this to identify your jobs on the cluster
fasta_file_wildcards = ['*.fasta', '*.fasta.txt', '*.fa'] # optional: set this to your preferred FASTA file extensions. This is used for finding FASTA files when specifying a directory in batch mode.

# The location of the text file containing the names of the configuration scripts
configurationFilesLocation = "make_fragments_confs.txt" # "/netapp/home/klabqb3backrub/make_fragments/make_fragments_confs.txt"
#
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
    #return subprocess.Popen("whoami", stdout=subprocess.PIPE).communicate()[0].strip()


def write_file(filepath, contents, ftype = 'w'):
    output_handle = open(filepath, ftype)
    output_handle.write(contents)
    output_handle.close()


def parse_FASTA_files(fasta_files):

    records = {}
    key_location = {}
    sequenceLine = re.compile("^[ACDEFGHIKLMNPQRSTVWY]+\n?$")

    for fasta_file in fasta_files:
        record_count = 0
        F = open(fasta_file, "r")
        fasta = F.readlines()
        F.close()

        if not fasta:
            raise Exception("Empty FASTA file.")

        first_line = [line for line in fasta if line.strip()][0]
        if first_line[0] != '>':
            raise Exception("The FASTA file is not formatted properly - the first non-blank line is not a description line (does not start with '>').")

        key = None
        line_count = 0
        for line in fasta:
            line_count += 1
            line = line.strip()
            if line:
                if line[0] == '>':
                    record_count += 1
                    tokens = [t.strip() for t in line[1:].split('|') if t.strip()]
                    if len(tokens) < 2:
                        raise Exception("The description line ('%s') of record %d of %s is invalid. It must contain both a protein description and a chain identifier, separated by a pipe ('|') symbol." % (line, record_count, fasta_file))
                    if len(tokens[0]) < 4:
                        raise Exception("The protein description in the description line ('%s') of record %d of %s is too short. It must be at least four characters long." % (line, record_count, fasta_file))
                    if len(tokens[1]) != 1:
                        raise Exception("The chain identifier in the description line ('%s') of record %d of %s is the wrong length. It must be exactky one character long." % (line, record_count, fasta_file))

                    # Note: We store the PDB ID as lower-case so that the user does not have to worry about case-sensitivity here (we convert the user's PDB ID argument to lower-case as well)
                    key = (tokens[0][0:4].lower(), tokens[1], fasta_file)
                    if key in records:
                        raise Exception("Duplicate protein/chain identifier pair. The key %s was generated from both %s and %s. Remember that the first four characters of the protein description are concatentated with the chain letter to generate a 5-character ID which must be unique." % (key, key_location[key], fasta_file))
                    key_location[key] = fasta_file

                    records[key] = [line]
                else:
                    mtchs = sequenceLine.match(line)
                    if not mtchs:
                        raise FastaException("Expected a record header or sequence line at line %d." % line_count)
                    records[key].append(line)
    return records


def parseArgs():
    global errcode
    errors = []
    pdbpattern = re.compile("^\w{4}$")
    description = ['\n']
    description.append("*** Help ***\n")
    description.append("The output of the computation will be saved in the output directory, along with")
    description.append("the input FASTA file which is generated from the supplied FASTA file.")
    description.append("A log of the output directories for cluster jobs is saved in")
    description.append("%s in the current directory to admit queries." % logfile.getName())
    description.append("")
    description.append("The FASTA description lines must have the following format:")
    description.append("'>protein_id|chain_letter', optionally followed by more text preceded by a '|'")

    description.append('''There are a few caveats:

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
from the FASTA files using the method above must be unique.

For example, if you have two records ">1A2P_001|A|" and "">1A2P_002|A|" then 
the job will fail.
On the other hand, ">1A2P_001|A|" and "">1A2P_001|B|" is perfectly fine and 
the script will output fragments for 1a2pA and 1a2pB.''')
    
    script_name = os.path.split(sys.argv[0])[1]
    description.append("\n*** Examples ***\n")
    description.append("Single-sequence fragment generation:")
    description.append("1: " + script_name + " -d results -f /path/to/1CYO.fasta.txt")
    description.append("2: " + script_name + " -d results -f /path/to/1CYO.fasta.txt -p1CYO -cA\n")
    description.append("Multi-sequence fragment generation (batch job):")
    description.append("1: " + script_name + " -d results -b /path/to/fasta_file.1,...,/path/to/fasta_file.n")
    description.append("2: " + script_name + " -d results -b /some/path/%.fa???,/some/other/path/,/path/to/fasta_file.1\n\n")
    
    description = "\n".join(description)

    parser = OptionParserWithNewlines(usage="usage: %prog [options]", version="%prog 1.1A", option_class=MultiOption)
    parser.epilog = description

    group = OptionGroup(parser, "Single sequence options (for running fragment generation for just one sequence)")
    group.add_option("-f", "--fasta", dest="fasta", help="The input FASTA file. This defaults to OUTPUT_DIRECTORY/PDBID.fasta.txt if the PDB ID is supplied.", metavar="FASTA")
    group.add_option("-c", "--chain", dest="chain", help="Chain used for the fragment. This is optional so long as the FASTA file only contains one chain.", metavar="CHAIN")
    group.add_option("-p", "--pdbid", dest="pdbid", help="The input PDB identifier. This is optional if the FASTA file is specified and only contains one PDB identifier.", metavar="PDBID")
    parser.add_option_group(group)

    group = OptionGroup(parser, "Multiple sequence options (fragment generation is run on all sequences). These options can be combined.")
    group.add_option("-b", "--batch", action="extend", dest="batch", help="Batch mode. The argument to this option is a comma-separated (no spaces) list of: i) FASTA files; ii) wildcard strings e.g. '/path/to/%.fasta'; or iii) directories. Fragment generation will be performed for all sequences in the explicitly lists files, files matching the wildcard selection, and '.fasta' files in any directory listed. Note: The 5-character IDs (see above) must be unique for this mode. Also, note that '%' is used as a wildcard character rather than '*' to prevent shell wildcard-completion.", metavar="LIST OF FILES or DIRECTORY")
    parser.add_option_group(group)

    group = OptionGroup(parser, "General options")
    group.add_option("-d", "--outdir", dest="outdir", help="Optional. Output directory relative to user space on netapp. Defaults to the current directory so long as that is within the user's netapp space.", metavar="OUTPUT_DIRECTORY")
    group.add_option("-N", "--nohoms", dest="nohoms", action="store_true", help="Optional. If this option is set then homologs are omitted from the search.")
    group.add_option("-V", "--overwrite", dest="overwrite", action="store_true", help="Optional. If the output directory <PDBID><CHAIN> for the fragment job(s) exists, delete the current contents.")
    group.add_option("-F", "--force", dest="force", action="store_true", help="Optional. Create the output directory without prompting.")
    group.add_option("-M", "--email", dest="sendmail", action="store_true", help="Optional. If this option is set, an email is sent when the job finishes or fails (cluster-dependent). WARNING: On an SGE cluster, an email will be sent for each FASTA file i.e. for each task in the job array.")
    parser.add_option_group(group)

    group = OptionGroup(parser, "Querying options")
    group.add_option("-q", "--queue", dest="queue", help="Optional. Specify which cluster queue to use. Whether this option works and what this value should be will depend on your cluster architecture. Valid arguments for the QB3 SGE cluster are long.q, lab.q, and short.q.", metavar="QUEUE_NAME")
    group.add_option("-K", "--check", dest="check", help="Optional, needs to be fixed for batch mode. Query whether or not a job is running. It if has finished, query %s and print whether the job was successful." % logfile.getName(), metavar="JOBID")
    group.add_option("-Q", "--query", dest="query", action="store_true", help="Optional, needs to be fixed for batch mode. Query the progress of the cluster job against %s and then quit." % logfile.getName())
    parser.add_option_group(group)

    parser.set_defaults(outdir = os.getcwd())
    parser.set_defaults(overwrite = False)
    parser.set_defaults(nohoms = False)
    parser.set_defaults(force = False)
    parser.set_defaults(query = False)
    parser.set_defaults(sendmail = False)
    parser.set_defaults(queue = 'lab.q')
    (options, args) = parser.parse_args()

    username = get_username()
    if len(args) >= 1:
        errors.append("Unexpected arguments: %s." % join(args, ", "))

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

    # PDB ID
    if options.pdbid:
        if not pdbpattern.match(options.pdbid):
            errors.append("Please enter a valid PDB identifier.")
        else:
            # Note: We stored the PDB ID as lower-case so that the user does not have to worry about case-sensitivity. Here, we convert the user's PDB ID argument to lower-case as well.
            options.pdbid = options.pdbid.lower()

    # CHAIN
    if options.chain and not (len(options.chain) == 1):
        errors.append("Chain must only be one character.")

    # OUTDIR
    outpath = options.outdir
    if outpath[0] != "/":
        outpath = os.path.abspath(outpath)
    outpath = os.path.normpath(outpath)

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

    # FASTA
    if options.fasta:
        if not os.path.isabs(options.fasta):
            options.fasta = os.path.realpath(options.fasta)
    if options.pdbid and not options.fasta:
        options.fasta = os.path.join(outpath, "%s.fasta.txt" % options.pdbid)

    # BATCH
    batch_files = []
    if options.batch:
        batch_params = options.batch
        missing_files = []

        batch_files = []
        for batch_file_selector in batch_params:
            if batch_file_selector.find('%') != -1:
                batch_file_selector = batch_file_selector.replace('%', '*')
                batch_files.extend(map(os.path.abspath, glob.glob(batch_file_selector)))
            elif batch_file_selector.find('?') != -1:
                batch_files.extend(map(os.path.abspath, glob.glob(batch_file_selector)))
            elif os.path.isdir(batch_file_selector):
                for fasta_file_wildcard in fasta_file_wildcards:
                    batch_files.extend(map(os.path.abspath, glob.glob(os.path.join(batch_file_selector, fasta_file_wildcard))))
            else:
                if not os.path.exists(batch_file_selector):
                    missing_files.append(batch_file_selector)
                else:
                    batch_files.append(os.path.abspath(batch_file_selector))
        batch_files = list(set(batch_files))

        if missing_files:
            if missing_files == 1:
                errors.append("FASTA file %s does not exist." % options.fasta)
            else:
                errors.append("FASTA files %s do not exist." % ', '.join(missing_files))

    if (not options.fasta) and (not batch_files):
        if not validOptions:
            parser.print_help()
            sys.exit(ERRCODE_ARGUMENTS)

    if (options.fasta) and (batch_files):
        parser.print_help()
        colorprinter.error('\nError: You must either use single sequence mode or batch mode. Both were specified')
        sys.exit(ERRCODE_ARGUMENTS)

    job_inputs = []
    if options.fasta:
        if not os.path.exists(options.fasta):
            errors.append("FASTA file %s does not exist." % options.fasta)
        elif not errors:
            job_inputs, errors = setup_jobs(outpath, options, [options.fasta], False)
    elif batch_files:
        if not errors:
            job_inputs, errors = setup_jobs(outpath, options, batch_files, True)

    if errors:
        if not errcode:
            parser.print_help()

        print("")
        for e in errors:
            colorprinter.error(e)
        print("")

        if errcode:
            sys.exit(errcode)
        sys.exit(ERRCODE_ARGUMENTS)

    no_homologs = ""
    if options.nohoms:
        no_homologs = "-nohoms"

    return {
        "queue"         : options.queue,
        "sendmail"         : options.sendmail,
        "no_homologs"	: no_homologs,
        "user"			: username,
        "outpath"		: outpath,
        "jobname"		: cluster_job_name,
        "job_inputs"    : job_inputs,
        #"qstatstats"	: "", # Override this with "qstat -xml -j $JOB_ID" to print statistics. WARNING: Only do this every, say, 100 runs to avoid spamming the queue master.
        }

def setup_jobs(outpath, options, fasta_files, batch_mode):
    job_inputs = None
    found_sequences, errors = get_sequences(options, fasta_files, batch_mode)
    if found_sequences or batch_mode:
        reformat(found_sequences)
    if not errors:
        job_inputs, errors = create_inputs(options, outpath, found_sequences)
    return job_inputs, errors

def get_sequences(options, fasta_files, batch_mode):
    errors = []
    fasta_files_str = ", ".join(fasta_files)
    fasta_records = None
    try:
        fasta_records = parse_FASTA_files(fasta_files)
        if not fasta_records:
            errors.append("No data found in the FASTA file(s) %s." % fasta_files_str)
    except Exception, e:
        errors.append("Error parsing FASTA file(s) %s:\n%s" % (fasta_files_str, str(e)))

    num_fasta_records = len(fasta_records)

    colorprinter.message('Found %d sequence(s).' % num_fasta_records)

    found_sequences = None
    if num_fasta_records == 0:
        errors.append("No sequences found in the FASTA file(s) %s." % fasta_files_str)
    elif num_fasta_records == 1:
        # One record - we will revert to a single task job below regardless of whether the script was called with batch mode or not
        key = fasta_records.keys()[0]
        (options.pdbid, options.chain, file_name) = key
        found_sequences = fasta_records
        colorprinter.message("One chain and PDB ID pair (%s, %s) found in %s. Using that pair as input." % (options.chain, options.pdbid, file_name))
    elif batch_mode:
        found_sequences = fasta_records

    if not found_sequences:
        # In single sequence mode - find the record we are looking for

        # Check for ambiguity in the records (same PDB ID, chain)
        record_frequency = {}
        for record in fasta_records.keys():
            k = (record[0], record[1])
            record_frequency[k] = record_frequency.get(k, 0) + 1
        multipledefinitions = ["\tPDB ID: %s, Chain %s" % (record[0], record[1]) for record, count in sorted(record_frequency.iteritems()) if count > 1]

        chains_present = sorted([record[1] for record in fasta_records.keys()])
        pdbids_present = sorted(list(set([record[0] for record in fasta_records.keys()])))

        if len(multipledefinitions) > 0:
            errors.append("The FASTA file(s) %s contains multiple sequences for the following chains:\n%s.\nPlease edit the file and remove the unnecessary chains." % (fasta_files_str, join(multipledefinitions, "\n")))
        else:
            if not options.chain:
                if chains_present > 1:
                    errors.append("Please enter a chain. Valid chains are: %s." % join(chains_present, ", "))
                else:
                    options.chain = chains_present[0]
                    colorprinter.message("No chain specified. Using the only one present in the fasta file(s), %s." % options.chain)
            if not options.pdbid:
                if pdbids_present > 1:
                    errors.append("Please enter a PDB identifier. Valid IDs are: %s." % join(pdbids_present, ", "))
                else:
                    options.pdbid = pdbids_present[0].lower()
                    colorprinter.message("No PDB ID specified. Using the only one present in the fasta file(s), %s." % options.pdbid)
            if options.chain and options.pdbid:
                for (pdbid, chain, file_name), sequence in sorted(fasta_records.iteritems()):
                    if pdbid == options.pdbid and chain == options.chain:
                        found_sequences = {(pdbid, chain, file_name) : sequence}
                        break
                if not found_sequences:
                    errors.append('Could not find the sequence for PDB ID %s and chain %s in the file(s) %s.' % (options.pdbid, options.chain, fasta_files_str))
    
    return found_sequences, errors


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
    if len(found_sequences) == 1:
        # In single sequence mode - find the record we are looking for
        batch_mode = True

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


def searchConfigurationFiles(findstr, replacestr = None):
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


def checkConfigurationPaths():
    pathregex1 = re.compile('.*"(/netapp.*?)".*')
    pathregex2 = re.compile('.*".*(/netapp.*?)\\\\".*')
    alloutput, allerrors = searchConfigurationFiles("netapp")
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


if __name__ == "__main__":

    this_dir = os.path.dirname(os.path.realpath(__file__))
    make_fragments_script = os.path.join(this_dir, make_fragments_script)

    errors = [] #checkConfigurationPaths()
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


    options = parseArgs()
    if options["outpath"] and options['job_inputs']:
        try:
            if len(options['job_inputs']) > 1:
                # Single sequence fragment generation
                task = ClusterEngine.MultipleTask(make_fragments_script, options, test_mode = test_mode)
                submission_script, scripts = task.get_scripts()
            else:
                # Single sequence fragment generation
                task = ClusterEngine.SingleTask(make_fragments_script, options, test_mode = test_mode)
                submission_script, scripts = task.get_scripts()
        except JobInitializationException, e:            
            colorprinter.error(str(e))
            sys.exit(ERRCODE_ARGUMENTS)
        
        for script_filename, script in scripts.iteritems():
            write_file(os.path.join(options["outpath"], script_filename), script, 'w')

        submission_script = os.path.join(options["outpath"], submission_script)

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
        if ClusterEngine.ClusterType == "SGE":
            print("The jobs have been submitted using the %s queue." % options['queue'])
        print('')
        logfile.writeToLogfile(datetime.now(), jobid, options["outpath"])



