from bs4 import BeautifulSoup, SoupStrainer
import httplib2
import pickle
import os
import requests
import ssl
import urllib
import hashlib
import re
import collections
import datetime
from requests.auth import HTTPBasicAuth
from config import *


print(datetime.datetime.now())

script_dir = os.path.dirname(__file__)
# print(script_dir)


def calcFilename(response, url, lecture):
    if "Content-Disposition" in response.headers.keys():
        filename = re.findall("filename=\"(.+)\"",
                              response.headers["Content-Disposition"])[0]
    else:
        filename = urllib.parse.quote(url[url.rfind("/")+1:])
    filename = urllib.parse.unquote(filename)

    if "media=" in filename:
        # print(filename)
        filename = re.findall("media=(.+)", filename)[0]
    # print(filename)

    filepath = lecture["folder"] + "/" + filename

    filepath = os.path.join(script_dir, filepath)

    return filename, filepath


def writeFile(filename, response, url, hash, filepath):
    print("opening file: " + filepath)
    with open(filepath, 'wb') as fd:
        if(lecture["download"]):
            fd.write(response.content) ### debug
            fd.close
            # add file to the list of downloaded objects
            print("downloaded " + filename)
        if(url in linkList):
            if(response.status_code == 401):
                return
            notify(lecture, filename, url,  '_Updated_ file online for ')
        else:
            notify(lecture, filename, url,  'New file online for ')
            linkList.add(url)

        hashList.add(hash)
        recentList.append(url)
        #print("end of write file " + filename)


def notify(lecture, filename, url, string):
    friendlyName = lecture["friendlyName"]

    telegramApi = 'https://api.telegram.org/bot' + telegramBotId + \
        '/sendMessage?chat_id=' + lecture["channel"] + '&text='
    if testingMode:
        telegramApi = 'https://api.telegram.org/bot' + telegramBotId + \
            '/sendMessage?chat_id=' + telegramDevChannel + '&text='

    requestStr = telegramApi + string + \
        '*' + friendlyName + '*: ' + \
        ' [' + filename + '](' + urllib.parse.quote(url) + \
        ')' + '&parse_mode=Markdown'
    requests.post(requestStr)
    print(requestStr)


def download(url, lecture):
    response = requests.get(url, auth=HTTPBasicAuth(
        ldapuser, ldappw))
    hash = hashlib.md5(response.content).digest()
    #print(hash, ":", not hash in hashList)
    if(response.status_code == 200 and not hash in hashList or response.status_code == 401):
        
        expected_length = response.headers.get('Content-Length')
        if expected_length is not None:
            actual_length = response.raw.tell()
            expected_length = int(expected_length)
            if actual_length < expected_length:
                raise IOError(
                    'incomplete read ({} bytes read, {} more expected)'.format(
                        actual_length,
                        expected_length - actual_length
                    )
                )

        filename, filepath = calcFilename(response, url, lecture)
        writeFile(filename, response, url, hash, filepath)
        print("end of download")
    elif(not hash in hashList):
        print(url, ":", response.status_code)


def checkUrl(link, lecture):
    if(link == "https://polybox.ethz.ch/index.php/s/YQC5Y0iuROmuNCD" or link == "https://polybox.ethz.ch/index.php/s/l2cCjDZZpwRlFRN"):
        #print("this is a special case")
        link = ""
        return
    if (link[-4:] == ".pdf") or (link[-5:] == ".docx") or (link[-4:] == ".zip") or (link[:15] == "https://polybox"):
        site = lecture["url"]
        if not (link[:4] == "http"):
            link = urllib.parse.urljoin(site, link)

            #print('link: ', link)
        if link[:15] == "https://polybox":
            link = link + "/download"

        if link in recentList or not link in linkList:
            download(link, lecture)
        #print("end of checkUrl")

def getLinks(lecture):
    http = httplib2.Http()
    status, response = http.request(lecture["url"])

    for link in BeautifulSoup(response, "html.parser", parse_only=SoupStrainer('a')):
        #print("link: ", link)
        if link.has_attr('href'):
            checkUrl(link['href'], lecture)
    #print("end of getLinks")

def loadDump(setVar, file):
    #setVar = set()
    try:
        dmp = open(file + ".dmp", "rb")
        setVar = pickle.load(dmp)
        print("return dump", file)
        return setVar
    except EOFError:
        dmp.close()
        print("EOF")
        return setVar
        pass
    except FileNotFoundError:
        print("fnf")
        return setVar
        pass
    else:
        dmp.close()


# initialize storage
hashList = set()
linkList = set()
recentList = collections.deque(maxlen=20)
# recentList.append("test")

hashList = loadDump(hashList, "hashList")
#print(hashList, "hashList")

linkList = loadDump(linkList, "linkList")
#print(linkList, "linkList")

recentList = loadDump(recentList, "recentList")
# recentList.append("test")
#print(recentList, "recentList")


for lecture in lectures:
    if not os.path.exists(lecture["folder"]):
        os.mkdir(lecture["folder"])
        print("Directory ", lecture["folder"],  " Created ")
    getLinks(lecture)
    #print("after lecture")

#print("before dmp")
def saveDump(list, file):
    #print("try to safe dump")
    dmp = open(file + ".dmp", "wb")
    pickle.dump(list, dmp)
    dmp.close()
    print("success saving ", file)


saveDump(hashList, "hashList")
saveDump(linkList, "linkList")
saveDump(recentList, "recentList")
