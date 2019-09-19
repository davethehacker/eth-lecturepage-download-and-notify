from bs4 import BeautifulSoup, SoupStrainer
import httplib2
import pickle
import os
import requests
import ssl
from urllib.parse import urlparse

api = 'https://api.telegram.org/bot<apiKey>/sendMessage?chat_id=<chat-id>&text='
subject = 'subject name'

def download(url):
    response = requests.get(url)
    if(response.status_code == 200):
        filename = url[url.rfind("/")+1:]
        with open(filename, 'wb') as fd:
            fd.write(response.content)
            # add file to the list of downloaded objects
            links.add(url)
            fd.close
            print(filename)
            payload = {'value1': filename, 'value2': subject}
            requests.post(
                'https://maker.ifttt.com/trigger/telegram/with/key/<ifttt-key>', params=payload)
            requestStr = api + 'New File online for ' + subject + ': ' + filename + ' ' + url
            requests.post(requestStr)


def checkUrl(link, site):
    if (link[-4:] == ".pdf") or (link[-4:] == ".zip"):
        if not (link[:4] == "http"):
            link = site + link
        if not (link in links):
            download(link)


def getLinks(site):
    http = httplib2.Http()
    status, response = http.request(site)
    print("res: ", status)

    for link in BeautifulSoup(response, "html.parser", parse_only=SoupStrainer('a')):
        # print("link: ", link)
        if link.has_attr('href'):
            checkUrl(link['href'], site)


links = {1, 2}

try:
    dmp = open(__file__ + ".dmp", "rb")
    links = pickle.load(dmp)
except EOFError:
    dmp.close()
    pass
except FileNotFoundError:
    pass
else:
    dmp.close()

getLinks("<website-url>")

dmp = open(__file__ + ".dmp", "wb")
pickle.dump(links, dmp)
dmp.close()
