import zipfile
import tempfile
import os

def unzip_to_tmp_dir(zipfile_path, root_dir = None):
    assert( zipfile_path.endswith('.zip') )
    tmp_dir = tempfile.mkdtemp(prefix='unzip_to_tmp_', dir = root_dir)
    with zipfile.ZipFile(zipfile_path, 'r') as z:
        z.extractall(tmp_dir)
    return tmp_dir
