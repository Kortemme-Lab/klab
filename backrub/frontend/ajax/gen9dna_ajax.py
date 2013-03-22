#!/usr/bin/python
# -*- coding: iso-8859-15 -*-

#import cgi


#import json

#import serial
#ser = serial.Serial('/dev/ttyUSB0', 57600)
#ser.write("Hello, this is a command for value %s from slider id!\n" % (form["rating"]))      # write a string
#ser.close()

#F = open("/tmp/testfile.txt", "w")
#F.write(estr)
#F.close()

import cgi
import cgitb
import traceback
import simplejson as json
import sys
import os
import base64

gen9db = None
try:
	
	sys.path.insert(0, '../../common')
	import rosettadb
	form = cgi.FieldStorage()
	#estr = ""
	
	from rosettahelper import WebsiteSettings
	settings = WebsiteSettings(sys.argv, os.environ['SCRIPT_NAME'])

	gen9db = rosettadb.ReusableDatabaseInterface(settings, host = "kortemmelab.ucsf.edu", db = "Gen9Design")
	
	small_molecule = ''
	if form.has_key('small_molecule'):
		small_molecule = form['small_molecule'].value
		results = gen9db.execute("SELECT Diagram FROM SmallMolecule WHERE ID=%s", parameters=(small_molecule,))
		if results:
			contents = results[0]['Diagram']
	elif form.has_key('size'):
		contents = open('../../images/pse%s.png' % form['size'].value, 'rb').read()
	else:
		contents = open('../../images/pse320.png', 'rb').read()
	
#print "Content-type: image/png\n\n"

#print "Content-type: image/png"
#print 'Content-Disposition: inline; filename="%s"' % ('pse320.png')
#print "Content-Length: %d" % len(contents)
#print
#print(json.dumps({"average": '%d' % len(contents)}))
#print(contents)
	print "Content-type: text/plain\n\n"
	print
	print(base64.b64encode(contents))
	F = open("/tmp/testfile.txt", "w")
	F.write("All okay")
	F.close()
	#sys.stdout.write(contents)
	#sys.stdout.flush()
	gen9db.close()
	
except Exception, e:
	if gen9db:
		gen9db.close()
	F = open("/tmp/testfile.txt", "w")
	F.write(str(form))
	F.write("%s\n%s" % (str(e), traceback.format_exc()))
	F.close()

	#print "Content-type: application/json\n\n"
	#print
	#print(json.dumps({"average": 'error'}))

