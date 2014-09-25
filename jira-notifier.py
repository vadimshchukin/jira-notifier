#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import os
import re
import time
import tempfile
import urllib
import urllib2
import cookielib
import argparse
import json
import webbrowser
import gtk # GTK bindings
import gobject # GObject library
import appindicator # GNOME indicators
import pynotify # NotifyOSD notifications
import feedparser # RSS/Atom feed parser
import pyquery # jQuery like library for Python

class Flusher():
    def __init__(self, file):
        self.file = file # preserve File object reference

    def write(self, data):
        self.file.write(data) # write data as ususal
        self.file.flush() # force flush

class Application:
    def __init__(self):
        sys.stdout = Flusher(sys.stdout) # force standard output flushing
        pynotify.init('jira-notifier') # initialize NotifyOSD notifications
        directoryName = os.path.join(os.path.dirname(__file__), 'avatars') # get 'avatars' directory name
        if not os.path.isdir(directoryName): # if it's not exists
            os.mkdir(directoryName) # then create it
        self.updated = {} # projects activity streams last updated timestamps
        iconFileName = os.path.abspath(os.path.join(os.path.dirname(__file__), 'icon.png')) # get 'icon.png' file name
        # create GNOME indicator 
        self.indicator = appindicator.Indicator('jira', iconFileName, appindicator.CATEGORY_APPLICATION_STATUS) 
        self.indicator.set_status(appindicator.STATUS_ACTIVE) # set initial active status
        # create URL opener using cookie jar
        self.opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cookielib.CookieJar())) 

    def logIn(self, userName, passWord): # log in JIRA
        request = urllib2.Request(self.trackerURL + '/rest/auth/latest/session') # construct request URL
        # all JIRA's REST communication should be in a JSON format
        request.add_header('Content-Type', 'application/json')
        request.add_header('Accept', 'application/json') # accept data in JSON
        # encode credentials to JSON and store in request
        request.add_data(json.dumps({'username': userName, 'password': passWord}))
        webFile = self.opener.open(request) # perform request and open output stream
        webFile.close() # close it permanently as we are just authorizing

    def logOut(self): # log out JIRA
        request = urllib2.Request(self.trackerURL + '/rest/auth/latest/session') # construct request URL
        request.add_header('Content-Type', 'application/json') # input data type
        request.get_method = lambda: 'DELETE' # DELETE should be used to log out
        webFile = self.opener.open(request) # perform request and open output stream
        webFile.close()

    def handleMenuItemSelect(self, widget, issueURL): # indicator menu item select handler
        output = os.dup(1) # duplicate standard otuput
        os.close(1) # close standard output
        os.open(os.devnull, os.O_RDWR) # open standard output as /dev/null in read/write
        try:
            webbrowser.open(issueURL) # open URL in browser
        finally:
            os.dup2(output, 1) # duplicate original standard output back

    def processFeed(self, key): # process Atom feed
        request = urllib2.Request(self.trackerURL + '/activity?streams=key+IS+%s' % key) # construct request URL
        webFile = self.opener.open(request) # perform request and open output stream
        feed = feedparser.parse(webFile.read()) # parse Atom feed
        feedEntries = feed['entries'] # get feed entries
        webFile.close() # close output stream
        for feedEntry in feedEntries: # loop through activity stream entries
            # if activity stream has been gathered for the first time or it wasn't changed
            if key not in self.updated or feedEntry['updated_parsed'] <= self.updated[key]:
                continue # then skip entry
            title = pyquery.PyQuery(feedEntry['title']).text() # get text from HTML
            if 'content' in feedEntry: # check for content in feed entry
                content = feedEntry['content']
                for item in content: # loop through content entries
                    if item['type'] == 'text/html': # check for MIME type
                        body = pyquery.PyQuery(item['value']).text() # get text from HTML
            else:
                body = feedEntry['summary_detail']['value'] # else just get plain text
            for link in feedEntry['links']: # loop through the entry links
                if link['rel'] == 'photo': # check for photo link
                    # get avatar id from link reference
                    match = re.search(r'avatarId=(?P<avatarIdentifier>\d+)', link.href)
                    avatarIdentifier = match.group('avatarIdentifier')
                    # get avatar file name
                    avatarFileName = os.path.join(os.path.dirname(__file__), 'avatars', '%s.png' % avatarIdentifier) 
                    if not os.path.isfile(avatarFileName): # if avatar don't exists
                        request = urllib2.Request(link.href) # construct request for avatar image
                        webFile = self.opener.open(request) # open it
                        open(avatarFileName, 'wb').write(webFile.read()) # write binary data to avatar file
                    break
            # construct NotifyOSD notification
            notification = pynotify.Notification(title, body, os.path.abspath(avatarFileName))
            notification.show() # show it
        for feedEntry in feedEntries: # loop through activity stream entries
            # if activity stream has been gathered for the first time or it was changed
            if key not in self.updated or self.updated[key] < feedEntry['updated_parsed']:
                self.updated[key] = feedEntry['updated_parsed'] # update projects last updated timestamps

    def update(self): # update application data
        menu = gtk.Menu() # create GTK menu for indicator
        for key in self.keys: # loop through project keys
            print 'processing feed for %s' % key # print log message
            self.processFeed(key) # process current project key
        for queryIndex in xrange(len(self.queries)): # loop through issue queries
            print 'executing query %s of %s' % ((queryIndex + 1), len(self.queries)) # print log message
            parameters = urllib.urlencode({'jql': self.queries[queryIndex]}) # GET parameteres
            resourceURL = self.trackerURL + '/rest/api/2/search?%s' % parameters # request issues by JQL filter
            webFile = self.opener.open(urllib2.Request(resourceURL)) # perform request and open output stream
            response = json.loads(webFile.read()) # parse JSON
            webFile.close()
            for issue in response['issues']: # loop through response issues
                # get menu item title, shorten summary to 32 characters
                title = '%s %s' % (issue['key'], issue['fields']['summary'][:32])
                item = gtk.MenuItem(title) # create menu item
                # connect menu item with function handler, binding it with appropriate URL
                item.connect('activate', self.handleMenuItemSelect, '%s/browse/%s' % (self.trackerURL, issue['key']))
                menu.append(item) # append item to menu
        item = gtk.MenuItem('Exit') # create exit item
        item.connect('activate', gtk.main_quit) # connect with GTK main loop quit
        menu.append(item) # append it
        menu.show_all() # show all items and menu itself
        self.indicator.set_menu(menu) # set indicator menu
        gobject.timeout_add_seconds(60, self.update) # schedule function invocation by timer

    def run(self): # main method
        # construct argument parser
        argumentParser = argparse.ArgumentParser(description='Notification application for a JIRA bug tracker')
        argumentParser.add_argument('-l', '--locator', required=True, help='JIRA server URL') # bug tracker URL
        argumentParser.add_argument('-u', '--username', required=True, help='authorization username') # JIRA username
        argumentParser.add_argument('-p', '--password', required=True, help='authorization password') # JIRA password
        argumentParser.add_argument('-k', '--keys', help='project keys') # list of project keys separated by comma
        argumentParser.add_argument('-q', '--queries', help='JQL queries file') # input JQL queries file
        arguments = argumentParser.parse_args() # parse command line arguments
        self.trackerURL = arguments.locator # get JIRA URL
        self.keys = arguments.keys.split(',') # get project keys
        self.queries = open(arguments.queries).read().split('\n') # read and split JQL queries
        print 'logging in as %s' % arguments.username # print log message
        self.logIn(arguments.username, arguments.password) # log in JIRA
        self.update() # first update of data
        gtk.main() # run infinite GTK main loop
        print 'logging out' # print log message
        self.logOut() # log out JIRA

if __name__ == '__main__': # if it's a main module
    Application().run() # then construct an Application object and run it