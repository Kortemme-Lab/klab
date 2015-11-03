#!/usr/bin/python
# encoding: utf-8
"""
schema.py
Functions for working with database schemas.

The MySQLSchema class requires sqlfairy. To install this on Ubuntu, run:
  sudo apt-get install sqlfairy

Created by Shane O'Connor 2013
"""

import sys
import os
import re
import subprocess
import getpass
import time
import shlex
sys.path.insert(0, '../..')

import klab.colortext as colortext
from mysql import DatabaseInterface as MySQLDatabaseInterface
from klab.fs.fsio import read_file, write_file, open_temp_file


class EmptyDiagramException(Exception): pass

class MySQLSchema(object):

    def __init__(self, settings = {}, isInnoDB=True, numTries=32, host=None, db=None, user=None, passwd=None, port=3306, unix_socket="/var/lib/mysql/mysql.sock", passwdfile=None, use_utf=False):

        self.db = db
        self.host = host
        self.original_schema = []

        if not(os.path.exists(unix_socket)):
            unix_socket = '/var/run/mysqld/mysqld.sock' # Ubuntu hack

        if not passwd and passwdfile:
            if os.path.exists(passwdfile):
                passwd = read_file(passwdfile).strip()
            else:
                passwd = getpass.getpass("Enter password to connect to MySQL database:")

        dbinterface = MySQLDatabaseInterface(settings, isInnoDB = isInnoDB, numTries = numTries, host = host, db = db, user = user, passwd = passwd, port = port, unix_socket = unix_socket, use_locking = False)

        # Get the DB schema, normalizing for sqlt-diagram
        db_schema = []
        self.num_tables = 0
        try:
            for t in sorted(dbinterface.TableNames):
              creation_string = dbinterface.execute_select('SHOW CREATE TABLE `%s`' % t)
              assert(len(creation_string) == 1)
              if creation_string[0].get('Create Table') == None: # e.g. for views
                  continue
              self.num_tables += 1
              creation_string = '%s;' % creation_string[0]['Create Table'].strip()
              self.original_schema.append(creation_string)

              # Fix input for sqlt-diagram (it is fussy)
              creation_string = creation_string.replace("default ''", "")
              creation_string = creation_string.replace("DEFAULT ''", "")
              creation_string = creation_string.replace("DEFERRABLE INITIALLY DEFERRED", "") # sqlt-diagram doesn't like this syntax for MySQL
              creation_string = creation_string.replace("AUTOINCREMENT", "") # sqlt-diagram doesn't like this syntax for MySQL
              creation_string = creation_string.replace("auto_increment", "") # sqlt-diagram doesn't like this syntax for MySQL
              creation_string = re.sub("COMMENT.*'.*'", "", creation_string, re.DOTALL) # sqlt-diagram doesn't like this syntax for MySQL
              creation_string = re.sub("CONSTRAINT.*?CHECK.*?,", "", creation_string, re.DOTALL) # sqlt-diagram doesn't like this syntax for MySQL
              creation_string = re.sub("CONSTRAINT.*?CHECK.*?[)][)]", ")", creation_string, re.DOTALL) # sqlt-diagram doesn't like this syntax for MySQL
              creation_string = re.sub(" AUTO_INCREMENT=\d+", "", creation_string, re.DOTALL)
              creation_string = creation_string.replace("''", "")
              creation_string = creation_string.replace('tg_', 'auth_')
              db_schema.append(creation_string)
        except: raise
        db_schema = '\n\n'.join(db_schema)
        self.db_schema = db_schema
        self.mysqldump_schema = self.get_schema(host, user, passwd, db)


    def print_schema(self):
        c = 1
        for x in self.sanitize_schema().split('\n'):
            colortext.warning('%04d: %s' % (c, x))
            c += 1
   

    def sanitize_schema(self):      
        # Fix input for sqlt-diagram (it is fussy)
        creation_string = self.mysqldump_schema
        creation_string = creation_string.replace("default ''", "")
        creation_string = creation_string.replace("DEFAULT ''", "")
        creation_string = creation_string.replace("DEFERRABLE INITIALLY DEFERRED", "") # sqlt-diagram doesn't like this syntax for MySQL
        creation_string = creation_string.replace("AUTOINCREMENT", "") # sqlt-diagram doesn't like this syntax for MySQL
        creation_string = creation_string.replace("auto_increment", "") # sqlt-diagram doesn't like this syntax for MySQL
        creation_string = re.sub("COMMENT.*'.*'", "", creation_string, re.DOTALL) # sqlt-diagram doesn't like this syntax for MySQL
        creation_string = re.sub("CONSTRAINT.*?CHECK.*?,", "", creation_string, re.DOTALL) # sqlt-diagram doesn't like this syntax for MySQL
        creation_string = re.sub("CONSTRAINT.*?CHECK.*?[)][)]", ")", creation_string, re.DOTALL) # sqlt-diagram doesn't like this syntax for MySQL
        creation_string = re.sub(" AUTO_INCREMENT=\d+", "", creation_string, re.DOTALL)
        creation_string = creation_string.replace("''' ,", "' ,")
        creation_string = creation_string.replace("''',", "',")
        creation_string = creation_string.replace("'' ,", "")
        creation_string = creation_string.replace("'',", "")
        creation_string = creation_string.replace("''", "")
        #write_file('/tmp/failed_schema.sql', creation_string)
        return creation_string


    def get_schema(self, host, username, passwd, database_name):
        try:
            outfile, outfilename = open_temp_file('/tmp', "w")
            p = subprocess.Popen(shlex.split("mysqldump -h %s -u %s -p%s --skip-add-drop-table --no-data %s" % (host, username, passwd, database_name)), stdout=outfile)
            p.wait()
            outfile.close()
            contents = read_file(outfilename)
            os.remove(outfilename)
            return contents
        except Exception, e:
            if os.path.exists(outfilename):
                os.remove(outfilename)
            raise


    def get_full_schema(self):
        # todo: rename this to get_definition as this is more appropriate
        return '\n\n'.join(self.original_schema)

    def generate_schema_diagram(self, output_filepath = None, show_fk_only = False):
        if self.num_tables == 0:
            raise EmptyDiagramException('No tables in schema.')
        tempfiles = self._generate_schema_diagram(show_fk_only)
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
            #output_handle.write('%s\n\n' % self.db_schema)
            output_handle.write('%s\n\n' % self.sanitize_schema())#mysqldump_schema)
            output_handle.close()
        except:
            output_handle.close()

        try:
            png_handle, png_filepath = open_temp_file('/tmp', ftype = 'w')
            png_handle.close()
            tempfiles.append(png_filepath)

            c = [
                "sqlt-diagram",
                "-d=MySQL",
                "-i=png",
                "-t=%s database on %s" % (self.db, self.host),
                "-o=%s" % png_filepath,
                "--color",
                sql_schema_filepath,
                ]
            if show_fk_only:
                # Useful to print a smaller schema of just the primary/foreign keys
                c.append("--show-fk-only")

            p = subprocess.Popen(c, stdout=subprocess.PIPE)
            stdout, stderr = p.communicate()
            if not p.returncode == 0:
                if stderr:
                    raise colortext.Exception("Error - sqlt-diagram exited with %d: '%s'." % (p.returncode, stderr))
                else:
                    raise colortext.Exception("Error - sqlt-diagram exited with %d." % (p.returncode))

        except Exception, e:
            colortext.error('Failed!')
            print(str(e))

        return tempfiles

if __name__ == '__main__':
    s = MySQLSchema(host = "kortemmelab.ucsf.edu", db = "ddG", user = "kortemmelab", passwdfile = 'pw')
    s.generate_schema_diagram(output_filepath = "mytest-ddG.png")
    s = MySQLSchema(host = "kortemmelab.ucsf.edu", db = "KortemmeLab", user = "root", passwdfile = 'mpw')
    s.generate_schema_diagram(output_filepath = "mytest-klab.png")
    #s = MySQLSchema(host = "localhost", db = "DesignCollection", user = "root", passwd = '...')
    #s.generate_schema_diagram(output_filepath = "DesignCollection_schema.png")
    #print(s.get_full_schema())
