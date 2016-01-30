#!/usr/bin/env python2
# This work is licensed under the terms of the MIT license. See LICENSE for the full text.

from cluster_template import ClusterTemplate

def process(data_dict, database_run = False, job_dict = None):
    cluster_template = ClusterTemplate(1, settings_dict = data_dict)
    cluster_template.set_job_dict(job_dict)
    cluster_template.write_runs()
