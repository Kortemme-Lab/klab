#!/usr/bin/python
import cgitb; cgitb.enable()

# Some hosts will need to have document_root appended
# to sys.path to be able to find user modules
import sys, os

sys.path.append(os.environ['DOCUMENT_ROOT'])

import session, time

sess = session.Session(expires=365*24*60*60, cookie_path='/')
# expires can be reset at any moment:
sess.set_expires('')
# or changed:
sess.set_expires(30*24*60*60)

# Session data is a dictionary like object
lastvisit = sess.data.get('lastvisit')
print "\n\n%s\n\n" % lastvisit
if lastvisit:
   message = 'Welcome back. Your last visit was at ' + \
      time.asctime(time.gmtime(float(lastvisit)))
else:
   message = 'New session'

# Save the current time in the session
sess.data['lastvisit'] = repr(time.time())
print """\
%s
Content-Type: text/plain\n
sess.cookie = %s
sess.data = %s
%s
""" % (sess.cookie, sess.cookie, sess.data, message)
sess.close()