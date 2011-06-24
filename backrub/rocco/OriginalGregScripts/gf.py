# Greg's python util functions

import commands, re, time, os, sys, glob, datetime, math, os.path, shelve
#import scipy.stats

# read table info from a file
# default separator is any blank space
def read_table(fn, sep=None):
    lines = open(fn).read().split("\n")
    data = []
    for line in lines:
        if line[0] == "#" or len(line.strip()) == 0: continue
        tok = line.split()
        data.append(tok)
    return data

# k1 k2 k3 val
class TableData:
    # data is list of lists
    def __init__(self, ncols, data):
        self.ncols = ncols
        self.data = data
        for row in self.data: assert(len(row) == ncols)

    def get_uniq_col_vals(self, col_no):
        import sets
        col_vals = [row[col_no] for row in self.data]
        return list(sets.Set(col_vals))

    def get_vals_by_col(self, col_nos, col_vals):
        vals = []
        for row in self.data:
            match = True
            for col_no, col_val in zip(col_nos, col_vals):
                if row[col_no] != col_val: match = False
            if match: vals.append(row[-1])
        return vals


# flatten nested lists
def flatten(L):
    if type(L) != type([]): return [L]
    if L == []: return L
    return flatten(L[0]) + flatten(L[1:])

# lookup value from a shelf, throws KeyError if not there
def shelf_lookup(shelf_fn, key):
    shelf = shelve.open(shelf_fn)
    val = shelf[key]
    shelf.close()
    return val

# lookup key in shelf; if not found, evaluate val_expr, store & return
def shelf_access(shelf_fn, key, val_expr, globals=None, locals=None, overwrite=False, use_shelf=True):
    val = None

    # load from shelf
    if not overwrite and use_shelf:
        try:
            shelf = shelve.open(shelf_fn)
            val = shelf[key]
            return val
        except: pass
        
    val = eval(val_expr, globals, locals)

    # store back in shelf
    if use_shelf:
        try:
            shelf[key] = val
            shelf.close()
        except: pass
    
    return val
    
def get_memusage():
    pid = os.getpid()
    a2 = os.popen('ps -p %d -o rss,sz' % pid).readlines()
    #print 'meminfo  ', a2[1],
    return map(int, a2[1].split())

def ch_mkdir(path):
    if not os.path.exists(path): os.mkdir(path)
    os.chdir(path)

# get absolute path relative to /zin/
def zin_abspath(fn):
    fn = os.path.abspath(fn)
    if fn.startswith("/home/"):
        return "/zin/" + fn[6:]
    elif fn.startswith("/home2/"):
        return "/zin/" + fn[7:]
    return fn

def flush():
    sys.stdout.flush()
    return ""

# format a list of floats
def fmt_floats(fs, digits, len="", sep=" "):
    fmt = "%"+str(len)+"."+str(digits)+"f"
    return sep.join([fmt%f for f in fs])
def fmt_list(fs, fmt, sep=" "):
    return sep.join([fmt%f for f in fs])

def plot_2Dfiles(files):
    import pylab
    pylab.ioff() # don't update every time
    
    lines = {}
    for fn in files:
        X, header = load(fn)
        xdata = X[:,0]
        for i in range(1, len(header)):
            name, ydata = header[i], X[:,i]
            pylab.subplot(len(header)-1, 1, i)
            line = pylab.plot(xdata, ydata)
            pylab.yticks([max(ydata)])

            if fn == files[0]:
                pylab.ylabel(name, rotation='horizontal')
                
            if i == len(header)-1:
                lines[fn] = line
            else:
                pylab.set(pylab.gca(), 'xticklabels', [])
    pylab.figlegend([lines[fn] for fn in files], files, 'right')

    pylab.show()
    pylab.ion()

def load(fname):
    """
    Load ASCII data from fname into an array and return the array.
    X = load('test.dat')    # a matrix of float data
    """
    from numarray import array
    fh = file(fname)
    
    X = []
    numCols = None
    header = None
    for line in fh:
        line = line[:line.rfind('%')].strip()
        if not len(line): continue
        try:
            row = [float(val) for val in line.split()]
        except ValueError:
            header = line.split()
            continue

        thisLen = len(row)
        if numCols is not None and thisLen != numCols:
            raise ValueError('All rows must have the same number of columns')
        X.append(row)

    X = array(X)
    r,c = X.shape
    if r==1 or c==1:
        X.shape = max([r,c]),
    return X, header

class Dict2D:
    def __init__(self):
        self.data = {}
    def __repr__(self):
        return repr(self.data)
    def get(self, key1, key2, default=None):
        if key1 not in self.data.keys(): self.data[key1] = {}
        try:
            val = self.data[key1][key2]
            return val
        except KeyError:
            return default
    def set(self, key1, key2, item):
        if key1 not in self.data.keys(): self.data[key1] = {}
        self.data[key1][key2] = item
    def get_keys1(self): return self.data.keys()
    def get_keys2(self): return self.data[self.get_keys1()[0]].keys()
    def get_list(self, key1_list, key2_list):
        l = []
        for key1 in key1_list:
            for key2 in key2_list:
                l += [self.data[key1][key2]]
        return l

class DictMD:
    def __init__(self, dimensions, warn_on_overwrite=False):
        self.data = {}
        self.dim = dimensions
        self.warn_on_overwrite = warn_on_overwrite
    def __repr__(self):
        return repr(self.data)
    def _get_subdict(self, *keys):
        curr_dict = self.data
        for key in keys:
            if key not in curr_dict: curr_dict[key] = {}
            curr_dict = curr_dict[key]
        return curr_dict
    def get(self, *keys):
        #print "getting %s" % (str(keys))
        assert(len(keys) == self.dim)
        return self._get_subdict(keys[:-1])[keys[-1]]
    def set(self, value, *keys):
        #print "setting %s to %s" % (keys, value)
        assert(len(keys) == self.dim)
        subdict = self._get_subdict(keys[:-1])
        if self.warn_on_overwrite:
            if keys[-1] in subdict:
                print "WARNING: overwriting %s from '%s' -> '%s'" % (keys, subdict[keys[-1]], value)
        subdict[keys[-1]] = value
        
# ???
class SQLSelect:
    def __init__(self, cursor, sql):
        self.sql = sql
        cursor.execute(self.sql)
        self.rows = cursor.fetchall()
        self.columns = []

        for j in range(len(self.rows[0])):
            self.columns.append([])
        for i in range(len(self.rows)):
            for j in range(len(self.rows[i])):
                self.columns[j].append(self.rows[i][j])

# stores configuration info read from python formatted data files
class Config:
    def __init__(self, config_fn):
        self._config_fn = config_fn
        self._cfg = {}
        execfile(config_fn, {}, self._cfg)
    def get(self):
        return self._cfg

# in seconds
class Timer:
    def __init__(self):
        self._start = time.time()
    def elapsed(self):
        return time.time() - self._start
    def __str__(self):
        return "%0d:%02d" % (self.elapsed()/60, self.elapsed()%60)

def current_timestr():
    return datetime.datetime.now().strftime("%Y%m%d-%H%M")
    
def run_sql(cursor, sql):
    cursor.execute(sql)
    return cursor

def float_to_sql(val, fmt):
    if val == BAD_VAL:
        return "NULL"
    else:
        return fmt%(val)
    
def fatal(string):
    print "FATAL: %s" % (string)
    sys.exit(1)

def assertif(condition, output):
    if not condition:
        print "*** ASSERT:  " + str(output) + "\n\n\n"
        assert(condition)
        
# glob for 1 file
def glob1(expression):
    result = glob.glob(expression)
    if len(result) == 0:
        return None
    elif len(result) == 1:
        return result[0]
    else:
        raise Exception("glob1 matched more than 1 file")
        
# wrapper for running commands
# returns status
def run(cmd, exception_on_error=True):
    stat, out = commands.getstatusoutput(cmd)
    if stat != 0:
        if exception_on_error:
            raise Exception("Running '%s': (%d) %s\n"%(cmd, stat, out))
        else:
            print "ERROR: " + out

    return out

# run cmd; if relay_output is True, pipe output to stdout/stderr, otherwise return as a string
# doesn't work if True!
def run2(cmd, relay_output):
    if relay_output:
        out, err = sys.stdout, sys.stderr
    else:
        out, err = subprocess.PIPE, subprocess.STDOUT
    p = subprocess.Popen(cmd, shell=True, stdout=out, stderr=err)
    status = p.wait()
    if status != 0:
        raise Exception("ERROR running '%s': (%d)" % (cmd, status))

    if relay_output:
        return None
    else:
        return p.stdout.read()

# simple re match wrapper
def search(patt, str, num_matches=1, flags=0):
    match = re.search(patt, str, flags)
    if match == None:
        return None
    else:
        if num_matches == 1:
            return match.groups()[0]
        else:
            return match.groups()[:num_matches]
        
def readlines(fil):
    assertif(os.path.exists(fil), fil +  " doesn't exist")
    f = open(fil)
    lines = f.readlines()
    f.close()
    return lines
    
def readfile(fil):
    f = open(fil)
    txt = f.read()
    f.close()
    return txt
                            
def writefile(fil, txt):
    f = open(fil, "w")
    f.write(txt)
    f.close()

def appendfile(fn, txt):
    f = open(fn, "a")
    f.write(txt)
    f.close()

# get the filename portion after all slashes but before the extension
def parse_filebase(fil):
    return os.path.basename(fil).split(".")[0]
    
# create a new list with the first item being the rank of the list ordered by the first item (same rank for equal items)
def ranklist(list):
    newlist = []
    for i in range(len(list)):
        if i == 0 or list[i][0] != list[i-1][0]:
            rank = i+1
        newlist.append([rank]+list[i])
    return newlist

# return val1 if condition is true, otherwise val2
def cond(condition, val1, val2):
    if condition:
        return val1
    return val2

# return val1,val2 if condition is true, otherwise val2,val1
def cond2(condition, val1, val2):
    if condition:
        return val1,val2
    return val2,val1

class StrIndexArray:
    sep = "|||"
    
    def __init__(self, copy=None):
        self.dict = {}
        if copy:
            assert(isinstance(copy, StrIndexArray))
            self.dict.update(copy.dict)

    def make_key(self, x, y):
        return "%s%s%s" % (x, self.sep, y)
    
    def set(self, x, y, val):
        self.dict[self.make_key(x, y)] = val

    def get(self, x, y):
        return self.dict[self.make_key(x, y)]

    def get_xs(self, y):
        xs = {}
        for key in self.dict.keys():
            if key.endswith(self.make_key("", y)):
               xs[key] = self.dict[key]
        return xs

    def get_ys(self, x):
        ys = {}
        for key in self.dict.keys():
            if key.startswith(self.make_key(x, "")):
               ys[key] = self.dict[key]
        return ys

    def get_all(self):
        return self.dict.values()


def make_all_subsets(set):
    i = set[0]
    if len(set) == 1: return [[i], []]
    else:
        subsets = make_all_subsets(set[1:])
        return subsets + [[i]+subset for subset in subsets]
