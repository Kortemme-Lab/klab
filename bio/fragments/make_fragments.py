#!/usr/bin/python
# -*- coding: utf-8 -*-
# Created 2011-10-13 by Shane O'Connor, Kortemme Lab

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
import getpass
from utils import LogFile, colorprinter

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
errcode = 0
#
#################


#################
#  Globals

logfile = LogFile("make_fragments_destinations.txt")
clusterJobName = "fragment_generation"

# The location of the text file containing the names of the configuration scripts
configurationFilesLocation = "make_fragments_confs.txt" # "/netapp/home/klabqb3backrub/make_fragments/make_fragments_confs.txt"
#
#################


def get_username():
    return getpass.getuser()
    #return subprocess.Popen("whoami", stdout=subprocess.PIPE).communicate()[0].strip()


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
            lvalue = value.split(" ")
            values.ensure_value(dest, []).extend(lvalue)
        else:
            Option.take_action(self, action, dest, opt, value, values, parser)


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

        if fasta[0][0] != '>':
            raise Exception("The FASTA file is not formatted properly - the first non-blank line is not a description line (does not start with '>').")

        key = None
        line_count = 0
        for line in fasta:
            line_count += 1
            line = line.strip()
            if line:
                if line[0] == '>':
                    record_count += 1
                    tokens = [t.strip() for t in line[1].split('|') if t.strip()]
                    if len(tokens) < 2:
                        raise Exception("The description line ('%s') of record %d of %s is invalid. It must contain both a protein description and a chain identifier, separated by a pipe ('|') symbol." % (line, record_count, fasta_file))
                    if len(tokens[0]) < 4:
                        raise Exception("The protein description in the description line ('%s') of record %d of %s is too short. It must be at least four characters long." % (line, record_count, fasta_file))
                    if len(tokens[1]) != 1:
                        raise Exception("The chain identifier in the description line ('%s') of record %d of %s is the wrong length. It must be exactky one character long." % (line, record_count, fasta_file))
                    key = '%s%s' % (tokens[0][0:4], tokens[1])
                    if key in records:
                        raise Exception("Duplicate protein/chain identifier pair. The key %s was generated from both %s and %s. Remember that the first four characters of the protein description are concatentated with the chain letter to generate a 5-character ID which must be unique." % (key, key_location[key], fasta_file))
                    key_location[key] = fasta_file

                    records[(record_count, key[0:4], key[4])] = [line]
                else:
                    assert(len(key) == 5)
                    mtchs = sequenceLine.match(line)
                    if not mtchs:
                        raise FastaException("Expected a record header or sequence line at line %d." % line_count)
                    records[(record_count, key[0:4], key[4])] = [line]
    return records

    chain_line = re.compile("^>(\w{4,})|(\w)\s+\n?$")
    chain_line = re.compile("^>(\w{4,})|(\w)|.*\n?$")

    records = {}
    pdbid = None
    chain = None
    count = 1
    recordcount = 0
    for line in fasta:
        if line.strip():
            if chain == None and pdbid == None:
                mtchs = chain_line.match(line)
                if not mtchs:
                    raise FastaException("Expected a record header at line %d." % count)

            mtchs = chain_line.match(line)
            if mtchs:
                recordcount += 1
                pdbid = (mtchs.group(1))
                chain = (mtchs.group(2))
                records[(recordcount, pdbid, chain)] = [line]
            else:
                mtchs = sequenceLine.match(line)
                if not mtchs:
                    raise FastaException("Expected a record header or sequence line at line %d." % count)
                records[(recordcount, pdbid, chain)].append(line)

        count += 1
    return records


def parseArgs():
    global errcode
    errors = []
    pdbpattern = re.compile("^\w{4}$")
    description = ['\n']
    description.append("Single job, example 1 : make_fragments.py -d results -f /path/to/1CYO.fasta.txt")
    description.append("Single job, example 2 : make_fragments.py -d results -f /path/to/1CYO.fasta.txt -p1CYO -cA")
    description.append("Batch job,  example 1 : make_fragments.py -d results -b /path/to/fasta_file.1,...,/path/to/fasta_file.n")
    description.append("Batch job,  example 2 : make_fragments.py -d results -b /folder/with/fasta/files")
    description.append("-----------------------------------------------------------------------------")
    description.append("The output of the computation will be saved in the output directory, along with the input FASTA file which is generated from the supplied FASTA file.")
    description.append("A log of the output directories for cluster jobs is saved in %s in the current directory to admit queries." % logfile.getName())
    description.append("")
    description.append("Warning: Do not reuse the same output directory for multiple runs. Results from a previous run may confuse the executable chain and lead to erroneous results.")
    description.append("To prevent this occurring e.g. in batch submissions, use the -S option to create the results in a subdirectory of the output directory.")
    description.append("")
    description.append("The FASTA description lines must have the following format: '>protein_id|chain_letter', optionally followed by more text preceded by a bar symbol.")
    description.append("The underlying Perl script requires a 5-character ID with the first four characters being the protein id (PDB ID) and the final character being the chain identifier.")
    description.append("To create a 5-character ID, this script takes the first four characters from protein_id and the chain letter to create the 5-character ID. The list of these IDs must be unique.")
    description.append("")
    description = "\n".join(description)

    parser = OptionParserWithNewlines(usage="usage: %prog [options]", version="%prog 1.1A", option_class=MultiOption)
    parser.epilog = description

    group = OptionGroup(parser, "Single sequence options (for running fragment generation for just one sequence)")
    group.add_option("-f", "--fasta", dest="fasta", help="The input FASTA file. This defaults to OUTPUT_DIRECTORY/PDBID.fasta.txt if the PDB ID is supplied.", metavar="FASTA")
    group.add_option("-c", "--chain", dest="chain", help="Chain used for the fragment. This is optional so long as the FASTA file only contains one chain.", metavar="CHAIN")
    group.add_option("-p", "--pdbid", dest="pdbid", help="The input PDB identifier. This is optional if the FASTA file is specified and only contains one PDB identifier.", metavar="PDBID")
    parser.add_option_group(group)

    group = OptionGroup(parser, "Multiple sequence options (fragment generation is run on all sequences)")
    group.add_option("-b", "--batch", action="extend", dest="batch", help="Batch mode. The argument to this option is either: i) a comma-separated (no spaces) list of FASTA files; or ii) a directory. In the former case, fragment generation will be performed for all sequences in the FASTA files. In the latter case, fragment generation will be performed for all sequences in all files in the directory ending with '.FASTA'. Note: The 5-character IDs (see above) must be unique for this mode.", metavar="LIST OF FILES or DIRECTORY")
    parser.add_option_group(group)

    group = OptionGroup(parser, "General options")
    group.add_option("-H", "--nohoms", dest="nohoms", action="store_true", help="Optional. If this option is set then homologs are omitted from the search.")
    group.add_option("-d", "--outdir", dest="outdir", help="Optional. Output directory relative to user space on netapp. Defaults to the current directory so long as that is within the user's netapp space.", metavar="OUTPUT_DIRECTORY")
    group.add_option("-N", "--noprompt", dest="noprompt", action="store_true", help="Optional. Create the output directory without prompting.")
    group.add_option("-S", "--subdirs", dest="subdirs", action="store_true", help="Optional. Create a subdirectory in the output directory named <PDBID><CHAIN>. See the notes above.")
    parser.add_option_group(group)

    group = OptionGroup(parser, "Querying options")
    group.add_option("-K", "--check", dest="check", help="Optional. Query whether or not a job is running. It if has finished, query %s and print whether the job was successful." % logfile.getName(), metavar="JOBID")
    group.add_option("-Q", "--query", dest="query", action="store_true", help="Optional. Query the progress of the cluster job against %s and then quit." % logfile.getName())
    parser.add_option_group(group)

    parser.set_defaults(outdir = os.getcwd())
    parser.set_defaults(nohoms = False)
    parser.set_defaults(noprompt = False)
    parser.set_defaults(subdirs = False)
    parser.set_defaults(query = False)
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
            ClusterEngine.check(logfile, jobID)

    validOptions = options.query or options.check

    # PDB ID
    if options.pdbid and not pdbpattern.match(options.pdbid):
        errors.append("Please enter a valid PDB identifier.")



    # CHAIN
    if options.chain and not (len(options.chain) == 1):
        errors.append("Chain must only be one character.")

    # OUTDIR
    outpath = options.outdir
    if outpath[0] != "/":
        outpath = os.path.join(os.getcwd(), outpath)
    userdir = os.path.join("/netapp/home", username)
    outpath = os.path.normpath(outpath)
    if os.path.commonprefix([userdir, outpath]) != userdir:
        errors.append("Please enter an output directory inside your netapp space.")
    else:
        if not os.path.exists(outpath):
            createDir = options.noprompt
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
            options.fasta= os.path.realpath(options.fasta)
    if options.pdbid and not options.fasta:
        options.fasta = os.path.join(outpath, "%s.fasta.txt" % options.pdbid)
    if not options.fasta:
        if not validOptions:
            parser.print_help()
            sys.exit(ERRCODE_ARGUMENTS)
    if options.fasta:
        if not os.path.exists(options.fasta):
            if not validOptions:
                errors.append("FASTA file %s does not exists." % options.fasta)
        elif not errors:
            fastadata = None
            try:
                fastadata = parse_FASTA_files([options.fasta])
                if not fastadata:
                    errors.append("No data found in the FASTA file %s." % options.fasta)

            except Exception, e:
                errors.append("Error parsing FASTA file %s:\n%s" % (options.fasta, str(e)))

            if fastadata:
                sequencecount = len(fastadata)
                recordfrequency = {}
                for record in fastadata.keys():
                    k = (record[1], record[2])
                    recordfrequency[k] = recordfrequency.get(k, 0) + 1
                multipledefinitions = ["\tPDB ID: %s, Chain %s" % (record[0], record[1]) for record, count in sorted(recordfrequency.iteritems()) if count > 1]
                chainspresent = sorted([record[2] for record in fastadata.keys()])
                pdbidspresent = sorted(list(set([record[1] for record in fastadata.keys()])))
                if len(multipledefinitions) > 0:
                    errors.append("The FASTA file %s contains multiple sequences for the following chains:\n%s.\nPlease edit the file and remove the unnecessary chains." % (options.fasta, join(multipledefinitions, "\n")))
                elif sequencecount == 0:
                    errors.append("No sequences found in the FASTA file %s." % options.fasta)
                else:
                    if not options.chain and sequencecount > 1:
                        errors.append("Please enter a chain. Valid chains are: %s." % join(chainspresent, ", "))
                    elif not options.pdbid and len(pdbidspresent) > 1:
                        errors.append("Please enter a PDB identifier. Valid IDs are: %s." % join(pdbidspresent, ", "))
                    else:
                        foundsequence = None

                        if sequencecount == 1:
                            key = fastadata.keys()[0]
                            (temp, options.pdbid, options.chain) = key
                            foundsequence = fastadata[key]
                            colorprinter.message("One chain and PDB ID pair (%s, %s) found in %s. Using that pair as input." % (options.chain, options.pdbid, options.fasta))
                        elif not options.pdbid:
                            assert(len(pdbidspresent) == 1)
                            options.pdbid = pdbidspresent[0]
                            colorprinter.message("No PDB ID specified. Using the only one present in the fasta file, %s." % options.pdbid)
                            if sequencecount > 1:
                                for (recordnumber, pdbid, chain), sequence in sorted(fastadata.iteritems()):
                                    if pdbid.upper() == options.pdbid.upper() and chain == options.chain:
                                        foundsequence = sequence

                        # This line determines in which case the filenames will be generated for the command chain
                        options.pdbid = options.pdbid.lower()

                        # Create subdirectories if specified
                        assert(options.pdbid and options.chain)
                        if options.subdirs:
                            newoutpath = os.path.join(outpath, "%s%s" % (options.pdbid, options.chain))
                            if os.path.exists(newoutpath):
                                count = 1
                                while count < 1000:
                                    newoutpath = os.path.join(outpath, "%s%s_%.3i" % (options.pdbid, options.chain, count))
                                    if not os.path.exists(newoutpath):
                                        break
                                    count += 1
                                if count == 1000:
                                    colorprinter.error("The directory %s contains too many previous results. Please clean up the old results or choose a new output directory." % outpath)
                                    sys.exit(ERRCODE_OLDRESULTS)
                            outpath = newoutpath
                            os.makedirs(outpath, 0755)

                        # Create a pruned FASTA file in the output directory
                        if foundsequence:
                            fpath, ffile = os.path.split(options.fasta)
                            newfile = os.path.join(outpath, "%s%s.fasta" % (options.pdbid, options.chain))
                            colorprinter.message("Creating a new FASTA file %s." % newfile)

                            writefile = True
                            if os.path.exists(newfile):
                                colorprinter.prompt("The file %(newfile)s exists. Do you want to overwrite it?" % vars())
                                answer = None
                                while answer not in ['Y', 'N']:
                                    colorprinter.prompt()
                                    answer = sys.stdin.readline().upper().strip()
                                if answer == 'N':
                                    writefile = False
                                    errors.append("Please remove the existing file %(newfile)s to continue." % vars())
                            if writefile:
                                F = open(newfile, "w")
                                for line in foundsequence:
                                    F.write("%s" % line)
                                F.close()
                                options.fasta = newfile
                        else:
                            errors.append("Could not find the sequence for chain %s in structure %s in FASTA file %s." % (options.chain, options.pdbid, options.fasta))
    if errors:
        print("")
        for e in errors:
            colorprinter.error(e)
        print("")
        if errcode:
            sys.exit(errcode)
        parser.print_help()
        sys.exit(ERRCODE_ARGUMENTS)

    no_homologs = ""
    if options.nohoms:
        no_homologs = "-nohoms"

    return {
        "no_homologs"	: no_homologs,
        "user"			: username,
        "outpath"		: outpath,
        "pdbid"			: options.pdbid,
        "chain"			: options.chain,
        "fasta"			: options.fasta,
        "jobname"		: clusterJobName,
        #"qstatstats"	: "", # Override this with "qstat -xml -j $JOB_ID" to print statistics. WARNING: Only do this every, say, 100 runs to avoid spamming the queue master.
        }


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
            if line.endswith("make_fragments.py"):
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
    if options["outpath"] and options["fasta"] and options["pdbid"] and options["chain"]:
        template = template % options

        # todo: remove this when we want to run the jobs
        print(template)
        sys.exit(0)
        qcmdfile = os.path.join(options["outpath"], "make_fragments_temp.cmd")
        F = open(qcmdfile, "w")
        F.write(template)
        F.close()

        try:
            (jobid, output) = ClusterEngine.submit(qcmdfile, options["outpath"] )
        except Exception, e:
            colorprinter.error("An exception occurred during submission to the cluster.")
            colorprinter.error(str(e))
            colorprinter.error(traceback.format_exc())
            sys.exit(ERRCODE_CLUSTER)

        colorprinter.message("\nmake_fragments jobs started with job ID %d. Results will be saved in %s." % (jobid, options["outpath"]))
        logfile.writeToLogfile(datetime.now(), jobid, options["outpath"])


