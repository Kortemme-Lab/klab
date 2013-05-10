#!/usr/bin/python

# Obtain version hash from git if possible
try:
    import subprocess
    script_version = str(subprocess.check_output(["git", 'rev-parse', '--short', 'HEAD']))
except Exception:
    script_version = '1.0'

program_description="Script to find files owned by you (or another user) and move them, tar them, and/or delete them. Version "+script_version

# Python import statements
import argparse
import os
import getpass
import time
import pwd
import sys

# Constants
report_interval=1.0

class Reporter:
    def __init__(self,task):
        self.start=time.time()
        self.lastreport=self.start
        self.task=task
        self.a=0
        self.b=0
        print 'Starting '+task
    def report(self,a,b):
        t=time.time()
        if self.lastreport<(t-report_interval):
            self.lastreport=t
            self.a=a
            self.b=b
            self.output_report()
    def output_report(self):
        sys.stdout.write("  Found %d files owned by user out of %d files total\r"%(self.a,self.b))
        sys.stdout.flush()
    def done(self):
        self.output_report()
        sys.stdout.write("\n")
        print 'Done %s, took %.3f seconds\n' % (self.task,time.time()-self.start)

def find_owner(f):
    return os.stat(f).st_uid

def find_files(input_dir,user):
    reporter=Reporter('Scanning %s for files owned by userid #%d'%(input_dir,user))
    total_files_count=0
    owned_files_count=0
    owned_files=[]
    for directory_root, directory, filenames in os.walk(input_dir):
        for filename in filenames:
            total_files_count+=1
            full_filename=os.path.join(directory_root,filename)
            owner=None
            if os.path.isfile(full_filename):
                owner=find_owner(full_filename)
            if owner==user:
                owned_files_count+=1
                owned_files.append(full_filename)
                reporter.report(owned_files_count,total_files_count)

    reporter.done()
    print owned_files_count,total_files_count

def main():
    parser = argparse.ArgumentParser(description=program_description,
                                     fromfile_prefix_chars='@')
    parser.add_argument('-u','--user',
                        default=None,
                        help='User whose ownership is used in search. Argument can be a string username or a numeric user id. Default: current user')
    parser.add_argument('-d','--delete',
                        action='store_true',
                        default=False,
                        help="Delete files after other tasks complete")
    parser.add_argument('-m','--move_dir',
                        default=None,
                        help="Specify root directory to move files to")
    parser.add_argument('-t','--tar_file',
                        default=None,
                        help="Specify new tar.gz file to save files in")
    parser.add_argument('input_dir',
                        help="Directory to recursively scan for files in")

    args=parser.parse_args()

    # Verify and fill in arguments
    if not os.path.isdir(args.input_dir) or not os.access(args.input_dir, os.R_OK):
        print "ERROR: Cannot open directory %s"%(args.input_dir)
        sys.exit(1)

    user=args.user
    if user==None:
        user=pwd.getpwnam(getpass.getuser()).pw_uid
    else:
        try:
            user=int(user)
        except ValueError:
            try:
                user=pwd.getpwnam(user).pw_uid
            except KeyError:
                print 'ERROR: Could not lookup user id for user %s'%(args.user)
                sys.exit(1)

    files=find_files(args.input_dir,user)

if __name__ == "__main__":
    main()
