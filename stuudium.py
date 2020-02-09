from __future__ import print_function
import datetime
import pickle
import os.path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from anydo_api.client import Client
from anydo_api.task import Task
from bs4 import BeautifulSoup
import bs4
import requests
from requests_html import HTMLSession


def remove_items(items, category):
    for tsk in category.tasks():
        if not any(tsk.title == item.text for item in items):
            print(tsk.title)
            tsk.destroy()


def add_items(items, input_user, category):
    for item in items:
        if item.checked:
            check = "CHECKED"
        else:
            check = ""
        if not any(obj.title == item.text for obj in category.tasks()):
            print(item.text)
            if item.test:
                priority = "High"
                y = item.date[:-4]
                d = item.date[-2:]
                m = item.date[-4:-2]
                due = "-".join([y, m, d])
                event = {
                    'summary': item.text,
                    'start': {
                        'date': due,
                        'timeZone': 'EET'
                    },
                    'end': {
                        'date': due,
                        'timeZone': 'EET'
                    },
                    'reminders': {
                        'useDefault': False,
                        'overrides': [
                        ]
                    }
                }
                service.events().insert(calendarId='primary', body=event).execute()
            else:
                priority = "Low"
            tsk = Task.create(
                status=check,
                user=input_user,
                title=item.text,
                priority=priority,
                category='School',
                repeatingMethod='TASK_REPEAT_OFF',
                alert=alert,
                dueDate=item.dateInTicks * 1000)
            category.add_task(tsk)


class HomeWork:
    def __init__(self, text, check, is_test, duedate, due):
        self.text = text
        self.checked = check
        self.test = is_test
        self.dateInTicks = duedate
        self.date = due


login_url = "https://nrg.ope.ee/auth/"
timetable_url = "https://nrg.edupage.org/timetable/"
message_url = "https://nrg.ope.ee/suhtlus/api/channels/updates/a/inbox?merge_events=1&get_post_membership_data=1"
data = {"data[User][username]": "Marcusb2kl@gmail.com",
        "data[User][password]": "678M5cFq1u3I"}
headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'}
session = requests.session()
main_page = session.post(login_url, data)
html = BeautifulSoup(main_page.text, features="html.parser")
divs = html.findAll('div', {'class': 'todo_container'})
Tasks = []
for div in divs:
    dateInTick = int(div.attrs['data-date_ts'])
    date = div.attrs['data-date']
    subject = div.find('a', {"class": "subject_name"})
    checked = 'is_marked' in div.attrs['class']
    if subject is not None:
        subject = subject.text + " "
    else:
        subject = ""
    test = not div.find('span', {"class": "test_indicator"}) is None
    task = div.find('span', {"class": "todo_content"})
    if task is not None:
        task = "".join([str(a) if type(a) is bs4.element.NavigableString else a.attrs['href'] if 'href' in a.attrs.keys() else "" for a in task.contents])
        if test:
            task = subject + "Kontrolltöö " + task
        else:
            task = subject + task
    else:
        if test:
            task = subject + "Kontrolltöö"
        else:
            task = subject.strip()
    task = task.strip()
    homework = HomeWork(task, checked, test, dateInTick,date)
    Tasks.append(homework)
alert = {'offset': 0, 'repeatEndsAfterOccurrences': -1, 'repeatStartsOn': None, 'repeatMonthType': 'ON_DATE',
         'repeatDays': '0000000', 'type': 'NONE', 'customTime': 0, 'repeatNextOccurrence': None,
         'repeatEndType': 'REPEAT_END_NEVER', 'repeatEndsOn': None, 'repeatInterval': 1}

#user = Client(email='marcusb2kl@gmail.com', password='Bindevald16').get_user()
#categories = list(map(lambda category: category['name'], user.categories(refresh=True)))
#chosen_category = user.categories()[categories.index("School")]
SCOPES = ['https://www.googleapis.com/auth/calendar']
creds = None
if os.path.exists('token.pickle'):
    with open('token.pickle', 'rb') as token:
        creds = pickle.load(token)
if not creds or not creds.valid:
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
    else:
        flow = InstalledAppFlow.from_client_secrets_file(
            'credentials.json', SCOPES)
        creds = flow.run_local_server(port=0)
    with open('token.pickle', 'wb') as token:
        pickle.dump(creds, token)
service = build('calendar', 'v3', credentials=creds)
#add_items(Tasks, user, chosen_category)
#remove_items(Tasks, chosen_category)
session = HTMLSession()
r = session.get(timetable_url)
r.html.render()
html = [element.text for element in r.html.find('g')]
print(r.text)

