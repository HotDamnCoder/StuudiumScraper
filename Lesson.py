from datetime import datetime as dt


class Lesson:
    def __init__(self, date: str, start_time: str, end_time: str, grade: str, subject: str) -> None:
        self.grade = grade
        self.subject = subject

        dt_date = dt.strptime(date, '%Y-%m-%d')
        dt_start_time = dt.strptime(start_time, '%H:%M')
        dt_end_time = dt.strptime(end_time, '%H:%M')
        dt_tzinfo = dt.now().astimezone().tzinfo

        self.start_date = dt_date.replace(
            hour=dt_start_time.hour, minute=dt_start_time.minute, tzinfo=dt_tzinfo)
        self.end_date = dt_date.replace(
            hour=dt_end_time.hour, minute=dt_end_time.minute, tzinfo=dt_tzinfo)

    def __getStartDate(self) -> str:
        start_date_str = self.start_date.strftime('%Y-%m-%dT%H:%M:%S%z')
        start_date_str = start_date_str[:-2] + ':' + start_date_str[-2:]
        return start_date_str

    def __getEndDate(self) -> str:
        end_date_str = self.end_date.strftime('%Y-%m-%dT%H:%M:%S%z')
        end_date_str = end_date_str[:-2] + ':' + end_date_str[-2:]
        return end_date_str

    def createCalendarEvent(self) -> dict:
        return {
            'summary': self.subject,
            'description': "Tund",
            'start': {
                'dateTime': self.__getStartDate(),
            },
            'end': {
                'dateTime': self.__getEndDate(),
            },
            'reminders': {
                'useDefault': False,
                'overrides': []
            }
        }
