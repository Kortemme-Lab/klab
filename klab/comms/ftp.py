#!/usr/bin/python
# encoding: utf-8
"""
ftp.py
ftp wrappers

Created by Shane O'Connor 2013
"""

import os
import traceback
from ftplib import FTP, FTP_TLS

from klab.fs.fsio import read_file, open_temp_file

class FTPException550(Exception): pass

def get_insecure_resource(host, resource, port = 21, output_filepath = None, timeout = None):

    using_temp_file = output_filepath == None
    output_handle = None
    ftp = None
    ftp_has_quit = True
    if timeout:
        ftp = FTP()
    else:
        ftp = FTP(timeout = 20)
    try:
        # Create an FTP connection and navigate to the correct directory
        ftp.connect(host, port)
        ftp_has_quit = False
        ftp.login()
        local_dirname, local_filename = os.path.split(resource)
        if local_dirname:
            ftp.cwd(local_dirname)

        #ftp://ftp.ebi.ac.uk/pub/databases/msd/sifts/xml/1xyz.xml.gz
        #ftp://ftp.ebi.ac.uk/pub/databases/msd/sifts/xml/1a2c.xml.gz

        # Create
        if not output_filepath:
            output_handle, output_filepath = open_temp_file('/tmp', ftype = 'wb')
        else:
            output_handle = open(output_filepath, 'wb')
        try:
            contents = ftp.retrbinary('RETR %s' % local_filename, output_handle.write, 1024)
        except Exception, e:
            if str(e).find('Failed to open file') != -1:
                raise FTPException550('Resource could not be located. FTP error: "%s"' % str(e))
            raise Exception('Unknown FTP error: "%s"' % str(e))

        output_handle.close()

        ftp.quit()
        ftp_has_quit = True

        if contents.find('Transfer complete') == -1:
            raise Exception('FTP error: "%s"' % contents)

    except FTPException550:
        if output_handle:
            output_handle.close()
        if not ftp_has_quit:
            ftp.quit()
        raise

    except Exception, e:
        if output_handle:
            output_handle.close()
        if not ftp_has_quit:
            ftp.quit()
        raise Exception('%s\n%s' % (str(e), traceback.format_exc()))

    contents = read_file(output_filepath)
    if using_temp_file:
        os.remove(output_filepath)
    return contents