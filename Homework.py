from datetime import datetime as dt


class Homework:
    def __init__(self, homework_html) -> None:

        self.due_date = dt.strptime(homework_html['data-date'], '%Y%m%d')

        self.done = 'is_marked' in homework_html['class']

        self.test = 'is_test' in homework_html.find_next(
            'div', {'class': 'todo'})['class']

        self.subject = homework_html.find_next(
            'a', {'class': 'subject_name'}).text.strip().lower()

        self.text = homework_html.find_next(
            'span', {'class': 'todo_content'}).text.strip()

    def getDueDate(self) -> str:
        return self.due_date.strftime('%Y-%m-%d')

    def createCalendarEvent(self) -> dict:
        return {
            'summary': self.text,
            'start': {
                'date': self.getDueDate(),
            },
            'end': {
                'date': self.getDueDate(),
            },
            'reminders': {
                'useDefault': False,
                'overrides': []
            }
        }
