from datetime import date, datetime
import sys
import os.path
import pickle
from typing import Union
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request


class CalendarAPI:
    CREDS = None
    SCOPES = ['https://www.googleapis.com/auth/calendar']

    def __init__(self) -> None:

        if os.path.exists(sys.path[0] + '/token.pickle'):
            with open(sys.path[0] + '/token.pickle', 'rb') as token:
                self.CREDS = pickle.load(token)
        if not self.CREDS or not self.CREDS.valid:
            if self.CREDS and self.CREDS.expired and self.CREDS.refresh_token:
                self.CREDS.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(sys.path[0] +
                                                                 '/credentials.json', self.SCOPES)
                self.CREDS = flow.run_local_server(port=0)
            with open(sys.path[0] + '/token.pickle', 'wb') as token:
                pickle.dump(self.CREDS, token)

        self.SERVICE = build('calendar', 'v3', credentials=self.CREDS)

    def listCalendarsIds(self, pageToken=None, calendars={}) -> dict[str, str]:
        calendars_response = self.SERVICE.calendarList().list(
            pageToken=pageToken, maxResults=250).execute()

        for item in calendars_response['items']:
            calendars[item['summary'].lower()] = item['id']

        if 'nextPageToken' in calendars_response.keys():
            pageToken = calendars_response['nextPageToken']
            return self.listCalendarsIds(
                pageToken=pageToken, calendars=calendars)

        return calendars

    def listEvents(self, events: list, calendar_id: str, start_date: Union[datetime, date] = None, end_date: Union[datetime, date] = None, pageToken=None):

        current_timezone = datetime.now().astimezone().isoformat()[-6:]

        if start_date is not None:
            if type(start_date) is date:
                start_date_str = start_date.strftime('%Y-%m-%d') + 'T00:00:00' + current_timezone
            else:
                 start_date_str = start_date.strftime('%Y-%m-%dT%H:%M:%S%z')
                 start_date_str = start_date_str[:-2] + ':' + start_date_str[-2:]
        else:
            start_date_str = None

        if end_date is not None:
            if type(start_date) is date:
                end_date_str = end_date.strftime('%Y-%m-%d') + 'T00:00:00' + current_timezone
            else:
                end_date_str = end_date.strftime('%Y-%m-%dT%H:%M:%S%z')
                end_date_str = end_date_str[:-2] + ':' + end_date_str[-2:]
        else:
            end_date_str = None

        events_response = self.SERVICE.events().list(calendarId=calendar_id,
                                                     timeMin=start_date_str,
                                                     timeMax=end_date_str,
                                                     maxResults=2500,
                                                     pageToken=pageToken).execute()
        for item in events_response['items']:
            if 'summary' not in item.keys():
                item['summary'] = ''
            events.append(item)

        if 'nextPageToken' in events_response.keys():
            pageToken = events_response['nextPageToken']
            return self.listEvents(calendar_id=calendar_id, start_date=start_date, end_date=end_date,
                                   pageToken=pageToken, events=events)

        return events

    def addEvent(self, calendar_id, event_data):
        self.SERVICE.events().insert(calendarId=calendar_id, body=event_data).execute()
        print(f'Added event "{event_data["summary"]}" to calendar.')

    def removeEvent(self, calendar_id: str, event_data: dict):
        self.SERVICE.events().delete(calendarId=calendar_id,
                                     eventId=event_data['id']).execute()
        print(f'Removed event "{event_data["summary"]}" from calendar.')
