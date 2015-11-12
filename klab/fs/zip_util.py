import os
import gzip
import subprocess

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
