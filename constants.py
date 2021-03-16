import datetime
import pickle
import os.path
import sys
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from anydo_api.client import Client


with open(sys.path[0] + '/config.txt', 'r', encoding='UTF-8') as config:
    lines = config.readlines()

    # SCHOOL INFO
    STUDY_YEAR = int(lines[0].split(':')[1].strip())
    CLASS = lines[1].split(':')[1].strip().lower()
    STUDY_GROUP = 'Group ' + lines[2].split(':')[1].strip()

    # VIKUNJA INFO
    CATEGORY_NAME = lines[3].split(':')[1].strip()
    ANY_DO_USERNAME = lines[4].split(':')[1].strip()
    ANY_DO_PASSWORD = lines[5].split(':')[1].strip()

    # STUUDIUM INFO
    STUUDIUM_USERNAME = lines[6].split(':')[1].strip()
    STUUDIUM_PASSWORD = lines[7].split(':')[1].strip()

# CONSTANTS

STUUDIUM_HEADERS = {'x-requested-with': 'XMLHttpRequest'}
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

# DATE INFO
DATEFROM = datetime.date.today() - datetime.timedelta(days=datetime.date.today().weekday())
DATETO = DATEFROM + datetime.timedelta(days=6)
NEXTWEEKDATEFROM = DATEFROM + datetime.timedelta(days=7)
NEXTWEEKDATETO = DATETO + datetime.timedelta(days=7)


# URLS
STUUDIUM_PAGE_URL = 'https://nrg.ope.ee'
STUUDIUM_LOGIN_URL = "https://nrg.ope.ee/auth/?lang=et"
TIMETABLE_URL = "https://nrg.edupage.org/timetable/server/currenttt.js?__func=curentttGetData"
TIMETABLE_DATABASE_URL = "https://nrg.edupage.org/rpr/server/maindbi.js?__func=mainDBIAccessor"
# STUUDIUM_MSG_URL = "https://nrg.ope.ee/suhtlus/api/channels/updates/a/inbox?merge_events=1&get_post_membership_data=1"
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
TIMETABLE_DATABASES_PAYLOAD = \
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
VIKUNJA_LOGIN_PAYLOAD = {'username': ANY_DO_USERNAME,
                         'password': ANY_DO_PASSWORD}

# Accessing Google api
creds = None
scopes = ['https://www.googleapis.com/auth/calendar']
if os.path.exists(sys.path[0] + '/token.pickle'):
    with open(sys.path[0] + '/token.pickle', 'rb') as token:
        creds = pickle.load(token)
if not creds or not creds.valid:
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
    else:
        flow = InstalledAppFlow.from_client_secrets_file(sys.path[0] + 
            '/credentials.json', scopes)
        creds = flow.run_local_server(port=0)
    with open(sys.path[0] + '/token.pickle', 'wb') as token:
        pickle.dump(creds, token)

SERVICE = build('calendar', 'v3', credentials=creds)

# CALANDER IDS
SUBJECT_CALANDER_IDS = {}
SCHOOL_TEST_CALANDER_ID = ''

pagetoken = None
while True:
    calander_list = SERVICE.calendarList().list(pageToken=pagetoken).execute()
    for item in calander_list['items']:
        if 'tund' in item['summary'].lower():
            SUBJECT_CALANDER_IDS[item['summary']] = item['id']
        elif 'kontrolltööd' in item['summary'].lower():
            SCHOOL_TEST_CALANDER_ID = item['id']
    if 'nextPageToken' in calander_list.keys():
        pagetoken = calander_list['nextPageToken']
    else:
        break


# Initialize any.do
USER = Client(email=ANY_DO_USERNAME, password=ANY_DO_PASSWORD).get_user()
any_do_categories = list(map(lambda cate: cate['name'], USER.categories(refresh=True)))
CATEGORY = USER.categories()[any_do_categories.index(CATEGORY_NAME)]

del any_do_categories
