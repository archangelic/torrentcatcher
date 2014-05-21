import os
from urllib import urlretrieve
from urllib2 import urlopen
from bs4 import BeautifulSoup
import time
from configobj import ConfigObj
appPath = os.path.dirname(__file__)
if appPath == '':
	appPath = "./"
else:
	appPath = appPath + '/'
config = ConfigObj(appPath + 'config.ini')

cache = appPath + 'cache/'
xmlcache = appPath + 'xmlcache/'
torrentfolder = config['torrentfolder']
apikey = config['tvdbkey']
tvdb = 'http://thetvdb.com/'
banners = tvdb + 'banners/'

cachelist = os.listdir(cache)

def stamper():
	servertime = urlopen('http://thetvdb.com/api/Updates.php?type=none')
	soup = BeautifulSoup(servertime)
	with open(xmlcache + 'timestamp', 'w') as myfile:
		myfile.write(soup.time.string)

def update(showid):
	with open(xmlcache + 'timestamp', 'r') as myfile:
		time = myfile.read()
	urlretrieve('http://thetvdb.com/api/Updates.php?type=all&time=' + time, filename = xmlcache + 'updatelist.xml')
	with open(xmlcache + 'updatelist.xml', 'r') as myfile:
		data = myfile.read()
	soup = BeautifulSoup(data)
	series = soup.series.find_all(showid)
	if series == []:
		return False
	elif series[0].string == showid:
		return True

def gatherdata(showid):
	xmlfile = xmlcache + showid + '.xml'
	urlretrieve('%sapi/%s/series/%s/all/en.xml' % (tvdb,apikey,showid), filename = xmlfile)
	with open(xmlfile, 'r') as myfile:
		data = myfile.read()
	soup = BeautifulSoup(data)
	poster = soup.find('poster').string
	if poster.endswith('.png'):
		posterfile = xmlcache + showid + '.png'
		urlretrieve(banners + poster, filename = posterfile)
	elif poster.endswith('.jpg'):
		posterfile = xmlcache + showid + '.jpg'
		urlretrieve(banners + poster, filename = posterfile)

def getshowid(name, xdict):
	try:
		if xdict[name]:
			with open(xmlcache + name, 'r') as myfile:
				showid = myfile.read()
			return showid
	except:
		url = '%sapi/GetSeries.php?seriesname=%s' % (tvdb,name)
		url = url.replace(' ', '%20')
		showxml = urlopen(url)
		soup = BeautifulSoup(showxml)
		search = soup.find('id')
		showid = search.string
		with open(xmlcache + name, 'w') as myfile:
			myfile.write(showid)
		gatherdata(showid)
		return showid
	
def main(location):
	x = 0
	xmllist = []
	xmllist = os.listdir(xmlcache)
	xmldict = {}
	for i in xmllist:
		xmldict[i] = '1'
	with open(location, 'r') as myfile:
		data = myfile.read()
	url,name,se,ep = data.split(' : ')
	showid = getshowid(name, xmldict)
	if os.path.isfile(xmlcache + 'timestamp') == False:
		stamper()
	else:
		stamper()
	if update(showid) == True:
		gatherdata(showid)
	return "XML data gathered"

if __name__ == '__main__':
	for each in cachelist:
		location = cache + each
		main(location)
	