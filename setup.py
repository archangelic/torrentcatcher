#!/usr/bin/env python
from distutils.core import setup

setup(
	name = "torrentcatcher",
    packages = ['torrentcatcher'],
	version = "2.0.0",
	url = "https://github.com/archangelic/torrentcatcher",
	description = "Takes torrent or magnet links from rss feeds you provide, parses them and sends them to transmission via the transmission-remote command line utility.",
    author = "Michael Hancock",
    email = "michaelhancock89@gmail.com",
    download_url="https://github.com/archangelic/torrentcatcher/tarball/v2.0.0",
	dependency_links = ['http://www.voidspace.org.uk/downloads/validate.py#egg=validate-1.0.1'],
	install_requires = ['configobj>=4.7.0', 'argparse>=1.2.1', 'validate>=1.0.1', 'feedparser>=5.1.3', 'tabulate>=0.7.3'],
	scripts = ['bin/torrentcatcher'],
    keywords = ['torrent', 'rss', 'transmission'],
    classifiers = []
)
