#!/usr/bin/python
# encoding: utf-8
"""
schema.py
Functions for working with database schemas.

Created by Shane O'Connor 2013
"""

import sys
import os
import re
import subprocess
import getpass
sys.path.insert(0, '../..')

from mysql import DatabaseInterface as MySQLDatabaseInterface
from tools.fs.fsio import read_file, write_file, open_temp_file

class MySQLSchema(object):

    def __init__(self, isInnoDB=True, numTries=1, host=None, db=None, user=None, passwd=None, port=None,
                 unix_socket=None, passwdfile=None, use_utf=False):

        temp_files = []

        if not passwd:
            if os.path.exists("pw"):
                passwd = read_file('pw').strip()
            else:
                passwd = getpass.getpass("Enter password to connect to MySQL database:")

        dbinterface = MySQLDatabaseInterface(
            {},
            isInnoDB = False,
            numTries = 32,
            host = "kortemmelab.ucsf.edu",
            db = "ddG", # "KortemmeLab",
            user = "kortemmelab", #"root",
            passwd = passwd,
            port = 3306,
            unix_socket = "/var/lib/mysql/mysql.sock",
            )

        db_schema = []
        for t in sorted(dbinterface.TableNames):
            creation_string = dbinterface.execute_select('SHOW CREATE TABLE %s' % t)
            assert(len(creation_string) == 1)
            creation_string = '%s;' % creation_string[0]['Create Table'].strip()

            # Fix input for sqlt-diagram (it is fussy)
            creation_string = creation_string.replace("default ''", "")
            creation_string = creation_string.replace("DEFERRABLE INITIALLY DEFERRED", "") # sqlt-diagram doesn't like this syntax for MySQL
            creation_string = creation_string.replace("AUTOINCREMENT", "") # sqlt-diagram doesn't like this syntax for MySQL
            creation_string = re.sub("COMMENT.*'.*'", "", creation_string, re.DOTALL) # sqlt-diagram doesn't like this syntax for MySQL
            creation_string = re.sub("CONSTRAINT.*?CHECK.*?,", "", creation_string, re.DOTALL) # sqlt-diagram doesn't like this syntax for MySQL
            creation_string = re.sub("CONSTRAINT.*?CHECK.*?[)][)]", ")", creation_string, re.DOTALL) # sqlt-diagram doesn't like this syntax for MySQL

            creation_string = re.sub(" AUTO_INCREMENT=\d+", "", creation_string, re.DOTALL)

            creation_string = creation_string.replace("''", "")
            #if t in ['UserDataSet', 'UserAnalysisSet', '_DBCONSTANTS', 'UserRatingSet', 'UserDataSetExperiment']:
            #    continue
            db_schema.append(creation_string)

        db_schema = '\n\n'.join(db_schema)
        self.db_schema = db_schema

    def generate_schema_diagram(self, output_filepath = None, show_fk_only = False):
        tempfiles = self._generate_schema_diagram(show_fk_only)
        import time
        time.sleep(4)

        self.schema_diagram = read_file(tempfiles[1])
        for fname in tempfiles:
            if os.path.exists(fname):
                os.remove(fname)

        if output_filepath:
            write_file(output_filepath, self.schema_diagram)

    def _generate_schema_diagram(self, show_fk_only):

        tempfiles = []

        output_handle, sql_schema_filepath = open_temp_file('/tmp', ftype = 'w')
        tempfiles.append(sql_schema_filepath)
        try:
            output_handle.write('%s\n\n' % self.db_schema)
            print(sql_schema_filepath)
        except:
            output_handle.close()

        #sql_schema_filepath = 'test.txt'
        try:
            png_handle, png_filepath = open_temp_file('/tmp', ftype = 'w')
            png_handle.close()
            tempfiles.append(png_filepath)

            c = [
                "sqlt-diagram",
                "-d=MySQL",
                "-i=png",
                "-t=Schema",
                "-o=%s" % png_filepath,
                "--color",
                sql_schema_filepath,
                ]
            if show_fk_only:
                # Useful to print a smaller schema of just the primary/foreign keys
                c.append("--show-fk-only")
            print(' '.join(c))
            subprocess.Popen(c)

        except Exception, e:
            print('failed!', str(e))

        return tempfiles

if __name__ == '__main__':
    s = MySQLSchema()
    s.generate_schema_diagram(output_filepath = "mytest.png")

