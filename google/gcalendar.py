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

import time
import traceback
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
        '''A wrapper for events().list. Returns the events from the calendar within the specified times. Some of the interesting fields are:
                description, end, htmlLink, location, organizer, start, summary

                Note: "Cancelled instances of recurring events (but not the underlying recurring event) will still be included if showDeleted and singleEvents are both False."
        '''
        es = []
        for calendar_id in self.calendar_ids:
            now = datetime.now(tz = self.timezone)
            events = self.service.events().list(calendarId = self.configured_calendar_ids[calendar_id], timeMin = start_time, timeMax = end_time, showDeleted = False).execute()
            for event in events['items']:
                dt = None
                nb = DeepNonStrictNestedBunch(event)
                if nb.status != 'cancelled':
                    # Ignore cancelled events
                    if nb.recurrence:
                        # Retrieve all occurrences of the recurring event within the timeframe
                        es += self.get_recurring_events(calendar_id, nb.id, start_time, end_time)
                    elif nb.start.dateTime:
                        dt = dateutil.parser.parse(nb.start.dateTime)
                    elif nb.start.date:
                        dt = dateutil.parser.parse(nb.start.date)
                        dt = datetime(year = dt.year, month = dt.month, day = dt.day, hour=0, minute=0, second=0, tzinfo=self.timezone)
                    if dt:
                        nb.datetime_o = dt
                        nb.calendar_id = calendar_id
                        es.append(nb)
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

    def remove_all_events(self, calendar_id):
        '''Removes all events from a calendar. WARNING: Be very careful using this.'''

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

    def updateBirthdays(self, bdays):
        eventstbl = self.getEventsTable("main")
        for dt, details in sorted(bdays.iteritems()):
            bdaykey = datetime(dt.year, dt.month, dt.day)
            if eventstbl.get((bdaykey, details["title"])):
                if str(eventstbl[(bdaykey, details["title"])]["title"]) == str(details["title"]):
                    continue
            colortext.message("adding " + details["title"])
            self.addBirthday(dt, details["title"], details["location"])

    def addBirthday(self, dt, title, location):
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

