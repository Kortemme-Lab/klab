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

from string import join

class RosettaDB:
    
    data = {}
    store_time = 7 # how long will the stuff be stored
    
    def __init__(self, hostname, database, user, password, port, socket, store_time):
        self.connection = MySQLdb.Connection( host=hostname, db=database, user=user, passwd=password, 
                                              port=port, unix_socket=socket )
        self.store_time = store_time
        
    def getData4ID(self, tablename, ID):
        """get the whole row from the database and store it in a dict"""
               
        fields = self._getFieldsInDB(tablename)
        #DATE_ADD(EndDate, INTERVAL 8 DAY), TIMEDIFF(DATE_ADD(EndDate, INTERVAL 7 DAY), NOW()), TIMEDIFF(EndDate, StartDate)
        SQL = '''SELECT *,DATE_ADD(EndDate, INTERVAL %s DAY),TIMEDIFF(DATE_ADD(EndDate, INTERVAL %s DAY), NOW()),TIMEDIFF(EndDate, StartDate) 
                 FROM %s WHERE ID=%s''' % (self.store_time, self.store_time, tablename, ID)
        
        array_data = self._execQuery(SQL)
        
        if len(array_data) > 0:
            for x in range( len(fields) ):
                self.data[fields[x]] = array_data[0][x]
            self.data['date_expiration']  = array_data[0][-3]
            self.data['time_expiration']  = array_data[0][-2]
            self.data['time_computation'] = array_data[0][-1]
            
            self.data['parameter'] = pickle.loads( self.data['parameter'] ) # unserialize parameter dict
            
        return self.data
        
    def getData4cryptID(self, tablename, ID):
        """get the whole row from the database and store it in a dict"""
               
        fields = self._getFieldsInDB(tablename)
        
        SQL = '''SELECT *,DATE_ADD(EndDate, INTERVAL %s DAY),TIMEDIFF(DATE_ADD(EndDate, INTERVAL %s DAY), NOW()),TIMEDIFF(EndDate, StartDate) 
                 FROM %s WHERE cryptID="%s"''' % (self.store_time, self.store_time, tablename, ID)
        
        array_data = self._execQuery(SQL)

        if len(array_data) > 0:
            for x in range( len(fields) ):
                self.data[fields[x]] = array_data[0][x]
            self.data['date_expiration']  = array_data[0][-3]
            self.data['time_expiration']  = array_data[0][-2]
            self.data['time_computation'] = array_data[0][-1]
            
            self.data['parameter'] = pickle.loads( self.data['parameter'] ) # unserialize parameter dict
                         
        return self.data
        
            
    def insertData_OLD(self, tablename, dict_value_pairs, list_SQLCMD_pairs=None):
        """insert data into table
            - ID: identifier of the updated value
            - list_value_pairs: contains the table field ID and the according value
            - list_SQLCMD_pairs: contains the table field ID and a SQL command
                          not sure anymore why I need the last one ... maybe for time/date related stuff
            """
        
        fields = self._getFieldsInDB(tablename)
        
        lst_field = []
        lst_value = []
        
        # normal field-value-pairs
        for key, value in dict_value_pairs.iteritems():
            if key in fields:
                lst_field.append( key )
                lst_value.append( '"%s"' % value )
            else:
                print "err: field %s can't be found in the table" % key
                return False
            
        # dict-SQL-command-pairs: the only difference is the missing double quotes in the SQL command
        if dict_SQLCMD_pairs != None:
            for key,value in dict_SQLCMD_pairs:
                if key in fields:
                    lst_field.append( key )
                    lst_value.append( value )
                else:
                    print "err: field %s can't be found in the table" % key
                    return False
                
        # build the command
        SQL = 'INSERT INTO %s (%s) VALUES (%s)' % ( tablename, join(lst_field, ','), join(lst_value, ',') )
        
        self._execQuery( SQL )
        
        return True
    
    # this is somewhat redundant but there are subtle differences
    def updateData(self, ID, tablename, dict_value_pairs, dict_SQLCMD_pairs=None):
        """update data in table
            - ID: identifier of the updated value
            - list_value_pairs: contains the table field ID and the according value
            - list_SQLCMD_pairs: contains the table field ID and a SQL command
            """
                
        fields = self._getFieldsInDB(tablename)
        
        lst_field = []
        # normal field-value-pairs
        for key,value in dict_value_pairs:
            if key in fields:
                lst_field.append( '%s="%s"' % (key, value) )
            else:
                print "err: field %s can't be found in the table" % key
                return False
            
        # field-SQL-command-pairs: the only difference is the missing double quotes in the SQL command
        if dict_SQLCMD_pairs != None:
            for key,value in dict_SQLCMD_pairs:
                if key in fields:
                    lst_field.append( '%s=%s' % (key, value) )
                else:
                    print "err: field %s can't be found in the table" % key
                    return False
                
        # build the command
        SQL = 'UPDATE %s SET (%s) WHERE ID=%s' % ( tablename, join(lst_field, ','), ID )
        
        self._execQuery( SQL )
        
        return True


    def getData4User(self, ID):
        """get all rows for a user from the database and store it to a dict
           do we need this?
           function is empty
        """
        pass
        
        
    def _execQuery(self,sql):
        cursor = self.connection.cursor()
        cursor.execute(sql)
        results = cursor.fetchall()
        cursor.close()
        
        return results   
    
    def _getFieldsInDB(self, tablename):
        """get all the fields from a specific table"""
        SQL = 'SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.Columns where TABLE_NAME="%s"' % tablename
    
        array_data = self._execQuery(SQL)
        
        return [x[0] for x in array_data]
    
















if __name__ == "__main__":
    """here goes our testcode"""
    
    test_fields = [ 'ID', 'cryptID', 'Date', 'StartDate', 'EndDate', 'UserID', 'Email', 'Status', 'Notes', 'task', 'PDBComplex', 'Mutations', 'ExperimentalValues', 'Errors', 'IPAddress', 'Host', 'ResultsTable', 'PDBComplexFile', 'ResultsRasmol', 'Mini', 'EnsembleSize', 'KeepOutput', 'PM_chain', 'PM_resid', 'PM_newres', 'PM_radius', 'RDC_temperature', 'RDC_num_designs_per_struct', 'RDC_segment_length'] 

    test_db = RosettaDB( 'localhost', 'alascan', 'alascan', 'h4UjX!', 3306, '/opt/lampp/var/mysql/mysql.sock' )
    
    SQL = 'SELECT Username FROM Users WHERE ID=1'
    print 'test: _execQuery()',
    try:
        assert test_db._execQuery(SQL)[0][0] == 'flo', 'test: _execQuery() failed'
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
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
