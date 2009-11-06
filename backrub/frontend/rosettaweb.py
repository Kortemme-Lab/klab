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
# execQuery()                            
# sendMail()
# print_countries()                            
# 
######################################## 

# import the basics
import sys, os
# Append document_root to sys.path to be able to find user modulesface
#sys.path.append(os.environ['DOCUMENT_ROOT'])

import sha, time
import cgi
import cgitb; cgitb.enable()
import Cookie
# set Python egg dir MscOSX only
if os.uname()[0] == 'Darwin':
  os.environ['PYTHON_EGG_CACHE'] = '/Applications/XAMPP/xamppfiles/tmp'
import MySQLdb  
import _mysql_exceptions
import socket
import md5

import session
from rosettahtml import RosettaHTML
import rosettadb
from rwebhelper import *

from datetime import datetime
from string import *
from cStringIO import StringIO
from cgi import escape

###############################################################################################
# Setup: Change these values according to your settings and usage of the server               #
###############################################################################################

parameter = read_config_file('/etc/rosettaweb/parameter.conf')

ROSETTAWEB_db_host   = parameter['db_host']
ROSETTAWEB_db_db     = parameter['db_name']
ROSETTAWEB_db_user   = parameter['db_user']
ROSETTAWEB_db_passwd = parameter['db_pw']
ROSETTAWEB_db_port   = int(parameter['db_port'])
ROSETTAWEB_db_socket = parameter['db_socket']

ROSETTAWEB_server_title  = parameter['server_title']
ROSETTAWEB_contact_name  = parameter['name_contact']
ROSETTAWEB_contact_email = parameter['email_contact']
ROSETTAWEB_admin_email   = parameter['email_admin']

ROSETTAWEB_server_name   = parameter['server_name']
ROSETTAWEB_server_script = os.environ['SCRIPT_NAME']

ROSETTAWEB_store_time         = parameter['store_time']
ROSETTAWEB_max_point_mutation = 31
ROSETTAWEB_cookie_expiration  = 60*60

ROSETTAWEB_bin_sendmail = parameter['bin_sendmail']
ROSETTAWEB_download_dir = parameter['rosetta_dl']

# open connection to MySQL
connection = MySQLdb.Connection( host=ROSETTAWEB_db_host, db=ROSETTAWEB_db_db, user=ROSETTAWEB_db_user, passwd=ROSETTAWEB_db_passwd, port=ROSETTAWEB_db_port, unix_socket=ROSETTAWEB_db_socket )
########################################## Setup End ##########################################



###############################################################################################
# ws()                                                                                        #
# This is the main function call. It parses the CGI arguments and generates web pages.        #
# It takes no formal arugments, but parses the following CGI form fields:                     #
#  query  [ register | login | logout | index | terms_of_service | submit | queue | update ]  #
###############################################################################################

def ws():
  
  s = sys.stdout
  sys.stderr = s # should be removed later

  debug = ''

  html_content = ''
  query_type   = 'dftba'
  SID          = ''
  username     = ''
  title        = ''

  comment = 'TEST MODE: Data might not be processed correctely.'
  warning = ''
  
  # get the POST data from the webserver
  form = cgi.FieldStorage()

  # SECURITY CHECK - escape HTML code
  for key in form:
    form[key].value = escape(form[key].value)
    if (key == "Password" or key == "ConfirmPassword" or key == "myPassword" or key == "password" or key == "confirmpassword"):
      tgb = str(form[key].value)
      form[key].value = md5.new(tgb.encode('utf-8')).hexdigest()

  ####################################### 
  # cookie check 
  ####################################### 
  
  # create session object
  my_session = session.Session(expires=ROSETTAWEB_cookie_expiration, cookie_path='/')
  # get time of last visit
  lastvisit = my_session.data.get('lastvisit')
  # set session ID
  SID = my_session.cookie['sid'].value
  # get present time as datetime object
  t = datetime.now()
  # set cookie to the present time with time() function
  my_session.data['lastvisit'] = repr(time.time())

  if lastvisit:  # lastvisit != 0 means that this cookie set to a time, hence the session should be known
    # get infos about session
    sql = "SELECT loggedin FROM Sessions WHERE SessionID = \"%s\"" % SID
    result = execQuery( connection, sql )
    # if this session is active (i.e. the user is logged in) allow all modes. If not restrict access or send him to login.
    if result[0][0] == 1 and form.has_key("query") and form['query'].value in ["register","login","loggedin","logout","index","jobinfo","terms_of_service","submit","submitted","queue", "update","doc","delete"]:
      query_type = form["query"].value
      
      sql = "SELECT u.UserName FROM Sessions s, Users u WHERE s.SessionID = \"%s\" AND u.ID=s.UserID" % SID
      result = execQuery(connection, sql)
      if result[0][0] != ():
        username = result[0][0]

    elif form.has_key("query") and form['query'].value in ["register","index","login","terms_of_service","oops","doc"]:
      query_type = form["query"].value
    else:
      query_type = "index"

  else: # new sessionID -> put it in DB and reload page with cookie
    # put actual time in the database
    lv_strftime = t.strftime("%Y-%m-%d %H:%M:%S")
    
    sql = "INSERT INTO Sessions (SessionID,Date,query,loggedin) VALUES (\"%s\",\"%s\",\"%s\",\"%s\") " % ( SID, lv_strftime, "login", "0" )
    result = execQuery( connection, sql )
    
    if form.has_key("query"):
      query_type = form["query"].value
    else:
      query_type = "index"
    
    # the next few lines create HTTP header which includes the cooki and MUST NOT be removed
    s.write(str(my_session.cookie)+'\n')  # DO NOT REMOVE OR COMMENT THIS LINE!!!
    s.write("Content-type: text/html\n")
    s.write("Location: http://%s/backrub/cgi-bin/%s?query=%s\n\n" % ( ROSETTAWEB_server_name, ROSETTAWEB_server_script, query_type ) ) # this line reloads the page, remember to CHANGE THIS URL
    # close session object
    my_session.close()
    return
  
  
  ###############################
  # HTML CODE GENERATION
  ###############################

  # send cookie info to webbrowser. DO NOT DELETE OR COMMENT THIS LINE!
  s.write(str(my_session.cookie)+'\n')
  s.write("Content-type: text/html\n\n\n")
  s.write(debug)
  my_session.close()
    
  ########## DEBUG Cookies ########## 
  #s.write(string_cookie+'\n<br><br>')
  #s.write('%s <br> sess.cookie = %s <br> sess.data = %s\n<br><br>' % (my_session.cookie, my_session.cookie, my_session.data))
  #s.write(str(my_session.cookie)+'\n<br><br>')
  ########## DEBUG Cookies ##########

  if not os.path.exists('/tmp/daemon-example.pid'):
    warning = 'Backend not running. Jobs will not be processed immediately.'

  rosettaHTML = RosettaHTML(ROSETTAWEB_server_name, 'Structure Prediction Backrub', ROSETTAWEB_server_script, ROSETTAWEB_download_dir, username=username, comment=comment, warning=warning, contact_email='kortemme@cgl.ucsf.edu' , contact_name='Tanja Kortemme')

  # session is now active, execute function
  if query_type == "index":
    html_content = rosettaHTML.index()
    title = 'Home'

  elif query_type == "login":
    login_return = login(form, my_session, t)
    if login_return == True:
      username = form["myUserName"].value
      html_content = rosettaHTML.loggedIn( username )
    elif login_return in ['no_password', 'wrong_password', 'wrong_username']:
      html_content = rosettaHTML.login( message='Wrong username or password. Please try again.' )
    elif login_return == 'logged_in':
      html_content = rosettaHTML.login( message='You\'re already logged in.', login_disabled=True )
    else:
      html_content = rosettaHTML.login() 
    title = 'Login'

  elif query_type  == "loggedin":
    html_content = rosettaHTML.loggedIn(username) 

  elif query_type   == "logout":
    if logout(form, my_session):
      html_content = rosettaHTML.logout( username )
    else:
      html_content = rosettaHTML.index()
    title = 'Logout'

  elif query_type   == "submitted":
    if submit(form, SID): # data was submitted and written to the database
      html_content = rosettaHTML.submited(jobname='')
      title = 'New Job submitted'
    else: # no data was submitted/there is an error
      html_content = "<br>Error<br><br>%s<br>" % form['error_msg']

  elif query_type  == "submit":
    html_content = rosettaHTML.submit(jobname='')
    title = 'Submission Form'

  elif query_type   == "queue":
    job_list = queue(form, SID)
    html_content = rosettaHTML.printQueue(job_list)
    title = 'Job Queue'

  elif query_type   == "jobinfo":
    parameter = jobinfo(form, SID)
    if parameter[0]:
        html_content = rosettaHTML.jobinfo(parameter[1])
    else:
        html_content = '<td align="center">No Data<br><br></td>'
    title = 'Job Info'

  elif query_type   == "register":
    register_result = register(form, SID)
    if register_result[0]:
        if register_result[1] == 'updated':
            html_content = rosettaHTML.updated()
        else:
            html_content = rosettaHTML.registered()
    else:
        html_content = rosettaHTML.register(error=register_result[1])
    title = 'Registration'

  elif query_type   == "update":
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

  elif query_type   == "terms_of_service":
    html_content = rosettaHTML.terms_of_service()
    title = 'Terms of Service'

  elif query_type   == "doc":
    html_content = rosettaHTML.help()
    title = 'Documentation'

  elif query_type   == "delete":
    html = deletejob(form, SID)
    title = 'Job Deleted'

  elif query_type   == "oops":
    password_result = send_password(form)
    if password_result[0]:
        html_content = rosettaHTML.passwordUpdated( password_result[1] )
    else:
        html_content = rosettaHTML.sendPassword( password_result[1] )
    title = 'Password'

  else:
    html = "this is impossible" # should never happen since we only allow states from list above 

  s.write( rosettaHTML.main(html_content, title) )

  s.close() 

########################################## end of ws() ########################################



###############################################################################################
# login()                                                                                     #
#   performs all necessary actions to log in a users                                          # 
###############################################################################################


def login(form, my_session, t):
  
  # get session info
  SID         = my_session.cookie['sid'].value
  lv_strftime = t.strftime("%Y-%m-%d %H:%M:%S")
    
  ## we first check if the user can login
  if form.has_key('login') and form['login'].value == "login" and form.has_key('myPassword'):
    # check for userID and password
    sql = 'SELECT ID,Password  FROM Users WHERE UserName = "%s"' % form["myUserName"].value
    result = execQuery(connection, sql)
    try:
      UserID = result[0][0]
      PW     = result[0][1]
      if form["myPassword"].value == PW: 
        # all clear ... go!
        sql = "UPDATE Sessions SET UserID = \"%s\", Date = \"%s\", loggedin = \"%s\" WHERE SessionID = \"%s\" " % ( UserID, lv_strftime, "1", SID)
        result = execQuery(connection, sql)
        return True # successfully logged in

      else:
        return 'wrong_password'
    except IndexError:
      return 'wrong_username'

#  elif not form.has_key('myPassword'):
#    return 'no_password' 

  else: # need form
    sql = "SELECT loggedin FROM Sessions WHERE SessionID = \"%s\"" % SID
    result = execQuery( connection, sql )
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
    sql = "UPDATE Sessions SET loggedin = \"%s\" WHERE SessionID = \"%s\" " % ( "0", SID)
    execQuery(connection, sql)

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
    result = execQuery(connection, sql)
    
    if len(result) < 1:
      password_updated = False
      message = 'Your email address is not in our database. Please <A href="rosettaweb.py?query=register">register</A>.<br><br> \n'
    else:
      password = join(random.sample('0123456789abcdefghijklmnopqrstuvwxyz0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789', 6),'')
      crypt_pw = md5.new(password.encode('utf-8')).hexdigest()
      
      sql = 'UPDATE Users SET Password="%s" WHERE ID=%s' % ( crypt_pw, result[0][0] )
      result_null = execQuery(connection, sql)
      
      text = """Dear %s,
    
Your username and a temporary Password are listed below. This email was 
generated upon request to send you a new password. Please login and change
your password.

If you DID NOT request to reset your password, please let us know.
mailto:lauck@cgl.ucsf.edu 
  
-----------------------
LOGIN NAME AND PASSWORD
-----------------------
              
LOGIN NAME:  %s
  PASSWORD:  %s
  
Have a nice day!

The Kortemme Lab Server Daemon

      """ % ( result[0][1], result[0][2], password )
        
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
    error        = ''
    
    sql = "SELECT * FROM Users WHERE UserName =\"%s\""  % form["username"].value
    sql_out = execQuery(connection, sql)
    if len(sql_out) >= 1:           # if we get something, name is already taken
      form["username"].value = ''   # reset
      process_data = False 
      error = 'Username is already in use.'
    
    sql = "SELECT * FROM Users WHERE Email = \"%s\""  % form["email"].value
    sql_out = execQuery(connection, sql)
    if len(sql_out) >= 1:
      form["email"].value = ''
      process_data = False
      error = 'Email address is already registered.'
    
    # check whether password is correct:
    if form["password"].value != form["confirmpassword"].value:
      process_data = False
      error = 'Passwords do not match.'    
    
    return (process_data, error)

def _updateUserInfo(form,SID):
    # transmit values to database
    # define allowed fields 
    value_list   = ["username", "firstname", "lastname", "institution", "email", "password"]
    value_list_o = ["address","city","zip","state","country"]  
    value_names  = {"username" : "UserName", "firstname" : "FirstName", "lastname" : "LastName", "email" : "Email", "institution" : "Institution", "address":"Address1", "city":"City", "state" : "State", "zip" : "Zip", "country" : "Country", "password" : "Password"}
    
    # check whether each parameter has a value and if so append it to the database string
    fields    = ""
    variables = ""
    # get userid from db
    sql = "SELECT UserID from Sessions WHERE SessionID = \"%s\" " % SID
    result = execQuery(connection, sql)
    userid = result[0][0]
    
    for value_name in value_list:
        if form.has_key(value_name):
            fields += value_names[value_name] + "=\"" + form[value_name].value + "\", "
    for value_name in value_list_o:
        if form.has_key(value_name):
            fields += value_names[value_name] + "=\"" + form[value_name].value + "\", "
    sql = "UPDATE Users SET %s WHERE ID=%s" % ( fields[:-2], userid )
    #print sql
    execQuery(connection, sql)


def register(form, SID):
  
  # define allowed fields 
  value_list   = ["username", "firstname", "lastname", "institution", "email", "password"]
  value_list_o = ["address","city","zip","state","country"]  
  value_names  = {"username" : "UserName", "firstname" : "FirstName", "lastname" : "LastName", "email" : "Email", "institution" : "Institution", "address":"Address1", "city":"City", "state" : "State", "zip" : "Zip", "country" : "Country", "password" : "Password"}
  process_data = True
  error        = ''
  form_db  = {}    # store values retrieved from Database
  
  if form.has_key("mode") and form["mode"].value == "check":
    process_data, error = _checkUserInfo(form)
  elif form.has_key("mode") and form["mode"].value == "update":
    _updateUserInfo(form, SID)
    return (True, 'updated')
  else:
    process_data = False
    
  if process_data:
    # transmit values to database
    # check whether each parameter has a value and if so append it to the database string
    fields    = ""
    variables = ""
    for value_name in value_list:
      if form.has_key(value_name):
        fields += value_names[value_name] + ","
        variables += "\"%s\"," % form[value_name].value
    for value_name in value_list_o:
      if form.has_key(value_name):
        fields += value_names[value_name] + ","
        variables += "\"%s\"," % form[value_name].value
      sql = "INSERT INTO Users (Date, %s) VALUES (NOW(), %s)" % ( fields[:-1], variables[:-1] )
    #print sql
    execQuery(connection, sql)

    # send a conformation email
    text = """Dear %s,

Thank you for creating an account at the %s. If you have questions or if you did not create an account please let us know: %s 

-----------------------
login:       %s
Name:        %s %s
Institution: %s

Have a nice day!

The Kortemme Lab Server Daemon
      
      """ % ( form["firstname"].value, ROSETTAWEB_server_title, ROSETTAWEB_admin_email, form["username"].value, form["firstname"].value, form["lastname"].value, form["institution"].value )
    
    sendMail(ROSETTAWEB_bin_sendmail, form["email"].value, ROSETTAWEB_admin_email, "[Kortemme Lab Server] New Account", text)
    
    text_to_admin = """Dear administrator,
    
A new user account for %s was created:

login:       %s
Name:        %s %s
Institution: %s          

Have a nice day!

The Kortemme Lab Server Daemon

    """ % ( ROSETTAWEB_server_title, form["username"].value, form["firstname"].value, form["lastname"].value, form["institution"].value )

    sendMail( ROSETTAWEB_bin_sendmail, ROSETTAWEB_admin_email, ROSETTAWEB_admin_email, "[Kortemme Lab Server] New Account created", text_to_admin)

  return (process_data, error)


################################### end register() ############################################

###############################################################################################
# update()                                                                                    #
#  here we have a little redundancy (register()) that might be removed sometime               #
#  for now this is better. due to the database call I have to make a different type of map    #
#  than the one used for "form". yes ... i dunno, works though! ;)                            #
###############################################################################################

def getUserData(form, SID):
  # define allowed fields 
  value_list   = ["username", "firstname", "lastname", "institution", "email", "password"]
  value_list_o = ["address","city","zip","state","country"]  
  value_names  = {"username" : "UserName", "firstname" : "FirstName", "lastname" : "LastName", "email" : "Email", "institution" : "Institution", "address":"Address1", "city":"City", "state" : "State", "zip" : "Zip", "country" : "Country", "password" : "Password"}
  process_data = True
  error        = ''  
  form_db = {}   # store values retrieved from Database
  
  # get userid from db
  sql = "SELECT UserID from Sessions WHERE SessionID = \"%s\"" % SID
  result = execQuery(connection, sql)
  # get all user data from DB
  UserID = result[0][0]
  sql = "SELECT * FROM Users WHERE ID = \"%s\""  % UserID
  sql_out = execQuery(connection, sql)
  
  # create a dict with that information
 
  if len(sql_out) >= 1 :
    form_db["username"]      = sql_out[0][1]
    form_db["lastname"]      = sql_out[0][2]
    form_db["firstname"]     = sql_out[0][3]
    form_db["email"]         = sql_out[0][4]
    form_db["institution"]   = sql_out[0][5]
    form_db["address"]       = sql_out[0][6]
    #form_db["Address2"]      = sql_out[0][7]
    form_db["city"]          = sql_out[0][8]
    form_db["state"]         = sql_out[0][9]
    form_db["zip"]           = sql_out[0][10]
    form_db["country"]       = sql_out[0][11]
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


###############################################################################################
# submit()                                                                                    #
# this function processes the parameter of the input form and adds a new job to the database  # 
###############################################################################################

def submit(form, SID):
  ''' This function processes the general parameters and calls the specific functions for the individual applications'''
  s = StringIO()
  
  # get information from the database
  sql      = 'SELECT UserID FROM Sessions WHERE SessionID = "%s"' % SID
  result   = execQuery(connection, sql)
  UserID   = result[0][0]
  sql      = 'SELECT UserName, Email FROM Users WHERE ID = "%s"'  % UserID
  sql_out  = execQuery(connection, sql)
  UserName = sql_out[0][0]
  Email    = sql_out[0][1]
  JobName  = ""
  Partner  = ""
  error    = ""  # is used to check if something went wrong

  # 2 modes: check and show form
  if form.has_key("mode") and form["mode"].value == "check":
  
    # check whether all arguments were entered is done by javascript
    # if that is not the case, something went wrong and we'll get a python exception here
    # so here we could add error handling if it would be necessary
    if form.has_key("JobName"):
      JobName = escape(form["JobName"].value)
    
    if form.has_key("PDBComplex"):
      pdbfile = form["PDBComplex"]
      if not pdbfile.file:
         error += " PDB data is not a file. "
      pdb_filename = form["PDBComplex"].filename
      if pdb_filename[-4:] not in ['.pdb','.PDB' ]:
        pdb_filename = pdb_filename + '.pdb'
        
        
    if form.has_key("Mutations"):
      mutationsfile = form["Mutations"]
      mutations_data = str(mutationsfile.value)
      if not mutationsfile.file:
         error += " Mutations list data is not a file. "
    else:
      mutations_data = ""
    
    # tasks are: no_mutation, point_mutation, multiple_mutation, upload_mutation, ensemble
    if form.has_key('task') and form['task'].value != '':
      if form['task'].value == 'parameter1_1':
        modus = 'point_mutation'
      elif form['task'].value == 'parameter1_2':
        modus = 'multiple_mutation'
      elif form['task'].value == 'parameter1_3':
        modus = 'upload_mutation'
      elif form['task'].value == 'parameter2_1':
        modus = 'no_mutation'
      elif form['task'].value == 'parameter2_2':
        modus = 'ensemble'
      elif form['task'].value == 'parameter3_1':
        modus = 'library_design'
    else:
      modus = None
      error += " No Task selected. "
    
    if form.has_key("Mini"):
      mini = form["Mini"].value # this is either 'mini' or 'classic'
    elif modus == 4 or modus == 'ensemble': # we're fine and don't need a binary, so let's set a default
      mini = " "
    else:
      error += " No Rosetta binary selected. " # this is preselected in HTML code, so this case should never occur, we still make sure!

    
    if form.has_key("nos"):
      nos = min( int(form["nos"].value), 100)
    else:
      nos = 10
        
    if form.has_key("keep_output") and int(form["keep_output"].value) == 1:
      keep_output = 1
    else:
      keep_output = 1 # ALWAYS KEEP OUTPUT FOR NOW
    
    PM_chain  = ''
    PM_resid  = ''
    PM_newres = ''
    PM_radius = ''
    ENS_temperature = ''
    ENS_num_designs_per_struct = ''
    ENS_segment_length = ''
        
    if modus == 'point_mutation':
      # submit_point_mutation(self,database,form)
      if form.has_key("PM_chain") and form["PM_chain"].value != '':
        PM_chain = form["PM_chain"].value

      if form.has_key("PM_resid") and form["PM_resid"].value != '':
        PM_resid = form["PM_resid"].value

      if form.has_key("PM_newres") and form["PM_newres"].value != '':
        PM_newres = form["PM_newres"].value

      if form.has_key("PM_radius") and form["PM_radius"].value != '':
        PM_radius = form["PM_radius"].value
    
    # Multiple PointMutations
    elif modus == 'multiple_mutation':
      PM_chain  = []
      PM_resid  = []
      PM_newres = []
      PM_radius = []
      
      for x in range(ROSETTAWEB_max_point_mutation):
        key = "PM_chain" + str(x)
        if form.has_key(key) and form[key].value != '':
          PM_chain.append(form[key].value)
        else:
          break
        key = "PM_resid" + str(x)
        if form.has_key(key) and form[key].value != '':
          PM_resid.append(form[key].value)
        key = "PM_newres" + str(x)
        if form.has_key(key) and form[key].value != '':
          PM_newres.append(form[key].value)
        key = "PM_radius" + str(x)
        if form.has_key(key) and form[key].value != '':
          PM_radius.append(form[key].value)

      PM_chain  = str(PM_chain).strip('[]').replace(', ','-')
      PM_resid  = str(PM_resid).strip('[]').replace(', ','-')
      PM_newres = str(PM_newres).strip('[]').replace(', ','-')
      PM_radius = str(PM_radius).strip('[]').replace(', ','-')
      
# gregs ensemble
    elif modus == 4:
      if form.has_key("ENS_temperature") and form["ENS_temperature"].value != '':
        ENS_temperature = form["ENS_temperature"].value
      else:
        ENS_temperature = ""
      if form.has_key("ENS_num_designs_per_struct") and form["ENS_num_designs_per_struct"].value != '':
        ENS_num_designs_per_struct = form["ENS_num_designs_per_struct"].value
      else:
        ENS_num_designs_per_struct = ""
      if form.has_key("ENS_segment_length") and form["ENS_segment_length"].value != '':
        ENS_segment_length = form["ENS_segment_length"].value
      else:
        ENS_segment_length = ""
  #    else:
  #      (ENS_temperature, ENS_num_designs_per_struct, ENS_segment_length) = ('','','')


    if len(error):      # if something went wrong, sent HTML header that redirects user/browser to the form
      s = sys.stdout
      sys.stderr = s
      s.write( "Content-type: text/html\n")
      s.write( "Location: http://%s/backrub/cgi-bin/%s?query=submit&error_msg=%s\n\n" % ( ROSETTAWEB_server_name, ROSETTAWEB_server_script, error) )
      return False
    else:
      # if we're good to go, create new job
      # get ip addr hostname
      IP = os.environ['REMOTE_ADDR']
      sock = socket
      hostname = sock.gethostbyaddr(IP)[0]
      
      # lock table
      sql = "LOCK TABLES backrub WRITE, Users READ"
      execQuery(connection, sql)
      # write information to database
      sql = """INSERT INTO backrub (Date,Email,UserID,Notes,Mutations,PDBComplex,PDBComplexFile,IPAddress,Host,Mini,EnsembleSize,KeepOutput,PM_chain,PM_resid,PM_newres,PM_radius,task, ENS_temperature, ENS_num_designs_per_struct, ENS_segment_length) 
                      VALUES (NOW(), "%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s")""" % ( Email, UserID, JobName, mutations_data, pdbfile.value.replace('"',' '), pdb_filename, IP, hostname, mini, nos, keep_output, PM_chain, PM_resid, PM_newres, PM_radius, modus, ENS_temperature, ENS_num_designs_per_struct, ENS_segment_length )
      try: 
        import random
        execQuery(connection, sql)
        sql = """SELECT ID FROM backrub WHERE UserID="%s" AND Notes="%s" ORDER BY Date DESC""" % ( UserID , JobName )
        result  = execQuery(connection, sql)
        ID      = result[0][0]
        # create a unique key as name for directories from the ID, for the case we need to hide the results
        # do not just use the ID but also a random sequence
        tgb = str(ID) + 'flo' + join(random.sample('0123456789abcdefghijklmnopqrstuvwxyz0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789', 6), '')
        cryptID = md5.new(tgb.encode('utf-8')).hexdigest()
        sql = 'UPDATE backrub SET cryptID="%s" WHERE ID="%s"' % (cryptID, ID)
        result  = execQuery(connection, sql)
        # success
      except _mysql_exceptions.OperationalError, e:
        html = '<H1 class="title">New Job not submitted</H1>'
        if e[0] == 1153:
          html += """<P>We are sorry but the size of the PDB file exceeds the upload limit. 
          Please revise your file and delete unneccessary entries (e.g. copies of chains).</P>
          <P><A href="rosettaweb.py?query=submit">Submit</A> a new job.</P>"""
        else:
          html += """<P>An error occurred. Please revise your data and <A href="rosettaweb.py?query=submit">submit</A> a new job. If you keep getting error messages please <A href="mailto:%s?subject=[%s] - Upload Error" style="font-size: 10pt">contact us</A>.</P>""" % ( ROSETTAWEB_contact_email, ROSETTAWEB_server_title )
      
      # unlock tables
      sql = "UNLOCK TABLES"
      execQuery(connection, sql)
      
  elif form.has_key("error_msg"):
    return False # we haven't processed any data
  else:
    form['error_msg'] = 'wrong mode for submit()'
    return False
    
  return True # true we processed the data

########################################## end of submit() ####################################

# def submit_point_mutation(); 
#     '''This function checks for the parameters from the form and writes them to the according database'''
#     # PointMutation
#     if form.has_key("PM_chain") and form["PM_chain"].value != '':
#       PM_chain = form["PM_chain"].value
#       if PM_chain = ######## I WAS WORKING HERE!!!!!!! ###################
#     else:
#       return false
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


def queue(form, SID):
  
  output = StringIO()
  output.write('<TD align="center">')
  sql = "SELECT ID, cryptID, Status, UserID, Date, Notes, Mini, EnsembleSize, Errors FROM backrub ORDER BY backrub.ID DESC"
  result1 = execQuery(connection, sql)
  # get user id of logged in user
  sql = 'SELECT UserID FROM Sessions WHERE SessionID="%s"' % SID
  userID1 = execQuery(connection, sql)[0][0]
  
  results = []
  for line in result1:
    new_lst = []
    sql = "SELECT UserName FROM Users WHERE ID=%s" % line[3]
    result2 = execQuery(connection, sql)
    new_lst.extend(line)
    if int(line[3]) == int(userID1):
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
  userID1 = execQuery(connection, sql)[0][0]  
    
  if form.has_key("jobID"): # check if there is in fact a jobID
    # get user id for this job
    sql = 'SELECT UserID,Status FROM backrub WHERE ID="%s"' % ( form["jobID"].value )
    userID2 = execQuery(connection, sql)
    
    # job does no longer exist
    if len(userID2) == 0:
      html += "Job %s not found. <br><br>" % ( form["jobID"].value )
    elif userID2[0][1] == 1:
      html += "Unable to delete job %s. Already running! <br><br>" % ( form["jobID"].value )
    elif userID2[0][1] == 2:
      html += "Job %s is done. It will automatically be deleted after 10 days.<br><br>" % ( form["jobID"].value )
    # see whether logged in user and job owner are the same, if not, log the cheater out!
    elif userID1 != userID2[0][0]:
      html += 'You are not allowed to delete this job! <br><font color="red"> Logout forced.</font><br><br>'
      logout(form,None,SID=SID)
      return html
    else:
      # delete the job from database only if it's still not running
      if form.has_key("button") and form["button"].value == "Delete":
        sql = 'DELETE FROM backrub WHERE ID="%s" AND UserID="%s" AND Status=0' % ( form["jobID"].value, userID1 )
        result = execQuery(connection, sql)
        html += 'Job %s deleted. <br> <br> \n' % ( form["jobID"].value )
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
        
        obj_DB = rosettadb.RosettaDB( ROSETTAWEB_db_host, ROSETTAWEB_db_db, ROSETTAWEB_db_user, ROSETTAWEB_db_passwd, ROSETTAWEB_db_port, ROSETTAWEB_db_socket, ROSETTAWEB_store_time )
        parameter = obj_DB.getData4cryptID('backrub', cryptID)
        if len(parameter) > 0:
            return (True, parameter)
    
    return (False, None)

########################################## end of jobinfo() ###################################



# run Forest run!
ws()
