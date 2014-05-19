#!/usr/bin/python
import requests
from os import environ
from tagger import main as tagger

name = environ['TR_TORRENT_NAME']
api = 'v1MA1cGJB8hungKO8FQZ7eV6lnv5EPWVEoujvqYP8DzAy'

def pushbullet(payload):
	requests.pos('https://api.pushbullet.com/api/pushes', data = payload, auth = (api, ""))
	
if name.endswith(".mp4"):
	tagger(name)
body = "File " + name + " was successfully downloaded."
payload = {'type': 'note', 'title':'Download completed', 'body':body}
pushbullet(payload)
