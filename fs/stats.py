#!/usr/bin/python
# encoding: utf-8
"""
stats.py
For filesystem statistics functions
"""

import os
import subprocess

if __name__ == '__main__':
    import sys
    sys.path.insert(0, '../..')

from tools.comms.mail import MailServer

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

class FileCounter(object):

    def __init__(self, top_dir, cut_off = None):
        if top_dir.endswith('/'):
            top_dir = top_dir[:-1]
        self.root = top_dir
        self.counts = {}
        self.cumulative_counts = {}
        self.depth_list = []
        self.cut_off = cut_off

        self.count_files(top_dir)
        self.depth_list = sorted(self.depth_list, reverse = True)
        self.create_cumulative_counts()

    def count_files(self, top_dir):
        for dirpath, dirnames, filenames in os.walk(top_dir, topdown=True, onerror=None, followlinks=False):
            if dirpath.endswith('/'):
                dirpath = dirpath[:-1]
            depth = len([t for t in dirpath.split('/') if t])
            self.depth_list.append((depth, dirpath))
            assert(self.counts.get(dirpath) == None)
            self.counts[dirpath] = len(filenames)


    def create_cumulative_counts(self):
        for k, v in self.counts.iteritems():
            self.cumulative_counts[k] = v

        for tpl in self.depth_list:
            child_dir = tpl[1]
            prnt_dir = os.path.split(child_dir)[0]
            if child_dir != self.root:
                self.cumulative_counts[prnt_dir] += self.cumulative_counts[child_dir]

    def send_email(self, email_address):
        s = ['Cumulative file counts for directories under %s.\n' % self.root]
        for k, v in sorted(self.cumulative_counts.iteritems(), key = lambda x:-x[1]):
            if v:
                if not(cut_off) or v >= cut_off:
                    s.append('%s: %d' % (k, v))
        msg = '\n'.join(s)
        ms = MailServer()
        ms.sendgmail('Directory file count statistics', [email_address], msg)

if __name__ == '__main__':
    if 2 <= len(sys.argv) <= 3 and os.path.exists(sys.argv[1]):
        cut_off = None
        if len(sys.argv) == 3:
            assert(sys.argv[2].isdigit())
            cut_off = int(sys.argv[2])

        root_dir = sys.argv[1]
        fc = FileCounter(os.path.abspath(os.path.normpath(root_dir)), cut_off)
        fc.send_email('shane.oconnor@ucsf.edu')
