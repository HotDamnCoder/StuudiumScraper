import sys
import datetime
from CalendarAPI import CalendarAPI
from Stuudium import Stuudium
from Timetable import Timetable
from helperFunctions import *

#* Read in constants from config
with open(sys.path[0] + '/config.txt', 'r', encoding='UTF-8') as config:
    lines = config.readlines()

    #* SCHOOL INFO
    STUDY_YEAR = int(lines[0].split(':')[1].strip())
    GRADE = lines[1].split(':')[1].strip().lower()
    STUDY_GROUP = 'Group ' + lines[2].split(':')[1].strip()
    BLACKLISTED_LESSONS = lines[3].split(':')[1].strip().lower().split(',')

    #* STUUDIUM INFO
    STUUDIUM_USERNAME = lines[4].split(':')[1].strip()
    STUUDIUM_PASSWORD = lines[5].split(':')[1].strip()


#* Date info
DATE_FROM = datetime.date.today() - datetime.timedelta(days=datetime.date.today().weekday())
DATE_TO = DATE_FROM + datetime.timedelta(days=6)
NEXT_WEEK_DATE_FROM = DATE_FROM + datetime.timedelta(days=7)
NEXT_WEEK_DATE_TO = DATE_TO + datetime.timedelta(days=7)

calendarAPI = CalendarAPI() 
timetable = Timetable()
stuudium = Stuudium(STUUDIUM_USERNAME, STUUDIUM_PASSWORD)

#* Find subject and tests calendar ids
subject_calendars_ids = {}
tests_calendar_id = ''

calendars = calendarAPI.listCalendarsIds()

for calendar in calendars:
    if 'tund' in calendar.lower():
        subject_calendars_ids[calendar] = calendars[calendar]
    elif 'kontrolltööd' in calendar.lower():
        tests_calendar_id = calendars[calendar]

test_events = calendarAPI.listEvents(
    calendar_id=tests_calendar_id, events=[])

homeworks = stuudium.getHomeworks()
for homework in homeworks:
    if homework.test:
        homework_event = homework.createCalendarEvent()
        homework_event['summary'] = homework.subject.capitalize() + " KT: " + homework_event['summary']

        same_events = findSameEvents(
            searched_event=homework_event, events=test_events)

        if len(same_events) != 0:
            print('Found possible duplicate/outdated test events!')
            event_already_exists = False
            for same_event in same_events:
                if not equalEvents(homework_event, same_event) or event_already_exists:
                    print('Found duplicate/outdated test event!')
                    calendarAPI.removeEvent(
                        tests_calendar_id, same_event)
                else:
                    print('Event for current test already exists!')
                    event_already_exists = True
            if not event_already_exists:
                calendarAPI.addEvent(
                    tests_calendar_id, homework_event)
        else:
            calendarAPI.addEvent(tests_calendar_id, homework_event)


subject_calendar_events = {}
for subject_calendar_id in subject_calendars_ids:
    subject_events = calendarAPI.listEvents(calendar_id=subject_calendars_ids[subject_calendar_id],
                                                start_date=DATE_FROM, end_date=NEXT_WEEK_DATE_TO, events=[])
    subject_calendar_events[subject_calendars_ids[subject_calendar_id]] = subject_events

current_week_lessons = timetable.getLessons(study_year=STUDY_YEAR, date_from=DATE_FROM,
                                            date_to=DATE_TO, grade=GRADE, study_group=STUDY_GROUP)
next_week_lessons = timetable.getLessons(
    study_year=STUDY_YEAR, study_group=STUDY_GROUP, grade=GRADE, date_from=NEXT_WEEK_DATE_FROM, date_to=NEXT_WEEK_DATE_TO)
lessons = [current_week_lessons, next_week_lessons]

for week_lessons in lessons:
    for lesson in week_lessons:
        if lesson.subject.lower() in BLACKLISTED_LESSONS:
            continue

        lesson_subject_calendar_id = getSubjectCalendarID(
            subject=lesson.subject, subject_calendars_ids=subject_calendars_ids)
        lesson_event = lesson.createCalendarEvent()

        event_already_exists = False
        for subject_calendar_id in subject_calendar_events:
            subject_events = subject_calendar_events[subject_calendar_id]
            for subject_event in subject_events:
                if equalEvents(lesson_event, subject_event):
                    if lesson_event['summary'] != subject_event['summary'] or event_already_exists:
                        print('Found duplicate/outdated lesson event!')
                        calendarAPI.removeEvent(
                            subject_calendar_id, subject_event)
                    else:
                        print('Event for current lesson already exists!')
                        event_already_exists = True
        if not event_already_exists:
            calendarAPI.addEvent(lesson_subject_calendar_id, lesson_event)
