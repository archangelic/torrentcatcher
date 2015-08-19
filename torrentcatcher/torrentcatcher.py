#!/usr/bin/env python
###########################################################################
# torrentcatcher v2.1.2
#     Copyright (C) 2015  Michael Hancock
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

import logging
import logging.handlers
import shlex
import sqlite3 as lite
import subprocess
import sys
import validate

from configobj import ConfigObj
from datetime import datetime
from feedparser import parse
from tabulate import tabulate


class TorrentCatcher():
    def __init__(self, trconf, trlog, trdb, trquiet=False):
        self.configfile = trconf
        self.log = trlog
        self.quiet = trquiet
        # Creates database if it does not exist
        self.con = lite.connect(trdb)
        self.cur = self.con.cursor()
        self.cur.execute((
                'CREATE TABLE IF NOT EXISTS torrents(id INTEGER PRIMARY KEY, '
                'name TEXT, url TEXT, source TEXT, downStatus BOOLEAN);'
            ))
        self.cur.execute((
                'CREATE TABLE IF NOT EXISTS feeds(id INTEGER PRIMARY KEY, '
                'name TEXT, url TEXT);'
            ))
        self.con.commit()
        # Set up logger
        self.logger = logging.getLogger('torrentcatcher')
        self.logger.setLevel(logging.DEBUG)
        self.logger.propagate = False
        fhandler = logging.handlers.RotatingFileHandler(
            trlog,
            maxBytes=1000000,
            backupCount=5
        )
        fhandler.setLevel(logging.DEBUG)
        out = logging.StreamHandler(stream=sys.stdout)
        out.setLevel(logging.INFO)
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        oformatter = logging.Formatter('%(message)s')
        fhandler.setFormatter(formatter)
        out.setFormatter(oformatter)
        self.logger.addHandler(fhandler)
        if not trquiet:
            self.logger.addHandler(out)

    # Function to parse the config file and return the dictionary of values.
    # Also creates a config file if one does not exist.
    def configreader(self):
        cfg = """hostname = string(default='localhost')
            port = string(default='9091')
            require_auth = boolean(default=False)
            username = string(default='')
            password = string(default='')
            download_directory = string(default='')"""
        spec = cfg.split("\n")
        config = ConfigObj(self.configfile, configspec=spec)
        validator = validate.Validator()
        config.validate(validator, copy=True)
        config.filename = self.configfile
        config.write()
        return config

    def write(self, name, url, source):
        self.cur.execute(
            ("INSERT INTO torrents(name, url, source, downStatus) "
             "VALUES (?, ?, ?, 0);"),
            (name, url, source)
        )
        self.con.commit()

    # Function to write entries from the feed to the database
    def feeder(self):
        entries = []
        count = {'arc': 0, 'cache': 0, 'write': 0}
        self.cur.execute('SELECT * FROM feeds;')
        feeds = self.cur.fetchall()
        if feeds == []:
            self.logger.warn((
                    "No feeds found! Use '-f' or '--add-feed' options to "
                    "add torrent feeds"
                ))
            return 0
        for i in feeds:
            self.logger.info('Reading entries for feed "' + i[1] + '"')
            feeddat = parse(i[2])
            entries = feeddat.entries
            feedname = i[1]
            for i in entries:
                title = i['title']
                link = i['link']
                self.cur.execute(
                    "SELECT EXISTS(SELECT * FROM torrents WHERE name=?);",
                    (title,)
                )
                test = self.cur.fetchall()
                if test[0][0] != 1:
                    self.write(title, link, feedname)
                    count['write'] += 1
                    self.logger.info(title+' was added to queue')
                else:
                    self.cur.execute("SELECT * FROM torrents WHERE name=?",
                                     (title,))
                    status = self.cur.fetchall()
                    if status[0][4] == 1:
                        count['arc'] += 1
                    elif status[0][4] == 0:
                        count['cache'] += 1
        total = count['arc'] + count['cache'] + count['write']
        if total != 0:
            self.logger.info('New Torrents: ' + str(count['write']))
            self.logger.info('Already Queued: ' + str(count['cache']))
            self.logger.info('Already Archived: ' + str(count['arc']))
        else:
            self.logger.error(
                'No feed information found. Something is probably wrong.'
            )

    # Function updates given entries to show they have been sent to the Archive
    def move(self, title):
        self.cur.execute("UPDATE torrents SET downStatus=1 WHERE name=?",
                         (title,))
        self.con.commit()
        self.logger.info(title + ' was moved to archive.')

    # Add Feed utility. Takes the name and URL and appends to the config file
    def addfeed(self, name, url):
        self.cur.execute('INSERT INTO feeds(name, url) VALUES (?,?);',
                         (name, url))
        self.con.commit()
        self.logger.info('Feed "' + name + '" added successfully.')

    # Searches the database for a given query
    def torsearch(self, category, query):
        resultlist = []
        if category == 'id':
            try:
                qtest = int(query)
                self.cur.execute("SELECT * FROM torrents WHERE id LIKE ?",
                                 (query,))
                results = self.cur.fetchall()
                if results == []:
                    print "No results found in '{0}' for '{1}".format(category,
                                                                      query)
                else:
                    for each in results:
                        if each[4] == 0:
                            status = 'Queue'
                        elif each[4] == 1:
                            status = 'Archive'
                        resultlist.append([each[0], each[1], each[3], status])
                    print tabulate(resultlist,
                                   ['ID', 'Name', 'Source', 'Status'])
            except:
                print "Please enter a valid ID number for ID searches."
        else:
            if category == 'name':
                self.cur.execute("SELECT * FROM torrents WHERE name LIKE ?;",
                                 ('%'+query+'%',))
            elif category == 'source':
                self.cur.execute("SELECT * FROM torrents WHERE source LIKE ?;",
                                 ('%'+query+'%',))
            results = self.cur.fetchall()
            if results == []:
                print "No results found in '{0}' for '{1}'".format(category,
                                                                   query)
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
                print tabulate(resultlist,
                               ['ID', 'Name', 'URL'],
                               tablefmt='pipe')
        if cat == 'archive':
            down = 1
            status = 'Archive'
        if cat == 'queue':
            down = 0
            status = 'Queue'
        if (cat == 'archive') or (cat == 'queue'):
            self.cur.execute('SELECT * FROM torrents WHERE downStatus=?;',
                             (down,))
            results = self.cur.fetchall()
            for each in results:
                resultlist.append([each[0], each[1], each[3], status])
            print tabulate(resultlist,
                           ['ID', 'Name', 'Source', 'Status'],
                           tablefmt='pipe')

    # Function to run the Archive only feature
    def archive(self, selID):
        self.logger.info(
            'Moving selected torrents in queue to the archive'
        )
        if selID[0] == 'all':
            self.cur.execute("SELECT * FROM torrents WHERE downStatus=0")
            cachelist = self.cur.fetchall()
            if cachelist == []:
                self.logger.info('No torrents to archive')
            else:
                for each in cachelist:
                    self.move(each[1])
                self.logger.info('Archive process completed successfully')
        else:
            ids = []
            for each in selID:
                if each != 'all':
                    try:
                        int(each)
                        ids.append(each)
                    except:
                        print "'%s' is not a valid ID." % (each)
            for each in ids:
                    self.cur.execute("SELECT * FROM torrents WHERE id=?",
                                     (each,))
                    selection = self.cur.fetchall()
                    if selection == []:
                        self.logger.error(("ID '%s' does not exist") % (each))
                    else:
                        seltor = selection[0]
                        if seltor[4] == 0:
                            self.move(seltor[1])
                        elif seltor[4] == 1:
                            self.logger.info((
                                    '%s is already in the archive.' %
                                    (seltor[1])
                            ))
            self.logger.info(
                'Archive process completed successfully'
            )

    # Function to add items to the queue from the archive
    def queue(self, selID):
        self.logger.info(
            'Moving selected torrents in the archive to the queue'
        )
        if selID[0] == 'all':
            self.cur.execute("SELECT * FROM torrents WHERE downStatus=1")
            cachelist = self.cur.fetchall()
            if cachelist == []:
                self.logger.info('No torrents to queue')
            else:
                for each in cachelist:
                    self.cur.execute(
                        "UPDATE torrents SET downStatus=0 WHERE name=?",
                        (each[1],)
                    )
                    self.con.commit()
                    self.logger.info(each[1] + ' was moved to the queue.')
                self.logger.info('Archive process completed successfully')
        else:
            ids = []
            for each in selID:
                if each != 'all':
                    try:
                        int(each)
                        ids.append(each)
                    except:
                        print "'%s' is not a valid ID." % (each)
            for each in ids:
                    self.cur.execute("SELECT * FROM torrents WHERE id=?",
                                     (each,))
                    selection = self.cur.fetchall()
                    if selection == []:
                        self.logger.error(("ID '%s' does not exist") % (each))
                    else:
                        seltor = selection[0]
                        if seltor[4] == 1:
                            self.cur.execute(
                                ("UPDATE torrents SET downStatus=0 "
                                 "WHERE name=?"),
                                (seltor[1],)
                            )
                            self.con.commit()
                            self.logger.info(
                                seltor[1]+' was moved to the queue.'
                            )
                        elif seltor[4] == 0:
                            self.logger.info(
                                '%s is already in the queue.' %
                                (seltor[1])
                            )
            self.logger.info('Queue process completed successfully')

    # Function to add files to Transmission over transmission-remote
    def transmission(self, title, url):
        config = self.configreader()
        host = config['hostname']
        port = config['port']
        auth = config['require_auth']
        authopt = config['username'] + ':' + config['password']
        downdir = config['download_directory']
        self.logger.info('Starting download for ' + title)
        if not auth:
            command = ('transmission-remote ' + host + ':' + port + ' -a "' +
                       url + '"')
        else:
            command = ('transmission-remote  ' + host + ':' + port + ' -n ' +
                       authopt + ' -a "' + url + '"')
        if downdir != '':
            command = command + ' -w ' + downdir
        transcmd = subprocess.Popen(shlex.split(command),
                                    stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE)
        output, error = transcmd.communicate()
        if error == "":
            self.move(title)
            self.logger.info(output.strip('\n'))
            return 0
        else:
            self.logger.error(error.strip('\n'))
            return 1

    # Function to run the Download only feature
    def download(self, selID):
        self.logger.info(
            'Starting download of already queued torrents'
        )
        if selID[0] == 'all':
            self.cur.execute("SELECT * FROM torrents WHERE downStatus=0")
            cachelist = self.cur.fetchall()
            if cachelist == []:
                self.logger.info('No torrents to download')
            else:
                errors = 0
                for each in cachelist:
                    test = self.transmission(each[1], each[2])
                    errors += test
                if errors > 0:
                    self.logger.info(
                            'There were errors adding torrents to Transmission'
                    )
                else:
                    self.logger.info(
                        'Initiated downloads successfully'
                    )
        else:
            errors = 0
            ids = []
            for each in selID:
                if each != 'all':
                    try:
                        int(each)
                        ids.append(each)
                    except:
                        print "'%s' is not a valid ID." % (each)
            for each in ids:
                self.cur.execute("SELECT * FROM torrents WHERE id=?", (each,))
                selection = self.cur.fetchall()
                if selection == []:
                    self.logger.error(("ID '%s' does not exist") % (each))
                else:
                    seltor = selection[0]
                    test = self.transmission(seltor[1], seltor[2])
                    errors += test
            if errors > 0:
                self.logger.error(
                    'There were errors adding torrents to Transmission'
                )
            else:
                self.logger.info('Initiated all downloads successfully')

    # The full automatic torrentcatcher
    def torrentcatcher(self):
        self.logger.info('Starting Torrentcatcher')
        self.feeder()
        self.cur.execute("SELECT * FROM torrents WHERE downStatus=0")
        cachelist = self.cur.fetchall()
        if cachelist == []:
            self.logger.info('No torrents to start')
        else:
            errors = 0
            for each in cachelist:
                test = self.transmission(each[1], each[2])
                errors += test
            if errors > 0:
                self.logger.error(
                        'There were errors adding torrents to Transmission'
                )
            else:
                self.logger.info(
                    'Initiated all downloads successfully'
                )
