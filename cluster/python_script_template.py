import sys
from time import strftime
import socket
import os
import platform
import subprocess
import tempfile
import shutil
import glob
import re
import shlex
import traceback


# Utility functions

class ProcessOutput(object):

    def __init__(self, stdout, stderr, errorcode):
        self.stdout = stdout
        self.stderr = stderr
        self.errorcode = errorcode

    def getError(self):
        if self.errorcode != 0:
            return("Errorcode: %d\n%s" % (self.errorcode, self.stderr))
        return None

def Popen(outdir, args):
    subp = subprocess.Popen(shlex.split(" ".join([str(arg) for arg in args])), stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=outdir, env={'SPARKSXDIR' : '/netapp/home/klabqb3backrub/tools/sparks-x'})
    output = subp.communicate()
    return ProcessOutput(output[0], output[1], subp.returncode) # 0 is stdout, 1 is stderr

def shell_execute(command_line):
    subp = subprocess.Popen(command_line, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    output = subp.communicate()
    return ProcessOutput(output[0], output[1], subp.returncode) # 0 is stdout, 1 is stderr

def create_scratch_path():
    path = tempfile.mkdtemp(dir = '/scratch')
    if not os.path.isdir(path):
        raise os.error
    return path

def print_tag(tag_name, content):
    print('<%s>%s</%s>' % (tag_name, content, tag_name))

def print_subprocess_output(subp):
    '''Prints the stdout and stderr output.'''
    if subp:
        if subp.errorcode != 0:
            print('<error errorcode="%s">' % str(subp.errorcode))
            print(subp.stderr)
            print("</error>")
            print_tag('stdout', '\n%s\n' % subp.stdout)
        else:
            print_tag('success', '\n%s\n' % subp.stdout)
            print_tag('warnings', '\n%s\n' % subp.stderr)


# Job/task parameters

task_id = os.environ.get('SGE_TASK_ID')
job_id = os.environ.get('JOB_ID')
array_idx = int(task_id) - 1              # this can be used to index Python arrays (0-indexed) rather than task_id (based on 1-indexing)
task_root_dir = None
subp = None
errorcode = 0 # failed jobs should set errorcode


# Markup opener
print('<task type="${JOB_NAME}" job_id="%s" task_id="%s">' % (job_id, task_id))


# Standard task properties - start time, host, architecture
print_tag("start_time", strftime("%Y-%m-%d %H:%M:%S"))
print_tag("host", socket.gethostname())
print_tag("architecture", platform.machine() + ', ' + platform.processor() + ', ' + platform.platform())


# Set up a scratch directory on the node
scratch_path = create_scratch_path()
print_tag("cwd", scratch_path)


# Job data arrays. This section defines arrays that are used for tasks.
${JOB_DATA_ARRAYS}


# Job setup. The job's root directory must be specified inside this block.
${JOB_SETUP_COMMANDS}
if not os.path.exists(task_root_dir):
    raise Exception("You must set the task's root directory so that the script can clean up the job.")


# Job execution block. Note: failed jobs should set errorcode.
print("<output>")
${JOB_EXECUTION_COMMANDS}
print("</output>")


# Post-processing. Copy files from scratch back to /netapp.
# Caveat: We assume here that task_root_dir should be empty.
os.rmdir(task_root_dir)
shutil.copytree(scratch_path, task_root_dir)
shutil.rmtree(scratch_path)
${JOB_POST_PROCESSING_COMMANDS}

# Print task run details. The full path to qstat seems necessary on the QB3 cluster if you are not using a bash shell.
task_usages = shell_execute('/usr/local/sge/bin/linux-x64/qstat -j %s' % job_id)
if task_usages.errorcode == 0:
  try:
    print("<qstat>")
    print(task_usages.stdout)
    print("</qstat>")
    mtchs = re.match('.*?usage\s*(\d+):(.*?)\n.*', task_usages.stdout, re.DOTALL)
    print(mtchs)
    if mtchs and str(mtchs.group(1)) == str(task_id):
      task_properties = [s.strip() for s in mtchs.group(2).strip().split(",")]
      for tp in task_properties:
         if tp:
           prp=tp.split('=')[0]
           v=tp.split('=')[1]
           print('<task_%s>%s</task_%s>' % (prp, v, prp))
  except Exception, e:
    print('<qstat_parse_error>')
    print(str(e))
    print(traceback.format_exc())
    print('</qstat_parse_error>')
else:
    print_tag('qstat_error', task_usages.stderr)


# Print the end walltime and close the outer tag
print_tag("end_time", strftime("%Y-%m-%d %H:%M:%S"))
print("</task>")


# Exit the job with the errorcode set in the execution block
if errorcode != 0:
    sys.exit(subp.errorcode)
