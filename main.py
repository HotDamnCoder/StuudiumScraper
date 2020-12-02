from anydo_api.task import Task as Any_do_task
from bs4 import BeautifulSoup
from helperFunctions import *


# Get timetable
for i in range(2):
    timetable_db, timetable = get_timetable_data(TIMETABLE_URL, TIMETABLE_DATABASE_URL, TIMETABLE_PAYLOAD,
                                                 TIMETABLE_DATABASES_PAYLOAD, CLASS)
    set_timetable_payload_date(TIMETABLE_PAYLOAD, TIMETABLE_DATABASES_PAYLOAD, NEXTWEEKDATEFROM, NEXTWEEKDATETO)
    add_lessons(timetable, timetable_db, STUDY_GROUP)

# Get stuudium page
stuudium_session = requests.session()
stuudium_session.headers = STUUDIUM_HEADERS
stuudium_session.post(STUUDIUM_LOGIN_URL, STUUDIUM_PAYLOAD)
stuudium_page = stuudium_session.get(STUUDIUM_PAGE_URL)
stuudium_session.close()

# This part gets tasks from stuudium page

# Abbreviation 'hw' means homework
hw_containers = BeautifulSoup(stuudium_page.text, features="html.parser").findAll('div', {'class': 'todo_container'})
# List of homework text and due date in ticks tuples
hws = []
for hw_container in hw_containers:
    # Gets needed info for homework from Stuudium
    due_date_in_ticks = int(hw_container.attrs['data-date_ts']) * 1000

    due_date = hw_container.attrs['data-date']
    year = due_date[:-4]
    day = due_date[-2:]
    month = due_date[-4:-2]
    due_date = "-".join([year, month, day])

    is_marked = 'is_marked' in hw_container.attrs['class']

    is_test = 'is_test' in hw_container.find('div').attrs['class']

    hw_text = " ".join(hw_container.text.strip().split('\n')[:-1])

    task_event = {
        'summary': hw_text,
        'start': {
            'date': due_date,
            'timeZone': 'EET'
        },
        'end': {
            'date': due_date,
            'timeZone': 'EET'
        },
        'reminders': {
            'useDefault': False,
            'overrides': [
            ]
        }
    } if is_test else None
    # Adds homework to tasks if there isn't already for the homework
    # Also adds it to calander if its a test and it isn't already there
    if not if_any_where(CATEGORY.tasks(), lambda x: x.title == hw_text):
        if is_test:
            SERVICE.events().insert(calendarId=SCHOOL_TEST_CALANDER_ID, body=task_event).execute()
            print('Added test "' + hw_text + '" to calender')
        any_do_task = Any_do_task.create(
            status="CHECKED" if is_marked else "",
            user=USER,
            title=hw_text,
            priority='High' if is_test else 'Low',
            category=CATEGORY['name'],
            repeatingMethod='TASK_REPEAT_OFF',
            alert=ANY_DO_ALERT,
            dueDate=due_date_in_ticks)
        CATEGORY.add_task(any_do_task)
        print("Task added:", any_do_task.title)
    # Updates tasks that has had its corresponding homework due date changed
    # Also updates corresponding calander event
    elif if_any_where(CATEGORY.tasks(),
                      lambda task: task.title == hw_text and task['dueDate'] != due_date_in_ticks):
        any_do_task = find_where(CATEGORY.tasks(),
                                 lambda task: task.title == hw_text and task['dueDate'] != due_date_in_ticks)
        if is_test:
            task_due_date = datetime.fromtimestamp(any_do_task['dueDate'])
            update_existing_event(task_due_date, hw_text, task_event, SCHOOL_TEST_CALANDER_ID)
        any_do_task['dueDate'] = due_date_in_ticks
        USER.save()
    # Finds task corresponding to the homework and checks it if it is checked in Stuudium and not in tasks
    else:
        any_do_task = find_where(CATEGORY.tasks(),
                                 lambda task: task.title == hw_text and task['dueDate'] == due_date_in_ticks)
        if is_marked and any_do_task['status'] == "":
            any_do_task.check()
            print('Task checked:', any_do_task.title)

    hws.append((hw_text, due_date_in_ticks))


# Removes old tasks by comparing if there's not any task:
#   with the same name of already existing homeworks and
#   with same due date of existing homeworks
for any_do_task in CATEGORY.tasks():
    if not if_any_where(hws, lambda hw: any_do_task.title == hw[0] and any_do_task['dueDate'] == hw[1]):
        any_do_task.destroy()
        print("Task destroyed:", any_do_task.title)

