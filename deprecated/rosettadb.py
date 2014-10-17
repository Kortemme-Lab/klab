#!/usr/bin/python2.4
# -*- coding: iso-8859-15 -*-

########################################
# This module interacts with the database and provides 
# access to parameters
# it's the approach to avoid embedded SQL code in python scripts
########################################

# let's do a general approach

import sys, os
import MySQLdb
import MySQLdb.cursors
import traceback
import md5
import pickle
import time
import re
from time import sleep
			
from datetime import datetime

from string import join

DictCursor = MySQLdb.cursors.DictCursor
StdCursor = MySQLdb.cursors.Cursor

import getpass
import rosettahelper

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

class DatabaseInterface(object):
	
	data = {}
	
	def __init__(self, settings, isInnoDB = True, numTries = 1, host = None, db = None, user = None, passwd = None, port = None, unix_socket = None, passwdfile = None):
		self.connection = None
		self.isInnoDB = isInnoDB
		self.host = host or settings["SQLHost"]
		self.db = db or settings["SQLDatabase"]
		self.user = user or settings["SQLUser"]
		self.passwd = passwd or settings["SQLPassword"]
		self.port = port or settings["SQLPort"]
		self.unix_socket	= unix_socket or settings["SQLSocket"]
		self.numTries = numTries
		self.lastrowid = None
		if (not self.passwd) and passwdfile:
			if os.path.exists(passwdfile):
				passwd = rosettahelper.readFile(passwdfile).strip()
			else:
				passwd = getpass.getpass("Enter password to connect to MySQL database:")
				
		self.locked = False
		self.lockstring = "LOCK TABLES %s" % join(["%s WRITE" % r[0] for r in self.execute("SHOW TABLES", cursorClass = StdCursor)], ", ")
		self.unlockstring = "UNLOCK TABLES"
		
		# Store a list of the table names  
		self.TableNames = [r[0] for r in self.execute("SHOW TABLES", cursorClass = StdCursor)]
		
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

	def _get_connection(self, cursorClass):
		self.connection = MySQLdb.connect(host = self.host, db = self.db, user = self.user, passwd = self.passwd, port = self.port, unix_socket = self.unix_socket, cursorclass = cursorClass)
		
	def _close_connection(self):
		if self.connection and self.connection.open:
			self.connection.close()
			
	def getLastRowID(self):
		return self.lastrowid
	
	def locked_execute(self, sql, parameters = None, cursorClass = DictCursor, quiet = False):
		'''We are lock-happy here but SQL performance is not currently an issue daemon-side.''' 
		return self.execute(sql, parameters, cursorClass, quiet = quiet, locked = True)
	
	def execute_select(self, sql, parameters = None, cursorClass = DictCursor, quiet = False, locked = False):
		self.execute(sql, parameters, cursorClass, quiet, locked, do_commit = False)
			
	def execute(self, sql, parameters = None, cursorClass = DictCursor, quiet = False, locked = False, do_commit = True):
		"""Execute SQL query. This uses DictCursor by default."""
		i = 0
		errcode = 0
		caughte = None
		cursor = None
		if sql.find(";") != -1 or sql.find("\\G") != -1:
			# Catches some injections
			raise Exception("The SQL command '%s' contains a semi-colon or \\G. This is a potential SQL injection." % sql)
		while i < self.numTries:
			i += 1
			try:
				assert(not(self.connection) or not(self.connection.open))
				self._get_connection(cursorClass)
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
				self._close_connection()
				return results
			except MySQLdb.OperationalError, e:
				if cursor:
					if self.locked:
						cursor.execute(self.unlockstring)
						self.locked = False
					cursor.close()
				self._close_connection()
				caughte = str(e)
				errcode = e[0]
				continue
			except Exception, e:
				if cursor:
					if self.locked:
						cursor.execute(self.unlockstring)
						self.locked = False
					cursor.close()
				self._close_connection()
				caughte = str(e)
				traceback.print_exc()
				break
			sleep(0.2)
		
		if not quiet:
			sys.stderr.write("\nSQL execution error in query %s at %s:" % (sql, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
			sys.stderr.write("\nErrorcode/Error: %d - '%s'.\n" % (errcode, str(caughte)))
			sys.stderr.flush()
		raise MySQLdb.OperationalError(caughte)
	
	def insertDict(self, tblname, d, fields = None):
		'''Simple function for inserting a dictionary whose keys match the fieldnames of tblname.'''
		
		if fields == None:
			fields = sorted(d.keys())
		values = None
		try:
			SQL = 'INSERT INTO %s (%s) VALUES (%s)' % (tblname, join(fields, ", "), join(['%s' for x in range(len(fields))], ','))
			values = tuple([d[k] for k in fields])
	 		self.locked_execute(SQL, parameters = values)
		except Exception, e:
			if SQL and values:
				sys.stderr.write("\nSQL execution error in query '%s' %% %s at %s:" % (SQL, values, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
			sys.stderr.write("\nError: '%s'.\n" % (str(e)))
			sys.stderr.flush()
			raise Exception("Error occurred during database insertion: '%s'." % str(e))

	def insertDictIfNew(self, tblname, d, PKfields, fields = None):
		'''Simple function for inserting a dictionary whose keys match the fieldnames of tblname. The function returns two values, the
			second of which is a dict containing the primary keys of the record. If a record already exists then no insertion is performed and
			(False, the dictionary of existing primary keys) is returned. Otherwise, the record is inserted into the database and (True, d)
			is returned.'''
		
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
			existingRecord = self.locked_execute("SELECT %s FROM %s" % (PKfields, tblname) + " WHERE %s" % wherestr, parameters = tuple(PKvalues))
			if existingRecord:
				return False, existingRecord[0] 
			
			SQL = 'INSERT INTO %s (%s) VALUES (%s)' % (tblname, join(fields, ", "), join(['%s' for x in range(len(fields))], ','))
			values = tuple([d[k] for k in fields])
			self.locked_execute(SQL, parameters = values)
	 		return True, d 
		except Exception, e:
			if SQL and values:
				sys.stderr.write("\nSQL execution error in query '%s' %% %s at %s:" % (SQL, values, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
			sys.stderr.write("\nError: '%s'.\n" % (str(e)))
			sys.stderr.flush()
			raise Exception("Error occurred during database insertion: '%s'." % str(e))

	def callproc(self, procname, parameters = (), cursorClass = DictCursor, quiet = False):
		"""Calls a MySQL stored procedure procname. This uses DictCursor by default."""
		i = 0
		errcode = 0
		caughte = None
		
		if not re.match("^\s*\w+\s*$", procname):
			raise Exception("Expected a stored procedure name in callproc but received '%s'." % procname)
		while i < self.numTries:
			i += 1
			try:
				assert(not(self.connection) or not(self.connection.open))
				self._get_connection(cursorClass)
				cursor = self.connection.cursor()
				if type(parameters) != type(()):
					parameters = (parameters,)
				errcode = cursor.callproc(procname, parameters)
				results = cursor.fetchall()
				self.lastrowid = int(cursor.lastrowid)
				cursor.close()
				self._close_connection()
				return results
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
			sys.stderr.write("\nSQL execution error call stored procedure %s at %s:" % (procname, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
			sys.stderr.write("\nErrorcode/Error: %d - '%s'.\n" % (errcode, str(caughte)))
			sys.stderr.flush()
		raise MySQLdb.OperationalError(caughte)
	
class ReusableDatabaseInterface(DatabaseInterface):
	def __init__(self, settings, isInnoDB = True, numTries = 1, host = None, db = None, user = None, passwd = None, port = None, unix_socket = None, passwdfile = None, use_utf = False):
		#super(ReusableDatabaseInterface, self).__init__(settings = settings, isInnoDB = isInnoDB, numTries = numTries, host = host, db = db, user = user, passwd = passwd, port = port, unix_socket = unix_socket, passwdfile = passwdfile)
		
		self.connection = None
		self.use_utf = use_utf 
		self.isInnoDB = isInnoDB
		self.host = host or settings["SQLHost"]
		self.db = db or settings["SQLDatabase"]
		self.user = user or settings["SQLUser"]
		self.passwd = passwd or settings.get("SQLPassword")
		self.port = port or settings["SQLPort"]
		self.unix_socket	= unix_socket or settings["SQLSocket"]
		self.numTries = numTries
		self.lastrowid = None
		if (not self.passwd) and passwdfile:
			if os.path.exists(passwdfile):
				self.passwd = rosettahelper.readFile(passwdfile).strip()
			else:
				self.passwd = getpass.getpass("Enter password to connect to MySQL database:")
		self.locked = False
		self.lockstring = "LOCK TABLES %s" % join(["%s WRITE" % r.values()[0] for r in self.execute("SHOW TABLES")], ", ")
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
		
		
		
	def close(self):
		if self.connection and self.connection.open:
			self.connection.close()

	def checkIsClosed(self):
		assert(not(self.connection) or not(self.connection.open))
	
	def _get_connection(self):
		if not(self.connection and self.connection.open):
			if self.use_utf:
				self.connection = MySQLdb.connect(host = self.host, db = self.db, user = self.user, passwd = self.passwd, port = self.port, unix_socket = self.unix_socket, cursorclass = DictCursor, charset='utf8', use_unicode=True)
			else:
				self.connection = MySQLdb.connect(host = self.host, db = self.db, user = self.user, passwd = self.passwd, port = self.port, unix_socket = self.unix_socket, cursorclass = DictCursor)

	def locked_execute(self, sql, parameters = None, cursorClass = DictCursor, quiet = False):
		'''We are lock-happy here but SQL performance is not currently an issue daemon-side.''' 
		return self.execute(sql, parameters = parameters, quiet = quiet, locked = True, do_commit = True)

	def execute_select(self, sql, parameters = None, quiet = False, locked = False):
		return self.execute(sql, parameters = parameters, quiet = quiet, locked = locked, do_commit = False)
			
	def execute_select_StdCursor(self, sql, parameters = None, quiet = False, locked = False):
		return self.execute_StdCursor(sql, parameters = parameters, quiet = quiet, locked = locked, do_commit = False)
	
	def execute_StdCursor(self, sql, parameters = None, quiet = False, locked = False, do_commit = True):
		"""Execute SQL query. This uses DictCursor by default."""
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
				self._get_connection()
				#if not self.connection:
				#	self.connection = MySQLdb.connect(host = self.host, db = self.db, user = self.user, passwd = self.passwd, port = self.port, unix_socket = self.unix_socket, cursorclass = cursorClass)
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
			sys.stderr.write("\nSQL execution error in query %s at %s:" % (sql, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
			sys.stderr.write("\nErrorcode/Error: %d - '%s'.\n" % (errcode, str(caughte)))
			sys.stderr.flush()
		raise MySQLdb.OperationalError(caughte)
	
	def execute(self, sql, parameters = None, quiet = False, locked = False, do_commit = True):
		"""Execute SQL query. This uses DictCursor by default."""
		i = 0
		errcode = 0
		caughte = None
		cursor = None
		cursorClass = DictCursor
		if sql.find(";") != -1 or sql.find("\\G") != -1:
			# Catches some injections
			raise Exception("The SQL command '%s' contains a semi-colon or \\G. This is a potential SQL injection." % sql)
		while i < self.numTries:
			i += 1
			try:
				self._get_connection()
				#if not self.connection:
				#	self.connection = MySQLdb.connect(host = self.host, db = self.db, user = self.user, passwd = self.passwd, port = self.port, unix_socket = self.unix_socket, cursorclass = cursorClass)
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
			sys.stderr.write("\nSQL execution error in query %s at %s:" % (sql, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
			sys.stderr.write("\nErrorcode/Error: %d - '%s'.\n" % (errcode, str(caughte)))
			sys.stderr.flush()
		raise MySQLdb.OperationalError(caughte)
	
	def callproc(self, procname, parameters = (), quiet = False):
		"""Calls a MySQL stored procedure procname. This uses DictCursor by default."""
		i = 0
		errcode = 0
		caughte = None
		
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
				results = cursor.fetchall()
				self.lastrowid = int(cursor.lastrowid)
				cursor.close()
				return results
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
			sys.stderr.write("\nSQL execution error call stored procedure %s at %s:" % (procname, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
			sys.stderr.write("\nErrorcode/Error: %d - '%s'.\n" % (errcode, str(caughte)))
			sys.stderr.flush()
		raise MySQLdb.OperationalError(caughte)
	
	



####
#Website classes and functions
####

def _lowercaseToStr(x):
	return str.lower(str(x))

def _getSortedString(o):
	"""
	Returns a string describing o, sorting the contents (case-insensitive on keys) if o is a dict.
	"""
	# todo: replace this with something like pprint on Python upgrade
	# We assume here that any container type is either list or tuple which may not always hold
	if isinstance(o, (dict)):
		pkeys = sorted(o.keys(), key=_lowercaseToStr)
		l = []
		for k in pkeys:
			l.append(str(k) + ":" + _getSortedString(o[k]))
		return "{" + join(l, ",") + "}"
	else:
		return str(o)

class RosettaDB:
	
	data = {}
	store_time = 7 # how long will the stuff be stored
	
	def close(self):
		self.connection.close()
		
	def __init__(self, settings, numTries = 1, host = None, db = None, user = None, passwd = None, port = None, unix_socket = None):
		host = host or settings["SQLHost"]
		db = db or settings["SQLDatabase"]
		user = user or settings["SQLUser"]
		passwd = passwd or settings["SQLPassword"]
		port = port or settings["SQLPort"]
		unix_socket	= unix_socket or settings["SQLSocket"]
		
		self.connection = MySQLdb.Connection(host = host, db = db, user = user, passwd = passwd, port = port, unix_socket = unix_socket)
		self.store_time = settings["StoreTime"]
		self.numTries = numTries
		self.lastrowid = None
	
	def getLastRowID(self):
		return self.lastrowid
													 
	def getData4ID(self, tablename, ID):
		"""get the whole row from the database and store it in a dict"""
			   
		fields = self._getFieldsInDB(tablename)
		#DATE_ADD(EndDate, INTERVAL 8 DAY), TIMEDIFF(DATE_ADD(EndDate, INTERVAL 7 DAY), NOW()), TIMEDIFF(EndDate, StartDate)
		SQL = '''SELECT *,DATE_ADD(EndDate, INTERVAL %s DAY),TIMEDIFF(DATE_ADD(EndDate, INTERVAL %s DAY), NOW()),TIMEDIFF(EndDate, StartDate) 
				 FROM %s WHERE ID=%s''' % (self.store_time, self.store_time, tablename, ID)

		array_data = self.execQuery(SQL)
		
		if len(array_data) > 0:
			for x in range( len(fields) ):
				self.data[fields[x]] = array_data[0][x]
			self.data['date_expiration']  = array_data[0][-3]
			self.data['time_expiration']  = array_data[0][-2]
			self.data['time_computation'] = array_data[0][-1]

		return self.data
		
	def getData4cryptID(self, tablename, ID):
		"""get the whole row from the database and store it in a dict"""
			   
		fields = self._getFieldsInDB(tablename)
		
		SQL = 'SELECT *,MAKETIME(0,0,TIMESTAMPDIFF(SECOND, StartDate, EndDate)),DATE_ADD(EndDate, INTERVAL %s DAY),TIMESTAMPDIFF(DAY,DATE_ADD(EndDate, INTERVAL %s DAY), NOW()),TIMESTAMPDIFF(HOUR,DATE_ADD(EndDate, INTERVAL %s DAY), NOW()) FROM %s WHERE cryptID="%s"' % (self.store_time, self.store_time, self.store_time, tablename, ID)
		
		array_data = self.execQuery(SQL)
		
		if len(array_data) > 0:
			for x in range( len(fields) ):
				self.data[fields[x]] = array_data[0][x]
			self.data['date_expiration']  = array_data[0][-3]
			time_expiration = None
			if array_data[0][-2] and array_data[0][-1]:
				time_expiration = "%d days, %d hours" % (abs(array_data[0][-2]),abs(array_data[0][-1]) - abs(array_data[0][-2] * 24))			
			self.data['time_expiration']  = time_expiration
			self.data['time_computation'] = array_data[0][-4]
						 
		return self.data
		
			
	def insertData(self, tablename, list_value_pairs, list_SQLCMD_pairs=None):
		"""insert data into table
			- ID: identifier of the updated value
			- list_value_pairs: contains the table field ID and the according value
			- list_SQLCMD_pairs: contains the table field ID and a SQL command
			"""
		
		fields = self._getFieldsInDB(tablename)
		
		lst_field = []
		lst_value = []
		
		# normal field-value-pairs
		for pair in list_value_pairs:
			if pair[0] in fields:
				lst_field.append( pair[0] )
				lst_value.append( '"%s"' % pair[1] )
			else:
				print "err: field %s can't be found in the table" % pair[0]
				return False
			
		# field-SQL-command-pairs: the only difference is the missing double quotes in the SQL command
		if list_SQLCMD_pairs != None:
			for pair in list_SQLCMD_pairs:
				if pair[0] in fields:
					lst_field.append( pair[0] )
					lst_value.append( pair[1] )
				else:
					print "err: field %s can't be found in the table" % pair[0]
					return False
				
		# build the command
		SQL = 'INSERT INTO %s (%s) VALUES (%s)' % ( tablename, join(lst_field, ','), join(lst_value, ',') )
		self.execQuery( SQL )
		
		return True

	def getData4User(self, ID):
		"""get all rows for a user from the database and store it to a dict
		   do we need this?
		   function is empty
		"""
		pass	
	
	def callproc(self, procname, parameters = (), cursorClass = DictCursor, quiet = False):
		"""Calls a MySQL stored procedure procname. This uses DictCursor by default."""
		i = 0
		errcode = 0
		caughte = None
		while i < self.numTries:
			i += 1
			try:	
				cursor = self.connection.cursor(cursorClass)
				if type(parameters) != type(()):
					parameters = (parameters,)
				errcode = cursor.callproc(procname, parameters)
				results = cursor.fetchall()
				self.lastrowid = int(cursor.lastrowid)
				cursor.close()
				return results
			except MySQLdb.OperationalError, e:
				errcode = e[0]
				self.connection.ping()
				caughte = e
				continue
			except:				
				traceback.print_exc()
				break
		
		if not quiet:
			sys.stderr.write("\nSQL execution error call stored procedure %s at %s:" % (procname, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
			sys.stderr.write("\nErrorcode/Error: %d - '%s'.\n" % (errcode, str(caughte)))
			sys.stderr.flush()
		raise MySQLdb.OperationalError(caughte)
	
	def execInnoDBQuery(self, sql, parameters = None, cursorClass = MySQLdb.cursors.Cursor):
		self.connection.ping(True)
		return self.execQuery(sql, parameters, cursorClass, InnoDB = True)
		
	def execQuery(self, sql, parameters = None, cursorClass = MySQLdb.cursors.Cursor, InnoDB = False):
		"""Execute SQL query."""
		i = 0
		errcode = 0
		caughte = None
		while i < self.numTries:
			i += 1
			try:	
				cursor = self.connection.cursor(cursorClass)
				if parameters:
					errcode = cursor.execute(sql, parameters)
				else:
					errcode = cursor.execute(sql)
				if InnoDB:
					self.connection.commit()
				results = cursor.fetchall()
				self.lastrowid = int(cursor.lastrowid)
				cursor.close()
				return results
			except MySQLdb.OperationalError, e:
				errcode = e[0]
				# errcodes of 2006 or 2013 usually indicate a dropped connection  
				# errcode 1100 is an error with table locking
				print(e)
				self.connection.ping(True)
				caughte = e
				continue
			except:				
				traceback.print_exc()
				break
		
		sys.stderr.write("\nSQL execution error in query at %s:" % datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
		sys.stderr.write("\n %s." % sql)
		sys.stderr.flush()
		sys.stderr.write("\nErrorcode: '%s'.\n" % (str(caughte)))
		sys.stderr.flush()
		raise MySQLdb.OperationalError(caughte)
		#return None

	def _getFieldsInDB(self, tablename):
		"""get all the fields from a specific table"""
		SQL = 'SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.Columns where TABLE_NAME="%s"' % tablename
	
		array_data = self.execQuery(SQL)
		
		return [x[0] for x in array_data]
	
	def generateHash(self, ID, debug = False):
		# create a hash key for the entry we just made
		sql = '''SELECT PDBComplex, PDBComplexFile, Mini, EnsembleSize, task, ProtocolParameters FROM backrub WHERE ID="%s" ''' % ID # get data
		result = self.execQuery(sql)
		value_string = "" 
		for value in result[0][0:5]: # combine it to a string
			value_string += str(value)
		
		# We sort the complex datatypes to get deterministic hashes
		# todo: This works better than before (it works!) but could be cleverer.
		value_string += _getSortedString(pickle.loads(result[0][5]))
		
		hash_key = md5.new(value_string.encode('utf-8')).hexdigest() # encode this string
		sql = 'UPDATE backrub SET hashkey="%s" WHERE ID="%s"' % (hash_key, ID) # store it in the database
		if not debug:
			result = self.execQuery(sql)
		else:
			print(sql)
		return hash_key
 
