#!/usr/bin/python
# encoding: utf-8
"""
gcalendar.py
Google Calendar functionality.

Created by Shane O'Connor 2014
"""

if __name__ == '__main__':
    # todo: save this as a non-repository file
    import sys
    sys.path.insert(0, '../..')

import json
import httplib2

from apiclient.discovery import build
from oauth2client.client import OAuth2WebServerFlow

from tools.general.structures import NestedBunch


class OAuthCredentials(NestedBunch):

    @staticmethod
    def from_JSON(oauth_json):
        '''At the time of writing, keys include:
            client_secret, client_email, redirect_uris (list), client_x509_cert_url, client_id, javascript_origins (list)
            auth_provider_x509_cert_url, auth_uri, token_uri.'''
        #return NestedBunch(json.loads(oauth_json)['web'])
        return NestedBunch(json.loads(oauth_json)['service'])


import gflags

from oauth2client.file import Storage
from oauth2client.tools import run

FLAGS = gflags.FLAGS








if __name__ == '__main__':
    # todo: save this as a non-repository file
    import sys
    sys.path.insert(0, '/admin')
    from tools.fs.fsio import read_file
    oauth_json = read_file('test.json')

    jw = NestedBunch.from_JSON(oauth_json)
    print(jw.web.client_id )
    oc = OAuthCredentials.from_JSON(oauth_json)
    calendar_ids = NestedBunch.from_JSON(oauth_json).calendars
    print(oc.client_id )
    print(calendar_ids)


    from httplib2 import Http
    import pprint
    from datetime import datetime, timedelta
    import pytz

    from oauth2client.client import SignedJwtAssertionCredentials
    from apiclient.discovery import build

    # Request both read/write (calendar) and read-only access (calendar.readonly)
    credentials = SignedJwtAssertionCredentials(oc.client_email, oc.private_key, scope=['https://www.googleapis.com/auth/calendar', 'https://www.googleapis.com/auth/calendar.readonly'])
    http_auth = credentials.authorize(Http())

    #sqladmin = build('sqladmin', 'v1beta3', http=http_auth)
    calendar_admin = build('calendar', 'v3', http=http_auth)
    #response = sqladmin.instances().list(project='exciting-example-123').execute()
    lists = calendar_admin.calendarList().list().execute()
    pprint.pprint(lists)

    calendar_id= calendar_ids.main

    # get events from calendar for the next 3 days
    cest = pytz.timezone('Europe/Skopje')
    now = datetime.now(tz=cest) # timezone?
    timeMin = datetime(year=now.year, month=now.month, day=now.day, tzinfo=cest) + timedelta(days=1)
    timeMin = timeMin.isoformat()
    timeMax = datetime(year=now.year, month=now.month, day=now.day, tzinfo=cest) + timedelta(days=3)
    timeMax = timeMax.isoformat()

    events = calendar_admin.events().list(calendarId=calendar_id, timeMin=timeMin, timeMax=timeMax).execute()

    pprint.pprint(events)

    sys.exit(0)
    # Set up a Flow object to be used if we need to authenticate. This
    # sample uses OAuth 2.0, and we set up the OAuth2WebServerFlow with
    # the information it needs to authenticate. Note that it is called
    # the Web Server Flow, but it can also handle the flow for native
    # applications
    # The client_id and client_secret can be found in Google Developers Console
    FLOW = OAuth2WebServerFlow(
        client_id=oc.client_id,
        client_secret=oc.client_secret,
        scope='https://www.googleapis.com/auth/calendar',
        user_agent='YOUR_APPLICATION_NAME/YOUR_APPLICATION_VERSION')

    # To disable the local server feature, uncomment the following line:
    # FLAGS.auth_local_webserver = False

    # If the Credentials don't exist or are invalid, run through the native client
    # flow. The Storage object will ensure that if successful the good
    # Credentials will get written back to a file.
    storage = Storage('calendar.dat')
    credentials = storage.get()
    if credentials is None or credentials.invalid == True:
      credentials = run(FLOW, storage)

    # Create an httplib2.Http object to handle our HTTP requests and authorize it
    # with our good Credentials.
    http = httplib2.Http()
    http = credentials.authorize(http)

    # Build a service object for interacting with the API. Visit
    # the Google Developers Console
    # to get a developerKey for your own application.
    service = build(serviceName='calendar', version='v3', http=http, developerKey='YOUR_DEVELOPER_KEY')

