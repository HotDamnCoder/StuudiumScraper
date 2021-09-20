import requests
from Homework import Homework
from bs4 import BeautifulSoup
from requests import Session


class Stuudium:
    __DATA_URL = 'https://nrg.ope.ee'
    __LOGIN_URL = 'https://nrg.ope.ee/auth/?lang=et'

    __LOGIN_HEADER = {'x-requested-with': 'XMLHttpRequest'}

    def __init__(self, username: str, password: str) -> None:
        self.__LOGIN_DATA = \
            {
                "data[User][username]": username,
                "data[User][password]": password
            }

    def __login(self) -> Session:
        logged_in_session = requests.session()
        logged_in_session.post(
            self.__LOGIN_URL, self.__LOGIN_DATA, headers=self.__LOGIN_HEADER)
        return logged_in_session

    def __getData(self) -> str:
        logged_in_session = self.__login()
        data = logged_in_session.get(self.__DATA_URL).text
        logged_in_session.close()
        return data

    def getHomeworks(self) -> list[Homework]:
        homework_htmls = BeautifulSoup(self.__getData(), features='html.parser').find_all(
            'div', {'class': 'todo_container'})
        homeworks = [Homework(homework_html)
                     for homework_html in homework_htmls]
        return homeworks
