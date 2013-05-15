#!/usr/bin/python

# Obtain version hash from git if possible
try:
    import subprocess
    script_version = str(subprocess.check_output(["git", 'rev-parse', '--short', 'HEAD'])).strip()
except Exception:
    script_version = '1.0'

program_description="Script to find files owned by you (or another user) and move them, tar them, and/or delete them. Version %s. One directory positional argument is required."%(script_version)

# Python import statements
import optparse # For compatibility with pre-2.7 version
import os
import getpass
import time
import pwd
import sys
import tarfile
import shutil

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
    def report(self,a,b=0):
        t=time.time()
        self.a=a
        self.b=b
        if self.lastreport<(t-report_interval):
            self.lastreport=t
            self.output_report()
    def output_report(self):
        if self.b==0:
            sys.stdout.write("  Processed files: %d\r"%(self.a))
        else:
            sys.stdout.write("  Found %d files owned by user out of %d files total\r"%(self.a,self.b))
        sys.stdout.flush()
    def done(self):
        self.output_report()
        sys.stdout.write("\n")
        print 'Done %s, took %.3f seconds\n' % (self.task,time.time()-self.start)

def find_owner(f):
    return os.stat(f).st_uid

def delete_files_prompt(num_files):
    while(True):
        prompt = raw_input('Delete all %d files? (yes/no): '%(num_files))
        if prompt == 'yes':
            return True
        if prompt == 'no':
            return False
        else:
            print 'Invalid choice, must type "yes" or "no"'

def sizeof_fmt(num):
    for x in ['bytes','KB','MB','GB']:
        if num < 1024.0 and num > -1024.0:
            return "%3.1f%s" % (num, x)
        num /= 1024.0
    return "%3.1f%s" % (num, 'TB')

def find_files(input_dir,user):
    reporter=Reporter('scanning %s for files owned by userid #%d'%(input_dir,user))
    total_files_count=0
    owned_files_count=0
    owned_files=[]
    owned_files_size=long(0)
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
                owned_files_size+=os.stat(full_filename).st_size
            reporter.report(owned_files_count,total_files_count)

    reporter.done()
    print 'Total owned file size: %s\n'%(sizeof_fmt(owned_files_size))

    return owned_files

def delete_files(files):
    r = Reporter('deleting files')
    c=0
    failures=0
    for f in files:
        try:
            os.remove(f)
        except Exception:
            failures+=1
        c+=1
        r.report(c)
    r.done()
    print '%d deletion failures\n'%(failures)

def tar_files(tar_file,input_dir,files):
    # Ensure correct file extension
    if (not tar_file.endswith('.tgz')) and (not tar_file.endswith('.gz')):
        if tar_file.endswith('.tar'):
            tar_file+='.gz'
        else:
            tar_file+='.tar.gz'

    r = Reporter('taring and zipping files')
    c=0

    tar=tarfile.open(tar_file,'w:gz')
    for f in files:
        relpath=os.path.relpath(f,input_dir)
        tar.add(f,arcname=relpath)
        c+=1
        r.report(c)

    tar.close()
    r.done()

def move_files(move_dir,input_dir,files,copy=False):
    if copy:
        r = Reporter('copying files')
    else:
        r = Reporter('moving files')
    c=0

    for f in files:
        relpath=os.path.relpath(f,input_dir)
        new_dir=os.path.join(move_dir,os.path.dirname(relpath))
        new_file=os.path.join(new_dir,os.path.basename(f))
        if not os.path.isdir(new_dir):
            os.makedirs(new_dir)
        if copy:
            shutil.copy(f,new_file)
        else:
            shutil.move(f,new_file)
        c+=1
        r.report(c)

    r.done()

def own_files():
    pass

def main():
    parser = optparse.OptionParser(description=program_description,
                                   version=script_version,
                                   usage="usage: %prog [options] scan_directory")
    parser.add_option('-u','--user',
                      default=None,
                      help='User whose ownership is used in search. Argument can be a string username or a numeric user id. Default: current user')
    parser.add_option('-d','--delete',
                      action='store_true',
                      default=False,
                      help="Delete files after other tasks complete")
    parser.add_option('-m','--move_dir',
                      default=None,
                      help="Specify root directory to copy files to. Will perform a move instead of a copy if --delete is also enabled.")
    parser.add_option('-t','--tar_file',
                      default=None,
                      help="Specify new tar.gz file to save files in")
    #parser.add_option('input_dir',
    #                  help="Directory to recursively scan for files in")

    (args,positional_args)=parser.parse_args()
    if len(positional_args)!=1:
        print 'ERROR: One directory positional argument is required'
        sys.exit(1)
    input_dir=positional_args[0]

    # Verify and fill in arguments
    if not os.path.isdir(input_dir) or not os.access(input_dir, os.R_OK):
        print "ERROR: Cannot open directory %s"%(input_dir)
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

    files=find_files(input_dir,user)

    if args.tar_file!=None:
        tar_files(args.tar_file,input_dir,files)

    if args.move_dir!=None:
        if args.delete:
            move_files(args.move_dir,input_dir,files,copy=False)
        else:
            move_files(args.move_dir,input_dir,files,copy=True)

    # Delete files if they haven't already been moved
    if args.delete and args.move_dir==None:
        # Ask for confirmation if files haven't been tared
        if args.tar_file==None:
            if delete_files_prompt(len(files)):
                delete_files(files)
        else:
            # Files have already been tared, ok to delete without confirmation
            delete_files(files)

if __name__ == "__main__":
    main()
