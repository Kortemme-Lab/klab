#!/usr/bin/python2.4

import os
import sys
import time
import MySQLdb

def execQuery(sql):
    """execute SQL query"""
    i = 1
    while i <= 32:
        try:
            connection = MySQLdb.Connection( host='localhost', db='alascan', user='alascan', passwd='h4UjX!', port='3306', unix_socket='/opt/lampp/var/mysql/mysql.sock' )
            cursor = connection.cursor()
            cursor.execute(sql)
            results = cursor.fetchall()
            cursor.close()
            return results
        except:
            time.sleep(i)
            i += i
            break        
    return None

def clean_db():
    sql = 'DELETE FROM Sessions WHERE Date < DATE_SUB(NOW(), INTERVAL 30 DAY)'
    execQuery(sql)


clean_db()

