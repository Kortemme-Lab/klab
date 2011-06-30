#!/usr/bin/python
### UTITLITY FUNCTIONS ###

import commands, os.path, time, os, sys, traceback, types, shelve
from math import floor
sys.path.append("./objgraph-1.7.0")
import objgraph

UTIL_POLL_INTERVAL = 10
UTIL_Q_JOBS_SUBMITTED = 0
UTIL_MERGE_PDBS_RUN_NAME = "sub-merge"
UTIL_VERBOSE_LEVEL = 0
UTIL_NFS_WAIT_TIME = 30   # how long to wait for NFS to give us our files before giving up

pushd_stack = []

import gc
from guppy import hpy
import time
starttime = time.time()
logfile = "heapprint.log"

DEBUGMODE = True
TERMINAL_GREEN = "\033[92m"
TERMINAL_YELLOW = "\033[93m"
TERMINAL_RED = "\033[91m"
TERMINAL_OFF = "\033[0m"


def CREATEFILE(filename, contents):
	if DEBUGMODE:
		F = open(filename, "w")
		F.write(contents)
		F.close()

def MSG(msg):
	print("%s%s%s" % (TERMINAL_GREEN, msg, TERMINAL_OFF))

def LOG(msg, warning = False, error = False):
	if error:
		print("%s%s%s" % (TERMINAL_RED, msg, TERMINAL_OFF))
	if warning:
		print("%s%s%s" % (TERMINAL_YELLOW, msg, TERMINAL_OFF))
	else:
		print(msg)
	if DEBUGMODE:
		F = open(logfile, "a")
		F.write(msg)
		F.close()
    
def WARN(msg):
	LOG("[Warning] %s" % msg, warning = True)

def ERROR(msg):
	LOG("[Warning] %s" % msg, error = True)

def PRINTHEAP(msg):
	global starttime
	newtime = time.time()
	if DEBUGMODE:
		tstr = ("**** %s. Time since last heap printout : %.2fs ****" % (msg or "", (newtime - starttime)))
		gc.collect()
		gc.collect()
		h = hpy()
		hp = str(h.heap())
		print("%s%s%s\n%s\n" % (TERMINAL_GREEN, tstr, TERMINAL_OFF, hp))
		F = open(logfile, "a")
		F.write("%s\n%s\n" % (tstr, hp))
		F.close()
	else:
		tstr = ("**** %s. Time taken : %.2fs ****" % (msg or "", (newtime - starttime)))
		print("%s%s%s\n" % (TERMINAL_GREEN, tstr, TERMINAL_OFF))
	starttime = newtime 
	


def flatten(lst):
    result = []
    for el in lst:
        if isinstance(el, (list, tuple)):
        #if hasattr(el, "__iter__") and not isinstance(el, basestring):
            result.extend(flatten(el))
        else:
            result.append(el)
    return result

    
class Job(object):
    def __init__(self, name, cmd, array_size, max_jobs_at_once=None, shell="/bin/sh",
                 queue_name="short.q", output_dir=None, proc_type="opt64"):
        self.name, self.cmd, self.array_size, self.shell, self.queue_name, self.output_dir, self.max_jobs_at_once = \
                   name, cmd, array_size, shell, queue_name, output_dir, max_jobs_at_once
        self.proc_type = proc_type
        if output_dir != None: self.output_dir = os.path.abspath(output_dir)
        self.cwd = os.getcwd()

class Queue:
    cmd_queue = [] # not yet used
    def __init__(self): self.empty = True
    def submit(self, job):
        #cmd_queue.append(job)
        while True:
            if job.max_jobs_at_once != None and job.array_size > job.max_jobs_at_once:
                jobs_per_batch = job.max_jobs_at_once/2
                subjob = job.copy()
                subjob.array_size = jobs_per_batch
                job.array_size -= jobs_per_batch
                self._submit(subjob)
            else:
                self._submit(job)
                break

            sleep(UTIL_POLL_INTERVAL)

            num_jobs_running = qnotdone(job.name, status="r")
            num_jobs_queued = qnotdone(job.name, status="qw")
            verbose_vars(["num_jobs_running", "num_jobs_queued"], 1, vars())

            # wait until there are no jobs waiting, and the # of jobs running is less than our cutoff
            print  "waiting for waiting jobs to stop waiting"
            qpoll(name, min_jobs_at_once = 0, status="qw")
            print  "waiting for running jobs to decrease in #"
            qpoll(name, min_jobs_at_once = jobs_per_batch, status="r")

        #def run(self, max_jobs_at_once=None):
        #ignore max jobs at once for now
        #for job in cmd_queue:
    def _submit(self, job):
        qsub(job.cmd, job.name, job.array_size, job.shell, job.queue_name, job.output_dir, proc_type=job.proc_type)
        self.empty = False

    def wait(self, job_name, user="gfriedla", njob_floor=0, query_status=None):
        if self.empty: return
        #print "\n# Queue.wait(): waiting for jobs in the queue"

        print "\nQueue.wait(): waiting for jobs to load into the queue", flush()
        sleep(UTIL_POLL_INTERVAL)
        num_stalled = qnotdone(job_name, user, status="dr")
        num_notdone = qnotdone(job_name, user, status=query_status)
        
        while(num_notdone-num_stalled > njob_floor):
            print "\nQueue.wait(): %s line(s) of jobs still in the queue" % num_notdone
            sleep(UTIL_POLL_INTERVAL)
            num_notdone = qnotdone(job_name, user, status=query_status)
    
        print "\n# Queue.wait(): done waiting (%s jobs still in the queue)\n" % num_notdone
        if (num_notdone == 0): self.empty = True
QUEUE = Queue()

def pushd(dirname):
    global pushd_stack
    pushd_stack.append(os.getcwd())
    print "# pushd: %s   ->     %s" % (os.getcwd(), dirname)
    cd(dirname)

def popd():
    global pushd_stack
    assert(len(pushd_stack) > 0)
    dirname, pushd_stack = pushd_stack[-1], pushd_stack[:-1]
    print "# popd: %s    <-     %s" % (dirname, os.getcwd())

    cd(dirname)
    return dirname

def assert2(val1, val2, txt):
    if val1 != val2:
        raise AssertionError(txt + ": %s != %s" % (str(val1), str(val2)))

def ASSERT(expr1, expr2, txt="", locals=None, globals=None):
    val1, val2 = CHECK(expr1, expr2, txt, locals, globals)
    if val1 != val2: sys.exit(1)

# doesn' throw exception
def CHECK(expr1, expr2, txt="", locals=None, globals=None):
    val1, val2 = eval(expr1, locals, globals), eval(expr2, locals, globals)
    if val1 != val2:
        print """%s:
        '%s'
        [[%s]]

        !=

        '%s'
        [[%s]]""" % (txt, val1, expr1, val2, expr2)
        import traceback
        print traceback.print_exc()
    return val1, val2

def print_last_exception():
    import traceback
    traceback.print_exc()
    print
    
# returns the resident set size and the memory size in KB
def get_memusage():
    pid = os.getpid()
    a2 = os.popen('ps -p %d -o rss,sz' % pid).readlines()
    #print 'meminfo  ', a2[1],
    return map(lambda s: int(s)/1024, a2[1].split())

# flush the stdout buffer
def flush():
    sys.stdout.flush()
    return ""


# convert an array to a pretty string
def arr2str(a, precision=2):
    from numpy import array2string
    return array2string(a, max_line_width=200, precision=precision)

# convert an array to a pretty string
def arr2str2(a, precision=2, length=5, col_names=None, row_names=None):
    fmt = "%" + str(length) + "s"
    shape = a.shape
    assert(len(shape) == 2)
    #s = "\n".join([fmt_floats(a[row,:], digits=precision) for row in range(shape[0])]) + "\n"
    str_arr = []
    if col_names != None: str_arr += [" "*(length+1) + " ".join([fmt%str(col) for col in col_names])]
    for i in range(shape[0]):
        row_header = ""
        if row_names != None: row_header = fmt % str(row_names[i]) + " "
        str_arr += [row_header + fmt_floats(a[i,:], digits=precision, length=length)]

    return "\n".join(str_arr) + "\n"

# convert an of complex #s array to a pretty string
def arr2str_complex(a, precision=2):
    shape = a.shape
    assert(len(shape) == 2)
    return "\n".join([fmt_complex(a[row,:], digits=precision) for row in range(shape[0])]) + "\n"

# track elapsed time in seconds
class Timer:
    def __init__(self): self._start = time.time()
    def elapsed(self):  return time.time() - self._start
    def __str__(self):  return "%0d:%02d" % (self.elapsed()/60, self.elapsed()%60)

# pretty print a list of floats
def fmt_floats(fs, digits=2, length="", sep=" "):
    fmt = "%"+str(length)+"."+str(digits)+"f"
    return sep.join([fmt%f for f in fs])

# pretty print a list of floats
def fmt_complex(cs, digits=2, len="5", sep=" "):
    fmt = "%"+str(len)+"."+str(digits)+"f" + "+"+ "%"+str(len)+"."+str(digits)+"f" + "i" + sep
    return sep.join([fmt%(c.real, c.imag) for c in cs])

# pretty print a list of ints
def fmt_ints(ints, len="", sep=" "):
    fmt = "%"+str(len)+"d"
    return sep.join([fmt%i for i in ints])

def set_verbose(verbose_level):
    global UTIL_VERBOSE_LEVEL
    UTIL_VERBOSE_LEVEL = verbose_level
    
# print the string if the verbose_level >= UTIL_VERBOSE_LEVEL
def verbose(s, verbose_level):
    if verbose_level <= UTIL_VERBOSE_LEVEL:
        print "[V%d]  %s" % (verbose_level, s)

# print out all the variables in the list at the given verobse level
def verbose_vars(var_names, verbose_level, local_vars={}, prefix_txt_str=""):
    if len(local_vars) == 0: raise Exception("ERROR verbose_vars(): local_vars has no elements")
    for var_name in var_names:
        assert2(var_name in local_vars.keys(), True, "'%s' not found in local_vars()" % var_name)
        verbose("%s     %s='%s'" % (prefix_txt_str, var_name, local_vars[var_name]), verbose_level)
        
# expand wildcards in the path and return a list of matching files,
# an empty list if nothing is found, or throw an exception if desired
#def expand_wildcards(path, throw=False):
#    try:
#        fns = run("find %s/ -maxdepth 1 -name %s" % (os.path.dirname(path), os.path.basename(path))).split()
#    except:
#        fns = []
#   if len(fns) == 0 and throw:
#        raise Exception("ERROR expand_wildcards; no files found")

#    return fns

# change directory
def cd(dir):
    output_sh_cmd("cd " + dir)
    os.chdir(dir)

def output_sh_cmd(cmd):
    cwd = os.getcwd().replace("/netapp/home/","~")
    if UTIL_VERBOSE_LEVEL >= 2: print "Exec       %s\n                 (cd %s)" % (cmd, cwd)
    sys.stdout.flush()

def mkdir(dir):
    d = os.path.abspath(dir)
    run("mkdir -p %s" % d)
    return d

# make directory and cd into it
def mkdir_cd(dir):
    mkdir(dir)
    cd(dir)

# checks that all the files are present; prints an error if they're not
# returns are_all_files_there? , matched_fns
# useful for matching wildcards
def look_for_files(paths, throw=False, num_attempts=1):
    assert(not isinstance(paths, types.StringType))

    verbose("look_for_files(): making %d attempts to find '%s'" % (num_attempts, paths), 1)
    for i in range(num_attempts):
        if i != 0: sleep(10)

        missing_paths = []
        all_matched_fns = []
        for path in paths:
            path = os.path.abspath(path)
            try:
                # do this because ls and -e somehow miss files that are there
                cmd = "find %s -maxdepth 1 -name %s" % (os.path.dirname(path), os.path.basename(path))
                matched_fns = run(cmd).strip().split()
                all_matched_fns += matched_fns

                if len(matched_fns) == 0: missing_paths.append(path)
            except Exception, e:
                if throw: raise e

                import traceback
                print("WARNING look_for_files() caught an exception:   %s\n" % \
                      " ".join(traceback.format_exception_only(sys.exc_type, sys.exc_value)).replace("CMD", cmd))
                missing_paths.append(path)

        # return early if we've found it
        if len(missing_paths) == 0: return True, all_matched_fns
        
    if len(missing_paths) > 0:
        if throw: raise Exception("\nFailed to find files:\n%s\n\n" % ("\n          ".join([""]+missing_paths)))
        return False, all_matched_fns
    return True, all_matched_fns

# CURRENTLY CONTAINS BUG WHERE THE RUN CMD OUTPUT CONTAINS THE FILENAMES
# return the number of lines in the file as an integer
#def count_file_lines(fns):
#    all_found, found_fns = look_for_files(fns, throw=True)
#    len_strs = run("wc -l %s | awk '{print $1}'" % (" ".join(found_fns))).split()
#    if len(len_strs) > 1: len_strs = len_strs[:-1] # if multiple files, wc sums them up on the last line
#    return map(int, len_strs)

# in seconds
class Timer:
    def __init__(self):
        self._start = time.time()
    def elapsed(self):
        return time.time() - self._start
    def __str__(self):
        return "%0d:%02d" % (self.elapsed()/60, self.elapsed()%60)

# retrieve a list of lines from the file    
def readlines(fns):
    if len(fns) == 0: raise Exception("ERROR readlines(): expected multiple files")
    elif len(fns[0]) <= 1: raise Exception("ERROR readlines(): expected multiple files")

    lines = []
    for fn in fns:
        f = open(fn)
        txt = f.read()
        f.close()
        #print "readlines() found: '%s'" % txt
        lines += txt.strip().split("\n")
    if len(lines)==0 or (len(lines) == 1 and lines[0] == ""): return None
    else: return lines

# run linux command and return stdout/stderr
# if quiet==True, don't fail upon error but print out the error info
def run(cmd, quiet=False):
    import os

    cmd2 = \
        """
sh <<EOF 2>&1
%s
EOF
        """ % cmd
    output_sh_cmd(cmd2)

    # modified from module commands and function getstatusoutput()
    pipe = os.popen(cmd2)
    output = pipe.read()
    status = pipe.close()

    if status is None: status = 0
    if output[-1:] == '\n': output = output[:-1]

#    status, output = commands.getstatusoutput(\
#        """sh <<EOF;
#        %s
#        EOF
#        """ % cmd)
    verbose("OUTPUT { " + output + " } OUTPUT END\n", 2)

    if status != 0:
        outstr = "ERROR running command (status=%d):\n  %s\n\n  %s'" % (status,cmd, output)
        if quiet: print "WARNING: run() exited with status>0; ignored. Output='%s'" % outstr
        else: raise Exception(outstr)
    return output
                                    
# parse the pdb file name from file paths
def parse_pdbnames(fns):
    pdbnames = []
    for fn in fns:
        pdbnames += [os.path.basename(fn).replace('.pdb', '').replace('.gz','')]
    return pdbnames
def parse_pdbname(fn): return parse_pdbnames([fn])[0]

# manages the queue. submitting all jobs in an array in batches so as not to overload things
#def qsub_throttle(cmd, name, array_size, shell="/bin/sh", queue="short.q", output_dir=None, wait=False, max_q_size=None):
#    if max_q_size == None:
#        return qsub(cmd, name, array_size, shell=shell, queue=queue, output_dir=output_dir, wait=wait)
#    else:
        # throttle ...
#        output_txt = ""
#        min_q_size = int(max_q_size/2.)
#        array_jobs_left = array_size
#        verbose_vars(["max_q_size", "min_q_size", "array_size", "array_jobs_left"], 1, vars())        
#        while array_jobs_left > 0:
#            curr_array_size = min(array_jobs_left, min_q_size)
#            num_jobs_running = qnotdone(name, status="r")

            # submit the jobs in this batch
#            print "\n#() throttling queue size (%d jobs in the queue)\n" % num_jobs_running
#            verbose_vars(["array_jobs_left", "num_jobs_running", "curr_array_size"], 1, vars())
#            output_txt += "\n" + qsub(cmd, name, curr_array_size, shell=shell, queue=queue, output_dir=output_dir, wait=wait)
#            array_jobs_left -= curr_array_size

#            num_jobs_running = qnotdone(name, status="r")
#            num_jobs_queued = qnotdone(name, status="qw")
#            verbose_vars(["num_jobs_running", "num_jobs_queued"], 1, vars())

            # wait until there are no jobs waiting, and the # of jobs running is less than our cutoff
#            print  "waiting for waiting jobs to stop waiting"
#            qpoll(name, min_jobs_at_once = 0, status="qw")
#            print  "waiting for running jobs to decrease in #"
#            qpoll(name, min_jobs_at_once = min_q_size, status="r")
#    return output_txt

# submit queue job
def qsub(cmd, name, array_size, shell="/bin/sh", queue_name="short.q", output_dir=None, wait=False, proc_type="opt64"):
#    global UTIL_Q_JOBS_SUBMITTED

    # to run multiple semicolon separate commands: qsub -q short.q -b y -cwd -j y -S  /bin/sh /bin/sh -c 'ls . ; ls ~/lib/'
    # qsub -b y -cwd -j y -l opt64=true -l netapp=1G,mem_free=1G -S /bin/sh -q short.q
    assert(proc_type in ("opt64", "ibm32"))
    qsub_cmd = "qsub -b y -cwd -j y -l %s=true -l netapp=1G,mem_free=1G -S %s -q %s" % (proc_type, shell, queue_name)
    if wait: qsub_cmd += " -sync y"
    if output_dir:
        run("mkdir -p %s" % (output_dir))
        qsub_cmd += " -o %s" % output_dir
#    qsub_cmd += " -N %s -t 1-%d sh -c '%s'" % (name, array_size, cmd.replace("'", "\'"))
    qsub_cmd += " -N %s -t 1-%d %s" % (name, array_size, cmd)    

#    UTIL_Q_JOBS_SUBMITTED += 1
    return run(qsub_cmd)
    
# how many jobs are still in the queue with the given name by the given user?
# if status is not none, the jobs that are counted are the ones in that state
def qnotdone(name, user="gfriedla", status=None):
    assert(status in (None, "r", "qw", "E", "dr"))

    #cmd = "qstat -u %s | awk '\"$3\"==\"%s\" && \"$4\"==\"%s\"' | wc -l" % (user, name, status)
    # e.g. ' 924672 0.05003 rdc_fit    gfriedla     r     04/04/2008 03:29:30 short.q@opt224                     1 15'    

    # filter by user
    q_jobs_str = run("qstat -u %s | grep %s" % (user, name), quiet=True).strip()
    q_jobs = q_jobs_str.split("\n")
    if (q_jobs_str == ""): return 0

    # filter by name 
    q_jobs = filter(lambda l: l.split()[2] == name, q_jobs)

    # filter by status
    if status != None and len(q_jobs) != 0:
        q_jobs = filter(lambda l: l.split()[4] == status, q_jobs)

    num_jobs = len(q_jobs)
    return num_jobs

def sleep(secs):
    verbose("Sleeping for %d seconds" % secs, 1)
    time.sleep(secs)

# keep looping until the queue has fewer than min_jobs_at_once
# if status is not None, only count jobs that are of this status
def qpoll(name, user="gfriedla", min_jobs_at_once=0, status=None):
#    global UTIL_Q_JOBS_SUBMITTED

#    if UTIL_Q_JOBS_SUBMITTED == 0: return 
    
    print "\nqpoll: waiting for jobs in the queue"
    time.sleep(UTIL_POLL_INTERVAL)
    num_notdone = qnotdone(name, user)
        
    while(num_notdone > min_jobs_at_once):
        print "\nqpoll: %s line(s) of jobs still in the queue (waiting until %d)\n" % (num_notdone, min_jobs_at_once)
        sleep(UTIL_POLL_INTERVAL)
        num_notdone = qnotdone(name, user, status=status)
#    UTIL_Q_JOBS_SUBMITTED = num_notdone

    print "\n# qpoll: done waiting (%s job in the queue)\n" % num_notdone

# take a bunch of pdb files and merge them into one multi pdb file with MODEL separators
def merge_pdbs_into_1_file(pdb_lst_fn, final_pdb_fn, gzip=True):
    cmd = "~/scripts/python/concat-mult-pdbs.py %s %s"  % (final_pdb_fn, pdb_lst_fn)
    qsub(cmd, UTIL_MERGE_PDBS_RUN_NAME, 1)

# lookup key in shelf; if not found, evaluate val_expr, store & return
def shelf_access(shelf_fn, key, val_expr, globals=None, locals=None, overwrite=False, use_shelf=True):
    val = None
    shelf = shelve.open(shelf_fn)

    # load from shelf
    if not overwrite and use_shelf:
        try:
            val = shelf[key]
            return val
        except: pass
        
    val = eval(val_expr, globals, locals)

    # store back in shelf
    if use_shelf:
        shelf[key] = val
    
    shelf.close()
    return val

def translate_to_C(code, variables):
    def _translate_vars(expr):
        return expr.replace(".", "_")

    s = ""
    for line in code.split("\n"):
        line2 = line.replace("\t", "    ")
        
        tok = line.replace("("," ").replace(")"," ").split()
        ntok = len(tok)
        
        # for: expect 5 or 6 fields
        #      e.g. for m2 in range(m1+1, self.nfdata.num_movies+1):
        if tok[0] == "for":
            assert(tok[3] == "range")
            assert(ntok in (5,6))
            var, start = tok[1], _translate_vars(tok[4])
            if ntok == 6: end = _translate_vars(tok[5])
            s += "for (unsigned int %s=%s; %s<%s; %s++) {" % (var, start, var, end, var)
        # if: expect 4 fields
        #     e.g. if C2 < MIN_BAYES_RATINGS:
        #elif tok[0] = "if":

class OptFields:
    def __init__(self, params, opt_mask, fmin_fn, func):
        pass

    def func(*args):
        print args[0] + args[1:]
        passed_args = numpy.asarray([x1[0], x2, x3, x4, x5])
        fn_args = zeros(len(opt_mask))
        fn_args[opt_mask] = passed_args[0]
        fn_args[logical_not(opt_mask)] = passed_args[1:]
        print fn_args

        return func(fn_args[0], fn_args[1], fn_args[2], fn_args[3], fn_args[4])
        #predictions = f_x(y, False, neighbor_predictor)
        rmse, count = calc_rmse(neighbor_predictor.test_ratings, predictions)
        print "  f(%s) = %5.3f; count = %10d" % (util.fmt_floats(fn_args, digits=3), rmse, count), util.flush()
        if count < OPTIMIZATION_COUNT_MIN * len(neighbor_predictor.test_ratings): rmse = 999
        return rmse
    
