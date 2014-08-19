#!/usr/bin/python
import os, subprocess, shlex, validate, argparse
import os.path as path
from datetime import datetime
from feedparser import parse
from configobj import ConfigObj as configobj

appPath = path.dirname(path.abspath(__file__))
if appPath == '':
	appPath = "."
dataPath = path.join(appPath, '.torrentcatcher')
	
keys = {
	'archive' : path.join(dataPath, 'archive'),
	'cache' : path.join(dataPath, 'cache'),
	'log' : path.join(dataPath, 'torrentcatcher.log'),
	'config' : path.join(dataPath, 'config')}

if path.isdir(dataPath) == False:
	os.mkdir(dataPath)

if path.isdir(keys['cache']) == False:
	os.mkdir(keys['cache'])
	
if path.isdir(keys['archive']) == False:
	os.mkdir(keys['archive'])
	
class Feeder():
	def __init__(self, keys):
		self.configfile = keys['config']
		self.archive = keys['archive']
		self.cache = keys['cache']
		self.log = keys['log']
		self.arcdict = {}
		self.cachedict = {}
		self.arclist = os.listdir(self.archive)
		self.cachelist = os.listdir(self.cache)
		self.cachelist.sort()
		for self.i in self.arclist:
			self.arcdict[self.i] = '1'
		for self.i in self.cachelist:
			self.cachedict[self.i] = '1'
				
	def write(self):
		self.entries = []
		self.count = {'arc' : 0, 'cache' : 0, 'write' : 0}
		self.config = configobj(self.configfile)
		self.feeds = self.config['feeds']
		if self.feeds == {}:
			self.logger("[ERROR] No feeds found in feeds file! Use '-f' or '--add-feed' options to add torrent feeds")
			return 0
		for self.i in self.feeds:
			self.logger('[FEEDS] Reading entries for feed "' + self.i + '"')
			self.feeddat = parse(self.feeds[self.i])
			self.entries = self.feeddat.entries
		for self.i in self.entries:
			self.title = self.i['title'].replace(' ', '.')
			self.link = self.i['link']
			try:
				if self.arcdict[self.title]:
					self.count['arc'] += 1
			except:
				try:
					if self.cachedict[self.title]:
						self.count['cache'] += 1
				except:
					with open(path.join(self.cache, self.title), 'w') as self.myfile:
						self.myfile.write(self.link)
					self.count['write'] += 1
					self.logger('[QUEUED] ' + self.title + ' was added to queue')
		self.total = self.count['arc'] + self.count['cache'] + self.count['write']
		if (self.total) != 0:
			self.logger('[QUEUE COMPLETE] New Torrents: ' + str(self.count['write']))
			self.logger('[QUEUE COMPLETE] Already Queued: ' + str(self.count['cache']))
			self.logger('[QUEUE COMPLETE] Already Archived: ' + str(self.count['arc']))
		else:
			self.logger('[ERROR] No feed information found. Something is probably wrong.')
						
	def move(self, title):
		self.title = title
		os.rename(path.join(self.cache, self.title), path.join(self.archive, self.title))
		self.logger('[ARCHIVED] ' + self.title + ' was moved to archive.')
		
	def lister(self):
		if self.cachelist != []:
			self.cachelist.sort()
			print 'Torrents queued for download:'
			for self.each in self.cachelist:
				print self.each
		else:
			print 'No torrents queued for download.'
			
	def logger(self, message):
		self.message = message
		print self.message
		with open(self.log, 'a') as self.myfile:
			self.myfile.write(str(datetime.now().strftime('[%a %m/%d/%y %H:%M:%S]')) + self.message + '\n')

myFeeder = Feeder(keys)

def configreader():
	configfile = keys['config']
	cfg = """[transmission]
		hostname = string(default='localhost')
		port = string(default='9091')
		require_auth = boolean(default=False)
		username = string(default='')
		password = string(default='')
		download_directory = string(default='')
		
		[feeds]"""
	spec = cfg.split("\n")
	config = configobj(configfile, configspec=spec)
	validator = validate.Validator()
	config.validate(validator, copy=True)
	config.filename = configfile
	config.write()
	return config

def transmission(title, trconfig):
	host = trconfig['hostname']
	port = trconfig['port']
	auth = trconfig['require_auth']
	authopt = trconfig['username'] + ':' + trconfig['password']
	downdir = trconfig['download_directory']
	myFeeder.logger('[TRANSMISSION] Starting download for ' + title)
	with open(path.join(cache, title), 'r') as myfile:
		url = myfile.read()
	if auth == False:
		command = 'transmission-remote ' + host + ':' + port + ' -a "' + url + '"'
	else:
		command = 'transmission-remote  ' + host + ':' + port + ' -n ' + authopt + ' -a "' + url + '"'
	if downdir != '':
		command = command + ' -w ' + downdir
	transcmd = subprocess.Popen(shlex.split(command), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
	output,error = transcmd.communicate()
	if error == "":
		myFeeder.move(title)
		myFeeder.logger('[TRANSMISSION] ' + output.strip('\n'))
		return 0
	else:
		myFeeder.logger('[ERROR] ' + error.strip('\n'))
		return 1

def addfeed(name, url):
	config = configreader()
	config['feeds'][name] = url
	config.write()
	myFeeder.logger('[FEEDS] Feed "' + name + '" added successfully.')
	
def logreader():
	logcmd = "sed -n '/\[TORRENTCATCHER\]/=' " + keys['log']
	logproc = subprocess.Popen(shlex.split(logcmd), stdout=subprocess.PIPE)
	output = logproc.communicate()
	lines = output[0].split('\n')
	linelist = []
	for each in lines:
		if each != '':
			linelist.append(int(each))
	linelist.sort()
	startline = lines[len(linelist)-1]
	logproc = subprocess.Popen(shlex.split('tail -n +' + str(startline) + ' ' + keys['log']), stdout=subprocess.PIPE)
	rawout = logproc.communicate()
	output = rawout[0].split('\n')
	for each in output:
		if each != '':
			print each
	
if __name__ == '__main__':
	cache = keys['cache']
	cachelist = os.listdir(cache)
	cachelist.sort()
	config = configreader()
	trconfig = config['transmission']
	parser = argparse.ArgumentParser()
	parser.add_argument('-a', '--archive', help="Moves all currently queued torrents to the archive.", action="store_true")
	parser.add_argument('-d', '--download', help="Sends all queued torrents to Transmission.", action="store_true")
	parser.add_argument('-f', '--add-feed', help="Brings up the add feed utility.", action="store_true")
	parser.add_argument('-l', '--list', help="Lists all queued torrents.", action="store_true")
	parser.add_argument('-L', '--log', help="Shows log from most recent full run.", action="store_true")
	parser.add_argument('-q', '--queue', help="Checks all feeds for new torrents to add to the queue. DOES NOT SEND TO TRANSMISSION.", action="store_true")
	args = parser.parse_args()
	if args.archive == True:
		myFeeder.logger('[ARCHIVE ONLY] Moving all torrents in queue to the archive')
		if cachelist == []:
			myFeeder.logger('[ARCHIVE COMPLETE] No torrents to archive')
		else:
			for each in cachelist:
				myFeeder.move(each)
			myFeeder.logger('[ARCHIVE COMPLETE] All torrents archived successfully')
	if args.download == True:
		myFeeder.logger('[DOWNLOAD ONLY] Starting download of already queued torrents')
		if cachelist == []:
			myFeeder.logger('[DOWNLOAD COMPLETE] No torrents to download')
		else:
			errors = 0
			for each in cachelist:
				test = transmission(each, trconfig)
				errors += test
			if errors > 0:
				myFeeder.logger('[DOWNLOAD COMPLETE] There were errors adding torrents to Transmission')
			else:
				myFeeder.logger('[DOWNLOAD COMPLETE] Initiated all downloads successfully')
	if args.add_feed == True:
		name = raw_input('Enter name for feed: ')
		url = raw_input('Enter URL for feed: ')
		addfeed(name, url)
	if args.list == True:
		myFeeder.lister()
	if args.log == True:
		logreader()
	if args.queue == True:
		myFeeder.logger('[QUEUE ONLY] Checking feeds for new torrents to queue')
		myFeeder.write()
	if (args.archive == False) & (args.download==False) & (args.add_feed==False) & (args.list==False) & (args.log==False) & (args.queue==False):
		myFeeder.logger('[TORRENTCATCHER] Starting Torrentcatcher')
		myFeeder.write()
		cachelist = os.listdir(cache)
		cachelist.sort()
		if cachelist == []:
			myFeeder.logger('[TORRENTCATCHER COMPLETE] No torrents to download')
		else:
			errors = 0
			for each in cachelist:
				test = transmission(each, trconfig)
				errors += test
			if errors > 0:
				myFeeder.logger('[TORRENTCATCHER COMPLETE] There were errors adding torrents to Transmission')
			else:
				myFeeder.logger('[TORRENTCATCHER COMPLETE] Initiated all downloads successfully')
