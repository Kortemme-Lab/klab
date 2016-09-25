#!/usr/bin/env python2
# This work is licensed under the terms of the MIT license. See LICENSE for the full text.

import os
import sys
import inspect
import math
import cPickle as pickle
import copy

path_to_this_module = os.path.abspath( os.path.dirname( inspect.getsourcefile(sys.modules[__name__]) ) )

template_file = os.path.join(path_to_this_module, 'template-2.py')

global_list_required_arguments = [
    'cluster_rosetta_bin',
    'local_rosetta_bin',
    'appname', 'rosetta_args_list',
    'cluster_rosetta_binary_type',
    'local_rosetta_binary_type',
]
global_arguments_with_defaults = [
    'cluster_rosetta_db',
    'local_rosetta_db',
]

def convert_list_arguments_to_list(settings, num_steps):
    l = list(global_list_required_arguments)
    l.extend(global_arguments_with_defaults)
    for arg in l:
        if arg in settings:
            settings[arg + '_list'] = [copy.deepcopy(settings[arg]) for x in xrange(num_steps)]
            del( settings[arg] )
    return settings

def format_list_to_string(l):
    assert( not isinstance(l, basestring) )
    return_str = ""
    if len(l) == 1:
        return_str += "'%s'" % str( l[0] )
    elif len(l) > 1:
        for arg in l[:-1]:
            return_str += "'%s', " % str( arg )
        return_str += "'%s'" % str( l[-1] )

    return return_str

class ClusterTemplate():
    def __init__(self, num_steps, settings_dict = None):
        # Defaults
        self.job_dict_template_name = 'job_dict-%d.pickle'
        self.script_template_name = 'run'
        self.settings_dict = None
        with open(template_file, 'r') as f:
            self.template_file_lines = f.readlines()

        self.arguments_with_defaults = global_arguments_with_defaults
        self.list_required_arguments = global_list_required_arguments
        self.list_required_arguments.extend( self.arguments_with_defaults )

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
            'output_dir',
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

        arguments_with_defaults = self.arguments_with_defaults
        for arg in arguments_with_defaults:
            if arg not in settings_dict and arg + '_list' not in settings_dict:
                settings_dict[arg] = ''

        # Handle arguments which used to be single but are now lists (for steps)
        list_required_arguments = self.list_required_arguments

        # Most of the if statements below could be simplified by making format_list_to_string recursive
        for arg in list_required_arguments:
            if arg in settings_dict and arg + '_list' in settings_dict:
                raise Exception("Can't have list and arg versions of settings arg: " + str(arg))

            if arg in settings_dict:
                if arg == 'rosetta_args_list':
                    if not isinstance(settings_dict['rosetta_args_list'], basestring):
                        args_str = format_list_to_string(settings_dict['rosetta_args_list'])
                        settings_dict['rosetta_args_list_list'] = [str(args_str) for x in xrange(self.num_steps)]
                    else:
                        args_str = settings_dict['rosetta_args_list']
                        settings_dict['rosetta_args_list_list'] = ["    ['" + str(args_str) + "']\n" for x in xrange(self.num_steps)]
                else:
                    settings_dict[ arg + '_list' ] = [str(settings_dict[arg]) for x in xrange(self.num_steps)]
                del( settings_dict[arg] )
            elif arg + '_list' in settings_dict:
                if arg == 'rosetta_args_list':
                    subl = ''
                    for l in settings_dict['rosetta_args_list_list']:
                        subl += '    [' + format_list_to_string(l) + '],\n'
                    settings_dict[ 'rosetta_args_list_list' ] = subl
                else:
                    if isinstance(settings_dict[ arg + '_list' ], basestring):
                        settings_dict[ arg + '_list' ] = '[' + format_list_to_string(settings_dict[ arg + '_list' ]) + ']'
            else:
                raise Exception("Missing required argument (in _list form or otherwise): " + str(arg))

        # There once was a way to run from a database, but it is no more, so we set False
        settings_dict['run_from_database'] = 'False'

        # Handle LD paths
        if 'extra_ld_path' in settings_dict:
            settings_dict['add_extra_ld_path'] = 'True'
        else:
            settings_dict['add_extra_ld_path'] = 'False'
            settings_dict['extra_ld_path'] = ''

        # Handle other options
        if 'db_id' not in settings_dict:
            settings_dict['db_id'] = ''

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
        for arg in self.settings_dict:
            new_arg = '#$#%s#$#' % arg
            value = self.settings_dict[arg]

            formatted_settings_dict[new_arg] = str(self.settings_dict[arg])
        self.formatted_settings_dict = formatted_settings_dict

    def verify_internal_data(self):
        first_job_dict_len = len(self.job_dicts[0])
        for job_dict in self.job_dicts[1:]:
            if len(job_dict) != first_job_dict_len:
                print self.job_dicts[0]
                print
                print job_dict
                print first_job_dict_len, len(job_dict)
                raise AssertionError
        for arg in self.list_required_arguments:
            assert( arg + '_list' in self.settings_dict )
        self.format_settings_dict()

    def write_runs(self, script_name_template = None):
        self.verify_internal_data()

        job_pickle_file_relpaths = []
        output_dir = self.settings_dict['output_dir']
        for step_num in xrange(self.num_steps):
            output_data_dir = os.path.join(output_dir, 'data-%d' % step_num)

            job_pickle_file = os.path.join(output_data_dir, self.job_dict_template_name % step_num)
            job_pickle_file_relpaths.append( os.path.relpath(job_pickle_file, output_dir) )

            if not os.path.isdir(output_data_dir):
                os.makedirs(output_data_dir)

            if 'pickle_protocol' in self.formatted_settings_dict:
                pickle_protocol = self.formatted_settings_dict['pickle_protocol']
            else:
                pickle_protocol = 2

            with open(job_pickle_file, 'w') as f:
                pickle.dump(self.job_dicts[step_num], f, protocol = pickle_protocol)

        self.settings_dict['job_pickle_files'] = '[ ' + format_list_to_string(job_pickle_file_relpaths) + ' ]'
        self.format_settings_dict()

        new_lines = []
        for line in self.template_file_lines:
            for arg in self.formatted_settings_dict:
                line = line.replace(arg, self.formatted_settings_dict[arg])
            new_lines.append(line)

        with open(os.path.join(self.settings_dict['output_dir'], '%s.py' % self.script_template_name), 'w') as f:
            for line in new_lines:
                f.write(line)
