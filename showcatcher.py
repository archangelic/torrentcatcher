#!/usr/bin/python
#
# 	Showcatcher - Takes urls from text files and downloads them using transmission
# 	Copyright (C) 2014  Michael Hancock
#
# 	This program is free software: you can redistribute it and/or modify
# 	it under the terms of the GNU General Public License as published by
# 	the Free Software Foundation, either version 3 of the License, or
# 	(at your option) any later version.
#
# 	This program is distributed in the hope that it will be useful,
# 	but WITHOUT ANY WARRANTY; without even the implied warranty of
# 	MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# 	GNU General Public License for more details.
#
# 	You should have received a copy of the GNU General Public License
# 	along with this program.  If not, see <http://www.gnu.org/licenses/>.

import requests
import os
import os.path as path
import subprocess
import logging
from feeder import main as feeder
from posterget import main as posterget
from configobj import ConfigObj
appPath = path.dirname(os.path.abspath(__file__))
if appPath == '':
	appPath = "./"
else:
	appPath = appPath + '/'
	
if path.isfile(appPath + 'config.ini') == True:
	config = ConfigObj(appPath + 'config.ini')
else:
	print "Configuration file not found."
	print "Enter absolute or relative path to your configuration file."
	configlocation = raw_input("--> ")
	while (path.isfile(configlocation) == False) | (configlocation.endswith('.ini') == False):
		print "Invalid location. Try again. "
		configlocation = raw_input("--> ")
	config = ConfigObj(configlocation)
	appPath = path.dirname(path.abspath(configlocation)) + '/'

#This is where the files from feeder and posterget should be put
cache = appPath + 'cache/'
xmlcache = appPath + 'xmlcache/'
#And this is where we will put them once they are done
archive = appPath + 'archive/'
logfile = appPath + 'logfile.log' 
#api key for Pushbullet
api = config['pushkey']

#Creates a logger to keep track of things going on in logfile.log
logging.basicConfig(format='[%(levelname)s] [%(asctime)s] %(message)s', filename=logfile, level = logging.INFO, datefmt="%m-%d-%y %H:%M:%S")
#Allows logging to the terminal when running manually
console = logging.StreamHandler()
formatter = logging.Formatter(fmt = "[%(levelname)s] %(message)s")
console.setFormatter(formatter)
logging.getLogger('').addHandler(console)

logging.info("Starting")

if path.isdir(cache) == False:
	logging.error("Directory '%s' does not exist" % (cache))
	os.mkdir(cache)
	logging.info("Created directory '%s'" % (cache))
	
if path.isdir(archive) == False:
	logging.error("Directory '%s' does not exist" % (archive))
	os.mkdir(archive)
	logging.info("Created directory '%s'" % (archive))
	
if path.isdir(xmlcache) == False:
	logging.error("Directory '%s' does not exist" % (xmlcache))
	os.mkdir(xmlcache)
	logging.info("Created directory '%s'" % (xmlcache))

try:
	feedmsg,arcount,cacount = feeder()
	if arcount != 0:
		logging.info('%s shows already in archive' % arcount)
	if cacount != 0:
		logging.info('%s shows ready to be downloaded' % cacount)
	for i in feedmsg:
		logging.info(feedmsg[i])
except:
	logging.error('Could not access rss feeds')
	
filelist = os.listdir(cache)
	
#Create a command to run
#This creates a transmission-cli session to run in a screen with the id transmission
#Will start detached
def transmission(magnet):
	# Executes the command in the system
	# Requires: screen and transmission-cli
	transmissioncommand = "transmission-remote -a %s" % (magnet)
 	success = os.system(transmissioncommand)
	if success == 0:
		logging.info("Download started")
	else:
		logging.error("Transmission remote error")
	return success

#This will prepare a note to push to devices over Pushbullet
def pushbullet(name):
	body = "File %s was added to transmission." % (name)
	payload = {'type': 'note', 'title':'Downloading new file', 'body':body}
	note = requests.post('https://api.pushbullet.com/api/pushes', data = payload, auth = (api, ""))
	if str(note) == "<Response [200]>":
 		logging.info("Push message for %s sent successfully" % (name))
 	else:
 		logging.error("An error occured while sending push note")
		logging.error(note)

if filelist != []:
	for name in filelist:
		location = cache + "/" + name
		postermsg = posterget(location)
		logging.info(postermsg)
		with open (location, "r") as myfile:
			data = myfile.read().replace('\n', '')
		link,show,se,ep = data.split(' : ')
		if transmission(link) == 0:
			pushbullet(name)
			os.rename(location, archive + "/" + name)
			logging.info("Archived %s" % (name))
else:
	logging.info("No files to download")
  
logging.info("Completed")
