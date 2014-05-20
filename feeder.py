from feedparser import parse
import os
from urllib2 import urlopen
from urllib import urlretrieve
from configobj import ConfigObj
config = ConfigObj('/home/michael/Dropbox/Projects/showcatcher/config.ini')

appPath = config['appPath']
cache = appPath + 'cache'
archive = appPath + 'archive'
feedfile = appPath + 'feeds'

arclist = os.listdir(archive)
cachelist = os.listdir(cache)
arcdict = {}
cachedict = {}
message = {}
show = {}
feeds = []
entries = []

with open(feedfile, 'r') as myfile:
	feeddata = myfile.read().split('\n')
for each in feeddata:
	if each != '':
		feeds.append(each)
for each in feeds:
	data = parse(each)
	for each in data.entries:
		entries.append(each)

def writer(x, title):
	z = 1
	y = 0
	entry = entries[x]
	show['1'] = entry['link']
	desc = entry['description']
	desc = desc.split('; ')
	if len(desc) == 4:
		for i in desc:
			if y == 0:
				showname,name = desc[y].split(': ')
				show['2'] = name
			elif y == 2:
				senum,num = desc[y].split(': ')
				show['3'] = num
			elif y == 3:
				epnum,num = desc[y].split(': ')
				show['4'] = num
			y += 1
		filename = cache + "/" + title
		for i in show:
			if z == 4:
				with open(filename, 'a') as file:
					file.write(show[str(z)])
			else:
				with open(filename, 'a') as file:
					file.write(show[str(z)] + ' : ')
			z += 1
		return True
	else:
		return False
	
def main():
	x = 0
	arcount = 0
	cacount = 0
	for thing in arclist:
		arcdict[thing] = '1'
	for thing in cachelist:
		cachedict[thing] = '1'
	for i in entries:
		title = entries[x]['filename'].replace('.[eztv].torrent', '')
		try:
			if arcdict[title]:
				arcount += 1
		except:
			try:
				if cachedict[title]:
					cacount += 1
			except:	
				if writer(x, title) == True:
					message[x] = "Created: " + title
		x += 1
	return message, arcount, cacount

if __name__ == '__main__':
	main()