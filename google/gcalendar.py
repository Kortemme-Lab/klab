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

import json
import httplib2
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
    def from_file(oauth_json_filepath, calendar_ids):
        return GoogleCalendar(read_file(oauth_json_filepath), calendar_ids)


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

    # ACL

    def get_acl_list(self, calendar_id):
        return self.service.acl().list(calendarId = self.configured_calendar_ids[calendar_id]).execute() # note: not using pagination here yet

    def get_calendar_users(self, calendar_id):
        users = {}
        acl_list = self.get_acl_list(calendar_id)
        if acl_list:
            for item in acl_list['items']:
                nb = DeepNonStrictNestedBunch(item)
                users[nb.role]= users.get(nb.role, [])
                if nb.scope.type == 'user':
                    if nb.scope.value.find('@group.calendar.google.com') == -1 and nb.scope.value.find('@developer.gserviceaccount.com') == -1:
                        users[nb.role].append(nb.scope.value)
                users[nb.role] = sorted(users[nb.role])
        nb = DeepNonStrictNestedBunch(users)
        import pprint
        pprint.pprint(users)


    # EVENTS

    def get_events_within_a_given_month(self, year, month, day = 1, hour = 0, minute = 0, second = 0):
        now = datetime.now(tz=self.timezone) # timezone?
        start_time = datetime(year=year, month=month, day=day, hour=hour, minute=minute, second=second, tzinfo=self.timezone)
        if start_time.month == 12:
            end_time = datetime(year = start_time.year, month = 12, day = 31, hour=23, minute=59, second=59, tzinfo=self.timezone)
        else:
            end_time = datetime(year = start_time.year, month = start_time.month + 1, day = 1, hour=0, minute=0, second=0, tzinfo=self.timezone)
            end_time = end_time - timedelta(seconds = 1)
        start_time = start_time.isoformat()
        end_time = end_time.isoformat()
        return self.get_events(start_time, end_time)


    def get_upcoming_events_within_the_current_month(self):
        now = datetime.now(tz=self.timezone) # timezone?
        return self.get_events_within_a_given_month(now.year, now.month, day = now.day, hour = now.hour, minute = now.minute, second = now.second)


    def get_upcoming_event_lists_for_the_remainder_of_the_month(self, year = None, month = None):
        '''Return the set of events as triple of (today's events, events for the remainder of the week, events for the remainder of the month).'''

        events = []
        if year == None and month == None:
            now = datetime.now(tz=self.timezone) # timezone?
        else:
            now = datetime(year=year, month=month, day=1, hour=0, minute=0, second=0, tzinfo=self.timezone)

        # Get today's events, including past events
        start_time = datetime(year=now.year, month=now.month, day=now.day, hour=0, minute=0, second=0, tzinfo=self.timezone)
        end_time = datetime(year = start_time.year, month = start_time.month, day = start_time.day, hour=23, minute=59, second=59, tzinfo=self.timezone)
        events.append(self.get_events(start_time.isoformat(), end_time.isoformat()))

        # Get this week's events
        if now.weekday() < 6:
            start_time = datetime(year=now.year, month=now.month, day=now.day + 1, hour=0, minute=0, second=0, tzinfo=self.timezone)
            end_time = start_time + timedelta(days = 6 - now.weekday())
            if end_time.month > now.month:
                # We do not want to return events in the next month
                end_time = end_time - timedelta(days = end_time.day)
                end_time = datetime(year = end_time.year, month = end_time.month, day = end_time.day, hour=23, minute=59, second=59, tzinfo=self.timezone)
            else:
                end_time = datetime(year = end_time.year, month = end_time.month, day = end_time.day - 1, hour=23, minute=59, second=59, tzinfo=self.timezone)
            events.append(self.get_events(start_time.isoformat(), end_time.isoformat()))
        else:
            events.append([])

        # Get this remaining events in the month
        start_time = end_time + timedelta(seconds = 1)
        if start_time.month == now.month:
            if now.month == 12:
                end_time = datetime(year = start_time.year, month = 12, day = 31, hour=23, minute=59, second=59, tzinfo=self.timezone)
            else:
                end_time = datetime(year = start_time.year, month = start_time.month + 1, day = 1, hour=0, minute=0, second=0, tzinfo=self.timezone)
                end_time = end_time - timedelta(seconds = 1)
            events.append(self.get_events(start_time.isoformat(), end_time.isoformat()))
        else:
            events.append([])

        return events


    def get_upcoming_events_within_the_current_week(self):
        '''Returns the events from the calendar for the next days_to_look_ahead days.'''
        now = datetime.now(tz=self.timezone) # timezone?
        start_time = datetime(year=now.year, month=now.month, day=now.day, hour=now.hour, minute=now.minute, second=now.second, tzinfo=self.timezone)
        end_time = start_time + timedelta(days = 6 - now.weekday())
        end_time = datetime(year = end_time.year, month = end_time.month, day = end_time.day, hour=23, minute=59, second=59, tzinfo=self.timezone)
        assert(end_time.weekday() == 6)
        start_time = start_time.isoformat()
        end_time = end_time.isoformat()
        return self.get_events(start_time, end_time)


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

    gc.get_calendar_users('main')
    sys.exit(0)

    # Events
    for evnt in gc.get_upcoming_events_within_the_current_month():
        print(evnt.datetime_o, evnt.description, evnt.location)

    colortext.warning('***')
    for evnt in gc.get_events_within_a_given_month(2014, 12):
        print(evnt.datetime_o, evnt.description, evnt.location)

    colortext.warning('***')

    todays_events, this_weeks_events, this_months_events = gc.get_upcoming_event_lists_for_the_remainder_of_the_month(year = 2014, month = 12)

    colortext.warning("*** Today's events ***")
    for evnt in todays_events:
        print(evnt.datetime_o, evnt.description, evnt.location)
    colortext.warning("*** This week's events ***")
    for evnt in this_weeks_events:
        print(evnt.datetime_o, evnt.description, evnt.location)
    colortext.warning("*** This month's events ***")
    for evnt in this_months_events:
        print(evnt.datetime_o, evnt.description, evnt.location)



