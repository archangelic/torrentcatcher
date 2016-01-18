torrentcatcher
===========
#WARNING: This is probably horribly broken and I don't have the time to fix it at the moment. If you have any suggestions, feel free to let me know.

###Description
Takes torrent or magnet links from rss feeds you provide, parses them and sends them to transmission via the transmission-remote command line utility.
###Installation and Usage
To install this for your personal use run these commands:
```
git clone https://github.com/archangelic/torrentcatcher
cd torrentcatcher/
python setup.py install
torrentcatcher --setup
```
OR
`pip install torrentcatcher`

Follow the setup instructions. Once completed, you will be able to just run `torrentcatcher` to start downloading from the feed you added!

`torrentcatcher.py -h` will reveal all available options and their descriptions.
