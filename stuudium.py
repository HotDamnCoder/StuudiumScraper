import requests
from bs4 import BeautifulSoup
import json

login_url = "https://nrg.ope.ee/auth/"
message_url = "https://nrg.ope.ee/suhtlus/api/channels/updates/a/inbox?merge_events=1&get_post_membership_data=1"
data = {"data[User][username]": "MarcusBVald03@gmail.com",
        "data[User][password]": "678M5cFq1u3I"}

session = requests.session()
session.post("stuudium://auth")
main_page = session.post("https://nrg.ope.ee/auth/?lang=et",data)
html = BeautifulSoup(main_page.text, features="html.parser")
print(main_page.text)
messages_main_url = html.find('a', {'data-nav-tab': "messages"}).get('href')
response1 = session.get(messages_main_url)
response2 = session.get(message_url)

jason = json.loads(response2.text)
print(jason)
divs = html.findAll('div', {'class':'todo'})
a = [[div.text[1:-1].split('\n')] for div in divs]
print(a)