import datetime
import pickle
import os.path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from anydo_api.client import Client
import requests
import json


def find_if(iterable, condition):
    found_item = next((item for item in iterable if condition(item)), None)
    if found_item is None:
        raise Exception("Couldn't find item satisfying said condition.")
    return found_item


with open('config.txt', 'r', encoding='UTF-8') as config:
    lines = config.readlines()

    # SCHOOL INFO
    STUDY_YEAR = int(lines[0].split(':')[1].strip())
    CHOSEN_ELECTIVE_COURSES = lines[1].split(':')[1].strip().split(',')
    CLASS = lines[2].split(':')[1].strip().lower()
    STUDY_GROUP = lines[3].split(':')[1].strip()

    # VIKUNJA INFO
    VIKUNJA_NAMESPACE_NAME = lines[4].split(':')[1].strip()
    VIKUNJA_USERNAME = lines[5].split(':')[1].strip()
    VIKUNJA_PASSWORD = lines[6].split(':')[1].strip()

    # STUUDIUM INFO
    STUUDIUM_USERNAME = lines[7].split(':')[1].strip()
    STUUDIUM_PASSWORD = lines[8].split(':')[1].strip()

    # CALENDER INFO
    CALENDER_ID = lines[9].split(':')[1].strip()

# CONSTANTS
SCOPES = ['https://www.googleapis.com/auth/calendar']

# ANY_DO INFO
ANY_DO_ALERT = \
    {
        'offset': 0,
        'repeatEndsAfterOccurrences': -1,
        'repeatStartsOn': None,
        'repeatMonthType': 'ON_DATE',
        'repeatDays': '0000000',
        'type': 'NONE',
        'customTime': 0,
        'repeatNextOccurrence': None,
        'repeatEndType': 'REPEAT_END_NEVER',
        'repeatEndsOn': None, 'repeatInterval': 1
    }

# SCHOOL INFO
DATEFROM = datetime.date.today() - datetime.timedelta(days=datetime.date.today().weekday())
DATETO = DATEFROM + datetime.timedelta(days=6)
NEXTWEEKDATEFROM = DATEFROM + datetime.timedelta(days=7)
NEXTWEEKDATETO = DATETO + datetime.timedelta(days=7)


# URLS
STUUDIUM_PAGE_URL = 'https://nrg.ope.ee'
STUUDIUM_LOGIN_URL = "https://nrg.ope.ee/auth/?lang=et"
TIMETABLE_URL = "https://nrg.edupage.org/timetable/server/currenttt.js?__func=curentttGetData"
TIMETABLE_MAINDB_URL = "https://nrg.edupage.org/rpr/server/maindbi.js?__func=mainDBIAccessor"
STUUDIUM_MSG_URL = "https://nrg.ope.ee/suhtlus/api/channels/updates/a/inbox?merge_events=1&get_post_membership_data=1"
VIKUNJA_LOGIN_URL = 'https://vikunja.room241.wtf/api/v1/login'
VIKUNJA_NAMESPACES_URL = 'https://vikunja.room241.wtf/api/v1/namespaces'

# PAYLOADS
TIMETABLE_PAYLOAD = \
    {
        "__args":
            [
                None,
                {
                    "year": STUDY_YEAR,
                    "datefrom": str(DATEFROM),
                    "dateto": str(DATETO),
                    "table": "classes",
                    "id": '',
                    "showColors": True
                }
            ],
        "__gsh": "00000000"
    }
TIMETABLE_MAINDB_PAYLOAD = \
    {
        "__args":
            [
                None,
                STUDY_YEAR,
                {
                    "vt_filter":
                        {
                            "datefrom": str(DATEFROM),
                            "dateto": str(DATETO)
                        }
                },
                {
                    "op": "fetch",
                    "needed_part":
                        {
                            "classes": ["__name"],
                            "subjects": ["__name", "name"],
                        },
                }
            ],
        "__gsh": "00000000"
    }
STUUDIUM_PAYLOAD = \
    {
        "data[User][username]": STUUDIUM_USERNAME,
        "data[User][password]": STUUDIUM_PASSWORD
    }
STUUDIUM_HEADERS = {'x-requested-with': 'XMLHttpRequest'}
VIKUNJA_LOGIN_PAYLOAD = {'username': VIKUNJA_USERNAME,
                         'password': VIKUNJA_PASSWORD}

# Initialize VIKUNJA api
#session = requests.session()
#token = json.loads(session.post(VIKUNJA_LOGIN_URL, VIKUNJA_LOGIN_PAYLOAD).text.strip())['token']
#session.headers['Authorization'] = 'Bearer ' + token
#vikunja_namespaces = json.loads(session.get(VIKUNJA_NAMESPACES_URL).text)

#VIKUNJA_CATEGORY_ID = find_if(vikunja_namespaces, lambda x: x['title'] == VIKUNJA_NAMESPACE_NAME)['id']

# Accessing Google api
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
SERVICE = build('calendar', 'v3', credentials=creds)
CALANDER_IDS = []
pagetoken = None
while True:
    calander_list = SERVICE.calendarList().list(pageToken=pagetoken).execute()
    CALANDER_IDS += calander_list['items']
    if 'nextPageToken' in calander_list.keys():
        pagetoken = calander_list['nextPageToken']
    else:
        break
# Initialize any.do
USER = Client(email=VIKUNJA_USERNAME, password=VIKUNJA_PASSWORD).get_user()
ANY_DO_CATEGORIES = list(map(lambda cate: cate['name'], USER.categories(refresh=True)))
ANY_CATEGORY = USER.categories()[ANY_DO_CATEGORIES.index(VIKUNJA_NAMESPACE_NAME)]
