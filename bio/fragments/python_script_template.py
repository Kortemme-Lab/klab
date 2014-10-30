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
    subp = subprocess.Popen([str(arg) for arg in args], stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=outdir, env={'SPARKSXDIR' : '/netapp/home/klabqb3backrub/tools/sparks-x'})
    output = subp.communicate()
    return ProcessOutput(output[0], output[1], subp.returncode) # 0 is stdout, 1 is stderr

def shell_execute(command_line):
    subp = subprocess.Popen(shlex.split(command_line), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    output = subp.communicate()
    return ProcessOutput(output[0], output[1], subp.returncode) # 0 is stdout, 1 is stderr

def create_scratch_path():
    path = tempfile.mkdtemp(dir = '/scratch')
    if not os.path.isdir(path):
        raise os.error
    return path

def print_tag(tag_name, content):
    print('<%s>%s</%s>' % (tag_name, content, tag_name))

task_id = os.environ.get('SGE_TASK_ID')
job_id = os.environ.get('JOB_ID')
array_idx = int(task_id) - 1
job_root_dir = None

print('<make_fragments job_id="%s" task_id="%s">' % (job_id, task_id))

print_tag("start_time", strftime("%Y-%m-%d %H:%M:%S"))
print_tag("host", socket.gethostname())
print_tag("arch", platform.machine() + ', ' + platform.processor() + ', ' + platform.platform())

# Set up scratch directory
scratch_path = create_scratch_path()

print_tag("cwd", scratch_path)

***
# JOB-SPECIFIC SETUP
chains = ['B', 'B']
pdb_ids = ['0050', '4un3']
fasta_files = ['/home/oconchus/dev/tools/bio/fragments/rpache_run/0050B/0050B.fasta', '/home/oconchus/dev/tools/bio/fragments/rpache_run/4un3B/4un3B.fasta']

chain = chains[array_idx]
pdb_id = pdb_ids[array_idx]
fasta_file = fasta_files[array_idx]
job_root_dir = os.path.split(fasta_file)[0]

# Copy resources
shutil.copy(fasta_file, scratch_path)

print("<cmd>")
cmd_args = [c for c in ['/home/oconchus/dev/tools/bio/fragments/make_fragments_RAP_cluster.pl', '-verbose', '-id', pdb_id + chain, '', '-frag_sizes 3,9', '-n_frags 200', '-n_candidates 1000', fasta_file] if c]
print(' '.join(cmd_args))
print("</cmd>")

os.remove(fasta_file)
***

if not os.path.exists(job_root_dir):
    raise Exception("You must set the job's root directory so that the script can clean up the job.")

print("<output>")
***
# JOB-SPECIFIC COMMANDS
subp = Popen(scratch_path, cmd_args)
sys.stdout.write(subp.stdout)

if True:
    print("<gzip>")
    for f in glob.glob(os.path.join(scratch_path, "*mers")) + [os.path.join(scratch_path, 'ss_blast')]:
        if os.path.exists(f):
            subpzip = Popen(scratch_path, ['gzip', f])
            print(f)
    print("</gzip>")
***
print("</output>")

# Copy files from scratch back to /netapp
os.rmdir(job_root_dir)
shutil.copytree(scratch_path, job_root_dir)
shutil.rmtree(scratch_path)

# Get task run details
task_usages = shell_execute('qstat -j %s' % job_id)
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
    
print_tag("end_time", strftime("%Y-%m-%d %H:%M:%S"))

print("</make_fragments>")

if subp.errorcode != 0:
    sys.stderr.write(subp.stderr)
    sys.exit(subp.errorcode)
