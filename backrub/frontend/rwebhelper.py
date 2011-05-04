#!/usr/bin/python2.4
# -*- coding: iso-8859-15 -*-

# This module contains some helper functions that are accesed by rosettaweb2.py and ???

import sys, os
import re
import _mysql_exceptions

# Common constants

# Sequence Tolerance (Smith and Kortemme)
ROSETTAWEB_max_seqtol_SK_chains = 6
ROSETTAWEB_SK_BoltzmannIncrease = 0.021
ROSETTAWEB_SK_InitialBoltzmann = 0.228
ROSETTAWEB_HK_MaxMutations = 10
ROSETTAWEB_SK_MaxMutations = 10
ROSETTAWEB_SK_MaxPremutations = 30
ROSETTAWEB_SK_RecommendedNumStructures = 10
ROSETTAWEB_SK_Radius = 10.0
ROSETTAWEB_MaxMultiplePointMutations = 30
#todo: change to 20
ROSETTAWEB_SK_RecommendedNumStructuresSeqTolSK = 2

ROSETTAWEB_CONTACT = "Tanja Kortemme"

#todo: Remove these from here - they are defined in rosettahelper
ROSETTAWEB_SK_AA = {"ALA": "A", "CYS": "C", "ASP": "D", "GLU": "E", "PHE": "F", "GLY": "G",
                    "HIS": "H", "ILE": "I", "LYS": "K", "LEU": "L", "MET": "M", "ASN": "N",
                    "PRO": "P", "GLN": "Q", "ARG": "R", "SER": "S", "THR": "T", "VAL": "V",
                    "TRP": "W", "TYR": "Y"}

ROSETTAWEB_SK_AAinv = {}
for k, v in ROSETTAWEB_SK_AA.items():
    ROSETTAWEB_SK_AAinv[v] = k
    
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
