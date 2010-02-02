#!/usr/bin/python2.4
# -*- coding: iso-8859-15 -*-

# This module contains some helper functions that are accesed by rosettaweb2.py and ???

import sys, os
import re
import MySQLdb
import _mysql_exceptions

#############################################################################################
# execQuery()                                                                               #
# A general function to execute an SQL query. This function is called whenever a query is   #
# made to the database.                                                                     #
#############################################################################################

def execQuery(connection, sql):
  #connection = MySQLdb.Connection(host=ROSETTAWEB_db_host, db=ROSETTAWEB_db_db, user=ROSETTAWEB_db_user, passwd=ROSETTAWEB_db_passwd, port=ROSETTAWEB_db_port, unix_socket=ROSETTAWEB_db_socket )
  cursor = connection.cursor()
  cursor.execute(sql)
  results = cursor.fetchall()
  cursor.close()
  
  return results

##################################### end of execQuery() ####################################

#############################################################################################
# sendMail()                                                                                #
# sendmail wrapper                                                                          #
#############################################################################################

def sendMail(bin_sendmail, mailTO, mailFROM, mailSUBJECT, mailTXT):
  
  mssg = "To: %s\nFrom: %s\nSubject: %s\n\n%s" % (mailTO, mailFROM, mailSUBJECT, mailTXT)
  # open a pipe to the mail program and
  # write the data to the pipe
  p = os.popen("%s -t" % bin_sendmail, 'w')
  p.write(mssg)
  exitcode = p.close()
  if exitcode:
    return exitcode
  else:
    return 1

##################################### end of sendMail() ######################################

def grep(string,list):
  expr = re.compile(string)
  results = filter(expr.search,[str(line) for line in list])
  return results

#############################################################################################
# read_config_file()                                                                        #
# parser for configuration file                                                             #
#############################################################################################

def read_config_file(filename_config):
    handle = open(filename_config, 'r')
    lines  = handle.readlines()
    handle.close()
    parameter = {}
    for line in lines:
        if line[0] != '#' and len(line) > 1  : # skip comments and empty lines
            # format is: "parameter = value"
            list_data = line.split()
            parameter[list_data[0]] = list_data[2]
    return parameter