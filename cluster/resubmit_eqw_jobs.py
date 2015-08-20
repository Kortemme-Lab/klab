#!/usr/bin/python
# encoding: utf-8
"""
resubmit_eqw_jobs.py

Created by Shane O'Connor 2015.
Simple script to resubmit any SGE jobs with Eqw status.
If your jobs failed for no good reason (run "qstat -explain c -j <job_id>" to see why they failed) then this script can be used to resubmit them.

Note: While writing this, I found out that there is an XML output option from qstat. This should be the direction to take instead.
"""

import sys
import traceback
import datetime
import subprocess
import pprint
import shlex
import re
import getpass


def get_jobs_by_state(stdout):
    js = {}
    jobs = get_jobs(stdout)
    for j in jobs:
        js[j['state']] = js.get(j['state'], [])
        js[j['state']].append(j)
    return js


def get_jobs(stdout, username = None):
    found_header = False
    start_parsing = False # if errors occur e.g. contacting hosts, these are printed before the header line - this allows us to ignore them
    jobs = []
    if not username:
        username = getpass.getuser()
    for l in stdout.split('\n'):
        if start_parsing:
            try:
                tokens = l.split()
                d = dict(
                    id = int(tokens[0]),
                    priority = float(tokens[1]),
                )            
                job_name = l[l.find(tokens[1]) + len(tokens[1]):l.find(username)].strip() # in case the job name contains spaces
                d['job_name'] = job_name
                d['username'] = username
                tokens = l[l.find(username) + len(username):].strip().split()
                d['state'] = tokens[0]
                d['submit_date'] = datetime.datetime.strptime('{0} {1}'.format(tokens[1], tokens[2]), '%m/%d/%Y %H:%M:%S')
                if tokens[3].find('q'):
                    d['queue'] = tokens[3]
                    tokens = tokens[3:]
                else:
                    tokens = tokens[2:]
                d['slots'] = tokens[0]
                task_ids = []
                task_ranges = tokens[1].split(',')
                for tr in task_ranges:
                    if tr.isdigit():
                        task_ids.append(int(tr))
                    else:
                        mtchs = re.match('(\d+)-(\d+):(\d+)', tr)
                        assert(mtchs)
                        # I do not know what the third number represents so I will ignore it in the parsing for now
                        task_ids.extend(range(int(mtchs.group(1)), int(mtchs.group(2)) + 1))                  
                        assert(tr.find(':') != -1 and tr.find('-') != -1)
                d['task_ids'] = task_ids            
                jobs.append(d)
            except:
                print('ERROR PARSING "{0}". LINE IGNORED.'.format(l))
        else:
            if not found_header:
                if l.startswith('job-ID'):
                    assert(l.split() == ['job-ID', 'prior', 'name', 'user', 'state', 'submit/start', 'at', 'queue', 'slots', 'ja-task-ID'])
                    found_header = True
            else:
                assert((len(l) > 1) and list(set(list(l.strip()))) == ['-'])
                start_parsing = True
    return jobs


class qmod(object):
    '''This should be moved into a submodule and the functions here turned into module functions.'''    
    @staticmethod
    def cj(job_ids):
        '''Simple implementation where joblist is expected to be a list of integers (job ids). The full grammar for this command allows more granular control.''' 
        for job_id in job_ids:
            job_id_types = set(map(type, job_ids))
            assert(len(job_id_types) == 1 and type(1) == job_id_types.pop())
            args = shlex.split('qmod -cj {0}'.format(job_id))
            subprocess.call(args, shell=False)


def resubmit_eqw_jobs():
    p = subprocess.Popen('qstat', stdout=subprocess.PIPE)
    stdout, stderr = p.communicate()
    if p.returncode != 0:
        print('An exception running qstat.')
        sys.exit(1)
    stdout = stdout.strip()
    try:
        jobs = get_jobs_by_state(stdout)
        eqw_jobs = []
        for j in jobs.get('Eqw', []):
            eqw_jobs.append(j['id'])
        if not eqw_jobs:
            print('No jobs with Eqw state were found.')
        qmod.cj(eqw_jobs)
    except Exception, e:
        print('An exception occurred in the parsing function. It probably needs to be fixed or updated.')
        print(str(e))
        print(traceback.format_exc())
        sys.exit(2)


if __name__ == '__main__':
    resubmit_eqw_jobs()


