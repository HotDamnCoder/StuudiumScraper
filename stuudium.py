import bs4
import json
import requests

from anydo_api.task import Task as Any_doTask
from bs4 import BeautifulSoup
from constants import *


class Task:
    def __init__(self, text, check, test, duedate_ticks, var_duedate):
        self.text = text
        self.checked = check
        self.test = test
        self.dateInTicks = duedate_ticks * 1000
        self.date = var_duedate


def find_calender_id(summary):
    for calender in CALANDER_IDS:
        if calender['summary'] == summary:
            return calender['id']
    return 'primary'


def find_table(tables, table_id):
    table_i = None
    for table in tables:
        if table['id'] == table_id:
            table_i = tables.index(table)
    if table_i is None:
        raise Exception("Couldn't find table", table_id)
    return table_i


def get_class_id(timetable_dict):
    class_id = ''
    class_index = find_table(timetable_dict['r']['tables'], 'classes')
    for rows in timetable_dict['r']['tables'][class_index]['data_rows']:
        if rows['short'] == CLASS:
            class_id = rows['id']
            break
    if class_id == '':
        raise Exception("Couldn't find class id")
    return class_id


def convert_to_google_date(var_duedate):
    y = var_duedate[:-4]
    d = var_duedate[-2:]
    m = var_duedate[-4:-2]
    date = "-".join([y, m, d])
    return date


def get_timetable_data(tt_url, db_url, tt_payload, db_payload, date_from, date_to):
    timetable_session = requests.session()

    tt_payload['__args'][1]['datefrom'] = str(date_from)
    tt_payload['__args'][1]['dateto'] = str(date_to)

    db_payload['__args'][2]['vt_filter']['datefrom'] = str(date_from)
    db_payload['__args'][2]['vt_filter']['dateto'] = str(date_to)

    timetable_maindb_json = json.loads(
        timetable_session.post(db_url, json.dumps(db_payload)).text)

    tt_payload['__args'][1]['id'] = get_class_id(timetable_maindb_json)

    timetable_currenttt_json = json.loads(
        timetable_session.post(tt_url, json.dumps(tt_payload)).text)

    timetable_session.close()

    return timetable_currenttt_json, timetable_maindb_json


def add_lessons(timetable_dict, db_dict, group):
    for item in timetable_dict['r']['ttitems']:
        if ('' in item['groupnames'] or 'Group ' + group in item['groupnames']) and len(item['classids']) <= 2:
            start_date = item['date'] + "T" + item['starttime'] + ":00"
            end_date = item['date'] + "T" + item['endtime'] + ":00"
            t_i = find_table(db_dict['r']['tables'],  'subjects')
            summary = find_if(db_dict['r']['tables'][t_i]['data_rows'], lambda x: item['subjectid'] == x['id'])['name']
            cal_id = find_calender_id(summary)
            colliding_events = list_events(cal_id, start_date, end_date)
            lesson_event = {
                'summary': summary,
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
            if len(colliding_events["items"]) >= 1:
                with_description_events = [i for i in colliding_events["items"] if "description" in i.keys()]
                for with_description_event in with_description_events:
                    if with_description_event["description"] == "Tund":
                        if with_description_event['summary'] != summary:
                            SERVICE.events().update(calendarId=cal_id, eventId=with_description_event['id'],
                                                    body=lesson_event)
                            print('Renamed lesson', with_description_event['summary'], 'to', summary)
            else:
                SERVICE.events().insert(calendarId=cal_id, body=lesson_event).execute()
                print('Added lesson:', summary)


def list_events(cal_id, start_date, end_date):
    current_timezone = datetime.datetime.now().astimezone().isoformat()[-6:]
    return SERVICE.events().list(calendarId=cal_id,
                                 timeMin=start_date + current_timezone,
                                 timeMax=end_date + current_timezone,
                                 ).execute()


def find_if(iterable, condition):
    found_item = next((item for item in iterable if condition(item)), None)
    if found_item is None:
        raise Exception("Couldn't find item satisfying said condition.")
    return found_item


def if_any(iterable, condition):
    return any(condition(item) for item in iterable)


def update_duplicate(var_due, var_task, var_task_event, var_cal_id):
    var_colliding_events = list_events(var_cal_id, var_due, var_due)['items']
    var_event = find_if(var_colliding_events, lambda x: x['summary'] == var_task.text)
    SERVICE.events().update(calendarId=var_cal_id, eventId=var_event['id'],
                            body=var_task_event)


# Getting timetable
current_week_data, current_week_db_data = get_timetable_data(TIMETABLE_URL, TIMETABLE_MAINDB_URL,
                                                             TIMETABLE_PAYLOAD, TIMETABLE_MAINDB_PAYLOAD,
                                                             DATEFROM, DATETO)
add_lessons(current_week_data, current_week_db_data, STUDY_GROUP)

next_week_data, next_week_db_data = get_timetable_data(TIMETABLE_URL, TIMETABLE_MAINDB_URL,
                                                       TIMETABLE_PAYLOAD, TIMETABLE_MAINDB_PAYLOAD,
                                                       NEXTWEEKDATEFROM, NEXTWEEKDATETO)
add_lessons(next_week_data, next_week_db_data, STUDY_GROUP)

# Get stuudium page
stuudium_session = requests.session()
stuudium_session.headers = STUUDIUM_HEADERS
stuudium_session.post(STUUDIUM_LOGIN_URL, STUUDIUM_PAYLOAD)
stuudium_page = stuudium_session.get(STUUDIUM_PAGE_URL)
stuudium_session.close()

# Get tasks from stuudium page
todos = BeautifulSoup(stuudium_page.text, features="html.parser").findAll('div', {'class': 'todo_container'})
tasks = []
for todo_container in todos:
    due_date_in_ticks = int(todo_container.attrs['data-date_ts'])
    due_date = todo_container.attrs['data-date']
    is_marked = 'is_marked' in todo_container.attrs['class']
    is_test = 'is_test' in todo_container.find('div').attrs['class']
    todo_content_container = todo_container.find('span', {"class": "todo_content"})
    todo_content_container_text = ""
    if todo_content_container is not None:
        for content in todo_content_container.contents:
            if isinstance(content, bs4.Tag):
                if content.name == 'br':
                    todo_content_container_text += '\n'
                else:
                    todo_content_container_text += content.text
            else:
                todo_content_container_text += content
        spliced_todo_container_text = todo_container.text.strip().replace('\n', ' ').split()[:-1]
        splice_index = 2 if is_test else 1
        spliced_todo_container_text[splice_index] = todo_content_container_text
        todo_text = " ".join(spliced_todo_container_text[:splice_index + 1])
        homework = Task(todo_text, is_marked, is_test, due_date_in_ticks, due_date)
        tasks.append(homework)
    else:
        continue

# Add tasks
for task in tasks:
    due = convert_to_google_date(task.date)
    calender_id = find_calender_id('Kontrolltööd')
    task_event = {
        'summary': task.text,
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
    } if task.test else None
    if not if_any(ANY_CATEGORY.tasks(), lambda x: x.title == task.text):
        if task.test:
            # noinspection PyBroadException
            try:
                update_duplicate(due, task, task_event, calender_id)
            except Exception:
                SERVICE.events().insert(calendarId=calender_id, body=task_event).execute()
                print('Added test "', task.text, '" to calender')
        anydo_task = Any_doTask.create(
            status="CHECKED" if task.checked else "",
            user=USER,
            title=task.text,
            priority='High' if task.test else 'Low',
            category=ANY_CATEGORY['name'],
            repeatingMethod='TASK_REPEAT_OFF',
            alert=ANY_DO_ALERT,
            dueDate=task.dateInTicks)
        ANY_CATEGORY.add_task(anydo_task)
        print("Task added:", anydo_task.title)

    elif if_any(ANY_CATEGORY.tasks(), lambda x: x.title == task.text and x['dueDate'] != task.dateInTicks):
        anydo_task = find_if(ANY_CATEGORY.tasks(), lambda x: x.title == task.text and x['dueDate'] != task.dateInTicks)
        if task.test:
            duedate = str(datetime.datetime.today() +
                          datetime.timedelta(microseconds=anydo_task['dueDate'] / 10000)).split()[0]
            update_duplicate(due, task, task_event, calender_id)
        else:
            anydo_task['dueDate'] = task.dateInTicks
            USER.save()

    else:
        anydo_task = find_if(ANY_CATEGORY.tasks(), lambda x: x.title == task.text and x['dueDate'] == task.dateInTicks)
        if task.checked and anydo_task['status'] == "":
            anydo_task.check()
            print('Task checked:', anydo_task.title)

# Remove old or not existent tasks
for anydo_task in ANY_CATEGORY.tasks():
    if (not if_any(tasks, lambda x: anydo_task.title == x.text)) and \
            not if_any(tasks, lambda x: anydo_task.title == x.text and anydo_task['dueDate'] != x.dateInTicks):
        anydo_task.destroy()
        print("Task destroyed:", anydo_task.title)
