#!/usr/bin/python
# encoding: utf-8
"""
gcalendar.py
Google Calendar functionality.

Created by Shane O'Connor 2014
"""

if __name__ == '__main__':
    import sys
    sys.path.insert(0, '../..')

#from oauth2client.client import OAuth2WebServerFlow

import json
import httplib2
import pprint
from datetime import datetime, timedelta
import dateutil.parser

import pytz
from apiclient.discovery import build
from oauth2client.client import SignedJwtAssertionCredentials

from tools.general.structures import NestedBunch, NonStrictNestedBunch, DeepNonStrictNestedBunch
from tools.fs.fsio import read_file
from tools import colortext


class OAuthCredentials(NestedBunch):

    @staticmethod
    def from_JSON(oauth_json, type = "service"):
        '''At the time of writing, keys include:
            client_secret, client_email, redirect_uris (list), client_x509_cert_url, client_id, javascript_origins (list)
            auth_provider_x509_cert_url, auth_uri, token_uri.'''
        assert(type == "service" or type == "web")
        return NestedBunch(json.loads(oauth_json)[type])


class GoogleCalendar(object):


    @staticmethod
    def from_file(oauth_json_filepath, calendar_id):
        return GoogleCalendar(read_file(oauth_json_filepath), calendar_id)


    def __init__(self, oauth_json, calendar_ids):
        '''oauth_json is a JSON string which should contain login credentials for OAuth 2.0.
           calendar_ids is a list of calendar aliases to connect to and should be defined in oauth_json["calendars"].
           We use calendar aliases e.g. "main" or "biosensor meetings" for convenience.
        '''
        oc = OAuthCredentials.from_JSON(oauth_json)
        configured_calendar_ids = NestedBunch.from_JSON(oauth_json).calendars
        for calendar_id in calendar_ids:
            assert(calendar_id in configured_calendar_ids.keys())
        self.calendar_ids = calendar_ids

        # Request both read/write (calendar) and read-only access (calendar.readonly)
        credentials = SignedJwtAssertionCredentials(oc.client_email, oc.private_key, scope=['https://www.googleapis.com/auth/calendar', 'https://www.googleapis.com/auth/calendar.readonly'])
        http_auth = credentials.authorize(httplib2.Http())

        # Create a service object for the Google Calendar v3 API
        self.service = build('calendar', 'v3', http = http_auth)
        self.timezone = pytz.timezone('America/Los_Angeles')
        self.configured_calendar_ids = configured_calendar_ids


    def get_upcoming_events_in_the_next_month(self):
        return self.get_upcoming_events(31)


    def get_upcoming_events_in_the_next_week(self):
        return self.get_upcoming_events(7)


    def get_upcoming_events_for_today(self):
        return self.get_upcoming_events(1)


    def get_upcoming_events(self, days_to_look_ahead):
        '''Returns the events from the calendar for the next days_to_look_ahead days.'''
        now = datetime.now(tz=self.timezone) # timezone?
        start_time = datetime(year=now.year, month=now.month, day=now.day, hour=now.hour, minute=now.minute, second=now.second, tzinfo=self.timezone)
        end_time = start_time + timedelta(days = days_to_look_ahead)
        start_time = start_time.isoformat()
        end_time = end_time.isoformat()
        return self.get_events(start_time, end_time)


    def get_events(self, start_time, end_time):
        '''Returns the events from the calendar within the specified times. Some of the interesting fields are:
               description, end, htmlLink, location, organizer, start, summary
        '''
        es = []
        for calendar_id in self.calendar_ids:
            now = datetime.now(tz = self.timezone)
            events = self.service.events().list(calendarId = self.configured_calendar_ids[calendar_id], timeMin = start_time, timeMax = end_time).execute()
            for event in events['items']:
                dt = None
                nb = DeepNonStrictNestedBunch(event)
                if nb.status != 'cancelled':
                    # Ignore cancelled events
                    if nb.recurrence:
                        # Retrieve all occurrences of the recurring event within the timeframe
                        es += self.get_recurring_events(start_time, end_time, calendar_id, nb.id)
                    else:
                        dt = dateutil.parser.parse(nb.start.dateTime)

                    if dt:
                        nb.datetime_o = dt
                        nb.calendar_id = calendar_id
                        es.append(nb)
        es.sort(key=lambda x: x.datetime_o)
        return es


    def get_recurring_events(self, start_time, end_time, calendar_id, event_id):
        '''Returns the list of recurring events for the given calendar alias within the specified timeframe.'''
        es = []
        page_token = None
        while True:
            events = self.service.events().instances(calendarId = self.configured_calendar_ids[calendar_id], eventId = event_id, pageToken=page_token, timeMin = start_time, timeMax = end_time).execute()
            for event in events['items']:
                dt = None
                nb = DeepNonStrictNestedBunch(event)
                if nb.start.date:
                    dt = dateutil.parser.parse(nb.start.date + 'T00:00:00-08:00')
                elif nb.start.dateTime:
                    dt = dateutil.parser.parse(nb.start.dateTime)
                nb.datetime_o = dt
                nb.calendar_id = calendar_id
                es.append(nb)
            page_token = events.get('nextPageToken')
            if not page_token:
                break
        return es


if __name__ == '__main__':
    gc = GoogleCalendar.from_file('test.json', ['main', 'rosetta_dev'])
    for evnt in gc.get_upcoming_events_in_the_next_month():
        print(evnt.datetime_o, evnt.description, evnt.location)




