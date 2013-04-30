#!/usr/bin/python
# -*- coding: iso-8859-15 -*-

# This module functions as a CGI script, parsing the CGI arguments 
# and calling the appropriate functions from the lower levels to
# produce web pages.


# import the basics
import sys, os
import sha, time

import cgi, Cookie
import cgitb; cgitb.enable()
# set Python egg dir MscOSX only
if os.uname()[0] == 'Darwin':
  os.environ['PYTHON_EGG_CACHE'] = '/Applications/XAMPP/xamppfiles/tmp'
import MySQLdb
import socket
import md5

# Append document_root to sys.path to be able to find user modules
sys.path.append(os.environ['DOCUMENT_ROOT'])

import session

from datetime import datetime
from string import *
from cStringIO import StringIO
from cgi import escape
from rwebhelper import *

UserID = None

EMAIL_FROM = "lauck@cgl.ucsf.edu"

parameter = read_config_file('/etc/rosettaweb/parameter.conf')

ROSETTAWEB_db_host   = parameter['db_host']
ROSETTAWEB_db_db     = parameter['db_name']
ROSETTAWEB_db_user   = parameter['db_user']
ROSETTAWEB_db_passwd = parameter['db_pw']
ROSETTAWEB_db_port   = int(parameter['db_port'])
ROSETTAWEB_db_socket = parameter['db_socket']

ROSETTAWEB_servername = os.environ['SERVER_NAME']
ROSETTAWEB_scriptname = os.environ['SCRIPT_NAME']

###############################################################################################
#                                                                                             #
# ws()                                                                                        #
#                                                                                             #
# This is the main function call. It parses the CGI arguments and generates web pages.        #
# It takes no formal arugments, but parses the following CGI form fields:                     #
#                                                                                             #
#  query  [ register | login | logout | index | terms_of_service | submit | queue | update ]  #
#                                                                                             # 
###############################################################################################

def ws():
  global UserID
  
  s = sys.stdout
  sys.stderr = s # should be removed later
  form = cgi.FieldStorage()

  # SECURITY CHECK - escape HTML code
  for key in form:
    form[key].value = escape(form[key].value)
    if key == "Password" or key == "ConfirmPassword" or key == "myPassword":
      tgb = str(form[key].value)
      form[key].value = md5.new(tgb.encode('utf-8')).hexdigest()

  expiration = 60*60 # = 1h
  html = ""
  query_type = "schnitzel"
  SID = ""
  
  # session ID
  # get cookie 
  my_session = session.Session(expires=expiration, cookie_path='/')
  # get time of last visit
  lastvisit = my_session.data.get('lastvisit')
  # set session ID 
  SID = my_session.cookie['sid'].value
  #get present time as datetime object
  t = datetime.now()
  # set cookie to the present time with time() function, should be almost the same as above
  my_session.data['lastvisit'] = repr(time.time())
  
  # for debug output, this way print-command will be shown before the make_header function 
  s.write(str(my_session.cookie)+'\n')
  s.write("Content-type: text/html\n")  

  if lastvisit:  # lastvisit != 0 means that this cookie wasn't just created. session should be known
    # get infos about session
    sql = "SELECT loggedin, UserID FROM Sessions WHERE SessionID = \"%s\"" % SID
    result = execQuery( sql )
    
    #if user is logged in do everything he wants ;) ... as long as he's allowed to do that, if not send him to login
    if result[0][0] == 1 and form.has_key("query") and form['query'].value in ["register","logout","index","jobinfo","terms_of_service","submit","queue", "update","data_formats","faq","doc"]:
      UserID = result[0][1]
      query_type = form["query"].value
    elif form.has_key("query") and form['query'].value in ["register","index","terms_of_service","oops","data_formats","faq","doc"]:
      query_type = form["query"].value
    else:
      query_type = "login"

  else: # new sessionID -> put it in DB and reload page with cookie
    # put actual time in the database
    lv_strftime = t.strftime("%Y-%m-%d %H:%M:%S")
    
    sql = "INSERT INTO Sessions (SessionID,Date,query,loggedin) VALUES (\"%s\",\"%s\",\"%s\",\"%s\") " % (SID, lv_strftime, "login", "0")
    result = execQuery( sql )
    
    sql = "SELECT UserID FROM Sessions WHERE SessionID = \"%s\"" % SID
    result = execQuery( sql )
    UserID = result[0][1]
    #s.write(str(my_session.cookie)+'\n')
    #s.write("Content-type: text/html\n")
    s.write( "Location: http://%s/alascan/cgi-bin/%s\n\n" % (ROSETTAWEB_servername, ROSETTAWEB_scriptname) )
    ## close session object
    my_session.close()
    return
  
  # session is now active, execute function
  if query_type     == "index":
    html += dummy()  
  elif query_type   == "submit":
    html += submit(form, SID)
  elif query_type   == "queue":
    html += queue(form, SID)
  elif query_type   == "jobinfo":
    html += jobinfo(form)
  elif query_type   == "login":
    html += login(form, my_session, t)
  elif query_type   == "register":
    html += register(form, SID)
  elif query_type   == "update":
    html += update(form, SID)
  elif query_type   == "terms_of_service":
    html += terms_of_service()
  elif query_type   == "data_formats":
    html += help("data_formats")
  elif query_type   == "faq":
    html += help("faq")
  elif query_type   == "doc":
    html += help("doc")
  elif query_type   == "logout":
    html += logout(form, my_session)
  elif query_type   == "oops":
    html += send_password(form)
  else:
    html += "you caused an impossible error" # should never happen since we only allow states from list above
  
  # if strange errors occur put these two lines at the beginning of the function:
#  s.write(str(my_session.cookie)+'\n')
#  s.write("Content-type: text/html\n\n")
  
  s.write("\n")   # this ends the HTML header from line 60-62
  #print os.environ
  s.write(make_header()) 
  s.write(make_menu(SID))
  if query_type in ["data_formats","doc","faq"]:
    s.write("<td><p>" + html + "</p>")
  else:
    s.write("<td align=center><p>" + html + "</p>")
  s.write(legal_info())
  s.write(make_footer())
  
  # close session object
  my_session.close()
  
########################################## end of ws() ########################################


###############################################################################################
#                                                                                             #
# login()                                                                                     #
#                                                                                             #
#   performs all necessary actions to login a users                                           # 
#                                                                                             #
###############################################################################################


def login(form, my_session, t):
  output = StringIO()
  
  # get session info
  SID         = my_session.cookie['sid'].value
  lastvisit   = my_session.data['lastvisit']
  lv_strftime = t.strftime("%Y-%m-%d %H:%M:%S")

  ## we first check if the user can login, if not, we send him the login form
  if form.has_key('login') and form['login'].value == "login" and form.has_key('myPassword') :
    # check for userID and password
    sql = "SELECT ID,Password  FROM Users WHERE UserName = \"%s\" " % form["myUserName"].value
    result = execQuery(sql)
    try:
      UserID = result[0][0]
      PW     = result[0][1]
      if UserID not in [7, 84, 379, 380]:
          output.write("""Server not publicly accessible.""")   
      else:
          output.write( "<br>" )
          if form["myPassword"].value == PW:
            # all clear ... go!
            sql = "UPDATE Sessions SET UserID = \"%s\", Date = \"%s\", loggedin = \"%s\" WHERE SessionID = \"%s\" " % ( UserID, lv_strftime, "1", SID)
            result = execQuery(sql)
            #output.write( sql )
            output.write( "<br>" )
            output.write(""" You have successfully logged in. <br> <br> \n 
                            Proceed to <A href="alascan2.py?query=submit">Simulation Form</A>  or                               \n
                                        <A href="alascan2.py?query=queue">Queue</A> . <br><br>                                   \n""")
          else:
            output.write(""" Wrong password. Please go <A href="alascan2.py?query=login">back</A> .                  \n""")   
    except IndexError:
      output.write( "<br>" )
      output.write(""" Username not found. Please go <A href="alascan2.py?query=login">back</A> .                  \n""")
    

  else: # print login form
    sql = "SELECT loggedin, UserID FROM Sessions WHERE SessionID = \"%s\"" % SID
    result = execQuery( sql )
    message = ""
    disable = ""
    if result[0][0] == 1:
      message = """<font color="FF0000">You are already logged in.</font><br>"""
      UserID = result[0][1] 
      disable = "disabled"
    output.write("""<H1 class="title">Login</H1> %s\n
                    <P>If you do not have an account, please <A href="/backrub/cgi-bin/rosettaweb.py?query=register">register</A> .</P>        \n
                    <form method=post action="alascan2.py">                                                                \n
                    <table border=0 cellpadding=5 cellspacing=0>                                                           \n
                        <tr><td align=right>Username: </td><td><input type=text name=myUserName value="" %s>    </td></tr> \n
                        <tr><td align=right>Password: </td><td><input type=password name=myPassword value="" %s></td></tr> \n
                        <tr><td></td>                                                                                      \n
                    <td align=left>                                                                                        \n
                    <input type=hidden name=query_type value="login">                                                      \n
                    <input type=hidden name=login      value="login">                                                      \n
                    <input type=submit name=submit     value="Login" %s>                                                   \n
                    </td></tr>                                                                                             \n
                    </table>                                                                                               \n
                    </form>                                                                                                \n
                    <P>Forget your password? <A href="alascan2.py?query=oops">Click here</A> .</P>                                 \n
                    <br><br>                                                                                               \n 
                    """ % (message, disable, disable, disable) )
  
  html = output.getvalue()
  output.close()
  
  return html

################################### end login() ###############################################

###############################################################################################
#                                                                                             #
# logout()                                                                                    #
#                                                                                             #
#  set logged in status to not logged in                                                      # 
#                                                                                             #
###############################################################################################

def logout(form, my_session):
  output = StringIO()
  # get sessionID
  SID = my_session.cookie['sid'].value
  # update database
  sql = "UPDATE Sessions SET loggedin = \"%s\" WHERE SessionID = \"%s\" " % ( "0", SID)
  #output.write(sql)
  execQuery(sql)
  output.write("""  You have successfully logged out. <br><br> \n""")
  
  html = output.getvalue()
  output.close()
  
  return html

################################### end logout() ##############################################

###############################################################################################
#                                                                                             #
# send_password()                                                                             #
#                                                                                             #
# asks for an email address to send password to                                               #
#                                                                                             #
###############################################################################################

def send_password(form):
  output = StringIO()
  if form.has_key("Email"):
    import random
    
    Email = form["Email"].value
    
    sql = "SELECT ID,FirstName,UserName FROM Users where Email=\"%s\"" % Email
    result = execQuery(sql)
    
    if len(result) < 1:
      output.write('Your email address is not in our database. Please <A href="alascan2.py?query=register">register</A>.<br><br> \n')
    else:
      password = join(random.sample('0123456789abcdefghijklmnopqrstuvwxyz0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789', 6),'')
      crypt_pw = md5.new(password.encode('utf-8')).hexdigest()
      
      sql = 'UPDATE Users SET Password="%s" WHERE ID=%s' % ( crypt_pw, result[0][0] )
      result_null = execQuery(sql)
      
      if len(result_null) != 0:
        output.write('An error occured while accessing database. Please try again.<br><br> \n')
      else:
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
        """ % ( result[0][1], result[0][2], password )
        
        if sendMail(Email, EMAIL_FROM, "Forgotten Password Request", text) == 1:
          output.write("""A new password was sent to %s <br><br> \n""" % Email)
        else:
          output.write("""Sending password failed. <br><br> \n""")
  
  else: # present form
  
    output.write("""
      <SCRIPT LANGUAGE="Javascript">
      <!-- Hide from old browsers
      function ValidateForm() {
            if ( document.myForm.Email.value.indexOf("@") == -1 ||
                document.myForm.Email.value.indexOf(".") == -1 ||
                document.myForm.Email.value.indexOf(" ") != -1 ||
                document.myForm.Email.value.length < 6 ) {
                            alert("Your email address is not valid.");
                            return false;
            }
            return true;
      }
      // Stop hiding from old browsers -->
      </SCRIPT>
      
      <H1 class="title">Forgot your password?</H1>
      <p>Enter your email address below to have your password emailed to you.</p>
      
      <form name="myForm" method="post" onsubmit="return ValidateForm();">
      <table border=0 cellpadding=3 cellspacing=0>
        <tr><td>
          Email Address: <br><input type="text" maxlength=100 name="Email" value="" size=20>
        </td></tr>
      </table>
      <br>
      <input type=hidden name="query" value="oops">
      <input type=submit value="Submit">
      </form>
      """)

  html = output.getvalue()
  output.close()
  
  return html

################################### end send_password() #######################################

###############################################################################################
#                                                                                             #
# register()                                                                                  #
#  present either a form for registration or check if user or emailadress already exist       #
#  if not add new user to database                                                            #
#                                                                                             #
###############################################################################################

def register(form, SID):
  output = StringIO()
  # define allowed fields 
  value_list   = ["UserName", "FirstName", "LastName", "Institution", "Email", "Password"]
  value_list_o = ["Country", "State", "Zip", "EmailList"]
  # mapping field name and field text
  value_names  = {"UserName" : "User Name", "FirstName" : "First Name", "LastName" : "Last Name", "Email" : "Email", "Institution" : "Institution", "State" : "State", "Zip" : "Zip", "Country" : "Country", "Password" : "Password", "EmailList" : "Email List"}
  
  run_form = False # used to define whether the form should be shown or not  
  form_db  = {}    # store values retrieved from Database
  
  # 2 modes check and form
  if form.has_key("mode") and form["mode"].value == "check":
    # check whether email or username are already in database
    # other values are checked by java script when entering in form
    sql = "SELECT * FROM Users WHERE UserName =\"%s\""  % form["UserName"].value
    sql_out = execQuery(sql)
    if len(sql_out) >= 1:           # if we get something, name is already taken
      form["UserName"].value = ''   # reset
      run_form = True               # show form
    
    sql = "SELECT * FROM Users WHERE Email = \"%s\""  % form["Email"].value
    sql_out = execQuery(sql)
    if len(sql_out) >= 1:
      form["Email"].value = ''
      run_form = True
    
  else:
     run_form = True
    
  if run_form:
    output.write( """
    <SCRIPT LANGUAGE="Javascript">
  
    <!-- 
    function ValidateForm() {
        if ( document.myForm.UserName.value == "" ||
            document.myForm.FirstName.value == "" ||
            document.myForm.LastName.value == "" ||
            document.myForm.Institution.value == "" ||
            document.myForm.Password.value == "" ||
            document.myForm.ConfirmPassword.value == "") {
                      alert("Please complete all required fields.");
                      return false;
        }
        if ( document.myForm.Email.value.indexOf("@") == -1 ||
            document.myForm.Email.value.indexOf(".") == -1 ||
            document.myForm.Email.value.indexOf(" ") != -1 ||
            document.myForm.Email.value.length < 6 ) {
                        alert("Your email address is not valid.");
                        return false;
        }
        if ( document.myForm.Password.value != document.myForm.ConfirmPassword.value  ) {
                alert("Your password does not match your password confirmation.");
                return false;
        }
        return true;
    }
    -->
  
    </SCRIPT>
    <H1 class="title">Registration</H1>
    <p>
    This is the <A href="http://kortemmelab.ucsf.edu">Kortemme Lab</A>  - Interface Alanine Scanning Server at <A href="http://www.ucsf.edu">UCSF</A> . Alinine Scanning is part of <A href="http://robetta.bakerlab.org">Robetta</A> . At this time, Robetta is only available for use by the academic community and other not-for-profit entities.
    </p>
    <P>
    This account will also valid for <A href="http://%s/backrub/">RosettaBackrub</A>. 
    </P>
    <br>
    <form name="myForm" method="post" onsubmit="return ValidateForm();">
      <table border=0 cellpadding=2 cellspacing=0>
        <tr><td colspan=2><b>Required Items</b></td></tr>
    """ % (ROSETTAWEB_servername))
    
    # for the required fields we have 3 options: 
    # - form has no such key => empty form
    # - form has key => fine, show value
    # - form has key, is empty => somthing wasn't right (username existed or so) mark it red
    
    # required items
    for value_entry in value_list:
      if value_entry == "Password":
        output.write("""                                                                          \n
          <tr><td align=right class="register">Password: </td>                                    \n
              <td><input type=password size=20 maxlength=50 name=Password value="">*</td>         \n
          </tr>                                                                                   \n
          <tr><td align=right class="register">Confirm Password: </td>                            \n
              <td><input type=password size=20 maxlength=50 name=ConfirmPassword value="">*</td>  \n
          </tr>                                                                                   \n """)
      else:
        output.write("""  <tr><td align=right class="register">%s: </td> """ % value_names[value_entry] )
        if form.has_key(value_entry):
          if form[value_entry].value == '':
            # something went wrong, color the field
            output.write(""" <td><input type=text name=%s size=20 maxlength=50 value="" style="background: #FF0000;"> *</td>  """ % value_entry )
          else:
            # we have data to put in
            output.write(""" <td><input type=text name=%s size=20 maxlength=50 value="%s"> *</td>   """ % (value_entry, form[value_entry].value) )
        else:
          # no data, field is shown for the first time
          output.write("""   <td><input type=text name=%s size=20 maxlength=50 value=""> *</td>     """ % value_entry )
        output.write("""     </tr>                                                                                """)
    
    output.write("""                                                                           
          <tr><td colspan=2>&nbsp;</td></tr>                                                  
          <tr><td colspan=2><b>Optional Items</b></td></tr>""")
                       
    # optional items
    for value_entry in value_list_o:
      # country is different
      if value_entry == "Country":
        output.write(""" <tr><td align=right class="register">Country</td>                                 """)
        output.write(""" <td><select name="Country">                                                       """)
        output.write( print_countries("") ) 
        output.write("""        </select> &nbsp; </td>                                                     """)
      # as well as email list
      elif value_entry == "EmailList":
        output.write(""" <tr><td align=right class=register>Add me to your email list: </td>               """)
        if form.has_key("EmailList"):
          if form["EmailList"] == 0:
            output.write("""            <td><input type=radio name=EmailList value=1> Yes &nbsp;
                                          <input type=radio name=EmailList value=0 checked> No</td>        """)        
        else:
          output.write("""            <td><input type=radio name=EmailList value=1 checked> Yes &nbsp;
                                          <input type=radio name=EmailList value=0 > No</td>               """)
      else :
        output.write("""  <tr><td align=right class="register">%s: </td>       """ % value_names[value_entry] )
        if form.has_key(value_entry):
          if form[value_entry].value == '':
            output.write(""" <td><input type=text name=%s size=20 maxlength=50 value="" style="background: #FF0000;"> </td> """ % value_entry )
          else:
            output.write(""" <td><input type=text name=%s size=20 maxlength=50 value="%s"> </td>     """ % (value_entry, form[value_entry].value) )
        else:
          output.write("""   <td><input type=text name=%s size=20 maxlength=50 value=""> </td>       """ % value_entry )
        output.write("""     </tr>                                                                         """)

    output.write("""
          <tr><td></td>                                                                        
              <td align=left><input type=hidden name=query  value=register>                     
                             <input type=hidden name=mode   value=check>                          
                             <input type=submit name=submit value=Register>                     
                    &nbsp; &nbsp; &nbsp; <A href="alascan.py?query=terms_of_service#privacy">privacy</A>  
              </td>
          </form>                    
      </tr>                            
    </table>
    """)

  else: # run form = false, i.e. everything is fine
        # transmit forms values to database
    # check whether each parameter has a value and if so append it to the database string
    fields    = "" 
    variables = "" 
    for value_name in value_list:
      if form.has_key(value_name):
        fields += value_name + ","
        variables += "\"%s\"," % form[value_name].value
    for value_name in value_list_o:
      if form.has_key(value_name):
        fields += value_name + ","
        variables += "\"%s\"," % form[value_name].value  
      sql = "INSERT INTO Users (Date, %s) VALUES (NOW(), %s)" % ( fields[:-1], variables[:-1] )
    #print sql
    execQuery(sql)
    
    text = """Dear %s,

Thank you for creating an account at the Alanine Scanning Server of Kortemme-Lab. If you have questions or if you did not create an account please let us know: %s 

-----------------------
login:       %s
Name:        %s %s
Institution: %s
      
      """ % ( form["FirstName"].value, EMAIL_FROM, form["UserName"].value, form["FirstName"].value, form["LastName"].value, form["Institution"].value )
    
    sendMail(form["Email"].value, EMAIL_FROM, "New Account", text)
    
    output.write(""" <H1 class="title">Thank you for registering.</H1> """)
    output.write(""" You may update your user information at any time by clicking the "User Information" link when your are logged in. <br><br>""")
    
  html = output.getvalue()
  output.close()
  return html


################################### end register() ##############################################

###############################################################################################
#                                                                                             #
# update()                                                                                    #
#  here we have a little redundancy (register()) that might be removed sometime               #
#  for now this is better. due to the database call I have to make a different type of map    #
#  than the one used for "form". yes ... i dunno, works though! ;)                            #
#                                                                                             #
###############################################################################################

def update(form, SID):
  output = StringIO()
  
  value_list   = ["FirstName", "LastName", "Institution", "Email", "Password"] # "UserName" ##; we don't want the user to change its name, to be able to identify him
  value_list_o = ["Country", "State", "Zip", "EmailList"]
  value_names  = {"UserName" : "User Name", "FirstName" : "First Name", "LastName" : "Last Name", "Email" : "Email", "Institution" : "Institution", "State" : "State", "Zip" : "Zip", "Country" : "Country", "Password" : "Password", "EmailList" : "Email List"}
  run_form = True
  
  form_db = {}   # store values retrieved from Database
   
  sql = "SELECT UserID from Sessions WHERE SessionID = \"%s\"" % SID
  result = execQuery(sql)
  
  UserID = result[0][0]
  sql = "SELECT * FROM Users WHERE ID = \"%s\""  % UserID
  sql_out = execQuery(sql)
  
  if form.has_key("mode") and form["mode"].value == "check":
    run_form = False
    # check whether email or username are already in database
    # other values are checked by java script when entering in form
    sql = "SELECT * FROM Users WHERE UserName =\"%s\" AND NOT ID = \"%s\""  % ( sql_out[0][1], sql_out[0][0] )
    sql_out1 = execQuery(sql)
    if len(sql_out1) >= 1:           # if this is the case, the username is already taken
      form["UserName"].value = ''   # reset
      run_form = True               # show form
    
    sql = "SELECT * FROM Users WHERE Email = \"%s\" AND NOT ID = \"%s\""  % ( sql_out[0][4], sql_out[0][0] )
    sql_out2 = execQuery(sql)
    if len(sql_out2) >= 1:
      form["Email"].value = ''
      run_form = True

 
  if len(sql_out) >= 1 :
    form_db["UserName"]      = sql_out[0][1]
    form_db["LastName"]      = sql_out[0][2]
    form_db["FirstName"]     = sql_out[0][3]
    form_db["Email"]         = sql_out[0][4]
    form_db["Institution"]   = sql_out[0][5]
    form_db["Address1"]      = sql_out[0][6]
    form_db["Address2"]      = sql_out[0][7]
    form_db["City"]          = sql_out[0][8]
    form_db["State"]         = sql_out[0][9]
    form_db["Zip"]           = sql_out[0][10]
    form_db["Country"]       = sql_out[0][11]
    form_db["Phone"]         = sql_out[0][12]
#    form_db["Password"]      = sql_out[0][13]
    form_db["Date"]          = sql_out[0][14]
    form_db["LastLoginDate"] = sql_out[0][15]
    form_db["Priority"]      = sql_out[0][16]
    form_db["Jobs"]          = sql_out[0][17]
    form_db["EmailList"]     = sql_out[0][18]
    
  if run_form:
    output.write( """
    <SCRIPT LANGUAGE="Javascript">
  
    <!-- 
    function ValidateForm() {
        if ( document.myForm.UserName.value == "" ||
            document.myForm.FirstName.value == "" ||
            document.myForm.LastName.value == "" ||
            document.myForm.Institution.value == "" // ||
        //    document.myForm.Password.value == "" ||
        //    document.myForm.ConfirmPassword.value == ""
           ) {        
                      alert("Please complete all required fields.");
                      return false;
        }
        if ( document.myForm.Email.value.indexOf("@") == -1 ||
            document.myForm.Email.value.indexOf(".") == -1 ||
            document.myForm.Email.value.indexOf(" ") != -1 ||
            document.myForm.Email.value.length < 6 ) {
                        alert("Your email address is not valid.");
                        return false;
        }
        if ( document.myForm.Password.value != document.myForm.ConfirmPassword.value  ) {
                alert("Your password does not match your password confirmation.");
                return false;
        }
        return true;
    }
    -->
  
    </SCRIPT>
    <H1 class="title">Please update your profile</H1>
    <p>
    At this time, Robetta is only available for use by the academic community and other not-for-profit entities.
    </p>
    <br>
    <form name="myForm" method="post" onsubmit="return ValidateForm();">
      <table border=0 cellpadding=2 cellspacing=0>
        <tr><td colspan=2><b>Required Items</b></td></tr>
        """ )
    
    # for the required fields we have 3 options: 
    # - form has no such key => empty form
    # - form has key => fine, show value
    # - form has key, is empty => somthing wasn't right (username existed or so) mark it red
    
    output.write("""  <tr><td align=right class="register">User Name: </td> """ )
    output.write(""" <td><input type=text name=UserName size=20 maxlength=50 value="%s" disabled> </td>  </tr> """ % form_db["UserName"] )
    for value_entry in value_list:
      
      if value_entry == "Password":
        output.write("""      
          <tr><td align=right class="register">Password: </td>                                
              <td><input type=password size=20 maxlength=50 name=Password value=""></td>    
          </tr>                                                                               
          <tr><td align=right class="register">Confirm Password: </td>                        
              <td><input type=password size=20 maxlength=50 name=ConfirmPassword value=""></td> 
          </tr>
      """)
      else:
        output.write("""  <tr><td align=right class="register">%s: </td> """ % value_names[value_entry] )
        if form_db.has_key(value_entry):
            output.write(""" <td><input type=text name=%s size=20 maxlength=50 value="%s"> </td>     """ % (value_entry, form_db[value_entry]) )
        else:
          output.write(""" <td><input type=text name=%s size=20 maxlength=50 value="" style="background: #FF0000;"> </td>   """ % value_entry )
        output.write("""     </tr>                                                                                """)

    output.write("""                                                                           
          <tr><td colspan=2>&nbsp;</td></tr>                                                  
          <tr><td colspan=2><b>Optional Items</b></td></tr>""")
                                       
    for value_entry in value_list_o:
                                         
      if value_entry == "Country":
        output.write(""" <tr><td align=right class="register">Country</td> """)
        output.write(""" <td><select name="Country"> """)
        output.write( print_countries(form_db[value_entry]) ) 
        output.write("""        </select> &nbsp; </td> """) 
        
      elif value_entry == "EmailList":
        output.write(""" <tr><td align=right class=register>Add me to your email list: </td> """)
        if form.has_key("EmailList"):
          if form["EmailList"] == 0:
            output.write("""            <td><input type=radio name=EmailList value=1> Yes &nbsp;
                                          <input type=radio name=EmailList value=0 checked> No</td> """)        
        else:
          output.write("""            <td><input type=radio name=EmailList value=1 checked> Yes &nbsp;
                                          <input type=radio name=EmailList value=0 > No</td> """)
      else :
        output.write("""  <tr><td align=right class="register">%s: </td> """ % value_names[value_entry] )
        if form_db.has_key(value_entry):
          output.write(""" <td><input type=text name=%s size=20 maxlength=50 value="%s"> </td>     """ % (value_entry, form_db[value_entry]) )
        else:
          output.write(""" <td><input type=text name=%s size=20 maxlength=50 value="" style="background: #FF0000;"> </td>   """ % value_entry )
        output.write("""     </tr>                                                                                """)

    output.write("""
          <tr><td></td>                                                                        
              <td align=left><input type=hidden name=query  value=update>                     
                             <input type=hidden name=mode   value=check>                          
                             <input type=submit name=submit value=Update>                     
                    &nbsp; &nbsp; &nbsp; <A href="alascan.py?query=terms_of_service#privacy">privacy</A>  
              </td>
          </form>
      </tr>                            
    </table>
    """)

  else: 
    # run form_db = false, i.e. everything is fine
    # transmit form_dbs values to database
    # check whether each single parameter is present is ommited, since the form_db contains an empty string
   
    data    = "" 
    for value_name in value_list + value_list_o:
      if form.has_key(value_name):
        data += value_name + " = \"" + str(form[value_name].value) + "\","

    sql = "UPDATE Users SET %s WHERE ID = %s" % (data[:-1], UserID)
    
    execQuery(sql)
    
    output.write(""" <H1 class="title">Thank you for updating your profile.</H1> <br><br> """)
    #output.write("""  """)
    
  html = output.getvalue()
  output.close()
  return html

################################### end register() ##############################################


###############################################################################################
#                                                                                             #
# submit()                                                                                    #
#                                                                                             #
# this function processes the parameter of the input form and adds a new job to the database  # 
#                                                                                             #
###############################################################################################

def submit(form, SID):
  output = StringIO()
  s = StringIO()
  
  # get information from the database
  sql      = "SELECT UserID from Sessions WHERE SessionID = \"%s\"" % SID
  result   = execQuery(sql)
  UserID   = result[0][0]
  sql      = "SELECT UserName, Email FROM Users WHERE ID = \"%s\""  % UserID
  sql_out  = execQuery(sql)
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
         error += " PDB not a file "
        
    if form.has_key("Mutations"):
      mutationsfile = form["Mutations"]
      if not mutationsfile.file:
         error += " Mutations not a file "

    # construct partner definition file
    if form["C1"].value != '' and form["C1P"].value != '' and form["C2"].value != '' and form["C2P"].value != '':
      partner1 = ""
      partner2 = ""
      num_p1   = 0
      num_p2   = 0
      for x in ["C1","C2","C3","C4","C5","C6"]:
        if form.has_key(x) and form[x].value != '' and form.has_key(x+"P") and form[x+"P"].value != '':
          if int(form[x+"P"].value) == 1:
            partner1 += " " + form[x].value
            num_p1   += 1
          elif int(form[x+"P"].value) == 2:
            partner2 += " " + form[x].value
            num_p2   += 1
          else: # should never happen due to limitations in the form
            error += "<br>For partner please choose either 1 or 2."
      Partner = str(num_p1) + partner1 + "\nF\n" + str(num_p2) + partner2 + "\nF\n"
  
    output.write('<br>')
    
    if len(error):      # if something went wrong, sent HTML header that redirects user/browser to the form
      s = sys.stdout
      s.write( "Content-type: text/html\n" )
      s.write( "Location: http://%s/alascan/cgi-bin/%s?query=submit&mode=error\n\n" % (ROSETTAWEB_servername, ROSETTAWEB_scriptname))
      return
    else:
      # if we're good to go, create new job
      # get ip addr hostname
      IP = os.environ['REMOTE_ADDR']
      sock = socket
      hostname = sock.gethostbyaddr(IP)[0]
      
      # lock table
      sql = "LOCK TABLES ALAScanQueue WRITE, Users READ"
      execQuery(sql)
      sql = "INSERT INTO ALAScanQueue (Date,Email,UserID,Notes,PartnerDefinition,Mutations,PDBComplex,PDBComplexFile,IPAddress,Host) VALUES (NOW(), \"%s\",\"%s\",\"%s\",\"%s\",\"%s\",\"%s\",\"%s\",\"%s\",\"%s\")" % ( Email, UserID, JobName, Partner, str(mutationsfile.value), str(pdbfile.value), pdbfile.filename, IP, hostname)
      #print sql
      execQuery(sql)
      
      #sql = "SELECT ID FROM ALAScanQueue WHERE UserID=\"%s\" AND Notes=\"%s\"" % ( UserID, JobName )
      #result = execQuery(sql)
      #jobID  = result[0][0]
      
      sql = "UNLOCK TABLES"
      execQuery(sql)
      
      #if pdbfile.filename:
        ## strip leading path from file name to avoid directory traversal attacks
        #fn = os.path.basename(pdbfile.filename)
        #os.mkdir("downloads/%s/" % jobID)
        #open("downloads/%s/"  % jobID + fn, 'wb').write(pdbfile.file.read())
      
      #output.write(""" <FORM NAME="submitform" method="POST" action="alascan.py" enctype="multipart/form-data">
                          #<INPUT TYPE="hidden" NAME="query" VALUE="queue">
                          #<INPUT TYPE="hidden" NAME="Email" VALUE="%s">
                          #<A href="javascript:document.submitform.submit()">To Queue</A> 
                      #</FORM>""" % form["Email"].value )
      output.write("""New Job successfully submitted.<br> 
                      User Name: %s<br> \n 
                      Job Name: %s<br> \n 
                      PDB File: %s<br><br>\n
                      Proceed to <A href="alascan2.py?query=submit">Simulation Form</A>  or <A href="alascan2.py?query=queue">Queue</A> . \n
                    """ % (UserName, JobName, pdbfile.filename) )
  
  ###############################
  #  Form for submitting a job  #
  ###############################
  else:
    error = ""
    if form.has_key("mode") and form["mode"].value == "error":
      error = "An error occured. [&nbsp;<font color="">Data was corrupted.</font>&nbsp;] <br>Please check your data and resubmit.<br><br>\n"
    output.write("""
    <SCRIPT LANGUAGE="Javascript">
    <!-- 
    function ValidateForm() {
        if ( document.submitform.JobName.value == "" ||
            document.submitform.PDBComplex.value == "" ||
            document.submitform.C1.value == "" ||
            document.submitform.C1P.value == "" ||
            document.submitform.C2.value == "" ||
            document.submitform.C2P.value == "" ) {        
                      alert("Please complete all required fields.");
                      return false;
        }
        if ( document.submitform.C1.value == document.submitform.C2.value ||
             document.submitform.C1P.value == document.submitform.C2P.value ) {
                      alert("Please check your Partner Definitions");
                      return false;
        }
        return true;
    }
    -->
    </SCRIPT>
    
    %s\n
    <!-- Start Submit Form -->
    <FORM NAME="submitform" method="POST" onsubmit="return ValidateForm();" action="alascan2.py" enctype="multipart/form-data">

    <TABLE border=0 cellpadding=2 cellspacing=0>
      <TR><TD colspan=2><b>Required</b></TD></TR>
      <TR>
        <TD colspan=2>User Name: <br> <INPUT TYPE="text" maxlength=40 SIZE=40 NAME="UserName" VALUE="%s" disabled>
        </TD>
      </TR>
      <TR></td></TR>
      <TR>
        <TD colspan=2>Job Name: <br> <INPUT TYPE="text" maxlength=40 SIZE=40 NAME="JobName" VALUE=""> </TD>
      </TR>
      <TR>
        <TD align=right>Upload <A href="alascan2.py?query=data_formats#pdbcomplex">Complex</A> : </TD>
        <TD align=left> <INPUT TYPE="file" NAME="PDBComplex"> *</TD>
      </TR>
      <TR> <TD colspan=2><A href="alascan2.py?query=doc#partnerdefs">Partner Definitions</A> : </TD> </TR>
      <TR> <TD align=right>Chain 1: </TD> 
          <TD align=left> <INPUT TYPE="text" SIZE=2 maxlength=2 NAME="C1" VALUE=""> *
                          <SELECT name=C1P><OPTION VALUE="">Select Partner</OPTION>
                                        <OPTION VALUE="1">1</OPTION>
                                        <OPTION VALUE="2">2</OPTION>
                          </SELECT> *
      </TD> </TR>
      
      <TR> <TD align=right>Chain 2: </TD>
            <TD align=left><INPUT TYPE="text" SIZE=2 maxlength=2 NAME="C2" VALUE=""> *
            <SELECT name=C2P><OPTION VALUE="">Select Partner</OPTION><OPTION VALUE="1">1</OPTION><OPTION VALUE="2">2</OPTION></SELECT> *
      </TD></TR>
  
      <TR> <TD align=right>Chain 3: </TD>
            <TD align=left><INPUT TYPE="text" SIZE=2 maxlength=2 NAME="C3" VALUE="">
            <SELECT name=C3P><OPTION VALUE="">Select Partner</OPTION><OPTION VALUE="1">1</OPTION><OPTION VALUE="2">2</OPTION></SELECT>
      </TD></TR>
  
      <TR> <TD align=right>Chain 4: </TD>
            <TD align=left><INPUT TYPE="text" SIZE=2 maxlength=2 NAME="C4" VALUE="">
            <SELECT name=C4P><OPTION VALUE="">Select Partner</OPTION><OPTION VALUE="1">1</OPTION><OPTION VALUE="2">2</OPTION></SELECT>
      </TD></TR>
  
      <TR> <TD align=right>Chain 5: </TD>
            <TD align=left><INPUT TYPE="text" SIZE=2 maxlength=2 NAME="C5" VALUE="">
            <SELECT name=C5P><OPTION VALUE="">Select Partner</OPTION><OPTION VALUE="1">1</OPTION><OPTION VALUE="2">2</OPTION></SELECT>
      </TD></TR>
  
      <TR> <TD align=right>Chain 6: </TD>
            <TD align=left><INPUT TYPE="text" SIZE=2 maxlength=2 NAME="C6" VALUE="">
            <SELECT name=C6P><OPTION VALUE="">Select Partner</OPTION><OPTION VALUE="1">1</OPTION><OPTION VALUE="2">2</OPTION></SELECT>
      </TD></TR>
      
      <TR><TD colspan=2><b>Optional</b></TD></TR>
      <TR>
        <TD align=right><A style="color:#365a79; "href="alascan2.py?query=data_formats#mutations">Mutations List</A> : </TD>
        <TD align=left><INPUT TYPE="file" NAME="Mutations"></TD>
      </TR>
      <TR><TD align=right colspan=2><br><INPUT TYPE="Submit" VALUE="Submit"></TD></TR>
      <TR><TD align=left colspan=2><br>
  
      </TD></TR>
    </TABLE>
    * required fields
    <INPUT TYPE="hidden" NAME="query" VALUE="submit">
    <INPUT TYPE="hidden" NAME="mode" VALUE="check">
    </FORM>
  <!-- End Submit Form -->
  """ % (error, UserName) )
     
  html = output.getvalue()
  output.close()
  return html

########################################## end of submit() ####################################

###############################################################################################
#                                                                                             #
# queue()                                                                                     #
#                                                                                             #
# this function shows active, pending and finished jobs                                       #
#                                                                                             #
###############################################################################################


def queue(form, SID):
  
  output = StringIO()
  if not UserID or UserID not in [7, 84, 379, 380]:
      output.write("""Server not publicly accessible.""")   
      html = output.getvalue()
      output.close()
      return html
  sql = "SELECT ID, Status, UserID, Date, Notes, Errors, Host FROM ALAScanQueue ORDER BY ALAScanQueue.ID DESC"
  result1 = execQuery(sql)
  
  results = []
  for line in result1:
    new_lst = []
    sql = "SELECT UserName FROM Users WHERE ID=%s" % line[2]
    result2 = execQuery(sql)
    new_lst.extend(line)
    new_lst[2] = result2[0][0]
    results.append(new_lst)
  
  output.write( """<H1 class="title"> Process queue </H1> <br>""" )
  output.write( """<table border=0 cellpadding=2 cellspacing=1 width=700 >
                   <colgroup>
                     <col width="30">
                     <col width="70">
                     <col width="100">
                     <col width="200">
                     <col width="100">
                     <col width="100">
                     <col width="100">
                   </colgroup>         """ )
  output.write( """<tr align=center bgcolor="#CCCCCC"> 
                   <td > ID </td> 
                   <td > Status </td> 
                   <td > User Name </td>
                   <td > Date (PST) </td>
                   <td > Job Name </td>
                   <td > Error </td>
                   <td > Host </td> </tr>""" )
  for line in results:
    output.write( """<tr align=center bgcolor="#EEEEEE">""" )
    i = 0
    for word in line:
      if i == 0:
        output.write( """<td><A href="alascan2.py?query=jobinfo&jobnumber=%s">%s</A> </td>""" % (str(word),str(word)) )
      
      elif i == 1:
        status = int(word)
        if status == 0:
          output.write( """<td><font color="orange">in queue</font></td>""")
        elif status == 1:
          output.write( """<td><font color="green">active</font></td>""" )
        elif status == 2:
          output.write( """<td><A href="../downloads/%s/">done</A> </td>""" % str(line[0]) )
        else:
          output.write( """<td><font color="FF0000">error</font></td>""")
      elif i == 4:
        if len(str(word)) < 12:
          output.write( "<td>%s</td>" % str(word))
        else:
          output.write( "<td>%s</td>" % (str(word)[0:10] + "..."))
      else:
        output.write( "<td>%s</td>" % str(word))
      i += 1
    output.write( "</tr>" )
  output.write( "</table> <br>" )

  html = output.getvalue()
  output.close()
  
  return html

########################################## end of queue() ####################################

###############################################################################################
#                                                                                             #
# jobinfo()                                                                                   #
#                                                                                             #
# this function shows active, pending and finished jobs                                      #
#                                                                                             #
###############################################################################################


def jobinfo(form):
  html = ""

  if form.has_key("jobnumber"):
    jobnumber = form["jobnumber"].value  
    sql = "SELECT Status, Email, Date, StartDate, EndDate, Notes, Errors, PartnerDefinition, DATE_ADD(EndDate, INTERVAL 8 DAY),  TIMEDIFF(DATE_ADD(EndDate, INTERVAL 7 DAY), NOW()) FROM ALAScanQueue WHERE ID=%s" % jobnumber
    result = execQuery(sql)
    status = ""
    if   int(result[0][0]) == 0:
      status = "in queue"
    elif int(result[0][0]) == 1:
      status = "active"
    elif int(result[0][0]) == 2:
      status = "done"
    else:
      status = """<font color="FF0000">error:</font> %s""" % result[0][6]
    
    p_def = result[0][7].split('\n')
    partner1 = p_def[0][1:]
    partner2 = p_def[2][1:]
    
    html += """ <H1 class="title">Interface Alanine Scanning Server Job %s</H1><br> """ % jobnumber
    if status == "done":
      html += """ The results can be displayed on the structure using a <a href="http://www.umass.edu/microbio/rasmol/getras.htm" target="_blank">Rasmol</a> script that is available in the <A href="../downloads/%s/">results directory</A>.\n\n
      <PRE>usage: rasmol -script &lt;scriptfile&gt;</PRE>\n\n
      Positions are colored by relative DDG(complex) values, <NOBR>Yellow -&gt; Red -&gt; Blue</NOBR>\n<br><br>\n """ % jobnumber
    html += """ 
      <table border=0 cellpadding=2 cellspacing=1>
        <tr><td align=right bgcolor="#EEEEEE">Job Name: </td><td bgcolor="#EEEEEE">%s</td></tr>
        <tr><td align=right bgcolor="#EEEEEE">Status: </td><td bgcolor="#EEEEEE">%s</td></tr>
        <tr><td align=right bgcolor="#EEEEEE">Date Submitted: </td><td bgcolor="#EEEEEE">%s</td></tr>
        <tr><td align=right bgcolor="#EEEEEE">Started: </td><td bgcolor="#EEEEEE">%s</td></tr>
        <tr><td align=right bgcolor="#EEEEEE">Ended: </td><td bgcolor="#EEEEEE">%s</td></tr>
        <tr><td align=right bgcolor="#EEEEEE">Expires: </td><td bgcolor="#EEEEEE">%s (%s)</td></tr>
        <tr><td align=right valign=top bgcolor="#EEEEEE">Chains (Partner 1): </td><td bgcolor="#EEEEEE">%s</td></tr>
        <tr><td align=right valign=top bgcolor="#EEEEEE">Chains (Partner 2): </td><td bgcolor="#EEEEEE">%s</td></tr>
        """ % (result[0][5],status,result[0][2],result[0][3],result[0][4],result[0][8],result[0][9],partner1,partner2)
    if status == "done":
      html += """ <tr><td colspan=2 align=center bgcolor="#EEEEEE"><A href="../downloads/%s/">Results</A> </td></tr> """ % jobnumber
    html += """</table><br><br> """
  else:
    html += """ <H1 class="title">No Data</H1><br> """
    
  return html

########################################## end of jobinfo() ####################################

def dummy():
  output = StringIO()
  output.write(""" 
           <H1 class="title">Welcome to Interface Alanine Scanning at 
           <A href="http://kortemmelab.ucsf.edu">Kortemme Lab</A> , <A href="http://www.ucsf.edu">UCSF</A> </H1> 
           <P>Alanine Scanning is part of <A href="http://robetta.bakerlab.org">Robetta</A>  
           - full-chain protein structure prediction server - developed by           
           <A href="http://www.bakerlab.org/">Baker Lab</A> , <A href="http://www.washington.edu/">University of Washington</A>.
           Please proceed to <A href="/backrub/cgi-bin/rosettaweb.py?query=register">Registration</A> or <A href="alascan2.py?query=login">login</A>.
           </P>
           <P> 
           Other services [&nbsp;<A href="http://%s/backrub/">RosettaBackrub</A>&nbsp;]
           </P>      
           <br>
  \n""" % (ROSETTAWEB_servername))
  html = output.getvalue()
  output.close()
  return html

def make_header():
  html = """
<!-- *********************************************************
     * Kortemme Lab, University of California, San Francisco *
     * Tanja Kortemme, Florian Lauck, 2008                   *
     ********************************************************* -->
  <html>
  <head>
    <title>Computational Interface Alinine Scanning Server</title>
    <META name="description" content="Robetta Server.">
    <META name="keywords" content="rosetta baker ab initio comparative modeling fragment server structure prediction">
    
    <link rel=STYLESHEET type="text/css" href="../style.css">

  </head>

  <body bgcolor="#ffffff">
  <center>
  <table border=0 width="725" cellpadding=0 cellspacing=0px>
    <tr>
      <td colspan=1 align=center width="501">
        <A href="../">
        <img src="../images/newtop.jpg" border="0" width=500 usemap="#links"></A>
      </td>
    </tr>
    <tr><td colspan=2><img src="../images/horzline_long.jpg" border=0></td></tr>
    <tr>
	<td align="right">[&nbsp;Other Services: <A href="../../backrub/"> <font style="color:green;">RosettaBackrub</font></A>&nbsp;]
        </td>
    </tr>
  </table>
  <table border=0 width="725" cellpadding=0 cellspacing=45px> 
    <tr>"""

  return html

def make_menu(SID):
  html = ""
  html += """<td align=center>\n[&nbsp;<A href="alascan2.py?query=index">Home</A>&nbsp;] &nbsp;&nbsp;&nbsp;"""
  html += """[&nbsp;<A href="alascan2.py?query=faq">FAQ</A>&nbsp;] &nbsp;&nbsp;&nbsp;\n"""
  html += """[&nbsp;<A href="alascan2.py?query=doc">Documentation</A>&nbsp;]\n"""
  html += "<br>"
  sql = "SELECT loggedin FROM Sessions WHERE SessionID = \"%s\"" % SID
  result = execQuery(sql)
  #html += "<br>%s<br>" % str(result[0][0])

  if result[0][0]:
    html += """[&nbsp;<A href="alascan2.py?query=submit">Submit</A>&nbsp;] &nbsp;&nbsp;&nbsp;\n"""
    html += """[&nbsp;<A href="alascan2.py?query=queue">Queue</A>&nbsp;] &nbsp;&nbsp;&nbsp;\n"""
    html += """[&nbsp;<A href="/backrub/cgi-bin/rosettaweb.py?query=update">User Information</A>&nbsp;] &nbsp;&nbsp;&nbsp;\n"""
    html += """[&nbsp;<A href="alascan2.py?query=logout">Logout</A>&nbsp;]\n"""
  else:
    html += """[&nbsp;<A href="alascan2.py?query=login">Login</A>&nbsp;] &nbsp;&nbsp;&nbsp;\n"""
    html += """[&nbsp;<A href="/backrub/cgi-bin/rosettaweb.py?query=register">Register</A>&nbsp;]\n"""
  
  html += """</td>\n</tr><tr>"""
  return html

def legal_info():
  html="""
    <table cellpadding=10px border=1><tr><td bgcolor="#FFFFE0">
    <p style="text-align:left; font-size: 10pt">
    If you are using the data, please cite:
    </p>
    <p style="text-align:left; font-size: 10pt">
    Kortemme, T., Kim, D.E., Baker, D. Computational Alanine Scanning of Protein-Protein Interfaces. Sci. STKE 2004
    </p>
    <p  style="text-align:left; font-size: 10pt" >
    Kortemme, T., Baker, D. A simple physical model for binding energy hot spots in protein-protein complexes. Proc Natl Acad Sci U S A. 2002 Oct 29;99(22):14116-21.
    </p>
    <p style="text-align:left; font-size: 10pt" >
    For questions, please contact <img src="/backrub/images/support_email.png" height="15"> 
    </p></td></tr></table>"""
    
  return html

def help():
  return " HELP !!!"

def make_footer():
  SSL = ''
  if ROSETTAWEB_servername == 'kortemmelab.ucsf.edu':
    SSL = '''
          <script language="javascript" src="https://seal.entrust.net/seal.js?domain=kortemmelab.ucsf.edu&img=16"></script>
          <a href="http://www.entrust.net">SSL</a>
          <script language="javascript" type="text/javascript">goEntrust();</script>
  '''

  html="""
  </td></tr>
    <tr>
      <td align=center><img src="../images/horzline_long.jpg" border=0>
	<table><tr><td>
		<p>
         	Robetta is available for NON-COMMERCIAL USE ONLY at this time<br>
         	<font color=#666688><b>[</b></font> 
            	<A href="/backrub/wiki/TermsOfService" class="nav">Terms of Service</A> 
         	<font color=#666688><b>]</b></font><br>
         	<small>Copyright &copy; 2008 University of California San Francisco, Tanja Kortemme, Florian Lauck</small>
      	</td>
      	<td>
       	%s
      	</td>
	</tr></table></td>
    </tr>
  </table>
  </center>
  </body>
  </html>\n""" % SSL
  
  return html

def terms_of_service():
  output = StringIO()
  # terms of service html can be found in this file
  f = open("../terms_of_service.html", 'r').readlines()
  # read the file and add it to our html page
  for line in f:
    output.write( line )
    
  
  html = output.getvalue()
  output.close()
  return html

def help(mode):
  output = StringIO()
    
  if mode == "data_formats":
    f = open("../data_formats.html", 'r').readlines()
    for line in f:
      output.write( line )
  if mode == "faq":
    f = open("../faq.html", 'r').readlines()
    for line in f:
      output.write( line )
  if mode == "doc":
    f = open("../doc.html", 'r').readlines()
    for line in f:
      output.write( line )
  
  html = output.getvalue()
  output.close()
  return html


#############################################################################################
#                                                                                           #
# execQuery()                                                                               #
#                                                                                           #
# A general function to execute an SQL query. This function is called whenever a query is   #
# made to the database.                                                                     #
#                                                                                           #
#############################################################################################

def execQuery(sql):
  
  connection = MySQLdb.Connection(host=ROSETTAWEB_db_host, db=ROSETTAWEB_db_db, user=ROSETTAWEB_db_user, passwd=ROSETTAWEB_db_passwd, port=ROSETTAWEB_db_port, unix_socket=ROSETTAWEB_db_socket )
  cursor = connection.cursor()
  cursor.execute(sql)
  results = cursor.fetchall()
  cursor.close()
  
  return results

##################################### end of execQuery() ####################################

def sendMail(mailTO, mailFROM, mailSUBJECT, mailTXT):
  MAIL = "/usr/sbin/sendmail"
  
  mssg = "To: %s\nFrom: %s\nSubject: %s\n\n%s" % (mailTO, mailFROM, mailSUBJECT, mailTXT)
  # open a pipe to the mail program and
  # write the data to the pipe
  p = os.popen("%s -t" % MAIL, 'w')
  p.write(mssg)
  exitcode = p.close()
  if exitcode:
    return exitcode
  else:
    return 1


def print_countries(selected):
  
  country_file = open("../countries.txt",'r')
  countries = country_file.readlines()
  country_file.close()
  html = ""
  
  if selected == "":
    html = """         <option value="" selected>Select Country</option>\n"""
  
  for country in countries:
    country_name = country.rstrip()
    if selected == country_name:
      html += """      <option value="%s"%s>%s</option>\n""" % (country_name, " selected ", country_name)
    else:
      html += """      <option value="%s">%s</option>\n""" % (country_name, country_name)

  return html








# run forest run!
ws()
