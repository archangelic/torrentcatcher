#!/usr/bin/python
import requests
from os import environ
from tagger import main as tagger
from configobj import ConfigObj
appPath = os.path.dirname(__file__) + '/'
config = ConfigObj(appPath + 'config.ini')

name = environ['TR_TORRENT_NAME']
api = config['pushkey']

def pushbullet(payload):
	requests.pos('https://api.pushbullet.com/api/pushes', data = payload, auth = (api, ""))
	
if name.endswith(".mp4"):
	tagger(name)
body = "File " + name + " was successfully downloaded."
payload = {'type': 'note', 'title':'Download completed', 'body':body}
pushbullet(payload)
