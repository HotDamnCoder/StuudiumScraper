import datetime
import pickle
import os.path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from anydo_api.client import Client

with open('config.txt', 'r', encoding='UTF-8') as config:
    lines = config.readlines()
    # SCHOOL INFO
    STUDY_YEAR = int(lines[0].split(':')[1].strip())
    CHOSEN_ELECTIVE_COURSES = lines[1].split(':')[1].strip().split(',')
    CLASS = lines[2].split(':')[1].strip().lower()
    STUDY_GROUP = lines[3].split(':')[1].strip()

    # ANY_DO INFO
    ANY_DO_CATEGORY_NAME = lines[4].split(':')[1].strip()
    ANY_DO_USERNAME = lines[5].split(':')[1].strip()
    ANY_DO_PASSWORD = lines[6].split(':')[1].strip()

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
STUUDIUM_LOGIN_URL = "https://nrg.ope.ee/auth/"
TIMETABLE_URL = "https://nrg.edupage.org/timetable/server/currenttt.js?__func=curentttGetData"
TIMETABLE_MAINDB_URL = "https://nrg.edupage.org/rpr/server/maindbi.js?__func=mainDBIAccessor"
STUUDIUM_MSG_URL = "https://nrg.ope.ee/suhtlus/api/channels/updates/a/inbox?merge_events=1&get_post_membership_data=1"

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

# Initialize any.do
USER = Client(email=ANY_DO_USERNAME, password=ANY_DO_PASSWORD).get_user()
ANY_DO_CATEGORIES = list(map(lambda cate: cate['name'], USER.categories(refresh=True)))
ANY_DO_CATEGORY = USER.categories()[ANY_DO_CATEGORIES.index(ANY_DO_CATEGORY_NAME)]