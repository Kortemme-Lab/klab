#!/usr/bin/env python2
# This work is licensed under the terms of the MIT license. See LICENSE for the full text.

import os
import sys
import inspect
import math
import cPickle as pickle

path_to_this_module = os.path.abspath( os.path.dirname( inspect.getsourcefile(sys.modules[__name__]) ) )

template_file = os.path.join(path_to_this_module, 'template.py')

def process(data_dict, database_run = False, job_dict = None):
    if database_run:
        required_arguments = [
            'numjobs', 'scriptname', 'mem_free',
            'cluster_rosetta_bin',
            'local_rosetta_bin',
            'output_dir',
            'cluster_rosetta_binary_type',
            'local_rosetta_binary_type',
            'db_id',
        ]
        unrequired_arguments = [
            'add_extra_ld_path',
            'numclusterjobs',
            'appname', 'rosetta_args_list',
            'rosetta_binary_type',
        ]
    else:
        required_arguments = [
            'numjobs', 'scriptname', 'mem_free',
            'cluster_rosetta_bin',
            'local_rosetta_bin',
            'appname', 'rosetta_args_list',
            'output_dir',
            'cluster_rosetta_binary_type',
            'local_rosetta_binary_type',
        ]
        unrequired_arguments = [
            'add_extra_ld_path',
            'numclusterjobs',
            'db_id',
        ]

    for arg in required_arguments:
        if arg not in data_dict:
            print 'ERROR: Data dictionary missing argument', arg
            sys.exit(1)

    for arg in unrequired_arguments:
        if arg in data_dict:
            print 'ERROR: Data dictionary cannot contain argument', arg
            sys.exit(1)

    if database_run:
        data_dict['appname'] = ''
            
    # Handle LD paths
    if 'extra_ld_path' in data_dict:
        data_dict['add_extra_ld_path'] = 'True'
    else:
        data_dict['add_extra_ld_path'] = 'False'
        data_dict['extra_ld_path'] = ''

    data_dict['rosetta_args_list'] = ''
    if not database_run:
        # Handle if general rosetta args are a list instead of a string
        if not isinstance(data_dict['rosetta_args_list'], basestring):
            rosetta_args = ""
            if len(data_dict['rosetta_args_list']) == 1:
                rosetta_args += "'%s'" % data_dict['rosetta_args_list']
            elif len(data_dict['rosetta_args_list']) > 1:
                for arg in data_dict['rosetta_args_list'][:-1]:
                    rosetta_args += "'%s', " % arg
                rosetta_args += "'%s'" % data_dict['rosetta_args_list'][-1]
            data_dict['rosetta_args_list'] = rosetta_args

    # Handle other options
    if 'run_from_database' not in data_dict:
        data_dict['run_from_database'] = False

    if 'db_id' not in data_dict:
        data_dict['db_id'] = ''
    
    if 'cluster_rosetta_db' not in data_dict:
        data_dict['cluster_rosetta_db'] = ''

    if 'local_rosetta_db' not in data_dict:
        data_dict['local_rosetta_db'] = ''

    if 'tasks_per_process' not in data_dict or data_dict['tasks_per_process'] == 1:
        data_dict['tasks_per_process'] = 1
        data_dict['numclusterjobs'] = data_dict['numjobs']
    elif data_dict['tasks_per_process'] > 1:
        data_dict['numclusterjobs'] = int(
            math.ceil( float(data_dict['numjobs']) / float(data_dict['tasks_per_process']) )
        )

    if not os.path.isdir(data_dict['output_dir']):
        os.makedirs(data_dict['output_dir'])

    # Check for invalid script name
    if data_dict['scriptname'][0].isdigit():
        data_dict['scriptname'] = 'run_' + data_dict['scriptname']
        
    formatted_data_dict = {}
    for arg in data_dict:
        new_arg = '#$#%s#$#' % arg
        value = data_dict[arg]

        formatted_data_dict[new_arg] = str(data_dict[arg])

    new_lines = []
    with open(template_file, 'r') as f:
        for line in f:
            for arg in formatted_data_dict:
                line = line.replace(arg, formatted_data_dict[arg])
            new_lines.append(line)

    with open(os.path.join(data_dict['output_dir'], '%s.py' % data_dict['scriptname']), 'w') as f:
        for line in new_lines:
            f.write(line)

    output_data_dir = os.path.join(data_dict['output_dir'], 'data')
    
    if not os.path.isdir(output_data_dir):
        os.makedirs(output_data_dir)

    if job_dict != None:
        with open(os.path.join(output_data_dir, 'job_dict.pickle'), 'w') as f:
            pickle.dump(job_dict, f)
