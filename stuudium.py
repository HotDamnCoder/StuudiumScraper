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
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import time
import datetime


class HomeWork:
    def __init__(self, text, check, is_test, duedate, due):
        self.text = text
        self.checked = check
        self.test = is_test
        self.dateInTicks = duedate
        self.date = due


def get_homework(source):
    source = BeautifulSoup(source.text, features="html.parser").findAll('div', {'class': 'todo_container'})
    tasks = []
    for div in source:
        date_in_tick = int(div.attrs['data-date_ts'])
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
            task = "".join([str(a) if type(a) is bs4.element.NavigableString else a.attrs[
                'href'] if 'href' in a.attrs.keys() else "" for a in task.contents])
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
        homework = HomeWork(task, checked, test, date_in_tick, date)
        tasks.append(homework)
    return tasks


def remove_items(items, category):
    for tsk in category.tasks():
        if not any(tsk.title == item.text for item in items):
            print("For removal: ", tsk.title)
            tsk.destroy()


def add_items(items, input_user, category):
    alert = {'offset': 0, 'repeatEndsAfterOccurrences': -1, 'repeatStartsOn': None, 'repeatMonthType': 'ON_DATE',
             'repeatDays': '0000000', 'type': 'NONE', 'customTime': 0, 'repeatNextOccurrence': None,
             'repeatEndType': 'REPEAT_END_NEVER', 'repeatEndsOn': None, 'repeatInterval': 1}
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
            print("Added:", item.text)
            category.add_task(tsk)


def parse_date(rect):
    x = rect.attrs['x']
    if x == '345':
        date = ['08:35:00', '09:45:00']
    elif x == '772.5':
        date = ['09:55:00', '11:05:00']
    elif x == '1200':
        date = ['11:15:00', '12:25:00']
    elif x == '1627.5':
        date = ['12:55:00', '14:05:00']
    elif x == '2055':
        date = ['14:15:00', '15:25:00']
    else:
        date = ['15:35:00', '16:45:00']
    return date


def parse_rects(rects, valik, group):
    rect_dict = {}
    for rect in rects:
        value = rect.text.split('\n')[0]
        if "Group" in rect.text:
            if "Group " + str(group) in rect.text:
                rect_dict[value] = parse_date(rect)
        elif value not in valik:
            rect_dict[value] = parse_date(rect)
    return rect_dict


def get_timetable(source, valik, group):
    source = BeautifulSoup(source, features="html.parser")

    e_rects = source.findAll('rect', {'y': '420'})
    e_rects.extend(source.findAll('rect', {'y': '573'}))
    e = parse_rects(e_rects, valik, group)

    t_rects = source.findAll('rect', {'y': '726'})
    t_rects.extend(source.findAll('rect', {'y': '879'}))
    t = parse_rects(t_rects, valik, group)

    k_rects = source.findAll('rect', {'y': '1032'})
    k_rects.extend(source.findAll('rect', {'y': '1185'}))
    k = parse_rects(k_rects, valik, group)

    n_rects = source.findAll('rect', {'y': '1338'})
    n_rects.extend(source.findAll('rect', {'y': '1491'}))
    n = parse_rects(n_rects, valik, group)

    r_rects = source.findAll('rect', {'y': '1644'})
    r_rects.extend(source.findAll('rect', {'y': '1797'}))
    r = parse_rects(r_rects, valik, group)

    return e, t, k, n, r


def add_lesson(days, date):
    current_weekday = 6 if int(date.strftime('%w')) - 1 < 0 else int(date.strftime('%w')) - 1
    week_start_date = date - datetime.timedelta(days=current_weekday)
    day_count = 0
    for day in days:
        date_updated = week_start_date + datetime.timedelta(days=day_count)
        for lesson in day:
            lesson_time = day.get(lesson)
            start_time = lesson_time[0]
            end_time = lesson_time[1]
            date_formatted_base = str(date_updated).split(' ')[0] + 'T'
            start_date = date_formatted_base + start_time
            end_date = date_formatted_base + end_time
            event = {
                'summary': lesson,
                'description': "Tund",
                'start': {
                    'dateTime': start_date,
                    'timeZone': 'EET'
                },
                'end': {
                    'dateTime': end_date,
                    'timeZone': 'EET'
                },
                'reminders': {
                    'useDefault': False,
                    'overrides': [
                    ]
                }
            }
            response_events = service.events().list(calendarId='primary',
                                                    timeMin=start_date + "+02:00",
                                                    timeMax=end_date + "+02:00").execute()
            if len(response_events["items"]) != 0:
                with_description = [i for i in response_events["items"] if "description" in i.keys()]
                if any(item["description"] == "Tund" for item in with_description):
                    items_for_removal = [item for item in with_description if item["summary"] != lesson]
                    if len(items_for_removal) != 0:
                        for i in items_for_removal:
                            service.events().delete(calendarId='primary', eventId=i["id"]).execute()
                        service.events().insert(calendarId='primary', body=event).execute()
            else:
                service.events().insert(calendarId='primary', body=event).execute()
                print("Added lesson:", lesson)
        day_count += 1


# Basic stuff
login_url = "https://nrg.ope.ee/auth/"
timetable_url = "https://nrg.edupage.org/timetable/"
message_url = "https://nrg.ope.ee/suhtlus/api/channels/updates/a/inbox?merge_events=1&get_post_membership_data=1"
data = {"data[User][username]": "Marcusb2kl@gmail.com",
        "data[User][password]": "678M5cFq1u3I"}
# Accessing Google api
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


# Getting timetable
chrome_options = Options()
chrome_options.add_argument("--headless")
driver = webdriver.Chrome(executable_path='D:\\Projects\\StuudiumScraper\\chromedriver.exe', options=chrome_options)
driver.get(timetable_url)
WebDriverWait(driver, 50).until(ec.visibility_of_element_located((By.XPATH, "//div[@class='print-sheet']")))
first_week_response = driver.page_source
next_week_button = driver.find_element_by_xpath('//span[text() = "See nädal"]')
next_week_button.click()
WebDriverWait(driver, 50).until(ec.visibility_of_element_located((By.XPATH, "//a[text() = 'Järgmine nädal']")))
next_week_button = driver.find_element_by_xpath("//a[text() = 'Järgmine nädal']")
next_week_button.click()
time.sleep(10)
second_week_response = driver.page_source
driver.close()
Valikkursused = ["Füüsika olümpiaad", "Segakoor", "Inglise keele suhtlus", "Saksa keel valikaine",
                 "Keemia olümpiaad", "Matemaatika olümpiaad"]
es, te, ko, ne, re = get_timetable(first_week_response, Valikkursused, 1)
now = datetime.datetime.now()
add_lesson([es, te, ko, ne, re], now)
es, te, ko, ne, re = get_timetable(second_week_response, Valikkursused, 1)
now += datetime.timedelta(days=7)
add_lesson([es, te, ko, ne, re], now)
# Getting tasks
session = requests.session()
main_page = session.post(login_url, data)
session.close()
Tasks = get_homework(main_page)
user = Client(email='marcusb2kl@gmail.com', password='Bindevald16').get_user()
categories = list(map(lambda category: category['name'], user.categories(refresh=True)))
chosen_category = user.categories()[categories.index("School")]
add_items(Tasks, user, chosen_category)
remove_items(Tasks, chosen_category)




