#!/usr/bin/python
# encoding: utf-8
"""
SGE.py
Fragment generation submission module for the Sun Grid Engine.

Created by Shane O'Connor 2013

Use this as a basis for your cluster system module. The following functionality should be provided:
    - A FragmentsJob class for array runs which creates a script object member to be used by the caller;
    - a submit function which takes a command_filename e.g. cluster script and a working directory in which to run the script;
    - a query function which takes a logfile path and an optional job ID and returns information, via the cluster scheduler, about all jobs (if job ID is not specified) or else the specified job;
    - a check function which takes a logfile path and an optional job ID. This is similar to the query function but describes whether the job has finished or not.
"""

import sys
import os
import re
import subprocess

sys.path.insert(0, "..")
from klab.bio.fragments.utils import colorprinter
from klab.cluster import sge_interface
import klab.cluster.sge_interface


# todo: move these into a common file e.g. utils.py
ERRCODE_ARGUMENTS = 1
ERRCODE_CLUSTER = 2
ERRCODE_OLDRESULTS = 3
ERRCODE_CONFIG = 4
ERRCODE_NOOUTPUT = 5
ERRCODE_JOBFAILED = 6
ERRCODE_MISSING_FILES = 1

ClusterType = "SGE"


class FragmentsJob(object):

    # The command line used to call the fragment generating script. Add -noporter into cmd below to skip running Porter
    cmd = 'make_fragments_RAP_cluster.pl -verbose -id %(pdbid)s%(chain)s %(no_homologs)s %(fasta)s'

    def __init__(self, make_fragments_perl_script, options, test_mode = False):

        # Check the options
        required_options = set(['queue', 'jobname', 'outpath', 'runtime', 'memfree', 'scratch', 'job_inputs', 'no_homologs', 'frag_sizes', 'n_frags', 'n_candidates', 'no_zip'])
        assert(sorted(set(options.keys()).intersection(required_options)) == sorted(required_options))

        self.make_fragments_perl_script = make_fragments_perl_script
        self.options = options
        self.test_mode = test_mode
        self._set_script_header_parameters()
        self._create_script()


    def _set_script_header_parameters(self):
        options = self.options

        self.queues = self.options['queue'] or ['long.q']
        if 'short.q' in self.queues:
            self.test_mode = True

        self.jobname = options['jobname']
        self.job_directory = options['outpath']
        if self.test_mode:
            self.runtime_string = '0:29:00'
        else:
            self.runtime_string = '%d:00:00' % int(self.options['runtime'])

        if self.test_mode:
            self.memory_in_GB = 2
            self.scratch_space_in_GB = 1
        else:
            self.memory_in_GB = int(self.options['memfree'])
            self.scratch_space_in_GB = int(self.options['scratch'])
        self.num_tasks = len(options['job_inputs'])


    def _create_script(self):
        options = self.options

        # Create the data arrays
        job_inputs = options['job_inputs']
        job_data_arrays = []
        job_data_arrays.append('chains = %s' % str([ji.chain for ji in job_inputs]))
        job_data_arrays.append('pdb_ids = %s' % str([ji.pdb_id for ji in job_inputs]))
        job_data_arrays.append('fasta_files = %s' % str([ji.fasta_file for ji in job_inputs]))
        self.job_data_arrays = '\n'.join(job_data_arrays)

        # Create the setup commands
        self.job_setup_commands = '''
chain = chains[array_idx]
pdb_id = pdb_ids[array_idx]
fasta_file = fasta_files[array_idx]
task_root_dir = os.path.split(fasta_file)[0]
job_root_dir = os.path.split(task_root_dir)[0]
print_tag('job_root_dir', job_root_dir)

sys.path.insert(0, job_root_dir)
from post_processing import post_process

# Copy resources
shutil.copy(fasta_file, scratch_path)
'''
        # Create the main task execution commands
        make_fragments_perl_script = self.make_fragments_perl_script
        no_homologs = options['no_homologs']
        frag_sizes = '-frag_sizes %s' % ','.join(map(str, options['frag_sizes']))
        n_frags = '-n_frags %d' % options['n_frags']
        n_candidates = '-n_candidates %d' % options['n_candidates']
        zip_files = str(not(options['no_zip']))
        #has_segment_mapping = options['has_segment_mapping']

        self.job_execution_commands = '''
cmd_args = [c for c in ['%(make_fragments_perl_script)s', '-verbose', '-id', pdb_id + chain, '%(no_homologs)s', '%(frag_sizes)s', '%(n_frags)s', '%(n_candidates)s', fasta_file] if c]
print_tag('cmd', ' '.join(cmd_args))

subp = Popen(scratch_path, cmd_args)
sys.stdout.write(subp.stdout)

if %(zip_files)s:
    print("<gzip>")
    for f in glob.glob(os.path.join(scratch_path, "*mers")) + [os.path.join(scratch_path, 'ss_blast')]:
        if os.path.exists(f):
            subpzip = Popen(scratch_path, ['gzip', f])
            print(f)
    print("</gzip>")

os.remove(fasta_file)
''' % locals()

        self.job_post_processing_commands = '''
# Run post-processing script
task_dirname = os.path.split(task_root_dir)[1]
post_process(task_dirname)
''' % locals()

        self.script = sge_interface.create_script(self.jobname, self.job_directory,
                  job_data_arrays = self.job_data_arrays, job_setup_commands = self.job_setup_commands, job_execution_commands = self.job_execution_commands, job_post_processing_commands = self.job_post_processing_commands,
                  architecture = 'linux-x64', num_tasks = self.num_tasks, memory_in_GB = self.memory_in_GB, scratch_space_in_GB = self.scratch_space_in_GB,
                  runtime_string = self.runtime_string, queues = self.queues)


def submit(command_filename, workingdir, send_mail = False, username = None):
    '''Submit the given command filename to the queue. Adapted from the qb3 example.'''
    return sge_interface.submit(command_filename, workingdir, send_mail = send_mail, username = username)


def query(logfile, jobID = None):
    """If jobID is an integer then return False if the job has finished and True if it is still running.
       Otherwise, returns a table of jobs run by the user."""
    
    joblist = logfile.readFromLogfile()
    if jobID and type(jobID) == type(1):
        command = ['qstat', '-j', str(jobID)]
    else:
        command = ['qstat']

    processoutput = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()
    output = processoutput[0]
    serror = processoutput[1]
    # Form command
    jobs = {}
    if type(jobID) == type(1):
        if serror.find("Following jobs do not exist") != -1:
            return False
        else:
            return True

    if not output.strip():
        colorprinter.message("No jobs running at present.")
    output = output.strip().split("\n")
    if len(output) > 2:
        for line in output[2:]:
            # We assume that our script names contain no spaces for the parsing below to work
            tokens = line.split()
            jid = int(tokens[0])
            jobstate = tokens[4]

            details = {  "jobid" : jid,
                         "prior" : tokens[1],
                         "name" : tokens[2],
                         "user" : tokens[3],
                         "state" : jobstate,
                         "submit/start at" : "%s %s" % (tokens[5], tokens[6])
                         }
            jataskID = 0
            if jobstate == "r":
                details["queue"] = tokens[7]
                details["slots"] = tokens[8]
            elif jobstate == "qw":
                details["slots"] = tokens[7]
                if len(tokens) >= 9:
                    jataskID = tokens[8]
                    details["ja-task-ID"] = jataskID

            if len(tokens) > 9:
                jataskID = tokens[9]
                details["ja-task-ID"] = jataskID

            jobs[jid] = jobs.get(jid) or {}
            jobs[jid][jataskID] = details
            if joblist.get(jid):
                jobdir = joblist[jid]["Directory"]
                jobtime = joblist[jid]["TimeInSeconds"]
                colorprinter.message("Job %d submitted %d minutes ago. Status: '%s'. Destination directory: %s." % (jid, jobtime / 60, jobstate, jobdir))
            else:
                colorprinter.message("Job %d submitted at %s %s. Status: '%s'. Destination directory unknown." % (jid, tokens[5], tokens[6], jobstate))
        return True


def check(logfile, job_id, cluster_job_name):
    # todo: this needs to be updated for array jobs
    errors = []
    joblist = logfile.readFromLogfile()
    jobIsRunning = query(logfile, job_id)
    if not joblist.get(job_id):
        if not jobIsRunning:
            errors.append("Job %d is not running but also has no entry in the logfile %s." % (job_id, logfile.getName()))
        else:
            errors.append("Job %d is running but has no entry in the logfile %s." % (job_id, logfile.getName()))
    else:
        cname = cluster_job_name
        dir = joblist[job_id]["Directory"]
        if not jobIsRunning:
            outputfile = os.path.join(dir, "%(cname)s.o%(job_id)d" % vars())
            if os.path.exists(outputfile):
                F = open(outputfile, "r")
                contents = F.read()
                F.close()
                success = re.compile('''Done!\s*</output>\s*<enddate>(.*?)</enddate>\s*</make_fragments>\s*$''', re.DOTALL)
                match = success.search(contents)
                if match:
                    colorprinter.message("Job %d finished successfully on %s. Results are in %s." % (job_id, match.groups(1)[0].strip(), dir))
                else:
                    errors.append("Job %d has finished running but was not successful. Results are in %s." % (job_id, dir))
                    errcode = ERRCODE_JOBFAILED
            else:
                    errors.append("The output file %s associated with job %d could not be found. Searched in %s." % (outputfile, job_id, dir))
                    errcode = ERRCODE_NOOUTPUT
        else:
            colorprinter.warning("Job %d is still running. Results are being stored in %s." % (job_id, dir))
    return errors
