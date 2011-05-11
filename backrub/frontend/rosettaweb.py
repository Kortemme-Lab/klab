#!/usr/bin/python
# -*- coding: iso-8859-15 -*-

# This module functions as a CGI script, parsing the CGI arguments 
# and calling the appropriate functions from the lower levels to
# produce web pages.


########################################
# functions                            
# 
# ws()                            
# login()                            
# logout()                            
# send_password()                            
# register()                            
## update()                            
# submit()                            
# queue()                            
# jobinfo()                            
# dummy()                            
# make_header()                            
# make_menu()                            
# legal_info()                            
# make_footer()                            
# terms_of_service()                            
# help()                            
# sendMail()
# print_countries()                            
# 
######################################## 

# import the basics
import sys, os
# Append document_root to sys.path to be able to find user modulesface
#sys.path.append(os.environ['DOCUMENT_ROOT'])

sys.path.insert(0, "../common/")
import shutil
import sha, time
import cgi
# import cgitb; cgitb.enable()
import Cookie
# set Python egg dir MscOSX only
if os.uname()[0] == 'Darwin':
  os.environ['PYTHON_EGG_CACHE'] = '/Applications/XAMPP/xamppfiles/tmp'
import _mysql_exceptions
import socket
import md5
import traceback

import urllib2

import session
from rosettahtml import RosettaHTML
import rosettadb
from rwebhelper import *
from rbutils import *
from RosettaProtocols import *
from rosettadatadir import RosettaDataDir

from datetime import datetime
from string import *
from cStringIO import StringIO
from cgi import escape

import string
import pickle

#todo: Test this for debugging import cgitb

###############################################################################################
# Setup: Change these values according to your settings and usage of the server               #
###############################################################################################

parameter = read_config_file()

from pdb import PDB
# todo: this gets more and more messy: solution: make a file with ALL libraries that possibly could ever be accessed by both front- and back-end!
ROSETTAWEB_base_dir = parameter["base_dir"]
sys.path.insert(0, "%sdaemon/" % ROSETTAWEB_base_dir)
from rosettaseqtol import make_seqtol_resfile

ROSETTAWEB_db_host = parameter['db_host']
ROSETTAWEB_db_db = parameter['db_name']
ROSETTAWEB_db_user = parameter['db_user']
ROSETTAWEB_db_passwd = parameter['db_pw']
ROSETTAWEB_db_port = int(parameter['db_port'])
ROSETTAWEB_db_socket = parameter['db_socket']

ROSETTAWEB_server_title = parameter['server_title']
ROSETTAWEB_contact_name = parameter['name_contact']
ROSETTAWEB_contact_email = parameter['email_contact']
ROSETTAWEB_admin_email = parameter['email_admin']

ROSETTAWEB_server_name = parameter['server_name']
ROSETTAWEB_server_script = os.environ['SCRIPT_NAME']

ROSETTAWEB_store_time = parameter['store_time']
ROSETTAWEB_max_point_mutation = 31
ROSETTAWEB_max_seqtol_design = 10
ROSETTAWEB_cookie_expiration = 60 * 60

ROSETTAWEB_bin_sendmail = parameter['bin_sendmail']
ROSETTAWEB_download_dir = parameter['rosetta_dl']

ROSETTAWEB_temp_dir = parameter["rosetta_tmp"]

# Keep a reference to the Apache error stream in case we need to use it for debugging scripts timing out.
apacheerr = sys.stderr     

if ROSETTAWEB_server_name == 'albana.ucsf.edu':
    import profile 
    
# open connection to MySQL
DBConnection = rosettadb.RosettaDB(ROSETTAWEB_db_host, ROSETTAWEB_db_db, ROSETTAWEB_db_user, ROSETTAWEB_db_passwd, ROSETTAWEB_db_port, ROSETTAWEB_db_socket, ROSETTAWEB_store_time)       
########################################## Setup End ##########################################

# todo: These would be tidier as member elements of a ws class
errors = []
warnings = []


def fixFilename(filename):
    filename = filename.replace(' ', '_')
    filename = filename.replace('.', '_')
    filename = filename.replace(':', '_')
    filename = filename.replace('\t', '_')
    if filename[-3:] not in ['pdb', 'PDB' ]:
        filename = filename + '.pdb'
    else:
        filename = filename[:-4] + '.pdb'
    return filename
    
def saveTempPDB(SID, pdb_object, pdb_filename):
    tempdir = "%spdbs" % ROSETTAWEB_temp_dir
    innertempdir = "%s/%s" % (tempdir, SID)
        
    try:
        if not os.path.exists(tempdir):
            os.mkdir(tempdir, 0775)
        if not os.path.exists(innertempdir):
            os.mkdir(innertempdir, 0775)
        
        pdb_filename = fixFilename(pdb_filename)
        filepath = "%s/%s" % (innertempdir, pdb_filename)
        pdb_object.write(filepath)        
        filepath = "pdbs/%s/%s" % (SID, pdb_filename)
        return True, filepath
    except:
        estring = traceback.format_exc()
        if estring.find("IOError: [Errno 13] Permission denied") != -1:
            estring = "Write permission was denied when creating the file. If this persists, please contact support@kortemmelab.ucsf.edu."
        else:
            # We don't know what the error was but returning the string back as is gives the user too much internal information
            # todo: We should log this error and should email the admin as well (update error string to indicate that admin was notified)
            estring = "An error occurred uploading the file. If this persists, please contact support@kortemmelab.ucsf.edu." 
        errors.append(estring)
        return False, ''

def getRosettaVersion(form):
    if form.has_key("ChosenBinary"):
        return form["ChosenBinary"].value
    else:
        return None    #if "protocol" in form:
   
def usingMini(form):
    if form.has_key("ChosenBinary"):
        return RosettaBinaries[form["ChosenBinary"].value]["mini"]
    elif form.has_key("Mini"):
        return RosettaBinaries[form["Mini"].value]["mini"]
    else:
        return None    #if "protocol" in form:
    #    print("proto: %s" % str(form['protocol'].value))
    #else:
    #    print("no protocol")
              
    #if form['protocolgroup'].value == '2' and form['protocoltask'].value == '1':
    #    return 'mini'
    #if form.has_key("Mini"):
    #    return form["Mini"].value # this is either 'mini' or 'classic'
    #elif modus == 4 or modus == 'ensemble': # we're fine and don't need a binary, so let's set a default
    #    return "classic"
    #else:
    #    return None          

###############################################################################################
# ws()                                                                                        #
# This is the main function call. It parses the CGI arguments and generates web pages.        #
# It takes no formal arugments, but parses the following CGI form fields:                     #
#  query  [ register | login | logout | index | terms_of_service | submit | queue | update ]  #
###############################################################################################

protocolGroups = []
protocols = []

def ws():
  s = sys.stdout
  if ROSETTAWEB_server_name == 'albana.ucsf.edu':
      sys.stderr = s # todo: should be removed later
      #todo: Test this for debugging  
      #cgitb.enable(display=0, logdir="/tmp")
  debug = ''
  
  html_content = ''
  query_type = 'dftba'
  SID = ''
  username = ''
  userid = ''
  title = ''

  comment = ''
  warning = ''
  
  # get the POST data from the webserver
  form = cgi.FieldStorage()

  # SECURITY CHECK
  for key in form:
    # Escape HTML code
    form[key].value = escape(form[key].value)
    if (key == "Password" or key == "ConfirmPassword" or key == "myPassword" or key == "password" or key == "confirmpassword"):
      # Store the password as an MD5 hex digest
      tgb = str(form[key].value)
      form[key].value = md5.new(tgb.encode('utf-8')).hexdigest()
    
  ####################################### 
  # cookie check                        #
  ####################################### 

  # create session object
  my_session = session.Session(expires=ROSETTAWEB_cookie_expiration, cookie_path='/')
  # get time of last visit
  lastvisit = my_session.data.get('lastvisit')
  # set session ID
  SID = my_session.cookie['sid'].value
  # get present time as datetime object
  t = datetime.now()
  
  # s.write(str(my_session.cookie)+'\n')
  # s.write("Content-type: text/html\n\n")
  # s.write("%s\n" % (lastvisit))
  # s.write("%s\n" % (SID))
  # my_session.close()
  # s.close() 
  # return
  
  if not (form.has_key("query") and form["query"].value == "datadir"):
          
      if lastvisit == None:  # lastvisit == None means that the user doesn't have a cookie
        
        # set the session object to the actual time and also write the time to the database
        my_session.data['lastvisit'] = repr(time.time())
        lv_strftime = t.strftime("%Y-%m-%d %H:%M:%S")
        sql = "INSERT INTO Sessions (SessionID,Date,query,loggedin) VALUES (\"%s\",\"%s\",\"%s\",\"%s\") " % (SID, lv_strftime, "login", "0")
        result = DBConnection.execQuery(sql)
        # redirect user to the index page
        query_type = "index"
         
        # then create the HTTP header which includes the cookie. THESE LINES MUST NOT BE REMOVED!
        # s.write(str(my_session.cookie)+'\n')  # DO NOT REMOVE OR COMMENT THIS LINE!!!
        # s.write("Content-type: text/html\n\n")
        # s.write("Location: %s?query=%s\n\n" % ( ROSETTAWEB_server_script, query_type ) ) # this line reloads the page
        # close session object
        # my_session.close()
        # s.close() 
        # return
    
      else: # we have a cookie already, let's look it up in the database and check whether the user is logged in
        # set cookie to the present time with time() function
        my_session.data['lastvisit'] = repr(time.time())
        # get infos about session
        sql = "SELECT loggedin FROM Sessions WHERE SessionID = \"%s\"" % SID  # is the user logged in?
        result = DBConnection.execQuery(sql)
        # if this session is active (i.e. the user is logged in) allow all modes. If not restrict access or send him to login.
        if result[0][0] == 1 and form.has_key("query") and form['query'].value in ["register", "login", "loggedin", "logout", "index", "jobinfo", "terms_of_service", "submit", "submitted", "queue", "update", "doc", "delete", "parsePDB"]:
          query_type = form["query"].value
        
          sql = "SELECT u.UserName,u.ID FROM Sessions s, Users u WHERE s.SessionID = \"%s\" AND u.ID=s.UserID" % SID
          result = DBConnection.execQuery(sql)
          if result[0][0] != () and result[0][0] != (): #todo
            username = result[0][0]
            userid = int(result[0][1])
    
        elif form.has_key("query") and form['query'].value in ["register", "index", "login", "terms_of_service", "oops", "doc"]:
          query_type = form["query"].value
        else:
          query_type = "index" # fallback, shouldn't occur

      # send cookie info to webbrowser. DO NOT DELETE OR COMMENT THIS LINE!
      s.write(str(my_session.cookie) + '\n')
      s.write("Content-type: text/html\n\n")
      s.write(debug)
      my_session.close()
   
  ###############################
  # HTML CODE GENERATION
  ###############################

    
  ########## DEBUG Cookies ########## 
  #s.write(string_cookie+'\n<br><br>')
  #s.write('%s <br> sess.cookie = %s <br> sess.data = %s\n<br><br>' % (my_session.cookie, my_session.cookie, my_session.data))
  #s.write(str(my_session.cookie)+'\n<br><br>')
  ########## DEBUG Cookies ##########

  if not os.path.exists('/tmp/daemon-example.pid'):
    if username == 'flo':
      warning = 'Backend not running. Jobs will not be processed immediately.'
    else:
      warning = '' #'Backend not running. Jobs will not be processed immediately.'

  rosettaDD = RosettaDataDir(ROSETTAWEB_server_name, 'RosettaBackrub', ROSETTAWEB_server_script, ROSETTAWEB_CONTACT, ROSETTAWEB_download_dir)
  rosettaHTML = RosettaHTML(ROSETTAWEB_server_name, 'RosettaBackrub', ROSETTAWEB_server_script, ROSETTAWEB_CONTACT, ROSETTAWEB_download_dir, username=username, comment=comment, warning=warning)
  
  global protocolGroups
  global protocols
  feProtocols = FrontendProtocols(rosettaDD, rosettaHTML)
  protocolGroups, protocols = feProtocols.getProtocols()
  
    #######################################
  # show the result files, no login     #
  #######################################
  if form.has_key("query") and form["query"].value == "datadir":
    s.write("Content-type: text/html\n\n")
    
    cryptID = ''
    status = ''
    task = ''
    html_content = ''
    mini = False

    if form.has_key("job"):
      cryptID = form["job"].value
      sql = 'SELECT ID,Status,task,mini,PDBComplexFile FROM backrub WHERE cryptID="%s"' % (cryptID)
      result = DBConnection.execQuery(sql)
      if len(result) > 0:
          jobid = result[0][0]
          status = result[0][1]
          task = result[0][2]
          
          mini = RosettaBinaries[result[0][3]]['mini']
          pdb_filename = result[0][4]
      else:
          html_content = "Either an invalid job ID was given or else the job no longer exists in the database."  
    else:
      html_content = "Invalid link. No job ID given."
      
    if status == 1: # running
      html_content = '<br>Job is Running. Please check again later.'
    elif status == 0:
      html_content = '<br>Job in queue. Please check again later.'
    elif status in [3, 4]:
      html_content = '<br>No data.'
        
    found = False
    if html_content == '':
        for p in protocols:
            if task == p.dbname:
                found = True
                p.getDataDirFunction()(cryptID, jobid, mini, pdb_filename)
                break
    if not found:
        html_content = "No data."

    s.write(rosettaDD.main(html_content))

    s.close()
    return

  # session is now active, execute function
  # if query_type == "index":
  #   html_content = rosettaHTML.index()
  #   title = 'Home'

  if query_type == "login" or query_type == "index":
    login_return = login(form, my_session, t)
    if login_return == True:
      username = form["myUserName"].value
      html_content = rosettaHTML.loggedIn(username)
    elif login_return in ['no_password', 'wrong_password', 'wrong_username']:
      html_content = rosettaHTML.login(message='Wrong username or password. Please try again.')
    elif login_return == 'logged_in':
      html_content = rosettaHTML.login(message='You\'re already logged in.', login_disabled=True)
    else:
      html_content = rosettaHTML.login()
    title = 'Home'

  elif query_type == "loggedin":
    html_content = rosettaHTML.loggedIn(username) 

  elif query_type == "logout":
    if logout(form, my_session):
      html_content = rosettaHTML.logout(username)
    else:
      html_content = rosettaHTML.index()
    title = 'Logout'

  elif query_type == "parsePDB":
      #html_content = rosettaHTML.submit(jobname='')
      #form
      
      protocol = (form["protocolgroup"].value, form["protocoltask"].value)
      
      #if False:
      pdb_okay, pdbfile, pdb_filename, pdb_object = parsePDB(rosettaHTML, form)
      if not pdb_okay:
          # reset the query for the JS startup function
          query_type = "submit"
          html_content = rosettaHTML.submit(jobname='', errors=errors, activeProtocol = protocol)
      else:              
          saveSucceeded, newfilepath = saveTempPDB(SID, pdb_object, pdb_filename)
          if not saveSucceeded:
              # reset the query for the JS startup function
              query_type = "submit"
              html_content = rosettaHTML.submit(jobname='', errors=errors)
          else:
              PDBchains = pdb_object.chain_ids() 
              numPDBchains = len(PDBchains)
              
              
              if numPDBchains > ROSETTAWEB_max_seqtol_SK_chains:
                  errors.append('The PDB file contains %d chains. The maximum number of chains currently supported by the applications is %d.' % (numPDBchains, ROSETTAWEB_max_seqtol_SK_chains))
              
              extraValues = '<INPUT TYPE="hidden" NAME="ChosenBinary" VALUE="%s">' % form["Mini"].value

              html_content = rosettaHTML.submit('', errors, protocol, pdb_filename, newfilepath, pdb_object.chain_ids(), form["MiniTextValue"].value, extraValues)
              title = 'Submission Form'
      
  elif query_type == "submitted":    
    return_val = submit(rosettaHTML, form, SID)
    if return_val: # data was submitted and written to the database
        html_content = rosettaHTML.submitted('', return_val[0], return_val[1], warnings)
        title = 'Job submitted'
    else: # no data was submitted/there is an error
        html_content = rosettaHTML.submit(jobname='', errors=errors)
        title = 'Submission Form'

  elif query_type == "submit":
    html_content = rosettaHTML.submit(jobname='')
    title = 'Submission Form'

  elif query_type == "queue":
    job_list = queue(form, userid)
    html_content = rosettaHTML.printQueue(job_list)
    title = 'Job Queue'

  elif query_type == "jobinfo":
    parameter = jobinfo(form, SID)
    if parameter[0]:
        html_content = rosettaHTML.jobinfo(parameter[1])
    else:
        html_content = '<td align="center">No Data<br><br></td>'
    title = 'Job Info'

  elif query_type == "register":
    register_result = register(form, SID)
    if register_result[0]:
        if register_result[1] == 'updated':
            html_content = rosettaHTML.updated()
        else:
            html_content = rosettaHTML.registered()
    else:
        html_content = rosettaHTML.register(errors=errors)
    title = 'Registration'

  elif query_type == "update":
    user_data = getUserData(form, SID)
    html_content = rosettaHTML.register(username=user_data['username'],
                                        firstname=user_data['firstname'],
                                        lastname=user_data['lastname'],
                                        institution=user_data['institution'],
                                        email=user_data['email'],
                                        address=user_data['address'],
                                        city=user_data['city'],
                                        zip=user_data['zip'],
                                        state=user_data['state'],
                                        country=user_data['country'],
                                        update=True)
    title = 'User Information'

  elif query_type == "terms_of_service":
    html_content = rosettaHTML.terms_of_service()
    title = 'Terms of Service'

  elif query_type == "doc":
    html_content = rosettaHTML.help()
    title = 'Documentation'

  elif query_type == "delete":
    html = deletejob(form, SID)
    title = 'Job Deleted'

  elif query_type == "oops":
    password_result = send_password(form)
    if password_result[0]:
        html_content = rosettaHTML.passwordUpdated(password_result[1])
    else:
        html_content = rosettaHTML.sendPassword(password_result[1])
    title = 'Password'

  else:
    html = "this is impossible" # should never happen since we only allow states from list above 

  s.write(rosettaHTML.main(html_content, title, query_type))

  s.close() 

########################################## end of ws() ########################################



###############################################################################################
# login()                                                                                     #
#   performs all necessary actions to log in a users                                          # 
###############################################################################################


def login(form, my_session, t):
  
  # get session info
  SID = my_session.cookie['sid'].value
  lv_strftime = t.strftime("%Y-%m-%d %H:%M:%S")
    
  ## we first check if the user can login
  if form.has_key('login') and form['login'].value == "login":
    # this is for the guest user
    if not form.has_key('myUserName'):
      return 'wrong_username'
    elif form["myUserName"].value == "guest" and not form.has_key('myPassword'):
      password_entered = ''
    elif not form.has_key('myPassword'):
      return 'wrong_password'
    else:
      password_entered = form["myPassword"].value
    # check for userID and password
    sql = 'SELECT ID,Password FROM Users WHERE UserName = "%s"' % form["myUserName"].value
    result = DBConnection.execQuery(sql)
    try:
      UserID = result[0][0]
      PW = result[0][1]
      if password_entered == PW: 
        # all clear ... go!
        sql = "UPDATE Sessions SET UserID = \"%s\", Date = \"%s\", loggedin = \"%s\" WHERE SessionID = \"%s\" " % (UserID, lv_strftime, "1", SID)
        result = DBConnection.execQuery(sql)
        return True # successfully logged in

      else:
        return 'wrong_password'
    except IndexError:
      return 'wrong_username'

#  elif not form.has_key('myPassword'):
#    return 'no_password' 

  else: # need form
    sql = "SELECT loggedin FROM Sessions WHERE SessionID = \"%s\"" % SID
    result = DBConnection.execQuery(sql)
    if result[0][0] == 1:
      return 'logged_in'

    return False

################################### end login() ###############################################

###############################################################################################
# logout()                                                                                    #
#  set logged in status to not logged in                                                      #
###############################################################################################

def logout(form, my_session, SID=None):
    # get sessionID
    if SID == None:
      SID = my_session.cookie['sid'].value
    # update database
    sql = "UPDATE Sessions SET loggedin = \"%s\" WHERE SessionID = \"%s\" " % ("0", SID)
    DBConnection.execQuery(sql)

    return True

################################### end logout() ##############################################

###############################################################################################
# send_password()                                                                             #
# asks for an email address to send password to                                               #
###############################################################################################

def send_password(form):
  password_updated = True
  message = ''
  
  if form.has_key("Email"):
    import random
    Email = form["Email"].value
    
    sql = "SELECT ID,FirstName,UserName FROM Users where Email=\"%s\"" % Email
    result = DBConnection.execQuery(sql)
    
    if len(result) < 1:
      password_updated = False
      message = 'Your email address is not in our database. Please <A href="rosettaweb.py?query=register">register</A>.<br><br> \n'
    else:
      password = join(random.sample('0123456789abcdefghijklmnopqrstuvwxyz0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789', 6), '')
      crypt_pw = md5.new(password.encode('utf-8')).hexdigest()
      
      sql = 'UPDATE Users SET Password="%s" WHERE ID=%s' % (crypt_pw, result[0][0])
      result_null = DBConnection.execQuery(sql)
      
      text = """Dear %s,
    
Your username and a temporary Password are listed below. This email was 
generated upon request to send you a new password. Please login and change
your password.

If you DID NOT request to reset your password, please let us know.
mailto:support@kortemmelab.ucsf.edu 
  
-----------------------
LOGIN NAME AND PASSWORD
-----------------------
              
LOGIN NAME:  %s
  PASSWORD:  %s
  
Have a nice day!

The Kortemme Lab Server Daemon

      """ % (result[0][1], result[0][2], password)
        
      if sendMail(ROSETTAWEB_bin_sendmail, Email, ROSETTAWEB_admin_email, "[Kortemme Lab Server] Forgotten Password Request", text) == 1:
          message = 'New password was send to %s <br><br> \n' % Email
      else:
          password_updated = False
          message = 'Sending password failed. <br><br> \n'
  
  else: 
    password_updated = False
  
  return (password_updated, message)

################################### end send_password() #######################################

###############################################################################################
# register()                                                                                  #
#  present either a form for registration or check if user or emailadress already exist       #
#  if not add new user to database                                                            #
###############################################################################################


def _checkUserInfo(form):
    # check whether email or username are already in database
    # other values are checked by java script when entering in form
    process_data = True
    error = None
    
    sql = "SELECT * FROM Users WHERE UserName =\"%s\"" % form["username"].value
    sql_out = DBConnection.execQuery(sql)
    if len(sql_out) >= 1:           # if we get something, name is already taken
      form["username"].value = ''   # reset
      process_data = False 
      error = 'Username is already in use.'
    
    sql = "SELECT * FROM Users WHERE Email = \"%s\"" % form["email"].value
    sql_out = DBConnection.execQuery(sql)
    if len(sql_out) >= 1:
      form["email"].value = ''
      process_data = False
      error = 'Email address is already registered.'
    
    # check whether password is correct:
    if form["password"].value != form["confirmpassword"].value:
      process_data = False
      error = 'Passwords do not match.'    
    
    return (process_data, error)

def _updateUserInfo(form, SID):
    # transmit values to database
    # define allowed fields 
    value_list = ["username", "firstname", "lastname", "institution", "email", "password"]
    value_list_o = ["address", "city", "zip", "state", "country"]  
    value_names = {"username" : "UserName", "firstname" : "FirstName", "lastname" : "LastName", "email" : "Email", "institution" : "Institution", "address":"Address1", "city":"City", "state" : "State", "zip" : "Zip", "country" : "Country", "password" : "Password"}
    
    # check whether each parameter has a value and if so append it to the database string
    fields = ""
    variables = ""
    # get userid from db
    sql = "SELECT UserID from Sessions WHERE SessionID = \"%s\" " % SID
    result = DBConnection.execQuery(sql)
    userid = result[0][0]
    
    for value_name in value_list:
        if form.has_key(value_name):
            fields += value_names[value_name] + "=\"" + form[value_name].value + "\", "
    for value_name in value_list_o:
        if form.has_key(value_name):
            fields += value_names[value_name] + "=\"" + form[value_name].value + "\", "
    sql = "UPDATE Users SET %s WHERE ID=%s" % (fields[:-2], userid)
    #print sql
    DBConnection.execQuery(sql)


def register(form, SID):
  
  # define allowed fields 
  value_list = ["username", "firstname", "lastname", "email", "password"]
  value_list_o = ["address", "institution", "city", "zip", "state", "country"]  
  value_names = {"username" : "UserName", "firstname" : "FirstName", "lastname" : "LastName", "email" : "Email", "institution" : "Institution", "address":"Address1", "city":"City", "state" : "State", "zip" : "Zip", "country" : "Country", "password" : "Password"}
  process_data = True
  form_db = {}    # store values retrieved from Database
  
  if form.has_key("mode") and form["mode"].value == "check":
    process_data, error = _checkUserInfo(form)
    if error:
        errors.append(error)
  elif form.has_key("mode") and form["mode"].value == "update":
    _updateUserInfo(form, SID)
    return (True, 'updated')
  else:
    process_data = False
    
  if process_data:
    # transmit values to database
    # check whether each parameter has a value and if so append it to the database string
    fields = ""
    variables = ""
    for value_name in value_list:
      if form.has_key(value_name):
        fields += value_names[value_name] + ","
        variables += "\"%s\"," % form[value_name].value
    for value_name in value_list_o:
      if form.has_key(value_name):
        fields += value_names[value_name] + ","
        variables += "\"%s\"," % form[value_name].value
      sql = "INSERT INTO Users (Date, %s) VALUES (NOW(), %s)" % (fields[:-1], variables[:-1])
    #print sql
    DBConnection.execQuery(sql)

    # send a conformation email
    text = """Dear %s,

Thank you for creating an account at the %s. If you have questions or if you did not create an account please let us know: %s 

-----------------------
login:       %s
Name:        %s %s

Have a nice day!

The Kortemme Lab Server Daemon
      
      """ % (form["firstname"].value, ROSETTAWEB_server_title, ROSETTAWEB_admin_email, form["username"].value, form["firstname"].value, form["lastname"].value)
    
    sendMail(ROSETTAWEB_bin_sendmail, form["email"].value, ROSETTAWEB_admin_email, "[Kortemme Lab Server] New Account", text)
    
    text_to_admin = """Dear administrator,
    
A new user account for %s was created:

login:       %s
Name:        %s %s

Have a nice day!

The Kortemme Lab Server Daemon

    """ % (ROSETTAWEB_server_title, form["username"].value, form["firstname"].value, form["lastname"].value)

    sendMail(ROSETTAWEB_bin_sendmail, ROSETTAWEB_admin_email, ROSETTAWEB_admin_email, "[Kortemme Lab Server] New Account created", text_to_admin)

  return (process_data)


################################### end register() ############################################

###############################################################################################
# update()                                                                                    #
#  here we have a little redundancy (register()) that might be removed sometime               #
#  for now this is better. due to the database call I have to make a different type of map    #
#  than the one used for "form". yes ... i dunno, works though! ;)                            #
###############################################################################################

def getUserData(form, SID):
  # define allowed fields 
  value_list = ["username", "firstname", "lastname", "institution", "email", "password"]
  value_list_o = ["address", "city", "zip", "state", "country"]  
  value_names = {"username" : "UserName", "firstname" : "FirstName", "lastname" : "LastName", "email" : "Email", "institution" : "Institution", "address":"Address1", "city":"City", "state" : "State", "zip" : "Zip", "country" : "Country", "password" : "Password"}
  process_data = True
  form_db = {}   # store values retrieved from Database
  
  # get userid from db
  sql = "SELECT UserID from Sessions WHERE SessionID = \"%s\"" % SID
  result = DBConnection.execQuery(sql)
  # get all user data from DB
  UserID = result[0][0]
  sql = "SELECT * FROM Users WHERE ID = \"%s\"" % UserID
  sql_out = DBConnection.execQuery(sql)
  
  # create a dict with that information
 
  if len(sql_out) >= 1 :
    form_db["username"] = sql_out[0][1]
    form_db["lastname"] = sql_out[0][2]
    form_db["firstname"] = sql_out[0][3]
    form_db["email"] = sql_out[0][4]
    form_db["institution"] = sql_out[0][5]
    form_db["address"] = sql_out[0][6]
    #form_db["Address2"]      = sql_out[0][7]
    form_db["city"] = sql_out[0][8]
    form_db["state"] = sql_out[0][9]
    form_db["zip"] = sql_out[0][10]
    form_db["country"] = sql_out[0][11]
    #form_db["Phone"]         = sql_out[0][12]
    #form_db["Password"]      = sql_out[0][13]
    #form_db["Date"]          = sql_out[0][14]
    #form_db["LastLoginDate"] = sql_out[0][15]
    #form_db["Priority"]      = sql_out[0][16]
    #form_db["Jobs"]          = sql_out[0][17]
    #form_db["EmailList"]     = sql_out[0][18]
  
  # this simply converts the mysql None entries into empty strings, noone pick None as value now! 
  for key, value in form_db.iteritems():
    if value == 'None':
      form_db[key] = ''
  
  return form_db

################################### end update() ##############################################

def check_pdb(pdb_object, pdb_filename, usingClassic, ableToUseMini):
    '''checks pdb file for errors'''
    
    # check the formatting of the file
    pdb_check_output, wrns = pdb_object.check_format(usingClassic, ableToUseMini)
    if pdb_check_output != True:
        errors.append("PDB format incorrect in %s:<p style='text-align:left'>" % pdb_filename)
        errors.extend(pdb_check_output)
        errors.append("</p>")
        return False
    else:
        warnings.extend(wrns)
    
    # check the number of atoms/residues/chains;
    # numbers are derived from 1KYO wich is huge: {'models': 0, 'chains': 23, 'residues': 4459, 'atoms': 35248}
    counts = pdb_object.get_stats()
    #todo: Parameterize these constants in rwebhelper
    if counts["atoms"] > 10000:
        errors.append("Maximum number of atoms exceeded;<br>The maximum is %d, the PDB contained %d." % (10000, counts["atoms"]))
        return False
    elif counts["residues"] > 1500:
        errors.append("Maximum number of residues exceeded;<br>The maximum is %d, the PDB contained %d." % (500, counts["residues"]))
        return False
    # todo: This value used to be 4 but ROSETTAWEB_max_seqtol_SK_chains is currently greater than 4 so we use that
    elif counts["chains"] > ROSETTAWEB_max_seqtol_SK_chains:
        errors.append("Maximum number of chains exceeded;<br>The maximum is %d, the PDB contained %d." % (ROSETTAWEB_max_seqtol_SK_chains, counts["chains"]))
        return False
    elif counts["cys"] > 50:
        errors.append("Maximum number of Cysteine residues exceeded;<br>The maximum is %d, the PDB contained %d." % (50, counts["cys"]))
        return False
    else:
        return True
    

def extract_1stmodel(pdbfile):
    # check if structure is NMR or X-RAY. Problem: if headerinfo and EXPDTA line are missing there is no way of telling.
    # Consider only the first model. Copy everything until the first ENDMDL entry.
    new_pdbfile = ''
    for line in pdbfile.split('\n'):
      new_pdbfile += line + '\n'
      if line.rstrip() == 'ENDMDL':
        new_pdbfile += 'END\n'
        break
    return new_pdbfile

###############################################################################################
# submit()                                                                                    #
# this function processes the parameter of the input form and adds a new job to the database  # 
###############################################################################################

def parsePDB(rosettaHTML, form):
    ############## PDB STUFF ###################
    pdb_okay = True
    pdbfile = ''
    pdb_filename = None
    pdb_object = None

    pgroup, ptask = int(form["protocolgroup"].value), int(form["protocoltask"].value)
    protocol = protocolGroups[pgroup][ptask]
    usingClassic = not(usingMini(form))
    ableToUseMini = protocol.canUseMini()
    if form.has_key("PDBComplex") and form["PDBComplex"].value != '':
        try:
            pdbfile = form["PDBComplex"].value
            if not form["PDBComplex"].file:
                errors.append("PDB data is not a file.")
            pdb_filename = form["PDBComplex"].filename
            pdb_filename = fixFilename(pdb_filename)
        except:
            errors.append("Invalid PDB file.")
            pdb_okay = False
    
    elif form.has_key("PDBID") and form["PDBID"].value != '':
        try:
            pdb_filename = form["PDBID"].value.upper() + '.pdb'
            url = "http://www.pdb.org/pdb/files/%s" % pdb_filename
            req = urllib2.Request(url)
            response = urllib2.urlopen(req)
            pdbfile = response.read()
            if len(pdbfile) <= 2:
                errors.append("Invalid PDB identifier.")
                pdb_okay = False
        except:
            errors.append("Invalid PDB identifier.")
            pdb_okay = False
    elif form.has_key("StoredPDB"):
        # We should have gotten here from a ParsePDB generated webpage
        # The filename in StoredPDB should have been created by saveTempPDB 
        sPDB = form["StoredPDB"].value
        if sPDB != '' and re.match("pdbs/[A-Z\d]+/[^\\/]+\.pdb", sPDB, re.IGNORECASE):
            # The filename should be generated from always match this if SID is alphanumeric
            try:
                pdb_filename = sPDB
                F = open("%s%s" % (ROSETTAWEB_temp_dir, pdb_filename), "r") 
                pdbfile = F.read()
                F.close()
            except Exception, e:
                errors.append("An I/O error (%s) occurred reading the uploaded file. Please contact support@kortemmelab.ucsf.edu." % e)
                pdb_okay = False
        else:
            # Something odd happened. We have gremlins on the bus.
            errors.append("The uploaded file could not be retrieved. Please contact support@kortemmelab.ucsf.edu.")
            pdb_okay = False
            
    else:
        errors.append("Invalid structure file.")
        pdb_okay = False
    
    if not pdb_okay:
        return pdb_okay, pdbfile, pdb_filename, pdb_object
    else:
        pdbfile = pdbfile.replace('"', ' ')  # removes \" that mislead python. not needed anyway
        pdbfile = extract_1stmodel(pdbfile) # removes everything but one model for NMR structures
        
        pdb_object = PDB(pdbfile.split('\n'))
        if form["AtomOccupancy"].value == "remove":
            pdb_object.removeUnoccupied()
        elif form["AtomOccupancy"].value == "fill":
            pdb_object.fillUnoccupied()
        
        pdb_check_result = check_pdb(pdb_object, pdb_filename, usingClassic, ableToUseMini)
        if not pdb_check_result:
            return pdb_check_result, pdbfile, pdb_filename, pdb_object
    
    # Specific check for sequence tolerance protocol
    if protocol.dbname == "sequence_tolerance":
        if len(pdb_object.chain_ids()) < 2:
            errors.append("The %s protocol requires at least two chains to be selected - the PDB only contains %d." % (protocol.name, len(pdb_object.chain_ids())))
            pdb_okay = False

    return pdb_okay, pdbfile, pdb_filename, pdb_object

            
def submit(rosettaHTML, form, SID):
    ''' This function processes the general parameters and writes them to the database'''
    s = StringIO()
    
    # get information from the database
    sql = 'SELECT UserID FROM Sessions WHERE SessionID = "%s"' % SID
    result = DBConnection.execQuery(sql)
    UserID = result[0][0]
    sql = 'SELECT UserName, Email FROM Users WHERE ID = "%s"' % UserID
    sql_out = DBConnection.execQuery(sql)
    UserName = sql_out[0][0]
    Email = sql_out[0][1]
    JobName = ""
    Partner = ""
    cryptID = ''
    pdbfile = ''
    pdb_object = None
    pgroup = None
    ptask = None
    
    try:
        # 2 modes: check and show form
        if form.has_key("mode") and form["mode"].value == "check":
            
            # check whether all arguments were entered is done by javascript
            # if that is not the case, something went wrong and we'll get a python exception here
            # so here we could add error handling if it would be necessary
            if form.has_key("JobName"):
                JobName = escape(form["JobName"].value)
    
            try:
                pgroup, ptask = int(form["protocolgroup"].value), int(form["protocoltask"].value)        
                modus = protocolGroups[pgroup][ptask].dbname
            except:
                errors.append("No Application selected.")
                return False

            ############## PDB STUFF ###################
                        
            pdb_okay, pdbfile, pdb_filename, pdb_object = parsePDB(rosettaHTML, form)
            if not pdb_okay:
                return False
            ############## PDB STUFF END ###############
                    
                                            
            # Note: Forces a cap on the number of structures
            #       This should be unnecessary as the JavaScript should enforce it
            nos = min(int(form["nos"].value), protocolGroups[pgroup][ptask].getNumStructures()[2])
                
            if form.has_key("keep_output") and int(form["keep_output"].value) == 1:
                keep_output = 1
            else:
                keep_output = 1 # ALWAYS KEEP OUTPUT FOR NOW
            
            mini = getRosettaVersion(form)
            if mini == None:
                # this is preselected in HTML code, so this case should never occur, we still make sure!
                errors.append("No Rosetta binary selected.")
                return False
            
            ProtocolParameters = {}    
            
            for protocol in protocols:                       
                if protocol.dbname == modus:
                    ProtocolParameters = protocol.StoreFunction(form, pdb_object)
                    if not ProtocolParameters:
                        errors.append("Server error: The store procedure for the protocol %s failed." % modus)
                        return False   
            
            # todo: output where the time is going on Albana
            # todo: add test input button which tests submit but does not add a job to the db
            ProtocolParameters = pickle.dumps(ProtocolParameters)
            
            return_vals = (cryptID, "new") # true we processed the data
        
            if not errors:
                # if we're good to go, create new job
                # get ip addr hostname
                IP = os.environ['REMOTE_ADDR']
                sock = socket
                try:
                    hostname = sock.gethostbyaddr(IP)[0]
                except:
                    hostname = IP
                # lock table
                sql = "LOCK TABLES backrub WRITE, Users READ"
                DBConnection.execQuery(sql)
                # write information to database
                
                # Strip the path information from  the pdb
                m = re.match("pdbs/[A-Z\d]+/([^\\/]+\.pdb)", pdb_filename, re.IGNORECASE)
                if m:
                    pdb_filename = m.group(1)
                
                # Add a dummy hashkey as this field should not be NULL
                sql = """INSERT INTO backrub ( Date,hashkey,Email,UserID,Notes, PDBComplex,PDBComplexFile,IPAddress,Host,Mini,EnsembleSize,KeepOutput,task, ProtocolParameters) 
                                VALUES (NOW(), "0", "%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s")""" % (Email, UserID, JobName, pdbfile, pdb_filename, IP, hostname, mini, nos, keep_output, modus, ProtocolParameters)
                  
                try: 
                    import random
                    DBConnection.execQuery(sql)
                    sql = """SELECT ID FROM backrub WHERE UserID="%s" AND Notes="%s" ORDER BY Date DESC""" % (UserID , JobName)
                    result = DBConnection.execQuery(sql)
                    ID = result[0][0]
                    # create a unique key as name for directories from the ID, for the case we need to hide the results
                    # do not just use the ID but also a random sequence
                    tgb = str(ID) + 'flo' + join(random.sample('0123456789abcdefghijklmnopqrstuvwxyz0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789', 6), '') #feel free to subsitute your own name here ;)
                    cryptID = md5.new(tgb.encode('utf-8')).hexdigest()
                    return_vals = (cryptID, "new")
                    sql = 'UPDATE backrub SET cryptID="%s" WHERE ID="%s"' % (cryptID, ID)
                    result = DBConnection.execQuery(sql)
                    # success
                    
                    hash_key = DBConnection.generateHash(ID)
            
                    # now find if there's a key like that already:
                    sql = '''SELECT ID, cryptID, PDBComplexFile FROM backrub WHERE backrub.hashkey="%s" AND (Status="2" OR Status="5") AND ID!="%s"''' % (hash_key, ID)
                    result = DBConnection.execQuery(sql)
                    # print sql, result
                    for r in result:
                        if str(r[0]) != str(ID): # if there is a OTHER FINISHED simulation with the same hash
                            shutil.copytree(os.path.join(ROSETTAWEB_download_dir, r[1]), os.path.join(ROSETTAWEB_download_dir, cryptID)) # copy the data to a new directory
                            sql = 'UPDATE backrub SET Status="2", StartDate=NOW(), EndDate=NOW(), PDBComplexFile="%s" WHERE ID="%s"' % (r[2], ID) # save the new/old filename and the simulation "end" time.
                            result = DBConnection.execQuery(sql)
                            return_vals = (cryptID, "old")
                            break
                    
                    # otherwise, see if there are already two similar jobs in the queue to avoid server spamming
                    sql = '''SELECT ID, cryptID, PDBComplexFile FROM backrub WHERE backrub.hashkey="%s" AND Status="0" AND ID!="%s"''' % (hash_key, ID)
                    results = DBConnection.execQuery(sql)
                    if results and len(results) > 0:
                        job = results[0]
                        #similarJobs = []
                        #for job in results:
                        #    similarJobs.append(job[0])
                        #join(map(str,similarJobs),", ")
                        errors.append('''There is already a job (<a href="%s?query=jobinfo&jobnumber=%s" target="_blank">#%s</a>) in the active queue with the same parameters. Please wait until it is finished to see the results.''' % (ROSETTAWEB_server_script, job[1], job[0]))
                        sql = """DELETE FROM backrub WHERE ID="%s" """ % ID
                        result = DBConnection.execQuery(sql)
                        return False
                     
                        
                except _mysql_exceptions.OperationalError, e:
                    html = '<H1 class="title">New Job not submitted</H1>'
                    if e[0] == 1153:
                        html += """<P>We are sorry but the size of the PDB file exceeds the upload limit. 
                        Please revise your file and delete unneccessary entries (e.g. copies of chains, MODELS, etc.).</P>
                        <P><A href="rosettaweb.py?query=submit">Submit</A> a new job.</P>"""
                    else:
                        html += """<P>An error occurred. Please revise your data and <A href="rosettaweb.py?query=submit">submit</A> a new job. If you keep getting error messages please contact <img src="../images/support_email.png" style="vertical-align:text-bottom;" height="15">.</P>"""
                    errors.append("Database error.")
                    return_vals = False
            
                # unlock tables
                sql = "UNLOCK TABLES"
                DBConnection.execQuery(sql)
                
                return return_vals
          
        else:
            form['error_msg'] = 'wrong mode for submit()'
            return False
    except Exception, e:
        excinfo = sys.exc_info()
        estring = traceback.format_exc()
        # todo: Maybe just log this to file and give the user less information
        errors.append("An exception occurred: %s." % estring)
        return False
    
    return (True, cryptID, "new")
                    

########################################## end of submit() ####################################

# def submit_point_mutation(); 
#     '''This function checks for the parameters from the form and writes them to the according database'''
#     # PointMutation
#     if form.has_key("PM_chain") and form["PM_chain"].value != '':
#       PM_chain = form["PM_chain"].value
#       if PM_chain = ######## I WAS WORKING HERE!!!!!!! ###################
#     else:
#       return False
# 
#     if form.has_key("PM_resid") and form["PM_resid"].value != '':
#       PM_resid = form["PM_resid"].value
#     
#     if form.has_key("PM_newres") and form["PM_newres"].value != '':
#       PM_newres = form["PM_newres"].value
#         
#     if form.has_key("PM_radius") and form["PM_radius"].value != '':
#       PM_radius = form["PM_radius"].value

    



###############################################################################################
# queue()                                                                                     #
# this function shows active, pending and finished jobs                                       #
###############################################################################################


def queue(form, userid):
  
  output = StringIO()
  output.write('<TD align="center">')
  
  thisserver = ROSETTAWEB_server_name.split('.')[0]
  
  sql = "SELECT ID, cryptID, Status, UserID, Date, Notes, Mini, EnsembleSize, Errors, task FROM backrub WHERE BackrubServer='%s' AND Expired=0 ORDER BY backrub.ID DESC" % thisserver
  result1 = DBConnection.execQuery(sql)
  print("yiyi")
  if thisserver == 'albana':
      print("yoyo")
      KlabDBConnection = rosettadb.RosettaDB("kortemmelab.ucsf.edu", ROSETTAWEB_db_db, ROSETTAWEB_db_user, ROSETTAWEB_db_passwd, ROSETTAWEB_db_port, ROSETTAWEB_db_socket, ROSETTAWEB_store_time)       
      sql = "SELECT ID, cryptID, Status, UserID, Date, Notes, Mini, EnsembleSize, Errors, task FROM backrub WHERE BackrubServer='%s' ORDER BY backrub.ID DESC" % thisserver #todo add Expired when klab db updated
      kresult = KlabDBConnection.execQuery(sql)
      KlabDBConnection.close()
      kresult.extend(result1)
      result1 = kresult
  
  # get user id of logged in user
  # sql = 'SELECT UserID FROM Sessions WHERE SessionID="%s"' % SID
  #   userID1 = DBConnection.execQuery(sql)[0][0]
  
  results = []
  for line in result1:
    new_lst = []
    sql = "SELECT UserName FROM Users WHERE ID=%s" % line[3]
    result2 = DBConnection.execQuery(sql)
    new_lst.extend(line)
    if int(line[3]) == int(userid):
        new_lst[3] = '<b><font color="green">' + result2[0][0] + '</font></b>'
    else:
        new_lst[3] = result2[0][0]
    results.append(new_lst)
    
  return results

########################################## end of queue() ####################################

###############################################################################################
# deletejob()                                                                                 #
# this function deletes a queued job from the database                                        #
###############################################################################################

def deletejob(form, SID):
  html = '<TD align="center">'
  
  # get logged in user
  sql = 'SELECT UserID FROM Sessions WHERE SessionID="%s"' % SID
  userID1 = DBConnection.execQuery(sql)[0][0]  
    
  if form.has_key("jobID"): # check if there is in fact a jobID
    # get user id for this job
    sql = 'SELECT UserID,Status FROM backrub WHERE ID="%s"' % (form["jobID"].value)
    userID2 = DBConnection.execQuery(sql)
    
    # job does no longer exist
    if len(userID2) == 0:
      html += "Job %s not found. <br><br>" % (form["jobID"].value)
    elif userID2[0][1] == 1:
      html += "Unable to delete job %s. Already running! <br><br>" % (form["jobID"].value)
    elif userID2[0][1] == 2:
      html += "Job %s is done. It will automatically be deleted after 10 days.<br><br>" % (form["jobID"].value)
    # see whether logged in user and job owner are the same, if not, log the cheater out!
    elif userID1 != userID2[0][0]:
      html += 'You are not allowed to delete this job! <br><font color="red"> Logout forced.</font><br><br>'
      logout(form, None, SID=SID)
      return html
    else:
      # delete the job from database only if it's still not running
      if form.has_key("button") and form["button"].value == "Delete":
        sql = 'DELETE FROM backrub WHERE ID="%s" AND UserID="%s" AND Status=0' % (form["jobID"].value, userID1)
        result = DBConnection.execQuery(sql)
        html += 'Job %s deleted. <br> <br> \n' % (form["jobID"].value)
      else:
        html += "Invalid. <br><br>"
  else:
    html += "No Job given. <br><br>"
  html += 'Proceed to <A href="rosettaweb.py?query=submit">Simulation Form</A>  or \n<A href="rosettaweb.py?query=queue">Queue</A> . <br><br> \n'
    
  return html
  
####################################### end of deletejob() ####################################

###############################################################################################
# jobinfo()                                                                                   #
# this function shows information about active, pending and finished jobs                     #
###############################################################################################

def jobinfo(form, SID):
    if form.has_key("jobnumber"):
        cryptID = form["jobnumber"].value
        
        parameter = DBConnection.getData4cryptID('backrub', cryptID)
        # for x,y in parameter.iteritems():
        #   print x, y, '<br>'
        if len(parameter) > 0:
            return (True, parameter)
    
    return (False, None)

########################################## end of jobinfo() ###################################

def checkResidues(pdb_object, chainsreslists):
    success  = True
    
    # Check the list of residues for matches within the pdb structure
    all_chains = pdb_object.chain_ids()
    all_resids = pdb_object.aa_resids()
    resid2type = pdb_object.aa_resid2type()
    
    for (chain, lst_resid, cysteinAllowed) in chainsreslists:
        if chain in all_chains:
            for res_no in lst_resid:
                resid = "%s%4.i" % (chain, int(res_no))
                if not resid in all_resids:
                    success = False
                    errors.append("Residue not found: %s.<br>Valid residues (displaying at most 1000) are:" % resid)
                    rnumber = 0
                    validres = ""
                    for r in all_resids:
                        validres += "%s, " % str(r)
                        rnumber += 1
                        if rnumber > 1000:
                            break;
                    errors.append(validres)
                elif resid2type[resid] == "C" and not cysteinAllowed:
                    success = False
                    errors.append("Mutation/design of Cysteine (CYS, C) is not permitted.")
        else:
            success = False
            errors.append("Chain '%s' not found." % chain)
    
    return success

###############################################################################################
# Protocol-specific functions - database storage                                                                                           #
###############################################################################################

def storePointMutation(form, pdb_object):                          
    """
     The submission logic for the single point mutations protocol.
     If submission fails then return None.
     Otherwise, returns a dictionary of parameters with the following fields:
        Mutations    List[(string, int, string, float)]
                     A list (of one element) containing a tuple with the fields chain, residue id, new residue, and radius
                     We use a list to allow similar logic to the Multiple Point Mutations protocol.
    """
    key = "PM_chain"
    if form.has_key(key) and form[key].value != '':
        chain = form[key].value
        key = "PM_resid"
        if form.has_key(key) and form[key].value != '':
            resid = form[key].value
            key = "PM_newres"
            if form.has_key(key) and form[key].value != '':
                newres = form[key].value
                key = "PM_radius"
                if form.has_key(key) and form[key].value != '':
                    radius = form[key].value
                    
                    chainsreslists = [(chain, [resid], False)] # Mutation of Cysteine is not permitted
                    if checkResidues(pdb_object, chainsreslists):                       
                        return {"Mutations" : [(chain, int(resid), newres, float(radius))]}
    return None
                
def storeMultiplePointMutations(form, pdb_object):                          
    """
     The submission logic for the multiple point mutations protocol.
     If submission fails then return None.
     Otherwise, returns a dictionary of parameters with the following fields:
        Mutations    List[(string, int, string, float)]    
                     A list of tuples containing the fields chain, residue id, new residue, and radius
    """
    Mutations = []
    chainsreslists = []
    chainres = {}
    for x in range(ROSETTAWEB_max_point_mutation):
        key = "PM_chain%d" % x
        if form.has_key(key) and form[key].value != '':
            chain = form[key].value
            key = "PM_resid%d" % x
            if form.has_key(key) and form[key].value != '':
                resid = form[key].value
                chainres[chain] = chainres.get(chain) or []
                chainres[chain].append(resid)
                key = "PM_newres%d" % x
                if form.has_key(key) and form[key].value != '':
                    newres = form[key].value
                    key = "PM_radius%d" % x
                    if form.has_key(key) and form[key].value != '':
                        radius = form[key].value
                        Mutations.append((chain, int(resid), newres, float(radius)))
        
    # Build up the chain/residues lists then check for matches within the pdb structure
    if Mutations:
        for p, residues in chainres:
            chainsreslists.append((p, residues, False))        
        if checkResidues(pdb_object, chainsreslists):    
            return {"Mutations" : Mutations.sort()} # sort the tuples
    return None

def storeEnsemble(form, pdb_object):
    return {"dummy" : 0}
    
def storeEnsembleDesign(form, pdb_object):
    """
     The submission logic for the ensemble design protocol.
     If submission fails then return None.
     Otherwise, returns a dictionary of parameters with the following fields:
        Temperature            Float      The temperature in kT
        NumDesignsPerStruct    Int        The number of designed sequences per ensemble structure
        SegmentLength          Int        Length of the segment to which backrub is applied
    """
    ProtocolParameters = None
    if form.has_key("ENS_temperature") and form["ENS_temperature"].value != '':
        if form.has_key("ENS_num_designs_per_struct") and form["ENS_num_designs_per_struct"].value != '':
            if form.has_key("ENS_segment_length") and form["ENS_segment_length"].value != '':
                ProtocolParameters = {
                    "Temperature"           :   float(form["ENS_temperature"].value),
                    "NumDesignsPerStruct"   :   int(form["ENS_num_designs_per_struct"].value),
                    "SegmentLength"         :   int(form["ENS_segment_length"].value),
                }
    return ProtocolParameters

def storeSequenceToleranceHK(form, pdb_object):
    """
     The submission logic for the first sequence tolerance protocol.
     If submission fails then return None.
     Otherwise, returns a dictionary of parameters with the following fields:
        Partners     List[Char]                 A list of chain names
        Designed     Partners -> [Int]          A mapping from chain names to a list of designed residues
        Weights      List[Float]                A list of weights in the order Other, kP0P0, kP1P1, kP0P1
    """
    if not (form.has_key("seqtol_chain1") and form["seqtol_chain1"].value != '') or not(form.has_key("seqtol_chain2") and form["seqtol_chain2"].value != ''):
        errors.append("Two chains must be entered.")
        return None                        
                    
    Designed = {}
    chain1 = str(form["seqtol_chain1"].value)
    chain2 = str(form["seqtol_chain2"].value)
    Designed[chain1] = []
    Designed[chain2] = []
                      
    for x in range(ROSETTAWEB_max_seqtol_design):
        key1 = "seqtol_mut_c_" + str(x)
        key2 = "seqtol_mut_r_" + str(x)
        if form.has_key(key1) and form.has_key(key2):
            chain = form[key1].value
            resid = form[key2].value
            if chain != '' and resid != '':
                if chain == chain1 or chain == chain2:
                    Designed[chain].append(int(resid))
                else:
                    errors.append("Chain not found.")
                    return None
        else:
            break

    if not Designed[chain1] and not Designed[chain2]:
        errors.append("There must be at least one designed residue.")
        return None

    chainsreslists = []
    chainsreslists.append((chain1, Designed[chain1], False))
    chainsreslists.append((chain2, Designed[chain2], False))
    if not checkResidues(pdb_object, chainsreslists):
        return None
    
    ProtocolParameters = {
        "Partners"      :   [chain1, chain2],
        "Designed"      :   Designed,
        "Weights"       :   [1.0, 1.0, 2.0],
    }
    return ProtocolParameters
        
def storeSequenceToleranceSK(form, pdb_object):
    """
     The submission logic for the second sequence tolerance protocol.
     If submission fails then return None.
     Otherwise, returns a dictionary of parameters with the following fields:
        Partners     List[Char]                 A list of chain names
        Premutated   Partners -> Int -> Char    A mapping from chain names to a mapping from residue positions to amino acids codes (the single letter codes used in resfiles) 
        Designed:    Partners -> Int -> {True}  A mapping from chain names to a mapping from designed residues to True
        Weights      List[Float]                A list of weights in the order Other, kP0P0, .., kPnPn, kP0P1, .. kP0Pn, kP1P2, .., kP1Pn, .. , kPn-1Pn. This order matches the seqtol protocol documentation
        kT           Float
     where n+1 is the number of selected chains.
    """
    success = True
    
    Partners = {}       # For convenience with the weights remapping, Partners is initially a mapping from names to their entered order on the form
    Premutated = {}
    Designed = {}
    Weights = []    
            
    # Store the Partner identifiers
    # Only read up to the number of chains selected by the user
    numChainsToRead = int(form["numPartners"].value)
    numPartners = 0                
    for i in range(0, numChainsToRead):
        mkey = "seqtol_SK_chain%d" % i
        if form.has_key(mkey):
            formvalue = form[mkey].value
            #todo: one of these checks may not be needed
            if formvalue != '' and formvalue != 'ignore':
                # Sanity check: Ensure partners are distinct chains
                if Partners.get(formvalue) != None:
                    success = False
                    errors.append("Partner %s was chosen multiple times." % formvalue)
                Partners[formvalue] = i
                Premutated[formvalue] = {}
                Designed[formvalue] = {}
                numPartners = numPartners + 1
    
    if len(Partners) != numChainsToRead:
        errors.append("Please check that all chains were filled in.")
        return None        
        
    # If the user specified the chains in a different order from the PDB, we will need to correct this
    # all_chains is ordered by appearance in the PDB    
    all_chains = pdb_object.chain_ids()
    weightRemap = []
    for i in range(0, len(all_chains)):
        if all_chains[i] in Partners:
            weightRemap.append(Partners[all_chains[i]])
        
    # Store the Score Reweighting values, using the mapping above to fix the order. We assume the JS has done its job properly. 
    try: 
        # We order the weights to match the command-line input format e.g. Other A B A-B, or A B C A-B A-C B-C, etc.                
        
        # Add the Other energy
        # todo: Check this value w/Colin or mention in tooltips
        Weights.append("0.4") 
            
        # Add the self-energies
        for i in range(0, numChainsToRead):
            uI = weightRemap[i]
            mkey = "seqtol_SK_kP%dP%d" % (uI, uI)
            if not(form.has_key(mkey)) or form[mkey].value == '':
                success = False
                errors.append("Partner %d was specified but its interaction energy k<sub>P<sub>%d</sub>P<sub>%d</sub></sub> was missing." % (x, x, x))
            else:
                Weights.append(float(form[mkey].value))
                            
        # Add the interaction energies
        for i in range(0, numChainsToRead):
            uI = weightRemap[i]
            for j in range(i + 1, numChainsToRead):
                uJ = weightRemap[j]
                x = min(uI, uJ)
                y = max(uI, uJ)
                # Check that the interaction energy is filled in
                mkey = "seqtol_SK_kP%dP%d" % (x, y)
                if not(form.has_key(mkey)) or form[mkey].value == '':
                    success = False
                    errors.append("Partners %d and %d were specified but their interaction energy k<sub>P<sub>%d</sub>P<sub>%d</sub></sub> was missing." % (x, y, x, y))
                    # else we could assign the default value of 1.0 here
                else:
                    # Store kPiPj where the partners are ordered as in the PDB 
                    Weights.append(float(form[mkey].value))
    except:
        errors.append("An error occurred reordering the weights matrix to match the PDB file.")
        return None
        
    # Store the residues
    scs, numDesignedResidues = storeSequenceToleranceSKResidues(form, Partners, Designed, ROSETTAWEB_SK_MaxMutations, "designed", "seqtol_SK_mut_c_", "seqtol_SK_mut_r_", None)
    success = success and scs
    scs, numPremutations = storeSequenceToleranceSKResidues(form, Partners, Premutated, ROSETTAWEB_SK_MaxPremutations, "premutated", "seqtol_SK_pre_mut_c_", "seqtol_SK_pre_mut_r_", "premutatedAA")
    success = success and scs
    if numDesignedResidues < 1:
        success = False
        errors.append("There must be at least one designed residue.")                               
    
    #todo: check in JS whether numeric values are actually numeric 
                               
    # Store the Boltzmann Factor
    kT = None
    if not(form.getvalue("customBoltzmann")) and form.has_key("seqtol_SK_Boltzmann") and form["seqtol_SK_Boltzmann"].value != '':
        userkT = str(form["seqtol_SK_Boltzmann"].value)
        try:
            kT = float(userkT)
        except ValueError:
            success = False
            errors.append("The Boltzmann factor was specified as '%s' which could not be read as a numeric value." % userkT)
        else:
            warnings.append("Using a user-defined value for kT (%s) rather than the published value." % userkT)
    else:
        kT = ROSETTAWEB_SK_InitialBoltzmann + numPremutations * ROSETTAWEB_SK_BoltzmannIncrease
        warnings.append("Running the job with the published value for kT = %f + %d * %f = %f." % (ROSETTAWEB_SK_InitialBoltzmann, numPremutations, ROSETTAWEB_SK_BoltzmannIncrease, kT))    
    
    parameters = {
            "Partners"      :   Partners.keys(),
            "Premutated"    :   Premutated,
            "Designed"      :   Designed,
            "Weights"       :   Weights,
            "kT"            :   kT,
        }
    
    if success and SequenceToleranceSKChecks(parameters, pdb_object):
        return parameters
    else:
        return None

def storeSequenceToleranceSKResidues(form, Partners, Residues, maxNumResidues, restype, chainprefix, idprefix, aaprefix):
    success = True
    numResidues = 0
    lastRes = maxNumResidues
    for x in range(maxNumResidues):
        lastRes = x
        sx = str(x)
        key1 = chainprefix + sx
        key2 = idprefix + sx
        key3 = (not aaprefix) or (aaprefix + sx)
        if form.has_key(key1) and form[key1].value != '' and form.has_key(key2) and form[key2].value != '' and ((not aaprefix) or (len(form[key3].value) == 3)):
            numResidues = numResidues + 1
            p = form[key1].value
            residueID = int(form[key2].value)
            AAid = (not aaprefix) or (ROSETTAWEB_SK_AA[form[key3].value])
            if Partners.get(p) != None: # This is important as Python treats numeric zero as False
                if Residues[p].get(residueID):
                    success = False
                    errors.append("There are multiple %s residues at position %s in chain %s." % (restype, residueID, p))                                
                else:
                    Residues[p][residueID] = AAid
            else:
                success = False
                errors.append("The chain %s was not found for %s residue %i ('%s%4.i')." % (p, restype, x + 1, p, int(residueID)))
        else:
            break
    
    # Warn if the user left gaps in the residue list
    for x in range(lastRes + 1, maxNumResidues):
        key1 = chainprefix + str(x)
        key2 = idprefix + str(x)
        if form.has_key(key1) and form[key1].value != '' and form.has_key(key2) and form[key2].value != '':
            warnings.append("The %s residue %d ('%s%4.i') was not added to the run as previous residues were left blank." % (restype, x + 1, form[key1].value, int(form[key2].value)))

    return success, numResidues

def SequenceToleranceSKChecks(params, pdb_object):
    # Sanity checks:
    
    # Check if chain/residue pairs exist in the structure
    # Build up the chain/residues lists then check for matches within the pdb structure
    chainsreslists = []
    for p in params["Partners"]:
        chainsreslists.append((p, params["Designed"][p].keys(), False))
        chainsreslists.append((p, params["Premutated"][p].keys(), True))
    success = checkResidues(pdb_object, chainsreslists)

    # Test to see if the seqtol resfile would be empty before proceeding 
    # todo: Tidy this logic up with rosettaseqtol.py        
    all_resids = pdb_object.aa_resids() # todo: Calling this twice (in checkResidues as well)
    resfileHasContents, contents = make_seqtol_resfile(pdb_object, params, ROSETTAWEB_SK_Radius, all_resids)
    
    if not resfileHasContents:
        success = False
        errors.append(contents)                     
    
    return success

class FrontendProtocols(WebserverProtocols):
      
    def __init__(self, rosettaDD, rosettaHTML):
        super(FrontendProtocols, self).__init__()
        
        # Add frontend specific information
        refIDs = rosettaHTML.refs.getReferences()
        protocolGroups = self.protocolGroups
        protocols = self.protocols
        
        for pgroup in protocolGroups:
            if pgroup.name == "Point Mutation":
                pgroup.setDescription('''
                This function utilizes the backrub protocol implemented in Rosetta and applies it to the neighborhood of a mutated amino acid residue to model conformational changes in this region.
                There are two options.
                <dl style="text-align:left;">
                    <dt><b>One Mutation</b></dt><dd>
                        A single amino acid residue will be substituted and the neighboring residues within a radius of 6&#197; of the mutated residues 
                        will be allowed to change their side-chain conformations (\"repacked\"). 
                        The method, choice of parameters and benchmarking are described in [<a href="#refSmithKortemme:2008">%(SmithKortemme:2008)d</a>].</dd><br>
                    <dt><b>Multiple Mutations</b></dt><dd>Up to 30 residues can be mutated and their neighborhoods repacked.
                                                          The modeling protocol is as described above for single mutations (but has not been benchmarked yet).</dd>
                    <!-- dt>Upload List</dt><dd>Upload a list with single residue mutations.</dd -->
                </dl>''' % refIDs)
            elif pgroup.name == "Backrub Ensembles":
                pgroup.setDescription('''
                This function utilizes backrub and design protocols implemented in Rosetta. 
                There are two options.
                <dl style="text-align:left;">
                    <dt><b>Backrub Conformational Ensemble</b></dt>
                        <dd>Backrub is applied to the entire input structure to generate a flexible backbone ensemble of modeled protein conformations. 
                        Near-native ensembles made using this method have been shown to be consistent with measures of protein dynamics by 
                        Residual Dipolar Coupling measurements on Ubiquitin [<a href="#refSmithKortemme:2008">%(SmithKortemme:2008)d</a>].</dd><br>
                    <dt><b>Backrub Ensemble Design</b></dt>
                      <dd>This method first creates an ensemble of structures to model protein flexibility. 
                          In a second step, the generated protein structures are used to predict an ensemble of low-energy sequences consistent with the input structures, 
                          using computational design implemented in Rosetta. The output is a sequence profile of this family of structures. 
                          For ubiquitin, the predicted conformational and sequence ensembles resemble those of the natural occurring protein family [<a href="#refFriedlandEtAl:2009">%(FriedlandEtAl:2009)d</a>].</dd>
                </dl>''' % refIDs)
            elif pgroup.name == "Sequence Tolerance":
                pgroup.setDescription('''
                
                This function utilizes backrub and design protocols in Rosetta. 

                There are two implementations:
                <dl style="text-align:left;">
                    <dt><b>Generalized RosettaBackrub sequence tolerance method</b> [<a href="#refSmithKortemme:2010">%(SmithKortemme:2010)d</a>]</dt>
                        <dd>Predicts tolerated sequences for proteins or protein-protein interfaces.  This is the most recent protocol based on Rosetta 3.0.</dd><br>
                    <dt><b>Interface sequence plasticity method</b> [<a href="#refHumphrisKortemme:2008">%(HumphrisKortemme:2008)d</a>]
                         <dd>Predicts tolerated sequence space for up to 10 positions in protein-protein interfaces.  This method is based on Rosetta 2.0.</dd>
                </dl>

                Both implementations first apply the RosettaBackrub method to generate a conformational ensemble, design sequences consistent with the members in the ensemble, and then combine the sequences to build a predicted profile.

                <!--This function utilizes backrub and design protocols implemented in Rosetta.
                There are two options.
                <dl style="text-align:left;">
                    <dt><b>Interface Sequence Tolerance</b></dt>
                        <dd>First, the backrub algorithm is applied to the uploaded protein-protein complex to generate a flexible backbone conformational ensemble of the entire complex. 
                        Then, for each of the resulting structure, residue positions given by the user (up to 10) are subjected to protein design, using a genetic algorithm implemented in Rosetta. 
                        All generated sequences are ranked by their Rosetta force field score. 
                        Sequences with favorable scores both for the total protein complex and the interaction interface are used to build a sequence profile, as described and benchmarked in [<a href="#refHumphrisKortemme:2008">%(HumphrisKortemme:2008)d</a>].</dd>
                    <dt><b>Interface / Fold Sequence Tolerance</b></dt>
                        <dd> Insert text.[<a href="#refSmithKortemme:2010">%(SmithKortemme:2010)d</a>]</dd>
                </dl>-->''' % refIDs) 
            else:
                raise

        for p in protocols:
            if p.dbname == "point_mutation":
                p.setSubmitFunction(rosettaHTML.submitformPointMutation)
                p.setShowResultsFunction(rosettaHTML.resultsPointMutation)
                p.setStoreFunction(storePointMutation)
                p.setDataDirFunction(rosettaDD.PointMutation)
                p.setReferences("SmithKortemme:2008")
            elif p.dbname == "multiple_mutation":
                p.setSubmitFunction(rosettaHTML.submitformMultiplePointMutations)
                p.setShowResultsFunction(rosettaHTML.resultsMultiplePointMutations)
                p.setStoreFunction(storeMultiplePointMutations)
                p.setDataDirFunction(rosettaDD.MultiplePointMutations)
                p.setReferences("SmithKortemme:2008")
            elif p.dbname == "no_mutation":
                p.setSubmitFunction(rosettaHTML.submitformEnsemble)
                p.setShowResultsFunction(rosettaHTML.showEnsemble)    
                p.setStoreFunction(storeEnsemble)
                p.setDataDirFunction(rosettaDD.Ensemble)
                p.setReferences("SmithKortemme:2008")
            elif p.dbname == "ensemble":
                p.setSubmitFunction(rosettaHTML.submitformEnsembleDesign)
                p.setShowResultsFunction(rosettaHTML.showEnsembleDesign)
                p.setStoreFunction(storeEnsembleDesign)
                p.setDataDirFunction(rosettaDD.EnsembleDesign)
                p.setReferences("FriedlandEtAl:2009")
            elif p.dbname == "sequence_tolerance":
                p.setSubmitFunction(rosettaHTML.submitformSequenceToleranceHK)
                p.setShowResultsFunction(rosettaHTML.showSequenceToleranceHK)
                p.setStoreFunction(storeSequenceToleranceHK)
                p.setDataDirFunction(rosettaDD.SequenceTolerance)
                p.setReferences("HumphrisKortemme:2008")
            elif p.dbname == "sequence_tolerance_SK":
                p.setSubmitFunction(rosettaHTML.submitformSequenceToleranceSK)
                p.setShowResultsFunction(rosettaHTML.showSequenceToleranceSK)
                p.setStoreFunction(storeSequenceToleranceSK)
                p.setDataDirFunction(rosettaDD.SequenceTolerance)
                p.setReferences("SmithKortemme:2010")  # todo: "SmithKortemme:2011"
            else:
                raise 
        # Create references for the HTML generators    
        rosettaDD.protocolGroups = protocolGroups
        rosettaHTML.protocolGroups = protocolGroups
        rosettaDD.protocols = protocols
        rosettaHTML.protocols = protocols
        
# run Forest run!
try:
    ws()
except Exception, e:
    traceback.print_exc()
    print "An error occured. Please check your input and contact us if the problem persists."

