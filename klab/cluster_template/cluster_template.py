#!/usr/bin/env python2
# This work is licensed under the terms of the MIT license. See LICENSE for the full text.

import os
import sys
import inspect
import math
import cPickle as pickle

path_to_this_module = os.path.abspath( os.path.dirname( inspect.getsourcefile(sys.modules[__name__]) ) )

template_file = os.path.join(path_to_this_module, 'template-2.py')

def format_list_to_string(l):
    assert( not isinstance(l, basestring) )
    return_str = ""
    if len(l) == 1:
        return_str += "'%s'" % l
    elif len(l) > 1:
        for arg in l[:-1]:
            return_str += "'%s', " % arg
        return_str += "'%s'" % l[-1]

    return return_str

class ClusterTemplate():
    def __init__(self, num_steps, settings_dict = None):
        # Defaults
        self.job_dict_template_name = 'job_dict-%d.pickle'
        self.script_template_name = 'run'
        self.settings_dict = None
        with open(template_file, 'r') as f:
            self.template_file_lines = f.readlines()

        # Arguments
        self.num_steps = num_steps
        assert( num_steps > 0 )
        self.job_dicts = [{} for x in xrange(num_steps)]
        if settings_dict:
            self.set_settings_dict(settings_dict)

    def set_job_dict(self, job_dict, step_num = 0):
        self.job_dicts[step_num] = job_dict

    def set_script_template_name(self, script_template_name):
        # Check for invalid script name
        if script_template_name[0].isdigit():
            script_template_name = 'run_' + script_template_name
        self.script_template_name = script_template_name

    def set_job_dict_template_name(self, job_dict_template_name):
        if '%d' not in job_dict_template_name:
            job_dict_template_name += '-%d'
        self.job_dict_template_name = job_dict_template_name

    def set_settings_dict(self, settings_dict):
        if 'job_dict_template_name' in settings_dict:
            self.job_dict_template_name = settings_dict['job_dict_template_name']

        required_arguments = [
            'numjobs', 'mem_free',
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
            'run_from_database',
            'db_id',
        ]

        for arg in required_arguments:
            if arg not in settings_dict:
                print 'ERROR: Data dictionary missing argument', arg
                sys.exit(1)

        for arg in unrequired_arguments:
            if arg in settings_dict:
                print 'ERROR: Data dictionary cannot contain argument', arg
                sys.exit(1)

        # There once was a way to run from a database, but it is no more, so we set False
        settings_dict['run_from_database'] = 'False'

        # Handle LD paths
        if 'extra_ld_path' in settings_dict:
            settings_dict['add_extra_ld_path'] = 'True'
        else:
            settings_dict['add_extra_ld_path'] = 'False'
            settings_dict['extra_ld_path'] = ''

        # Handle if general rosetta args are a list instead of a string
        if not isinstance(settings_dict['rosetta_args_list'], basestring):
            settings_dict['rosetta_args_list'] = format_list_to_string(settings_dict['rosetta_args_list'])

        # Handle other options
        if 'db_id' not in settings_dict:
            settings_dict['db_id'] = ''

        if 'cluster_rosetta_db' not in settings_dict:
            settings_dict['cluster_rosetta_db'] = ''

        if 'local_rosetta_db' not in settings_dict:
            settings_dict['local_rosetta_db'] = ''

        if 'tasks_per_process' not in settings_dict or settings_dict['tasks_per_process'] == 1:
            settings_dict['tasks_per_process'] = 1
            settings_dict['numclusterjobs'] = settings_dict['numjobs']
        elif settings_dict['tasks_per_process'] > 1:
            settings_dict['numclusterjobs'] = int(
                math.ceil( float(settings_dict['numjobs']) / float(settings_dict['tasks_per_process']) )
            )

        if not os.path.isdir(settings_dict['output_dir']):
            os.makedirs(settings_dict['output_dir'])

        if 'scriptname' in settings_dict:
            self.set_script_template_name(settings_dict['scriptname'])

        self.settings_dict = settings_dict

    def format_settings_dict(self):
        formatted_settings_dict = {}
        for arg in settings_dict:
            new_arg = '#$#%s#$#' % arg
            value = settings_dict[arg]

            formatted_settings_dict[new_arg] = str(settings_dict[arg])
        self.formatted_settings_dict = formatted_settings_dict

    def verify_internal_data(self):
        first_job_dict_len = len(self.job_dicts[0])
        for job_dict in self.job_dicts[1:]:
            assert( len(job_dict) == first_job_dict_len )

    def write_runs(self, script_name_template = None):
        self.verify_internal_data()

        job_pickle_file_relpaths = []
        for step_num in xrange(self.num_steps):
            output_data_dir = os.path.join(self.formatted_settings_dict['output_dir'], 'data-%d' % step_num)

            job_pickle_file = os.path.join(output_data_dir, self.job_dict_template_name % step_num)
            job_pickle_file_relpaths.append( os.path.relpath(job_pickle_file, output_data_dir) )

            if not os.path.isdir(output_data_dir):
                os.makedirs(output_data_dir)

            if 'pickle_protocol' in self.formatted_settings_dict:
                pickle_protocol = self.formatted_settings_dict['pickle_protocol']
            else:
                pickle_protocol = 2

            with open(job_pickle_file, 'w') as f:
                pickle.dump(self.job_dicts[step_num], f, protocol = pickle_protocol)

        self.settings_dict['job_pickle_files'] = format_list_to_string(job_pickle_file_relpaths)
        self.format_settings_dict()

        new_lines = []
        for line in self.template_file_lines:
            for arg in self.formatted_settings_dict:
                line = line.replace(arg, formatted_settings_dict[arg])
            new_lines.append(line)

        with open(os.path.join(self.formatted_settings_dict['output_dir'], '%s.py' % self.script_template_name), 'w') as f:
            for line in new_lines:
                f.write(line)
