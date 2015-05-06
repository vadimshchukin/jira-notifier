#!/usr/bin/env python
# -*- coding: utf-8 -*-

# standard modules:
import sys
import os
import re
import time
import urllib
import urllib2
import cookielib
import argparse
import json
import thread
import webbrowser

import gtk # GTK bindings
import gobject # GObject library
import appindicator # GNOME indicators
import pynotify # NotifyOSD notifications
import feedparser # RSS/Atom feed parser
import pyquery # jQuery-like library for Python

class Flusher(): # standard output flusher
    def __init__(self, file):
        self.file = file # preserve File object reference

    def write(self, data):
        self.file.write(data) # write data as ususal
        self.file.flush() # force flush

class Application: # application logic
    def __init__(self):
        sys.stdout = Flusher(sys.stdout) # force standard output flushing
        pynotify.init('jira-notifier') # initialize NotifyOSD notifications
        self.published = {} # projects activity streams last published timestamps
        # create URL opener using cookie jar
        self.opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cookielib.CookieJar()))
        self.update = True # update loop flag

    def initialize(self):
        # create GNOME indicator
        iconFileName = os.path.abspath(self.iconFileName)
        category = appindicator.CATEGORY_APPLICATION_STATUS
        self.indicator = appindicator.Indicator('jira-notifier', iconFileName, category)
        self.indicator.set_status(appindicator.STATUS_ACTIVE) # set initial active status

        exitItem = gtk.MenuItem('Exit') # create exit item
        exitItem.connect('activate', gtk.main_quit) # connect with GTK main loop quit
        indicatorMenu = gtk.Menu() # create indicator menu
        indicatorMenu.append(exitItem) # append it
        indicatorMenu.show_all() # show all items and menu itself
        self.indicator.set_menu(indicatorMenu) # set indicator menu

        if not os.path.isdir(self.avatarsDirectoryName): # if avatars directory doesn't exist
            os.mkdir(self.avatarsDirectoryName) # then create it

    def login(self, username, password): # log in JIRA
        request = urllib2.Request(self.trackerURL + '/rest/auth/latest/session') # construct request URL
        # all JIRA's REST communication should be in a JSON format
        request.add_header('Content-Type', 'application/json')
        request.add_header('Accept', 'application/json') # accept data in JSON
        # encode credentials to JSON and store in request
        request.add_data(json.dumps({'username': username, 'password': password}))

        webFile = self.opener.open(request) # perform request and open output stream
        webFile.close() # close it permanently as we are just authorizing

    def logout(self): # log out JIRA
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

    def processProjectActivityStream(self, projectKey): # process Atom feed
        # construct request
        request = urllib2.Request(self.trackerURL + '/activity?streams=key+IS+%s' % projectKey)
        webFile = self.opener.open(request) # perform request and open output stream
        feed = feedparser.parse(webFile.read()) # parse Atom feed
        feedEntries = feed['entries'] # get feed entries
        webFile.close() # close output stream

        feedEntries.reverse() # reverse entries order
        for feedEntry in feedEntries: # loop through activity stream entries
            
            # if activity stream has been gathered for the first time or it wasn't changed
            if projectKey not in self.published or feedEntry['published_parsed'] <= self.published[projectKey]:
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
                    avatarFileName = os.path.join(self.avatarsDirectoryName, '%s.png' % avatarIdentifier)
                    
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
            if projectKey not in self.published or self.published[projectKey] < feedEntry['published_parsed']:
                self.published[projectKey] = feedEntry['published_parsed'] # update projects last published timestamps

    def processIssueQuery(self, issueQuery, menu):
        parameters = urllib.urlencode({'jql': issueQuery}) # prepare GET parameteres
        resourceURL = self.trackerURL + '/rest/api/2/search?%s' % parameters # request issues by JQL filter
        webFile = self.opener.open(urllib2.Request(resourceURL)) # perform request and open output stream
        response = json.loads(webFile.read()) # parse response JSON
        webFile.close() # close output stream

        projectKey = None # current project key
        for issue in response['issues']: # loop through response issues

            match = re.match(r'(?P<projectKey>\w+)-(\d+)', issue['key'])
            # if project key has changed
            if not projectKey or match.group('projectKey') != projectKey:
                projectKey = match.group('projectKey')
                projectKeyItem = gtk.MenuItem(projectKey) # create project key item
                # prepare project URL
                projectURL = '%s/browse/%s' % (self.trackerURL, projectKey)
                # connect project key item with function handler, binding it with appropriate URL
                projectKeyItem.connect('activate', self.handleMenuItemSelect, projectURL)
                menu.append(projectKeyItem) # append item to menu
            
            # preapre issue item title, shorten summary to 32 characters
            issueTitle = '%s %s' % (issue['key'], issue['fields']['summary'][:32])
            issueItem = gtk.MenuItem(issueTitle) # create menu item
            # prepare issue URL
            issueURL = '%s/browse/%s' % (self.trackerURL, issue['key'])
            # connect menu item with function handler, binding it with appropriate URL
            issueItem.connect('activate', self.handleMenuItemSelect, issueURL)
            menu.append(issueItem) # append issue item to menu

    def updateData(self): # update application data
        indicatorMenu = gtk.Menu() # create GTK menu for indicator

        for queryIndex in xrange(len(self.issueQueries)): # loop through issue queries
            print 'processing issue query #%s of %s' % ((queryIndex + 1), len(self.issueQueries)) # print log message
            self.processIssueQuery(self.issueQueries[queryIndex], indicatorMenu)
        
        exitItem = gtk.MenuItem('Exit') # create exit item
        exitItem.connect('activate', gtk.main_quit) # connect with GTK main loop quit
        indicatorMenu.append(exitItem) # append it

        indicatorMenu.show_all() # show all items and menu itself
        self.indicator.set_menu(indicatorMenu) # set indicator menu

        for projectKey in self.projectKeys: # loop through project keys
            print "processing activity stream for '%s' project" % projectKey # print log message
            self.processProjectActivityStream(projectKey) # process current project key

    def updateDataLoop(self): # infinite update loop
        if self.username:
            print "logging in JIRA as '%s'" % self.username # print log message
            self.login(self.username, self.password) # log in jira

        while self.update:
            self.updateData() # update JIRA data
            print 'waiting for %d seconds' % self.updateInterval
            time.sleep(self.updateInterval) # suspend execution for a specified interval
        
        if self.username:
            print 'logging out JIRA' # print log message
            self.logout() # log out JIRA

    def run(self): # main method
        # construct argument parser
        argumentParser = argparse.ArgumentParser(description='Desktop notifier for JIRA issue tracker')
        argumentParser.add_argument('-j', '--jira', required=True, help='JIRA tracker URL') # JIRA tracker URL
        argumentParser.add_argument('-u', '--username', help='JIRA username') # JIRA username
        argumentParser.add_argument('-p', '--password', help='JIRA password') # JIRA password
        argumentParser.add_argument('-k', '--keys', help='project keys') # list of project keys separated by comma
        argumentParser.add_argument('-q', '--queries', help='JQL queries file') # input JQL queries file
        argumentParser.add_argument('-i', '--interval', type=int, default=60, help='update interval') # timer update interval
        argumentParser.add_argument('-a', '--avatars', default='avatars', help='avatars directory') # avatars directory
        argumentParser.add_argument('-c', '--icon', default='icon.png', help='icon file') # icon file
        arguments = argumentParser.parse_args() # parse command line arguments

        self.trackerURL = arguments.jira # get JIRA URL
        self.username = arguments.username # get JIRA username
        self.password = arguments.password # get JIRA password
        self.projectKeys = arguments.keys.split(',') # get project keys
        self.issueQueries = open(arguments.queries).read().split('\n') # read and split JQL queries
        self.updateInterval = arguments.interval # get update interval
        self.avatarsDirectoryName = arguments.avatars # get avatars directory name
        self.iconFileName = arguments.icon # get icon file name

        print 'notifier options:'
        print 'tracker URL: %s' % self.trackerURL
        if self.username:
            print 'username: %s' % self.username
        print 'project keys: %s' % arguments.queries
        print 'issue queries file: %s' % os.path.abspath(arguments.queries)
        print 'update interval: %d seconds' % self.updateInterval
        print 'avatars directory: %s' % os.path.abspath(self.avatarsDirectoryName)
        print 'icon file: %s' % os.path.abspath(self.iconFileName)
        print ''

        self.initialize()

        print 'starting update loop'
        thread.start_new_thread(self.updateDataLoop, ()) # start new update loop thread
        gobject.threads_init() # allow multiple threads to serialize access to the interpreter
        gtk.main() # run infinite GTK main loop

if __name__ == '__main__': # if it's a main module
    Application().run() # then construct an Application object and run it
