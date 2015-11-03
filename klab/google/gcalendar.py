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

import pprint
import copy
import time
import traceback
import json
import httplib2
from datetime import datetime, timedelta, date
import dateutil.parser

import pytz
from apiclient.discovery import build
from oauth2client.client import SignedJwtAssertionCredentials

from klab.general.structures import NestedBunch, NonStrictNestedBunch, DeepNonStrictNestedBunch
from klab.fs.fsio import read_file
from klab import colortext
from gauth import OAuthCredentials

class BasicEvent(object):

    def __init__(self, calendar_object, start_dt, end_dt, location = None, summary = None, description = None, visibility = 'default', email_map = {}, username_map = {}):
        '''start_dt should be a datetime.date object for all-day events or a datetime.datetime object for ranged events. Similarly for end_dt.' \
        '''
        e = {}
        self.timezone_string = calendar_object.timezone_string
        assert(visibility == 'default' or visibility == 'public' or visibility == 'private' or visibility == 'confidential')
        if isinstance(start_dt, date):
            e['start'] = {'date' : start_dt.isoformat(), 'timeZone' : self.timezone_string}
        else:
            assert(isinstance(start_dt, datetime))
            e['start'] = {'dateTime' : start_dt.isoformat(), 'timeZone' : self.timezone_string}
        if isinstance(end_dt, date):
            e['end'] = {'date' : end_dt.isoformat(), 'timeZone' : self.timezone_string}
        else:
            assert(isinstance(end_dt, datetime))
            e['end'] = {'dateTime' : end_dt.isoformat(), 'timeZone' : self.timezone_string}
        e['summary'] = summary
        e['description'] = description or summary
        e['location'] = location
        e['status'] = 'confirmed'
        self.email_map = email_map
        self.username_map = username_map
        self.event = e

    def initialize_tagged_copy(self):
        e = copy.deepcopy(self.event)
        e['extendedProperties'] = e.get('extendedProperties', {})
        e['extendedProperties']['shared'] = e['extendedProperties'].get('shared', {})
        assert(not(e['extendedProperties']['shared'].get('event_type')))
        return e


    # Main calendar


    def create_lab_meeting(self, event_type, presenters, foodie = None, locked = False):
        'Presenters can be a comma-separated list of presenters.'
        e = self.initialize_tagged_copy()
        summary_texts = {
            'Lab meeting' : 'Kortemme Lab meeting',
            'Kortemme/DeGrado joint meeting' : 'DeGrado/Kortemme labs joint meeting'
        }
        assert(summary_texts.get(event_type))
        e['extendedProperties']['shared']['event_type'] = event_type
        e['extendedProperties']['shared']['Presenters'] = presenters
        e['extendedProperties']['shared']['Food'] = foodie
        e['extendedProperties']['shared']['Locked meeting'] = locked
        print(presenters)
        print([[p for p in presenters.split(',')] + [foodie]])
        participants = [p.strip() for p in ([p for p in presenters.split(',')] + [foodie]) if p and p.strip()]
        participants = [p for p in [self.email_map.get(p) for p in participants] if p]
        participant_names = [self.username_map.get(p.strip(), p.strip()) for p in presenters.split(',') if p.strip()]
        if participants:
            e['extendedProperties']['shared']['ParticipantList'] = ','.join(participants)
        if not e['summary']:
            e['summary'] = '%s: %s' % (summary_texts[event_type], ', '.join(participant_names))
        e['description'] = e['description'] or e['summary']
        return e


    def create_journal_club_meeting(self, presenters, food_vendor, paper = None):
        'Presenters can be a comma-separated list of presenters.'
        e = self.initialize_tagged_copy()
        e['extendedProperties']['shared']['event_type'] = 'Journal club'
        e['extendedProperties']['shared']['Presenters'] = presenters
        e['extendedProperties']['shared']['Food vendor'] = food_vendor
        e['extendedProperties']['shared']['Paper'] = paper
        participants = [p.strip() for p in [p for p in presenters.split(',')] if p and p.strip()]
        participants = [p for p in [self.email_map.get(p) for p in participants] if p]
        participant_names = [self.username_map.get(p.strip(), p.strip()) for p in presenters.split(',') if p.strip()]
        if participants:
            e['extendedProperties']['shared']['ParticipantList'] = ','.join(participants)
        if not e['summary']:
            e['summary'] = 'Journal club: %s' % (', '.join(participant_names))
        e['description'] = e['description'] or e['summary']
        return e


    # Notices calendar


    def create_birthday(self, celebrant, caker):
        e = self.initialize_tagged_copy()
        e['summary'] # overwrite summary
        e['extendedProperties']['shared']['event_type'] = 'Birthday'
        e['extendedProperties']['shared']['Celebrant'] = celebrant
        e['extendedProperties']['shared']['Bringer Of CAKE!'] = caker
        participants = [p for p in [self.email_map.get(celebrant), self.email_map.get(caker)] if p]
        if participants:
            e['extendedProperties']['shared']['ParticipantList'] = ','.join(participants)
        e['summary'] = "%s's birthday" % self.username_map.get(celebrant, celebrant)
        e['description'] = e['summary']
        e['gadget'] = {
            'display' : 'icon',
            'iconLink' : 'https://guybrush.ucsf.edu/images/cake.png',
            'title' : e['summary'],
        }
        return e





class GoogleCalendar(object):
    ''' A class to interact with a set of Google calendars. This is used by our local lab website and by the meetings script.
        The class methods are split up following the API here:
            https://developers.google.com/resources/api-libraries/documentation/calendar/v3/python/latest/ '''


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
        self.timezone_string = 'America/Los_Angeles'
        self.timezone = pytz.timezone(self.timezone_string)
        self.configured_calendar_ids = configured_calendar_ids


    # Access control lists (acl)


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
        return DeepNonStrictNestedBunch(users)


    # Calendar list (calendarList)


    def get_calendars(self):
        calendars = []
        cl = self.service.calendarList().list().execute()
        for c in cl.get('items', []):
            nb = DeepNonStrictNestedBunch(c)
            calendars.append(nb)
        return calendars


    def get_calendar(self, calendar_id):
        return DeepNonStrictNestedBunch(self.service.calendarList().get(calendarId = self.configured_calendar_ids[calendar_id]).execute())


    # Calendar and event colors (colors)


    def get_colors(self):
        import pprint
        clrs = self.service.colors().get().execute()
        pprint.pprint(clrs)



    # Calendar events (events)

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
            # We do still want to return events in the next month if they fall within this week. Otherwise
            #if end_time.month != now.month:
            #    end_time = end_time - timedelta(days = end_time.day)
            #    end_time = datetime(year = end_time.year, month = end_time.month, day = end_time.day, hour=23, minute=59, second=59, tzinfo=self.timezone)
            #else:
            end_time = end_time + timedelta(seconds = -1)
            #end_time = datetime(year = end_time.year, month = end_time.month, day = end_time.day - 1, hour=23, minute=59, second=59, tzinfo=self.timezone)
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


    def get_event(self, calendar_id, event_id):
        event = self.service.events().get(calendarId = self.configured_calendar_ids[calendar_id], eventId=event_id).execute()
        nb = DeepNonStrictNestedBunch(event)
        dt = None
        if nb.start.dateTime:
            dt = dateutil.parser.parse(nb.start.dateTime)
        elif nb.start.date:
            dt = dateutil.parser.parse(nb.start.date)
            dt = datetime(year = dt.year, month = dt.month, day = dt.day, hour=0, minute=0, second=0, tzinfo=self.timezone)
        if dt:
            nb.datetime_o = dt
            nb.calendar_id = calendar_id
        return nb


    def get_events(self, start_time, end_time, ignore_cancelled = True, get_recurring_events_as_instances = True, restrict_to_calendars = []):
        '''A wrapper for events().list. Returns the events from the calendar within the specified times. Some of the interesting fields are:
                description, end, htmlLink, location, organizer, start, summary

                Note: "Cancelled instances of recurring events (but not the underlying recurring event) will still be included if showDeleted and singleEvents are both False."
        '''
        es = []
        calendar_ids = restrict_to_calendars or self.calendar_ids
        for calendar_id in calendar_ids:
            now = datetime.now(tz = self.timezone)
            events = []
            page_token = None
            while True:
                events = self.service.events().list(pageToken=page_token, maxResults = 250, calendarId = self.configured_calendar_ids[calendar_id], timeMin = start_time, timeMax = end_time, showDeleted = False).execute()
                for event in events['items']:
                    dt = None
                    nb = DeepNonStrictNestedBunch(event)
                    assert(not(nb._event))
                    nb._event = event # keep the original event as returned in case we want to reuse it e.g. insert it into another calendar
                    if (not ignore_cancelled) or (nb.status != 'cancelled'):
                        # Ignore cancelled events
                        if nb.recurrence:
                            if get_recurring_events_as_instances:
                                # Retrieve all occurrences of the recurring event within the timeframe
                                es += self.get_recurring_events(calendar_id, nb.id, start_time, end_time)
                            else:
                                es.append(nb)
                        elif nb.start.dateTime:
                            dt = dateutil.parser.parse(nb.start.dateTime)
                        elif nb.start.date:
                            dt = dateutil.parser.parse(nb.start.date)
                            dt = datetime(year = dt.year, month = dt.month, day = dt.day, hour=0, minute=0, second=0, tzinfo=self.timezone)
                        if dt:
                            nb.datetime_o = dt
                            nb.calendar_id = calendar_id
                            es.append(nb)
                page_token = events.get('nextPageToken')
                if not page_token:
                    break

        es.sort(key=lambda x: x.datetime_o)
        return es


    def get_recurring_events(self, calendar_id, event_id, start_time, end_time, maxResults = None):
        '''A wrapper for events().instances. Returns the list of recurring events for the given calendar alias within the specified timeframe.'''
        es = []
        page_token = None
        while True:
            events = self.service.events().instances(calendarId = self.configured_calendar_ids[calendar_id], eventId = event_id, pageToken=page_token, timeMin = start_time, timeMax = end_time, maxResults = maxResults, showDeleted = False).execute()
            for event in events['items']:
                dt = None
                nb = DeepNonStrictNestedBunch(event)
                assert(not(nb._event))
                nb._event = event # keep the original event as returned in case we want to reuse it e.g. insert it into another calendar
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


    # Administration
    #### Quarters and holiday creation: main calendar


    def add_company_quarter(self, company_name, quarter_name, dt, calendar_id = 'notices'):
        '''Adds a company_name quarter event to the calendar. dt should be a date object. Returns True if the event was added.'''

        assert(calendar_id in self.configured_calendar_ids.keys())
        calendarId = self.configured_calendar_ids[calendar_id]

        quarter_name = quarter_name.title()
        quarter_numbers = {
            'Spring' : 1,
            'Summer' : 2,
            'Fall' : 3,
            'Winter' : 4
        }
        assert(quarter_name in quarter_numbers.keys())

        start_time = datetime(year=dt.year, month=dt.month, day=dt.day, hour=0, minute=0, second=0, tzinfo=self.timezone) + timedelta(days = -1)
        end_time = start_time + timedelta(days = 3, seconds = -1)
        summary = '%s %s Quarter begins' % (company_name, quarter_name)

        # Do not add the quarter multiple times
        events = self.get_events(start_time.isoformat(), end_time.isoformat(), ignore_cancelled = True)
        for event in events:
            if event.summary.find(summary) != -1:
                return False

        event_body = {
            'summary' : summary,
            'description' : summary,
            'start' : {'date' : dt.isoformat(), 'timeZone' : self.timezone_string},
            'end' : {'date' : dt.isoformat(), 'timeZone' : self.timezone_string},
            'status' : 'confirmed',
            'gadget' : {
                'display' : 'icon',
                'iconLink' : 'https://guybrush.ucsf.edu/images/Q%d_32.png' % quarter_numbers[quarter_name],
                'title' : summary,
            },
            'extendedProperties' : {
                'shared' : {
                    'event_type' : '%s quarter' % company_name,
                    'quarter_name' : quarter_name
                }
            }
        }
        colortext.warning('\n%s\n' % pprint.pformat(event_body))
        created_event = self.service.events().insert(calendarId = self.configured_calendar_ids[calendar_id], body = event_body).execute()
        return True


    def add_holiday(self, start_dt, holiday_name, end_dt = None, calendar_id = 'notices'):
        '''Adds a holiday event to the calendar. start_dt and end_dt (if supplied) should be date objects. Returns True if the event was added.'''

        assert(calendar_id in self.configured_calendar_ids.keys())
        calendarId = self.configured_calendar_ids[calendar_id]

        # Note: end_date is one day ahead e.g. for the New Years' holiday Dec 31-Jan 1st, we specify the end_date as Jan 2nd. This is what the calendar expects.
        if not end_dt:
            end_dt = start_dt
        start_date = date(year=start_dt.year, month=start_dt.month, day=start_dt.day)#, tzinfo=self.timezone)
        end_date = date(year=end_dt.year, month=end_dt.month, day=end_dt.day) + timedelta(days = 1) #, tzinfo=self.timezone)
        start_time = datetime(year=start_dt.year, month=start_dt.month, day=start_dt.day, hour=0, minute=0, second=0, tzinfo=self.timezone) + timedelta(days = -1)
        end_time = datetime(year=end_dt.year, month=end_dt.month, day=end_dt.day, hour=23, minute=59, second=59, tzinfo=self.timezone) + timedelta(days = 2)

        # Do not add the quarter multiple times
        events = self.get_events((start_time + timedelta(days = -1)).isoformat(), (end_time + timedelta(days = 1)).isoformat(), ignore_cancelled = True)
        for event in events:
            if event.summary.find(holiday_name) != -1:
                return False

        event_body = {
            'summary' : holiday_name,
            'description' : holiday_name,
            'start' : {'date' : start_date.isoformat(), 'timeZone' : self.timezone_string},
            'end' : {'date' : end_date.isoformat(), 'timeZone' : self.timezone_string},
            'status' : 'confirmed',
            'extendedProperties' : {
                'shared' : {
                    'event_type' : 'Holiday'
                }
            }
        }
        if abs((end_date - start_date).days) > 7:
            raise Exception('The range of dates from {0} to {1} is greater than expected. Please check to make sure that the dates are correct.'.format(start_date, end_date))
        elif end_date < start_date:
            raise Exception('Error: The end date {1} occurs before the start date ({0}).'.format(start_date, end_date))

        created_event = self.service.events().insert(calendarId = self.configured_calendar_ids[calendar_id], body = event_body).execute()
        return True


    def remove_all_events(self, calendar_id):
        '''Removes all events from a calendar. WARNING: Be very careful using this.'''
        # todo: incomplete

        now = datetime.now(tz=self.timezone) # timezone?
        start_time = datetime(year=now.year - 1, month=now.month, day=now.day, hour=now.hour, minute=now.minute, second=now.second, tzinfo=self.timezone)
        end_time = datetime(year=now.year + 1, month=now.month, day=now.day, hour=now.hour, minute=now.minute, second=now.second, tzinfo=self.timezone)
        start_time = start_time.isoformat()
        end_time = end_time.isoformat()


        #events = self.service.events().list(calendarId = self.configured_calendar_ids[calendar_id], showDeleted = False).execute()
        events = self.service.events().list(calendarId = self.configured_calendar_ids[calendar_id], timeMin = start_time, timeMax = end_time, showDeleted = False).execute()

        print(len(events['items']))

        for event in events['items']:
            dt = None
            nb = DeepNonStrictNestedBunch(event)
            #print(event)
            if (nb.summary or nb.description or '').find('presentation') != -1:
                print(nb.id)
                print(nb.summary or nb.description)
                print(nb.start)


    #### Meetings creation: main calendar

    # Tag events. This is all that is needed for the Rosetta development and regular meetings
    def tag_event(self, calendar_id, event_id, extendedProperties):
        '''Add extendedProperties to a meeting. Warning: extendedProperties must contain only shared and private dicts and
           their contents will overwrite anything in the event's extendedProperties i.e. we do *not* deep-merge the dicts.
        '''
        event_body = self.service.events().get(calendarId = self.configured_calendar_ids[calendar_id], eventId=event_id).execute()
        event_body['extendedProperties'] = event_body.get('extendedProperties', {})
        event_body['extendedProperties']['shared'] = event_body['extendedProperties'].get('shared', {})
        event_body['extendedProperties']['private'] = event_body['extendedProperties'].get('private', {})
        assert(sorted(set(extendedProperties.keys()).union(set(['shared', 'private']))) == ['private', 'shared'])
        for k, v in extendedProperties['shared'].iteritems():
            event_body['extendedProperties']['shared'][k] = v
        for k, v in extendedProperties['private'].iteritems():
            event_body['extendedProperties']['private'][k] = v
        raise Exception('not tested yet')
        updated_event = self.service.events().update(calendarId = self.configured_calendar_ids[calendar_id], eventId = event_id, body = event_body).execute()


    # Lab meetings
    def add_lab_meeting(self, calendar_id, start_dt, end_dt, location, presenters, foodie, summary = None, description = None, visibility = 'default', username_map = {}, email_map = {}):
        e = BasicEvent(self, start_dt, end_dt, location = location, summary = summary, description = description, visibility = visibility, username_map = username_map, email_map = email_map)
        event = e.create_lab_meeting('Lab meeting', presenters, foodie)
        colortext.warning(pprint.pformat(event))


    # Journal club meetings
    def add_journal_club_meeting(self, calendar_id, start_dt, end_dt, location, presenters, food_vendor, paper = None, summary = None, description = None, visibility = 'default', username_map = {}, email_map = {}):
        e = BasicEvent(self, start_dt, end_dt, location = location, summary = summary, description = description, visibility = visibility, username_map = username_map, email_map = email_map)
        event = e.create_journal_club_meeting(presenters, food_vendor, paper = paper)
        colortext.warning(pprint.pformat(event))


    # Kortemme/DeGrado labs joint meetings
    def add_kortemme_degrado_joint_meeting(self, calendar_id, start_dt, end_dt, location, presenters, summary = None, description = None, visibility = 'default', username_map = {}, email_map = {}):
        e = BasicEvent(self, start_dt, end_dt, location = location, summary = summary, description = description, visibility = visibility, username_map = username_map, email_map = email_map)
        event = e.create_lab_meeting('Kortemme/DeGrado joint meeting', presenters, locked = True)
        colortext.warning(pprint.pformat(event))


    #### Meetings creation: notices calendar


    def add_birthday(self, start_dt, end_dt, location, celebrant, caker, summary = None, description = None, visibility = 'default', username_map = {}, email_map = {}, calendar_id = 'notices'):
        e = BasicEvent(self, start_dt, end_dt, location = location, summary = summary, description = description, visibility = visibility, username_map = username_map, email_map = email_map)
        event_body = e.create_birthday(celebrant, caker)
        created_event = self.service.events().insert(calendarId = self.configured_calendar_ids[calendar_id], body = event_body).execute()
        return created_event

    # Deprecated - remove these when we switch over to the new system

    # Getters, deleters
    def getAllEvents(self, calendar_id, year = None, month = None):
        # See note above for query parameters

        #query = gdata.calendar.client.CalendarEventQuery()
        #query.max_results = 2**31-1
        #query.singleevents = "true"
        start_time = None
        end_time = None
        if year:
            if month and (type(month) == type(1)) and month >= 1 and month <=12:
                start_time = "%d-%d-01T00:00:00-08:00" % (year, month)
                end_time = "%d-%d-31T23:59:00-08:00" % (year, month)
            else:
                start_time = "%d-01-01T00:00:00-08:00" % year
                end_time = "%d-12-31T23:59:00-08:00" % year

        events = self.service.events().list(
            calendarId = self.configured_calendar_ids[calendar_id],
            timeMin = start_time,
            timeMax = end_time,
            singleEvents = True,
            maxResults = 2**31-1,
            showDeleted = False).execute()

        #print(query, self.URI)
        #feed = self.client.GetCalendarEventFeed(q=query, uri = self.URI)

        #events = []
        #for event in events:
        #    events.append(event)
        #    eventIDText = event.id.text
        #    eventEditURL = event.GetEditLink().href
        #    eventHTMLURL = event.GetHtmlLink().href
        return events.get('items')



    def getEventsTable(self, calendar_id, year = None, month = None):
        eventstbl = {}
        events = self.getAllEvents(calendar_id, year, month)
        for event in events:
            event = DeepNonStrictNestedBunch (event)
            if event.start and event.location and event.status != 'cancelled':
                EventTitle = event.summary

                if event.start.get('dateTime'):
                    startdate = event.start['dateTime']
                    startdate = time.strptime(startdate[0:19], '%Y-%m-%dT%H:%M:%S')
                    startdate = datetime.fromtimestamp(time.mktime(startdate))
                elif event.start.get('date'):
                    startdate = event.start['date']
                    startdate = time.strptime(startdate, '%Y-%m-%d')
                    startdate = datetime.fromtimestamp(time.mktime(startdate))
                else:
                    raise Exception('Cannot determine start date.')
                if event.end.get('dateTime'):
                    enddate = event.end['dateTime']
                    enddate = time.strptime(enddate[0:19], '%Y-%m-%dT%H:%M:%S')
                    enddate = datetime.fromtimestamp(time.mktime(enddate))
                elif event.end.get('date'):
                    enddate = event.end['date']
                    enddate = time.strptime(enddate, '%Y-%m-%d')
                    enddate = datetime.fromtimestamp(time.mktime(enddate))
                else:
                    raise Exception('Cannot determine end date.')

                isBirthday = EventTitle.find("birthday") != -1

                location = event.get('location')
                eventstbl[(startdate, EventTitle)] = {"event": event, "enddate" : enddate, "location" : location, "title" : EventTitle}
        #for k in sorted(eventstbl.keys()):
        #	print(k, eventstbl[k]["title"])
        return eventstbl

    def updateEvents(self, calendar_id, newEvents):
        currentEvents = self.getEventsTable(calendar_id)

        #colortext.message(newEvents)
        #colortext.warning(currentEvents)

        # Events to remove
        toRemove = []
        for startdateTitle, event in sorted(currentEvents.iteritems()):
            if event["title"].find("birthday") != -1:
                # Don't remove birthdays
                continue
            if newEvents.get(startdateTitle):
                newEvent = newEvents[startdateTitle]
                if newEvent["enddate"] == event["enddate"]:
                    if event["location"].startswith(newEvent["location"]):
                        if str(newEvent["title"]) == str(event["title"]):
                            # Don't remove events which are in both newEvents and the calendar
                            continue

            # Remove events which are on the calendar but not in newEvents
            toRemove.append(startdateTitle)

        # Events to add
        toAdd = []
        for startdateTitle, event in sorted(newEvents.iteritems()):
            if currentEvents.get(startdateTitle):
                currentEvent = currentEvents[startdateTitle]
                if currentEvent["enddate"] == event["enddate"]:
                    if currentEvent["location"].startswith(event["location"]):
                        if str(currentEvent["title"]) == str(event["title"]):
                            # Don't add events which are in both newEvents and the calendar
                            continue
            # Add events which are in newEvents but not on the calendar
            toAdd.append(startdateTitle)

        if toRemove:
            colortext.error("Removing these %d events:" % len(toRemove))
            for dtTitle in toRemove:
                colortext.warning(dtTitle)
                self.removeEvent(calendar_id, currentEvents[dtTitle]["event"].id)

        if toAdd:
            colortext.message("Adding these %d events:" % len(toAdd))
            for dtTitle in toAdd:
                newEvent = newEvents[dtTitle]
                #print(dtTitle, newEvent)
                self.addNewEvent(calendar_id, dtTitle[0], newEvent["enddate"], newEvent["location"], newEvent["title"])

    def removeEvent(self, calendar_id, event_id):
        for i in range(3):
            try:
                assert(self.service.events().get(calendarId = self.configured_calendar_ids[calendar_id], eventId = event_id).execute())
                self.service.events().delete(calendarId = self.configured_calendar_ids[calendar_id], eventId = event_id).execute()
                break
            except Exception, e:
                colortext.error("An error occurred:")
                colortext.error(e)
                colortext.error("Trying again.")
                time.sleep(2)

    def addNewEvent(self, calendar_id, startdate, enddate, location, title):
        colortext.message("\nAdding %s on %s at %s" % (title, startdate, location))

        #start_time = startdate.strftime('%Y-%m-%dT%H:%M:%S').isoformat()
        #end_time =	 enddate.strftime('%Y-%m-%dT%H:%M:%S').isoformat()
        start_time = startdate.isoformat()
        end_time =	 enddate.isoformat()

        loc = location
        if loc.startswith("Tahoe"):
            loc = "%s, 10 minutes outside Truckee, CA @ 39.328455,-120.184078" % loc
        else:
            if location.startswith("BH "):
                loc = "%s, Byers Hall" % loc
            loc = "%s, removeEvent/Mission Bay, San Francisco, CA @ 37.767952,-122.392214" % loc

        for i in range(3):
            try:
                self.service.events().insert(
                    calendarId = self.configured_calendar_ids[calendar_id],
                    body = {
                        "start" : {
                            "timeZone" : self.timezone_string,
                            "dateTime" : start_time,
                        },
                        "end" : {
                            "timeZone" : self.timezone_string,
                            "dateTime" : end_time,
                        },
                        "location" : loc,
                        "summary" : title,
                        "description" : title
                    }).execute()
                break
            except Exception, e:
                colortext.error("An error occurred:")
                colortext.error(traceback.format_exc())
                colortext.error(e)
                colortext.error("Trying again.")
                time.sleep(2)


    ### Birthdays - rewrite these functions

    def add_bidet(self):
        raise Exception('update')
        main_calendar = GoogleCalendar.from_file('/admin/calendars.json', ['main'])
        notices_calendar = GoogleCalendar.from_file('/admin/calendars.json', ['notices'])
        timezone = main_calendar.timezone
        event_ids = set()
        seen_notices = set()
        for year in range(2014, 2017):
        #for year in range(2014, 2015):
            colortext.message('\n\nTagging events in %d:\n' % year)
            extra_days = 0
            if year % 4 == 0:
                extra_days = 1
            start_time = datetime(year=year, month=1, day=1, hour=0, minute=0, second=0, tzinfo=timezone)
            end_time = start_time + timedelta(days = 730 + extra_days, seconds = -1)
            start_time, end_time = start_time.isoformat(), end_time.isoformat()

            #main_meetings = main_calendar.get_events(start_time, end_time, ignore_cancelled = True, get_recurring_events_as_instances = False)
            #for m in main_meetings:
            #    if m.extendedProperties.shared:
            #        event_type = m.extendedProperties.shared['event_type']
            #        if event_type == 'Birthday'

            notices = notices_calendar.get_events(start_time, end_time, ignore_cancelled = True, get_recurring_events_as_instances = False)
            for n in notices:
                if n.id in seen_notices:
                    continue
                seen_notices.add(n.id)
                if n.extendedProperties.shared and n.extendedProperties.shared.event_type:
                    event_type = n.extendedProperties.shared['event_type']
                    if event_type == 'Birthday':
                        print(n.summary, n.id)
                        print(n.start)
                        event_body = main_calendar.service.events().get(calendarId = main_calendar.configured_calendar_ids["notices"], eventId=n.id).execute()
                        event_body['gadget'] = {
                            'display' : 'icon',
                            'iconLink' : 'https://guybrush.ucsf.edu/images/cake.png',
                            'title' : n.summary,
                            #'type' : 'application/x-google-gadgets+xml',
                        }
                        created_event = main_calendar.service.events().update(calendarId = main_calendar.configured_calendar_ids["notices"], eventId = n.id, body = event_body).execute()



    def updateBirthdays(self, bdays):
        raise Exception('update')
        eventstbl = self.getEventsTable("main")
        for dt, details in sorted(bdays.iteritems()):
            bdaykey = datetime(dt.year, dt.month, dt.day)
            if eventstbl.get((bdaykey, details["title"])):
                if str(eventstbl[(bdaykey, details["title"])]["title"]) == str(details["title"]):
                    continue
            colortext.message("adding " + details["title"])
            self.addBirthday(dt, details["title"], details["location"])

    def addBirthday(self, dt, title, location):
        raise Exception('update')
        #if recurrence_data is None:
        #  recurrence_data = ('DTSTART;VALUE=DATE:20070501\r\n'
        #	+ 'DTEND;VALUE=DATE:20070502\r\n'
        #	+ 'RRULE:FREQ=WEEKLY;BYDAY=Tu;UNTIL=20070904\r\n')
        raise Exception('add this functionality')
        dtstart ="DATE:%d%0.2d%0.2dT070000" % (dt.year, dt.month, dt.day)
        dtend ="DATE:%d%0.2d%0.2dT235900" % (dt.year, dt.month, dt.day)
        untildt ="%d%0.2d%0.2d" % (dt.year + 10, dt.month, dt.day)

        recurrence_data = ('DTSTART;VALUE=%s\r\n' % dtstart) + ('DTEND;VALUE=%s\r\n' % dtend) + ('RRULE:FREQ=YEARLY;UNTIL=%s\r\n' % untildt)

        event = gdata.calendar.data.CalendarEventEntry()
        event.title = atom.data.Title(text=title)
        event.content = atom.data.Content(text=title)
        event.where.append(gdata.calendar.data.CalendarWhere(value=location))

        # Set a recurring event
        event.recurrence = gdata.data.Recurrence(text=recurrence_data)
        self.addEvent(event)

    # Utility functions
    def printAllEvents(self, calendar_id, year = None):
        colortext.message('Events on Calendar: %s' % (self.get_calendar(calendar_id).summary))
        eventstbl = self.getEventsTable(calendar_id, year)
        for startdateTitle, details in sorted(eventstbl.iteritems()):
            startdate = startdateTitle[0]
            print(("%s -> %s at %s: %s" % (startdate, details["enddate"], details["location"][0:details["location"].find("@")], details["title"])).encode('ascii', 'ignore'))




    def remove_all_cancelled_events(self, calendar_ids = []):

        for calendar_id in calendar_ids or self.calendar_ids:
            colortext.message('Removing cancelled events in %s' % calendar_id)
            events = self.service.events().list(calendarId = self.configured_calendar_ids[calendar_id]).execute()
            print(len(events['items']))

            for event in events['items']:
                dt = None
                nb = DeepNonStrictNestedBunch(event)
                if nb.status == 'cancelled':
                    if nb.recurringEventId:
                        colortext.warning(nb.recurringEventId)
                        # Retrieve all occurrences of the recurring event within the timeframe
                        start_time = datetime(year=2010, month=1, day=1, tzinfo=self.timezone).isoformat()
                        end_time = datetime(year=2015, month=1, day=1, tzinfo=self.timezone).isoformat()
                        for e in self.get_recurring_events(calendar_id, nb.id, start_time, end_time, maxResults = 10):
                            print(e)
                    else:
                        colortext.warning(nb)


if __name__ == '__main__':
    import pprint
    gc = GoogleCalendar.from_file('test.json', ['main', 'rosetta_dev', 'regular_meetings', 'vacations'])

    tests = ['events']
    #'admin'
    # acl
    if 'acl' in tests:
        gc.get_calendar_users('main')

    # calendarList
    if 'calendarList' in tests:
        gc.get_calendars()
        v = gc.get_calendar('vacations')
        colortext.message('Description: %s' % v.description)
        colortext.warning('Role: %s' % v.accessRole)
        colortext.warning('Time zone: %s' % v.timeZone)

    # colors
    if 'colors' in tests:
        gc.get_colors()

    # events
    if 'events' in tests:
        for evnt in gc.get_upcoming_events_within_the_current_month():
            pass
            #print(evnt.datetime_o, evnt.description, evnt.location)

        colortext.warning('***')
        for evnt in gc.get_events_within_a_given_month(2014, 12):
            pass
            #print(evnt)
            #colortext.warning('%s, %s, %s' % (evnt.datetime_o, evnt.description or evnt.summary, evnt.location))

        colortext.warning('***')

        todays_events, this_weeks_events, this_months_events = gc.get_upcoming_event_lists_for_the_remainder_of_the_month(year = 2014, month = 12)
        sys.exit(0)
        colortext.warning("*** Today's events ***")
        for evnt in todays_events:
            print(evnt.datetime_o, evnt.description, evnt.location)
        colortext.warning("*** This week's events ***")
        for evnt in this_weeks_events:
            print(evnt.datetime_o, evnt.description, evnt.location)
        colortext.warning("*** This month's events ***")
        for evnt in this_months_events:
            print(evnt.datetime_o, evnt.description, evnt.location)

    # admin
    if 'admin' in tests:
        gc.remove_all_cancelled_events()

