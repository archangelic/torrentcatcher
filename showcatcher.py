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
import logging

#This is where the files from IFTTT should be put
cache = 'cache'
#And this is where we will put them once they are done
archive = 'archive'
#api key for Pushbullet
api = '<your api key here>'

#Creates a logger to keep track of things going on in logfile.log
logging.basicConfig(format='[%(levelname)s] [%(asctime)s] %(message)s', filename='logfile.log', level = logging.INFO, datefmt="%m-%d-%y %H:%M:%S")
#Allows logging to the terminal when running manually
console = logging.StreamHandler()
formatter = logging.Formatter(fmt = "[%(levelname)s] %(message)s")
console.setFormatter(formatter)
logging.getLogger('').addHandler(console)
	
logging.info("Starting")

if os.path.isdir(cache) == False:
	logging.error("Directory '%s' does not exist" % (cache))
	os.mkdir(cache)
	logging.info("Created directory '%s'" % (cache))
	
if os.path.isdir(archive) == False:
	logging.error("Directory '%s' does not exist" % (archive))
	os.mkdir(archive)
	logging.info("Created directory '%s'" % (archive))

filelist = os.listdir(cache)
	
#Create a command to run
#This creates a transmission-cli session to run in a screen with the id transmission
#Will start detached
def transmission(magnet, number):
	if number == 1: number = ''
	number = str(number)
	# Executes the command in the system
	# Requires: screen and transmission-cli
	transmissioncommand = "screen -d -m -S transmission%s transmission-cli %s" % (number, magnet)
 	os.system(transmissioncommand)
	logging.info("Download started on screen transmission%s" % (number))

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

x = 1
if filelist != []:
	for i in filelist:
		location = cache + "/" + i
		with open (location, "r") as myfile:
			data = myfile.read().replace('\n', '')
		name = i[:len(i)-4]
		transmission(data, x)
		pushbullet(name)
		os.rename(location, archive + "/" + i)
		logging.info("Archived %s" % (i))
		x += 1
else:
	logging.info("No files to download")
  
logging.info("Completed")