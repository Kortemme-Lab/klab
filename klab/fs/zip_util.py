import os
import gzip
import subprocess
from subprocess import Popen, PIPE, check_call
import signal

class LineReader:
    def __init__(self,fname):
        if fname.endswith('.gz'):
            if not os.path.isfile(fname):
                raise IOError(fname)
            self.f = Popen(['gunzip', '-c', fname], stdout=PIPE, stderr=PIPE)
            self.zipped=True
        else:
            self.f = open(fname,'r')
            self.zipped=False
    def readlines(self):
        if self.zipped:
            for line in self.f.stdout:
                yield line
        else:
            for line in self.f.readlines():
                yield line
    def close(self):
        if self.zipped:
            if self.f.poll() == None:
                os.kill(self.f.pid, signal.SIGHUP)
        else:
            self.f.close()
    def __enter__(self):
        return self
    def __exit__(self, type, value, traceback):
        self.close()
    def __iter__(self):
        return self.readlines()

def zip_file(file_path):
    if os.path.isfile(file_path):
        f_in = open(file_path, 'rb')
        f_out_name = file_path + '.gz'
        f_out = gzip.open(f_out_name, 'wb')
        f_out.writelines(f_in)
        f_out.close()
        f_in.close()
        os.remove(file_path)
        return f_out_name

def zip_file_with_gzip(file_path):
    if file_path.endswith('.gz'):
        return file_path

    subprocess.check_call(['gzip', file_path])
    zipped_path = file_path + '.gz'
    assert( os.path.isfile(zipped_path) )
    return zipped_path

def unzip_file(file_path):
    if os.path.isfile(file_path) and file_path.endswith('.gz'):
        f_in = gzip.open(file_path,'rb')
        f_out_name = file_path[:-3]
        f_out = open(f_out_name, 'wb')
        f_out.writelines(f_in)
        f_out.close()
        f_in.close()
        os.remove(file_path)
        return f_out_name
