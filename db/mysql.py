#!/usr/bin/python2.4
# -*- coding: iso-8859-15 -*-

import sys, os
import MySQLdb
import MySQLdb.cursors
import traceback
import re
from time import sleep
import getpass
from datetime import datetime
from string import join

from tools.fs.io import read_file

DictCursor = MySQLdb.cursors.DictCursor
StdCursor = MySQLdb.cursors.Cursor

class DatabaseInterface(object):

    def __init__(self, settings, isInnoDB=True, numTries=1, host=None, db=None, user=None, passwd=None, port=None,
                 unix_socket=None, passwdfile=None, use_utf=False):
        self.connection = None
        self.StdCursor_connection = None
        self.queries_run = 0
        self.procedures_run = 0
        self.use_utf = use_utf
        self.isInnoDB = isInnoDB
        self.host = host or settings["SQLHost"]
        self.db = db or settings["SQLDatabase"]
        self.user = user or settings["SQLUser"]
        self.passwd = passwd or settings["SQLPassword"]
        self.port = port or settings["SQLPort"]
        self.unix_socket = unix_socket or settings["SQLSocket"]
        self.numTries = numTries
        self.lastrowid = None
        if (not self.passwd) and passwdfile:
            if os.path.exists(passwdfile):
                passwd = read_file(passwdfile).strip()
            else:
                passwd = getpass.getpass("Enter password to connect to MySQL database:")

        self.locked = False
        self.lockstring = "LOCK TABLES %s" % join(["%s WRITE" % r.values()[0] for r in self.execute("SHOW TABLES")],
                                                  ", ")
        self.unlockstring = "UNLOCK TABLES"

        # Store a list of the table names
        self.TableNames = [r.values()[0] for r in self.execute("SHOW TABLES")]

        # Store a hierarchy of objects corresponding to the table names and their field names
        self.FieldNames = _FieldNames(None)
        self.FlatFieldNames = _FieldNames(None)
        tablenames = self.TableNames
        for tbl in tablenames:
            setattr(self.FieldNames, tbl, _FieldNames(tbl))
            fieldDescriptions = self.execute("SHOW COLUMNS FROM %s" % tbl)
            for field in fieldDescriptions:
                fieldname = field["Field"]
                setattr(getattr(self.FieldNames, tbl), fieldname, fieldname)
                setattr(self.FlatFieldNames, fieldname, fieldname)
            getattr(self.FieldNames, tbl).makeReadOnly()
        self.FieldNames.makeReadOnly()
        self.FlatFieldNames.makeReadOnly()


    def __del__(self):
        if self.connection and self.connection.open:
            self.connection.close()
        if self.StdCursor_connection and self.StdCursor_connection.open:
            self.StdCursor_connection.close()


    def close(self):
        if self.connection and self.connection.open:
            self.connection.close()
        if self.StdCursor_connection and self.StdCursor_connection.open:
            self.StdCursor_connection.close()


    def checkIsClosed(self):
        assert ((not (self.connection) or not (self.connection.open)) and (not (self.StdCursor_connection) or not (self.StdCursor_connection.open)))


    def _get_connection(self):
        if not (self.connection and self.connection.open):
            if self.use_utf:
                self.connection = MySQLdb.connect(host=self.host, db=self.db, user=self.user, passwd=self.passwd,
                                                  port=self.port, unix_socket=self.unix_socket, cursorclass=DictCursor,
                                                  charset='utf8', use_unicode=True)
            else:
                self.connection = MySQLdb.connect(host=self.host, db=self.db, user=self.user, passwd=self.passwd,
                                                  port=self.port, unix_socket=self.unix_socket, cursorclass=DictCursor)

    def _get_StdCursor_connection(self):
        if not (self.StdCursor_connection and self.StdCursor_connection.open):
            if self.use_utf:
                self.StdCursor_connection = MySQLdb.connect(host=self.host, db=self.db, user=self.user, passwd=self.passwd,
                                                  port=self.port, unix_socket=self.unix_socket, cursorclass=StdCursor,
                                                  charset='utf8', use_unicode=True)
            else:
                self.StdCursor_connection = MySQLdb.connect(host=self.host, db=self.db, user=self.user, passwd=self.passwd,
                                                  port=self.port, unix_socket=self.unix_socket, cursorclass=StdCursor)

    def _close_connection(self):
        self.close()


    def getLastRowID(self):
        return self.lastrowid


    def locked_execute(self, sql, parameters=None, cursorClass=DictCursor, quiet=False):
        '''We are lock-happy here but SQL performance is not currently an issue daemon-side.'''
        return self.execute(sql, parameters=parameters, quiet=quiet, locked=True, do_commit=True)


    def execute_select(self, sql, parameters=None, quiet=False, locked=False):
        return self.execute(sql, parameters=parameters, quiet=quiet, locked=locked, do_commit=False)


    def execute_select_StdCursor(self, sql, parameters=None, quiet=False, locked=False):
        return self.execute_StdCursor(sql, parameters=parameters, quiet=quiet, locked=locked, do_commit=False)


    def execute_StdCursor(self, sql, parameters=None, quiet=False, locked=False, do_commit=True):
        """Execute SQL query. This uses DictCursor by default."""
        self.queries_run += 1
        i = 0
        errcode = 0
        caughte = None
        cursor = None
        cursorClass = StdCursor
        if sql.find(";") != -1 or sql.find("\\G") != -1:
            # Catches some injections
            raise Exception("The SQL command '%s' contains a semi-colon or \\G. This is a potential SQL injection." % sql)
        while i < self.numTries:
            i += 1
            try:
                self._get_StdCursor_connection()
                cursor = self.StdCursor_connection.cursor()
                if locked:
                    cursor.execute(self.lockstring)
                    self.locked = True
                if parameters:
                    errcode = cursor.execute(sql, parameters)
                else:
                    errcode = cursor.execute(sql)
                self.lastrowid = int(cursor.lastrowid)
                if do_commit and self.isInnoDB:
                    self.StdCursor_connection.commit()
                results = cursor.fetchall()
                if locked:
                    cursor.execute(self.unlockstring)
                    self.locked = False
                cursor.close()
                return results
            except MySQLdb.OperationalError, e:
                if cursor:
                    if self.locked:
                        cursor.execute(self.unlockstring)
                        self.locked = False
                    cursor.close()
                caughte = str(e)
                errcode = e[0]
                continue
            except Exception, e:
                if cursor:
                    if self.locked:
                        cursor.execute(self.unlockstring)
                        self.locked = False
                    cursor.close()
                caughte = str(e)
                traceback.print_exc()
                break
            sleep(0.2)

        if not quiet:
            sys.stderr.write(
                "\nSQL execution error in query %s at %s:" % (sql, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
            sys.stderr.write("\nErrorcode/Error: %d - '%s'.\n" % (errcode, str(caughte)))
            sys.stderr.flush()
        raise MySQLdb.OperationalError(caughte)

    def list_stored_procedures(self):
        return [r['Name'] for r in self.execute("SHOW PROCEDURE STATUS")]

    def run_transaction(self, command_list, do_commit=True):
        '''This can be used to stage multiple commands and roll back the transaction if an error occurs. This is useful
            if you want to remove multiple records in multiple tables for one entity but do not want the deletion to occur
            if the entity is tied to table not specified in the list of commands. Performing this as a transaction avoids
            the situation where the records are partially removed. If do_commit is false, the entire transaction is cancelled.'''

        pass
        # I decided against creating this for now.
        # It may be more useful to create a stored procedure like in e.g. _create_protein_deletion_stored_procedure
        # in the DDGadmin project and then use callproc

        for c in command_list:
            if c.find(";") != -1 or c.find("\\G") != -1:
                # Catches *some* injections
                raise Exception("The SQL command '%s' contains a semi-colon or \\G. This is a potential SQL injection." % c)
        if do_commit:
            sql = "START TRANSACTION;\n%s;\nCOMMIT" % "\n".join(command_list)
        else:
            sql = "START TRANSACTION;\n%s;" % "\n".join(command_list)
        #print(sql)
        return

    def execute(self, sql, parameters=None, quiet=False, locked=False, do_commit=True, allow_unsafe_query=False):
        """Execute SQL query. This uses DictCursor by default."""
        if do_commit:
            pass#print('s')
            self.queries_run += 1
        i = 0
        errcode = 0
        caughte = None
        cursor = None
        cursorClass = DictCursor
        if not(allow_unsafe_query) and (sql.find(";") != -1 or sql.find("\\G") != -1):
            # Catches some injections
            raise Exception("The SQL command '%s' contains a semi-colon or \\G. This is a potential SQL injection." % sql)
        while i < self.numTries:
            i += 1
            try:
                self._get_connection()
                cursor = self.connection.cursor()
                if locked:
                    cursor.execute(self.lockstring)
                    self.locked = True
                if parameters:
                    errcode = cursor.execute(sql, parameters)
                else:
                    errcode = cursor.execute(sql)
                self.lastrowid = int(cursor.lastrowid)
                if do_commit and self.isInnoDB:
                    self.connection.commit()
                results = cursor.fetchall()
                if locked:
                    cursor.execute(self.unlockstring)
                    self.locked = False
                cursor.close()
                return results
            except MySQLdb.OperationalError, e:
                if cursor:
                    if self.locked:
                        cursor.execute(self.unlockstring)
                        self.locked = False
                    cursor.close()
                caughte = str(e)
                errcode = e[0]
                continue
            except Exception, e:
                if cursor:
                    if self.locked:
                        cursor.execute(self.unlockstring)
                        self.locked = False
                    cursor.close()
                caughte = str(e)
                traceback.print_exc()
                break
            sleep(0.2)

        if not quiet:
            sys.stderr.write(
                "\nSQL execution error in query %s at %s:" % (sql, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
            sys.stderr.write("\nErrorcode/Error: %d - '%s'.\n" % (errcode, str(caughte)))
            sys.stderr.flush()
        raise MySQLdb.OperationalError(caughte)


    def callproc(self, procname, parameters=(), quiet=False, expect_return_value=False):
        """Calls a MySQL stored procedure procname. This uses DictCursor by default.
            To get return values back out of a stored procedure, prefix the parameter with a @ character.
        """
        self.procedures_run += 1
        i = 0
        errcode = 0
        caughte = None

        out_param_indices = []
        for j in range(len(parameters)):
            p = parameters[j]
            if type(p) == type('') and p[0] == '@':
                assert(p.find(' ') == -1)
                out_param_indices.append(j)

        if procname not in self.list_stored_procedures():
            raise Exception("The stored procedure '%s' does not exist." % procname)
        if not re.match("^\s*\w+\s*$", procname):
            raise Exception("Expected a stored procedure name in callproc but received '%s'." % procname)
        while i < self.numTries:
            i += 1
            try:
                self._get_connection()
                cursor = self.connection.cursor()
                if type(parameters) != type(()):
                    parameters = (parameters,)
                errcode = cursor.callproc(procname, parameters)
                self.lastrowid = int(cursor.lastrowid)
                cursor.close()

                # Get the out parameters
                out_param_results = []
                if out_param_indices:
                    out_param_results = self.execute('SELECT %s' % ", ".join(['@_%s_%d AS %s' % (procname, pindex, parameters[pindex][1:]) for pindex in out_param_indices]))

                return out_param_results
            except MySQLdb.OperationalError, e:
                self._close_connection()
                errcode = e[0]
                caughte = e
                continue
            except:
                self._close_connection()
                traceback.print_exc()
                break

        if not quiet:
            sys.stderr.write("\nSQL execution error call stored procedure %s at %s:" % (
            procname, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
            sys.stderr.write("\nErrorcode/Error: %d - '%s'.\n" % (errcode, str(caughte)))
            sys.stderr.flush()
        raise MySQLdb.OperationalError(caughte)


    def insertDict(self, tblname, d, fields=None):
        '''Simple function for inserting a dictionary whose keys match the fieldnames of tblname.'''

        self.queries_run += 1
        if fields == None:
            fields = sorted(d.keys())
        values = None
        try:
            SQL = 'INSERT INTO %s (%s) VALUES (%s)' % (
            tblname, join(fields, ", "), join(['%s' for x in range(len(fields))], ','))
            values = tuple([d[k] for k in fields])
            self.locked_execute(SQL, parameters=values)
        except Exception, e:
            if SQL and values:
                sys.stderr.write("\nSQL execution error in query '%s' %% %s at %s:" % (
                SQL, values, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
            sys.stderr.write("\nError: '%s'.\n" % (str(e)))
            sys.stderr.flush()
            raise Exception("Error occurred during database insertion: '%s'." % str(e))


    def insertDictIfNew(self, tblname, d, PKfields, fields=None):
        '''Simple function for inserting a dictionary whose keys match the fieldnames of tblname. The function returns two values, the
            second of which is a dict containing the primary keys of the record. If a record already exists then no insertion is performed and
            (False, the dictionary of existing primary keys) is returned. Otherwise, the record is inserted into the database and (True, d)
            is returned.'''

        self.queries_run += 1
        if type(PKfields) == type(""):
            PKfields = [PKfields]

        if fields == None:
            fields = sorted(d.keys())
        values = None
        SQL = None
        try:
            # Search for existing records
            wherestr = []
            PKvalues = []
            for PKfield in PKfields:
                wherestr.append("%s=%%s" % PKfield)
                PKvalues.append(d[PKfield])
            PKfields = join(PKfields, ",")
            wherestr = join(wherestr, " AND ")
            existingRecord = self.locked_execute("SELECT %s FROM %s" % (PKfields, tblname) + " WHERE %s" % wherestr,
                                                 parameters=tuple(PKvalues))
            if existingRecord:
                return False, existingRecord[0]

            SQL = 'INSERT INTO %s (%s) VALUES (%s)' % (
            tblname, join(fields, ", "), join(['%s' for x in range(len(fields))], ','))
            values = tuple([d[k] for k in fields])
            self.locked_execute(SQL, parameters=values)
            return True, d
        except Exception, e:
            if SQL and values:
                sys.stderr.write("\nSQL execution error in query '%s' %% %s at %s:" % (
                SQL, values, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
            sys.stderr.write("\nError: '%s'.\n" % (str(e)))
            sys.stderr.flush()
            raise Exception("Error occurred during database insertion: '%s'." % str(e))


class _FieldNames(object):
    '''This class is used to store the database structure accessed via element access rather than using raw strings or doing a dict lookup.
       The class can be made read-only to prevent accidental updates.'''

    def __init__(self, name):
        try:
            # If we are creating a new class and the class has already been made read-only then we need to remove the lock.
            # It is the responsibility of the programmer to lock the class as read-only again after creation.
            # A better implementation may be to append this instance to a list and change readonly_setattr to allow updates only to elements in that list.
            getattr(self.__class__, 'original_setattr')
            self.__class__.__setattr__ = self.__class__.original_setattr
        except:
            self.__class__.original_setattr = self.__class__.__setattr__
        self._name = name

    def makeReadOnly(self):
        self.__class__.__setattr__ = self.readonly_setattr

    def readonly_setattr(self, name, value):
        raise Exception("Attempted to add/change an element of a read-only class.")


class ReusableDatabaseInterface(DatabaseInterface):
    def __init__(self, settings, isInnoDB=True, numTries=1, host=None, db=None, user=None, passwd=None, port=None,
                 unix_socket=None, passwdfile=None, use_utf=False):

        print("THE ReusableDatabaseInterface CLASS IS DEPRECATED. PLEASE REPLACE 'ReusableDatabaseInterface' WITH 'DatabaseInterface' IN YOUR CODE.")
        super(ReusableDatabaseInterface, self).__init__(settings, isInnoDB=isInnoDB, numTries=numTries, host=host, db=db, user=user, passwd=passwd, port=port,
                 unix_socket=unix_socket, passwdfile=passwdfile, use_utf=use_utf)
