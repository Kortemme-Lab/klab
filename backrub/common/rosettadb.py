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
import traceback
import md5
import pickle
import time

from string import join

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
        
    def __init__(self, hostname, database, user, password, port, socket, store_time, numTries = 1):
        self.connection = MySQLdb.Connection( host=hostname, db=database, user=user, passwd=password, 
                                              port=port, unix_socket=socket )
        self.store_time = store_time
        self.numTries = numTries
        
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
    
    def execQuery(self, sql):
        """execute SQL query"""
        # Note: This loop was always disabled!
        i = 0
        errcode = 0
        while i < self.numTries:
            try:    
                cursor = self.connection.cursor()
                errcode = cursor.execute(sql)
                #@debug:
                #if errcode != 1:
                #    print("%d: %s" %(errcode,traceback.print_stack()))
                results = cursor.fetchall()
                cursor.close()
                return results
            except MySQLdb.OperationalError, e:
                errcode = e[0]
                # errcode 1100 is an error with table locking
                # @debug:
                # sys.stderr.write("\nSQL execution error.")
                # sys.stderr.write("\nErrorcode %d: '%s'.\n" % (e[0], e[1]))
                traceback.print_exc()
                raise MySQLdb.OperationalError
                break
            except:                
                traceback.print_exc()
                break
        return None

    def _getFieldsInDB(self, tablename):
        """get all the fields from a specific table"""
        SQL = 'SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.Columns where TABLE_NAME="%s"' % tablename
    
        array_data = self.execQuery(SQL)
        
        return [x[0] for x in array_data]
    
    def generateHash(self, ID, debug = False):
        # create a hash key for the entry we just made
        sql = '''SELECT PDBComplex, PDBComplexFile, Mini, EnsembleSize, task, ProtocolParameters
                   FROM backrub 
                  WHERE ID="%s" ''' % ID # get data
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
 


if __name__ == "__main__":
    """here goes our testcode"""
    
    test_fields = [ 'ID', 'cryptID', 'Date', 'StartDate', 'EndDate', 'UserID', 'Email', 'Status', 'Notes', 'task', 'PDBComplex', 'ExperimentalValues', 'Errors', 'IPAddress', 'Host', 'ResultsTable', 'PDBComplexFile', 'ResultsRasmol', 'Mini', 'EnsembleSize', 'KeepOutput', 'RDC_temperature', 'RDC_num_designs_per_struct', 'RDC_segment_length'] 

    SQL = 'SELECT Username FROM Users WHERE ID=1'
    print 'test: execQuery()',
    try:
        assert test_db.execQuery(SQL)[0][0] == 'flo', 'test: execQuery() failed'
        print "success"
    except AssertionError:
        print "failed"
    print    
    
    print 'test: _getFieldsInDB()',
    try:
        assert test_db._getFieldsInDB('backrub') == test_fields, 'test: _getFieldsInDB() failed'
        print "success"
    except AssertionError:
        print "failed"
    print
    
    print 'test: getData4ID()',
    try:
        #test some random parameters
        test_data = test_db.getData4ID('backrub', 328)
        assert test_data['ID'] == 328, 'test: getData4ID():ID failed'
        assert test_data['cryptID'] == '7b355bbbe07755de00daf8fc66938229', 'test: getData4ID():cryptID failed'
        assert str(test_data['EndDate']) == '2009-03-19 11:38:53', 'test: getData4ID():EndDate failed'
        assert test_data['Status'] == 2, 'test: getData4ID():Status failed'
        assert test_data['Host'] == 'exception', 'test: getData4ID():Host failed'
        assert test_data['IPAddress'] == '169.230.90.84', 'test: getData4ID():IPAddress failed'
        assert test_data['Mini'] == 0, 'test: getData4ID():Mini failed'
        assert test_data['EnsembleSize'] == 2, 'test: getData4ID():EnsembleSize failed'
        print "success"
    except AssertionError:
        print "failed"
    print    
    
    #print 'test: insertData()'
    ##right
    #print test_db.insertData('backrub', [('Errors','help'),('Host','abaer'),('Mini','2'),('EnsembleSize','101')],[('Date','NOW()')])
    ## and wrong#
    #print test_db.insertData('backrub', [('Errors','help'),('Host','abaer'),('Mini','2'),('EnsembleSize','101')],[('Date','NOW()')])
    #print
    
    #print 'test: updateData()'
    ##right
    #print test_db.updateData(328,'backrub', [('Errors','help'),('Host','abaer'),('Mini','2'),('EnsembleSize','101')],[('Date','NOW()')])
    ## and wrong#
    #print test_db.updateData(328,'backrub', [('Errors','help'),('Host','abaer'),('Mini','2'),('EnsembleSize','101')],[('Date','NOW()')])
    #print
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
