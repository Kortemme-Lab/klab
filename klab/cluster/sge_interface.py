import os
import string
import re
import subprocess

from klab.fs.fsio import read_file
from klab import colortext
from cluster_interface import JobInitializationException

available_queues = {
    'QB3' : ['lab.q', 'long.q', 'short.q'],
}

def create_script(job_name, job_directory,
                  job_data_arrays = '', job_setup_commands = '', job_execution_commands = '', job_post_processing_commands = '',
                  architecture = 'linux-x64', num_tasks = 1, memory_in_GB = 2, scratch_space_in_GB = 1,
                  runtime_string = '24:00:00', queues = ['long.q'], cluster = 'QB3'):
    '''This function uses python_script_template to create a script that can execute on the cluster. The template has
       useful boiler-plate functionality and contains Genshi-style substitution syntax - strings of the form ${varname}
       inside the template (typically syntax errors) are meant to be replaced with valid code. This function performs
       the substitutions and returns a hopefully valid cluster script.

       Note that we do not use standard Python-style subsitution syntax as this breaks if you use curly braces in another
       context e.g. dict definition (even though you can define dicts without braces).
       '''

    allowed_queues = available_queues[cluster]

    # Check inputs
    try: assert(int(num_tasks) > 0 and str(num_tasks).isdigit())
    except: raise JobInitializationException('numtasks should be a non-zero integer.')

    try: assert(int(memory_in_GB) > 0 and str(memory_in_GB).isdigit())
    except: raise JobInitializationException('memory_in_GB should be a non-zero integer.')

    try: assert(int(scratch_space_in_GB) > 0 and str(scratch_space_in_GB).isdigit())
    except: raise JobInitializationException('scratch_space_in_GB should be a non-zero integer.')

    mtches = re.match('(\d{1,2}):(\d{1,2}):(\d{1,2})', runtime_string)
    try:
        assert(mtches != None)
        assert(int(mtches.group(2)) < 60)
        assert(int(mtches.group(3)) < 60)
    except:
        raise JobInitializationException('The runtime parameter should be given in the format HH:MM:SS.')

    if not queues:
        raise JobInitializationException("A cluster queue must be specified.")
    if 'short.q' in queues:
        # NOTE: This if/elif block is specific to the QB3 cluster system and is only included for the benefit of QB3 users. Delete this line or alter it to fit your SGE cluster queue names.
        if not len(queues) == 1:
            raise JobInitializationException("The short queue cannot be specified if any other queue is specified.")
    for q in queues:
        if not (q in allowed_queues):
            raise JobInitializationException("The queue you specified (%s) is invalid. Please use any or either of %." % (options['queue'], ', '.join(allowed_queues)))

    # Create the script
    header = '''
#!/usr/bin/python
#$ -S /usr/bin/python
#$ -N {job_name}
#$ -o {job_directory}
#$ -e {job_directory}
#$ -cwd
#$ -r y
#$ -t 1-{num_tasks}
#$ -l arch={architecture}
#$ -l mem_free={memory_in_GB}G
#$ -l scratch={scratch_space_in_GB}G
#$ -l h_rt={runtime_string}
    '''.format(**locals())
    if queues:
        queues = ','.join(queues)
        header = header.strip() + '\n#$ -q {queues}'.format(**locals())

    template_file = os.path.join(os.path.split(os.path.realpath(__file__))[0], 'python_script_template.py')
    template = read_file(template_file)
    template = template.replace('${JOB_NAME}', job_name)
    template = template.replace('${JOB_DATA_ARRAYS}', '%s' % job_data_arrays.strip())
    template = template.replace('${JOB_SETUP_COMMANDS}', '%s' % job_setup_commands.strip())
    template = template.replace('${JOB_EXECUTION_COMMANDS}', '%s' % job_execution_commands.strip())
    template = template.replace('${JOB_POST_PROCESSING_COMMANDS}', '%s' % job_post_processing_commands.strip())
    return '\n\n'.join(map(string.strip, [header, template]))


def submit(command_filename, workingdir, send_mail = False, username = None):
    '''Submit the given command filename to the queue. Adapted from the qb3 example.'''

    # Open streams
    command_filename = command_filename
    outfile = command_filename + ".out"
    file_stdout = open(outfile, 'w')

    # Form command
    command = ['qsub']

    if send_mail and username:
        #username = 'Shane.OConnor@ucsf.edu'
        command.extend(['-m', 'eas', '-M', '%s@chef.compbio.ucsf.edu' % username])
    command.append(command_filename)

    # Submit the job and capture output.
    try:
        subp = subprocess.Popen(command, stdout=file_stdout, stderr=file_stdout, cwd=workingdir)
    except Exception, e:
        colortext.error('Failed running qsub command: %s in cwd %s.' % (command, workingdir))
        raise

    waitfor = 0
    errorcode = subp.wait()
    file_stdout.close()

    file_stdout = open(outfile, 'r')
    output = file_stdout.read().strip()
    file_stdout.close()

    if errorcode != 0:
        colortext.error('Failed running qsub command: %s in cwd %s.' % (command, workingdir))
        if output.find("unable to contact qmaster") != -1:
            raise Exception("qsub failed: unable to contact qmaster")
        else:
            raise Exception(output)

    # Match job id
    # This part of the script may be error-prone as it depends on the server message.
    matches = re.match('Your job-array (\d+).(\d+)-(\d+):(\d+)', output)
    if not matches:
        matches = re.match('Your job (\d+) \(".*"\) has been submitted.*', output)

    if matches:
        jobid = int(matches.group(1))
    else:
        jobid = -1

    output = output.replace('"', "'")
    if output.startswith("qsub: ERROR"):
        raise Exception(output)

    os.remove(outfile)
    #os.remove(command_filename)

    return jobid, output
