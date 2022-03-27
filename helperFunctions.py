
from exceptions import NoSubjectCalander

def getSubjectCalendarID(subject: str, subject_calendars_ids: dict[str, str]) -> str:
    subject_calendar_name = subject.lower() + ' : tund'
    if subject_calendar_name in subject_calendars_ids:
        return subject_calendars_ids[subject_calendar_name]
    else:
        print ("Didn't find subject '" + subject + "' calendar id")
        return ''


def findSameEvents(searched_event, events) -> list:
    colliding_events = []
    for event in events:
        if (event['summary'] == searched_event['summary']):
            colliding_events.append(event)
    return colliding_events




def sameTimeEvents(event1, event2) -> bool:
    #! kinda bad implementation but I couldnt be arsed to overengineer a better solution

    event1_start_date_str = event1['start']['date'] if 'date' in event1['start'].keys() else event1['start']['dateTime']
    event1_end_date_str = event1['end']['date'] if 'date' in event1['end'].keys() else event1['end']['dateTime']

    event2_start_date_str = event2['start']['date'] if 'date' in event2['start'].keys() else event2['start']['dateTime']
    event2_end_date_str = event2['end']['date'] if 'date' in event2['end'].keys() else event2['end']['dateTime']

    return event1_start_date_str == event2_start_date_str and event1_end_date_str == event2_end_date_str

