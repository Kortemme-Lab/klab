#!/usr/bin/env python2
# -*- mode:python;show-trailing-whitespace:t; -*-

import getpass
import string

def choose_user(user=None):
    if user is not None:
        return user
    else:
        return getpass.getuser()

def choose_project(project=None, user=None):
    if project is not None:
        return project
    else:
        if user == None:
            user = choose_user(user)
        return sh('''\
                qconf -suser {user} |
                grep default_project |
                awk '{{print $2}}' ''')

def sh(cmd):
    """
    Run the given command in a shell.

    The command should be a single string containing a shell command.  If the
    command contains the names of any local variables enclosed in braces, the
    actual values of the named variables will be filled in.  (Note that this
    works on variables defined in the calling scope, which is a little bit
    magical.)  Regular braces must be escaped as you would with str.format().
    Also be aware that this approach is vulnerable to shell injection attacks.
    """

    # Figure out what local variables are defined in the calling scope.

    import inspect
    frame = inspect.currentframe()
    try: locals = frame.f_back.f_locals
    finally: del frame

    # Run the given command in a shell.  Return everything written to stdout if
    # the command returns an error code of 0, otherwise raise an exception.

    from subprocess import Popen, PIPE, CalledProcessError
    process = Popen(cmd.format(**locals), shell=True, stdout=PIPE)
    stdout, unused_stderr = process.communicate()
    retcode = process.poll()
    if retcode:
        error = subprocess.CalledProcessError(retcode, cmd)
        error.output = stdout
        raise error
    return stdout.strip()

if __name__ == '__main__':
    my_user = choose_user()
    my_project = choose_project( user = my_user )

    qstat_output = sh('qstat -ext -u \\*').split('\n')

    my_jobs = {}
    jobs_by_project = {}

    lab_jobs = {}

    for line in qstat_output[2:]:
        fields = line.split()
        state = fields[7]
        name = fields[3]
        user = fields[4]
        project = fields[5]
        if 'r' in state:
            queue = fields[17].split('@')[0]
            slots = int(fields[18])
        else:
            queue = 'Waiting/Other'
            slots = int(fields[14])
        if user == my_user:
            if name not in my_jobs:
                my_jobs[name] = {}
            if queue not in my_jobs[name]:
                my_jobs[name][queue] = slots
            else:
                my_jobs[name][queue] += slots
        elif project == my_project:
            if user not in lab_jobs:
                lab_jobs[user] = {}
            if queue not in lab_jobs[user]:
                lab_jobs[user][queue] = slots
            else:
                lab_jobs[user][queue] += slots

        if project not in jobs_by_project:
            jobs_by_project[project] = {}
        if queue not in jobs_by_project[project]:
            jobs_by_project[project][queue] = slots
        else:
            jobs_by_project[project][queue] += slots

    if len(my_jobs) > 0:
        print 'Jobs for user %s:' % my_user
        for name in my_jobs:
            print '%s:' % string.rjust(name, 10)
            for num_jobs, queue in sorted([(num_jobs, queue) for queue, num_jobs in my_jobs[name].iteritems()], reverse = True):
                print '           %s: %d' % (queue, num_jobs)
        print

    if my_project in jobs_by_project:
        print 'Total jobs for lab %s:' % my_project
        for num_jobs, queue in sorted([(num_jobs, queue) for queue, num_jobs in jobs_by_project[my_project].iteritems()], reverse = True):
            print '%s: %d' % (string.rjust(queue, 8), num_jobs)
        print

    if len(lab_jobs) > 0:
        print 'Jobs for each other user in %s:' % my_project
        for user in sorted(lab_jobs.keys()):
            print '%s:' % user
            for num_jobs, queue in sorted([(num_jobs, queue) for queue, num_jobs in lab_jobs[user].iteritems()], reverse = True):
                print '%s: %d' % (string.rjust(queue, 20), num_jobs)
        print

    if len(jobs_by_project) > 0:
        job_count_per_lab = {}
        total_all_labs = 0
        for project in jobs_by_project:
            total_jobs = sum([num_jobs for queue, num_jobs in jobs_by_project[project].iteritems() if queue != 'Waiting/Other'])
            job_count_per_lab[project] = total_jobs
            total_all_labs += total_jobs

        print 'Running jobs for all labs (and %% total):'
        for num_jobs, project in sorted([(num_jobs, project) for project, num_jobs in job_count_per_lab.iteritems()], reverse = True):
            print '%s: %d (%.1f%%)' % (string.rjust(project, 20), num_jobs, float(num_jobs)/float(total_all_labs)*100.0)
