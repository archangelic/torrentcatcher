#!/usr/bin/python
###########################################################################
# torrentcatcher v1.0.1
#     Copyright (C) 2014  Michael Hancock
#
#     This program is free software: you can redistribute it and/or modify
#     it under the terms of the GNU General Public License as published by
#     the Free Software Foundation, either version 3 of the License, or
#     (at your option) any later version.
#
#     This program is distributed in the hope that it will be useful,
#     but WITHOUT ANY WARRANTY; without even the implied warranty of
#     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#     GNU General Public License for more details.
#
#     You should have received a copy of the GNU General Public License
#     along with this program.  If not, see <http://www.gnu.org/licenses/>.
###########################################################################

import argparse, shlex, subprocess, sys, validate
import sqlite3 as lite
from configobj import ConfigObj as configobj
from datetime import datetime
from feedparser import parse
from os import path, mkdir
from tabulate import tabulate

class Torrentcatcher():
	def __init__(self, keys):
		self.configfile = keys['config']
		self.log = keys['log']
		# Creates database if it does not exist
		self.con = lite.connect(keys['database'])
		self.cur = self.con.cursor()
		self.cur.execute('CREATE TABLE IF NOT EXISTS torrents(id INTEGER PRIMARY KEY, name TEXT, url TEXT, source TEXT, downStatus BOOLEAN);')
		self.cur.execute('CREATE TABLE IF NOT EXISTS feeds(id INTEGER PRIMARY KEY, name TEXT, url TEXT);')
		self.con.commit()

	# Function to parse the config file and return the dictionary of values. Also creates a config file if one does not exist.
	def configreader(self):
		cfg = """hostname = string(default='localhost')
			port = string(default='9091')
			require_auth = boolean(default=False)
			username = string(default='')
			password = string(default='')
			download_directory = string(default='')"""
		spec = cfg.split("\n")
		config = configobj(self.configfile, configspec=spec)
		validator = validate.Validator()
		config.validate(validator, copy=True)
		config.filename = self.configfile
		config.write()
		return config
	
	def write(self, name, url, source):
		self.cur.execute("INSERT INTO torrents(name, url, source, downStatus) VALUES (?, ?, ?, 0);", (name, url, source))
		self.con.commit()

	# Function to write entries from the feed to the database
	def feeder(self):
		entries = []
		count = {'arc' : 0, 'cache' : 0, 'write' : 0}
		self.cur.execute('SELECT * FROM feeds;')
		feeds = self.cur.fetchall()
		if feeds == []:
			self.logger("[ERROR] No feeds found! Use '-f' or '--add-feed' options to add torrent feeds")
			return 0
		for i in feeds:
			self.logger('[FEEDS] Reading entries for feed "' + i[1] + '"')
			feeddat = parse(i[2])
			entries = feeddat.entries
			feedname = i[1]
			for i in entries:
				title = i['title']
				link = i['link']
				self.cur.execute("SELECT EXISTS(SELECT * FROM torrents WHERE name=?);", (title,))
				test = self.cur.fetchall()
				if test[0][0] != 1:
					self.write(title, link, feedname)
					count['write'] += 1
					self.logger('[QUEUED] ' + title + ' was added to queue')
				else:
					self.cur.execute("SELECT * FROM torrents WHERE name=?", (title,))
					status = self.cur.fetchall()
					if status[0][4] == 1:
						count['arc'] += 1
					elif status[0][4] == 0:
						count['cache'] += 1
		total = count['arc'] + count['cache'] + count['write']
		if total != 0:
			self.logger('[QUEUE COMPLETE] New Torrents: ' + str(count['write']))
			self.logger('[QUEUE COMPLETE] Already Queued: ' + str(count['cache']))
			self.logger('[QUEUE COMPLETE] Already Archived: ' + str(count['arc']))
		else:
			self.logger('[ERROR] No feed information found. Something is probably wrong.')

	# Function updates given entries to show they have been sent to the Archive
	def move(self, title):
		self.cur.execute("UPDATE torrents SET downStatus=1 WHERE name=?", (title,))
		self.con.commit()
		self.logger('[ARCHIVED] ' + title + ' was moved to archive.')

	# Homebrewed logging solution. Any passed messages are outputted to the console as well as appended to the log
	def logger(self, message):
		print message
		with open(self.log, 'a') as myfile:
			myfile.write(str(datetime.now().strftime('[%a %m/%d/%y %H:%M:%S]')) + message + '\n')

	# Add Feed utility. Takes the name and URL and appends it to the config file
	def addfeed(self, name, url):
		self.cur.execute('INSERT INTO feeds(name, url) VALUES (?,?);', (name, url))
		self.con.commit()
		self.logger('[FEEDS] Feed "' + name + '" added successfully.')

	# Searches the database for a given query
	def torsearch(self, category, query):
		resultlist = []
		if category == 'id':
			try:
				qtest = int(query)
				self.cur.execute("SELECT * FROM torrents WHERE id LIKE ?", (query,))
				results = self.cur.fetchall()
				if results == []:
					print "No results found in '{0}' for '{1}".format(category, query)
				else:
					for each in results:
						if each[4] == 0:
							status = 'Queue'
						elif each[4] == 1:
							status = 'Archive'
						resultlist.append([each[0], each[1], each[3], status])
					print tabulate(resultlist, ['ID', 'Name', 'Source', 'Status'])
			except:
				print "Please enter a valid ID number for ID searches."
		else:
			if category == 'name':
				self.cur.execute("SELECT * FROM torrents WHERE name LIKE ?;", ('%'+query+'%',))
			elif category == 'source':
				self.cur.execute("SELECT * FROM torrents WHERE source LIKE ?;", ('%'+query+'%',))
			results = self.cur.fetchall()
			if results == []:
				print "No results found in '{0}' for '{1}'".format(category, query)
			else:
				for each in results:
					if each[4] == 0:
						status = 'Queue'
					elif each[4] == 1:
						status = 'Archive'
					resultlist.append([each[0], each[1], each[3], status])
				print tabulate(resultlist, ['ID', 'Name', 'Source', 'Status'])

	# Function to list out given requests
	def lister(self, cat):
		resultlist = []
		down = 0
		status = ''
		if cat == 'feeds':
			self.cur.execute('SELECT * FROM feeds;')
			feedlist = self.cur.fetchall()
			if feedlist == []:
				print 'No feeds were found!'
				print "Use the '-f' or '--add-feed' option to add feeds."
			else:
				for each in feedlist:
					resultlist.append([each[0], each[1], each[2]])
				print tabulate(resultlist, ['ID', 'Name', 'URL'], tablefmt='pipe')
		if cat == 'archive':
			down = 1
			status = 'Archive'
		if cat == 'queue':
			down = 0
			status = 'Queue'
		if (cat == 'archive') or (cat == 'queue'):
			self.cur.execute('SELECT * FROM torrents WHERE downStatus=?;', (down,))
			results = self.cur.fetchall()
			for each in results:
				resultlist.append([each[0], each[1], each[3], status])
			print tabulate(resultlist, ['ID', 'Name', 'Source', 'Status'], tablefmt='pipe')

	# Function to run the Archive only feature
	def archive(self, selID):
		self.logger('[ARCHIVE ONLY] Moving selected torrents in queue to the archive')
		if selID == 'all':
			self.cur.execute("SELECT * FROM torrents WHERE downStatus=0")
			cachelist = self.cur.fetchall()
			if cachelist == []:
				self.logger('[ARCHIVE COMPLETE] No torrents to archive')
			else: 
				for each in cachelist:
					self.move(each[1])
				self.logger('[ARCHIVE COMPLETE] Archive process completed successfully')
		else:
			for each in args.archive:
				if each != 'all':
					self.cur.execute("SELECT * FROM torrents WHERE id=?", (each,))
					selection = self.cur.fetchall()
					seltor = selection[0]
					if seltor[4] == 0:
						self.move(seltor[1])
					elif seltor[4] == 1:
						self.logger('[ARCHIVE] %s is already in the archive.' % (seltor[1]))
			self.logger('[ARCHIVE COMPLETE] Archive process completed successfully')

	# Function to add files to Transmission over transmission-remote
	def transmission(self, title, url):
		config = self.configreader()
		host = config['hostname']
		port = config['port']
		auth = config['require_auth']
		authopt = config['username'] + ':' + config['password']
		downdir = config['download_directory']
		self.logger('[TRANSMISSION] Starting download for ' + title)
		if not auth:
			command = 'transmission-remote ' + host + ':' + port + ' -a "' + url + '"'
		else:
			command = 'transmission-remote  ' + host + ':' + port + ' -n ' + authopt + ' -a "' + url + '"'
		if downdir != '':
			command = command + ' -w ' + downdir
		transcmd = subprocess.Popen(shlex.split(command), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
		output,error = transcmd.communicate()
		if error == "":
			self.move(title)
			self.logger('[TRANSMISSION] ' + output.strip('\n'))
			return 0
		else:
			self.logger('[ERROR] ' + error.strip('\n'))
			return 1

	# Parses out the log for the most recent run of torrentcatcher. Shows the entire log since the last time the command sans arguments ran.
	def logreader(self):
		logcmd = "sed -n '/\[TORRENTCATCHER\]/=' " + self.log
		logproc = subprocess.Popen(shlex.split(logcmd), stdout=subprocess.PIPE)
		output = logproc.communicate()
		lines = output[0].split('\n')
		linelist = []
		for each in lines:
			if each != '':
				linelist.append(int(each))
		linelist.sort()
		startline = lines[len(linelist)-1]
		logproc = subprocess.Popen(shlex.split('tail -n +' + str(startline) + ' ' + self.log), stdout=subprocess.PIPE)
		rawout = logproc.communicate()
		output = rawout[0].split('\n')
		for each in output:
			if each != '':
				print each
	
	# Function to run the Download only feature
	def download(self, selID):
		self.logger('[DOWNLOAD ONLY] Starting download of already queued torrents')
		if selID == 'all':
			self.cur.execute("SELECT * FROM torrents WHERE downStatus=0")
			cachelist = cur.fetchall()
			if cachelist == []:
				self.logger('[DOWNLOAD COMPLETE] No torrents to download')
			else:
				errors = 0
				for each in cachelist:
					test = self.transmission(each[1], each[2])
					errors += test
				if errors > 0:
					self.logger('[DOWNLOAD COMPLETE] There were errors adding torrents to Transmission')
				else:
					self.logger('[DOWNLOAD COMPLETE] Initiated all downloads successfully')
		else:
			errors = 0
			for each in selID:
				if each != 'all':
					self.cur.execute("SELECT * FROM torrents WHERE id=?", (each,))
					selection = self.cur.fetchall()
					seltor = selction[0]
					test = self.transmission(seltor[1], seltor[2])
					errors +=test
			if errors > 0:
				self.logger('[DOWNLOAD COMPLETE] There were errors adding torrents to Transmission')
			else:
				self.logger('[DOWNLOAD COMPLETE] Initiated all downloads successfully')	

	# The full automatic torrentcatcher
	def torrentcatcher(self):
		self.logger('[TORRENTCATCHER] Starting Torrentcatcher')
		self.feeder()
		self.cur.execute("SELECT * FROM torrents WHERE downStatus=0")
		cachelist = self.cur.fetchall()
		if cachelist == []:
			self.logger('[TORRENTCATCHER COMPLETE] No torrents to download')
		else:
			errors = 0
			for each in cachelist:
				test = self.transmission(each[1], each[2])
				errors += test
			if errors > 0:
				self.logger('[TORRENTCATCHER COMPLETE] There were errors adding torrents to Transmission')
			else:
				self.logger('[TORRENTCATCHER COMPLETE] Initiated all downloads successfully')

# Function to check if file location is writeable. Only creates up to one subdirectory. Will error otherwise.
def filecheck(filepath):
	x = path.abspath(filepath)
	xpath = path.dirname(x)
	if not path.isdir(xpath):
		try:
			mkdir(filepath)
			return xpath
		except OSError,e:
			print '[OSError]', e
			quit()
		except IOError,e:
			print '[IOError]', e
			quit()

if __name__ == '__main__':
	# Finds the location of torrentcatcher
	appPath = path.dirname(path.abspath(__file__))
	if appPath == '':
		appPath = "."
	dataPath = path.join(appPath, 'data')
	# Dictionary of values for Torrentcatcher class
	keys = {
		'log' : path.join(dataPath, 'torrentcatcher.log'),
		'config' : path.join(dataPath, 'trconfig'),
		'database' : path.join(dataPath, 'torcatch.db')}
	# Creates data directory for config file, database, and log file
	if not path.isdir(dataPath):
		mkdir(dataPath)
	# Parsing out arguments for command line input
	parser = argparse.ArgumentParser(prog='torrentcatcher')
	parser.add_argument('-a', '--archive', nargs='+', metavar='all|ID', help="Moves selected torrents to the archive. Using the argument 'all' will move all currently queued torrents to the archive. Use the '--list' option to see IDs.")
	parser.add_argument('-C', nargs=1, metavar='<path to trconfig file>', help="Overrides default config file location. If the config file does not exist at given location, the file will be created there.")
	parser.add_argument('-d', '--download', nargs='+', metavar='all|ID', help="Moves selected torrents to Transmission.Using the argument 'all' will move all currently queued torrents to Transmission. Use the '--list' option to see IDs.")
	parser.add_argument('-D', nargs=1, metavar='<path to database>', help="Overrides default database location. If the database file does not exist at given location, it will be created there.")
	parser.add_argument('-f', '--add-feed', help="Starts the add feed utility.", action="store_true")
	parser.add_argument('-l', '--list', nargs=1, choices=['queue', 'archive', 'feeds'], help="Lists all items for given category.")
	parser.add_argument('-L', nargs=1, metavar='<path to log file>', help="Choose location for log output.")
	parser.add_argument('-q', '--queue', help="Checks all feeds for new torrents to add to the queue. DOES NOT SEND TO TRANSMISSION.", action="store_true")
	parser.add_argument('--search', nargs=1, choices=['name', 'source', 'id'], help="Searches archive and queue for given query. Can search by name, source, or ID number.")
	parser.add_argument('--showlog', help="Shows log from most recent full run.", action="store_true")
	parser.add_argument('--version', action='version', version='%(prog)s 1.1.0')
	args = parser.parse_args()
	# Check for custom data file locations
	if args.C != None:
		keys['config'] = filecheck(args.C[0])
	if args.D != None:
		keys['database'] = filecheck(args.D[0])
	if args.L != None:
		keys['log'] = filecheck(args.L[0])
	# Initialize Torrentcatcher class
	myData = Torrentcatcher(keys)
	# Create the configuration file if it does not exist
	myData.configreader()
	# Interprets arguments to their respective functions
	if args.archive != None:
		myData.archive(args.archive[0])
	if args.download != None:
		myData.download(args.download[0])
	if args.add_feed:
		name = raw_input('Enter name for feed: ')
		url = raw_input('Enter URL for feed: ')
		myData.addfeed(name, url)
	if args.list != None:
		myData.lister(args.list[0])
	if args.showlog:
		myData.logreader()
	if args.queue:
		myData.logger('[QUEUE ONLY] Checking feeds for new torrents to queue')
		myData.write()
	if args.search != None:
		query = raw_input('Enter query: ')
		myData.torsearch(args.search[0], query)
	if (args.archive==None) and (args.download==None) and (not args.add_feed) and (args.list==None) and (not args.showlog) and (not args.queue) and (args.search==None):
		myData.torrentcatcher()
