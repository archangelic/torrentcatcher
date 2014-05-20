from mutagen.mp4 import MP4 as mp4
from mutagen.mp4 import MP4Cover as mp4cover
from bs4 import BeautifulSoup as bsoup
import os
from configobj import ConfigObj
config = ConfigObj('/home/michael/Dropbox/Projects/showcatcher/config.ini')

appPath = config['appPath']
archive = appPath + 'archive'
xmlcache = appPath + 'xmlcache'
downdir = config['torrentfolder']

arclist = os.listdir(archive)
showlist = {}
arcdict = {}
for each in arclist:
	showlist[each + '.mp4'] = '1'
	arcdict[each] = '1'
downlist = os.listdir(downdir)

def arcdig(show):
	if arcdict[show]:
		with open(archive + show, 'r') as myfile:
			link,name,se,ep = myfile.read().split(' : ')
	return name,se,ep
			
def xmldig(name,se,ep):
	with open(xmlcache + name, 'r') as myfile:
		showid = myfile.read()
	location = xmlcache + showid + '.xml'
	with open(location, 'r') as myfile:
		soup = bsoup(myfile.read())
	show = soup.find('series')
	episodes = soup.find_all('episode')
	season = []
	for each in episodes:
		if each.find('seasonnumber').string == se:
			season.append(each)
	for each in season:
		if each.find('episodenumber').string == ep:
			episode = each
	selen = len(season)
	return episode, show, showid, selen
	
def tagbuilder(filename, episode, show, showid, selen):
	epinfo = {}
	epinfo['video'] = downdir + filename
	epinfo['selen'] = selen
	epinfo['episodename'] = episode.find('episodename').string
	epinfo['seriesname'] = show.find('seriesname').string
	epinfo['seasonnumber'] = int(episode.find('seasonnumber').string)
	epinfo['episodenumber'] = int(episode.find('episodenumber').string)
	epinfo['album'] = '%s, Season %s' % (show.find('seriesname').string, episode.find('seasonnumber').string)
	if os.path.isfile(xmlcache + showid + '.jpg'):
		epinfo['coverart'] = xmlcache + showid + '.jpg'
	elif os.path.isfile(xmlcache + showid + '.png'):
		epinfo['coverart'] = xmlcache + showid + '.png'
	overview = episode.find('overview').string
	if len(overview) > 255:
		description = overview.split('. ')
		description = description[0].replace('\n', ' ')
		epinfo['description'] = description + '.'
	else:
		description = overview.replace('\n', ' ')
		epinfo['description'] = description
	epinfo['type'] = "TV Show"
	atomicparsley = 'AtomicParsley %(video)s --title "%(episodename)s" --artist "%(seriesname)s" --album "%(album)s" --TVShowName "%(seriesname)s" --tracknum %(episodenumber)d/%(selen)d  --TVSeasonNum %(seasonnumber)d --TVEpisodeNum %(episodenumber)d --disk %(seasonnumber)d --description "%(description)s" --artwork %(coverart)s --stik "%(type)s"' % epinfo
	os.system(atomicparsley)
	os.system('rm ' + epinfo['video'])

def main(filename):
	filenoext = filename.replace('.mp4', '')
	name,se,ep = arcdig(filenoext)
	episode,show,showid,selen = xmldig(name,se,ep)
	tagbuilder(filename, episode, show, showid, selen)
	
if __name__ == '__main__':
	count = 0
	for each in os.listdir(downdir):
		if each.endswith('.mp4') == True:
			count += 1
			print count, each
			main(each)