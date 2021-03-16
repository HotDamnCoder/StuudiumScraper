import json
import requests
from constants import *
from datetime import datetime
from datetime import date
from exceptions import *


def find_where(iterable: list, condition: callable(object)):
    found_item = next((item_in_iterable for item_in_iterable in iterable if condition(item_in_iterable)), None)
    if found_item is None:
        raise ItemNotFound("Couldn't find item satisfying said condition.")
    return found_item


def if_any_where(iterable: list, condition: callable(object)):
    return any(condition(item_in_iterable) for item_in_iterable in iterable)


def set_timetable_payload_date(tt_payload: dict, db_payload: dict, date_from: date, date_to: date):
    """
    Sets timetable and timetable databases payloads dates
    :param tt_payload: Timetable website request payload
    :param db_payload: Timetable database request payload
    :param date_from: Date from which to start taking timetable
    :param date_to: Date from which to end taking timetable
    :return: Nothing
    """
    tt_payload['__args'][1]['datefrom'] = str(date_from)
    tt_payload['__args'][1]['dateto'] = str(date_to)

    db_payload['__args'][2]['vt_filter']['datefrom'] = str(date_from)
    db_payload['__args'][2]['vt_filter']['dateto'] = str(date_to)


def get_timetable_data(tt_url: str, db_url: str, tt_payload: dict, db_payload: dict, searched_class: str):
    """
    Gets necessary data to add lesson to calander
    :param tt_url: Timetable website url for getting the timetable
    :param db_url: Timetable database url for class names, ids and such
    :param tt_payload: Timetable website request payload
    :param db_payload: Timetable database request payload
    :param searched_class: The class for whom the timetables is pulled for
    :return: Responses from both websites as dictionaries
    Timetable websites response is a list of dictionaries containing necessary info about lessons
    Timetable databases response is a dictionary of two dictionaries:
                            1. for subject ids corresponding to subjects name
                            2. for class ids corresponding to class name
    """
    current_session = requests.session()
    timetable_database_response = current_session.post(db_url, json.dumps(db_payload)).text
    timetable_tables = json.loads(timetable_database_response)['r']['tables']
    timetables_tables_dict = {table['id']: {row['id']: row['name'] for row in table['data_rows']}
                              for table in timetable_tables}

    for class_id in timetables_tables_dict['classes']:
        if timetables_tables_dict['classes'][class_id] == searched_class:
            tt_payload['__args'][1]['id'] = class_id
            break
    if tt_payload['__args'][1]['id'] == '':
        raise ClassIdNotFound("Couldn't find id for class!")

    timetables_website_response = current_session.post(tt_url, json.dumps(tt_payload)).text
    timetable_lessons = json.loads(timetables_website_response)['r']['ttitems']
    timetable_lessons_dict = [{'subjectid': lesson['subjectid'],
                               'starttime': lesson['starttime'],
                               'endtime': lesson['endtime'],
                               'date': lesson['date'],
                               'groupnames': lesson['groupnames']} for lesson in timetable_lessons]

    del timetables_website_response, timetable_lessons, timetable_database_response, timetable_tables
    current_session.close()

    return timetables_tables_dict, timetable_lessons_dict


def find_subject_calender_id(subject: str):
    """
    Finds subjects calander id
    :param subject: Subjects name
    :return: Subjects calander id
    """
    subject += ' : Tund'
    if subject in SUBJECT_CALANDER_IDS.keys():
        return SUBJECT_CALANDER_IDS[subject]
    raise NoSubjectCalander("Didn't find subject calander id: " + subject)


def update_existing_event(event_due_date: date, event_summary: str, event_info: dict, calander_id: str):
    """
    Updates existing events time
    :param event_due_date: Event date
    :param event_summary: Self-explanatory
    :param event_info: Self-explanatory
    :param calander_id: Self-explanatory
    :return: Nothing
    """
    event_due_date = str(event_due_date).split()[0]
    current_timezone = datetime.now().astimezone().isoformat()[-6:]

    time_min = event_due_date + 'T00:00:00' + current_timezone
    time_max = event_due_date + 'T23:59:59' + current_timezone

    var_colliding_events = SERVICE.events().list(calendarId=calander_id,
                                                 timeMin=time_min,
                                                 timeMax=time_max).execute()['items']
    try:
        event = find_where(var_colliding_events, lambda x: x['summary'] == event_summary)

        SERVICE.events().update(calendarId=calander_id, eventId=event['id'],
                                body=event_info)
    except Exception:
        pass


def list_lesson_events(start_date: date, end_date: date):
    """
    Lists all lesson events in calander starting from start date to end date
    :param start_date: Self-explanatory
    :param end_date: Self-explanatory
    :return:
    """
    current_timezone = datetime.now().astimezone().isoformat()[-6:]

    lesson_events = []
    for name in SUBJECT_CALANDER_IDS:
        events = SERVICE.events().list(calendarId=SUBJECT_CALANDER_IDS[name],
                                       timeMin=str(start_date) + current_timezone,
                                       timeMax=str(end_date) + current_timezone).execute()['items']
        for event in events:
            lesson_events.append({'id': event['id'], 'cal_id': event['creator']['email'], 'summary': event['summary']})
    return lesson_events


def add_lessons(timetable: list, db: dict, group: str):
    """
    Adds lessons from timetable to calander
    :param timetable: list of dictionaries containing necessary info about lessons
    :param db: dictionary of two dictionaries:
                            1. for subject ids corresponding to subjects name
                            2. for class ids corresponding to class name
    :param group: Study group
    :return: Nothing
    """
    for lesson in timetable:
        lesson_name = db['subjects'][lesson['subjectid']]
        if '' in lesson['groupnames'] or group in lesson['groupnames']:
            try:
                subject_calender_id = find_subject_calender_id(lesson_name)
                start_date = lesson['date'] + "T" + lesson['starttime'] + ":00"
                end_date = lesson['date'] + "T" + lesson['endtime'] + ":00"
                lesson_cal_event = {
                    'summary': lesson_name,
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
                colliding_events = list_lesson_events(start_date, end_date)
                if len(colliding_events) > 0:
                    for event in colliding_events:
                        if event['summary'] != lesson_name:
                            SERVICE.events().update(calendarId=event['cal_id'], eventId=event['id'],
                                                    body=lesson_cal_event)
                            print('Renamed lesson', event['summary'], 'to', lesson_name)
                else:
                    SERVICE.events().insert(calendarId=subject_calender_id, body=lesson_cal_event).execute()
                    print('Added lesson:', lesson_name)
            except NoSubjectCalander as e:
                print(str(e))
