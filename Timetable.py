from datetime import datetime as dt
import json
import requests
from Lesson import Lesson


class Timetable:
    __LESSON_TABLE_URL = 'https://nrg.edupage.org/timetable/server/currenttt.js?__func=curentttGetData'
    __DATABASES_URL = 'https://nrg.edupage.org/rpr/server/maindbi.js?__func=mainDBIAccessor'

    LESSON_TABLE_PAYLOAD = \
        {
            '__args':
            [
                None,
                {
                    # * Study year placeholder. Accessible with key "['__args'][1]['year']"
                    'year': 0,
                    # * Date from placeholder. Accessible with key "['__args'][1]['datefrom']"
                    'datefrom': '',
                    # * Date to placeholder. Accessible with key "['__args'][1]['dateto']"
                    'dateto': '',
                    'table': 'classes',
                    # * Class id placeholder. Accessible with key "['__args'][1]['id']"
                    'id': '',
                }
            ],
            '__gsh': '00000000'
        }
    __DATABASE_PAYLOAD = \
        {
            '__args':
            [
                None,
                # * Study year placeholder. Accessible with key "['__args'][1]"
                0,
                {
                    'vt_filter':
                    {
                        # * Date from placeholder. Accessible with key "['__args'][2]['vt_filter']['datefrom']"
                        'datefrom': '',
                        # * Date to placeholder. Accessible with key "['__args'][2]['vt_filter']['dateto']"
                        'dateto': ''
                    }
                },
                {
                    'op': 'fetch',
                    'needed_part':
                    {
                        'classes': ['name'],
                        'subjects': ['name'],
                    },
                }
            ],
            '__gsh': '00000000'
        }

    def __setTime(self, study_year: int, date_from: dt, date_to: dt):
        self.__DATABASE_PAYLOAD['__args'][1] = study_year
        self.LESSON_TABLE_PAYLOAD['__args'][1]['year'] = study_year

        self.__DATABASE_PAYLOAD['__args'][2]['vt_filter']['datefrom'] = date_from.strftime('%Y-%m-%d')
        self.LESSON_TABLE_PAYLOAD['__args'][1]['datefrom'] = date_from.strftime('%Y-%m-%d')

        self.__DATABASE_PAYLOAD['__args'][2]['vt_filter']['dateto'] = date_to.strftime('%Y-%m-%d')
        self.LESSON_TABLE_PAYLOAD['__args'][1]['dateto'] = date_to.strftime('%Y-%m-%d')

    def __getGrades_N_Subjects(self) -> tuple[dict[str, str], dict[str, str]]:
        database_session = requests.session()
        database = database_session.post(
            self.__DATABASES_URL, json.dumps(self.__DATABASE_PAYLOAD)).text
        database_json = json.loads(database)
        database_tables = {table['id']: {row['name']: row['id'] for row in table['data_rows']}
                           for table in database_json['r']['tables']}

        grade_ids = database_tables['classes']
        subjects = database_tables['subjects']
        # * Reversed from subjects because default key format is [id : name]
        subject_names = {subjects[key]: key for key in subjects}

        # * Grade ids contains ids for grade names, subject names contains names for subject ids
        return grade_ids, subject_names

    def __setGradeId(self, grade_id: str):
        self.LESSON_TABLE_PAYLOAD['__args'][1]['id'] = grade_id

    def __getLessons(self, grade: str, study_group: str, grade_ids: dict[str, str], subject_names: dict[str, str]) -> list[Lesson]:
        self.__setGradeId(grade_ids[grade])

        table_session = requests.session()
        table = table_session.post(
            self.__LESSON_TABLE_URL, json.dumps(self.LESSON_TABLE_PAYLOAD)).text
        table_json = json.loads(table)
        table_items = table_json['r']['ttitems']

        lessons = []
        for item in table_items:
            item_groups = item['groupnames']
            if '' in item_groups or study_group in item_groups:
                item_date = item['date']
                item_start_time = item['starttime']
                item_end_time = item['endtime']
                item_subject_id = item['subjectid']

                if item_subject_id != '':
                    if item_subject_id in subject_names:
                        lessons.append(Lesson(item_date, item_start_time,
                        item_end_time, grade, subject_names[item_subject_id]))
                    else:
                        lessons.append(Lesson(item_date, item_start_time,
                        item_end_time, grade, item_subject_id))

        return lessons

    def getLessons(self, study_year, date_from, date_to, grade, study_group) -> list[Lesson]:
        self.__setTime(study_year=study_year,
                       date_from=date_from, date_to=date_to)
        grade_ids, subject_names = self.__getGrades_N_Subjects()
        lessons = self.__getLessons(
            grade=grade, study_group=study_group, grade_ids=grade_ids, subject_names=subject_names, )

        return lessons
