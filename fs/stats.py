#!/usr/bin/python
# encoding: utf-8
"""
stats.py
For filesystem statistics functions
"""

import subprocess

df_conversions = {
    'MB': float(2 ** 10),
    'GB': float(2 ** 20),
    'TB': float(2 ** 30),
}

def df(unit = 'GB'):
    '''A wrapper for the df shell command.'''
    details = {}
    headers = ['Filesystem', 'Type', 'Size', 'Used', 'Available', 'Use%', 'MountedOn']
    n = len(headers)

    unit = df_conversions[unit]
    p = subprocess.Popen(args = ['df', '-T'], stdout = subprocess.PIPE)
    stdout, stderr = p.communicate()

    lines = stdout.split("\n")
    lines[0] = lines[0].replace("Mounted on", "MountedOn").replace("1K-blocks", "Size")
    assert(lines[0].split() == headers)

    lines = [l.strip() for l in lines if l.strip()]
    for line in lines[1:]:
        tokens = line.split()
        if tokens[0] == 'none': # skip uninteresting entries
            continue
        assert(len(tokens) == n)
        d = {}
        for x in range(1, len(headers)):
            d[headers[x]] = tokens[x]
        d['Size'] = float(d['Size']) / unit
        assert(d['Use%'].endswith("%"))
        d['Used'] = float(d['Used']) / unit
        d['Available'] = float(d['Available']) / unit
        d['Using'] = 100*(d['Used']/d['Size']) # same as Use% but with more precision

        if d['Type'].startswith('ext'):
            pass
            d['Using'] += 5 # ext2, ext3, and ext4 reserve 5% by default
        else:
            ext3_filesystems = ['ganon:', 'kortemmelab:', 'albana:']
            for e3fs in ext3_filesystems:
                if tokens[0].find(e3fs) != -1:
                    d['Using'] += 5 # ext3 reserves 5%
                    break
        details[tokens[0]] = d

    return details
